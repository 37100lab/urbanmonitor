#!/bin/bash
sudo cp urban-monitoring.service /lib/systemd/system/urban-monitoring.service

chmod +x ../startMonitoring.sh
chmod +x daemonCmd.sh

sudo systemctl enable urban-monitoring
sudo systemctl start urban-monitoring
