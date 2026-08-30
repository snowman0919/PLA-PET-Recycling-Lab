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

  // High-current, low-RPM startup is expected during the canonical grace time.
  in.current_amp = 12.0f;
  in.cutter_rpm = 0.0f;
  in.now_ms = JAM_STARTUP_GRACE_MS - 1;
  out = c.update(in);
  assert(out.command == ShredderCommand::FORWARD && out.retry_count == 0);
  in.now_ms = JAM_STARTUP_GRACE_MS;
  out = c.update(in);
  assert(out.command == ShredderCommand::OVERLOAD_DWELL);
  in.now_ms += PLA_PROFILE.overload_ms;
  out = c.update(in);
  assert(out.command == ShredderCommand::RETRY_STOP && out.retry_count == 0);
  in.now_ms += JAM_STOP_MS;
  out = c.update(in);
  assert(out.command == ShredderCommand::REVERSE && out.retry_count == 1);
  in.now_ms += PLA_PROFILE.reverse_ms;
  out = c.update(in);
  assert(out.command == ShredderCommand::FORWARD);

  // Two more production-threshold jams latch after the third bounded reverse.
  for (int retry = 2; retry <= 3; ++retry) {
    in.now_ms += JAM_STARTUP_GRACE_MS;
    out = c.update(in);
    assert(out.command == ShredderCommand::OVERLOAD_DWELL);
    in.now_ms += PLA_PROFILE.overload_ms;
    out = c.update(in);
    assert(out.command == ShredderCommand::RETRY_STOP);
    in.now_ms += JAM_STOP_MS;
    out = c.update(in);
    assert(out.command == ShredderCommand::REVERSE && out.retry_count == retry);
    in.now_ms += PLA_PROFILE.reverse_ms;
    out = c.update(in);
  }
  assert(out.command == ShredderCommand::FAULT_LATCHED);
  assert(!c.clearFault(false, in));
  assert(c.clearFault(true, in));

  // Power mutual exclusion and permission loss are fail-safe.
  in.heater_or_screw_enabled = true;
  assert(!c.start(PET_PROFILE, in));
  in.heater_or_screw_enabled = false;
  in.permission_chain_ok = true;
  in.current_amp = 2.0f;
  in.cutter_rpm = 0.0f;
  assert(c.start(PET_PROFILE, in));
  in.now_ms += JAM_STARTUP_GRACE_MS + PET_PROFILE.overload_ms + 1;
  out = c.update(in);
  assert(out.command == ShredderCommand::FORWARD);  // Brownout-like RPM deficit without torque overload.
  in.permission_chain_ok = false;
  assert(c.update(in).command == ShredderCommand::FAULT_LATCHED);

  std::cout << "SHREDDER_CALIBRATED_TORQUE_RPM_RETRY_OK\n";
}
