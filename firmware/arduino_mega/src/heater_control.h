#pragma once

#include <stdint.h>

#include "hardware_interfaces.h"
#include "material_profile.h"

enum HeaterFault : uint16_t {
  HEATER_FAULT_NONE = 0,
  HEATER_SENSOR_OPEN = 1 << 0,
  HEATER_SENSOR_RANGE = 1 << 1,
  HEATER_THERMAL_CHAIN = 1 << 2,
  HEATER_OVERTEMPERATURE = 1 << 3,
  HEATER_NOT_HEATING = 1 << 4,
  HEATER_UNEXPECTED_RISE = 1 << 5,
  HEATER_PERMISSION_MISMATCH = 1 << 6,
};

struct HeaterOutput {
  float duty_percent;
  bool time_proportion_on;
  uint16_t fault_bits;
};

class HeaterController {
 public:
  HeaterOutput update(uint8_t zone, const TemperatureReading &reading, float target_c,
                      bool phase_permission, bool thermal_chain_ok,
                      bool permission_feedback, uint32_t now_ms);
  bool canClearFault(bool physical_lockout_confirmed, bool thermal_chain_ok,
                     bool temperature_sensors_healthy = true) const;
  bool clearFault(bool physical_lockout_confirmed, bool thermal_chain_ok);
  uint16_t faults() const { return latched_faults_; }

 private:
  friend class MachineSupervisor;
  void commitFaultClear();
  struct Zone {
    float integral{0};
    float watch_temperature{0};
    uint32_t last_ms{0};
    uint32_t watch_start_ms{0};
    bool heating_watch{false};
    bool off_watch{false};
  } zones_[4];
  uint16_t latched_faults_{HEATER_FAULT_NONE};
};

bool processHeaterPhaseAllowed(MachineState state);
