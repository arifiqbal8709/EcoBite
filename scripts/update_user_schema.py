import sqlite3
import os


# Auto-updated path by refactoring script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def update_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking database schema...")

    # Check for new columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'address' not in columns:
        print("Adding 'address' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
        
    if 'bio' not in columns:
        print("Adding 'bio' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
        
    if 'profile_pic' not in columns:
        print("Adding 'profile_pic' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
        
    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    update_schema()
