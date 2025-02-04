#!/bin/sh

apt-get update
apt-get install ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update

apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker

cat <<EOF > Dockerfile
FROM ubuntu:22.04

#RUN sed -i -e 's|http://[^ ]*archive.ubuntu.com/ubuntu|http://my.archive.ubuntu.com/ubuntu|g' -e 's|http://[^ ]*security.ubuntu.com/ubuntu|http://my.archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list  
RUN apt-get update 
RUN yes | apt-get install -y nano htop wget dialog openssh-server openssh-client sudo tmate snapd curl iputils-ping
RUN yes | unminimize
RUN sed -i 's/^#\?\s*PermitRootLogin\s\+.*/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN echo 'root:root' | chpasswd
RUN printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d
RUN apt-get install -y systemd systemd-sysv dbus dbus-user-session
RUN printf "systemctl start systemd-logind" >> /etc/profile

ENTRYPOINT ["/sbin/init"]
EOF

docker build -t utmp .

docker network create --subnet=10.73.17.0/24 kvmnet

cat <<EOF > Dockerfile2
FROM ubuntu:22.04  
RUN apt update
RUN apt install -y openssh-server curl sudo wget dialog tmate
RUN mkdir /var/run/sshd
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config  
CMD ["/usr/sbin/sshd", "-D"]
EOF

docker build -t tmatelol -f Dockerfile2 . 

echo "fs.inotify.max_user_instances = 2147483647" > /etc/sysctl.conf 
sysctl -p 

clear && echo done
