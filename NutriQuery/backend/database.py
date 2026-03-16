import pymssql

# Connection parameters for the MSSQL Docker container
DB_CONFIG = {
    "server": "127.0.0.1",
    "port": "1433",
    "user": "sa",
    "password": "SqlRoot#2026",
    "database": "NutriQuery",
}


def get_connection():
    """Return a raw pymssql connection to the NutriQuery database."""
    return pymssql.connect(**DB_CONFIG)


def get_db():
    """FastAPI dependency — yields a (connection, cursor) tuple, auto-closes."""
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()
