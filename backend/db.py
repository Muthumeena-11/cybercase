# db.py
import sqlite3, os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
