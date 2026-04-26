#!/bin/bash
set -e

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
7z x "$DOWNLOAD_PATH" -o"$INSTALL_DIR"

rm "/usr/local/bin/organteq"

echo "Création du lien symbolique..."
ln -sf "$INSTALL_DIR/Organteq 2/arm-64bit/Organteq 2" /usr/local/bin/organteq

echo "Nettoyage..."
rm "$DOWNLOAD_PATH"

echo "${PLUGIN_NAME} is succesfully installed"