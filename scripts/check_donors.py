import sqlite3
import os

db_path = os.path.join('database', 'sharemeal.db')
if not os.path.exists(db_path):
    print("Database file not found.")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    donors = cursor.execute("SELECT name, email, role FROM users WHERE role = 'donor'").fetchall()
    conn.close()
    
    if not donors:
        print("No donor accounts found.")
    else:
        for d in donors:
            print(f"Name: {d['name']}, Email: {d['email']}, Role: {d['role']}")
