
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def add_food_name_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN food_name TEXT")
        print("Added food_name column to donations.")
    except Exception as e:
        print(f"Skipping food_name (might exist): {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_food_name_column()
