#include <cassert>
#include <iostream>

#include "shredder_control.h"

int main() {
  ShredderController c;
  DriveCalibration calibration = REFERENCE_DRIVE_CALIBRATION;
  calibration.verified = true;  // Host test fixture; production requires Gate-1 record.
  assert(c.configureDrive(calibration));
  ShredderInputs in{0, 2.0f, 32.0f, true, false};
  assert(c.start(PLA_PROFILE, in));
  auto out = c.update(in);
  assert(out.command == ShredderCommand::FORWARD && out.target_rpm == 32);

  in.current_amp = 12.0f;
  in.now_ms = 100;
  c.update(in);
  in.now_ms = 751;
  out = c.update(in);
  assert(out.command == ShredderCommand::REVERSE && out.retry_count == 1);
  in.current_amp = 2.0f;
  in.cutter_rpm = 32.0f;
  in.now_ms = 1552;
  out = c.update(in);
  assert(out.command == ShredderCommand::FORWARD);

  // Two more sustained jams latch after the third bounded reverse.
  for (int retry = 2; retry <= 3; ++retry) {
    in.current_amp = 12.0f;
    in.now_ms += 10;
    c.update(in);
    in.now_ms += 651;
    out = c.update(in);
    assert(out.command == ShredderCommand::REVERSE);
    in.current_amp = 2.0f;
    in.now_ms += 801;
    out = c.update(in);
  }
  assert(out.command == ShredderCommand::FAULT_LATCHED);
  assert(!c.clearFault(false, in));
  assert(c.clearFault(true, in));

  // Power mutual exclusion and permission loss are fail-safe.
  in.heater_or_screw_enabled = true;
  assert(!c.start(PET_PROFILE, in));
  in.heater_or_screw_enabled = false;
  assert(c.start(PET_PROFILE, in));
  in.permission_chain_ok = false;
  assert(c.update(in).command == ShredderCommand::FAULT_LATCHED);

  std::cout << "SHREDDER_CALIBRATED_TORQUE_RPM_RETRY_OK\n";
}
