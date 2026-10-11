import sqlite3
import os


# Auto-updated path by refactoring script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def create_admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    email = "admin@sharemeal.com"
    password = "admin" # Simple password for now
    name = "System Administrator"
    phone = "0000000000"
    role = "admin"

    try:
        cursor.execute('INSERT INTO users (name, email, password, phone, role) VALUES (?, ?, ?, ?, ?)',
                       (name, email, password, phone, role))
        conn.commit()
        print(f"Admin account created successfully.\nEmail: {email}\nPassword: {password}")
    except sqlite3.IntegrityError:
        print("Admin account already exists.")
    except Exception as e:
        print(f"Error creating admin: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
