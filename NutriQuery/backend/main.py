from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List

import schemas
import crud
import ml_service
from database import get_db

# ── FastAPI Application ───────────────────────────────
app = FastAPI(title="NutriQuery API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Type alias for the database dependency (Annotated style)
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
    result = crud.update_nutrition(conn, cursor, fdc_id, nutrition.model_dump(exclude_unset=True))
    if result is None:
        raise HTTPException(status_code=404, detail="Nutrition record not found")
    return result


@app.put("/foods/{fdc_id}/health", response_model=schemas.Health)
def update_food_health(fdc_id: int, health: schemas.HealthBase, db: DbDep):
    conn, cursor = db
    result = crud.update_health(conn, cursor, fdc_id, health.model_dump(exclude_unset=True))
    if result is None:
        raise HTTPException(status_code=404, detail="Health record not found")
    return result


# ── Req 4: Range Querying ────────────────────────────
@app.get("/queries/range", response_model=List[schemas.Food])
def query_by_range(
    db: DbDep,
    min_health_score: Annotated[float, Query()] = 50.0,
    max_sodium: Annotated[float, Query()] = 200.0,
    max_carbs: Annotated[float, Query()] = 30.0,
):
    conn, cursor = db
    return crud.get_foods_by_range(conn, cursor, min_health_score, max_sodium, max_carbs)


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
def query_aggregation(db: DbDep, category: Annotated[str, Query()] = "Snacks"):
    conn, cursor = db
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


# ── NEW: Data Import Trigger ────────────────────────
@app.post("/import")
def trigger_import():
    import data_import
    result = data_import.import_all_data()
    return result
