#include "gauge_control.h"

#include <math.h>

namespace {
float clampf(float value, float low, float high) {
  return value < low ? low : (value > high ? high : value);
}
}

bool GaugeController::setCalibration(const GaugeCalibration &c) {
  if (!c.valid || c.x_mm_per_count <= 0 || c.y_mm_per_count <= 0 || c.u95_mm <= 0 || c.u95_mm > 0.05f) return false;
  calibration_ = c;
  return true;
}

GaugeReading GaugeController::update(uint16_t x_adc, uint16_t y_adc, bool optical_valid) {
  const bool raw_valid = x_adc > 2 && x_adc < 1021 && y_adc > 2 && y_adc < 1021;
  const bool valid = calibration_.valid && optical_valid && raw_valid;
  const float x = valid ? (x_adc - calibration_.x_offset_adc) * calibration_.x_mm_per_count : 0;
  const float y = valid ? (y_adc - calibration_.y_offset_adc) * calibration_.y_mm_per_count : 0;
  reading_ = {x, y, (x + y) * 0.5f, fabsf(x - y), calibration_.u95_mm, valid, calibration_.valid};
  return reading_;
}

float DiameterController::update(const GaugeReading &gauge, float target_mm,
                                 float feedforward_mm_s, float kp, float ki,
                                 float dt_s, bool allow_integral) {
  if (!gauge.valid || !gauge.calibrated || gauge.u95_mm > 0.03f) {
    reset();
    return 0;
  }
  safe_pause_ = false;
  const float error = gauge.mean_mm - target_mm;
  if (allow_integral)
    integral_ = clampf(integral_ + error * dt_s, -20.0f, 20.0f);
  const float raw = feedforward_mm_s + kp * error + ki * integral_;
  saturated_ = raw <= 1.0f || raw >= 80.0f;
  return clampf(raw, 1.0f, 80.0f);
}

void DiameterController::reset() {
  integral_ = 0;
  safe_pause_ = true;
  saturated_ = false;
}
