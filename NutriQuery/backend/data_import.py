"""
data_import.py — Imports data from the 5 real CSV files in data/raw/
into the MSSQL 8-table 3NF schema using raw SQL INSERT statements via pymssql.
"""
import pandas as pd
import os
from database import get_connection

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

def import_all_data():
    """
    Master import function: loads the CSV files and populates
    Brands, FOOD_CATEGORY, DATA_TYPE, Foods, Nutrition_Metrics,
    HEALTH_SCORE, and ALLERGEN_PROFILE tables.
    Returns a summary dict.
    """
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    stats = {
        "brands": 0, "categories": 0, "data_types": 0,
        "foods": 0, "nutrition": 0, "health": 0, "allergens": 0,
        "errors": [],
    }

    try:
        # ---------- 1. comprehensive_foods_usda.csv ----------
        usda_path = os.path.join(DATA_DIR, "comprehensive_foods_usda.csv")
        if os.path.exists(usda_path):
            print(f"Loading {usda_path}...")
            df = pd.read_csv(usda_path)
            df = df.where(pd.notnull(df), None)

            brand_cache = {}     # brand_name → brand_id
            category_cache = {}  # category_name → category_id
            type_cache = {}      # type_name → type_id

            for idx, row in df.iterrows():
                try:
                    # — Brand (lookup-or-create) —
                    brand_id = None
                    bname = row.get("brand_name")
                    if bname and str(bname).strip():
                        bname = str(bname).strip()[:255]
                        if bname in brand_cache:
                            brand_id = brand_cache[bname]
                        else:
                            cursor.execute(
                                "SELECT brand_id FROM Brands WHERE brand_name = %s",
                                (bname,),
                            )
                            existing = cursor.fetchone()
                            if existing:
                                brand_id = existing["brand_id"]
                            else:
                                bowner = str(row.get("brand_owner") or "")[:255] or None
                                cursor.execute(
                                    "INSERT INTO Brands (brand_name, brand_owner) VALUES (%s, %s)",
                                    (bname, bowner),
                                )
                                cursor.execute("SELECT @@IDENTITY AS bid")
                                brand_id = int(cursor.fetchone()["bid"])
                                stats["brands"] += 1
                            brand_cache[bname] = brand_id

                    # — Food Category (lookup-or-create) —
                    category_id = None
                    cat_name = row.get("food_category")
                    if cat_name and str(cat_name).strip():
                        cat_name = str(cat_name).strip()[:255]
                        if cat_name in category_cache:
                            category_id = category_cache[cat_name]
                        else:
                            cursor.execute(
                                "SELECT category_id FROM FOOD_CATEGORY WHERE category_name = %s",
                                (cat_name,),
                            )
                            existing = cursor.fetchone()
                            if existing:
                                category_id = existing["category_id"]
                            else:
                                cursor.execute(
                                    "INSERT INTO FOOD_CATEGORY (category_name) VALUES (%s)",
                                    (cat_name,),
                                )
                                cursor.execute("SELECT @@IDENTITY AS cid")
                                category_id = int(cursor.fetchone()["cid"])
                                stats["categories"] += 1
                            category_cache[cat_name] = category_id

                    # — Data Type (lookup-or-create) —
                    type_id = None
                    dt_name = row.get("data_type")
                    if dt_name and str(dt_name).strip():
                        dt_name = str(dt_name).strip()[:100]
                        if dt_name in type_cache:
                            type_id = type_cache[dt_name]
                        else:
                            cursor.execute(
                                "SELECT type_id FROM DATA_TYPE WHERE type_name = %s",
                                (dt_name,),
                            )
                            existing = cursor.fetchone()
                            if existing:
                                type_id = existing["type_id"]
                            else:
                                cursor.execute(
                                    "INSERT INTO DATA_TYPE (type_name) VALUES (%s)",
                                    (dt_name,),
                                )
                                cursor.execute("SELECT @@IDENTITY AS tid")
                                type_id = int(cursor.fetchone()["tid"])
                                stats["data_types"] += 1
                            type_cache[dt_name] = type_id

                    # — Food —
                    fdc_id = int(row["fdc_id"])
                    cursor.execute("SELECT fdc_id FROM Foods WHERE fdc_id = %s", (fdc_id,))
                    if cursor.fetchone() is None:
                        cursor.execute(
                            """INSERT INTO Foods (fdc_id, brand_id, category_id, type_id, food_name)
                               VALUES (%s, %s, %s, %s, %s)""",
                            (
                                fdc_id,
                                brand_id,
                                category_id,
                                type_id,
                                str(row["food_name"])[:500],
                            ),
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
                            (
                                fdc_id,
                                _safe_float(row.get("calories")),
                                _safe_float(row.get("protein_g")),
                                _safe_float(row.get("fat_g")),
                                _safe_float(row.get("carbs_g")),
                                _safe_float(row.get("sodium_mg")),
                            ),
                        )
                        stats["nutrition"] += 1

                    # — Health Score —
                    cursor.execute(
                        "SELECT score_id FROM HEALTH_SCORE WHERE fdc_id = %s",
                        (fdc_id,),
                    )
                    if cursor.fetchone() is None:
                        cursor.execute(
                            """INSERT INTO HEALTH_SCORE
                               (fdc_id, health_score)
                               VALUES (%s, %s)""",
                            (
                                fdc_id,
                                _safe_float(row.get("health_score")),
                            ),
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

                except Exception as row_err:
                    stats["errors"].append(f"Row {idx}: {str(row_err)[:120]}")

                if idx % 500 == 0:
                    conn.commit()
                    print(f"  USDA: {idx} rows processed...")

            conn.commit()
            print(f"  USDA import done: {stats['foods']} foods, "
                  f"{stats['brands']} brands, {stats['categories']} categories, "
                  f"{stats['data_types']} data types")

        # ---------- 2. foods_health_scores_allergens.csv ----------
        health_path = os.path.join(DATA_DIR, "foods_health_scores_allergens.csv")
        if os.path.exists(health_path):
            print(f"Loading {health_path}...")
            df_h = pd.read_csv(health_path)
            df_h = df_h.where(pd.notnull(df_h), None)

            health_updated = 0
            allergen_updated = 0
            for idx, row in df_h.iterrows():
                try:
                    pname = row.get("product_name")
                    if not pname:
                        continue

                    # Try to find matching food by name
                    cursor.execute(
                        "SELECT TOP 1 fdc_id FROM Foods WHERE food_name LIKE %s",
                        (str(pname)[:100] + "%",),
                    )
                    match = cursor.fetchone()
                    if match:
                        # Update HEALTH_SCORE
                        ns_grade = row.get("nutriscore_grade")
                        if ns_grade and str(ns_grade).upper() in ("A", "B", "C", "D", "E"):
                            ns_grade = str(ns_grade).upper()
                        else:
                            ns_grade = None

                        nova = _safe_int(row.get("nova_group"))

                        cursor.execute(
                            """UPDATE HEALTH_SCORE
                               SET nutriscore_grade = %s, nova_group = %s
                               WHERE fdc_id = %s""",
                            (ns_grade, nova, match["fdc_id"]),
                        )
                        if cursor.rowcount > 0:
                            health_updated += 1

                        # Update ALLERGEN_PROFILE
                        gluten = 1 if str(row.get("contains_gluten", "")).lower() == "true" else 0
                        dairy = 1 if str(row.get("contains_dairy", "")).lower() == "true" else 0

                        cursor.execute(
                            """UPDATE ALLERGEN_PROFILE
                               SET contains_gluten = %s, contains_dairy = %s
                               WHERE fdc_id = %s""",
                            (gluten, dairy, match["fdc_id"]),
                        )
                        if cursor.rowcount > 0:
                            allergen_updated += 1

                except Exception:
                    pass

                if idx % 500 == 0:
                    conn.commit()

            conn.commit()
            print(f"  Health scores enrichment done: {health_updated} records updated")
            print(f"  Allergen profile enrichment done: {allergen_updated} records updated")

        conn.commit()
        print("All imports complete!")

    except Exception as e:
        stats["errors"].append(f"Fatal: {str(e)[:200]}")
        conn.rollback()
        print(f"Import error: {e}")

    finally:
        cursor.close()
        conn.close()

    return {
        "message": f"Import complete: {stats['foods']} foods, {stats['brands']} brands, "
                   f"{stats['categories']} categories, {stats['data_types']} data types, "
                   f"{stats['nutrition']} nutrition, {stats['health']} health scores, "
                   f"{stats['allergens']} allergen profiles",
        "stats": stats,
    }


def _safe_float(val):
    """Convert a value to float, return None if not possible."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if not pd.isna(f) else None
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """Convert a value to int, return None if not possible."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    result = import_all_data()
    print(result)
