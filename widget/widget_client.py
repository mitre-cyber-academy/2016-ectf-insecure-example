#!/usr/bin/env python
import json
import socket
import smbus
import subprocess
import time
import threading
from uuid import getnode as get_mac

# This is a (bad) example of the "something you have" portion of the authentication.
DEVICE_KEY = '12345'

class AVRChip(object):
    """
    Class for communicating with the AVR on the CryptoCape. The AVR is
    responsible for reading characters from the keypad and controlling the
    status LED. On initialization this runs the "program_avr.sh" script, which
    verifies that the AVR is running the correct image, and loads the image if
    it isn't.
    """
    AVR_ADDR = 0x42

    def __init__(self):
        # Program the AVR. It has a tendency to fail without the delays here.
        time.sleep(5)
        subprocess.call('/usr/local/bin/program_avr.sh')
        time.sleep(5)
        self.bus = smbus.SMBus(1) # /dev/i2c-1

    def reset_keys(self):
        self.bus.write_byte(AVRChip.AVR_ADDR, 0x00)

    def read_key(self):
        return chr(self.bus.read_byte(AVRChip.AVR_ADDR))

    def led_on(self):
        self.bus.write_byte(AVRChip.AVR_ADDR, 0x02)

    def led_off(self):
        self.bus.write_byte(AVRChip.AVR_ADDR, 0x03)

class ServerConnection(object):
    """
    This class manages the connection to the door server. It automatically
    attempts to reconnect to the server every 10 seconds if the connection
    fails.
    """
    SERVER_ADDR = '192.168.7.1'
    SERVER_PORT = 5000

    def __init__(self, logger):
        self.logger = logger
        self.conn = None
        self.device_id = str(get_mac())

    def connect(self):
        while self.conn is None:
            try:
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.connect((ServerConnection.SERVER_ADDR,
                                   ServerConnection.SERVER_PORT))
            except socket.error:
                self.conn = None
                self.logger.error('Failed to connect to server. Retrying in 10 seconds...')
                time.sleep(10)

    def send(self, data_dict):
        """
        Send some data to the server. The connection will be retried until the
        data is sent. Returns 1 for success, 0 for failure.
        """
        data_dict['device_key'] = DEVICE_KEY
        data_dict['device_id'] = self.device_id
        data = json.dumps(data_dict)

        while True:
            self.connect()

            try:
                self.conn.sendall(data)
                response = self.conn.recv(4096)
                d = json.loads(response)

                if 'flag' in d:
                    self.logger.info('Got flag "%s"' % d['flag'])

                return d['success']
            except socket.error:
                self.conn = None
            except (ValueError, TypeError, KeyError):
                # JSON decoding errors
                return 0

    def register_device(self):
        d = {'type' : 'register_device'}

        return self.send(d)

    def open_door(self, pin):
        d = {'type' : 'open_door',
             'pin' : pin}

        return self.send(d)

    def change_password(self, current_pin, new_pin):
        d = {'type' : 'tenant_change_password',
             'current_pin' : current_pin,
             'new_pin' : new_pin}

        return self.send(d)

    def change_password_master(self, master_pin, new_pin):
        d = {'type' : 'master_change_password',
             'master_pin' : master_pin,
             'new_pin' : new_pin}

        return self.send(d)

class Logger(object):
    """
    Logs information to connections on port 6000. Simple way of accessing logs
    using netcat:
                    nc 192.168.7.2 6000
    """
    LOGGER_PORT = 6000

    def __init__(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conns = []
        self.thread = threading.Thread(target = self.accept_thread)
        self.thread.start()

    def accept_thread(self):
        """
        Simple thread that waits for connections and appends them to the list
        as they come in.
        """
        self.listen_socket.bind(('', Logger.LOGGER_PORT))
        self.listen_socket.listen(1)
        
        while True:
            try:
                conn, _ = self.listen_socket.accept()
                self.conns.append(conn)
            except:
                break

    def close(self):
        # forces accept() in accept_thread to raise an exception
        self.listen_socket.shutdown(socket.SHUT_RDWR)
        self.listen_socket.close()
        self.thread.join()

    def message(self, msg):
        bad_conns = []

        for conn in self.conns:
            try:
                conn.sendall(msg + "\n")
            except socket.error:
                bad_conns.append(conn)

        for bad_conn in bad_conns:
            self.conns.remove(bad_conn)

    def info(self, msg):
        self.message("INFO: " + msg)

    def error(self, msg):
        self.message("Error: " + msg)

def avr_indicate_success(avr):
    """
    Indicate a successful operation by turning on the LED for 3 seconds.
    """
    avr.led_on()
    time.sleep(3)
    avr.led_off()

def avr_indicate_failure(avr):
    """
    Indicate a failure by blinking the LED quickly 3 times.
    """
    for _ in range(3):
        avr.led_on()
        time.sleep(0.3)
        avr.led_off()
        time.sleep(0.3)

def main():
    """
    Main program loop. Sets up the connections to the AVR and the server, then
    reads key presses and sends them to the server.
    """
    avr = AVRChip()
    avr.reset_keys() # clear the key buffer on the AVR
    avr.led_off()
    logger = Logger()

    try:
        server = ServerConnection(logger)

        buf = ""

        while (True):
            c = avr.read_key()
            
            # read_key() will always return a character. NULL means no new
            # key presses.
            if c == '\0':
                time.sleep(0.1)
                continue

            buf += c

            # maximum size to avoid running out of memory
            if len(buf) > 16:
                logger.error('Reached maximum buffer size')
                buf = ""

            if c == '#':
                # These are the cases where we should continue reading input.
                # Otherwise, the # character always terminates the input.
                if buf in ('*#', '*#*#', '*#*#*#'):
                    continue
                
                if buf == '*#*#*#*#':
                    if server.register_device():
                        logger.info('Registration successful')
                        avr_indicate_success(avr)
                    else:
                        logger.info('Registration unsuccessful')
                        avr_indicate_failure(avr)
                elif len(buf) == 7:
                    password = buf[:6]

                    if server.open_door(password):
                        logger.info('Door open successful')
                        avr_indicate_success(avr)
                    else:
                        logger.info('Door open unsuccessful')
                        avr_indicate_failure(avr)
                elif len(buf) == 14:
                    if buf[6] != '*':
                        logger.error('Invalid entry')
                        buf = ""
                        continue

                    current_password = buf[:6]
                    new_password = buf[7:-1]

                    if server.change_password(current_password, new_password):
                        logger.info('Password change successful')
                        avr_indicate_success(avr)
                    else:
                        logger.info('Password change unsuccessful')
                        avr_indicate_failure(avr)
                elif len(buf) == 16:
                    if buf[8] != '*':
                        logger.error('Invalid entry')
                        buf = ""
                        continue
                    
                    master_password = buf[:8]
                    new_password = buf[9:-1]

                    if server.change_password_master(master_password, new_password):
                        logger.info('Password change successful')
                        avr_indicate_success(avr)
                    else:
                        logger.info('Password change unsuccessful')
                        avr_indicate_failure(avr)
                else:
                    logger.error('Invalid entry')

                buf = ""
    except KeyboardInterrupt:
        pass
    finally:
        logger.close()

if __name__ == '__main__':
    main()
