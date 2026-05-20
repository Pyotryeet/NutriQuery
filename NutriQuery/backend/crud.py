# ── Shared FOOD_SELECT columns + FROM/JOINs (DRY — single source of truth) ──
_FOOD_COLUMNS = """
    f.fdc_id, f.food_name, f.brand_id,
    dt.type_name AS data_type,
    fc.category_name AS food_category,
    b.brand_name, b.brand_owner,
    n.nutrition_id, n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg,
    hs.score_id,
    hs.health_score, hs.nutriscore_grade, hs.nova_group,
    ap.allergen_id,
    ap.contains_gluten, ap.contains_dairy
"""

_FOOD_FROM = """
    FROM Foods f
    LEFT JOIN Brands b            ON f.brand_id    = b.brand_id
    LEFT JOIN FOOD_CATEGORY fc    ON f.category_id = fc.category_id
    LEFT JOIN DATA_TYPE dt        ON f.type_id     = dt.type_id
    LEFT JOIN Nutrition_Metrics n ON f.fdc_id      = n.fdc_id
    LEFT JOIN HEALTH_SCORE hs     ON f.fdc_id      = hs.fdc_id
    LEFT JOIN ALLERGEN_PROFILE ap ON f.fdc_id      = ap.fdc_id
"""


def _food_query(extra="", top=None):
    """Build a full food SELECT query. Set top=N for TOP N queries."""
    select = f"SELECT TOP {top} " if top else "SELECT "
    return f"{select}{_FOOD_COLUMNS} {_FOOD_FROM} {extra}"


# ── Requirement 2: Record Retrieval ────────────────────
def get_food(conn, cursor, fdc_id: int):
    cursor.execute(
        _food_query("WHERE f.fdc_id = %s"),
        (fdc_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return _build_food_dict(row)


# ── Requirement 3: Data Correction ─────────────────────
def _update_row(conn, cursor, table, columns, fdc_id, data):
    """Generic UPDATE helper. Builds SET clauses, executes, commits, returns row."""
    set_clauses = []
    values = []
    for col in columns:
        if col in data and data[col] is not None:
            set_clauses.append(f"{col} = %s")
            values.append(data[col])

    if not set_clauses:
        return None

    values.append(fdc_id)
    cursor.execute(
        f"UPDATE {table} SET {', '.join(set_clauses)} WHERE fdc_id = %s",
        tuple(values),
    )
    conn.commit()
    cursor.execute(f"SELECT * FROM {table} WHERE fdc_id = %s", (fdc_id,))
    return cursor.fetchone()


def update_nutrition(conn, cursor, fdc_id: int, data: dict):
    return _update_row(conn, cursor, "Nutrition_Metrics",
                       ("calories", "protein_g", "fat_g", "carbs_g", "sodium_mg"),
                       fdc_id, data)


def update_health_score(conn, cursor, fdc_id: int, data: dict):
    return _update_row(conn, cursor, "HEALTH_SCORE",
                       ("health_score", "nutriscore_grade", "nova_group"),
                       fdc_id, data)


def update_allergen(conn, cursor, fdc_id: int, data: dict):
    return _update_row(conn, cursor, "ALLERGEN_PROFILE",
                       ("contains_gluten", "contains_dairy"),
                       fdc_id, data)


# ── Requirement 4: Range Querying ──────────────────────
def get_foods_by_range(conn, cursor, min_health_score, max_sodium, max_carbs, limit=100):
    cursor.execute(
        _food_query("""
        WHERE hs.health_score >= %s
          AND n.sodium_mg    <= %s
          AND n.carbs_g      <= %s
        ORDER BY hs.health_score DESC
        """, top=limit),
        (min_health_score, max_sodium, max_carbs),
    )
    return [_build_food_dict(row) for row in cursor.fetchall()]


# ── Requirement 5: Dietary Filtering ──────────────────
def get_foods_by_diet(conn, cursor, no_gluten=False, no_dairy=False, limit=100):
    where_clauses = []

    if no_gluten:
        where_clauses.append("(ap.contains_gluten IS NULL OR ap.contains_gluten = 0)")
    if no_dairy:
        where_clauses.append("(ap.contains_dairy IS NULL OR ap.contains_dairy = 0)")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cursor.execute(
        _food_query(f"{where_sql} ORDER BY f.food_name", top=limit),
    )
    return [_build_food_dict(row) for row in cursor.fetchall()]


# ── Requirement 6: Aggregation ─────────────────────────
def get_category_aggregation(conn, cursor, category: str):
    cursor.execute("""
        SELECT
            fc.category_name AS food_category,
            AVG(n.calories)  AS avg_calories,
            AVG(n.protein_g) AS avg_protein,
            AVG(n.fat_g)     AS avg_fat,
            AVG(n.carbs_g)   AS avg_carbs,
            COUNT(f.fdc_id)  AS item_count
        FROM Foods f
        JOIN FOOD_CATEGORY fc     ON f.category_id = fc.category_id
        JOIN Nutrition_Metrics n  ON f.fdc_id      = n.fdc_id
        WHERE fc.category_name = %s
        GROUP BY fc.category_name
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
def get_foods_with_missing_data(conn, cursor, limit=100):
    cursor.execute(
        _food_query("""
        WHERE n.calories   IS NULL
           OR n.protein_g IS NULL
           OR n.fat_g     IS NULL
           OR n.carbs_g   IS NULL
           OR n.sodium_mg IS NULL
        """, top=limit),
    )
    return [_build_food_dict(row) for row in cursor.fetchall()]


# ── Requirement 8: Metadata Management ────────────────
def create_brand(conn, cursor, data: dict):
    cursor.execute(
        "INSERT INTO Brands (brand_name, brand_owner) VALUES (%s, %s)",
        (data["brand_name"], data.get("brand_owner")),
    )
    conn.commit()
    cursor.execute("SELECT @@IDENTITY AS brand_id")
    new_id = cursor.fetchone()["brand_id"]
    cursor.execute("SELECT * FROM Brands WHERE brand_id = %s", (int(new_id),))
    return cursor.fetchone()


def get_brands(conn, cursor, skip=0, limit=100):
    cursor.execute("""
        SELECT * FROM Brands
        ORDER BY brand_id
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """, (skip, limit))
    return cursor.fetchall()


# ── Search & Listing ──────────────────────────────────
def search_foods(conn, cursor, name: str, limit=50):
    cursor.execute("""
        SELECT TOP %s
            f.fdc_id, f.food_name,
            fc.category_name AS food_category,
            b.brand_name
        FROM Foods f
        LEFT JOIN FOOD_CATEGORY fc ON f.category_id = fc.category_id
        LEFT JOIN Brands b         ON f.brand_id    = b.brand_id
        WHERE f.food_name LIKE %s
        ORDER BY f.food_name
    """, (limit, f"%{name}%"))
    return cursor.fetchall()


def get_foods_browse(conn, cursor, skip=0, limit=50, name=None):
    """Paginated food listing with nutrition data. Optional name filter."""
    if name:
        cursor.execute("""
            SELECT f.fdc_id, f.food_name,
                   fc.category_name AS food_category,
                   b.brand_name,
                   n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg
            FROM Foods f
            LEFT JOIN FOOD_CATEGORY fc ON f.category_id = fc.category_id
            LEFT JOIN Brands b         ON f.brand_id    = b.brand_id
            LEFT JOIN Nutrition_Metrics n ON f.fdc_id   = n.fdc_id
            WHERE f.food_name LIKE %s
            ORDER BY f.food_name
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """, (f"%{name}%", skip, limit))
    else:
        cursor.execute("""
            SELECT f.fdc_id, f.food_name,
                   fc.category_name AS food_category,
                   b.brand_name,
                   n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg
            FROM Foods f
            LEFT JOIN FOOD_CATEGORY fc ON f.category_id = fc.category_id
            LEFT JOIN Brands b         ON f.brand_id    = b.brand_id
            LEFT JOIN Nutrition_Metrics n ON f.fdc_id   = n.fdc_id
            ORDER BY f.fdc_id
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """, (skip, limit))
    return cursor.fetchall()


def get_all_foods(conn, cursor, skip=0, limit=50):
    cursor.execute("""
        SELECT f.fdc_id, f.food_name,
               fc.category_name AS food_category,
               b.brand_name
        FROM Foods f
        LEFT JOIN FOOD_CATEGORY fc ON f.category_id = fc.category_id
        LEFT JOIN Brands b         ON f.brand_id    = b.brand_id
        ORDER BY f.fdc_id
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """, (skip, limit))
    return cursor.fetchall()


def get_categories(conn, cursor):
    cursor.execute("""
        SELECT category_name
        FROM FOOD_CATEGORY
        ORDER BY category_name
    """)
    return [row["category_name"] for row in cursor.fetchall()]


def get_predictions(conn, cursor, limit=100):
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
    food = {
        "fdc_id": row["fdc_id"],
        "food_name": row["food_name"],
        "data_type": row.get("data_type"),
        "food_category": row.get("food_category"),
        "brand_id": row.get("brand_id"),
        "brand": None,
        "nutrition": None,
        "health_score": None,
        "allergen": None,
    }

    if row.get("brand_name"):
        food["brand"] = {
            "brand_id": row["brand_id"],
            "brand_name": row["brand_name"],
            "brand_owner": row.get("brand_owner"),
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

    if row.get("score_id"):
        food["health_score"] = {
            "score_id": row["score_id"],
            "fdc_id": row["fdc_id"],
            "health_score": row.get("health_score"),
            "nutriscore_grade": row.get("nutriscore_grade"),
            "nova_group": row.get("nova_group"),
        }

    if row.get("allergen_id"):
        food["allergen"] = {
            "allergen_id": row["allergen_id"],
            "fdc_id": row["fdc_id"],
            "contains_gluten": bool(row.get("contains_gluten")),
            "contains_dairy": bool(row.get("contains_dairy")),
        }

    return food
