import sqlite3
import os


# Auto-updated path by refactoring script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def add_claimed_at_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN claimed_at TEXT")
        print("Column 'claimed_at' added successfully.")
    except sqlite3.OperationalError as e:
        print(f"Error (column might already exist): {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_claimed_at_column()
