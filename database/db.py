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
            role TEXT NOT NULL,
            address TEXT,
            bio TEXT,
            profile_pic TEXT
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
    
    # Create Emergency Broadcasts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngo_id INTEGER,
            title TEXT,
            description TEXT,
            area TEXT,
            contact_details TEXT,
            level TEXT,
            status TEXT DEFAULT 'Active',
            timestamp TEXT,
            FOREIGN KEY (ngo_id) REFERENCES users (id)
        )
    ''')

    # Create SOS Alerts Table used by frontend emergency banner
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

    # Create Scheduled Donations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER,
            food_name TEXT,
            food_type TEXT,
            quantity TEXT,
            pickup_address TEXT,
            schedule_type TEXT,
            scheduled_date TEXT,
            scheduled_time TEXT,
            instructions TEXT,
            status TEXT DEFAULT 'Scheduled',
            timestamp TEXT,
            FOREIGN KEY (donor_id) REFERENCES users (id)
        )
    ''')

    # Create AI Feedback Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT,
            ai_predicted TEXT,
            donor_corrected TEXT,
            diet_type TEXT,
            food_category TEXT,
            model_version TEXT,
            timestamp TEXT,
            review_status TEXT DEFAULT 'Pending'
        )
    ''')

    # Create Notifications Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            related_donation_id INTEGER,
            is_read BOOLEAN DEFAULT 0,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create Claims Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donation_id INTEGER UNIQUE NOT NULL,
            ngo_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Claimed',
            claimed_at TEXT,
            FOREIGN KEY (donation_id) REFERENCES donations (id),
            FOREIGN KEY (ngo_id) REFERENCES users (id)
        )
    ''')

    # Create Delivery Tasks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donation_id INTEGER UNIQUE NOT NULL,
            claim_id INTEGER,
            delivery_partner_id INTEGER,
            pickup_location TEXT,
            drop_location TEXT,
            status TEXT DEFAULT 'Available',
            created_at TEXT,
            assigned_at TEXT,
            picked_up_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (donation_id) REFERENCES donations (id),
            FOREIGN KEY (delivery_partner_id) REFERENCES users (id)
        )
    ''')

    # Create Delivery Proofs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_proofs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            donation_id INTEGER,
            proof_type TEXT,
            otp_entered TEXT,
            verified_at TEXT,
            FOREIGN KEY (donation_id) REFERENCES donations (id)
        )
    ''')

    # Create Delivery OTPs Table for Secure Hashed OTP Verification
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donation_id INTEGER UNIQUE NOT NULL,
            pickup_otp_hash TEXT NOT NULL,
            pickup_otp_enc TEXT NOT NULL,
            delivery_otp_hash TEXT NOT NULL,
            delivery_otp_enc TEXT NOT NULL,
            pickup_attempts INTEGER DEFAULT 0,
            delivery_attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 5,
            pickup_verified INTEGER DEFAULT 0,
            delivery_verified INTEGER DEFAULT 0,
            pickup_verified_at TEXT,
            delivery_verified_at TEXT,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donation_id) REFERENCES donations (id) ON DELETE CASCADE
        )
    ''')

    # Create Complaints Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            user_role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            related_donation_id INTEGER,
            related_delivery_id INTEGER,
            priority TEXT NOT NULL DEFAULT 'MEDIUM',
            status TEXT NOT NULL DEFAULT 'OPEN',
            attachment_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            assigned_admin_id INTEGER,
            resolved_at TEXT,
            reopen_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (assigned_admin_id) REFERENCES users (id)
        )
    ''')

    # Create Complaint Replies Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaint_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            sender_role TEXT NOT NULL,
            sender_name TEXT NOT NULL,
            message TEXT NOT NULL,
            is_internal_note BOOLEAN DEFAULT 0,
            attachment_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users (id)
        )
    ''')

    # Create Complaint History / Audit Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaint_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            changed_by_id INTEGER NOT NULL,
            changed_by_role TEXT NOT NULL,
            changed_by_name TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
        )
    ''')

    # Create Contact Submissions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Simple migration for existing tables (if columns missing)
    for column_sql in [
        "ALTER TABLE users ADD COLUMN address TEXT",
        "ALTER TABLE users ADD COLUMN bio TEXT",
        "ALTER TABLE users ADD COLUMN profile_pic TEXT",
        "ALTER TABLE users ADD COLUMN donor_type TEXT",
        "ALTER TABLE donations ADD COLUMN food_name TEXT",
        "ALTER TABLE donations ADD COLUMN image_path TEXT",
        "ALTER TABLE donations ADD COLUMN diet_type TEXT",
        "ALTER TABLE donations ADD COLUMN preparation_time TEXT",
        "ALTER TABLE donations ADD COLUMN expiry_datetime TEXT",
        "ALTER TABLE donations ADD COLUMN claimed_by INTEGER",
        "ALTER TABLE donations ADD COLUMN claimed_at TEXT",
        "ALTER TABLE donations ADD COLUMN otp TEXT",
        "ALTER TABLE donations ADD COLUMN delivery_req BOOLEAN DEFAULT 1",
        "ALTER TABLE donations ADD COLUMN delivery_by INTEGER",
        "ALTER TABLE donations ADD COLUMN food_category TEXT",
        "ALTER TABLE donations ADD COLUMN servings_count INTEGER",
        "ALTER TABLE donations ADD COLUMN storage_condition TEXT",
        "ALTER TABLE donations ADD COLUMN allergens TEXT",
        "ALTER TABLE donations ADD COLUMN safety_status TEXT",
        "ALTER TABLE complaints ADD COLUMN reopen_count INTEGER DEFAULT 0",
    ]:
        try:
            cursor.execute(column_sql)
        except sqlite3.OperationalError:
            pass

    # Ensure Standard Demo Accounts Exist with Working Passwords
    default_users = [
        ('ARSH (Verified Donor)', 'donor@sharemeal.com', 'password123', '7070280186', 'donor', 'Chas, Bokaro, Jharkhand', 'Active Surplus Food Donor'),
        ('Jyoti NGO Center', 'ngo@sharemeal.com', 'password123', '7070280186', 'ngo', 'GGSESTC, Kandra, Chas', 'Community Hunger Relief Mission'),
        ('Delivery Partner Rider', 'del@sharemeal.com', 'password123', '9876543212', 'delivery', 'Ranchi Hub Station', 'EcoBite Volunteer Driver'),
        ('System Administrator', 'admin@sharemeal.com', 'password123', '9876543210', 'admin', 'HQ Office, Ranchi', 'Central Platform Admin'),
    ]

    for name, email, password, phone, role, address, bio in default_users:
        existing = cursor.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if not existing:
            cursor.execute('''
                INSERT INTO users (name, email, password, phone, role, address, bio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, password, phone, role, address, bio))
        else:
            # Keep credentials aligned so user can easily log in
            cursor.execute('''
                UPDATE users SET password = ?, role = ? WHERE email = ?
            ''', (password, role, email))

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# Initialize when executed directly or when file doesn't exist
if __name__ == '__main__':
    init_db()
elif not os.path.exists(DB_PATH):
    init_db()

