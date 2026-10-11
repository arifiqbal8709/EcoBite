
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def update_schema_delivery_req():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Default to 1 (True) so existing checks still work
        cursor.execute("ALTER TABLE donations ADD COLUMN delivery_req INTEGER DEFAULT 1")
        print("Added delivery_req column.")
    except Exception as e:
        print(f"Skipping delivery_req (might exist): {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_schema_delivery_req()
