import pytest
from httpx import AsyncClient

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to NutriQuery API"}

def test_list_categories(client):
    response = client.get("/categories/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_search_foods(client):
    response = client.get("/foods/search?name=Apple")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_foods(client):
    response = client.get("/foods/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

def test_queries_range(client):
    response = client.get("/queries/range?min_health_score=50&max_sodium=200&max_carbs=30")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_queries_dietary(client):
    response = client.get("/queries/dietary?no_gluten=true&no_dairy=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_queries_aggregation(client):
    response = client.get("/queries/aggregation?category=Snacks")
    assert response.status_code == 200
    assert "avg_calories" in response.json()

def test_list_brands(client):
    response = client.get("/brands/?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
