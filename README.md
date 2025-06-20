
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

## 📙 Jour 4 – Jeudi : Fonctionnalités avancées et interface d’administration

### Objectifs pédagogiques
- Interface d'administration console
- Authentification SQLite (hashée)
- Gestion des canaux & multi-clients
- Logs audit/debug

### Nouveautés :
- `server_classcord.py` refondu
- `test_client.py`
- Logs : `audit.log`, `debug.log`, `classcord.log`, `server_stdout.log`
- `channel_switch` pour changer de canal

---

## 📒 Jour 5 – Vendredi : Exportation, outils d’analyse et intégration finale

### Objectifs pédagogiques
- Export CSV utilisateurs/messages
- Console interactive avec menus
- Menu console :
```
1. Voir les clients connectés
2. Voir l'état des canaux
3. Voir les utilisateurs et messages
4. Quitter le serveur
```

### Scripts
- `admin_view.py` (visualisation des données SQLite)
- `start_server.sh` (exécution en arrière-plan)
- Export CSV automatique dans `scripts/exports/`

---

## 🗂 Structure finale

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

Projet complet, reproductible, prêt à être présenté en évaluation ou soutenance.  
- Multi-clients / multi-canaux fonctionnels
- Sécurité, journalisation, persistance des données
- Exports automatisés pour analyse

