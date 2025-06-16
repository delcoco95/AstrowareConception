import socket
import json

def send_json_message(sock, message):
    json_data = json.dumps(message)
    sock.send((json_data + '\n').encode('utf-8'))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 12345))

# Test d'enregistrement
register_message = {
    "type": "register",
    "username": "testuser",
    "password": "testpass"
}

try:
    print("Envoi demande d'enregistrement...")
    send_json_message(client, register_message)
    response = client.recv(1024).decode('utf-8')
    print(f"Réponse du serveur: {response}")
    
    # Test de login
    login_message = {
        "type": "login",
        "username": "testuser",
        "password": "testpass"
    }
    
    print("\nEnvoi demande de connexion...")
    send_json_message(client, login_message)
    response = client.recv(1024).decode('utf-8')
    print(f"Réponse du serveur: {response}")

except Exception as e:
    print(f"Erreur: {e}")
finally:
    client.close()