#!/bin/bash

# Create log directory
sudo mkdir -p /var/log/classcord
sudo chown classcord:classcord /var/log/classcord
sudo chmod 755 /var/log/classcord

# Install fail2ban
sudo apt-get update
sudo apt-get install -y fail2ban

# Copy fail2ban configuration
sudo cp config/fail2ban/jail.local /etc/fail2ban/jail.d/classcord.local
sudo cp config/fail2ban/filter.d/classcord.conf /etc/fail2ban/filter.d/

# Copy logrotate configuration
sudo cp config/logrotate/classcord /etc/logrotate.d/
sudo chmod 644 /etc/logrotate.d/classcord
sudo chown root:root /etc/logrotate.d/classcord

# Copy systemd service
sudo cp config/systemd/classcord.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/classcord.service
sudo chown root:root /etc/systemd/system/classcord.service

# Reload configurations and start services
sudo systemctl daemon-reload
sudo systemctl enable classcord.service
sudo systemctl start classcord.service
sudo systemctl restart fail2ban