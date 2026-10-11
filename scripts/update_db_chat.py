
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'sharemeal.db')

def update_schema_chat():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donation_id INTEGER,
                sender_id INTEGER,
                receiver_id INTEGER,
                message TEXT,
                timestamp TEXT,
                FOREIGN KEY (donation_id) REFERENCES donations (id),
                FOREIGN KEY (sender_id) REFERENCES users (id),
                FOREIGN KEY (receiver_id) REFERENCES users (id)
            )
        ''')
        print("Messages table created successfully.")
    except Exception as e:
        print(f"Error creating messages table: {e}")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_schema_chat()
