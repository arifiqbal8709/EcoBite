
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def update_schema_read():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
        print("Added is_read column to messages.")
    except Exception as e:
        print(f"Skipping is_read (might exist): {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_schema_read()
