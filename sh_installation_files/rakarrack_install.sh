#!/usr/bin/env bash

set -e

# Vérification root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root."
    exit 1
fi

PLUGIN_NAME="Rakarrack-plus"
TMP_DIR="/tmp"

echo "${PLUGIN_NAME} installation"

#1.Dépendances (Debian/Ubuntu)
echo "[+] Installation des dépendances..."
apt-get update -y
apt-get install -y \
    git build-essential cmake \
    libfltk1.3-dev \
    libx11-dev libxext-dev libxft-dev libxinerama-dev libxcursor-dev libxfixes-dev \
    libpng-dev libjpeg-dev libsndfile1-dev libsamplerate0-dev \
    libfftw3-dev liblo-dev \
    libasound2-dev jackd2 libjack-jackd2-dev \
    lv2-dev \
    libxpm-dev \
    libcairo2-dev \
    libzita-resampler-dev \
    xvfb

cd "$TMP_DIR"

#2.Getting NTK
if [ -d "${TMP_DIR}/ntk-unofficial" ]; then
    echo "[!] Existing directory found, removing..."
    rm -rf "${TMP_DIR}/ntk-unofficial"
fi

git clone https://github.com/Stazed/ntk-unofficial.git
cd ntk-unofficial
mkdir build
cd build
cmake ..
make
make install

#3.Récupération du code source de Rakarrack-plus

if [ -d "${TMP_DIR}/rakarrack-plus" ]; then
    echo "[!] Existing directory found, removing..."
    rm -rf "${TMP_DIR}/rakarrack-plus"
fi

echo "[+] Clonage du dépot..."
git clone https://github.com/Stazed/rakarrack-plus.git
cd rakarrack-plus

ln -sf /usr/include/lv2/core/lv2.h /usr/include/lv2.h

mkdir -p /usr/include/lv2/lv2plug.in/ns/ext
mkdir -p /usr/include/lv2/lv2plug.in/ns/extensions
mkdir -p /usr/include/lv2/lv2plug.in/ns/lv2core

ln -sf /usr/include/lv2/core/lv2.h /usr/include/lv2/lv2plug.in/ns/lv2core/lv2.h

for dir in /usr/include/lv2/*/; do
    name=$(basename "$dir")
    # Ignore lv2plug.in pour éviter la récursion
    [ "$name" = "lv2plug.in" ] && continue
    ln -sf "$dir" "/usr/include/lv2/lv2plug.in/ns/ext/$name"
    ln -sf "$dir" "/usr/include/lv2/lv2plug.in/ns/extensions/$name"
done

#4.Compilation
echo "[+] Compilation..."
mkdir -p build
cd build

cmake ..

#5.Installation
echo "[+] Installation..."
make install

#6.Rafraichissement cache
ldconfig

echo "${PLUGIN_NAME} is succesfully installed"
