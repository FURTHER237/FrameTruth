import sqlite3

DB_PATH = "analysis_logs.db"  # Path to your SQLite database file

# Connect to the database (will create it if it doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS analysis_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    filename TEXT NOT NULL,
    confidence REAL NOT NULL,
    is_forged BOOLEAN NOT NULL,
    metadata TEXT NOT NULL,
    image_base64 TEXT NOT NULL,
    mask_base64 TEXT,
    analysed_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Database and table initialized successfully.")
