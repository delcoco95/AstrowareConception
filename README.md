
# 📘 Documentation Projet Classcord

**Installation, déploiement, sécurisation et maintenance**  
_Mise à jour : 18 juin 2025_

---

## 📕 Jour 1 - Lundi : Prise en main, exécution locale et configuration VM

### Objectifs pédagogiques
- Comprendre le fonctionnement du serveur Python
- Créer une machine virtuelle sous Debian
- Tester le serveur localement avec des clients
- Mettre en place les premiers outils réseau (UFW)

### 1. Création d’une machine virtuelle Debian 11
- Hyperviseur : VirtualBox (ou autre)
- Nom : `Classcord`
- Type : Linux / Debian (64-bit)
- RAM : 2 Go
- Disque dur : 20 Go (VDI, alloué dynamiquement)
- Réseau :
  - **Adaptateur 1** : NAT
  - **Adaptateur 2** : Réseau privé hôte

### 2. Installation de Debian
- Langue : Français
- Localisation : France
- Clavier : Français
- Partition : Guidée – utiliser tout le disque
- Environnement de bureau : Aucun
- Activer serveur SSH

### 3. Installation des outils essentiels
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl python3 python3-pip ufw
```

### 4. Clonage du projet serveur
```bash
git clone https://github.com/AstrowareConception/classcord-server.git
cd classcord-server
```

### 5. Lancement du serveur Python
```bash
python3 server_classcord.py
```

### 6. Test multi-clients
- Port utilisé : `12345`
- Connexion client via JSON
- Logs affichés dans la console

### 7. Vérification réseau et ouverture du port
```bash
ss -tulpn | grep 12345
sudo ufw allow 12345/tcp
```

---

## 📗 Jour 2 - Mardi : Déploiement réseau, automatisation et Docker

### Objectifs pédagogiques
- Déployer le serveur sur réseau pédagogique
- Automatiser avec systemd
- Conteneuriser avec Docker
- Documenter l'accès

### 1. Vérification de l’écoute réseau
```bash
sudo ufw allow 12345/tcp
ss -tulpn | grep 12345
hostname -I
```

### 2. Création d’un utilisateur dédié
```bash
sudo useradd -m classcord
sudo passwd classcord
su - classcord
```

### 3. Création du service systemd
Fichier : `/etc/systemd/system/classcord.service`
```ini
[Unit]
Description=Serveur ClassCord
After=network.target

[Service]
User=classcord
WorkingDirectory=/home/classcord/classcord-server
ExecStart=/usr/bin/python3 /home/classcord/classcord-server/server_classcord.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Activation :
```bash
sudo systemctl daemon-reexec
sudo systemctl enable --now classcord.service
```

### 4. Dockerfile (racine du projet)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt || true
EXPOSE 12345
CMD ["python", "server_classcord.py"]
```

### 5. docker-compose.yml
```yaml
version: '3'
services:
  classcord:
    build: .
    ports:
      - "12345:12345"
    restart: unless-stopped
```

### 6. Tests
```bash
docker build -t classcord-server .
docker run -it --rm -p 12345:12345 classcord-server
```

Fichiers à produire : `doc_connexion.md`, `CONTAINERS.md`

---

## 📖 Jour 3 - Mercredi : Sécurisation, journalisation et monitoring

### Objectifs
- Logger tous les événements
- Protéger avec fail2ban
- Sauvegarder automatiquement `users.pkl`
- Automatiser avec cron

### 1. Configuration des logs (Python)
```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('/var/log/classcord/classcord.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
```

Créer le dossier :
```bash
sudo mkdir -p /var/log/classcord
sudo chown -R classcord:classcord /var/log/classcord
```

### 2. Rotation des logs avec logrotate
Fichier `/etc/logrotate.d/classcord` :
```conf
/var/log/classcord/classcord.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 classcord classcord
    postrotate
        systemctl restart classcord.service
    endscript
}
```

### 3. Fail2ban

Fichier `/etc/fail2ban/filter.d/classcord.conf` :
```conf
[Definition]
failregex = \[LOGIN\] Failed login attempt from <HOST>
ignoreregex =
```

Fichier `/etc/fail2ban/jail.local` :
```conf
[classcord]
enabled = true
port = 12345
filter = classcord
logpath = /var/log/classcord/classcord.log
maxretry = 3
findtime = 300
bantime = 3600
```

### 4. Sauvegarde automatique (cron)
```bash
crontab -e
```

Ajouter :
```cron
0 * * * * cp /home/classcord/classcord-server/users.pkl /home/classcord/backups/users-$(date +\%F-\%H\%M).pkl
```

### 5. Outils de surveillance utiles
```bash
sudo tail -f /var/log/classcord/classcord.log
sudo fail2ban-client status classcord
sudo systemctl status classcord.service
sudo journalctl -u classcord.service -f
```

---


## 📘 Jour 4 – Jeudi : Améliorations fonctionnelles, personnalisation et administration

### 🎯 Objectifs pédagogiques
- Gérer les canaux de discussion côté serveur
- Stocker de façon persistante les utilisateurs et messages
- Mettre en place un menu administrateur
- Créer un script d’export CSV
- Gérer la déconnexion des clients et l’arrêt du serveur

---

### 🧠 1. Gestion des canaux

Structure créée dans le code :
```python
CHANNELS = {'#général': [], '#dev': [], '#admin': []}
```

Adaptation du serveur pour :
- Attribuer un canal à chaque client connecté
- Diffuser uniquement aux clients présents dans le même canal

Extrait :
```python
def broadcast(message, channel=None, exclude=None):
    targets = CHANNELS[channel] if channel else sum(CHANNELS.values(), [])
    for client in targets:
        if client != exclude:
            ...
```

---

### 🛠️ 2. Stockage persistant avec SQLite

Commandes :
```bash
mkdir -p config/database
```

Initialisation automatique dans le script :
```python
DB_PATH = 'config/database/classcord.db'
```

Création des tables :
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    channel TEXT,
    content TEXT,
    timestamp TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

Les mots de passe sont hachés en SHA256 :
```python
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()
```

---

### 🖥️ 3. Console administrateur (menu intégré)

Ajout dans le serveur :
```python
def admin_console():
    while True:
        print("1. Voir les clients connectés")
        print("2. Voir l'état des canaux")
        print("3. Voir les utilisateurs et messages")
        ...
```

Accessible en parallèle via un `thread` :
```python
threading.Thread(target=admin_console, daemon=True).start()
```

---

### 📋 4. Script `admin_view.py`

Fonction :
- Affiche les utilisateurs et les messages récents
- Utilise `sqlite3` et `tabulate`

Installation de la dépendance :
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install tabulate
```

Utilisation :
```bash
python3 admin_view.py
```

---

### 📦 5. Export CSV des messages et utilisateurs

Fichiers générés automatiquement :
- `scripts/exports/messages_export_YYYY-MM-DD.csv`
- `scripts/exports/users_export_YYYY-MM-DD.csv`

Structure créée :
```bash
mkdir -p scripts/exports
```

Code :
```python
with open(f"scripts/exports/messages_export_{date.today()}.csv", "w") as f:
    writer = csv.writer(f)
    ...
```

---

### 🔁 6. Notification des clients à l'arrêt

Lorsqu’un administrateur arrête le serveur :
```python
for sock in list(CLIENTS.keys()):
    try:
        send_json(sock, {"type": "shutdown", "message": "Serveur arrêté."})
    except:
        pass
```

Les clients reçoivent un message de fin et ferment leur socket.

---

### ✅ Résumé des livrables
- Serveur avec gestion de canaux
- Authentification sécurisée par hash
- Menu administrateur intégré
- Base de données SQLite fonctionnelle
- Script `admin_view.py` utilisable
- Export CSV automatisé

---
## 📘 Jour 5 – Vendredi : Finalisation, automatisation système et bilan

### 🎯 Objectifs pédagogiques
- Intégrer le serveur dans le système (systemd)
- Automatiser le démarrage et le redémarrage en cas d’échec
- Vérifier la stabilité multi-clients
- Documenter tout le projet de manière claire
- Exporter les données (utilisateurs, messages)
- S’assurer de la sécurité et du suivi du serveur

---

### 🛠️ 1. Service systemd

Création du fichier :
```bash
sudo nano /etc/systemd/system/classcord.service
```

Contenu :
```ini
[Unit]
Description=Serveur ClassCord
After=network.target

[Service]
User=classcord
WorkingDirectory=/home/classcord/classcord-server
ExecStart=/usr/bin/python3 /home/classcord/classcord-server/server_classcord.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Commandes :
```bash
sudo systemctl daemon-reexec
sudo systemctl enable --now classcord.service
```

Vérification :
```bash
sudo systemctl status classcord.service
sudo journalctl -u classcord.service -f
```

---

### 🧪 2. Test multi-clients (fonctionnel)

- Lancement simultané de plusieurs `test_client.py`
- Chaque client peut :
  - s’enregistrer
  - se connecter
  - envoyer/recevoir des messages en temps réel
  - changer de canal

Exemple de réception :
```json
{ "type": "message", "from": "lia", "channel": "#général", "content": "salut leo", "timestamp": "..." }
```

---

### 📤 3. Exportation des données

Dans l’interface console (admin) :
```text
3. Voir les utilisateurs et messages
```

➡️ Génère :
- `scripts/exports/messages_export_2025-06-20.csv`
- `scripts/exports/users_export_2025-06-20.csv`

---

### 🧾 4. Journalisation complète

| Fichier                     | Contenu                                                                 |
|----------------------------|-------------------------------------------------------------------------|
| `logs/classcord.log`       | Activité standard du serveur                                            |
| `logs/audit.log`           | Actions administratives (alerte, changement canal, arrêt serveur...)   |
| `logs/debug.log`           | Infos détaillées, erreurs de threads, exceptions techniques             |
| `logs/server_stdout.log`   | Sortie standard du serveur (si lancé via `start_server.sh`)            |

Commandes utiles :
```bash
tail -f logs/classcord.log
tail -f logs/audit.log
```

---

### 🧹 5. Nettoyage et sécurité finale

- Suppression de `users.pkl` si encore présent
```bash
rm users.pkl
```

- Vérification des permissions sur la base SQLite :
```bash
chmod 600 config/database/classcord.db
```

- Vérification des ports :
```bash
ss -tulpn | grep 12345
```

- Activation pare-feu :
```bash
sudo ufw allow 12345/tcp
sudo ufw enable
```

---

### ✅ Résumé des livrables
- Serveur stable et multi-clients
- Données utilisateurs/messages persistantes
- Export CSV automatisé
- Interface console opérationnelle
- Démarrage automatique avec systemd
- Journalisation complète et filtrable

---

## 🗂 Arborescence projet
```
classcord-server/
├── server_classcord.py
├── test_client.py
├── admin_view.py
├── start_server.sh
├── config/
│   ├── database/
│   ├── fail2ban/
│   ├── logrotate/
│   └── systemd/
├── logs/
│   ├── audit.log
│   ├── debug.log
│   ├── classcord.log
│   └── server_stdout.log
├── scripts/
│   └── exports/
│       ├── messages_YYYY-MM-DD.csv
│       └── users_YYYY-MM-DD.csv
```

---

## ✅ Conclusion

- Projet prêt à déployer et documenté
- Fonctionnalités avancées : multi-clients, sécurité, logging, base de données
- Livrables disponibles pour évaluation
