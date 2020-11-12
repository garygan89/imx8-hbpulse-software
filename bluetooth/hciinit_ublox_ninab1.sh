#!/bin/bash
# Initializing uBlox Nina B1 bluetooth as hci0 interface. 
# Flash the firmware using Apache Newt, see 
# https://developer.solid-run.com/knowledge-base/building-newt-nimble-blehci-firmware-for-the-imx8mq-nina-b1-module

# attach to hci0
sudo btattach -B /dev/ttymxc3 -S 1000000 -N &

sleep 3

# Start sending BLE advertising
sudo hciconfig hci0 leadv 0

# Start pairing agent
python3 simple-agent


