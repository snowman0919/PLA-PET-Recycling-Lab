#include <assert.h>
#include <math.h>
#include <stdint.h>

#include <fstream>
#include <iostream>
#include <set>
#include <string>

#include "calibration_record.h"
#include "cooling_monitor.h"
#include "machine_supervisor.h"
#include "puller_speed_control.h"
#include "screw_motion_monitor.h"
#include "shredder_control.h"
#include "spooler_control.h"
#include "tach_contract_generated.h"
#include "tach_estimator.h"
#include "traverse_control.h"
#include "traverse_homing.h"

struct MachineSupervisorTestAccess {
  static void homeTraverse(MachineSupervisor &supervisor) {
    TraverseHomingOutput out = supervisor.traverse_homing_.update(true, false, true, 0);
    assert(out.state == TraverseHomingState::TRAVERSE_BACKOFF);
    for (uint32_t now = 2; now < 2000 && !out.homed; now += 2)
      out = supervisor.traverse_homing_.update(false, false, true, now);
    assert(out.homed);
    supervisor.traverse_control_.setHomedPosition(out.estimated_position_mm);
    supervisor.traverse_homing_output_ = out;
  }

  static void enterExtrusion(MachineSupervisor &supervisor, const InputSnapshot &input) {
    assert(supervisor.process_.selectMaterial(MaterialProfile::PLA));
    assert(supervisor.process_.requestState(MachineState::PREHEATING, input.safety));
    assert(supervisor.process_.requestState(MachineState::REQUALIFYING, input.safety));
    assert(supervisor.process_.requestState(MachineState::EXTRUSION, input.safety));
    supervisor.forming_state_ = FormingChainState::NORMAL;
    supervisor.spool_eligible_ = true;
    supervisor.waste_mode_ = false;
  }

  static void enterPurge(MachineSupervisor &supervisor, const InputSnapshot &input) {
    assert(supervisor.process_.selectMaterial(MaterialProfile::PLA));
    assert(supervisor.process_.requestMaterialChange(MaterialProfile::PET, input.safety));
    assert(supervisor.process_.requestPurgePreheat(input.safety));
    assert(supervisor.process_.markPurgeReady(input.safety));
    assert(supervisor.process_.startPurge(true, input.safety));
    supervisor.purge_feed_approved_ = true;
    supervisor.purge_started_ms_ = 1000;
    supervisor.purge_start_screw_revolutions_ = 0.0f;
    supervisor.purge_screw_revolutions_measured_ = true;
    supervisor.purge_temperature_stable_ = true;
  }

  static void enterPhase(MachineSupervisor &supervisor, MachineState phase,
                         const InputSnapshot &input) {
    assert(supervisor.process_.selectMaterial(MaterialProfile::PLA));
    if (phase == MachineState::SHREDDING) {
      assert(supervisor.process_.requestState(phase, input.safety));
      return;
    }
    if (phase == MachineState::MAINTENANCE_PURGE) {
      assert(supervisor.process_.requestMaterialChange(MaterialProfile::PET, input.safety));
      assert(supervisor.process_.requestPurgePreheat(input.safety));
      return;
    }
    assert(supervisor.process_.requestState(MachineState::PREHEATING, input.safety));
    if (phase == MachineState::PREHEATING) return;
    if (phase == MachineState::COOLDOWN) {
      assert(supervisor.process_.requestState(phase, input.safety));
      return;
    }
    assert(supervisor.process_.requestState(MachineState::REQUALIFYING, input.safety));
    if (phase == MachineState::REQUALIFYING) return;
    assert(supervisor.process_.requestState(MachineState::EXTRUSION, input.safety));
    if (phase == MachineState::EXTRUSION) return;
    assert(supervisor.process_.requestState(MachineState::FORMING_CHAIN_RUNDOWN, input.safety));
    if (phase == MachineState::FORMING_CHAIN_RUNDOWN) return;
    assert(phase == MachineState::THERMAL_HOLD);
    assert(supervisor.process_.requestState(MachineState::THERMAL_HOLD, input.safety));
  }
};

namespace {
uint64_t timestamp_edge_count = 0;

class Trace {
 public:
  explicit Trace(const char *path) {
    if (path != nullptr) stream_.open(path);
    if (stream_.is_open())
      stream_ << "scenario,status,path,time_ms,command_pwm,estimated_rpm,detail\n";
  }

  void pass(const char *scenario, const char *path, uint32_t time_ms = 0,
            int command_pwm = 0, float estimated_rpm = 0.0f,
            const char *detail = "assertions_passed") {
    scenarios_.insert(scenario);
    if (stream_.is_open())
      stream_ << scenario << ",PASS," << path << ',' << time_ms << ',' << command_pwm
              << ',' << estimated_rpm << ',' << detail << '\n';
  }

  size_t count() const { return scenarios_.size(); }

 private:
  std::ofstream stream_;
  std::set<std::string> scenarios_;
};

class PulseAdapter {
 public:
  explicit PulseAdapter(const TachEstimatorConfig &config) : config_(config) {
    assert(estimator_.configure(config));
  }

  TachEstimate sample(uint64_t absolute_now_us, float physical_rpm, bool connected = true) {
    if (!initialized_) {
      initialized_ = true;
      last_abs_us_ = absolute_now_us;
      if (connected && physical_rpm > 0.0f)
        next_pulse_abs_us_ = absolute_now_us + intervalUs(physical_rpm);
    }
    if (connected && physical_rpm > 0.0f) {
      const uint64_t interval = intervalUs(physical_rpm);
      if (next_pulse_abs_us_ < last_abs_us_ ||
          next_pulse_abs_us_ > last_abs_us_ + interval * 2ULL)
        next_pulse_abs_us_ = last_abs_us_ + interval;
      while (next_pulse_abs_us_ <= absolute_now_us) {
        estimator_.onPulse(static_cast<uint32_t>(next_pulse_abs_us_));
        ++timestamp_edge_count;
        next_pulse_abs_us_ += interval;
      }
    } else {
      next_pulse_abs_us_ = absolute_now_us + 1;
    }
    last_abs_us_ = absolute_now_us;
    return estimator_.estimate(static_cast<uint32_t>(absolute_now_us));
  }

 private:
  uint64_t intervalUs(float rpm) const {
    const double interval = 60000000.0 /
        (static_cast<double>(rpm) * static_cast<double>(config_.pulses_per_revolution));
    return static_cast<uint64_t>(interval + 0.5);
  }

  TachEstimatorConfig config_{};
  TachEstimator estimator_{};
  bool initialized_{false};
  uint64_t last_abs_us_{0};
  uint64_t next_pulse_abs_us_{0};
};

class PwmPlant {
 public:
  PwmPlant(const TachEstimatorConfig &tach, uint8_t dead_zone, uint8_t maximum_pwm,
           float minimum_rpm, float maximum_rpm)
      : tach_(tach), dead_zone_(dead_zone), maximum_pwm_(maximum_pwm),
        minimum_rpm_(minimum_rpm), maximum_rpm_(maximum_rpm) {}

  TachEstimate advance(uint64_t now_us, int16_t pwm, float load = 1.0f,
                       bool connected = true) {
    const float magnitude = static_cast<float>(pwm < 0 ? -pwm : pwm);
    float target = 0.0f;
    if (magnitude >= dead_zone_) {
      target = minimum_rpm_ + (magnitude - dead_zone_) /
          static_cast<float>(maximum_pwm_ - dead_zone_) * (maximum_rpm_ - minimum_rpm_);
      target *= load;
    }
    rpm_ += 0.18f * (target - rpm_);
    if (rpm_ < 0.02f) rpm_ = 0.0f;
    return tach_.sample(now_us, rpm_, connected);
  }

  float rpm() const { return rpm_; }

 private:
  PulseAdapter tach_;
  uint8_t dead_zone_;
  uint8_t maximum_pwm_;
  float minimum_rpm_;
  float maximum_rpm_;
  float rpm_{0.0f};
};

CalibrationRecord completeCalibrationRecord() {
  CalibrationRecord record{};
  for (uint8_t id = 0; id < CAL_COUNT; ++id)
    initializeCalibrationValueRecord(record.records[id], static_cast<CalibrationId>(id));
  record.drive = REFERENCE_DRIVE_CALIBRATION;
  record.drive.verified = true;
  record.gauge = {100, 0.002f, 100, 0.002f, 0.02f, true};
  record.current_zero_adc = 512.0f;
  record.current_amps_per_count = 0.01f;
  record.cooling_zero_adc = 500.0f;
  record.cooling_amps_per_count = 0.01f;
  record.puller = {30.0f, 20.0f, 30.0f, 3.0f, 1.2f, 45, 255,
                   800, 4000, 1000, 0.8f, 1.0f, 0.0f};
  record.spooler = {26.0f, 100.0f, 68.0f, 1.75f, 0.0f, 20.0f, 5.0f,
                    42, 220, 800, 1200, 0.88f, 0.5f, 8.0f,
                    4.0f, 1.0f, 7500, 1200, 1.0f};
  record.traverse = {68.0f, 1.85f, 80.0f, 1200};
  record.traverse_steps_per_mm = 80.0f;
  record.shredder_tach_pulses_per_revolution = 6.0f;
  record.screw_tach_pulses_per_revolution = 12.0f;
  record.spooler_tach_pulses_per_revolution = 20.0f;
  record.fan1_tach_pulses_per_revolution = 2.0f;
  record.fan2_tach_pulses_per_revolution = 2.0f;
  record.dancer_radians_per_count = 0.001f;
  const float values[CAL_COUNT] = {6.0f, 40.0f, 12.0f, 20.0f, 30.0f, 20.0f, 8.0f,
      80.0f, 0.002f, 0.01f, 2.0f, 2.0f, 0.001f, 0.01f};
  for (uint8_t id = 0; id < CAL_COUNT; ++id) {
    assert(setCalibrationValueRecord(record.records[id], static_cast<CalibrationId>(id),
        values[id], calibrationUnitsForId(static_cast<CalibrationId>(id)), 621,
        CalibrationSource::COMMISSIONING_MEASUREMENT, true, values[id] * 0.5f,
        values[id] * 1.5f));
  }
  finalizeCalibrationRecord(record);
  assert(calibrationRecordValid(record));
  return record;
}

InputSnapshot nominalInput() {
  InputSnapshot in{};
  in.safety = {true, true, true, true, true, true, true, true, true};
  for (auto &temperature : in.temperatures) temperature = {200.0f, true, false, 0};
  in.gauge_x_adc = 975;
  in.gauge_y_adc = 975;
  in.gauge_optical_valid = true;
  in.cooling_feedback_valid = true;
  in.fan1_rpm = 1800.0f;
  in.fan2_rpm = 1800.0f;
  in.fan1_tach_valid = true;
  in.fan2_tach_valid = true;
  in.shredder_current_amp = 2.0f;
  in.shredder_rpm = 32.0f;
  in.shredder_tach_valid = true;
  in.screw_rpm = 16.0f;
  in.screw_tach_valid = true;
  in.screw_speed_is_measured = true;
  in.puller_rpm = 6.0f;
  in.puller_tach_ok = true;
  in.spooler_rpm = 3.0f;
  in.spooler_tach_ok = true;
  in.traverse_permission_ok = true;
  in.traverse_position_valid = true;
  return in;
}

bool allHazardsOff(const ActuatorCommands &a) {
  bool heater = false;
  for (bool on : a.heater_on) heater = heater || on;
  return a.shredder_pwm == 0 && !a.feeder_enable && a.screw_pwm == 0 &&
      a.puller_pwm == 0 && a.spooler_pwm == 0 && a.cooling_pwm == 0 &&
      !a.traverse_enable && !a.hopper_ptc_on && !heater;
}

void calibrationAndTraverseScenarios(Trace &trace) {
  InputSnapshot input = nominalInput();
  input.fan1_rpm = input.fan2_rpm = 0.0f;
  MachineSupervisor cold;
  const SupervisorOutput cold_out = cold.update(input, 100);
  assert(!cold.formingCalibrationReady() && allHazardsOff(cold_out.actuators));
  trace.pass("cold_boot_no_cal", "MachineSupervisor::update");

  CalibrationRecord partial = completeCalibrationRecord();
  partial.records[CAL_SCREW_TACH].verified = 0;
  partial.records[CAL_SCREW_TACH].crc = calibrationValueRecordCrc(partial.records[CAL_SCREW_TACH]);
  finalizeCalibrationRecord(partial);
  MachineSupervisor partial_supervisor;
  assert(partial_supervisor.configureCalibrationRecord(partial));
  assert(!partial_supervisor.calibrationReadiness().screw_tach_valid);
  assert(!partial_supervisor.formingCalibrationReady());
  trace.pass("partial_calibration", "CalibrationRecord-v4->MachineSupervisor");

  MachineSupervisor complete;
  const CalibrationRecord record = completeCalibrationRecord();
  assert(complete.configureCalibrationRecord(record));
  assert(complete.formingCalibrationReady());
  trace.pass("complete_calibration", "CalibrationRecord-v4->MachineSupervisor");

  assert(complete.selectMaterial(MaterialProfile::PLA));
  assert(complete.requestTraverseHoming(input));
  input.traverse_left_limit = true;
  SupervisorOutput out = complete.update(input, 200);
  assert(out.view.traverse_homing.state == TraverseHomingState::TRAVERSE_BACKOFF);
  input.traverse_left_limit = false;
  for (uint32_t t = 202; t < 1000 && !complete.traverseHomed(); t += 2)
    out = complete.update(input, t);
  assert(complete.traverseHomed());
  trace.pass("traverse_homing", "MachineSupervisor->TraverseHomingController", 1000,
             0, 0.0f, "left_switch_then_2mm_backoff");

  complete.reportTraversePositionLoss();
  assert(!complete.traverseHomed() && !complete.spoolEligible());
  TraverseController endpoint;
  assert(endpoint.configure({2.0f, 0.5f, 2.0f, 10}));
  endpoint.setHomedPosition(0.0f);
  endpoint.update(2.0f, false, false, true, 2);
  endpoint.update(2.0f, false, false, true, 4);
  TraverseOutput endpoint_out = endpoint.update(4.0f, false, false, true, 6);
  assert(!endpoint_out.hard_fault);
  endpoint_out = endpoint.update(4.0f, false, false, true, 17);
  assert(endpoint_out.hard_fault);
  trace.pass("traverse_endpoint_loss",
             "TraverseController missed endpoint->MachineSupervisor position loss", 17);
}

void shredderScenarios(Trace &trace) {
  ShredderController controller;
  DriveCalibration calibration = REFERENCE_DRIVE_CALIBRATION;
  calibration.verified = true;
  assert(controller.configureDrive(calibration));
  PwmPlant plant(SHREDDER_TACH_CONFIG, 35, 255, 5.0f, 40.0f);
  ShredderInputs input{0, 1.5f, 0.0f, true, false, false};
  assert(controller.start(PLA_PROFILE, input));
  trace.pass("shredder_start", "ShredderController::start");
  int16_t pwm = 0;
  ShredderOutput out{};
  for (uint32_t ms = 0; ms <= 8000; ms += 20) {
    const TachEstimate estimate = plant.advance(static_cast<uint64_t>(ms) * 1000ULL, pwm);
    const int adc = 512 + static_cast<int>(1.5f / 0.01f + 0.5f);
    input = {ms, (adc - 512) * 0.01f, estimate.rpm, true, false, estimate.valid};
    out = controller.update(input);
    pwm = out.pwm;
  }
  assert(out.command == ShredderCommand::FORWARD && out.tach_valid && pwm > 0);
  trace.pass("shredder_nominal", "ADC-quantized->ShredderController->PWMPlant->TachEstimator",
             8000, pwm, out.target_rpm, "adc_current_count=662");

  bool saw_jam_dwell = false;
  bool saw_reverse = false;
  for (uint32_t ms = 8020; ms <= 12000; ms += 20) {
    const TachEstimate estimate = plant.advance(static_cast<uint64_t>(ms) * 1000ULL, pwm, 0.05f);
    const int adc = 512 + static_cast<int>(8.0f / 0.02f + 0.5f);
    input = {ms, (adc - 512) * 0.02f, estimate.rpm, true, false, estimate.valid};
    out = controller.update(input);
    pwm = out.pwm;
    saw_jam_dwell = saw_jam_dwell || out.command == ShredderCommand::OVERLOAD_DWELL;
    saw_reverse = saw_reverse || out.command == ShredderCommand::REVERSE;
    if (saw_reverse && pwm < 0) break;
  }
  assert(saw_jam_dwell && saw_reverse && pwm < 0);
  trace.pass("shredder_jam", "ShredderController overload dwell", input.now_ms, pwm,
             input.cutter_rpm, "quantized_current_trip");
  trace.pass("shredder_reverse", "ShredderController retry reverse", input.now_ms, pwm,
             input.cutter_rpm);
}

void screwScenarios(Trace &trace) {
  ScrewMotionMonitor controller;
  PwmPlant plant(SCREW_TACH_CONFIG, 38, 255, 1.0f, 25.0f);
  ScrewMotionOutput out{};
  int16_t pwm = 0;
  for (uint32_t ms = 0; ms <= 12000; ms += 20) {
    const bool load = ms >= 7000;
    const TachEstimate estimate = plant.advance(static_cast<uint64_t>(ms) * 1000ULL, pwm,
                                                 load ? 0.82f : 1.0f);
    out = controller.update(18.0f, estimate.rpm, estimate.valid, ms);
    pwm = out.control_pwm;
    if (ms == 6000)
      trace.pass("screw_nominal", "ScrewMotionMonitor->PWMPlant->TachEstimator", ms, pwm,
                 estimate.rpm);
  }
  assert(out.tach_valid && !out.command_motion_mismatch);
  trace.pass("screw_load", "ScrewMotionMonitor closed-loop load step", 12000, pwm,
             plant.rpm());
  for (uint32_t ms = 12020; ms <= 22000 && !out.command_motion_mismatch; ms += 20) {
    const TachEstimate estimate = plant.advance(static_cast<uint64_t>(ms) * 1000ULL, pwm, 1.0f, false);
    out = controller.update(18.0f, estimate.rpm, estimate.valid, ms);
    pwm = out.control_pwm;
  }
  assert(out.command_motion_mismatch && out.tach_loss && pwm == 0);
  trace.pass("screw_tach_loss", "TachEstimator timeout->ScrewMotionMonitor", 22000, pwm,
             out.actual_rpm);
}

PullerCalibration pullerCalibration() {
  return {30.0f, 20.0f, 30.0f, 3.0f, 1.2f, 45, 255,
          800, 4000, 1000, 0.8f, 1.0f, 0.0f};
}

void pullerScenarios(Trace &trace) {
  PullerSpeedController controller;
  assert(controller.configure(pullerCalibration()));
  PwmPlant plant(PULLER_TACH_CONFIG, 45, 255, 1.0f, 30.0f);
  PullerSpeedOutput out{};
  int16_t pwm = 0;
  for (uint32_t ms = 0; ms <= 18000; ms += 20) {
    const bool slip = ms >= 10000;
    const TachEstimate estimate = plant.advance(static_cast<uint64_t>(ms) * 1000ULL, pwm,
                                                 slip ? 0.75f : 1.0f);
    out = controller.update(9.28f, estimate.rpm, estimate.valid, true, ms);
    pwm = out.pwm;
    if (ms == 9000)
      trace.pass("puller_nominal", "PullerSpeedController->PWMPlant->TachEstimator", ms, pwm,
                 estimate.rpm);
  }
  assert(out.tach_valid && !out.saturated);
  trace.pass("puller_slip", "PullerSpeedController closed-loop slip load", 18000, pwm,
             plant.rpm());

  PwmPlant deadzone(PULLER_TACH_CONFIG, 45, 255, 1.0f, 30.0f);
  TachEstimate estimate{};
  for (uint32_t ms = 0; ms <= 5000; ms += 20)
    estimate = deadzone.advance(static_cast<uint64_t>(ms) * 1000ULL, 44);
  assert(deadzone.rpm() == 0.0f && !estimate.valid);
  trace.pass("puller_deadzone", "PWM dead-zone->TachEstimator timeout", 5000, 44, 0.0f);

  PullerSpeedController saturated;
  assert(saturated.configure(pullerCalibration()));
  for (uint32_t ms = 0; ms <= 2500; ms += 100)
    out = saturated.update(200.0f, 0.0f, true, true, ms);
  assert(out.pwm == 255 && out.pwm_limited && out.saturated);
  trace.pass("puller_saturation", "PullerSpeedController saturation dwell", 2500,
             out.pwm, out.measured_rpm);
}

SpoolerConfig spoolerConfig() {
  return {26.0f, 100.0f, 68.0f, 1.75f, 0.0f, 20.0f, 5.0f,
          42, 220, 800, 1200, 0.88f, 0.5f, 8.0f,
          4.0f, 1.0f, 7500, 1200, 1.0f};
}

void spoolerScenarios(Trace &trace) {
  SpoolerController controller;
  const SpoolerConfig config = spoolerConfig();
  assert(controller.configure(config));
  PwmPlant plant(SPOOLER_TACH_CONFIG, 42, 220, 0.5f, 8.0f);
  SpoolerOutput out{};
  int16_t pwm = 0;
  for (uint32_t ms = 0; ms <= 24000; ms += 20) {
    const TachEstimate estimate = plant.advance(static_cast<uint64_t>(ms) * 1000ULL, pwm);
    out = controller.update(9.0f, 0.0f, estimate.rpm, estimate.valid, true, ms);
    pwm = out.pwm;
  }
  assert(out.tach_valid && !out.jam && out.estimated_radius_mm >= 26.0f);
  trace.pass("spool_empty", "SpoolerController->PWMPlant->TachEstimator", 24000, pwm,
             plant.rpm());

  const float half_radius = 63.0f;
  const float half_length = (half_radius * half_radius - 26.0f * 26.0f) *
      (4.0f * config.packing_factor * config.spool_width_mm) /
      (config.filament_diameter_mm * config.filament_diameter_mm);
  assert(controller.applyMeasuredLengthCorrection(half_length));
  out = controller.update(9.0f, 0.0f, 1.36f, true, true, 24100);
  assert(fabsf(out.estimated_radius_mm - half_radius) < 0.1f);
  trace.pass("spool_half", "SpoolerController volume-conservation radius", 24100,
             out.pwm, out.measured_rpm);
  assert(controller.applyMeasuredLengthCorrection(1.0e9f));
  out = controller.update(9.0f, 0.0f, 0.86f, true, true, 24200);
  assert(fabsf(out.estimated_radius_mm - 100.0f) < 0.1f);
  trace.pass("spool_full", "SpoolerController clamped full radius", 24200,
             out.pwm, out.measured_rpm);

  SpoolerController jam;
  assert(jam.configure(config));
  bool saw_jam = false;
  for (uint32_t ms = 1; ms <= 10000; ms += 100) {
    out = jam.update(9.0f, 0.2f, 0.0f, false, true, ms);
    saw_jam = saw_jam || out.jam;
    if (saw_jam) break;
  }
  assert(saw_jam && out.pwm >= config.minimum_useful_pwm);
  trace.pass("spool_jam", "SpoolerController jam dwell", 1301, out.pwm, 0.0f);
}

TachEstimatorConfig fanConfig() {
  return {2, 300.0f, 3000.0f, 1500.0f, 200000UL, 3, 500000UL,
          5000UL, 100000UL, 5000.0f, 0.5f};
}

void seedAdapterInputs(InputSnapshot &input, uint64_t now_us, PulseAdapter &screw,
                       PulseAdapter &puller, PulseAdapter &spooler,
                       PulseAdapter &fan1, PulseAdapter &fan2,
                       bool fan1_connected = true, bool fan2_connected = true) {
  const TachEstimate s = screw.sample(now_us, 16.0f);
  const TachEstimate p = puller.sample(now_us, 6.0f);
  const TachEstimate w = spooler.sample(now_us, 3.0f);
  const TachEstimate f1 = fan1.sample(now_us, 1800.0f, fan1_connected);
  const TachEstimate f2 = fan2.sample(now_us, 1800.0f, fan2_connected);
  input.screw_rpm = s.rpm;
  input.screw_tach_valid = s.valid;
  input.screw_speed_is_measured = s.valid;
  input.puller_rpm = p.rpm;
  input.puller_tach_ok = p.valid;
  input.spooler_rpm = w.rpm;
  input.spooler_tach_ok = w.valid;
  input.fan1_rpm = f1.rpm;
  input.fan1_tach_valid = f1.valid;
  input.fan2_rpm = f2.rpm;
  input.fan2_tach_valid = f2.valid;
  input.cooling_feedback_valid = f1.valid || f2.valid;
}

void prepareProduction(MachineSupervisor &supervisor, InputSnapshot &input,
                       PulseAdapter &screw, PulseAdapter &puller, PulseAdapter &spooler,
                       PulseAdapter &fan1, PulseAdapter &fan2) {
  assert(supervisor.configureCalibrationRecord(completeCalibrationRecord()));
  MachineSupervisorTestAccess::homeTraverse(supervisor);
  for (uint64_t us = 0; us <= 5000000ULL; us += 20000ULL)
    seedAdapterInputs(input, us, screw, puller, spooler, fan1, fan2);
  MachineSupervisorTestAccess::enterExtrusion(supervisor, input);
  supervisor.update(input, 5000);
}

void purgeAndSystemScenarios(Trace &trace) {
  InputSnapshot input = nominalInput();
  PulseAdapter screw(SCREW_TACH_CONFIG), puller(PULLER_TACH_CONFIG), spooler(SPOOLER_TACH_CONFIG);
  PulseAdapter fan1(fanConfig()), fan2(fanConfig());
  for (uint64_t us = 0; us <= 5000000ULL; us += 20000ULL)
    seedAdapterInputs(input, us, screw, puller, spooler, fan1, fan2);

  MachineSupervisor purge;
  assert(purge.configureCalibrationRecord(completeCalibrationRecord()));
  MachineSupervisorTestAccess::homeTraverse(purge);
  PulseAdapter purge_screw(SCREW_TACH_CONFIG);
  TachEstimate purge_estimate{};
  for (uint32_t ms = 0; ms <= 1000; ms += 20)
    purge_estimate = purge_screw.sample(static_cast<uint64_t>(ms) * 1000ULL, 18.0f);
  assert(purge_estimate.valid);
  input.screw_rpm = purge_estimate.rpm;
  input.screw_tach_valid = true;
  input.screw_speed_is_measured = true;
  MachineSupervisorTestAccess::enterPurge(purge, input);
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  SupervisorOutput out{};
  for (uint32_t ms = 1020; ms <= 123000; ms += 500) {
    const TachEstimate estimate = purge_screw.sample(static_cast<uint64_t>(ms) * 1000ULL, 18.0f);
    input.screw_rpm = estimate.rpm;
    input.screw_tach_valid = estimate.valid;
    input.screw_speed_is_measured = estimate.valid;
    out = purge.update(input, ms);
  }
  assert(out.view.purge_screw_revolutions >= PURGE_MINIMUM_SCREW_REVOLUTIONS);
  assert(out.view.purge_screw_revolutions_measured);
  assert(purge.confirmPurgeComplete(true, input, 123000));
  trace.pass("purge_actual_pulse_revolutions",
             "TachEstimator timestamps->InputSnapshot->MachineSupervisor purge evidence",
             123000, out.actuators.screw_pwm, input.screw_rpm,
             "no_ideal_rpm_injection_after_adapter");

  auto runFanLoss = [&](const char *name, bool keep1, bool keep2) {
    InputSnapshot local = nominalInput();
    PulseAdapter ls(SCREW_TACH_CONFIG), lp(PULLER_TACH_CONFIG), lw(SPOOLER_TACH_CONFIG);
    PulseAdapter lf1(fanConfig()), lf2(fanConfig());
    MachineSupervisor supervisor;
    prepareProduction(supervisor, local, ls, lp, lw, lf1, lf2);
    for (uint64_t us = 5020000ULL; us <= 8000000ULL; us += 20000ULL) {
      seedAdapterInputs(local, us, ls, lp, lw, lf1, lf2, keep1, keep2);
      out = supervisor.update(local, static_cast<uint32_t>(us / 1000ULL));
    }
    assert(supervisor.formingState() == FormingChainState::RUNDOWN);
    assert((supervisor.formingFaultReasons() & FORMING_COOLING_FAILURE) != 0);
    trace.pass(name, "fan TachEstimator->CoolingMonitor->MachineSupervisor rundown", 8000,
               out.actuators.cooling_pwm, keep1 ? local.fan1_rpm : local.fan2_rpm);
  };
  runFanLoss("fan1_loss", false, true);
  runFanLoss("fan2_loss", true, false);
  runFanLoss("dual_fan_loss", false, false);

  InputSnapshot gauge_input = nominalInput();
  PulseAdapter gs(SCREW_TACH_CONFIG), gp(PULLER_TACH_CONFIG), gw(SPOOLER_TACH_CONFIG);
  PulseAdapter gf1(fanConfig()), gf2(fanConfig());
  MachineSupervisor gauge;
  prepareProduction(gauge, gauge_input, gs, gp, gw, gf1, gf2);
  gauge_input.gauge_optical_valid = false;
  out = gauge.update(gauge_input, 5100);
  assert(gauge.formingState() == FormingChainState::RUNDOWN);
  assert(out.actuators.spooler_pwm == 0 && !out.actuators.traverse_enable);
  trace.pass("gauge_loss", "GaugeController->MachineSupervisor bounded rundown", 5100);
  for (uint64_t us = 5120000ULL; us <= 16000000ULL; us += 20000ULL) {
    seedAdapterInputs(gauge_input, us, gs, gp, gw, gf1, gf2);
    out = gauge.update(gauge_input, static_cast<uint32_t>(us / 1000ULL));
  }
  assert(gauge.formingState() == FormingChainState::THERMAL_HOLD);
  assert(out.actuators.screw_pwm == 0);
  trace.pass("forming_rundown", "MachineSupervisor rundown->thermal hold", 16000);

  InputSnapshot rq_input = nominalInput();
  PulseAdapter rs(SCREW_TACH_CONFIG), rp(PULLER_TACH_CONFIG), rw(SPOOLER_TACH_CONFIG);
  PulseAdapter rf1(fanConfig()), rf2(fanConfig());
  MachineSupervisor requal;
  prepareProduction(requal, rq_input, rs, rp, rw, rf1, rf2);
  rq_input.gauge_x_adc = rq_input.gauge_y_adc = 1010;
  out = requal.update(rq_input, 5100);
  assert(requal.formingState() == FormingChainState::REQUALIFYING);
  rq_input.gauge_x_adc = rq_input.gauge_y_adc = 975;
  for (uint64_t us = 5200000ULL; us <= 38000000ULL; us += 200000ULL) {
    seedAdapterInputs(rq_input, us, rs, rp, rw, rf1, rf2);
    out = requal.update(rq_input, static_cast<uint32_t>(us / 1000ULL));
  }
  assert(requal.formingState() == FormingChainState::READY_TO_RETHREAD);
  trace.pass("gauge_requalification", "GaugeController->MachineSupervisor requalification", 38000,
             0, 0.0f, "20_samples_plus_stability_and_transport");
}

void estopAndAtomicClearScenarios(Trace &trace) {
  const struct PhaseCase { MachineState phase; const char *name; } phases[] = {
      {MachineState::SHREDDING, "estop_shredding"},
      {MachineState::PREHEATING, "estop_preheating"},
      {MachineState::REQUALIFYING, "estop_requalifying"},
      {MachineState::EXTRUSION, "estop_extrusion"},
      {MachineState::MAINTENANCE_PURGE, "estop_maintenance_purge"},
      {MachineState::FORMING_CHAIN_RUNDOWN, "estop_forming_rundown"},
      {MachineState::THERMAL_HOLD, "estop_thermal_hold"},
      {MachineState::COOLDOWN, "estop_cooldown"},
  };
  for (const auto &phase : phases) {
    MachineSupervisor supervisor;
    assert(supervisor.configureCalibrationRecord(completeCalibrationRecord()));
    InputSnapshot input = nominalInput();
    PulseAdapter shredder(SHREDDER_TACH_CONFIG), screw(SCREW_TACH_CONFIG);
    PulseAdapter puller(PULLER_TACH_CONFIG), spooler(SPOOLER_TACH_CONFIG);
    PulseAdapter fan1(fanConfig()), fan2(fanConfig());
    for (uint64_t us = 0; us <= 5000000ULL; us += 20000ULL) {
      const TachEstimate sh = shredder.sample(us, 32.0f);
      input.shredder_rpm = sh.rpm;
      input.shredder_tach_valid = sh.valid;
      seedAdapterInputs(input, us, screw, puller, spooler, fan1, fan2);
    }
    MachineSupervisorTestAccess::homeTraverse(supervisor);
    MachineSupervisorTestAccess::enterPhase(supervisor, phase.phase, input);
    assert(supervisor.process().state() == phase.phase);
    input.safety.estop_ok = false;
    const SupervisorOutput out = supervisor.update(input, 9000);
    assert(supervisor.process().state() == MachineState::ESTOP && allHazardsOff(out.actuators));
    trace.pass(phase.name, "MachineSupervisor E-stop one-cycle zero", 9000);
  }

  MachineSupervisor atomic;
  assert(atomic.configureCalibrationRecord(completeCalibrationRecord()));
  InputSnapshot input = nominalInput();
  PulseAdapter ashredder(SHREDDER_TACH_CONFIG), ascrew(SCREW_TACH_CONFIG);
  PulseAdapter apuller(PULLER_TACH_CONFIG), aspooler(SPOOLER_TACH_CONFIG);
  PulseAdapter afan1(fanConfig()), afan2(fanConfig());
  for (uint64_t us = 0; us <= 5000000ULL; us += 20000ULL) {
    const TachEstimate sh = ashredder.sample(us, 32.0f);
    input.shredder_rpm = sh.rpm;
    input.shredder_tach_valid = sh.valid;
    seedAdapterInputs(input, us, ascrew, apuller, aspooler, afan1, afan2);
  }
  MachineSupervisorTestAccess::enterPhase(atomic, MachineState::PREHEATING, input);
  input.safety.estop_ok = false;
  assert(atomic.update(input, 10000).view.process_phase == MachineState::ESTOP);
  input.safety.estop_ok = true;
  input.safety.restart_permission = true;
  assert(!atomic.clearAllFaults(input, false));
  assert(atomic.process().state() == MachineState::ESTOP);
  assert(atomic.clearAllFaults(input, true));
  assert(atomic.process().state() == MachineState::IDLE);
  trace.pass("atomic_fault_clear", "MachineSupervisor two-phase preflight/commit", 10000);
}

void rolloverScenario(Trace &trace) {
  PulseAdapter adapter(SCREW_TACH_CONFIG);
  TachEstimate estimate{};
  const uint64_t start = (1ULL << 32) - 400000ULL;
  for (uint64_t us = start; us <= start + 1600000ULL; us += 20000ULL)
    estimate = adapter.sample(us, 18.0f);
  assert(estimate.valid && fabsf(estimate.rpm - 18.0f) / 18.0f < 0.03f);
  trace.pass("uint32_rollover", "TachEstimator modular timestamp subtraction", 1600,
             0, estimate.rpm);
}
}  // namespace

int main(int argc, char **argv) {
  Trace trace(argc > 1 ? argv[1] : nullptr);
  calibrationAndTraverseScenarios(trace);
  shredderScenarios(trace);
  screwScenarios(trace);
  pullerScenarios(trace);
  spoolerScenarios(trace);
  purgeAndSystemScenarios(trace);
  estopAndAtomicClearScenarios(trace);
  rolloverScenario(trace);
  assert(trace.count() == 37);
  assert(timestamp_edge_count > 100);
  std::cout << "HARDWARE_ADAPTER_E2E_V0621_OK scenarios=" << trace.count() << '\n';
  return 0;
}
