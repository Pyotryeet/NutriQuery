"""
Tests that verify each bug fix from the forensic audit.

Each test validates that a specific fix is working correctly.
All tests run against the isolated test database with real data.
No mocks.
"""
import crud


def test_allergen_join_includes_unprofiled_foods(db_conn, db_cursor, seed_test_data):
    """
    Bug #2 fix: LEFT JOIN on ALLERGEN_PROFILE should include foods
    that have no allergen profile row. Food 1005 has no ALLERGEN_PROFILE row.
    With the old INNER JOIN, this food would be excluded entirely.
    """
    results = crud.get_foods_by_diet(db_conn, db_cursor, no_gluten=True, no_dairy=False)

    fdc_ids = [r["fdc_id"] for r in results]
    # Food 1005 has no allergen profile — should still appear
    assert 1005 in fdc_ids, (
        f"Food 1005 (no allergen profile) was excluded — LEFT JOIN fix not working. "
        f"Found IDs: {fdc_ids}"
    )


def test_allergen_filter_respects_nulls(db_conn, db_cursor, seed_test_data):
    """
    Bug #2 fix: NULL allergen flags should be treated as "no restriction hit."
    Food 1005 (no profile) should pass gluten-free filter.
    """
    results = crud.get_foods_by_diet(db_conn, db_cursor, no_gluten=True, no_dairy=True)

    fdc_ids = [r["fdc_id"] for r in results]
    # 1005: no profile → passes
    # 1001, 1002: gluten=0, dairy=0 → passes
    # 1003: dairy=1 → excluded
    # 1004: gluten=1 → excluded
    assert 1005 in fdc_ids
    assert 1001 in fdc_ids
    assert 1003 not in fdc_ids
    assert 1004 not in fdc_ids


def test_ecoscore_not_in_brand_schema(db_conn, db_cursor, seed_test_data):
    """
    Bug #1 fix: brand creation should not accept or store ecoscore_grade.
    """
    result = crud.create_brand(db_conn, db_cursor, {
        "brand_name": "EcoScore Test Brand",
        "brand_owner": "Test Owner",
        "ecoscore_grade": "A",  # This should be silently ignored if passed
    })

    assert result["brand_name"] == "EcoScore Test Brand"

    # Verify only the expected columns exist (no ecoscore_grade)
    db_cursor.execute(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = 'Brands'"
    )
    columns = [r["COLUMN_NAME"] for r in db_cursor.fetchall()]
    assert "ecoscore_grade" not in columns


def test_food_query_uses_left_joins(db_conn, db_cursor, seed_test_data):
    """
    Issue #9 fix: the shared FOOD query should use LEFT JOINs so that
    foods without optional related data (brand, allergen, health, etc.)
    are still returned.
    """
    # Food 1005 has no ALLERGEN_PROFILE and no HEALTH_SCORE
    food = crud.get_food(db_conn, db_cursor, 1005)
    assert food is not None, "Food 1005 should be found even with missing related data"
    assert food["fdc_id"] == 1005
    assert food["food_name"] == "Test Energy Bar"
    # No allergen profile — should be None
    assert food["allergen"] is None


def test_predictions_field_removed(db_conn, db_cursor, seed_test_data):
    """
    Issue #6 third-pass fix: the predictions field has been removed from the
    Food schema since it was never populated. The key should not exist.
    """
    food = crud.get_food(db_conn, db_cursor, 1001)
    assert "predictions" not in food, (
        "predictions key should not exist in food dict, got: %s" % food.get("predictions")
    )


def test_gap_detection_finds_missing_nutrition(db_conn, db_cursor, seed_test_data):
    """
    Issue (gap detection sanity check): Food 1004 has all-NULL nutrition.
    Should appear in the gaps query.
    """
    gaps = crud.get_foods_with_missing_data(db_conn, db_cursor)
    fdc_ids = [g["fdc_id"] for g in gaps]
    assert 1004 in fdc_ids, f"Food 1004 should be in gaps, got: {fdc_ids}"


def test_range_query_filters_correctly(db_conn, db_cursor, seed_test_data):
    """
    Sanity check: range query should filter by health score, sodium, carbs.
    """
    results = crud.get_foods_by_range(
        db_conn, db_cursor,
        min_health_score=50.0, max_sodium=100.0, max_carbs=20.0,
    )
    fdc_ids = [r["fdc_id"] for r in results]
    # 1001: health=85, sodium=1, carbs=14 → included
    # 1003: health=50, sodium=120, carbs=12 → excluded (sodium > 100)
    # 1004: health=20, ... → excluded (health < 50)
    assert 1001 in fdc_ids
    assert 1003 not in fdc_ids
    assert 1004 not in fdc_ids


def test_category_aggregation_returns_stats(db_conn, db_cursor, seed_test_data):
    """
    Sanity check: aggregation should return correct stats for a category.
    """
    agg = crud.get_category_aggregation(db_conn, db_cursor, "Snacks")
    # 1001 (Apple): 52 cal, 0.3p, 0.2f, 14c
    # 1002 (Banana): 89 cal, 1.1p, 0.3f, 23c
    # 1004 (Cookie): has nutrition row but all NULLs — COUNT includes it, AVG ignores NULLs
    # 1005 (Energy Bar): no nutrition row — excluded by INNER JOIN
    assert agg["item_count"] == 3  # 1001, 1002, 1004 have nutrition rows
    assert agg["avg_calories"] == round((52 + 89) / 2, 2)  # 1004 NULL calories ignored by AVG


def test_brand_crud_flow(db_conn, db_cursor, seed_test_data):
    """
    Sanity check: create brand, verify it appears in get_brands.
    """
    result = crud.create_brand(db_conn, db_cursor, {
        "brand_name": "Flow Test Brand",
        "brand_owner": "Flow Inc",
    })
    assert result["brand_name"] == "Flow Test Brand"
    assert result["brand_id"] is not None

    brands = crud.get_brands(db_conn, db_cursor)
    brand_names = [b["brand_name"] for b in brands]
    assert "Flow Test Brand" in brand_names
    assert "Test Brand" in brand_names
