import pytest
import crud

def test_get_categories(db_conn, db_cursor):
    categories = crud.get_categories(db_conn, db_cursor)
    assert isinstance(categories, list)

def test_search_foods(db_conn, db_cursor):
    results = crud.search_foods(db_conn, db_cursor, "Apple", limit=5)
    assert isinstance(results, list)

def test_get_all_foods(db_conn, db_cursor):
    results = crud.get_all_foods(db_conn, db_cursor, skip=0, limit=5)
    assert isinstance(results, list)
    assert len(results) <= 5

def test_brand_creation_and_retrieval(db_conn, db_cursor):
    # Insert a test brand
    brand_data = {
        "brand_name": "Test Brand Pytest",
        "brand_owner": "Test Owner",
        "ecoscore_grade": "A"
    }
    new_brand = crud.create_brand(db_conn, db_cursor, brand_data)
    assert new_brand is not None
    assert new_brand["brand_name"] == brand_data["brand_name"]
    
    # Verify it was actually saved by querying it directly
    db_cursor.execute("SELECT * FROM Brands WHERE brand_id = %s", (new_brand["brand_id"],))
    retrieved_brand = db_cursor.fetchone()
    assert retrieved_brand is not None
    assert retrieved_brand["brand_id"] == new_brand["brand_id"]

def test_gap_identification(db_conn, db_cursor):
    gaps = crud.get_foods_with_missing_data(db_conn, db_cursor, limit=10)
    assert isinstance(gaps, list)

def test_category_aggregation(db_conn, db_cursor):
    agg = crud.get_category_aggregation(db_conn, db_cursor, "Snacks")
    assert isinstance(agg, dict)
    assert "avg_calories" in agg
