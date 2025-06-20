import sqlite3
import json
import csv
import sys
import os
from datetime import datetime

def export_messages(format='json'):
    # Chemin de la base de données
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'database', 'classcord.db')
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Récupération des messages avec les noms d'utilisateurs
    cursor.execute('''
        SELECT messages.id, users.username, messages.channel, 
               messages.content, messages.timestamp
        FROM messages
        JOIN users ON messages.user_id = users.id
        ORDER BY messages.timestamp
    ''')
    
    messages = [dict(row) for row in cursor.fetchall()]
    
    # Création du dossier exports s'il n'existe pas
    os.makedirs('exports', exist_ok=True)
    
    # Nom du fichier avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format.lower() == 'json':
        # Export en JSON
        filename = f'exports/messages_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
            
    elif format.lower() == 'csv':
        # Export en CSV
        filename = f'exports/messages_{timestamp}.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'username', 'channel', 'content', 'timestamp'])
            writer.writeheader()
            writer.writerows(messages)
    
    conn.close()
    print(f"Messages exportés dans {filename}")

if __name__ == "__main__":
    # Format par défaut : JSON
    format = 'json' if len(sys.argv) < 2 else sys.argv[1].lower()
    
    if format not in ['json', 'csv']:
        print("Format non supporté. Utilisez 'json' ou 'csv'")
        sys.exit(1)
        
    export_messages(format)