#!/usr/bin/env bash

set -e

# Vérification root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root."
    exit 1
fi

PLUGIN_NAME="Guitarix"
echo "${PLUGIN_NAME} installation"

# Variables
REPO_URL="https://github.com/brummer10/guitarix.git"
TMP_DIR="/tmp/guitarix-build"
INSTALL_PREFIX="/opt"

#1.Dépendances
echo "[+] Installing dependencies..."

apt-get update -y
apt-get install -y \
    git build-essential pkg-config \
    python3 gettext intltool sassc \
    liblrdf-dev \
    ladspa-sdk \
    libgtkmm-3.0-dev \
    libglibmm-2.4-dev libsigc++-2.0-dev \
    libjack-jackd2-dev jackd2 \
    libasound2-dev \
    libboost-iostreams-dev \
    libboost-dev \
    libfftw3-dev \
    libeigen3-dev \
    libsndfile1-dev \
    libsamplerate0-dev \
    libzita-convolver-dev \
    libzita-resampler-dev \
    lv2-dev \
    liblilv-dev \
    libserd-dev libsord-dev libsratom-dev \
    liblo-dev \
    libcurl4-openssl-dev \
    libavahi-client-dev \
    libcairo2-dev \
    libx11-dev \
    libavahi-gobject-dev

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
    cd guitarix
    git pull
else
    echo "[+] Cloning repository..."
    git clone "$REPO_URL"
    cd guitarix
fi

#4.Configuration
git submodule update --init --recursive
cd trunk
echo "[+] Configuring (waf)..."
./waf configure --prefix="$INSTALL_PREFIX" --includeresampler --includeconvolver --optimization

mkdir -p /usr/include/lv2/lv2plug.in/ns/ext
mkdir -p /usr/include/lv2/lv2plug.in/ns/extensions

for dir in /usr/include/lv2/*/; do
    name=$(basename "$dir")
    ln -sf "$dir" "/usr/include/lv2/lv2plug.in/ns/extensions/$name"
done

for dir in /usr/include/lv2/*/; do
    name=$(basename "$dir")
    ln -sf "$dir" "/usr/include/lv2/lv2plug.in/ns/ext/$name"
done

#5.Compilation
echo "[+] Building..."
./waf build

#6.Installation
echo "[+] Installing..."
./waf install

#7.Refresh libs
ldconfig

echo "${PLUGIN_NAME} is succesfully installed"
