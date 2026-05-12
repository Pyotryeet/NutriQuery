import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to Python path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from database import get_connection

@pytest.fixture(scope="module")
def client():
    """Provides a TestClient for FastAPI endpoints."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def db_conn():
    """Provides a raw database connection for direct CRUD testing."""
    conn = get_connection()
    yield conn
    conn.close()

@pytest.fixture(scope="module")
def db_cursor(db_conn):
    """Provides a database cursor for direct CRUD testing."""
    cursor = db_conn.cursor(as_dict=True)
    yield cursor
    cursor.close()
