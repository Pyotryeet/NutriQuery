import pytest

def test_ml_device(client):
    response = client.get("/ml/device")
    assert response.status_code == 200
    assert "device" in response.json()

def test_get_predictions(client):
    response = client.get("/predictions/?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# We avoid POST /ml/predict and DELETE /ml/predictions in automated tests
# unless we have a mocked/test database as they alter the entire dataset.
