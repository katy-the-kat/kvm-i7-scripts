bash -c "$(wget -qLO - https://github.com/community-scripts/ProxmoxVE/raw/main/misc/post-pve-install.sh)"
apt update
apt install figlet sudo -yr
rm /etc/sudoers
echo '
Defaults        env_reset
Defaults        mail_badpass
Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults        use_pty
root    ALL=(ALL:ALL) ALL
ssh ALL=(ALL) NOPASSWD: /usr/sbin/pct enter *
@includedir /etc/sudoers.d
' > /etc/sudoers
pip3 install discord paramiko docker requests --break-system-packages
adduser ssh
wget -O /usr/bin/nossh https://raw.githubusercontent.com/katy-the-kat/kvm-i7-scripts/refs/heads/main/nossh
chmod +x /usr/bin/nossh
chsh -s /usr/bin/nossh ssh
