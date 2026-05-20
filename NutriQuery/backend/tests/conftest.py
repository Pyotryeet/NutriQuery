"""
Test fixtures for NutriQuery.

Creates a separate NutriQuery_Test database per session.
Session-scoped seed data is committed once and shared by all tests.
Function-scoped db_conn/db_cursor use transactions for modification isolation.

No mocks — all tests use real pymssql connections to the test database.
"""
import pytest
import pymssql
import os
import sys
import re
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

TEST_DB_NAME = "NutriQuery_Test"

BASE_CONFIG = {
    "server": "127.0.0.1",
    "port": "1433",
    "user": "SA",
    "password": "MbLp6hezU8@",
    "autocommit": True,
    "login_timeout": 10,
    "timeout": 30,
}


def _get_master_connection():
    return pymssql.connect(**{**BASE_CONFIG, "database": "master"})


def _get_test_connection():
    return pymssql.connect(**{**BASE_CONFIG, "database": TEST_DB_NAME})


@pytest.fixture(scope="session")
def test_db_setup():
    """Session-scoped: create the test DB, run init.sql, seed data, drop at end."""
    master = _get_master_connection()
    master.autocommit(True)
    cursor = master.cursor()

    cursor.execute(f"""
        IF DB_ID('{TEST_DB_NAME}') IS NOT NULL
        BEGIN
            ALTER DATABASE [{TEST_DB_NAME}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            DROP DATABASE [{TEST_DB_NAME}];
        END
    """)
    cursor.execute(f"CREATE DATABASE [{TEST_DB_NAME}]")
    cursor.close()
    master.close()

    # Run init.sql
    init_sql_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'init.sql')
    )
    with open(init_sql_path, 'r') as f:
        content = f.read()

    blocks = re.split(r'\n\s*GO\s*\n', content)
    conn = _get_test_connection()
    cursor = conn.cursor()
    for block in blocks:
        stmt = block.strip()
        if not stmt:
            continue
        if (stmt.upper().startswith('CREATE DATABASE')
                or stmt.upper().startswith('USE ')):
            continue
        try:
            cursor.execute(stmt)
        except pymssql.ProgrammingError as e:
            # MSSQL error 2714: object already exists; 1913: index already exists
            err_code = e.args[0][0] if e.args and e.args[0] else 0
            if err_code not in (2714, 1913):
                raise
    conn.commit()
    cursor.close()
    conn.close()

    # Seed data — committed so API endpoints (separate connections) can see it
    _seed_ids = _seed_database()
    # Store for the seed_test_data fixture to access
    test_db_setup._seed_ids = _seed_ids

    yield TEST_DB_NAME

    # Teardown
    master = _get_master_connection()
    master.autocommit(True)
    cursor = master.cursor()
    cursor.execute(f"""
        IF DB_ID('{TEST_DB_NAME}') IS NOT NULL
        BEGIN
            ALTER DATABASE [{TEST_DB_NAME}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            DROP DATABASE [{TEST_DB_NAME}];
        END
    """)
    cursor.close()
    master.close()


def _seed_database():
    """Insert known test records (committed — visible to all connections)."""
    conn = _get_test_connection()
    cursor = conn.cursor(as_dict=True)

    cursor.execute(
        "INSERT INTO Brands (brand_name, brand_owner) VALUES (%s, %s)",
        ("Test Brand", "Test Corp"),
    )
    cursor.execute("SELECT @@IDENTITY AS bid")
    brand_id = int(cursor.fetchone()["bid"])

    cursor.execute(
        "INSERT INTO FOOD_CATEGORY (category_name) VALUES (%s)", ("Snacks",)
    )
    cursor.execute("SELECT @@IDENTITY AS cid")
    cat_id = int(cursor.fetchone()["cid"])

    cursor.execute(
        "INSERT INTO FOOD_CATEGORY (category_name) VALUES (%s)", ("Dairy",)
    )
    cursor.execute("SELECT @@IDENTITY AS cid")
    cat2_id = int(cursor.fetchone()["cid"])

    cursor.execute(
        "INSERT INTO DATA_TYPE (type_name) VALUES (%s)", ("SR Legacy",)
    )
    cursor.execute("SELECT @@IDENTITY AS tid")
    type_id = int(cursor.fetchone()["tid"])

    foods = [
        (1001, brand_id, cat_id, type_id, "Test Apple"),
        (1002, brand_id, cat_id, type_id, "Test Banana"),
        (1003, None, cat2_id, type_id, "Test Milk"),
        (1004, None, cat_id, type_id, "Test Cookie"),
        (1005, brand_id, cat_id, type_id, "Test Energy Bar"),
    ]
    for fdc_id, bid, cid, tid, fname in foods:
        cursor.execute(
            """INSERT INTO Foods (fdc_id, brand_id, category_id, type_id, food_name)
               VALUES (%s, %s, %s, %s, %s)""",
            (fdc_id, bid, cid, tid, fname),
        )

    nutrition = [
        (1001, 52, 0.3, 0.2, 14.0, 1.0),
        (1002, 89, 1.1, 0.3, 23.0, 1.0),
        (1003, 150, 8.0, 8.0, 12.0, 120.0),
        (1004, None, None, None, None, None),
    ]
    for fdc_id, cal, prot, fat, carb, sod in nutrition:
        cursor.execute(
            """INSERT INTO Nutrition_Metrics (fdc_id, calories, protein_g, fat_g, carbs_g, sodium_mg)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (fdc_id, cal, prot, fat, carb, sod),
        )

    health = [
        (1001, 85.0, "A", 1),
        (1002, 65.0, "B", 1),
        (1003, 50.0, "C", 2),
        (1004, 20.0, "D", 4),
    ]
    for fdc_id, hscore, grade, nova in health:
        cursor.execute(
            """INSERT INTO HEALTH_SCORE (fdc_id, health_score, nutriscore_grade, nova_group)
               VALUES (%s, %s, %s, %s)""",
            (fdc_id, hscore, grade, nova),
        )

    allergens = [
        (1001, 0, 0),
        (1002, 0, 0),
        (1003, 0, 1),
        (1004, 1, 0),
    ]
    for fdc_id, gluten, dairy in allergens:
        cursor.execute(
            """INSERT INTO ALLERGEN_PROFILE (fdc_id, contains_gluten, contains_dairy)
               VALUES (%s, %s, %s)""",
            (fdc_id, gluten, dairy),
        )

    conn.commit()
    cursor.close()
    conn.close()

    return {"brand_id": brand_id, "cat_id": cat_id, "cat2_id": cat2_id, "type_id": type_id}


@pytest.fixture
def db_conn(test_db_setup):
    """
    Function-scoped connection with transaction isolation.
    Modifications (INSERT/UPDATE/DELETE) roll back after each test.
    """
    conn = _get_test_connection()
    conn.autocommit(False)
    cur = conn.cursor()
    cur.execute("BEGIN TRANSACTION")
    cur.close()
    yield conn
    cur = conn.cursor()
    cur.execute("ROLLBACK TRANSACTION")
    cur.close()
    conn.close()


@pytest.fixture
def db_cursor(db_conn):
    """Function-scoped cursor sharing db_conn's transaction."""
    cursor = db_conn.cursor(as_dict=True)
    yield cursor
    cursor.close()


@pytest.fixture
def seed_test_data(test_db_setup):
    """
    Data is committed at session scope in _seed_database().
    Returns the actual IDs generated by the database (not hardcoded guesses).
    """
    ids = getattr(test_db_setup, '_seed_ids', None)
    if ids is not None:
        return ids
    # Fallback: these match IDENTITY(1,1) on a fresh DB
    return {
        "brand_id": 1,
        "cat_id": 1,
        "cat2_id": 2,
        "type_id": 1,
    }


@pytest.fixture
def client(test_db_setup):
    """
    Function-scoped FastAPI TestClient pointed at the test DB.
    API endpoints create their own connections so seed data must be committed.
    """
    import database
    original_db = database.DB_CONFIG.get("database")
    database.DB_CONFIG["database"] = TEST_DB_NAME

    from main import app
    with TestClient(app) as c:
        yield c

    if original_db:
        database.DB_CONFIG["database"] = original_db
