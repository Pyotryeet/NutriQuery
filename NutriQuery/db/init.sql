CREATE DATABASE NutriQuery;
GO

USE NutriQuery;
GO

-- 1. Brands Table
CREATE TABLE Brands (
    brand_id INT IDENTITY(1,1) PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL,
    brand_owner VARCHAR(255)
);
GO

-- 2. Food Categories Table
CREATE TABLE FOOD_CATEGORY (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL UNIQUE
);
GO

-- 3. Data Types Table
CREATE TABLE DATA_TYPE (
    type_id INT IDENTITY(1,1) PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE
);
GO

-- 4. Foods Table
CREATE TABLE Foods (
    fdc_id INT PRIMARY KEY,
    brand_id INT,
    category_id INT,
    type_id INT,
    food_name VARCHAR(500) NOT NULL,
    CONSTRAINT fk_foods_brand FOREIGN KEY (brand_id) REFERENCES Brands(brand_id) ON DELETE SET NULL,
    CONSTRAINT fk_foods_category FOREIGN KEY (category_id) REFERENCES FOOD_CATEGORY(category_id),
    CONSTRAINT fk_foods_type FOREIGN KEY (type_id) REFERENCES DATA_TYPE(type_id)
);
GO

-- FK indexes on Foods (improves JOIN performance)
CREATE INDEX idx_foods_brand_id ON Foods(brand_id);
CREATE INDEX idx_foods_category_id ON Foods(category_id);
CREATE INDEX idx_foods_type_id ON Foods(type_id);
-- B-tree index on food_name; helps prefix searches (LIKE 'Apple%').
-- NOTE: leading-wildcard queries (LIKE '%Apple%') will still table-scan.
CREATE INDEX idx_foods_food_name ON Foods(food_name);
GO

-- 5. Nutrition_Metrics Table
CREATE TABLE Nutrition_Metrics (
    nutrition_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL UNIQUE,
    calories FLOAT,
    protein_g FLOAT,
    fat_g FLOAT,
    carbs_g FLOAT,
    sodium_mg FLOAT,
    CONSTRAINT fk_nutrition_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

-- 6. Health_Score Table
CREATE TABLE HEALTH_SCORE (
    score_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL UNIQUE,
    health_score FLOAT,
    nutriscore_grade VARCHAR(50),
    nova_group INT,
    CONSTRAINT fk_healthscore_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

-- 7. Allergen_Profile Table
CREATE TABLE ALLERGEN_PROFILE (
    allergen_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL UNIQUE,
    contains_gluten BIT DEFAULT 0,
    contains_dairy BIT DEFAULT 0,
    CONSTRAINT fk_allergen_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

-- 8. Prediction Models Table for Machine Learning Pipeline
-- NOTE: predicted_nova is always NULL — NOVA cannot be predicted from nutrition data.
-- The column is retained for backward compatibility; remove in a future migration.
CREATE TABLE ML_Predictions (
    prediction_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL,
    predicted_nutriscore VARCHAR(50),
    predicted_nova INT,
    confidence_score FLOAT,
    prediction_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_predictions_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

-- FK index on ML_Predictions
CREATE INDEX idx_ml_predictions_fdc_id ON ML_Predictions(fdc_id);
GO
