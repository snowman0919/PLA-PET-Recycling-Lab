#pragma once

#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

constexpr uint8_t LOW = 0;
constexpr uint8_t HIGH = 1;
constexpr uint8_t INPUT = 0;
constexpr uint8_t OUTPUT = 1;
constexpr uint8_t INPUT_PULLUP = 2;

constexpr uint8_t A0 = 54;
constexpr uint8_t A1 = 55;
constexpr uint8_t A2 = 56;
constexpr uint8_t A3 = 57;
constexpr uint8_t A4 = 58;
constexpr uint8_t A5 = 59;
constexpr uint8_t A6 = 60;
constexpr uint8_t A7 = 61;
constexpr uint8_t A8 = 62;
constexpr uint8_t A9 = 63;
constexpr uint8_t A10 = 64;
constexpr uint8_t A11 = 65;
constexpr uint8_t A12 = 66;
constexpr uint8_t A13 = 67;
constexpr uint8_t A14 = 68;
constexpr uint8_t A15 = 69;

class HardwareSerial {
 public:
  void begin(unsigned long) {}
  int available() const { return 0; }
  int read() { return -1; }
  size_t write(const uint8_t*, size_t length) { return length; }
};

extern HardwareSerial Serial;

uint32_t millis();
int digitalRead(uint8_t pin);
int analogRead(uint8_t pin);
void digitalWrite(uint8_t pin, uint8_t value);
void analogWrite(uint8_t pin, int value);
void pinMode(uint8_t pin, uint8_t mode);
