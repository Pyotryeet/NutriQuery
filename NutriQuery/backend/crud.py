# ── Requirement 2: Record Retrieval ────────────────────
def get_food(conn, cursor, fdc_id: int):
    """
    Retrieve a full food profile by fdc_id, joining across all related tables.
    Uses a multi-table JOIN to pull brand, nutrition, and health data in one query.
    """
    cursor.execute("""
        SELECT
            f.fdc_id, f.food_name, f.data_type, f.food_category, f.brand_id,
            b.brand_name, b.brand_owner, b.ecoscore_grade,
            n.nutrition_id, n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg,
            h.profile_id, h.contains_gluten, h.contains_dairy,
            h.health_score, h.nutriscore_grade, h.nova_group
        FROM Foods f
        LEFT JOIN Brands b ON f.brand_id = b.brand_id
        LEFT JOIN Nutrition_Metrics n ON f.fdc_id = n.fdc_id
        LEFT JOIN Health_and_Allergens h ON f.fdc_id = h.fdc_id
        WHERE f.fdc_id = %s
    """, (fdc_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return _build_food_dict(row)


# ── Requirement 3: Data Correction ─────────────────────
def update_nutrition(conn, cursor, fdc_id: int, data: dict):
    """Update nutrition metrics for a food item via a dynamic UPDATE statement."""
    set_clauses = []
    values = []
    for col in ("calories", "protein_g", "fat_g", "carbs_g", "sodium_mg"):
        if col in data and data[col] is not None:
            set_clauses.append(f"{col} = %s")
            values.append(data[col])

    if not set_clauses:
        return None

    values.append(fdc_id)
    cursor.execute(
        f"UPDATE Nutrition_Metrics SET {', '.join(set_clauses)} WHERE fdc_id = %s",
        tuple(values),
    )
    conn.commit()

    cursor.execute("SELECT * FROM Nutrition_Metrics WHERE fdc_id = %s", (fdc_id,))
    return cursor.fetchone()


def update_health(conn, cursor, fdc_id: int, data: dict):
    """Update health/allergen profile for a food item."""
    set_clauses = []
    values = []
    for col in ("contains_gluten", "contains_dairy", "health_score", "nutriscore_grade", "nova_group"):
        if col in data and data[col] is not None:
            set_clauses.append(f"{col} = %s")
            values.append(data[col])

    if not set_clauses:
        return None

    values.append(fdc_id)
    cursor.execute(
        f"UPDATE Health_and_Allergens SET {', '.join(set_clauses)} WHERE fdc_id = %s",
        tuple(values),
    )
    conn.commit()

    cursor.execute("SELECT * FROM Health_and_Allergens WHERE fdc_id = %s", (fdc_id,))
    return cursor.fetchone()


# ── Requirement 4: Range Querying ──────────────────────
def get_foods_by_range(conn, cursor, min_health_score: float, max_sodium: float, max_carbs: float, limit: int = 100):
    """
    Complex cross-table range query: find foods that satisfy simultaneous constraints
    on health score, sodium, and carb levels using a 3-table JOIN with WHERE filters.
    """
    cursor.execute("""
        SELECT TOP %s
            f.fdc_id, f.food_name, f.data_type, f.food_category, f.brand_id,
            b.brand_name, b.brand_owner, b.ecoscore_grade,
            n.nutrition_id, n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg,
            h.profile_id, h.contains_gluten, h.contains_dairy,
            h.health_score, h.nutriscore_grade, h.nova_group
        FROM Foods f
        JOIN Nutrition_Metrics n ON f.fdc_id = n.fdc_id
        JOIN Health_and_Allergens h ON f.fdc_id = h.fdc_id
        LEFT JOIN Brands b ON f.brand_id = b.brand_id
        WHERE h.health_score >= %s
          AND n.sodium_mg <= %s
          AND n.carbs_g <= %s
        ORDER BY h.health_score DESC
    """, (limit, min_health_score, max_sodium, max_carbs))
    return [_build_food_dict(row) for row in cursor.fetchall()]


# ── Requirement 5: Dietary Filtering ──────────────────
def get_foods_by_diet(conn, cursor, no_gluten: bool = False, no_dairy: bool = False, limit: int = 100):
    """Filter foods by allergen/dietary restrictions using conditional WHERE clauses."""
    where_clauses = []
    values = []

    if no_gluten:
        where_clauses.append("h.contains_gluten = 0")
    if no_dairy:
        where_clauses.append("h.contains_dairy = 0")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cursor.execute(f"""
        SELECT TOP %s
            f.fdc_id, f.food_name, f.data_type, f.food_category, f.brand_id,
            b.brand_name, b.brand_owner, b.ecoscore_grade,
            n.nutrition_id, n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg,
            h.profile_id, h.contains_gluten, h.contains_dairy,
            h.health_score, h.nutriscore_grade, h.nova_group
        FROM Foods f
        JOIN Health_and_Allergens h ON f.fdc_id = h.fdc_id
        LEFT JOIN Nutrition_Metrics n ON f.fdc_id = n.fdc_id
        LEFT JOIN Brands b ON f.brand_id = b.brand_id
        {where_sql}
        ORDER BY f.food_name
    """, (limit,))
    return [_build_food_dict(row) for row in cursor.fetchall()]


# ── Requirement 6: Aggregation ─────────────────────────
def get_category_aggregation(conn, cursor, category: str):
    """
    Aggregate nutritional statistics for a given food category.
    Uses AVG() and COUNT() aggregate functions with GROUP BY.
    """
    cursor.execute("""
        SELECT
            f.food_category,
            AVG(n.calories) AS avg_calories,
            AVG(n.protein_g) AS avg_protein,
            AVG(n.fat_g) AS avg_fat,
            AVG(n.carbs_g) AS avg_carbs,
            COUNT(f.fdc_id) AS item_count
        FROM Foods f
        JOIN Nutrition_Metrics n ON f.fdc_id = n.fdc_id
        WHERE f.food_category = %s
        GROUP BY f.food_category
    """, (category,))
    row = cursor.fetchone()
    if not row:
        return {
            "food_category": category,
            "avg_calories": 0, "avg_protein": 0,
            "avg_fat": 0, "avg_carbs": 0, "item_count": 0,
        }
    return {
        "food_category": row["food_category"],
        "avg_calories": round(row["avg_calories"] or 0, 2),
        "avg_protein": round(row["avg_protein"] or 0, 2),
        "avg_fat": round(row["avg_fat"] or 0, 2),
        "avg_carbs": round(row["avg_carbs"] or 0, 2),
        "item_count": row["item_count"] or 0,
    }


# ── Requirement 7: Gap Identification ─────────────────
def get_foods_with_missing_data(conn, cursor, limit: int = 100):
    """
    Identify records with incomplete nutritional data (NULL values)
    to surface data quality issues.
    """
    cursor.execute("""
        SELECT TOP %s
            f.fdc_id, f.food_name, f.data_type, f.food_category, f.brand_id,
            b.brand_name, b.brand_owner, b.ecoscore_grade,
            n.nutrition_id, n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg,
            h.profile_id, h.contains_gluten, h.contains_dairy,
            h.health_score, h.nutriscore_grade, h.nova_group
        FROM Foods f
        JOIN Nutrition_Metrics n ON f.fdc_id = n.fdc_id
        LEFT JOIN Health_and_Allergens h ON f.fdc_id = h.fdc_id
        LEFT JOIN Brands b ON f.brand_id = b.brand_id
        WHERE n.calories IS NULL
           OR n.protein_g IS NULL
           OR n.fat_g IS NULL
           OR n.carbs_g IS NULL
           OR n.sodium_mg IS NULL
    """, (limit,))
    return [_build_food_dict(row) for row in cursor.fetchall()]


# ── Requirement 8: Metadata Management ────────────────
def create_brand(conn, cursor, data: dict):
    """Insert a new brand record and return it with the generated brand_id."""
    cursor.execute(
        "INSERT INTO Brands (brand_name, brand_owner, ecoscore_grade) VALUES (%s, %s, %s)",
        (data["brand_name"], data.get("brand_owner"), data.get("ecoscore_grade")),
    )
    conn.commit()
    cursor.execute("SELECT @@IDENTITY AS brand_id")
    new_id = cursor.fetchone()["brand_id"]
    cursor.execute("SELECT * FROM Brands WHERE brand_id = %s", (int(new_id),))
    return cursor.fetchone()


def get_brands(conn, cursor, skip: int = 0, limit: int = 100):
    """Retrieve a paginated list of brands using OFFSET/FETCH."""
    cursor.execute("""
        SELECT * FROM Brands
        ORDER BY brand_id
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """, (skip, limit))
    return cursor.fetchall()


# ── NEW: Food Search by Name ──────────────────────────
def search_foods(conn, cursor, name: str, limit: int = 50):
    """Substring search on food_name using LIKE with wildcards."""
    cursor.execute("""
        SELECT TOP %s
            f.fdc_id, f.food_name, f.food_category,
            b.brand_name
        FROM Foods f
        LEFT JOIN Brands b ON f.brand_id = b.brand_id
        WHERE f.food_name LIKE %s
        ORDER BY f.food_name
    """, (limit, f"%{name}%"))
    return cursor.fetchall()


# ── NEW: Paginated Food Listing ───────────────────────
def get_all_foods(conn, cursor, skip: int = 0, limit: int = 50):
    """Retrieve a page of food records."""
    cursor.execute("""
        SELECT f.fdc_id, f.food_name, f.food_category, b.brand_name
        FROM Foods f
        LEFT JOIN Brands b ON f.brand_id = b.brand_id
        ORDER BY f.fdc_id
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """, (skip, limit))
    return cursor.fetchall()


# ── NEW: Distinct Food Categories ─────────────────────
def get_categories(conn, cursor):
    """List all distinct food categories for use in aggregation dropdowns."""
    cursor.execute("""
        SELECT DISTINCT food_category
        FROM Foods
        WHERE food_category IS NOT NULL
        ORDER BY food_category
    """)
    return [row["food_category"] for row in cursor.fetchall()]


# ── NEW: Retrieve ML Predictions ─────────────────────
def get_predictions(conn, cursor, limit: int = 100):
    """Fetch ML predictions joined with food names."""
    cursor.execute("""
        SELECT TOP %s
            p.prediction_id, p.fdc_id, f.food_name,
            p.predicted_nutriscore, p.predicted_nova,
            p.confidence_score, p.prediction_date
        FROM ML_Predictions p
        JOIN Foods f ON p.fdc_id = f.fdc_id
        ORDER BY p.prediction_date DESC
    """, (limit,))
    return cursor.fetchall()


# ── Helper ────────────────────────────────────────────
def _build_food_dict(row):
    """
    Transform a flat JOIN result row into a nested Food dict
    matching the schemas.Food model structure.
    """
    food = {
        "fdc_id": row["fdc_id"],
        "food_name": row["food_name"],
        "data_type": row.get("data_type"),
        "food_category": row.get("food_category"),
        "brand_id": row.get("brand_id"),
        "brand": None,
        "nutrition": None,
        "health": None,
        "predictions": [],
    }

    if row.get("brand_name"):
        food["brand"] = {
            "brand_id": row["brand_id"],
            "brand_name": row["brand_name"],
            "brand_owner": row.get("brand_owner"),
            "ecoscore_grade": row.get("ecoscore_grade"),
        }

    if row.get("nutrition_id"):
        food["nutrition"] = {
            "nutrition_id": row["nutrition_id"],
            "fdc_id": row["fdc_id"],
            "calories": row.get("calories"),
            "protein_g": row.get("protein_g"),
            "fat_g": row.get("fat_g"),
            "carbs_g": row.get("carbs_g"),
            "sodium_mg": row.get("sodium_mg"),
        }

    if row.get("profile_id"):
        food["health"] = {
            "profile_id": row["profile_id"],
            "fdc_id": row["fdc_id"],
            "contains_gluten": bool(row.get("contains_gluten")),
            "contains_dairy": bool(row.get("contains_dairy")),
            "health_score": row.get("health_score"),
            "nutriscore_grade": row.get("nutriscore_grade"),
            "nova_group": row.get("nova_group"),
        }

    return food
