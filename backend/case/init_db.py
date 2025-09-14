# init_db.py
import sqlite3, os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database.db")

def init_case_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Mission score table
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            score INTEGER,
            status TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Mission tables created/verified in database.db")

if __name__ == "__main__":
    init_case_tables()
