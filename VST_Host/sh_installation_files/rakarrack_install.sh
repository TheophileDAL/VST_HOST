#!/usr/bin/env bash

set -e

PLUGIN_NAME="Rakarrack-plus"

echo "${PLUGIN_NAME} installation"

# 1.Dépendances (Debian/Ubuntu)
echo "[+] Installation des dépendances..."
sudo apt update
sudo apt install -y \
    git build-essential cmake \
    libfltk1.3-dev \
    libx11-dev libxext-dev libxft-dev libxinerama-dev libxcursor-dev libxfixes-dev \
    libpng-dev libjpeg-dev libsndfile1-dev libsamplerate0-dev \
    libfftw3-dev liblo-dev \
    libasound2-dev jackd2 libjack-jackd2-dev \
    lv2-dev

# 2.Récupération du code source
echo "[+] Clonage du dépot..."
git clone https://github.com/Stazed/rakarrack-plus.git
cd rakarrack-plus

# 3.Compilation
echo "[+] Compilation..."
mkdir -p build
cd build

cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DBuildCarlaPresets=ON

make -j$(nproc)

# 4.Installation
echo "[+] Installation..."
sudo make install

# 5.Rafraichissement cache
sudo ldconfig

echo "${PLUGIN_NAME} is succesfully installed"