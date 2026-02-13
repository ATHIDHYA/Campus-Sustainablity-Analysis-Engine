import sqlite3

DB_NAME = "sustainability_analytics.db"

def get_connection():
    """
    Creates and returns a database connection.
    timeout=10 prevents 'database is locked' errors.
    """
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
