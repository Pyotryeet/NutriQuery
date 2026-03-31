"""
data_import.py — Imports data from the 5 real CSV files in data/raw/
into the MSSQL database using raw SQL INSERT statements via pymssql.
"""
import pandas as pd
import os
from database import get_connection

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

def import_all_data():
    """
    Master import function: loads the CSV files and populates
    Brands, Foods, Nutrition_Metrics, and Health_and_Allergens tables.
    Returns a summary dict.
    """
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    stats = {"brands": 0, "foods": 0, "nutrition": 0, "health": 0, "errors": []}

    try:
        # ---------- 1. comprehensive_foods_usda.csv ----------
        # Columns: fdc_id, food_name, data_type, food_category, brand_owner,
        #          brand_name, calories, carbs_g, fat_g, protein_g, sodium_mg,
        #          health_score, food_type, etc.
        usda_path = os.path.join(DATA_DIR, "comprehensive_foods_usda.csv")
        if os.path.exists(usda_path):
            print(f"Loading {usda_path}...")
            df = pd.read_csv(usda_path)
            df = df.where(pd.notnull(df), None)

            brand_cache = {}   # brand_name → brand_id

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

                    # — Food —
                    fdc_id = int(row["fdc_id"])
                    cursor.execute("SELECT fdc_id FROM Foods WHERE fdc_id = %s", (fdc_id,))
                    if cursor.fetchone() is None:
                        cursor.execute(
                            """INSERT INTO Foods (fdc_id, brand_id, food_name, data_type, food_category)
                               VALUES (%s, %s, %s, %s, %s)""",
                            (
                                fdc_id,
                                brand_id,
                                str(row["food_name"])[:500],
                                str(row.get("data_type") or "")[:100] or None,
                                str(row.get("food_category") or "")[:255] or None,
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

                    # — Health & Allergens (basic from USDA) —
                    cursor.execute(
                        "SELECT profile_id FROM Health_and_Allergens WHERE fdc_id = %s",
                        (fdc_id,),
                    )
                    if cursor.fetchone() is None:
                        cursor.execute(
                            """INSERT INTO Health_and_Allergens
                               (fdc_id, contains_gluten, contains_dairy, health_score)
                               VALUES (%s, %s, %s, %s)""",
                            (
                                fdc_id,
                                0,
                                0,
                                _safe_float(row.get("health_score")),
                            ),
                        )
                        stats["health"] += 1

                except Exception as row_err:
                    stats["errors"].append(f"Row {idx}: {str(row_err)[:120]}")

                if idx % 500 == 0:
                    conn.commit()
                    print(f"  USDA: {idx} rows processed...")

            conn.commit()
            print(f"  USDA import done: {stats['foods']} foods, {stats['brands']} brands")

        # ---------- 2. foods_health_scores_allergens.csv ----------
        # Columns: product_name, brands, nutriscore_grade, nova_group,
        #          ecoscore_grade, contains_gluten, contains_dairy, energy_kcal, etc.
        health_path = os.path.join(DATA_DIR, "foods_health_scores_allergens.csv")
        if os.path.exists(health_path):
            print(f"Loading {health_path}...")
            df_h = pd.read_csv(health_path)
            df_h = df_h.where(pd.notnull(df_h), None)

            updated = 0
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
                        ns_grade = row.get("nutriscore_grade")
                        if ns_grade and str(ns_grade).upper() in ("A", "B", "C", "D", "E"):
                            ns_grade = str(ns_grade).upper()
                        else:
                            ns_grade = None

                        nova = _safe_int(row.get("nova_group"))
                        gluten = 1 if str(row.get("contains_gluten", "")).lower() == "true" else 0
                        dairy = 1 if str(row.get("contains_dairy", "")).lower() == "true" else 0

                        cursor.execute(
                            """UPDATE Health_and_Allergens
                               SET nutriscore_grade = %s, nova_group = %s,
                                   contains_gluten = %s, contains_dairy = %s
                               WHERE fdc_id = %s""",
                            (ns_grade, nova, gluten, dairy, match["fdc_id"]),
                        )
                        updated += 1

                except Exception:
                    pass

                if idx % 500 == 0:
                    conn.commit()

            conn.commit()
            print(f"  Health scores enrichment done: {updated} records updated")

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
                   f"{stats['nutrition']} nutrition, {stats['health']} health records",
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
