# Run this script once to (re)create the SQLite DB with sample levels.
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "challenges.db")
if os.path.exists(DB):
    print("Removing existing DB:", DB)
    os.remove(DB)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""CREATE TABLE levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    solution TEXT NOT NULL,
    hint TEXT
)""")

levels = [
    (1, "Hello World", "Print the text hello world exactly as shown.", "Use echo with quoted text", 'echo "hello world"'),
    (2, "Count Files", "Show the number of files (not directories) in the current directory.", "Use ls and wc -l", "ls -p | grep -v / | wc -l"),
    (3, "Show First Line", "Print the first line of the file sample.txt (assume it exists).", "Use head or sed", "head -n 1 sample.txt"),
    (4, "Find TODOs", "Recursively find lines containing TODO in the current directory.", "Use grep with -R -n", "grep -R -n TODO .")
]

cur.executemany("INSERT INTO levels (id, title, description, hint, solution) VALUES (?, ?, ?, ?, ?)", levels)
conn.commit()
conn.close()
print("Initialized DB at", DB)
