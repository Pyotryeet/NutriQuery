"""Inspect the MSSQL database structure on localhost:1433"""
import pymssql

# Connection parameters from backend/database.py
conn = pymssql.connect(
    server='127.0.0.1',
    port='1433',
    user='SA',
    password='MbLp6hezU8@',
    database='NutriQuery'
)

cursor = conn.cursor()

# 1. List all tables
print("=" * 80)
print("TABLES")
print("=" * 80)
cursor.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME
""")
tables = cursor.fetchall()
for schema, table in tables:
    print(f"  [{schema}].[{table}]")

# 2. For each table, get columns with PK/FK info
for schema, table in tables:
    print(f"\n{'='*60}")
    print(f"TABLE: [{schema}].[{table}]")
    print(f"{'='*60}")
    cursor.execute(f"""
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            COLUMNPROPERTY(OBJECT_ID('{schema}.{table}'), c.COLUMN_NAME, 'IsIdentity') as IS_IDENTITY,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PK' ELSE '' END as IS_PK
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON pk.TABLE_SCHEMA = c.TABLE_SCHEMA 
            AND pk.TABLE_NAME = c.TABLE_NAME 
            AND pk.COLUMN_NAME = c.COLUMN_NAME
        WHERE c.TABLE_SCHEMA = '{schema}' AND c.TABLE_NAME = '{table}'
        ORDER BY c.ORDINAL_POSITION
    """)
    for col in cursor.fetchall():
        col_name, dtype, max_len, num_prec, num_scale, nullable, default, is_ident, is_pk = col
        type_str = dtype
        if max_len and max_len > 0:
            type_str += f"({max_len})"
        elif max_len == -1:
            type_str += "(MAX)"
        elif num_prec:
            type_str += f"({num_prec})"
        pk_str = f" [PK]" if is_pk else ""
        ident_str = " [IDENTITY]" if is_ident else ""
        null_str = "NULL" if nullable == "YES" else "NOT NULL"
        def_str = f" DEFAULT {default}" if default else ""
        print(f"  {col_name:30s} {type_str:20s} {null_str:10s}{pk_str}{ident_str}{def_str}")

# 3. Foreign keys
print(f"\n{'='*60}")
print("FOREIGN KEYS")
print(f"{'='*60}")
cursor.execute("""
    SELECT 
        fk.name AS FK_Name,
        tp.name AS Parent_Table,
        cp.name AS Parent_Column,
        tr.name AS Referenced_Table,
        cr.name AS Referenced_Column,
        fk.delete_referential_action_desc AS On_Delete
    FROM sys.foreign_keys fk
    JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
    JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
    JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
    JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
    ORDER BY tp.name, fk.name
""")
for fk_name, parent, parent_col, ref, ref_col, on_del in cursor.fetchall():
    print(f"  {fk_name}: {parent}.{parent_col} -> {ref}.{ref_col}  ON DELETE {on_del}")

# 4. Row counts
print(f"\n{'='*60}")
print("ROW COUNTS")
print(f"{'='*60}")
for schema, table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}]")
    count = cursor.fetchone()[0]
    print(f"  [{schema}].[{table}]: {count} rows")

# 5. Sample data (3 rows per table)
print(f"\n{'='*60}")
print("SAMPLE DATA (3 rows each)")
print(f"{'='*60}")
cursor_dict = conn.cursor(as_dict=True)
for schema, table in tables:
    cursor_dict.execute(f"SELECT TOP 3 * FROM [{schema}].[{table}]")
    rows = cursor_dict.fetchall()
    print(f"\n  [{schema}].[{table}]:")
    for row in rows:
        print(f"    {dict(row)}")

# 6. Check for normalization issues
print(f"\n{'='*60}")
print("NORMALIZATION ANALYSIS")
print(f"{'='*60}")

# Check for duplicate data patterns
print("\n  -- Checking for repeated brand_owner per brand_name --")
cursor.execute("""
    SELECT brand_name, COUNT(DISTINCT brand_owner) as owner_variants
    FROM Brands
    GROUP BY brand_name
    HAVING COUNT(DISTINCT brand_owner) > 1
""")
rows = cursor.fetchall()
if rows:
    for r in rows:
        print(f"    brand_name='{r[0]}' has {r[1]} different owners")
else:
    print("    No brand_name with multiple owners found")

# Check for food_category distribution
print("\n  -- Food categories (potential separate entity?) --")
cursor.execute("""
    SELECT food_category, COUNT(*) as cnt
    FROM Foods
    WHERE food_category IS NOT NULL
    GROUP BY food_category
    ORDER BY cnt DESC
""")
for r in cursor.fetchall():
    print(f"    '{r[0]}': {r[1]} foods")

# Check 1:1 vs 1:N relationships
print("\n  -- Nutrition_Metrics per food (1:1 or 1:N?) --")
cursor.execute("""
    SELECT fdc_id, COUNT(*) as cnt
    FROM Nutrition_Metrics
    GROUP BY fdc_id
    HAVING COUNT(*) > 1
""")
rows = cursor.fetchall()
print(f"    Foods with multiple nutrition rows: {len(rows)}")

print("\n  -- Health_and_Allergens per food (1:1 or 1:N?) --")
cursor.execute("""
    SELECT fdc_id, COUNT(*) as cnt
    FROM Health_and_Allergens
    GROUP BY fdc_id
    HAVING COUNT(*) > 1
""")
rows = cursor.fetchall()
print(f"    Foods with multiple health rows: {len(rows)}")

print("\n  -- ML_Predictions per food (1:N?) --")
cursor.execute("""
    SELECT fdc_id, COUNT(*) as cnt
    FROM ML_Predictions
    GROUP BY fdc_id
    HAVING COUNT(*) > 1
""")
rows = cursor.fetchall()
print(f"    Foods with multiple predictions: {len(rows)}")

# Check if ecoscore_grade in Brands is functionally dependent on something else
print("\n  -- ecoscore_grade values in Brands --")
cursor.execute("""
    SELECT DISTINCT ecoscore_grade FROM Brands WHERE ecoscore_grade IS NOT NULL
""")
for r in cursor.fetchall():
    print(f"    '{r[0]}'")

# Check NULL counts
print("\n  -- NULL analysis per table --")
for schema, table in tables:
    cursor.execute(f"""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
        ORDER BY ORDINAL_POSITION
    """)
    cols = [r[0] for r in cursor.fetchall()]
    for col in cols:
        cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}] WHERE [{col}] IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}]")
            total = cursor.fetchone()[0]
            print(f"    {table}.{col}: {null_count}/{total} NULL ({100*null_count/total:.1f}%)")

conn.close()
print("\n\nDone.")
