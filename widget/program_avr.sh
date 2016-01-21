#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

pin=49
serial=/dev/ttyO4
tts=.9
image=/usr/local/share/avr/keypad.ino.standard.hex

(echo 0 > /sys/class/gpio/gpio$pin/value \
    && sleep $tts \
    && echo 1 > \
    /sys/class/gpio/gpio$pin/value) &

avrdude -c arduino -p m328p -b 57600 \
    -P $serial -U flash:v:$image

if [ $? -ne 0 ]; then
    (echo 0 > /sys/class/gpio/gpio$pin/value \
        && sleep $tts \
        && echo 1 > \
        /sys/class/gpio/gpio$pin/value) &

    avrdude -c arduino -p m328p -b 57600 \
        -P $serial -U flash:w:$image
fi


