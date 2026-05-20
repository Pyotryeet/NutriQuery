"""
ml_service.py — PyTorch-based ML inference for Nutri-Score prediction.
Uses raw SQL via pymssql.

Note: NOVA group classification cannot be reliably predicted from nutrition
features alone (calories, protein, fat, carbs, sodium) — NOVA measures food
processing level, not nutritional composition. The `predicted_nova` column is
set to NULL to reflect this. A diet soda (0 cal) is NOVA 4; a raw avocado
(high cal) is NOVA 1. Training a model on nutrition data to predict NOVA
would produce systematically invalid results.
"""
import torch
import torch.nn as nn
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from database import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DbDep = Annotated[tuple, Depends(get_db)]

_device = None


def _get_device():
    """Lazily detect and cache the best available compute device."""
    global _device
    if _device is None:
        if torch.cuda.is_available():
            _device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            _device = torch.device("mps")
        else:
            _device = torch.device("cpu")
        logger.info("ML device: %s", _device)
    return _device


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
        self._feature_mean = None
        self._feature_std = None

    def forward(self, x):
        return self.net(x)


NUTRISCORE_LABELS = ["A", "B", "C", "D", "E"]
MAX_EPOCHS = 200


def _compute_normalization_stats(cursor):
    """
    Compute mean and std from ALL foods with complete nutrition data.
    Using the full dataset for normalization ensures training and inference
    use the same statistics.

    NOTE: Builds a full tensor in memory. At 40K rows this is ~800 KB;
    at 10M+ rows consider incremental Welford's algorithm or batch processing.
    """
    cursor.execute("""
        SELECT n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg
        FROM Nutrition_Metrics n
        WHERE n.calories IS NOT NULL
          AND n.protein_g IS NOT NULL
          AND n.fat_g IS NOT NULL
          AND n.carbs_g IS NOT NULL
          AND n.sodium_mg IS NOT NULL
    """)
    rows = cursor.fetchall()
    if not rows:
        return None, None

    features = torch.tensor(
        [[r["calories"] or 0, r["protein_g"] or 0, r["fat_g"] or 0,
          r["carbs_g"] or 0, r["sodium_mg"] or 0] for r in rows],
        dtype=torch.float32,
    )
    mean = features.mean(dim=0)
    std = features.std(dim=0) + 1e-8
    return mean, std


def _train_model(cursor):
    """
    Train a fresh model on labelled data from the database.
    Creates a new model instance each call to avoid thread-safety issues.
    Returns (model, True) if training succeeded, (None, False) if not.
    """
    device = _get_device()
    model = NutriScorePredictor(input_size=5, num_classes=5).to(device)

    # Compute normalization from the full dataset (fixes distribution mismatch)
    mean, std = _compute_normalization_stats(cursor)
    if mean is None:
        logger.warning("No nutrition data available for normalization.")
        return None, False

    # Store normalization stats on the model for inference
    model._feature_mean = mean.to(device)
    model._feature_std = std.to(device)

    cursor.execute("""
        SELECT n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg,
               hs.nutriscore_grade
        FROM Nutrition_Metrics n
        JOIN HEALTH_SCORE hs ON n.fdc_id = hs.fdc_id
        WHERE hs.nutriscore_grade IS NOT NULL
          AND hs.nutriscore_grade IN ('A', 'B', 'C', 'D', 'E')
          AND n.calories IS NOT NULL
          AND n.protein_g IS NOT NULL
          AND n.fat_g IS NOT NULL
          AND n.carbs_g IS NOT NULL
          AND n.sodium_mg IS NOT NULL
    """)
    rows = cursor.fetchall()

    if len(rows) < 10:
        logger.warning(
            "Not enough labelled data to train ML model (%d samples, need >= 10). "
            "Predictions will not be generated.",
            len(rows),
        )
        return None, False

    label_map = {v: i for i, v in enumerate(NUTRISCORE_LABELS)}
    features_list = []
    labels = []
    for r in rows:
        features_list.append([
            r["calories"] or 0, r["protein_g"] or 0, r["fat_g"] or 0,
            r["carbs_g"] or 0, r["sodium_mg"] or 0,
        ])
        labels.append(label_map[r["nutriscore_grade"]])

    X = torch.tensor(features_list, dtype=torch.float32).to(device)
    y = torch.tensor(labels, dtype=torch.long).to(device)

    # Normalize using full-dataset statistics
    X = (X - model._feature_mean) / model._feature_std

    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    criterion = nn.CrossEntropyLoss()

    epochs = min(MAX_EPOCHS, max(30, len(rows) * 5))
    step_size = max(10, epochs // 3)  # Scale LR decay to dataset size
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=0.5)
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()
        scheduler.step()

    logger.info(
        "Training complete — final loss: %.4f  (%d samples, %d epochs)",
        loss.item(), len(rows), epochs,
    )
    return model, True


def run_inference_and_store(conn, cursor):
    """
    Requirement 9: Run inference on all food records and store predictions
    in the ML_Predictions table.

    If training fails (not enough labeled data), no predictions are generated
    and an error is returned — random-weight predictions are not stored.
    """
    model, trained = _train_model(cursor)

    if not trained:
        raise HTTPException(
            status_code=400,
            detail="Not enough labeled data to train the ML model. "
                   "Add more foods with nutriscore_grade values (A-E) and retry.",
        )

    device = _get_device()

    cursor.execute("""
        SELECT f.fdc_id,
               n.calories, n.protein_g, n.fat_g, n.carbs_g, n.sodium_mg
        FROM Foods f
        JOIN Nutrition_Metrics n ON f.fdc_id = n.fdc_id
        WHERE n.calories IS NOT NULL
    """)
    rows = cursor.fetchall()

    if not rows:
        return {"message": "No data available for inference", "trained": True}

    # Clear old predictions within a transaction so we can roll back on failure
    cursor.execute("SELECT COUNT(*) AS cnt FROM ML_Predictions")
    old_count = cursor.fetchone()["cnt"]
    cursor.execute("DELETE FROM ML_Predictions")

    model.eval()
    count = 0

    with torch.no_grad():
        for row in rows:
            features = torch.tensor([[
                row["calories"] or 0, row["protein_g"] or 0, row["fat_g"] or 0,
                row["carbs_g"] or 0, row["sodium_mg"] or 0,
            ]], dtype=torch.float32).to(device)

            features = (features - model._feature_mean) / model._feature_std

            outputs = model(features)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probs, 1)

            predicted_score = NUTRISCORE_LABELS[predicted_idx.item()]
            # predicted_nova is set to NULL — NOVA cannot be determined
            # from nutrition data alone (it measures processing level)

            cursor.execute(
                """INSERT INTO ML_Predictions
                   (fdc_id, predicted_nutriscore, predicted_nova, confidence_score)
                   VALUES (%s, %s, NULL, %s)""",
                (row["fdc_id"], predicted_score, round(confidence.item(), 4)),
            )
            count += 1

            if count % 500 == 0:
                conn.commit()

    conn.commit()
    return {
        "message": f"Generated {count} predictions on {str(device).upper()} (replaced {old_count} old)",
        "device": str(device),
        "trained": True,
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
def get_device_info():
    return {"device": str(_get_device())}
