CREATE DATABASE NutriQuery;
GO

USE NutriQuery;
GO

-- 1. Brands Table
CREATE TABLE Brands (
    brand_id INT IDENTITY(1,1) PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL,
    brand_owner VARCHAR(255),
    ecoscore_grade VARCHAR(50)
);
GO

-- 2. Foods Table
CREATE TABLE Foods (
    fdc_id INT PRIMARY KEY, -- USDA identifier
    brand_id INT,
    food_name VARCHAR(500) NOT NULL,
    data_type VARCHAR(100),
    food_category VARCHAR(255),
    CONSTRAINT fk_foods_brand FOREIGN KEY (brand_id) REFERENCES Brands(brand_id) ON DELETE SET NULL
);
GO

-- 3. Nutrition_Metrics Table
CREATE TABLE Nutrition_Metrics (
    nutrition_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL,
    calories FLOAT,
    protein_g FLOAT,
    fat_g FLOAT,
    carbs_g FLOAT,
    sodium_mg FLOAT,
    CONSTRAINT fk_nutrition_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

-- 4. Health_and_Allergens Table
CREATE TABLE Health_and_Allergens (
    profile_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL,
    contains_gluten BIT DEFAULT 0,
    contains_dairy BIT DEFAULT 0,
    health_score FLOAT,
    nutriscore_grade VARCHAR(50),
    nova_group INT,
    CONSTRAINT fk_health_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON DELETE CASCADE
);
GO

-- 5. Prediction Models Table for Machine Learning Pipeline (Requirement 9 & 10)
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
