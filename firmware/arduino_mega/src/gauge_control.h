#pragma once

#include <stdint.h>

#include "hardware_interfaces.h"

struct GaugeCalibration {
  float x_offset_adc;
  float x_mm_per_count;
  float y_offset_adc;
  float y_mm_per_count;
  float u95_mm;
  bool valid;
};

class GaugeController {
 public:
  bool setCalibration(const GaugeCalibration &calibration);
  GaugeReading update(uint16_t x_adc, uint16_t y_adc, bool optical_valid);
  const GaugeReading &reading() const { return reading_; }

 private:
  GaugeCalibration calibration_{0, 0, 0, 0, 1, false};
  GaugeReading reading_{0, 0, 0, 0, 1, false, false};
};

class DiameterController {
 public:
  float update(const GaugeReading &gauge, float target_mm, float feedforward_mm_s,
               float kp, float ki, float dt_s);
  void reset();
  bool safePause() const { return safe_pause_; }

 private:
  float integral_{0};
  bool safe_pause_{true};
};
