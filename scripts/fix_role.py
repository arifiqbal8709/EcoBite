import sqlite3
import os


# Auto-updated path by refactoring script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def fix_role():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'delivery' WHERE email = 'delivery@sharemeal.com'")
    conn.commit()
    print(f"Updated {cursor.rowcount} rows.")
    conn.close()

if __name__ == "__main__":
    fix_role()
