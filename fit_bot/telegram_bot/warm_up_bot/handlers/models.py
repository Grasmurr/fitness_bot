import sqlite3


def create_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            gender TEXT,
            phone TEXT,
            age INTEGER,
            weight REAL,
            height REAL,
            activity_level INTEGER,
            problem TEXT,
            last_interaction_time TEXT,
            notified INTEGER DEFAULT 0,
            last_bot_message_id INTEGER,
            last_bot_message_type TEXT)''')

    conn.commit()

