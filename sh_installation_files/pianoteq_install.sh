#!/bin/bash
set -e

PLUGIN_NAME="Pianoteq"
DOWNLOAD_PATH="$1"
INSTALL_DIR="/opt/pianoteq"

if [ -z "$DOWNLOAD_PATH" ] || [ ! -f "$DOWNLOAD_PATH" ]; then
    echo "ERROR: Fichier introuvable : $DOWNLOAD_PATH"
    exit 1
fi

echo "${PLUGIN_NAME} installation"

echo "Mise à jour des paquets..."
apt-get update -y

#Dependencie to extract tar.xz downloaded file
echo "Installation de p7zip..."
apt-get install -y tar

echo "Extraction de l'archive..."
mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER /opt/pianoteq
tar -xf "$DOWNLOAD_PATH" -C "$INSTALL_DIR"

if [ -d "/usr/local/bin/pianoteq" ]; then
    echo "[!] Existing directory found, removing..."
    rm -rf "/usr/local/bin/pianoteq"
fi

echo "Création du lien symbolique..."
ln -sf "$INSTALL_DIR/Pianoteq 9/arm-64bit/Pianoteq 9" /usr/local/bin/pianoteq

echo "Nettoyage..."
rm "$DOWNLOAD_PATH"

echo "${PLUGIN_NAME} is succesfully installed"
