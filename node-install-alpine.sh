#!/bin/sh

apk update
apk add nano docker bc bash

rc-update add docker boot
service docker start

cat <<EOF > Dockerfile
FROM ubuntu:22.04

#RUN sed -i -e 's|http://[^ ]*archive.ubuntu.com/ubuntu|http://my.archive.ubuntu.com/ubuntu|g' -e 's|http://[^ ]*security.ubuntu.com/ubuntu|http://my.archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list  
RUN apt-get update 
RUN yes | apt-get install -y nano htop wget dialog openssh-server openssh-client sudo tmate snapd
RUN yes | unminimize
RUN wget -O /usr/bin/port https://raw.githubusercontent.com/katy-the-kat/realinstallscript/refs/heads/main/ipv4x
RUN chmod +x /usr/bin/port
RUN sed -i 's/^#\?\s*PermitRootLogin\s\+.*/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN echo 'root:root' | chpasswd
RUN printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d
RUN apt-get install -y systemd systemd-sysv dbus dbus-user-session
RUN printf "systemctl start systemd-logind" >> /etc/profile

ENTRYPOINT ["/sbin/init"]
EOF

docker build -t utmp .

clear && echo done
