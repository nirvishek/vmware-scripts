#!/bin/bash
IP=$1
GATEWAY=$2
DNS=$3
rm -f /etc/netplan/*.yml /etc/netplan/*.yaml
cat > /etc/netplan/network.yaml <<EOF
network:
  version: 2
  ethernets:
    eth0:
      addresses:
      - $IP
      gateway4: $GATEWAY
      nameservers:
        addresses:
        - $DNS
      dhcp4: false
EOF
netplan apply
