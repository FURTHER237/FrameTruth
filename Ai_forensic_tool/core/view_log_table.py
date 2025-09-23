import sqlite3
import json

conn = sqlite3.connect("analysis_logs.db")
cur = conn.cursor()

cur.execute("SELECT * FROM analysis_logs ORDER BY analysed_at DESC LIMIT 5")
rows = cur.fetchall()

print("Before")
for row in rows:
    print("ID:", row[0])
    print("Filename:", row[1])
    print("Metadata:", json.loads(row[2]))
    print("Image Path:", row[3])
    print("Mask Path:", row[4])
    print("User:", row[5])
    print("Analysed At:", row[6])
    print("---")
print("After")

conn.close()