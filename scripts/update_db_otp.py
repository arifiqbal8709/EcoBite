import sqlite3
import os


# Auto-updated path by refactoring script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def add_otp_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN otp TEXT")
        print("Success: otp column added.")
    except sqlite3.OperationalError as e:
        print(f"Info: {e} (Column might already exist)")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_otp_column()
