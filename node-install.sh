bash -c "$(wget -qLO - https://github.com/community-scripts/ProxmoxVE/raw/main/misc/post-pve-install.sh)"
apt update
apt install figlet sudo -y
rm /etc/sudoers
echo '
Defaults        env_reset
Defaults        mail_badpass
Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults        use_pty
root    ALL=(ALL:ALL) ALL
host    ALL=(ALL:ALL) NOPASSWD: ALL
ssh ALL=(ALL) NOPASSWD: /usr/sbin/pct enter *
@includedir /etc/sudoers.d
' > /etc/sudoers
adduser ssh
adduser host
echo 'exit' > /root/.bashrc
wget -O /usr/bin/nossh https://raw.githubusercontent.com/katy-the-kat/kvm-i7-scripts/refs/heads/main/nossh
chmod +x /usr/bin/nossh
chsh -s /usr/bin/nossh ssh
wget -O /var/lib/vz/template/cache/ubuntu-22.04-standard_22.04-1_amd64.tar.zst http://download.proxmox.com/images/system/ubuntu-22.04-standard_22.04-1_amd64.tar.zst
