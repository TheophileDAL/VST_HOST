#!/bin/bash
echo "=== Installation des dépendances système ==="
xargs sudo apt install -y < apt-requirements.txt

echo "=== Installation des dépendances Python ==="
pip install -r requirements.txt --break-system-packages

echo "=== Terminé ! ==="
