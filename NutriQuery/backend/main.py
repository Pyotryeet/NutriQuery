from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List, Optional, TYPE_CHECKING
import time

if TYPE_CHECKING:
    import pymssql

import schemas
import crud
import ml_service
import data_import
from database import get_db

# ── FastAPI Application ───────────────────────────────
app = FastAPI(title="NutriQuery API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Type alias for the database dependency
DbDep = Annotated[tuple, Depends(get_db)]

# Include the ML router
app.include_router(ml_service.ml_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to NutriQuery API"}


# ── NEW: Food Search by Name ────────────────────────
@app.get("/foods/search", response_model=List[schemas.FoodSearchResult])
def search_foods(
    db: DbDep,
    name: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    conn, cursor = db
    return crud.search_foods(conn, cursor, name, limit)


# ── NEW: Browse Foods with Nutrition ───────────────
@app.get("/foods/browse", response_model=List[schemas.FoodBrowseResult])
def browse_foods(
    db: DbDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    name: Annotated[Optional[str], Query()] = None,
):
    conn, cursor = db
    return crud.get_foods_browse(conn, cursor, skip=skip, limit=limit, name=name)


# ── NEW: Paginated Food Listing ─────────────────────
@app.get("/foods/", response_model=List[schemas.FoodSearchResult])
def list_foods(
    db: DbDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    conn, cursor = db
    return crud.get_all_foods(conn, cursor, skip=skip, limit=limit)


# ── Req 2: Record Retrieval ──────────────────────────
@app.get("/foods/{fdc_id}", response_model=schemas.Food)
def read_food(fdc_id: int, db: DbDep):
    conn, cursor = db
    food = crud.get_food(conn, cursor, fdc_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Food not found")
    return food


# ── Req 3: Data Correction ──────────────────────────
@app.put("/foods/{fdc_id}/nutrition", response_model=schemas.Nutrition)
def update_food_nutrition(fdc_id: int, nutrition: schemas.NutritionBase, db: DbDep):
    conn, cursor = db
    # model_dump() includes all fields (even defaults); exclude_unset would
    # reject explicit null values as "not set" since the default is also None.
    data = {k: v for k, v in nutrition.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    result = crud.update_nutrition(conn, cursor, fdc_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Nutrition record not found")
    return result


@app.put("/foods/{fdc_id}/health", response_model=schemas.HealthScore)
def update_food_health(fdc_id: int, health: schemas.HealthScoreBase, db: DbDep):
    conn, cursor = db
    data = {k: v for k, v in health.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    result = crud.update_health_score(conn, cursor, fdc_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Health score record not found")
    return result


@app.put("/foods/{fdc_id}/allergen", response_model=schemas.AllergenProfile)
def update_food_allergen(fdc_id: int, allergen: schemas.AllergenProfileBase, db: DbDep):
    conn, cursor = db
    # AllergenProfileBase defaults are False, so a user sending {contains_gluten: false}
    # would have it excluded by exclude_unset. Use model_dump() and check for non-default.
    data = allergen.model_dump()
    if not any(data.values()):
        raise HTTPException(status_code=400, detail="No fields provided to update")
    result = crud.update_allergen(conn, cursor, fdc_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Allergen profile not found")
    return result


# ── Req 4: Range Querying ────────────────────────────
@app.get("/queries/range", response_model=List[schemas.Food])
def query_by_range(
    db: DbDep,
    min_health_score: Annotated[float, Query(description="Minimum health score (0-100)")] = 50.0,
    max_sodium: Annotated[float, Query(description="Maximum sodium in mg")] = 200.0,
    max_carbs: Annotated[float, Query(description="Maximum carbs in grams")] = 30.0,
    limit: Annotated[int, Query(ge=1, le=500, description="Max results")] = 100,
):
    conn, cursor = db
    return crud.get_foods_by_range(conn, cursor, min_health_score, max_sodium, max_carbs, limit=limit)


# ── Req 5: Dietary Filtering ────────────────────────
@app.get("/queries/dietary", response_model=List[schemas.Food])
def query_dietary(
    db: DbDep,
    no_gluten: Annotated[bool, Query()] = True,
    no_dairy: Annotated[bool, Query()] = True,
):
    conn, cursor = db
    return crud.get_foods_by_diet(conn, cursor, no_gluten, no_dairy)


# ── Req 6: Aggregation ──────────────────────────────
@app.get("/queries/aggregation", response_model=schemas.AggregationResult)
def query_aggregation(db: DbDep, category: Annotated[str, Query(description="Food category name")] = None):
    conn, cursor = db
    if category is None:
        cats = crud.get_categories(conn, cursor)
        if not cats:
            return {"food_category": "(none)", "avg_calories": 0,
                    "avg_protein": 0, "avg_fat": 0, "avg_carbs": 0, "item_count": 0}
        category = cats[0]
    return crud.get_category_aggregation(conn, cursor, category)


# ── Req 7: Gap Identification ────────────────────────
@app.get("/queries/gaps", response_model=List[schemas.Food])
def query_missing_data(db: DbDep):
    conn, cursor = db
    return crud.get_foods_with_missing_data(conn, cursor)


# ── Req 8: Metadata Management ──────────────────────
@app.post("/brands/", response_model=schemas.Brand)
def create_brand(brand: schemas.BrandCreate, db: DbDep):
    conn, cursor = db
    return crud.create_brand(conn, cursor, brand.model_dump())


@app.get("/brands/", response_model=List[schemas.Brand])
def read_brands(
    db: DbDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    conn, cursor = db
    return crud.get_brands(conn, cursor, skip=skip, limit=limit)


# ── NEW: Categories Listing ─────────────────────────
@app.get("/categories/")
def list_categories(db: DbDep):
    conn, cursor = db
    return crud.get_categories(conn, cursor)


# ── NEW: View Predictions ───────────────────────────
@app.get("/predictions/", response_model=List[schemas.MLPrediction])
def list_predictions(db: DbDep, limit: Annotated[int, Query(ge=1, le=500)] = 100):
    conn, cursor = db
    return crud.get_predictions(conn, cursor, limit)


# ── Import state tracking ────────────────────────────
# NOTE: This state is per-process. Under `uvicorn --workers N`, each worker
# has its own copy. Use a single-worker deployment for accurate status.
_import_state = {"running": False, "started_at": None, "completed_at": None, "last_result": None}


def _run_import():
    _import_state["running"] = True
    _import_state["started_at"] = time.time()
    _import_state["completed_at"] = None
    _import_state["last_result"] = None
    try:
        _import_state["last_result"] = data_import.import_all_data()
    finally:
        _import_state["running"] = False
        _import_state["completed_at"] = time.time()


@app.post("/import")
def trigger_import(background_tasks: BackgroundTasks):
    if _import_state["running"]:
        return {"message": "Import already in progress.", "status": "running"}
    background_tasks.add_task(_run_import)
    return {"message": "Import started in background.", "status": "started"}


@app.get("/import/status")
def import_status():
    elapsed = None
    if _import_state["running"] and _import_state["started_at"]:
        elapsed = round(time.time() - _import_state["started_at"], 1)
    return {
        "running": _import_state["running"],
        "elapsed_seconds": elapsed,
        "last_result": _import_state["last_result"],
    }
