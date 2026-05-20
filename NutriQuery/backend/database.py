import pymssql
import logging
import time

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "server": "127.0.0.1",
    "port": "1433",
    "user": "SA",
    "password": "MbLp6hezU8@",
    "database": "NutriQuery",
    "login_timeout": 10,
    "timeout": 30,
}


def get_connection():
    """Return a pymssql connection with retry on transient failures."""
    last_error = None
    for attempt in range(3):
        try:
            return pymssql.connect(**DB_CONFIG)
        except pymssql.OperationalError as e:
            last_error = e
            logger.warning(
                "DB connection attempt %d/3 failed: %s", attempt + 1, e,
            )
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
    raise last_error


def get_db():
    """FastAPI dependency — yields a (connection, cursor) tuple, auto-closes."""
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()
