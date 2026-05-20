"""
Tests for the ML service module.

Tests the ML device detection, model creation, and the prediction pipeline
against the test database with seeded labeled data.
"""
import pytest
import ml_service


def test_ml_device_detection():
    """Verify device detection returns a valid device string."""
    device_str = ml_service._get_device()
    assert device_str is not None
    assert str(device_str) in ("cpu", "cuda", "mps")


def test_ml_device_is_cached():
    """Verify device is cached after first call."""
    d1 = ml_service._get_device()
    d2 = ml_service._get_device()
    assert d1 == d2


def test_model_creation():
    """Verify the model can be created and moved to device."""
    import torch
    device = ml_service._get_device()
    model = ml_service.NutriScorePredictor(input_size=5, num_classes=5).to(device)
    assert model is not None
    assert len(model.net) == 6  # Linear, ReLU, Dropout, Linear, ReLU, Linear


def test_model_forward_pass():
    """Verify a forward pass through the model works."""
    import torch
    device = ml_service._get_device()
    model = ml_service.NutriScorePredictor(input_size=5, num_classes=5).to(device)
    model.eval()
    x = torch.randn(1, 5).to(device)
    with torch.no_grad():
        output = model(x)
    assert output.shape == (1, 5)  # 5 classes (A-E)


def test_labels_are_correct():
    """Verify the Nutri-Score label mapping is A through E."""
    assert ml_service.NUTRISCORE_LABELS == ["A", "B", "C", "D", "E"]


def test_predict_endpoint_rejects_untrained(client, seed_test_data):
    """
    Bug #3 fix: The /ml/predict endpoint should return an error
    when there isn't enough labeled data to train the model.
    With only 4 labeled foods in our seed data, we should get a 400.
    """
    response = client.post("/ml/predict")
    # Should fail because we have < 10 labeled samples
    assert response.status_code == 400


def test_delete_predictions_works_even_when_empty(client, seed_test_data):
    """Deleting predictions when the table is empty should succeed."""
    response = client.delete("/ml/predictions")
    assert response.status_code == 200
    assert "Deleted" in response.json()["message"]


def test_device_endpoint(client):
    """The /ml/device endpoint should return a valid device."""
    response = client.get("/ml/device")
    assert response.status_code == 200
    assert "device" in response.json()
    assert response.json()["device"] in ("cpu", "cuda", "mps")


def test_predictions_list_endpoint(client, seed_test_data):
    """The /predictions/ endpoint should return a list."""
    response = client.get("/predictions/?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ml_pipeline_with_labeled_data(db_conn, db_cursor, seed_test_data):
    """
    E2E: Seed enough labeled data (>= 10), train, predict, verify predictions exist.
    """
    # Insert additional labeled foods to reach >= 10 samples
    for i in range(10, 20):
        fdc_id = 2000 + i
        db_cursor.execute(
            """INSERT INTO Foods (fdc_id, food_name, category_id, type_id)
               VALUES (%s, %s, %s, %s)""",
            (fdc_id, f"Train Food {i}", seed_test_data["cat_id"], seed_test_data["type_id"]),
        )
        db_cursor.execute(
            """INSERT INTO Nutrition_Metrics (fdc_id, calories, protein_g, fat_g, carbs_g, sodium_mg)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (fdc_id, 100 + i * 10, 5.0 + i, 3.0 + i, 15.0 + i, 50.0 + i),
        )
        db_cursor.execute(
            """INSERT INTO HEALTH_SCORE (fdc_id, health_score, nutriscore_grade, nova_group)
               VALUES (%s, %s, %s, %s)""",
            (fdc_id, 50.0 + i, ["A", "B", "C", "D", "E"][i % 5], i % 4 + 1),
        )
        db_cursor.execute(
            """INSERT INTO ALLERGEN_PROFILE (fdc_id, contains_gluten, contains_dairy)
               VALUES (%s, 0, 0)""",
            (fdc_id,),
        )

    db_conn.commit()

    # Now run training + inference directly via the module
    result = ml_service.run_inference_and_store(db_conn, db_cursor)

    assert result["trained"] is True
    assert "predictions" in result["message"].lower() or "generated" in result["message"].lower()

    # Verify predictions were stored
    db_cursor.execute("SELECT COUNT(*) AS cnt FROM ML_Predictions")
    count = db_cursor.fetchone()["cnt"]
    assert count > 0
