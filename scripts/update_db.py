import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'sharemeal.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Create Donations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_type TEXT,
            quantity TEXT,
            pickup_address TEXT,
            instructions TEXT,
            status TEXT DEFAULT 'Available',
            timestamp TEXT,
            donor_id INTEGER,
            
            -- New Columns for Enhanced Flow
            food_name TEXT,
            image_path TEXT,
            diet_type TEXT,
            preparation_time TEXT,
            expiry_datetime TEXT,
            
            -- Claim & Delivery Logic
            claimed_by INTEGER,
            claimed_at TEXT,
            otp TEXT,
            delivery_req BOOLEAN DEFAULT 1,
            delivery_by INTEGER,
            
            FOREIGN KEY (donor_id) REFERENCES users (id)
        )
    ''')
    
    # Simple migration for existing tables (if columns missing)
    try:
        cursor.execute("ALTER TABLE donations ADD COLUMN food_name TEXT")
        cursor.execute("ALTER TABLE donations ADD COLUMN image_path TEXT")
        cursor.execute("ALTER TABLE donations ADD COLUMN diet_type TEXT")
        cursor.execute("ALTER TABLE donations ADD COLUMN preparation_time TEXT")
        cursor.execute("ALTER TABLE donations ADD COLUMN expiry_datetime TEXT")
        
        cursor.execute("ALTER TABLE donations ADD COLUMN claimed_by INTEGER")
        cursor.execute("ALTER TABLE donations ADD COLUMN claimed_at TEXT")
        cursor.execute("ALTER TABLE donations ADD COLUMN otp TEXT")
        cursor.execute("ALTER TABLE donations ADD COLUMN delivery_req BOOLEAN DEFAULT 1")
        cursor.execute("ALTER TABLE donations ADD COLUMN delivery_by INTEGER")
    except:
        pass # Columns likely exist
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# Initialize when imported
if not os.path.exists(DB_PATH):
    init_db()
