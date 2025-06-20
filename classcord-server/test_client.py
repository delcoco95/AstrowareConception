import socket
import json
import threading

HOST = '127.0.0.1'
PORT = 12345

def listen_for_messages(sock):
    buffer = ''
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                msg = json.loads(line)
                print("\n[REÇU]", msg)
        except Exception as e:
            print("[ERREUR RECEPTION]", e)
            break

def send_and_receive(sock, data):
    sock.sendall((json.dumps(data) + '\n').encode())

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    print("1. S'enregistrer")
    print("2. Se connecter")
    choice = input("Choix : ")

    username = input("Nom d'utilisateur : ")
    password = input("Mot de passe : ")

    if choice == '1':
        send_and_receive(sock, {
            "type": "register",
            "username": username,
            "password": password
        })

        print("Connexion automatique après enregistrement...")
        send_and_receive(sock, {
            "type": "login",
            "username": username,
            "password": password
        })
    else:
        send_and_receive(sock, {
            "type": "login",
            "username": username,
            "password": password
        })

    # Démarre l’écoute des messages
    threading.Thread(target=listen_for_messages, args=(sock,), daemon=True).start()

    # Envoi en boucle
    try:
        while True:
            msg = input()
            if msg.strip():
                send_and_receive(sock, {
                    "type": "message",
                    "content": msg
                })
    except KeyboardInterrupt:
        print("Déconnexion...")
        sock.close()

if __name__ == '__main__':
    main()
