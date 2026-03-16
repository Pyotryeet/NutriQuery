from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ── Brand ──────────────────────────────────────────────
class BrandBase(BaseModel):
    brand_name: str
    brand_owner: Optional[str] = None
    ecoscore_grade: Optional[str] = None


class BrandCreate(BrandBase):
    pass


class Brand(BrandBase):
    brand_id: int


# ── Nutrition ──────────────────────────────────────────
class NutritionBase(BaseModel):
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class Nutrition(NutritionBase):
    nutrition_id: int
    fdc_id: int


# ── Health & Allergens ─────────────────────────────────
class HealthBase(BaseModel):
    contains_gluten: bool = False
    contains_dairy: bool = False
    health_score: Optional[float] = None
    nutriscore_grade: Optional[str] = None
    nova_group: Optional[int] = None


class Health(HealthBase):
    profile_id: int
    fdc_id: int


# ── ML Predictions ─────────────────────────────────────
class MLPredictionBase(BaseModel):
    predicted_nutriscore: Optional[str] = None
    predicted_nova: Optional[int] = None
    confidence_score: Optional[float] = None


class MLPrediction(MLPredictionBase):
    prediction_id: int
    fdc_id: int
    prediction_date: Optional[datetime] = None


# ── Food ───────────────────────────────────────────────
class FoodBase(BaseModel):
    food_name: str
    data_type: Optional[str] = None
    food_category: Optional[str] = None


class Food(FoodBase):
    fdc_id: int
    brand_id: Optional[int] = None
    brand: Optional[Brand] = None
    nutrition: Optional[Nutrition] = None
    health: Optional[Health] = None
    predictions: List[MLPrediction] = []


class FoodSearchResult(BaseModel):
    fdc_id: int
    food_name: str
    food_category: Optional[str] = None
    brand_name: Optional[str] = None


# ── Aggregation ────────────────────────────────────────
class AggregationResult(BaseModel):
    food_category: str
    avg_calories: float
    avg_protein: float
    avg_fat: float
    avg_carbs: float
    item_count: int
