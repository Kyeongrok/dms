#!/bin/bash
set -uex

USER=ingest
GROUP=resim
PASSWORD=password

groupadd $GROUP
adduser $USER -g $GROUP -ppassword
echo -e "${PASSWORD}\n${PASSWORD}" | passwd ingest

# add to sudo group
usermod -aG wheel $USER

# set passwordless sudo
echo "$USER ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers
