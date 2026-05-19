import pymssql

conn = pymssql.connect(
    server='127.0.0.1',
    port='1433',
    user='SA',
    password='MbLp6hezU8@',
    database='NutriQuery',
    autocommit=True
)

cursor = conn.cursor()

print("Starting migrations...")

# 1. Drop ecoscore_grade from Brands
print("Dropping ecoscore_grade from Brands...")
try:
    cursor.execute("ALTER TABLE Brands DROP COLUMN ecoscore_grade")
    print("Dropped ecoscore_grade.")
except Exception as e:
    print("Warning or already dropped:", e)

# 2. Create FOOD_CATEGORY and DATA_TYPE tables
print("Creating FOOD_CATEGORY and DATA_TYPE...")
cursor.execute("""
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='FOOD_CATEGORY')
CREATE TABLE FOOD_CATEGORY (
    category_id INT IDENTITY PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL UNIQUE
)
""")

cursor.execute("""
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='DATA_TYPE')
CREATE TABLE DATA_TYPE (
    type_id INT IDENTITY PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE
)
""")

# 3. Migrate distinct strings from Foods
print("Migrating category and type data...")
cursor.execute("""
INSERT INTO FOOD_CATEGORY (category_name)
SELECT DISTINCT food_category FROM Foods WHERE food_category IS NOT NULL
AND food_category NOT IN (SELECT category_name FROM FOOD_CATEGORY)
""")

cursor.execute("""
INSERT INTO DATA_TYPE (type_name)
SELECT DISTINCT data_type FROM Foods WHERE data_type IS NOT NULL
AND data_type NOT IN (SELECT type_name FROM DATA_TYPE)
""")

# 4. Alter Foods table: Add FK columns, update them, and drop old strings
print("Adding category_id and type_id to Foods...")
try:
    cursor.execute("ALTER TABLE Foods ADD category_id INT")
    cursor.execute("ALTER TABLE Foods ADD type_id INT")
except Exception as e:
    print("Columns may already exist:", e)

print("Updating Foods with category_id and type_id...")
cursor.execute("""
UPDATE f
SET f.category_id = c.category_id
FROM Foods f
JOIN FOOD_CATEGORY c ON f.food_category = c.category_name
""")

cursor.execute("""
UPDATE f
SET f.type_id = d.type_id
FROM Foods f
JOIN DATA_TYPE d ON f.data_type = d.type_name
""")

print("Adding FK constraints to Foods...")
try:
    cursor.execute("ALTER TABLE Foods ADD CONSTRAINT FK_Foods_Category FOREIGN KEY (category_id) REFERENCES FOOD_CATEGORY(category_id)")
    cursor.execute("ALTER TABLE Foods ADD CONSTRAINT FK_Foods_DataType FOREIGN KEY (type_id) REFERENCES DATA_TYPE(type_id)")
except Exception as e:
    print("Constraints may already exist:", e)

print("Dropping old columns from Foods...")
try:
    cursor.execute("ALTER TABLE Foods DROP COLUMN food_category")
    cursor.execute("ALTER TABLE Foods DROP COLUMN data_type")
except Exception as e:
    print("Old columns may already be dropped:", e)

# 5. Create HEALTH_SCORE and ALLERGEN_PROFILE tables
print("Creating HEALTH_SCORE and ALLERGEN_PROFILE...")
cursor.execute("""
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='HEALTH_SCORE')
CREATE TABLE HEALTH_SCORE (
    score_id INT IDENTITY PRIMARY KEY,
    fdc_id INT NOT NULL UNIQUE,
    health_score FLOAT NULL,
    nutriscore_grade VARCHAR(50) NULL,
    nova_group INT NULL,
    CONSTRAINT FK_HealthScore_Food FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id)
)
""")

cursor.execute("""
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='ALLERGEN_PROFILE')
CREATE TABLE ALLERGEN_PROFILE (
    allergen_id INT IDENTITY PRIMARY KEY,
    fdc_id INT NOT NULL UNIQUE,
    contains_gluten BIT DEFAULT 0,
    contains_dairy BIT DEFAULT 0,
    CONSTRAINT FK_Allergen_Food FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id)
)
""")

# 6. Migrate data from Health_and_Allergens
print("Migrating data from Health_and_Allergens...")
try:
    cursor.execute("""
    INSERT INTO HEALTH_SCORE (fdc_id, health_score, nutriscore_grade, nova_group)
    SELECT fdc_id, health_score, nutriscore_grade, nova_group
    FROM Health_and_Allergens
    WHERE fdc_id NOT IN (SELECT fdc_id FROM HEALTH_SCORE)
    """)
    
    cursor.execute("""
    INSERT INTO ALLERGEN_PROFILE (fdc_id, contains_gluten, contains_dairy)
    SELECT fdc_id, contains_gluten, contains_dairy
    FROM Health_and_Allergens
    WHERE fdc_id NOT IN (SELECT fdc_id FROM ALLERGEN_PROFILE)
    """)
    
    print("Dropping Health_and_Allergens...")
    cursor.execute("DROP TABLE Health_and_Allergens")
except Exception as e:
    print("Health_and_Allergens migration issue or already dropped:", e)

print("Migration completed successfully!")
conn.close()
