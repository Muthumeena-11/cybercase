import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create users table with desired columns
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        points INTEGER DEFAULT 0,
        badge TEXT DEFAULT 'Newbie'
    )
    """)

    # Insert demo user (if not exists)
    demo_email = "test@example.com"
    demo_username = "Demo User"
    demo_password_hash = generate_password_hash("password123")
    try:
        c.execute("INSERT INTO users (username, email, password, points, badge) VALUES (?, ?, ?, ?, ?)",
                  (demo_username, demo_email, demo_password_hash, 10, "Beginner"))
        print("Demo user created.")
    except sqlite3.IntegrityError:
        print("Demo user already exists.")

    conn.commit()
    conn.close()
    print("Database initialized at:", DB_PATH)

if __name__ == "__main__":
    init_db()
