#include <new>
#include "heater_control.h"

extern "C" {
void *ppr_heater_create() { return new (std::nothrow) HeaterController(); }
void ppr_heater_destroy(void *handle) {
  delete static_cast<HeaterController *>(handle);
}
unsigned ppr_heater_step(void *handle, const float *temperature,
                         const float *target, unsigned now_ms,
                         float *duty, bool permit, bool chain) {
  auto *controller = static_cast<HeaterController *>(handle);
  if (!controller) return 65535;
  for (unsigned i = 0; i < 4; ++i) {
    const TemperatureReading reading{temperature[i], true, false, now_ms};
    const auto request = controller->update(i, reading, target[i], permit,
                                             chain, permit, now_ms);
    const auto applied = controller->applyAllocation(i, request.duty_percent, now_ms);
    duty[i] = applied.allocated_duty_percent;
  }
  const unsigned faults = controller->faults();
  if (faults) for (unsigned i = 0; i < 4; ++i) duty[i] = 0;
  return faults;
}
}
