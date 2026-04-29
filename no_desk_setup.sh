#!/bin/bash

# Installation des dépendances
source install.sh
 
ACTUAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 
# Détecte automatiquement l'utilisateur réel
if [ "$SUDO_USER" ]; then
    CURRENT_USER=$SUDO_USER
    USER_ID=$(id -u $SUDO_USER)
else
    CURRENT_USER=$(whoami)
    USER_ID=$(id -u)
fi
 
SERVICE_FILE=/etc/systemd/system/vst_host.service
INSTALL_DIR=$ACTUAL_DIR/sh_installations_file
 
# Autoriser tous les scripts d'installation sans mot de passe
echo "=== Configuration des droits sudo pour les scripts d'installation ==="
SUDOERS_LINE="$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/bash $INSTALL_DIR/*.sh"
SUDOERS_FILE=/etc/sudoers.d/vst_host
 
echo "$SUDOERS_LINE" | sudo tee $SUDOERS_FILE > /dev/null
sudo chmod 440 $SUDOERS_FILE
echo "    Droits configurés dans $SUDOERS_FILE"
 
if [ -f "$SERVICE_FILE" ]; then
    echo "=== Le service existe déjà. Remplacement... ==="
    sudo systemctl stop vst_host.service 2>/dev/null
    sudo systemctl disable vst_host.service 2>/dev/null
fi
 
echo "=== Création du service systemd ==="
 
sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=VST Host
After=multi-user.target bluetooth.target sound.target
Wants=bluetooth.target sound.target
 
[Service]
Type=simple
User=$CURRENT_USER
Group=audio
Environment=HOME=/home/$CURRENT_USER
Environment=XDG_RUNTIME_DIR=/run/user/$USER_ID
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$USER_ID/bus
Environment=QT_QPA_PLATFORM=offscreen
LimitRTPRIO=95
LimitMEMLOCK=infinity
ExecStart=python3 $ACTUAL_DIR/vst_host.py
Restart=on-failure
StandardOutput=append:$ACTUAL_DIR/vst_host.log
StandardError=append:$ACTUAL_DIR/vst_host.log
 
[Install]
WantedBy=multi-user.target
EOF
 
echo "=== Activation du linger pour $CURRENT_USER ==="
sudo loginctl enable-linger $CURRENT_USER
 
echo "=== Ajout de $CURRENT_USER au groupe audio ==="
sudo usermod -aG audio $CURRENT_USER
 
echo "=== Rechargement de systemd ==="
sudo systemctl daemon-reload
 
echo "=== Activation du service au démarrage ==="
sudo systemctl enable vst_host.service
 
echo "=== Démarrage immédiat de VST HOST ==="
sudo systemctl start vst_host.service
 
echo ""
echo "=== VST HOST est lancé ==="
