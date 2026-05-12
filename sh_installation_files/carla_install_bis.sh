#!/bin/bash
set -e

# Vérification root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root."
    exit 1
fi

REPO_URL="https://github.com/falkTX/Carla.git"
PLUGIN_NAME="Carla"
TMP_DIR="/tmp/carla-build"

echo "${PLUGIN_NAME} installation"

#2.Préparation dossier temporaire
echo "[+] Preparing build directory..."

if [ -d "$TMP_DIR" ]; then
    echo "[!] Existing directory found, removing..."
    rm -rf "$TMP_DIR"
fi

mkdir -p "$TMP_DIR"
cd "$TMP_DIR"

#3.Clonage ou mise à jour
if [ -d "guitarix" ]; then
    echo "[+] Repository already exists, updating..."
    cd Carla
    git pull
else
    echo "[+] Cloning repository..."
    git clone "$REPO_URL"
    cd Carla
fi

make

make install

echo "${PLUGIN_NAME} is succesfully installed"