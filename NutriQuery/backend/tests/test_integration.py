"""
End-to-end integration tests for NutriQuery.

These tests exercise the full pipeline: database → CRUD → API.
All tests use the real test database with seeded data.
No mocks.
"""
import crud


def test_full_food_profile_retrieval(db_conn, db_cursor, seed_test_data):
    """
    E2E: Retrieve a food and verify all nested relationships are populated.
    """
    food = crud.get_food(db_conn, db_cursor, 1001)

    assert food["fdc_id"] == 1001
    assert food["food_name"] == "Test Apple"
    assert food["food_category"] == "Snacks"
    assert food["data_type"] == "SR Legacy"

    # Brand
    assert food["brand"] is not None
    assert food["brand"]["brand_name"] == "Test Brand"

    # Nutrition
    assert food["nutrition"] is not None
    assert food["nutrition"]["calories"] == 52.0

    # Health Score
    assert food["health_score"] is not None
    assert food["health_score"]["nutriscore_grade"] == "A"
    assert food["health_score"]["nova_group"] == 1

    # Allergen
    assert food["allergen"] is not None
    assert food["allergen"]["contains_gluten"] == 0
    assert food["allergen"]["contains_dairy"] == 0


def test_full_food_without_brand(db_conn, db_cursor, seed_test_data):
    """E2E: Food without a brand (brand_id=NULL) should still work."""
    food = crud.get_food(db_conn, db_cursor, 1003)
    assert food["fdc_id"] == 1003
    assert food["brand"] is None
    assert food["food_category"] == "Dairy"


def test_update_nutrition_flow(db_conn, db_cursor, seed_test_data):
    """E2E: Update nutrition data, verify persistence within the transaction."""
    result = crud.update_nutrition(db_conn, db_cursor, 1001, {
        "calories": 60.0,
        "protein_g": 0.5,
    })
    assert result is not None
    assert result["calories"] == 60.0
    assert result["protein_g"] == 0.5
    # Other fields should be unchanged
    assert result["fat_g"] == 0.2


def test_update_health_score_flow(db_conn, db_cursor, seed_test_data):
    """E2E: Update health score, verify persistence."""
    result = crud.update_health_score(db_conn, db_cursor, 1001, {
        "health_score": 90.0,
        "nutriscore_grade": "A",
    })
    assert result["health_score"] == 90.0


def test_update_allergen_flow(db_conn, db_cursor, seed_test_data):
    """E2E: Update allergen flags, verify persistence."""
    result = crud.update_allergen(db_conn, db_cursor, 1001, {
        "contains_gluten": True,
    })
    assert result["contains_gluten"] == 1


def test_search_foods_by_name(db_conn, db_cursor, seed_test_data):
    """E2E: Search for foods by name substring."""
    results = crud.search_foods(db_conn, db_cursor, "Apple")
    assert len(results) >= 1
    names = [r["food_name"] for r in results]
    assert any("Apple" in n for n in names)


def test_paginated_food_listing(db_conn, db_cursor, seed_test_data):
    """E2E: Paginated listing returns correct page size."""
    results = crud.get_all_foods(db_conn, db_cursor, skip=0, limit=2)
    assert len(results) <= 2


def test_categories_list(db_conn, db_cursor, seed_test_data):
    """E2E: Categories list includes seeded categories."""
    categories = crud.get_categories(db_conn, db_cursor)
    assert "Snacks" in categories
    assert "Dairy" in categories


def test_ml_predictions_crud(db_conn, db_cursor, seed_test_data):
    """E2E: Manually insert a prediction, fetch it, verify structure."""
    # Insert a test prediction
    db_cursor.execute(
        """INSERT INTO ML_Predictions
           (fdc_id, predicted_nutriscore, predicted_nova, confidence_score)
           VALUES (%s, %s, %s, %s)""",
        (1001, "B", None, 0.85),
    )
    db_conn.commit()

    predictions = crud.get_predictions(db_conn, db_cursor, limit=10)
    assert len(predictions) >= 1
    pred = predictions[0]
    assert pred["fdc_id"] == 1001
    assert pred["predicted_nutriscore"] == "B"
    assert pred["predicted_nova"] is None  # NOVA not predicted
    assert pred["food_name"] == "Test Apple"


def test_dietary_filter_comprehensive(db_conn, db_cursor, seed_test_data):
    """E2E: Comprehensive dietary filter with combinations."""
    # Gluten-free + dairy-free
    results = crud.get_foods_by_diet(db_conn, db_cursor, no_gluten=True, no_dairy=True)
    fdc_ids = [r["fdc_id"] for r in results]
    assert 1001 in fdc_ids  # clean
    assert 1002 in fdc_ids  # clean
    assert 1003 not in fdc_ids  # dairy
    assert 1004 not in fdc_ids  # gluten
    assert 1005 in fdc_ids  # no profile → passes

    # Gluten-free only
    results = crud.get_foods_by_diet(db_conn, db_cursor, no_gluten=True, no_dairy=False)
    fdc_ids = [r["fdc_id"] for r in results]
    assert 1003 in fdc_ids  # has dairy but not gluten
    assert 1004 not in fdc_ids  # has gluten
