import socket
import threading
import json
import sqlite3
import os
from datetime import datetime
import logging
import hashlib
import csv

HOST = '0.0.0.0'
PORT = 12345
DB_PATH = 'config/database/classcord.db'
AUDIT_LOG = 'logs/audit.log'
EXPORT_DIR = 'exports'
CHANNELS = {'#général': [], '#dev': [], '#admin': []}
CLIENTS = {}
LOCK = threading.Lock()

os.makedirs('logs', exist_ok=True)
os.makedirs('config/database', exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

logging.basicConfig(
    filename=AUDIT_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_audit(msg):
    logging.info(msg)
    print("[AUDIT]", msg)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.commit()

def send_json(sock, data):
    try:
        sock.sendall((json.dumps(data) + '\n').encode())
    except:
        pass

def broadcast(message, channel=None, exclude=None):
    msg = json.dumps(message) + '\n'
    targets = CHANNELS[channel] if channel else sum(CHANNELS.values(), [])
    for client in targets:
        if client != exclude:
            try:
                client.sendall(msg.encode())
            except:
                disconnect_client(client)

def disconnect_client(sock):
    with LOCK:
        if sock in CLIENTS:
            username = CLIENTS[sock]['username']
            channel = CLIENTS[sock]['channel']
            CHANNELS[channel].remove(sock)
            del CLIENTS[sock]
            broadcast({'type': 'status', 'user': username, 'state': 'offline'}, channel=channel)
    try:
        sock.close()
    except:
        pass

def handle_client(sock):
    buffer = ''
    try:
        while True:
            data = sock.recv(1024).decode()
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                msg = json.loads(line)

                if msg['type'] == 'register':
                    with sqlite3.connect(DB_PATH) as conn:
                        try:
                            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                                         (msg['username'], hash_password(msg['password'])))
                            conn.commit()
                            send_json(sock, {'type': 'register', 'status': 'ok'})
                        except sqlite3.IntegrityError:
                            send_json(sock, {'type': 'error', 'message': 'Utilisateur déjà existant'})

                elif msg['type'] == 'login':
                    with sqlite3.connect(DB_PATH) as conn:
                        cur = conn.execute('SELECT id, password FROM users WHERE username=?', (msg['username'],))
                        row = cur.fetchone()
                        if row and row[1] == hash_password(msg['password']):
                            CLIENTS[sock] = {'username': msg['username'], 'channel': '#général'}
                            CHANNELS['#général'].append(sock)
                            send_json(sock, {'type': 'login', 'status': 'ok'})
                            broadcast({'type': 'status', 'user': msg['username'], 'state': 'online'}, '#général', exclude=sock)
                            log_audit(f"{msg['username']} connecté depuis {sock.getpeername()}")
                        else:
                            send_json(sock, {'type': 'error', 'message': 'Identifiants invalides'})

                elif msg['type'] == 'message' and sock in CLIENTS:
                    username = CLIENTS[sock]['username']
                    channel = CLIENTS[sock]['channel']
                    timestamp = datetime.now().isoformat()
                    broadcast({'type': 'message', 'from': username, 'channel': channel, 'content': msg['content'], 'timestamp': timestamp}, channel, exclude=sock)
                    with sqlite3.connect(DB_PATH) as conn:
                        cur = conn.execute('SELECT id FROM users WHERE username=?', (username,))
                        user_id = cur.fetchone()
                        if user_id:
                            conn.execute('INSERT INTO messages (user_id, channel, content, timestamp) VALUES (?, ?, ?, ?)',
                                         (user_id[0], channel, msg['content'], timestamp))
                            conn.commit()

                elif msg['type'] == 'channel_switch' and sock in CLIENTS:
                    old = CLIENTS[sock]['channel']
                    new = msg['channel']
                    if new in CHANNELS:
                        CHANNELS[old].remove(sock)
                        CHANNELS[new].append(sock)
                        CLIENTS[sock]['channel'] = new
                        send_json(sock, {'type': 'info', 'message': f'Vous avez rejoint {new}'})
                    else:
                        send_json(sock, {'type': 'error', 'message': 'Canal inexistant'})
    except Exception as e:
        logging.error(f"Erreur client: {e}")
    finally:
        disconnect_client(sock)

def export_data():
    date_str = datetime.now().strftime('%Y-%m-%d')
    msg_path = os.path.join(EXPORT_DIR, f'messages_{date_str}.csv')
    users_path = os.path.join(EXPORT_DIR, f'users_{date_str}.csv')

    with sqlite3.connect(DB_PATH) as conn:
        messages = conn.execute('''
            SELECT users.username, messages.channel, messages.content, messages.timestamp
            FROM messages
            JOIN users ON messages.user_id = users.id
            ORDER BY messages.timestamp DESC
        ''').fetchall()
        with open(msg_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Utilisateur', 'Canal', 'Contenu', 'Horodatage'])
            writer.writerows(messages)

        users = conn.execute('SELECT id, username FROM users').fetchall()
        with open(users_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', "Nom d'utilisateur"])
            writer.writerows(users)

    print(f"[EXPORT] Messages exportés dans {msg_path}")
    print(f"[EXPORT] Utilisateurs exportés dans {users_path}")

def afficher_logs_audit():
    print("\n📜 Derniers logs audit :")
    try:
        with open(AUDIT_LOG, 'r') as f:
            lines = f.readlines()[-10:]
            for l in lines:
                print(l.strip())
    except FileNotFoundError:
        print("Aucun fichier de log trouvé.")

def envoyer_message_admin():
    canal = input("Sur quel canal envoyer ? (ex: #général, all): ").strip()
    texte = input("Contenu du message : ").strip()
    if texte:
        msg = {
            'type': 'message',
            'from': 'ADMIN',
            'channel': canal,
            'content': texte,
            'timestamp': datetime.now().isoformat()
        }
        if canal == 'all':
            broadcast(msg)
        elif canal in CHANNELS:
            broadcast(msg, channel=canal)
        else:
            print("Canal invalide")

def admin_console():
    while True:
        print("\n=== Console Admin ===")
        print("1. Voir les clients connectés")
        print("2. Voir l'état des canaux")
        print("3. Voir les utilisateurs et messages")
        print("4. Quitter le serveur")
        print("5. Exporter les données (messages + utilisateurs)")
        print("6. Afficher les logs audit")
        print("7. Envoyer un message (admin)")
        choix = input("Choix : ")
        if choix == '1':
            print("\n[Clients connectés] :")
            for sock, data in CLIENTS.items():
                print(f"- {data['username']} ({data['channel']})")
        elif choix == '2':
            print("\n[Canaux] :")
            for name, clients in CHANNELS.items():
                print(f"{name} : {len(clients)} client(s)")
        elif choix == '3':
            afficher_donnees()
        elif choix == '4':
            print("Arrêt du serveur...")
            broadcast({'type': 'server_shutdown', 'message': 'Le serveur va être déconnecté.'})
            for sock in list(CLIENTS):
                try:
                    sock.close()
                except:
                    pass
            os._exit(0)
        elif choix == '5':
            export_data()
        elif choix == '6':
            afficher_logs_audit()
        elif choix == '7':
            envoyer_message_admin()
        else:
            print("Choix invalide")

def afficher_donnees():
    with sqlite3.connect(DB_PATH) as conn:
        users = conn.execute('SELECT id, username FROM users').fetchall()
        print("\n📋 Utilisateurs :")
        for u in users:
            print(f"- ID: {u[0]} | Nom: {u[1]}")

        messages = conn.execute('SELECT user_id, channel, content, timestamp FROM messages ORDER BY id DESC LIMIT 10').fetchall()
        print("\n💬 Derniers messages :")
        for m in messages:
            print(f"[{m[3]}] (user {m[0]}) #{m[1]}: {m[2]}")

def main():
    init_database()
    log_audit("Base de données initialisée")
    threading.Thread(target=admin_console, daemon=True).start()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVEUR] En écoute sur {HOST}:{PORT}")
    while True:
        client, addr = server.accept()
        print(f"[NOUVELLE CONNEXION] {addr}")
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()

if __name__ == '__main__':
    main()
