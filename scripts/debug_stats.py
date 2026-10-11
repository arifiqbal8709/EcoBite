
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def debug_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- USERS ---")
    users = cursor.execute("SELECT id, name, email FROM users").fetchall()
    for u in users:
        print(f"ID: {u['id']}, Name: {u['name']}, Email: {u['email']}")

    print("\n--- DONATIONS ---")
    donations = cursor.execute("SELECT id, donor_id, quantity, food_type FROM donations").fetchall()
    for d in donations:
        print(f"ID: {d['id']}, DonorID: {d['donor_id']}, Quantity: {d['quantity']}, Food: {d['food_type']}")

    conn.close()

if __name__ == '__main__':
    debug_db()
