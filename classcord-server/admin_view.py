import sqlite3

DB_PATH = 'config/database/classcord.db'

def list_users():
    with sqlite3.connect(DB_PATH) as conn:
        users = conn.execute('SELECT id, username FROM users').fetchall()
        print("\n📋 Utilisateurs enregistrés :")
        for user in users:
            print(f"- ID: {user[0]} | Nom: {user[1]}")

def list_messages():
    with sqlite3.connect(DB_PATH) as conn:
        msgs = conn.execute('SELECT user_id, channel, content, timestamp FROM messages ORDER BY id DESC LIMIT 10').fetchall()
        print("\n💬 Derniers messages :")
        for msg in msgs:
            print(f"[{msg[3]}] (user {msg[0]}) #{msg[1]}: {msg[2]}")

if __name__ == '__main__':
    list_users()
    list_messages()