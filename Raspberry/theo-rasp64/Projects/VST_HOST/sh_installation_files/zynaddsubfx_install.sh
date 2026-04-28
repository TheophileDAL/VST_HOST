#!/bin/bash
set -e

# Vérification root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root."
    exit 1
fi

PLUGIN_NAME="Zynaddsubfx"
DOWNLOAD_PATH="/tmp/kxstudio-repos.deb"
PACKAGE_URL="https://launchpad.net/~kxstudio-debian/+archive/kxstudio/+files/kxstudio-repos_11.2.0_all.deb"

echo "${PLUGIN_NAME} installation"

echo "Mise à jour des paquets..."
apt-get update -y

# Install required dependencies
apt-get install -y gpgv wget

# Download package file
wget -4 -q -O "$DOWNLOAD_PATH" "$PACKAGE_URL"

# Install it
dpkg -i "$DOWNLOAD_PATH"

# Mise à jour après ajout du repo KXStudio
apt-get update -y

# Zynaddsubfx installation
apt-get install -y zynaddsubfx

echo "Nettoyage..."
rm -f "$DOWNLOAD_PATH"

echo "${PLUGIN_NAME} is succesfully installed"
