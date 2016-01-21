#include <Keypad.h>
#include <Wire.h>

const byte ROWS = 4;
const byte COLS = 3;
char keys[ROWS][COLS] = {
  {'1', '2', '3'},
  {'4', '5', '6'},
  {'7', '8', '9'},
  {'*', '0', '#'}
};

/*
 * This is wher the pin connections between the AVR and the pin pad are defined
 * This is the configuration for connecting the pin pad directly to the header
 * on the CryptoCape, with the pin pad extending downwards.
 */
byte rowPins[ROWS] = {8, 3, 4, 6};
byte  colPins[COLS] = {7, 9, 5};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
const int I2C_ADDR = 0x42;

/* ring buffer for data to be transmitted */
char key_buf[20] = {0};
unsigned int read_idx, write_idx;

const int LED = 13;

void setup() {
  read_idx = 0;
  write_idx = 0;
  Wire.begin(I2C_ADDR);
  Wire.onRequest(on_request);
  Wire.onReceive(on_receive);
  pinMode(LED, OUTPUT);
}

void loop() {
  char key = keypad.getKey();
  if (key != NO_KEY) {
    key_buf[write_idx] = key;
    write_idx += 1;

    if (write_idx >= sizeof(key_buf)) {
      write_idx = 0;
    }
  }
}

void on_request() {
  if (read_idx == write_idx) {
    return;
  }
  
  Wire.write((uint8_t *)(key_buf + read_idx), 1);
  read_idx += 1;

  if (read_idx >= sizeof(key_buf)) {
    read_idx = 0;
  }
}

void on_receive(int bytes) {
  while (Wire.available() > 0) {
    char c = Wire.read();

    if (c == 0x00) {
      // reset the character buffer
      read_idx = write_idx;
    } else if (c == 0x02) {
      digitalWrite(LED, HIGH);
    } else if (c == 0x03) {
      digitalWrite(LED, LOW);
    }
  }
}
