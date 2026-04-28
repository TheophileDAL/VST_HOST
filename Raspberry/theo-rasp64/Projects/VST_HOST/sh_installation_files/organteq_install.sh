#!/bin/bash
set -e

# Vérification root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root."
    exit 1
fi

PLUGIN_NAME="Organteq"
DOWNLOAD_PATH="$1"   # chemin du .7z déjà téléchargé par Python
INSTALL_DIR="/opt/organteq"

if [ -z "$DOWNLOAD_PATH" ] || [ ! -f "$DOWNLOAD_PATH" ]; then
    echo "ERROR: Fichier introuvable : $DOWNLOAD_PATH"
    exit 1
fi

echo "${PLUGIN_NAME} installation"

echo "Mise à jour des paquets..."
apt-get update -y

# Dependencie to extract 7z downloaded file
echo "Installation de p7zip..."
apt-get install -y p7zip-full

echo "Extraction de l'archive..."
mkdir -p "$INSTALL_DIR"
7z x -y "$DOWNLOAD_PATH" -o"$INSTALL_DIR"

if [ -L "/usr/local/bin/organteq" ]; then
    echo "[!] Existing symlink found, removing..."
    rm -f "/usr/local/bin/organteq"
fi

echo "Création du lien symbolique..."
ln -sf "$INSTALL_DIR/Organteq 2/arm-64bit/Organteq 2" /usr/local/bin/organteq

echo "Nettoyage..."
rm -f "$DOWNLOAD_PATH"

echo "${PLUGIN_NAME} is succesfully installed"
