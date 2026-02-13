import sqlite3
import hashlib

DB_NAME = "sustainability_analytics.db"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # ---------------- USERS ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- ENERGY DATA ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS energy_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value REAL NOT NULL,
        month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
        year INTEGER NOT NULL,
        entered_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entered_by) REFERENCES users(id) ON DELETE SET NULL
    )
    """)

    # ---------------- WATER DATA ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value REAL NOT NULL,
        month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
        year INTEGER NOT NULL,
        entered_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entered_by) REFERENCES users(id) ON DELETE SET NULL
    )
    """)

    # ---------------- WASTE DATA ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS waste_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value REAL NOT NULL,
        month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
        year INTEGER NOT NULL,
        entered_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entered_by) REFERENCES users(id) ON DELETE SET NULL
    )
    """)

    # ---------------- GREENERY DATA ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS greenery_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value REAL NOT NULL,
        month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
        year INTEGER NOT NULL,
        entered_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entered_by) REFERENCES users(id) ON DELETE SET NULL
    )
    """)

    # ---------------- SUSTAINABILITY SCORES ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sustainability_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
        year INTEGER NOT NULL,
        energy_score REAL,
        water_score REAL,
        waste_score REAL,
        greenery_score REAL,
        total_score REAL,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- ACTIVITY LOGS ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # ---------------- INDEXES ----------------
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_year ON sustainability_scores(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_energy_year ON energy_data(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_year ON water_data(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_waste_year ON waste_data(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_greenery_year ON greenery_data(year)")

    # ---------------- DEFAULT ADMIN ----------------
    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    admin = cursor.fetchone()

    if not admin:
        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, ("admin", hash_password("admin123"), "admin"))

        print("✅ Default admin created")
        print("   Username: admin")
        print("   Password: admin123")

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully!")


if __name__ == "__main__":
    init_db()
