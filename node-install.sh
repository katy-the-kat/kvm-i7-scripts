bash -c "$(wget -qLO - https://github.com/community-scripts/ProxmoxVE/raw/main/misc/post-pve-install.sh)"
apt update
apt install python3 sshpass figlet python3-pip -y
pip3 install discord paramiko docker requests --break-system-packages
adduser ssh
wget -O /usr/bin/nossh 
chmod +x /usr/bin/nossh
chsh -s /usr/bin/nossh ssh
