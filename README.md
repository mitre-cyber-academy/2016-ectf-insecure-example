# Embedded CTF Example Code

This repository contains an example reference system for the 
[Embedded System CTF](http://mitrecyberacademy.org/competitions/embedded/).
This example meets (almost*) all the requirements outlined in the challenge writeup
document, but is not implemented securely.  


_* This repo does not currently meet the "Image and Setup" requirement because we haven't provided
a system image.  We’ll release a ready-to-go image soon that does meet this requirement._

## DoorApp code

The code for the server is contained in the "door_app" directory. 

* server.py:
    The main DoorApp code that runs the server for accepting data, reading registered-widgets.txt
    file, verifying submitted PINs, adding requests to the requested-widgets.txt file, and sending
    responses back to the BeagleBone.  It is written for Python 2.7.

* registered-widgets.txt:
    A configuration file that contains information for each of the registered widgets.


## Widget code

The code for the BeagleBone portion is contained in the "widget" directory. 

* INSTALL.md:
    Contains instructions for installing the widget code onto a new BeagleBone.

* widget_client.py:
    The main code that runs the client application. It is written for Python 2.7.

* keypad/keypad.ino:
    The code that runs on the AVR on the CryptoCape. It must be
    compiled to a hex file using the Arduino tools. See INSTALL.md for
    instructions.

* program_avr.sh:
    A script to program the AVR on the CryptoCape. Uses avrdude,
    which must be installed separately. See INSTALL.md for instructions.

* widget-client.service:
    A systemd service file for the widget client. Using systemd allows
    us to start the client at boot, and to restart it if anything goes wrong.

## Running example code

### Starting the server

The DoorApp server.py code should work on almost any system with Python2.7 and 
[Twisted](https://pypi.python.org/pypi/Twisted).  Initially, we recommend running the server.py 
code natively on your host computer.  Later on, we will provide a docker image that can also 
be used to run the server.  Information on how to install and use Docker can be found at https://docs.docker.com.  


### Starting the client

Either follow the installation procedure defined in widget/INSTALL.md, or use
the pre-made SD card image provided.

The BeagleBoard website has instructions for installing a new SD card image
from a Windows machine: http://beagleboard.org/getting-started#update

If you're doing this from a Mac or Linux machine, follow these instructions:

1. Insert a 4GB SD card into the machine.

2. Find where it is mounted using the "dmesg" command. You should see log
   messages indicating where the SD card was mounted. On Linux this will be
   something like `/dev/sdb` or `/dev/sdc`. On the Mac it will be something like
   `/dev/disk1` or `/dev/disk2`.

3. Verify that this is REALLY the device you want to completely OVERWRITE.
   `parted /dev/sdXXX print`

4. Unmount the card if it was mounted:
    Linux: `umount <device>`
    Mac: `diskutil unmount <device>`

5. Copy the image file to the device. _WARNING: This step will IRREVERSIBLY OVERWRITE the target
   device.  Please verify that this is the SD card not a system drive._  If you're using a mac, 
   you should use the raw disk device, which is prefixed with an "r". So if your SD card device is
   `/dev/disk2`, use `/dev/rdisk2` instead. Now execute the following command:

    `dd bs=1m if=<image file> of=<device>`
    
6. From here you can follow the [instructions on the BeagleBone web site](http://beagleboard.org/getting-started) (step 8).

### Testing the Full System

To test that the full system works you need to provide a "proxy" to redirect traffic from the
Widget to the Server.  [Socat](http://linux.die.net/man/1/socat) is a good tool to do this and can
be installed with [Cygwin](https://cygwin.com).  You may also want to install [netcat](http://nc110.sourceforge.net) 
for viewing the debug console on the Widget.

1. Plug the BeagleBone into a host computer using the USB cable.  
   Verify that a new virtual ethernet adapter was created on your host computer with IP address 
   192.168.7.1 and that you are able to ping 192.168.7.2 (the BeagleBone IP).
   
2. Connect netcat to the debug console of the Widget application running on the BeagleBone.
 
    `nc 192.168.7.2 6000`

3. Run the DoorApp code.

4. Run socat to redirect traffic from the Widget to the DoorApp.  
 
    `socat -v tcp-listen:5000 tcp-connect:localhost:9500`

5. Send a registration request from the Widget by entering `*#*#*#*#` on the keypad.

6. If the registration request is received by the server it should respond with a success message 
   and write the registration request to the **requested-widgets.txt** file.
  
7. Manually move the line from **requested-widgets.txt** to **registered-widgets.txt** and optionally update
   the 'flag' and 'pin' fields.  The server.py must be restarted for the changes to take effect.
  
8. After restarting the server to complete the Widget registration, you should be able to unlock
   the door and change your PIN (either by using the current PIN or by using the master PIN).

9. Verify that the unlock result and flags are observed on the traffic from the Widget port 6000.
