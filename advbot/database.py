import sqlite3
from datetime import datetime, timedelta
from config import message_limit_per_24h

def create_connection():
    conn = sqlite3.connect('messages.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            sender_id INTEGER,
            likes INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_message_limits (
            user_id INTEGER PRIMARY KEY,
            last_message_date TEXT,
            message_count INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def insert_message(message_id, sender_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (id, sender_id, likes) VALUES (?, ?, ?)', (message_id, sender_id, 0))
    conn.commit()
    conn.close()

def update_likes(message_id, likes):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE messages SET likes = ? WHERE id = ?', (likes, message_id))
    conn.commit()
    conn.close()

def get_likes(message_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT likes FROM messages WHERE id = ?', (message_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0 

def delete_message(message_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()

# New functions for user message limits
def check_user_message_limit(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT last_message_date, message_count FROM user_message_limits WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_user_message_limit(user_id):
    now = datetime.now()
    conn = create_connection()
    cursor = conn.cursor()
    
    # Check if the user exists in the table
    cursor.execute('SELECT last_message_date, message_count FROM user_message_limits WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result:
        last_message_date, message_count = result
        last_message_date = datetime.fromisoformat(last_message_date)
        
        # Check if the last message was sent within the last 24 hours
        if now - last_message_date < timedelta(days=1):
            if message_count >= message_limit_per_24h:
                conn.close()
                return False  # User has reached the limit
            else:
                message_count += 1
        else:
            message_count = 1  # Reset count if more than a day has passed
        
        cursor.execute('UPDATE user_message_limits SET last_message_date = ?, message_count = ? WHERE user_id = ?', 
                       (now.isoformat(), message_count, user_id))
    else:
        # Insert new user record
        cursor.execute('INSERT INTO user_message_limits (user_id, last_message_date, message_count) VALUES (?, ?, ?)', 
                       (user_id, now.isoformat(), 1))
    
    conn.commit()
    conn.close()
    return True  # User can send a message
