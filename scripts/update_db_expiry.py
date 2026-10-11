
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def update_schema_expiry():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN expiry_datetime TEXT")
        print("Added expiry_datetime column.")
    except Exception as e:
        print(f"Skipping expiry_datetime (might exist): {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_schema_expiry()
