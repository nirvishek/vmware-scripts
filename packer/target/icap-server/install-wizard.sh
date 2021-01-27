#!/bin/bash

# install wizard for ova/esxi.
# defining vars
DEBIAN_FRONTEND=noninteractive
KERNEL_BOOT_LINE='net.ifnames=0 biosdevname=0'

# sudo without password prompt
echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER >/dev/null

# update packages
sudo apt update && sudo apt upgrade -y

# install needed packages
sudo apt install -y telnet tcpdump open-vm-tools net-tools dialog curl git sed grep fail2ban
sudo systemctl enable fail2ban.service
sudo tee -a /etc/fail2ban/jail.d/sshd.conf << EOF > /dev/null
[sshd]
enabled = true
port = ssh
action = iptables-multiport
logpath = /var/log/auth.log
bantime  = 10h
findtime = 10m
maxretry = 5
EOF
sudo systemctl restart fail2ban

# switching to predictable network interfaces naming
grep "$KERNEL_BOOT_LINE" /etc/default/grub >/dev/null || sudo sed -Ei "s/GRUB_CMDLINE_LINUX=\"(.*)\"/GRUB_CMDLINE_LINUX=\"\1 $KERNEL_BOOT_LINE\"/g" /etc/default/grub

# cloning vmware scripts repo
git clone --single-branch -b main https://github.com/k8-proxy/vmware-scripts.git ~/scripts

# installing the wizard
sudo install -T ~/scripts/scripts/wizard/wizard.sh /usr/local/bin/wizard -m 0755

# installing initconfig ( for running wizard on reboot )
sudo cp -f ~/scripts/scripts/bootscript/initconfig.service /etc/systemd/system/initconfig.service
sudo install -T ~/scripts/scripts/bootscript/initconfig.sh /usr/local/bin/initconfig.sh -m 0755
sudo systemctl daemon-reload

# enable initconfig for the next reboot
sudo systemctl enable initconfig

# increase partition size to maximum disk size
sudo tee -a /etc/init.d/update_partition <<EOF
#!/bin/bash

### BEGIN INIT INFO
# Provides:             update_partition
# Required-Start:       $local_fs $remote_fs $network $syslog $named
# Required-Stop:        $local_fs $remote_fs $network $syslog $named
# Default-Start:        2 3 4 5
# Default-Stop:         
# Short-Description:    updates partition 
# Description:          size to maximum disk size
### END INIT INFO
growpart /dev/sda 1
resize2fs /dev/sda1
EOF
sudo chmod +x /etc/init.d/update_partition
sudo update-rc.d update_partition defaults
