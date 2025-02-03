#!/bin/sh

apt install nano docker.io -y

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

cat <<EOF > Dockerfile
FROM ubuntu:22.04

#RUN sed -i -e 's|http://[^ ]*archive.ubuntu.com/ubuntu|http://my.archive.ubuntu.com/ubuntu|g' -e 's|http://[^ ]*security.ubuntu.com/ubuntu|http://my.archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list  
RUN apt-get update 
RUN yes | apt-get install -y nano htop wget dialog openssh-server openssh-client sudo snapd curl iputils-ping
RUN sed -i 's/^#\?\s*PermitRootLogin\s\+.*/PermitRootLogin yes/' /etc/ssh/sshd_config

ENTRYPOINT ["/sbin/init"]
EOF

echo "fs.inotify.max_user_instances = 2147483647" > /etc/sysctl.conf 
sysctl -p 

clear && echo done
