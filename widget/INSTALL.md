# Compling AVR image

1. Download the Arduino tools:

    http://www.arduino.cc/en/Main/Software

2. Install the Keypad library:

    http://www.arduino.cc/playground/Code/Keypad

3. Open the keypad.ini file. Verify the code, then select
   "Sketch -> Export compiled Binary". This should create the file
   keypad.ino.standard.hex.

# Installation instructions

1. Boot BeagleBone from latest Debian image found on the BeagleBone website:

    http://beagleboard.org/latest-images

2. Install avrdude version 5.11.1 on the BeagleBone:

    http://download.savannah.gnu.org/releases/avrdude/avrdude-5.11.1.tar.gz

3. Copy the following files to the following directories:

    widget_client.py -> /usr/local/bin/
    
    widget-client.service -> /etc/systemd/system/
    
    program_avr.sh -> /usr/local/bin/
    
    keypad.ino.standard.hex -> /usr/local/share/avr/

4. Enable the widget service on the BeagleBone by executing:

    sudo systemctl daemon-reload
    
    sudo systemctl enable embedded-ctf-client.service

5. Reboot the BeagleBone, or execute

    sudo systemctl start embedded-ctf-client.service

