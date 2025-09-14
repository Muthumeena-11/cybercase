import sqlite3
from werkzeug.security import generate_password_hash

DB = "database.db"

def create_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)
    demo_email = "test@example.com"
    demo_name = "Demo User"
    demo_password_hash = generate_password_hash("password123")
    try:
        c.execute("INSERT INTO users (name, email, password_hash, points, badge) VALUES (?, ?, ?, ?, ?)",
                  (demo_name, demo_email, demo_password_hash, 10, "Beginner"))
        conn.commit()
        print("Demo user created.")
    except sqlite3.IntegrityError:
        print("Demo user already exists.")
    conn.close()
    

if __name__ == "__main__":
    create_db()
