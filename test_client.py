import socket
import json
import threading
import time

def send_json_message(sock, message):
    json_data = json.dumps(message)
    sock.send((json_data + '\n').encode('utf-8'))

def receive_messages(sock):
    while True:
        try:
            response = sock.recv(1024).decode('utf-8')
            if response:
                print(f"\nMessage reçu: {response}")
        except:
            break

def start_receiver(sock):
    receiver_thread = threading.Thread(target=receive_messages, args=(sock,))
    receiver_thread.daemon = True
    receiver_thread.start()
    return receiver_thread

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 12345))

try:
    # Démarrer le thread de réception
    receiver_thread = start_receiver(client)

    # Register first
    register_message = {
        "type": "register",
        "username": "testuser",
        "password": "testpass"
    }
    
    print("\nEnvoi demande d'enregistrement...")
    send_json_message(client, register_message)
    time.sleep(1)  # Attendre la réponse

    # Then login
    login_message = {
        "type": "login",
        "username": "testuser",
        "password": "testpass"
    }
    
    print("\nEnvoi demande de connexion...")
    send_json_message(client, login_message)
    time.sleep(1)  # Attendre la réponse

    # Boucle principale pour envoyer des messages
    while True:
        message = input("\nEntrez votre message (ou 'quit' pour quitter): ")
        if message.lower() == 'quit':
            break
            
        chat_message = {
            "type": "message",
            "content": message
        }
        send_json_message(client, chat_message)

except KeyboardInterrupt:
    print("\nFermeture du client...")
except Exception as e:
    print(f"Erreur: {e}")
finally:
    client.close()