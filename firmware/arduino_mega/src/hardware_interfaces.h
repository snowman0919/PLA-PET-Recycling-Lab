#pragma once

#include <stdint.h>

enum class TemperatureChannel : uint8_t { T1, T2, T3, TDIE, THOPPER, COUNT };

struct TemperatureReading {
  float celsius;
  bool valid;
  bool sensor_open;
  uint32_t sampled_ms;
};

struct GaugeReading {
  float x_mm;
  float y_mm;
  float mean_mm;
  float ovality_mm;
  float u95_mm;
  bool valid;
  bool calibrated;
};

struct ActuatorCommands {
  int16_t shredder_pwm;
  bool feeder_enable;
  int16_t screw_pwm;
  int16_t puller_pwm;
  int16_t spooler_pwm;
  uint8_t cooling_pwm;
  bool traverse_step;
  bool traverse_direction;
  bool traverse_enable;
  bool heater_on[4];
  bool hopper_ptc_on;
};

struct CoolingFeedback {
  float current_amp;
  bool valid;
};

class CoolingFeedbackBackend {
 public:
  virtual ~CoolingFeedbackBackend() = default;
  virtual CoolingFeedback read(uint32_t now_ms) = 0;
};

class TemperatureBackend {
 public:
  virtual ~TemperatureBackend() = default;
  virtual TemperatureReading read(TemperatureChannel channel, uint32_t now_ms) = 0;
};

class ActuatorBackend {
 public:
  virtual ~ActuatorBackend() = default;
  virtual void apply(const ActuatorCommands &commands) = 0;
};
