import sqlite3
import os

def init_db():
    # Obtenir le chemin absolu du répertoire de base
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(base_dir, 'config', 'database')
    db_path = os.path.join(db_dir, 'classcord.db')
    
    # Assurez-vous que le répertoire existe
    os.makedirs(db_dir, exist_ok=True)
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Création des tables
    cursor.executescript('''
    -- Table des utilisateurs
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    );

    -- Table des canaux
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    -- Table des messages
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        channel TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    ''')
    
    # Insertion des canaux par défaut
    channels = ['#général', '#dev', '#admin']
    for channel in channels:
        cursor.execute('INSERT OR IGNORE INTO channels (name) VALUES (?)', (channel,))
    
    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès")
    print(f"Base de données créée à : {db_path}")

if __name__ == "__main__":
    init_db()