"""
data_import.py — Imports data from CSV files in data/raw/
into the MSSQL 8-table 3NF schema using raw SQL INSERT via pymssql.

Structure:
  import_all_data()          — orchestrator
  _load_usda_csv()           — comprehensive_foods_usda.csv
  _load_health_csv()         — foods_health_scores_allergens.csv enrichment
  _resolve_or_create()       — generic lookup-or-create (brands, categories, types)
  _safe_float() / _safe_int() — value coercion helpers
"""
import csv
import os
import logging
import pymssql
from database import get_connection

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")


# ── Value Helpers ────────────────────────────────────
def _safe_float(val):
    if val is None or val == "":
        return None
    try:
        f = float(val)
        return f if abs(f) != float('inf') else None
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    if val is None or val == "":
        return None
    try:
        f = float(val)
        if abs(f) == float('inf'):
            return None
        return int(f)
    except (ValueError, TypeError, OverflowError):
        return None


# ── Generic Lookup-or-Create ─────────────────────────
def _resolve_or_create(cursor, cache, table, id_col, name_col, name_value, extra_cols=None):
    """
    Look up a name in a lookup table; insert it if not found.
    Returns the id (INT). Updates the cache dict in-place.

    cache: dict mapping name → id
    table: e.g. 'Brands', 'FOOD_CATEGORY', 'DATA_TYPE'
    id_col: e.g. 'brand_id', 'category_id', 'type_id'
    name_col: e.g. 'brand_name', 'category_name', 'type_name'
    extra_cols: optional dict of {col_name: value} for INSERT (e.g. brand_owner)
    """
    if name_value in cache:
        return cache[name_value]

    cursor.execute(
        f"SELECT {id_col} FROM {table} WHERE {name_col} = %s",
        (name_value,),
    )
    existing = cursor.fetchone()
    if existing:
        cache[name_value] = existing[id_col]
        return existing[id_col]

    if extra_cols:
        cols = [name_col] + list(extra_cols.keys())
        placeholders = ["%s"] * len(cols)
        values = [name_value] + list(extra_cols.values())
        cursor.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
            tuple(values),
        )
    else:
        cursor.execute(
            f"INSERT INTO {table} ({name_col}) VALUES (%s)",
            (name_value,),
        )
    cursor.execute("SELECT @@IDENTITY AS new_id")
    new_id = int(cursor.fetchone()["new_id"])
    cache[name_value] = new_id
    return new_id


# ── USDA CSV Import ──────────────────────────────────
def _load_usda_csv(conn, cursor, stats):
    """
    Load comprehensive_foods_usda.csv into the 3NF schema.

    Uses SELECT-before-INSERT for idempotency (safe to re-run).
    For bulk imports on large datasets, consider INSERT WHERE NOT EXISTS
    or MERGE to reduce round trips (~240K SELECTs for 40K rows).
    """
    usda_path = os.path.join(DATA_DIR, "comprehensive_foods_usda.csv")
    if not os.path.exists(usda_path):
        logger.warning("USDA CSV not found at %s", usda_path)
        return

    logger.info("Loading %s ...", usda_path)

    brand_cache = {}
    category_cache = {}
    type_cache = {}

    with open(usda_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader):
            try:
                fdc_id = int(row["fdc_id"])

                # — Brand —
                brand_id = None
                bname = (row.get("brand_name") or "").strip()[:255]
                if bname:
                    brand_owner = (row.get("brand_owner") or "").strip()[:255] or None
                    is_new = bname not in brand_cache
                    brand_id = _resolve_or_create(
                        cursor, brand_cache,
                        "Brands", "brand_id", "brand_name", bname,
                        extra_cols={"brand_owner": brand_owner} if brand_owner else None,
                    )
                    if is_new:
                        stats["brands"] += 1

                # — Food Category —
                category_id = None
                cat_name = (row.get("food_category") or "").strip()[:255]
                if cat_name:
                    is_new = cat_name not in category_cache
                    category_id = _resolve_or_create(
                        cursor, category_cache,
                        "FOOD_CATEGORY", "category_id", "category_name", cat_name,
                    )
                    if is_new:
                        stats["categories"] += 1

                # — Data Type —
                type_id = None
                dt_name = (row.get("data_type") or "").strip()[:100]
                if dt_name:
                    is_new = dt_name not in type_cache
                    type_id = _resolve_or_create(
                        cursor, type_cache,
                        "DATA_TYPE", "type_id", "type_name", dt_name,
                    )
                    if is_new:
                        stats["data_types"] += 1

                # — Food —
                cursor.execute(
                    "SELECT fdc_id FROM Foods WHERE fdc_id = %s", (fdc_id,),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        """INSERT INTO Foods (fdc_id, brand_id, category_id, type_id, food_name)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (fdc_id, brand_id, category_id, type_id,
                         (row.get("food_name") or "")[:500]),
                    )
                    stats["foods"] += 1

                # — Nutrition Metrics —
                cursor.execute(
                    "SELECT nutrition_id FROM Nutrition_Metrics WHERE fdc_id = %s",
                    (fdc_id,),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        """INSERT INTO Nutrition_Metrics
                           (fdc_id, calories, protein_g, fat_g, carbs_g, sodium_mg)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (fdc_id,
                         _safe_float(row.get("calories")),
                         _safe_float(row.get("protein_g")),
                         _safe_float(row.get("fat_g")),
                         _safe_float(row.get("carbs_g")),
                         _safe_float(row.get("sodium_mg"))),
                    )
                    stats["nutrition"] += 1

                # — Health Score —
                cursor.execute(
                    "SELECT score_id FROM HEALTH_SCORE WHERE fdc_id = %s",
                    (fdc_id,),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        """INSERT INTO HEALTH_SCORE (fdc_id, health_score)
                           VALUES (%s, %s)""",
                        (fdc_id, _safe_float(row.get("health_score"))),
                    )
                    stats["health"] += 1

                # — Allergen Profile —
                cursor.execute(
                    "SELECT allergen_id FROM ALLERGEN_PROFILE WHERE fdc_id = %s",
                    (fdc_id,),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        """INSERT INTO ALLERGEN_PROFILE
                           (fdc_id, contains_gluten, contains_dairy)
                           VALUES (%s, 0, 0)""",
                        (fdc_id,),
                    )
                    stats["allergens"] += 1

            except (ValueError, KeyError, TypeError, pymssql.Error) as row_err:
                stats["errors"].append(
                    f"Row {idx} (fdc_id={row.get('fdc_id', '?')}): {str(row_err)[:120]}"
                )

            if idx % 500 == 0:
                conn.commit()
                logger.info("  USDA: %d rows processed...", idx)

    conn.commit()
    logger.info(
        "USDA import done: %d foods, %d brands, %d categories, %d data types",
        stats["foods"], stats["brands"], stats["categories"], stats["data_types"],
    )


# ── Health/Allergen Enrichment ───────────────────────
def _load_health_csv(conn, cursor):
    """
    Enrich HEALTH_SCORE and ALLERGEN_PROFILE with data from
    foods_health_scores_allergens.csv.

    Matches by product_name → food_name (LIKE prefix, shortest match preferred).
    """
    health_path = os.path.join(DATA_DIR, "foods_health_scores_allergens.csv")
    if not os.path.exists(health_path):
        logger.warning("Health CSV not found at %s", health_path)
        return 0, 0

    logger.info("Loading %s ...", health_path)

    health_updated = 0
    allergen_updated = 0

    with open(health_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader):
            try:
                pname = (row.get("product_name") or "").strip()
                if not pname:
                    continue

                # Match by shortest food_name that starts with the product name.
                # ORDER BY LEN(food_name) ASC, food_name ASC makes this deterministic
                # — "Apple" matches before "Apple pie filling".
                cursor.execute(
                    """SELECT TOP 1 fdc_id
                       FROM Foods
                       WHERE food_name LIKE %s
                       ORDER BY LEN(food_name) ASC, food_name ASC""",
                    (pname[:100] + "%",),
                )
                match = cursor.fetchone()
                if not match:
                    continue

                # — Update HEALTH_SCORE —
                ns_raw = (row.get("nutriscore_grade") or "").strip().upper()
                ns_grade = ns_raw if ns_raw in ("A", "B", "C", "D", "E") else None
                nova = _safe_int(row.get("nova_group"))

                cursor.execute(
                    """UPDATE HEALTH_SCORE
                       SET nutriscore_grade = %s, nova_group = %s
                       WHERE fdc_id = %s""",
                    (ns_grade, nova, match["fdc_id"]),
                )
                if cursor.rowcount > 0:
                    health_updated += 1

                # — Update ALLERGEN_PROFILE —
                gluten = 1 if (row.get("contains_gluten") or "").strip().lower() == "true" else 0
                dairy = 1 if (row.get("contains_dairy") or "").strip().lower() == "true" else 0

                cursor.execute(
                    """UPDATE ALLERGEN_PROFILE
                       SET contains_gluten = %s, contains_dairy = %s
                       WHERE fdc_id = %s""",
                    (gluten, dairy, match["fdc_id"]),
                )
                if cursor.rowcount > 0:
                    allergen_updated += 1

            except (ValueError, KeyError, TypeError, pymssql.Error) as row_err:
                logger.debug("Health enrichment row %d skipped: %s", idx, str(row_err)[:100])

            if idx % 500 == 0:
                conn.commit()

    conn.commit()
    logger.info("Health scores enrichment: %d records updated", health_updated)
    logger.info("Allergen profile enrichment: %d records updated", allergen_updated)
    return health_updated, allergen_updated


# ── Orchestrator ─────────────────────────────────────
def import_all_data():
    """
    Master import function: loads CSV files and populates all 8 tables
    of the 3NF schema. Returns a summary dict.
    """
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    stats = {
        "brands": 0, "categories": 0, "data_types": 0,
        "foods": 0, "nutrition": 0, "health": 0, "allergens": 0,
        "health_enriched": 0, "allergen_enriched": 0,
        "errors": [],
    }

    try:
        _load_usda_csv(conn, cursor, stats)
        enriched_health, enriched_allergens = _load_health_csv(conn, cursor)
        stats["health_enriched"] = enriched_health
        stats["allergen_enriched"] = enriched_allergens
        conn.commit()
        logger.info("All imports complete!")

    except Exception as e:
        stats["errors"].append(f"Fatal: {str(e)[:200]}")
        try:
            conn.rollback()
        except Exception:
            pass  # Connection may already be dead
        logger.error("Import error: %s", e)

    finally:
        cursor.close()
        conn.close()

    return {
        "message": (
            f"Import complete: {stats['foods']} foods, {stats['brands']} brands, "
            f"{stats['categories']} categories, {stats['data_types']} data types, "
            f"{stats['nutrition']} nutrition, {stats['health']} health scores, "
            f"{stats['allergens']} allergen profiles, "
            f"{stats['health_enriched']} health enriched, "
            f"{stats['allergen_enriched']} allergens enriched"
        ),
        "stats": stats,
    }


if __name__ == "__main__":
    result = import_all_data()
    logger.info("%s", result["message"])
