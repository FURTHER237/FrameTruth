import sqlite3

DB_PATH = "aift.db"  # your database file

def list_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, role, created_at FROM users")
    users = cursor.fetchall()
    
    if not users:
        print("No users found in the database.")
    else:
        print("Existing users:")
        for user in users:
            print(f"ID: {user['id']}, Username: {user['username']}, Role: {user['role']}, Created At: {user['created_at']}")
    
    conn.close()

if __name__ == "__main__":
    list_users()
