
import sqlite3
import os

# Define path to database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def update_db():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Add donation_type column to donations
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN donation_type TEXT DEFAULT 'Normal'")
        print("Added 'donation_type' column to 'donations'.")
    except sqlite3.OperationalError as e:
        print(f"Skipping 'donation_type': {e}")

    # 2. Add event_details column to donations (for specific event info like 'Wedding', 'Corporate')
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN event_details TEXT")
        print("Added 'event_details' column to 'donations'.")
    except sqlite3.OperationalError as e:
        print(f"Skipping 'event_details': {e}")

    # 3. Create sos_alerts table
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sos_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                location TEXT,
                radius_km INTEGER DEFAULT 5,
                status TEXT DEFAULT 'Active',
                timestamp TEXT,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        print("Created 'sos_alerts' table.")
    except Exception as e:
        print(f"Error creating 'sos_alerts': {e}")

    # 4. Create broadcasts table
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                level TEXT DEFAULT 'Info', -- Info, Warning, Cryptic/Emergency
                is_active INTEGER DEFAULT 1,
                timestamp TEXT,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        print("Created 'broadcasts' table.")
    except Exception as e:
        print(f"Error creating 'broadcasts': {e}")

    conn.commit()
    conn.close()
    print("Database schema updated for Emergency & Event features.")

if __name__ == '__main__':
    update_db()
