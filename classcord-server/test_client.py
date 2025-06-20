import socket
import json
import threading

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(sock):
    buffer = ''
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                print("[REÇU]", json.loads(line))
        except:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("❌ Impossible de se connecter au serveur.")
        return

    print("1. S'enregistrer")
    print("2. Se connecter")
    print("3. Se connecter en tant qu'invité")
    choix = input("Choix : ")

    if choix == '1':
        username = input("Nom d'utilisateur : ")
        password = input("Mot de passe : ")
        sock.sendall(json.dumps({"type": "register", "username": username, "password": password}).encode() + b'\n')
        sock.sendall(json.dumps({"type": "login", "username": username, "password": password}).encode() + b'\n')
    elif choix == '2':
        username = input("Nom d'utilisateur : ")
        password = input("Mot de passe : ")
        sock.sendall(json.dumps({"type": "login", "username": username, "password": password}).encode() + b'\n')
    elif choix == '3':
        username = input("Nom affiché (laisser vide pour aléatoire) : ") or f"Invité{socket.gethostname()}"
        password = "guest"
        sock.sendall(json.dumps({"type": "register", "username": username, "password": password}).encode() + b'\n')
        sock.sendall(json.dumps({"type": "login", "username": username, "password": password}).encode() + b'\n')
    else:
        print("Choix invalide.")
        sock.close()
        return

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    while True:
        try:
            msg = input()
            if msg == "/quit":
                break
            sock.sendall(json.dumps({"type": "message", "content": msg}).encode() + b'\n')
        except:
            break

    sock.close()

if __name__ == "__main__":
    main()
