#!/usr/bin/bash

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install RPi.GPIO python3-pip python3-pil fonts-dejavu -y
sudo pip3 install adafruit-circuitpython-ssd1306
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
sudo python3 -m pip install --force-reinstall adafruit-blinka

if ! grep -q dtparam=i2c_arm=on /boot/config.txt
then
	echo "Enabling i2c in /boot/config.txt"
	sudo echo dtparam=i2c_arm=on >> /boot/config.txt
fi

if ! grep -q i2c-dev /etc/modules
then
	echo "Enabling i2c in /etc/modules"
	sudo echo i2c-dev >> /etc/modules
fi

if [ ! -d "/usr/local/display" ]
then
	echo "Creating /usr/local/display/ and installing files"
	sudo mkdir /usr/local/display
	sudo cp display.sh /usr/local/display
	sudo cp ssd1306_stats.py /usr/local/display

	echo "Installing display service to auto-start at bootup"
	sudo cp display.service /etc/systemd/system/display.service
	sudo systemctl daemon-reload
	sudo systemctl start display
	#systemctl status display
	sudo systemctl enable display
else
	echo "ALERT: /usr/local/display exists so no automated installation was done.  Please check this file for commands to run manually or delete that folder and try again."
fi

