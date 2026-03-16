"""
ml_service.py — PyTorch-based ML inference for Nutri-Score and NOVA prediction.
Uses raw SQL via pymssql — no ORM.
"""
import torch
import torch.nn as nn
import numpy as np
from fastapi import APIRouter, Depends
from typing import Annotated
from database import get_db
import logging

# ── Device Selection ──────────────────────────────────
if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"ML device: {device}")

DbDep = Annotated[tuple, Depends(get_db)]


# ── Neural Network Model ─────────────────────────────
class NutriScorePredictor(nn.Module):
    """Simple feed-forward classifier: nutrition features → Nutri-Score (A-E)."""

    def __init__(self, input_size=5, num_classes=5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, num_classes),
        )

    def forward(self, x):
        return self.net(x)


# Global model instance
model = NutriScorePredictor(input_size=5, num_classes=5).to(device)

NUTRISCORE_LABELS = ["A", "B", "C", "D", "E"]


def _train_model(cursor):
    """
    Train the model on labelled data from the database.
    Uses foods that already have a nutriscore_grade assigned.
    """
    cursor.execute("""
        SELECT n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg,
               h.nutriscore_grade
        FROM Nutrition_Metrics n
        JOIN Health_and_Allergens h ON n.fdc_id = h.fdc_id
        WHERE h.nutriscore_grade IS NOT NULL
          AND h.nutriscore_grade IN ('A', 'B', 'C', 'D', 'E')
          AND n.calories IS NOT NULL
          AND n.protein_g IS NOT NULL
          AND n.fat_g IS NOT NULL
          AND n.carbs_g IS NOT NULL
          AND n.sodium_mg IS NOT NULL
    """)
    rows = cursor.fetchall()

    if len(rows) < 10:
        logger.warning("Not enough labelled data to train — using random weights.")
        return False

    label_map = {v: i for i, v in enumerate(NUTRISCORE_LABELS)}
    features = []
    labels = []
    for r in rows:
        features.append([
            r["calories"] or 0, r["protein_g"] or 0, r["fat_g"] or 0,
            r["carbs_g"] or 0, r["sodium_mg"] or 0,
        ])
        labels.append(label_map[r["nutriscore_grade"]])

    X = torch.tensor(features, dtype=torch.float32).to(device)
    y = torch.tensor(labels, dtype=torch.long).to(device)

    # Normalize features
    mean = X.mean(dim=0)
    std = X.std(dim=0) + 1e-8
    X = (X - mean) / std

    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(100):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()

    logger.info(f"Training complete — final loss: {loss.item():.4f}  ({len(rows)} samples)")
    model._feature_mean = mean
    model._feature_std = std
    return True


def run_inference_and_store(conn, cursor):
    """
    Requirement 9: Run inference on all food records and store predictions
    in the ML_Predictions table using raw SQL INSERT.
    """
    trained = _train_model(cursor)

    cursor.execute("""
        SELECT f.fdc_id,
               n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg
        FROM Foods f
        JOIN Nutrition_Metrics n ON f.fdc_id = n.fdc_id
        WHERE n.calories IS NOT NULL
    """)
    rows = cursor.fetchall()

    if not rows:
        return {"message": "No data available for inference"}

    # Clear old predictions
    cursor.execute("DELETE FROM ML_Predictions")
    conn.commit()

    model.eval()
    count = 0

    with torch.no_grad():
        for row in rows:
            features = torch.tensor([[
                row["calories"] or 0, row["protein_g"] or 0, row["fat_g"] or 0,
                row["carbs_g"] or 0, row["sodium_mg"] or 0,
            ]], dtype=torch.float32).to(device)

            # Apply saved normalization if model was trained
            if trained and hasattr(model, "_feature_mean"):
                features = (features - model._feature_mean) / model._feature_std

            outputs = model(features)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probs, 1)

            predicted_score = NUTRISCORE_LABELS[predicted_idx.item()]
            nova_group = 1 if (row["calories"] or 0) < 100 else (2 if (row["calories"] or 0) < 250 else (3 if (row["calories"] or 0) < 400 else 4))

            cursor.execute(
                """INSERT INTO ML_Predictions
                   (fdc_id, predicted_nutriscore, predicted_nova, confidence_score)
                   VALUES (%s, %s, %s, %s)""",
                (row["fdc_id"], predicted_score, nova_group, round(confidence.item(), 4)),
            )
            count += 1

            if count % 500 == 0:
                conn.commit()

    conn.commit()
    return {
        "message": f"Generated {count} predictions on {str(device).upper()}",
        "device": str(device),
        "trained": trained,
    }


def delete_predictions(conn, cursor):
    """Requirement 10: Delete all prediction records."""
    cursor.execute("SELECT COUNT(*) AS cnt FROM ML_Predictions")
    count = cursor.fetchone()["cnt"]
    cursor.execute("DELETE FROM ML_Predictions")
    conn.commit()
    return {"message": f"Deleted {count} prediction records"}


# ── FastAPI Router ────────────────────────────────────
ml_router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@ml_router.post("/predict")
def generate_predictions(db: DbDep):
    conn, cursor = db
    return run_inference_and_store(conn, cursor)


@ml_router.delete("/predictions")
def clear_predictions(db: DbDep):
    conn, cursor = db
    return delete_predictions(conn, cursor)


@ml_router.get("/device")
def get_device():
    return {"device": str(device)}
