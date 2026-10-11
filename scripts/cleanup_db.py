import sqlite3
import os


# Auto-updated path by refactoring script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def delete_cooked_veg():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM donations WHERE food_type LIKE ?", ('%cooked_veg%',))
        print(f"Deleted {cursor.rowcount} rows with 'cooked_veg'.")
    except Exception as e:
        print(f"Error: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    delete_cooked_veg()
