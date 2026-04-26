#!/bin/bash
set -e

PLUGIN_NAME="Zynaddsubfx"
DOWNLOAD_PATH="/tmp/kxstudio-repos.deb"
PACKAGE_URL="https://launchpad.net/~kxstudio-debian/+archive/kxstudio/+files/kxstudio-repos_11.2.0_all.deb"

echo "${PLUGIN_NAME} installation"

echo "Mise à jour des paquets..."
apt-get update -y

# Install required dependencies
apt-get install -y gpgv wget

# Download package file
wget -O "$DOWNLOAD_PATH" "$PACKAGE_URL"

# Install it
dpkg -i "$DOWNLOAD_PATH"

#Carla installation
apt install -y zynaddsubfx

echo "Nettoyage..."
rm "$DOWNLOAD_PATH"

echo "${PLUGIN_NAME} is succesfully installed"