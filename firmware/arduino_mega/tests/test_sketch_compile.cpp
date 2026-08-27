#include "Arduino.h"

#include <stdio.h>

HardwareSerial Serial;

uint32_t millis() { return 0; }
int digitalRead(uint8_t) { return HIGH; }
int analogRead(uint8_t) { return 0; }
void digitalWrite(uint8_t, uint8_t) {}
void analogWrite(uint8_t, int) {}
void pinMode(uint8_t, uint8_t) {}

#include "../filament_recycler_mega.ino"

int main() {
  puts("MEGA_SKETCH_COMPILE_OK");
  return 0;
}
