#!/bin/bash

apt update > /dev/null &
apt full-upgrade > /dev/null &

clear
cat > /etc/ssh/sshd_config << EOF
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
EOF

systemctl restart sshd
ssh-keygen -t rsa -b 4096 -m PEM -f /root/.ssh/id_rsa -N '' <<<y >/dev/null 2>&1
cp /root/.ssh/id_rsa /root/.ssh/private_key.pem
cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
chmod 600 /root/.ssh/private_key.pem
chmod 644 /root/.ssh/id_rsa.pub
UPLOAD_OUTPUT=$(curl -s bashupload.com -T /root/.ssh/private_key.pem)
DOWNLOAD_LINK=$(echo "$UPLOAD_OUTPUT" | grep -o 'http://bashupload.com/[^ ]*')
IP=$(hostname -i)
echo -e "\nIP: $IP\nUser: root\nSSH Key Download: $DOWNLOAD_LINK"
