#!/bin/bash

# Script de démarrage du serveur Classcord
# Créé par: delcoco95
# Date: 2025-06-17 14:08:22 UTC

echo "Démarrage du serveur Classcord..."

# Vérifie si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Erreur: Python3 n'est pas installé"
    exit 1
fi

# Se place dans le répertoire du serveur
cd "$(dirname "$0")/.." || exit 1

# Lance le serveur
python3 server_classcord.py

# Capture le code de sortie
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "Erreur: Le serveur s'est arrêté avec le code $exit_code"
    exit $exit_code
fi