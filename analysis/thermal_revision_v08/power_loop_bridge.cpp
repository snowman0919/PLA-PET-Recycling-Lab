#include <cmath>
#include <new>
#include "heater_control.h"
#include "heater_power_allocator.h"

struct HostLoop {
  HeaterController controller;
  HeaterPowerAllocator allocator;
  unsigned priority = 0;
  unsigned fault_zone = 4;
};
extern "C" {
void *ppr_loop_create() { return new (std::nothrow) HostLoop(); }
void ppr_loop_destroy(void *p) { delete static_cast<HostLoop *>(p); }
unsigned ppr_loop_fault_zone(void *p) { return p ? static_cast<HostLoop *>(p)->fault_zone : 4; }
unsigned ppr_loop_sample_ms() { return HEATER_SAMPLE_PERIOD_MS; }
unsigned ppr_loop_window_ms() { return HEATER_WINDOW_MS; }
float ppr_loop_cap(bool extrusion) {
  const auto state = extrusion ? MachineState::EXTRUSION : MachineState::PREHEATING;
  return STATE_HEATER_PEAK_CAP_W[static_cast<unsigned>(state)];
}
void ppr_loop_targets(float *target) {
  if (!target) return;
  for (unsigned i = 0; i < 3; ++i) target[i] = PET_PROFILE.zone_c[i];
  target[3] = PET_PROFILE.die_c;
}
unsigned ppr_loop_step(void *p, const float *temperature, const float *target,
                       unsigned now_ms, float cap, bool permit, bool chain,
                       float *duty, unsigned char *on) {
  if (!p || !temperature || !target || !duty || !on) return 65535;
  auto &host = *static_cast<HostLoop *>(p);
  float requested[4]{};
  for (unsigned zone = 0; zone < 4; ++zone) {
    const TemperatureReading reading{temperature[zone], true, false, now_ms};
    const auto previous = host.controller.faults();
    const auto out = host.controller.update(zone, reading, target[zone],
                                            permit, chain, permit, now_ms);
    if (!previous && out.fault_bits) host.fault_zone = zone;
    requested[zone] = out.requested_duty_percent;
    duty[zone] = 0; on[zone] = 0;
  }
  if (!std::isfinite(cap) || cap < 0 || cap > ppr_loop_cap(false)) return 65535;
  if (host.controller.faults()) cap = 0;
  const auto allocation = host.allocator.allocate(requested, cap);
  constexpr float watts[4] = {100.0f, 100.0f, 100.0f, 60.0f};
  float commanded = 0;
  for (unsigned step = 0; step < 4; ++step) {
    const unsigned zone = (host.priority + step) % 4;
    const auto out = host.controller.applyAllocation(zone, allocation.allocated_duty[zone], now_ms);
    duty[zone] = out.allocated_duty_percent;
    if (out.time_proportion_on && commanded + watts[zone] <= cap) {
      on[zone] = 1;
      commanded += watts[zone];
    }
  }
  host.priority = (host.priority + 1) % 4;
  return host.controller.faults();
}
}
