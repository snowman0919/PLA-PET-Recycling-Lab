#include <cassert>
#include <iostream>

#include "heater_control.h"

int main() {
  HeaterController controller;
  TemperatureReading good{25.0f, true, false, 0};
  auto out = controller.update(0, good, 180.0f, true, true, true, 250);
  assert(out.duty_percent == 100.0f && out.fault_bits == 0);
  assert(processHeaterPhaseAllowed(MachineState::PREHEATING));
  assert(processHeaterPhaseAllowed(MachineState::EXTRUSION));
  assert(!processHeaterPhaseAllowed(MachineState::SHREDDING));
  out = controller.update(0, good, 180.0f, true, true, false, 500);
  assert((out.fault_bits & HEATER_PERMISSION_MISMATCH) != 0);
  assert(out.duty_percent == 0);
  assert(!controller.clearFault(false, true));
  assert(controller.clearFault(true, true));

  TemperatureReading open{-273.0f, false, true, 750};
  out = controller.update(1, open, 195.0f, true, true, true, 750);
  assert((out.fault_bits & HEATER_SENSOR_OPEN) != 0);
  assert((out.fault_bits & HEATER_SENSOR_RANGE) != 0);
  assert(out.duty_percent == 0);
  std::cout << "HEATER_PID_TIME_PROPORTION_PROTECTIONS_OK\n";
}
