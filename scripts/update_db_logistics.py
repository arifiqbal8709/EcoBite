import sqlite3
import os


# Auto-updated path by refactoring script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def update_schema_logistics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Add new columns for enhanced logistics
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN preparation_time TEXT")
        print("Added 'preparation_time'")
    except: pass

    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN category TEXT") # Veg/Non-Veg
        print("Added 'category'")
    except: pass

    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN delivery_by INTEGER") # Delivery Person ID
        print("Added 'delivery_by'")
    except: pass

    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN is_verified INTEGER DEFAULT 0") # Verification Status
        print("Added 'is_verified'")
    except: pass

    # Create Messages Table for Chat
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            donation_id INTEGER,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Created/Checked 'messages' table")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema_logistics()
