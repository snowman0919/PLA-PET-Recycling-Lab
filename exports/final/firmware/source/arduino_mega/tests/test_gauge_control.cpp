#include <cassert>
#include <cmath>
#include <iostream>

#include "gauge_control.h"

int main() {
  GaugeController gauge;
  assert(!gauge.setCalibration({100, 0.002f, 100, 0.002f, 0.06f, true}));
  assert(gauge.setCalibration({100, 0.002f, 100, 0.002f, 0.02f, true}));
  auto reading = gauge.update(975, 965, true);
  assert(reading.valid && reading.calibrated);
  assert(std::fabs(reading.mean_mm - 1.74f) < 0.001f);
  assert(std::fabs(reading.ovality_mm - 0.02f) < 0.001f);
  DiameterController controller;
  const float command = controller.update(reading, 1.75f, 9.28f, 0.40f, 0.025f, 0.1f);
  assert(command > 1 && !controller.safePause());
  const float integrated = controller.integratorState();
  assert(std::fabs(integrated) > 0.0001f);
  for (unsigned sample = 0; sample < 20; ++sample)
    controller.update(reading, 1.75f, 9.28f, 0.40f, 0.025f, 0.1f, false);
  assert(std::fabs(controller.integratorState() - integrated) < 0.000001f);
  controller.update(reading, 1.75f, 9.28f, 0.40f, 0.025f, 0.1f, true);
  assert(std::fabs(controller.integratorState() - integrated) > 0.0001f);
  reading.valid = false;
  assert(controller.update(reading, 1.75f, 9.28f, 0.40f, 0.025f, 0.1f) == 0);
  assert(controller.safePause());
  std::cout << "GAUGE_CALIBRATION_DIAMETER_PI_SAFE_PAUSE_OK\n";
}
