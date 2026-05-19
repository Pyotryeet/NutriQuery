USE NutriQuery;
GO

PRINT '1. Dropping ecoscore_grade from Brands';
IF COL_LENGTH('Brands', 'ecoscore_grade') IS NOT NULL
BEGIN
    ALTER TABLE Brands DROP COLUMN ecoscore_grade;
END
GO

PRINT '2. Creating FOOD_CATEGORY and DATA_TYPE tables';
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='FOOD_CATEGORY')
CREATE TABLE FOOD_CATEGORY (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL UNIQUE
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='DATA_TYPE')
CREATE TABLE DATA_TYPE (
    type_id INT IDENTITY(1,1) PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE
);
GO

PRINT '3. Migrating distinct category and type strings';
INSERT INTO FOOD_CATEGORY (category_name)
SELECT DISTINCT food_category FROM Foods WHERE food_category IS NOT NULL
AND food_category NOT IN (SELECT category_name FROM FOOD_CATEGORY);
GO

INSERT INTO DATA_TYPE (type_name)
SELECT DISTINCT data_type FROM Foods WHERE data_type IS NOT NULL
AND data_type NOT IN (SELECT type_name FROM DATA_TYPE);
GO

PRINT '4. Altering Foods table with category_id and type_id';
IF COL_LENGTH('Foods', 'category_id') IS NULL
BEGIN
    ALTER TABLE Foods ADD category_id INT;
END
IF COL_LENGTH('Foods', 'type_id') IS NULL
BEGIN
    ALTER TABLE Foods ADD type_id INT;
END
GO

UPDATE f
SET f.category_id = c.category_id
FROM Foods f
JOIN FOOD_CATEGORY c ON f.food_category = c.category_name
WHERE f.category_id IS NULL;
GO

UPDATE f
SET f.type_id = d.type_id
FROM Foods f
JOIN DATA_TYPE d ON f.data_type = d.type_name
WHERE f.type_id IS NULL;
GO

IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Foods_Category')
BEGIN
    ALTER TABLE Foods ADD CONSTRAINT FK_Foods_Category FOREIGN KEY (category_id) REFERENCES FOOD_CATEGORY(category_id);
END
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Foods_DataType')
BEGIN
    ALTER TABLE Foods ADD CONSTRAINT FK_Foods_DataType FOREIGN KEY (type_id) REFERENCES DATA_TYPE(type_id);
END
GO

PRINT 'Dropping old columns from Foods';
IF COL_LENGTH('Foods', 'food_category') IS NOT NULL
BEGIN
    ALTER TABLE Foods DROP COLUMN food_category;
END
IF COL_LENGTH('Foods', 'data_type') IS NOT NULL
BEGIN
    ALTER TABLE Foods DROP COLUMN data_type;
END
GO

PRINT '5. Creating HEALTH_SCORE and ALLERGEN_PROFILE tables';
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='HEALTH_SCORE')
CREATE TABLE HEALTH_SCORE (
    score_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL UNIQUE,
    health_score FLOAT NULL,
    nutriscore_grade VARCHAR(50) NULL,
    nova_group INT NULL,
    CONSTRAINT FK_HealthScore_Food FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='ALLERGEN_PROFILE')
CREATE TABLE ALLERGEN_PROFILE (
    allergen_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL UNIQUE,
    contains_gluten BIT DEFAULT 0,
    contains_dairy BIT DEFAULT 0,
    CONSTRAINT FK_Allergen_Food FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

PRINT '6. Migrating data from Health_and_Allergens';
IF EXISTS (SELECT * FROM sys.tables WHERE name='Health_and_Allergens')
BEGIN
    INSERT INTO HEALTH_SCORE (fdc_id, health_score, nutriscore_grade, nova_group)
    SELECT fdc_id, health_score, nutriscore_grade, nova_group
    FROM Health_and_Allergens
    WHERE fdc_id NOT IN (SELECT fdc_id FROM HEALTH_SCORE);

    INSERT INTO ALLERGEN_PROFILE (fdc_id, contains_gluten, contains_dairy)
    SELECT fdc_id, contains_gluten, contains_dairy
    FROM Health_and_Allergens
    WHERE fdc_id NOT IN (SELECT fdc_id FROM ALLERGEN_PROFILE);
    
    PRINT '7. Dropping Health_and_Allergens';
    DROP TABLE Health_and_Allergens;
END
GO

PRINT 'Migration complete.';
GO
