import sqlite3

DB_NAME = "sustainability_analytics.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS energy_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value REAL NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    entered_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS water_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value REAL NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    entered_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS waste_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value REAL NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    entered_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS greenery_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value REAL NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    entered_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sustainability_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    energy_score REAL,
    water_score REAL,
    waste_score REAL,
    greenery_score REAL,
    total_score REAL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ Database initialized successfully")
