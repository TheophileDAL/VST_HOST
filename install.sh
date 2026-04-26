#!/bin/bash
set -e
 
# Vérification root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root."
    exit 1
fi
 
echo "=== Installation des dépendances système ==="
apt-get update -y
xargs apt-get install -y < apt_requirements.txt
 
echo "=== Installation des dépendances Python ==="
pip install -r requirements.txt --break-system-packages
 
echo "=== Terminé ! ==="
