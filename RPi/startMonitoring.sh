#!/bin/bash
cd /home/pi/urban_monitoring

daemonWasActive=$(systemctl is-active urban-monitoring)
params='./tracking.py --fps 2'

if [ "$daemonWasActive" = "active" ] && [ "$1" != "daemon" ]; then
    echo "Stoping urban monitoring deemon..."
    sudo ./daemon/daemonCmd.sh stop
fi

if [ "$1" = "debug" ]; then
    params='./tracking.py --fps 2 --debug'
    echo "Starting debug mode..."
elif [ "$1" = "gate" ]; then
    params='./draw.py'
    echo "Starting gate mode..."
elif [ "$1" = "gui" ]; then
    params='./tracking.py --fps 2 -u'
    echo "Starting gui mode..."
else
    echo "Starting monitoring..."
fi

echo "Press Ctrl+C to stop"
python3 $params

if [ "$daemonWasActive" = "active" ] && [ "$1" != "daemon" ]; then
    echo "Restarting urban monitoring deemon..."
    sudo ./daemon/daemonCmd.sh start
fi

echo "Done"