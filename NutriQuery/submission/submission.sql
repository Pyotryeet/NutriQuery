-- Dialect : MsSQL
-- Team Members : Yigit Aydogan (150230208) , Emir Mete Donmez (150220205)
-- ====================================================================================================

-- TABLE 1: Brands
-- Owner : Emir Mete Donmez
-- Non-key columns : brand_name, brand_owner, ecoscore_grade (3 cols)
-- Foreign Keys : 0
-- ====================================================================================================
CREATE TABLE Brands (
    brand_id INT IDENTITY(1,1) PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL,
    brand_owner VARCHAR(255),
    ecoscore_grade VARCHAR(50)
);

-- TABLE 2: Foods
-- Owner : Emir Mete Donmez
-- Non-key columns : food_name, data_type, food_category (3 cols)
-- Foreign Keys : 1
-- ====================================================================================================
CREATE TABLE Foods (
    fdc_id INT PRIMARY KEY,
    brand_id INT,
    food_name VARCHAR(500) NOT NULL,
    data_type VARCHAR(100),
    food_category VARCHAR(255),
    CONSTRAINT fk_foods_brand FOREIGN KEY (brand_id) REFERENCES Brands(brand_id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- TABLE 3: Nutrition_Metrics
-- Owner : Yigit Aydogan
-- Non-key columns : calories, protein_g, fat_g, carbs_g, sodium_mg (5 cols)
-- Foreign Keys : 1
-- ====================================================================================================
CREATE TABLE Nutrition_Metrics (
    nutrition_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL,
    calories FLOAT,
    protein_g FLOAT,
    fat_g FLOAT,
    carbs_g FLOAT,
    sodium_mg FLOAT,
    CONSTRAINT fk_nutrition_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- TABLE 4: Health_and_Allergens
-- Owner : Yigit Aydogan
-- Non-key columns : contains_gluten, contains_dairy, health_score, nutriscore_grade, nova_group (5 cols)
-- Foreign Keys : 1
-- ====================================================================================================
CREATE TABLE Health_and_Allergens (
    profile_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL,
    contains_gluten BIT DEFAULT 0,
    contains_dairy BIT DEFAULT 0,
    health_score FLOAT,
    nutriscore_grade VARCHAR(50),
    nova_group INT,
    CONSTRAINT fk_health_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- TABLE 5: ML_Predictions
-- Owner : Yigit Aydogan
-- Non-key columns : predicted_nutriscore, predicted_nova, confidence_score, prediction_date (4 cols)
-- Foreign Keys : 1
-- ====================================================================================================
CREATE TABLE ML_Predictions (
    prediction_id INT IDENTITY(1,1) PRIMARY KEY,
    fdc_id INT NOT NULL,
    predicted_nutriscore VARCHAR(50),
    predicted_nova INT,
    confidence_score FLOAT,
    prediction_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_predictions_foods FOREIGN KEY (fdc_id) REFERENCES Foods(fdc_id) ON UPDATE CASCADE ON DELETE CASCADE
);
