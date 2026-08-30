#include "heater_control.h"

namespace {
float clampf(float value, float low, float high) {
  return value < low ? low : (value > high ? high : value);
}
}

bool processHeaterPhaseAllowed(MachineState state) {
  return state == MachineState::PREHEATING || state == MachineState::EXTRUSION ||
         state == MachineState::MAINTENANCE_PURGE || state == MachineState::FORMING_CHAIN_RUNDOWN ||
         state == MachineState::THERMAL_HOLD || state == MachineState::REQUALIFYING;
}

HeaterOutput HeaterController::update(uint8_t zone, const TemperatureReading &reading,
                                      float target_c, bool phase_permission,
                                      bool thermal_chain_ok, bool permission_feedback,
                                      uint32_t now_ms) {
  if (zone >= 4) return {0, false, HEATER_SENSOR_RANGE};
  Zone &z = zones_[zone];
  const float dt = z.last_ms == 0 ? HEATER_SAMPLE_PERIOD_MS / 1000.0f : clampf((now_ms - z.last_ms) / 1000.0f, 0.001f, 2.0f);
  z.last_ms = now_ms;

  if (reading.sensor_open) latched_faults_ |= HEATER_SENSOR_OPEN;
  if (!reading.valid || reading.celsius < HEATER_MIN_VALID_C || reading.celsius > HEATER_MAX_VALID_C) latched_faults_ |= HEATER_SENSOR_RANGE;
  if (!thermal_chain_ok) latched_faults_ |= HEATER_THERMAL_CHAIN;
  if (reading.valid && reading.celsius >= HEATER_OVERTEMPERATURE_C) latched_faults_ |= HEATER_OVERTEMPERATURE;
  if (phase_permission && !permission_feedback) latched_faults_ |= HEATER_PERMISSION_MISMATCH;

  const bool allowed = phase_permission && thermal_chain_ok && permission_feedback && latched_faults_ == HEATER_FAULT_NONE;
  const float error = target_c - reading.celsius;
  float duty = 0;
  if (allowed) {
    z.integral = clampf(z.integral + error * dt, -500.0f, 500.0f);
    duty = clampf(2.0f * error + 0.08f * z.integral, 0.0f, 100.0f);
  } else {
    z.integral = 0;
  }

  if (allowed && duty >= 40.0f) {
    if (!z.heating_watch) {
      z.heating_watch = true;
      z.watch_start_ms = now_ms;
      z.watch_temperature = reading.celsius;
    } else if (now_ms - z.watch_start_ms >= HEATER_NOT_HEATING_DWELL_MS) {
      if (reading.celsius - z.watch_temperature < HEATER_NOT_HEATING_MIN_RISE_C) latched_faults_ |= HEATER_NOT_HEATING;
      z.heating_watch = false;
    }
  } else {
    z.heating_watch = false;
  }

  if (!phase_permission && reading.valid) {
    if (!z.off_watch) {
      z.off_watch = true;
      z.watch_start_ms = now_ms;
      z.watch_temperature = reading.celsius;
    } else if (now_ms - z.watch_start_ms >= HEATER_UNEXPECTED_RISE_DWELL_MS) {
      if (reading.celsius - z.watch_temperature >= HEATER_UNEXPECTED_RISE_C) latched_faults_ |= HEATER_UNEXPECTED_RISE;
      z.off_watch = false;
    }
  } else {
    z.off_watch = false;
  }

  if (latched_faults_ != HEATER_FAULT_NONE) duty = 0;
  const uint32_t on_ms = static_cast<uint32_t>(HEATER_WINDOW_MS * duty / 100.0f);
  return {duty, duty > 0 && now_ms % HEATER_WINDOW_MS < on_ms, latched_faults_};
}

bool HeaterController::canClearFault(bool lockout, bool thermal_chain_ok,
                                     bool temperature_sensors_healthy) const {
  return lockout && thermal_chain_ok && temperature_sensors_healthy;
}

bool HeaterController::clearFault(bool lockout, bool thermal_chain_ok) {
  if (!canClearFault(lockout, thermal_chain_ok)) return false;
  commitFaultClear();
  return true;
}

void HeaterController::commitFaultClear() {
  latched_faults_ = HEATER_FAULT_NONE;
  for (auto &zone : zones_) zone = Zone{};
}
