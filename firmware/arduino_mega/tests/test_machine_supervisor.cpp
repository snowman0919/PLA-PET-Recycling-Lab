#include <cassert>
#include <iostream>

#include "machine_supervisor.h"

struct MachineSupervisorTestAccess {
  static SupervisorOutput injectCandidate(MachineSupervisor &supervisor,
                                          const ActuatorCommands &candidate,
                                          const InputSnapshot &input, uint32_t now_ms) {
    return supervisor.finalizeOutput(candidate, input, now_ms);
  }

  static void completeTraverseHoming(MachineSupervisor &supervisor) {
    auto out = supervisor.traverse_homing_.update(true, false, true, 0);
    assert(out.state == TraverseHomingState::TRAVERSE_BACKOFF);
    for (uint32_t now = 2; now < 1000 && !out.homed; now += 2)
      out = supervisor.traverse_homing_.update(false, false, true, now);
    assert(out.homed && out.state == TraverseHomingState::TRAVERSE_READY);
    supervisor.traverse_control_.setHomedPosition(out.estimated_position_mm);
    supervisor.traverse_homing_output_ = out;
  }

  static void forceSpoolEligibility(MachineSupervisor &supervisor) {
    supervisor.spool_eligible_ = true;
  }

  static float traverseStepsPerMm(const MachineSupervisor &supervisor) {
    return supervisor.traverse_control_.stepsPerMm();
  }
};

namespace {
InputSnapshot nominal() {
  InputSnapshot in;
  in.safety = {true, true, true, true, true, true, true, true, true};
  for (auto &temperature : in.temperatures) temperature = {200.0f, true, false, 0};
  in.gauge_x_adc = 975;
  in.gauge_y_adc = 975;
  in.gauge_optical_valid = true;
  in.cooling_feedback_valid = true;
  in.screw_speed_is_measured = true;
  in.shredder_current_amp = 2.0f;
  in.shredder_rpm = 32.0f;
  in.screw_rpm = 16.0f;
  in.spooler_rpm = 0.3f;
  return in;
}

void calibrateDomains(MachineSupervisor &s) {
  DriveCalibration drive = REFERENCE_DRIVE_CALIBRATION;
  drive.verified = true;
  assert(s.configureDriveCalibration(drive));
  assert(s.configureCurrentSensorCalibration(512.0f, 0.01f));
  assert(s.configureGaugeCalibration({100, 0.002f, 100, 0.002f, 0.02f, true}));
  assert(s.configureCoolingFeedbackCalibration(100.0f, 0.01f));
  assert(s.configurePullerCalibration({30.0f, 20.0f, 160.0f, 3.0f, 1.2f,
                                       45, 255, 800, 600, 800, 2.0f}));
  assert(s.configureSpoolerDriveCalibration(
      {26.0f, 100.0f, 68.0f, 1.75f, 0.0f, 180.0f, 45.0f, 42, 220, 1200, 1000}));
  assert(s.configureTachCalibration(CAL_SHREDDER_TACH, 7.0f));
  assert(s.configureTachCalibration(CAL_SCREW_TACH, 1.0f));
  assert(s.configureTachCalibration(CAL_SPOOLER_TACH, 20.0f));
  assert(s.configureTachCalibration(CAL_FAN1_TACH, 2.0f));
  assert(s.configureTachCalibration(CAL_FAN2_TACH, 2.0f));
  assert(s.configureTraverseCalibration(80.0f));
  assert(s.configureDancerCalibration(0.001f));
  assert(s.formingCalibrationReady());
}

void calibrate(MachineSupervisor &s) {
  calibrateDomains(s);
  MachineSupervisorTestAccess::completeTraverseHoming(s);
}

SupervisorOutput completeCoolingStartupProbe(MachineSupervisor &s, const InputSnapshot &healthy,
                                             uint32_t first_command_ms) {
  InputSnapshot fan_off = healthy;
  fan_off.cooling_feedback_valid = false;
  SupervisorOutput out = s.update(fan_off, first_command_ms);
  assert(out.invariants_ok);
  assert(s.process().state() == MachineState::IDLE);
  assert(out.view.cooling_startup_request != CoolingStartupRequest::NONE);
  assert(out.actuators.cooling_pwm >= COOLING_COMMAND_THRESHOLD_PWM);
  assert(out.actuators.shredder_pwm == 0 && out.actuators.screw_pwm == 0 &&
         out.actuators.puller_pwm == 0 && out.actuators.spooler_pwm == 0 &&
         !out.actuators.feeder_enable && !out.actuators.traverse_enable);
  for (bool heater_on : out.actuators.heater_on) assert(!heater_on);
  out = s.update(healthy, first_command_ms + 1);
  assert(s.process().state() == MachineState::IDLE);
  for (bool heater_on : out.actuators.heater_on) assert(!heater_on);
  out = s.update(healthy, first_command_ms + 1 + COOLING_STARTUP_HEALTHY_DWELL_MS);
  assert(out.view.cooling_startup_request == CoolingStartupRequest::NONE);
  return out;
}

uint32_t enterProductionExtrusion(MachineSupervisor &s, const InputSnapshot &input) {
  calibrate(s);
  assert(s.selectMaterial(MaterialProfile::PLA));
  assert(s.requestPreheat(input));
  completeCoolingStartupProbe(s, input, 100);
  assert(s.armExtrusion(input, 1800));
  SupervisorOutput out{};
  for (uint32_t now_ms = 2000; now_ms <= 30000; now_ms += 1000) out = s.update(input, now_ms);
  assert(s.formingState() == FormingChainState::READY_TO_RETHREAD);
  assert(s.confirmManualRethread(input));
  out = s.update(input, 30001);
  assert(s.spoolEligible());
  out = s.update(input, 30101);
  assert(out.actuators.spooler_pwm > 0);
  return 30101;
}
}

int main() {
  InputSnapshot in = nominal();

  // Regression: NONE-profile cold boot cannot produce hazardous commands.
  MachineSupervisor cold_boot;
  assert(!cold_boot.formingCalibrationReady() && !cold_boot.traverseHomed());
  auto cold = cold_boot.update(in, 250);
  assert(cold_boot.process().material() == MaterialProfile::NONE);
  assert(cold.actuators.shredder_pwm == 0 && cold.actuators.screw_pwm == 0 &&
         !cold.actuators.feeder_enable && cold.actuators.spooler_pwm == 0);
  InputSnapshot cold_fault_input = in;
  cold_fault_input.safety.service_guard_closed = false;
  cold = cold_boot.update(cold_fault_input, 500);
  assert(cold_boot.process().state() == MachineState::FAULT);
  assert(cold.actuators.cooling_pwm == 0);  // NONE must never use profileFor() fallback to command a fan.

  // Regression: the final production envelope faults and zeros an injected invariant violation.
  MachineSupervisor invariant_guard;
  ActuatorCommands conflicting{};
  conflicting.shredder_pwm = 100;
  conflicting.screw_pwm = 100;
  const SupervisorOutput rejected = MachineSupervisorTestAccess::injectCandidate(
      invariant_guard, conflicting, in, 600);
  assert(!rejected.invariants_ok && invariant_guard.process().state() == MachineState::FAULT);
  assert(rejected.view.process_phase == MachineState::FAULT);
  assert(rejected.actuators.shredder_pwm == 0 && rejected.actuators.screw_pwm == 0 &&
         rejected.actuators.cooling_pwm == 0);

  // Mutation guard: even complete independent calibration cannot permit winding before homing.
  MachineSupervisor unhomed_winding;
  calibrateDomains(unhomed_winding);
  assert(unhomed_winding.formingCalibrationReady() && !unhomed_winding.traverseHomed());
  MachineSupervisorTestAccess::forceSpoolEligibility(unhomed_winding);
  ActuatorCommands premature_winding{};
  premature_winding.spooler_pwm = 50;
  const auto no_home = MachineSupervisorTestAccess::injectCandidate(
      unhomed_winding, premature_winding, in, 700);
  assert(!no_home.invariants_ok && no_home.actuators.spooler_pwm == 0);

  MachineSupervisor independent_calibration;
  assert(independent_calibration.configurePullerCalibration(
      {30.0f, 20.0f, 160.0f, 3.0f, 1.2f, 45, 255, 800, 600, 800, 2.0f}));
  assert(independent_calibration.calibrationReadiness().puller_drive_valid);
  assert(independent_calibration.calibrationReadiness().puller_tach_valid);
  assert(!independent_calibration.calibrationReadiness().screw_tach_valid);
  assert(!independent_calibration.calibrationReadiness().spooler_tach_valid);
  assert(!independent_calibration.calibrationReadiness().traverse_valid);

  CalibrationRecord stored{};
  stored.traverse_steps_per_mm = 80.0f;  // stale compatibility mirror must not win.
  assert(setCalibrationValueRecord(stored.records[CAL_TRAVERSE], CAL_TRAVERSE, 40.0f,
      CalibrationUnits::STEPS_PER_MILLIMETRE, 12,
      CalibrationSource::COMMISSIONING_MEASUREMENT, true, 10.0f, 1000.0f));
  finalizeCalibrationRecord(stored);
  MachineSupervisor stored_calibration;
  assert(stored_calibration.configureCalibrationRecord(stored));
  assert(stored_calibration.calibrationReadiness().traverse_valid);
  assert(!stored_calibration.calibrationReadiness().puller_drive_valid);
  assert(MachineSupervisorTestAccess::traverseStepsPerMm(stored_calibration) == 40.0f);

  // Regression: boot must not select a material and calibration domains are independent.
  MachineSupervisor transaction;
  assert(transaction.process().material() == MaterialProfile::NONE);
  assert(!transaction.requestShredding(in, 0));
  DriveCalibration drive = REFERENCE_DRIVE_CALIBRATION;
  drive.verified = true;
  assert(transaction.configureDriveCalibration(drive));
  assert(!transaction.calibrationReadiness().current_sensor_calibration_valid);
  assert(transaction.configureCurrentSensorCalibration(512.0f, 0.01f));
  assert(transaction.configureTachCalibration(CAL_SHREDDER_TACH, 7.0f));
  assert(transaction.selectMaterial(MaterialProfile::PLA));
  InputSnapshot start_estop = in;
  start_estop.safety.estop_ok = false;
  assert(!transaction.requestShredding(start_estop, 0));
  assert(transaction.process().state() == MachineState::IDLE);
  in.safety.driver_fault_free = false;
  assert(!transaction.requestShredding(in, 0));
  assert(transaction.process().state() == MachineState::IDLE);
  in.safety.driver_fault_free = true;
  assert(transaction.requestShredding(in, 0));
  assert(transaction.process().state() == MachineState::SHREDDING);
  transaction.requestStop(in);

  // Regression: fan-off feedback cannot deadlock startup; a calibrated fan-only proof runs first.
  MachineSupervisor missing_cooling;
  DriveCalibration missing_cooling_drive = REFERENCE_DRIVE_CALIBRATION;
  missing_cooling_drive.verified = true;
  assert(missing_cooling.configureDriveCalibration(missing_cooling_drive));
  assert(missing_cooling.configureCurrentSensorCalibration(512.0f, 0.01f));
  assert(missing_cooling.configureGaugeCalibration({100, 0.002f, 100, 0.002f, 0.02f, true}));
  assert(missing_cooling.selectMaterial(MaterialProfile::PLA));
  assert(!missing_cooling.requestPreheat(in));
  assert(missing_cooling.configureCoolingFeedbackCalibration(100.0f, 0.01f));
  assert(missing_cooling.configureTachCalibration(CAL_FAN1_TACH, 2.0f));
  assert(missing_cooling.configureTachCalibration(CAL_FAN2_TACH, 2.0f));
  InputSnapshot unhealthy_fan = in;
  unhealthy_fan.cooling_feedback_valid = false;
  assert(missing_cooling.requestPreheat(unhealthy_fan));
  auto out = missing_cooling.update(unhealthy_fan, 0);
  assert(missing_cooling.process().state() == MachineState::IDLE && out.actuators.cooling_pwm > 0);
  for (bool heater_on : out.actuators.heater_on) assert(!heater_on);
  out = missing_cooling.update(unhealthy_fan, COOLING_STARTUP_PROBE_TIMEOUT_MS);
  assert(missing_cooling.process().state() == MachineState::FAULT);
  assert((missing_cooling.formingFaultReasons() & FORMING_COOLING_FAILURE) != 0);
  assert(out.actuators.cooling_pwm == 0);
  assert(missing_cooling.clearAllFaults(unhealthy_fan, true));
  assert(missing_cooling.process().state() == MachineState::IDLE);
  out = missing_cooling.update(unhealthy_fan, COOLING_STARTUP_PROBE_TIMEOUT_MS + 1);
  assert(out.actuators.cooling_pwm == 0);  // Clear never auto-restarts the failed transaction.
  assert(missing_cooling.requestPreheat(unhealthy_fan));
  out = missing_cooling.update(unhealthy_fan, COOLING_STARTUP_PROBE_TIMEOUT_MS + 2);
  assert(out.actuators.cooling_pwm > 0);  // A new explicit request must prove the fan again.
  missing_cooling.requestStop(unhealthy_fan);

  // Unrelated shredder drive/current readiness must not mask a legal extrusion UI flow.
  MachineSupervisor extrusion_only_readiness;
  assert(extrusion_only_readiness.configureGaugeCalibration({100, 0.002f, 100, 0.002f, 0.02f, true}));
  assert(extrusion_only_readiness.configureCoolingFeedbackCalibration(100.0f, 0.01f));
  assert(extrusion_only_readiness.configureTachCalibration(CAL_FAN1_TACH, 2.0f));
  assert(extrusion_only_readiness.configureTachCalibration(CAL_FAN2_TACH, 2.0f));
  assert(extrusion_only_readiness.selectMaterial(MaterialProfile::PLA));
  out = extrusion_only_readiness.update(in, 10);
  assert(!out.view.calibration.drive_calibration_valid &&
         !out.view.calibration.current_sensor_calibration_valid);
  assert(out.view.ui_state == SupervisorUiState::READY_TO_PREHEAT);
  assert(extrusion_only_readiness.requestPreheat(unhealthy_fan));
  out = extrusion_only_readiness.update(unhealthy_fan, 20);
  assert(out.view.ui_state == SupervisorUiState::COOLING_STARTUP_PROBE);
  extrusion_only_readiness.update(in, 21);
  out = extrusion_only_readiness.update(in, 21 + COOLING_STARTUP_HEALTHY_DWELL_MS);
  assert(out.view.ui_state == SupervisorUiState::READY_TO_EXTRUDE);

  // Regression: changed temperature/guard inputs abort the probe before phase/heater commit.
  MachineSupervisor changed_probe_inputs;
  calibrate(changed_probe_inputs);
  assert(changed_probe_inputs.selectMaterial(MaterialProfile::PLA));
  assert(changed_probe_inputs.requestPreheat(unhealthy_fan));
  changed_probe_inputs.update(unhealthy_fan, 0);
  InputSnapshot opened_sensor = in;
  opened_sensor.temperatures[0] = {-273.0f, false, true, 100};
  out = changed_probe_inputs.update(opened_sensor, 100);
  assert(changed_probe_inputs.process().state() == MachineState::FAULT && out.actuators.cooling_pwm == 0);
  for (bool heater_on : out.actuators.heater_on) assert(!heater_on);
  assert(!changed_probe_inputs.clearAllFaults(opened_sensor, true));
  assert(changed_probe_inputs.clearAllFaults(in, true));

  MachineSupervisor opened_guard_probe;
  calibrate(opened_guard_probe);
  assert(opened_guard_probe.selectMaterial(MaterialProfile::PLA));
  assert(opened_guard_probe.requestPreheat(unhealthy_fan));
  opened_guard_probe.update(unhealthy_fan, 0);
  InputSnapshot opened_guard = in;
  opened_guard.safety.service_guard_closed = false;
  out = opened_guard_probe.update(opened_guard, 100);
  assert(opened_guard_probe.process().state() == MachineState::FAULT && out.actuators.cooling_pwm == 0);
  for (bool heater_on : out.actuators.heater_on) assert(!heater_on);

  // Regression: thermal readiness alone never starts feeder/screw; explicit arm is mandatory.
  calibrate(transaction);
  assert(transaction.requestPreheat(in));
  out = completeCoolingStartupProbe(transaction, in, 1000);
  assert(transaction.process().state() == MachineState::PREHEATING);
  assert(out.view.ui_state == SupervisorUiState::READY_TO_EXTRUDE);
  assert(out.actuators.screw_pwm == 0 && out.actuators.feeder_enable == false);
  InputSnapshot bad_gauge = in;
  bad_gauge.safety.gauge_valid = false;
  assert(!transaction.armExtrusion(bad_gauge, 2600));
  assert(transaction.armExtrusion(in, 2700));
  assert(transaction.process().state() == MachineState::REQUALIFYING);
  assert(!transaction.spoolEligible() && transaction.wasteMode());

  // Regression: requalification gates winding and requires explicit manual rethread.
  InputSnapshot saturated_during_requalification = in;
  saturated_during_requalification.puller_saturated = true;
  out = transaction.update(saturated_during_requalification, 2800);
  assert(transaction.formingState() == FormingChainState::REQUALIFYING);
  assert(out.view.requalification_valid_samples == 0 && !transaction.spoolEligible());
  for (uint32_t t = 2900; t < 3800; t += 100) out = transaction.update(in, t);
  assert(out.view.requalification_valid_samples <= 5);  // 0.2 s contract cadence, not update frequency.
  InputSnapshot diameter_bad_during_requalification = in;
  diameter_bad_during_requalification.gauge_x_adc = 1010;
  diameter_bad_during_requalification.gauge_y_adc = 1010;
  out = transaction.update(diameter_bad_during_requalification, 3800);
  assert(out.view.requalification_valid_samples == 0 && !transaction.spoolEligible());
  for (uint32_t t = 4000; t <= 34000; t += 1000) out = transaction.update(in, t);
  assert(transaction.formingState() == FormingChainState::READY_TO_RETHREAD);
  assert(out.view.ui_state == SupervisorUiState::READY_TO_RETHREAD);
  assert(out.actuators.spooler_pwm == 0 && !out.actuators.traverse_enable);
  InputSnapshot rethread_blocked = in;
  rethread_blocked.safety.service_guard_closed = false;
  assert(!transaction.confirmManualRethread(rethread_blocked));
  InputSnapshot rethread_bad_diameter = in;
  rethread_bad_diameter.gauge_x_adc = 1010;
  rethread_bad_diameter.gauge_y_adc = 1010;
  assert(!transaction.confirmManualRethread(rethread_bad_diameter));
  assert(!transaction.spoolEligible() && transaction.formingState() == FormingChainState::READY_TO_RETHREAD);
  assert(transaction.confirmManualRethread(in));
  out = transaction.update(in, 34100);
  assert(transaction.spoolEligible() && !transaction.wasteMode());

  // Regression: gauge loss enters the shared bounded rundown and disables winding immediately.
  bad_gauge.gauge_optical_valid = false;
  out = transaction.update(bad_gauge, 34200);
  assert(transaction.formingState() == FormingChainState::RUNDOWN);
  assert((transaction.formingFaultReasons() & FORMING_GAUGE_INVALID) != 0);
  assert(out.actuators.spooler_pwm == 0 && !out.actuators.traverse_enable);
  assert(out.actuators.screw_pwm > 0);
  out = transaction.update(bad_gauge, 44300);
  assert(transaction.formingState() == FormingChainState::THERMAL_HOLD);
  assert(out.actuators.screw_pwm == 0);

  // Production quality excursions stop winding in the same cycle and require full requalification.
  for (uint8_t quality_case = 0; quality_case < 3; ++quality_case) {
    MachineSupervisor quality;
    const uint32_t production_ms = enterProductionExtrusion(quality, in);
    InputSnapshot excursion = in;
    if (quality_case == 0) {
      excursion.gauge_x_adc = 1010;
      excursion.gauge_y_adc = 1010;
    } else if (quality_case == 1) {
      excursion.gauge_x_adc = 1010;
      excursion.gauge_y_adc = 940;
    } else {
      excursion.puller_saturated = true;
    }
    out = quality.update(excursion, production_ms + 100);
    assert(quality.process().state() == MachineState::REQUALIFYING);
    assert(quality.formingState() == FormingChainState::REQUALIFYING);
    assert(!quality.spoolEligible() && quality.wasteMode());
    assert(out.actuators.spooler_pwm == 0 && !out.actuators.traverse_enable);
    assert(quality.formingFaultReasons() == FORMING_FAULT_NONE);
  }

  // Regression: E-stop zeros every hazardous command in one supervisor cycle and cannot restart.
  InputSnapshot estop = in;
  estop.safety.estop_ok = false;
  out = transaction.update(estop, 44400);
  assert(transaction.process().state() == MachineState::ESTOP);
  assert(out.actuators.shredder_pwm == 0 && out.actuators.screw_pwm == 0 &&
         out.actuators.puller_pwm == 0 && out.actuators.spooler_pwm == 0 && !out.actuators.feeder_enable &&
         out.actuators.cooling_pwm == 0 && !out.actuators.traverse_enable && !out.actuators.hopper_ptc_on);

  // Regression: a refused atomic clear leaves every latch and process state unchanged.
  const uint16_t reasons_before = transaction.formingFaultReasons();
  in.safety.restart_permission = true;
  assert(!transaction.clearAllFaults(in, false));
  assert(transaction.process().state() == MachineState::ESTOP);
  assert(transaction.formingFaultReasons() == reasons_before);
  assert(transaction.clearAllFaults(in, true));
  assert(transaction.process().state() == MachineState::IDLE);
  assert(!transaction.spoolEligible());

  // Regression: purge is a timed/revolution-bounded phase and pending material cannot activate early.
  MachineSupervisor purge;
  calibrate(purge);
  assert(purge.selectMaterial(MaterialProfile::PLA));
  assert(purge.requestMaterialChange(MaterialProfile::PET, in));
  assert(!purge.update(in, 0).view.purge_run_completed);
  assert(purge.requestPurgePreheat(in));
  out = completeCoolingStartupProbe(purge, in, 100);
  assert(purge.process().materialSession() == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  assert(out.actuators.cooling_pwm > 0 && out.actuators.screw_pwm == 0 &&
         !out.actuators.feeder_enable && out.actuators.puller_pwm == 0 &&
         out.actuators.spooler_pwm == 0 && !out.actuators.traverse_enable);
  assert(!purge.confirmPurgeWastePath(in, 2000));
  in.purge_feed_approved = true;
  out = purge.update(in, 1800);
  assert(out.actuators.screw_pwm == 0 && !out.actuators.feeder_enable && out.actuators.puller_pwm == 0);
  assert(!purge.confirmPurgeWastePath(in, 2000));
  in.purge_waste_path_confirmed = true;
  assert(!purge.confirmPurgeWastePath(in, 2000));  // Raw snapshot flags cannot bypass the operator API.
  assert(purge.approvePurgeFeed(true));
  out = purge.update(in, 1900);
  assert(out.actuators.screw_pwm == 0 && !out.actuators.feeder_enable && out.actuators.puller_pwm == 0);
  InputSnapshot purge_commit_fan_lost = in;
  purge_commit_fan_lost.cooling_feedback_valid = false;
  assert(!purge.confirmPurgeWastePath(purge_commit_fan_lost, 1950));
  out = purge.update(purge_commit_fan_lost, 1950);
  assert(purge.process().materialSession() == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  assert(out.actuators.screw_pwm == 0 && !out.actuators.feeder_enable && out.actuators.puller_pwm == 0);
  assert(purge.confirmPurgeWastePath(in, 2000));
  InputSnapshot purge_start = in;
  purge_start.screw_rpm = 0.0f;
  out = purge.update(purge_start, 2000);
  assert(!out.view.purge_run_completed);
  assert(!purge.confirmPurgeComplete(true, in, 2000));  // Elapsed time and measured revolutions are insufficient.
  assert(out.actuators.screw_pwm > 0 && out.actuators.feeder_enable && out.actuators.puller_pwm > 0);
  assert(purge.process().material() == MaterialProfile::PLA);
  purge.update(in, 122000);
  InputSnapshot unsafe_purge_completion = in;
  unsafe_purge_completion.safety.service_guard_closed = false;
  assert(!purge.confirmPurgeComplete(true, unsafe_purge_completion, 122000));
  assert(purge.process().materialSession() == MaterialSession::PURGE_RUNNING);
  unsafe_purge_completion = in;
  unsafe_purge_completion.safety.estop_ok = false;
  assert(!purge.confirmPurgeComplete(true, unsafe_purge_completion, 122000));
  assert(purge.process().materialSession() == MaterialSession::PURGE_RUNNING);
  assert(purge.confirmPurgeComplete(true, in, 122000));
  out = purge.update(in, 122000);
  assert(out.view.purge_run_completed);
  assert(!out.view.purge_feed_approved);
  assert(purge.process().state() == MachineState::COOLDOWN);
  assert(out.actuators.cooling_pwm > 0 && out.actuators.screw_pwm == 0 &&
         !out.actuators.feeder_enable && out.actuators.puller_pwm == 0 &&
         out.actuators.spooler_pwm == 0 && !out.actuators.traverse_enable);
  for (bool heater_on : out.actuators.heater_on) assert(!heater_on);
  InputSnapshot purge_safe_temperature = in;
  for (uint8_t channel = 0; channel < 4; ++channel)
    purge_safe_temperature.temperatures[channel].celsius = COOLDOWN_SAFE_TEMPERATURE_C;
  out = purge.update(purge_safe_temperature, 122001);
  assert(purge.process().state() == MachineState::IDLE && out.actuators.cooling_pwm == 0);
  assert(purge.process().material() == MaterialProfile::PLA);
  assert(purge.acknowledgeMaterialStep(MaterialSession::SCREEN_CLEAN_REQUIRED, true));
  assert(purge.acknowledgeMaterialStep(MaterialSession::HOPPER_CLEAN_REQUIRED, true));
  assert(purge.acknowledgeMaterialStep(MaterialSession::TEMPERATURE_TRANSITION_REQUIRED, true));
  assert(purge.acknowledgeMaterialStep(MaterialSession::FINAL_CONFIRM_REQUIRED, true));
  assert(purge.process().material() == MaterialProfile::PET);

  // Approval is single-use: stale snapshot data cannot authorize the next material-change purge.
  assert(purge.requestMaterialChange(MaterialProfile::PLA, in));
  assert(!purge.update(in, 123000).view.purge_feed_approved);
  assert(purge.requestPurgePreheat(in));
  completeCoolingStartupProbe(purge, in, 123100);
  assert(purge.process().materialSession() == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  assert(!purge.confirmPurgeWastePath(in, 125000));
  assert(purge.approvePurgeFeed(true));
  assert(purge.confirmPurgeWastePath(in, 125000));
  purge.requestStop(in);
  out = purge.update(in, 125001);
  assert(purge.process().state() == MachineState::COOLDOWN);
  assert(purge.process().materialSession() == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(out.actuators.cooling_pwm > 0 && out.actuators.screw_pwm == 0 &&
         !out.actuators.feeder_enable && out.actuators.puller_pwm == 0);
  out = purge.update(purge_safe_temperature, 125002);
  assert(purge.process().state() == MachineState::IDLE && out.actuators.cooling_pwm == 0);

  MachineSupervisor purge_probe_abort;
  calibrate(purge_probe_abort);
  assert(purge_probe_abort.selectMaterial(MaterialProfile::PLA));
  assert(purge_probe_abort.requestMaterialChange(MaterialProfile::PET, in));
  assert(purge_probe_abort.requestPurgePreheat(in));
  InputSnapshot fan_off = in;
  fan_off.cooling_feedback_valid = false;
  out = purge_probe_abort.update(fan_off, 0);
  assert(out.actuators.cooling_pwm > 0);
  purge_probe_abort.requestStop(fan_off);
  out = purge_probe_abort.update(fan_off, 1);
  assert(purge_probe_abort.process().state() == MachineState::IDLE);
  assert(purge_probe_abort.process().materialSession() == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(out.actuators.cooling_pwm == 0 && out.actuators.screw_pwm == 0 &&
         !out.actuators.feeder_enable && out.actuators.puller_pwm == 0);

  // Regression: purge E-stop/clear returns to an explicit safe restart point without early material commit.
  MachineSupervisor aborted_purge;
  calibrate(aborted_purge);
  assert(aborted_purge.selectMaterial(MaterialProfile::PLA));
  assert(aborted_purge.requestMaterialChange(MaterialProfile::PET, in));
  assert(aborted_purge.requestPurgePreheat(in));
  completeCoolingStartupProbe(aborted_purge, in, 100);
  assert(aborted_purge.approvePurgeFeed(true));
  assert(aborted_purge.confirmPurgeWastePath(in, 2000));
  assert(!aborted_purge.update(in, 2000).view.purge_run_completed);
  estop.purge_feed_approved = true;
  aborted_purge.update(estop, 2100);
  assert(aborted_purge.process().state() == MachineState::ESTOP);
  assert(aborted_purge.clearAllFaults(in, true));
  assert(aborted_purge.process().state() == MachineState::IDLE);
  assert(aborted_purge.process().materialSession() == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(aborted_purge.process().material() == MaterialProfile::PLA);

  // Regression: purge screw-driver failure aborts outputs and returns to the safe restart session after clear.
  MachineSupervisor purge_drive_fault;
  calibrate(purge_drive_fault);
  assert(purge_drive_fault.selectMaterial(MaterialProfile::PLA));
  assert(purge_drive_fault.requestMaterialChange(MaterialProfile::PET, in));
  assert(purge_drive_fault.requestPurgePreheat(in));
  completeCoolingStartupProbe(purge_drive_fault, in, 100);
  assert(purge_drive_fault.approvePurgeFeed(true));
  assert(purge_drive_fault.confirmPurgeWastePath(in, 2000));
  InputSnapshot screw_fault = in;
  screw_fault.safety.driver_fault_free = false;
  out = purge_drive_fault.update(screw_fault, 2200);
  assert(purge_drive_fault.process().state() == MachineState::FAULT);
  assert(out.actuators.screw_pwm == 0 && !out.actuators.feeder_enable);
  assert(purge_drive_fault.clearAllFaults(in, true));
  assert(purge_drive_fault.process().materialSession() == MaterialSession::PURGE_PREHEAT_REQUIRED);

  // A mature purge cannot keep motion when completion is attempted with fresh cooling loss.
  MachineSupervisor purge_completion_cooling_fault;
  calibrate(purge_completion_cooling_fault);
  assert(purge_completion_cooling_fault.selectMaterial(MaterialProfile::PLA));
  assert(purge_completion_cooling_fault.requestMaterialChange(MaterialProfile::PET, in));
  assert(purge_completion_cooling_fault.requestPurgePreheat(in));
  completeCoolingStartupProbe(purge_completion_cooling_fault, in, 100);
  assert(purge_completion_cooling_fault.approvePurgeFeed(true));
  assert(purge_completion_cooling_fault.confirmPurgeWastePath(in, 2000));
  purge_completion_cooling_fault.update(in, 122000);
  InputSnapshot completion_fan_lost = in;
  completion_fan_lost.cooling_feedback_valid = false;
  assert(!purge_completion_cooling_fault.confirmPurgeComplete(true, completion_fan_lost, 122000));
  assert(purge_completion_cooling_fault.process().materialSession() == MaterialSession::PURGE_RUNNING);
  out = purge_completion_cooling_fault.update(completion_fan_lost, 122000);
  assert(purge_completion_cooling_fault.process().state() == MachineState::FAULT);
  assert(out.actuators.cooling_pwm == 0 && out.actuators.screw_pwm == 0 &&
         !out.actuators.feeder_enable && out.actuators.puller_pwm == 0);

  // Regression: cooling feedback dwell applies during purge and preserves the pending material on clear.
  MachineSupervisor purge_cooling_fault;
  calibrate(purge_cooling_fault);
  assert(purge_cooling_fault.selectMaterial(MaterialProfile::PLA));
  assert(purge_cooling_fault.requestMaterialChange(MaterialProfile::PET, in));
  assert(purge_cooling_fault.requestPurgePreheat(in));
  completeCoolingStartupProbe(purge_cooling_fault, in, 100);
  assert(purge_cooling_fault.approvePurgeFeed(true));
  assert(purge_cooling_fault.confirmPurgeWastePath(in, 2000));
  InputSnapshot purge_fan_failed = in;
  purge_fan_failed.cooling_feedback_valid = false;
  out = purge_cooling_fault.update(purge_fan_failed, 2100);
  assert(purge_cooling_fault.process().state() == MachineState::MAINTENANCE_PURGE);
  out = purge_cooling_fault.update(purge_fan_failed, 2100 + COOLING_FEEDBACK_DWELL_MS);
  assert(purge_cooling_fault.process().state() == MachineState::FAULT);
  assert(purge_cooling_fault.formingState() == FormingChainState::LATCHED_FAULT);
  assert((purge_cooling_fault.formingFaultReasons() & FORMING_COOLING_FAILURE) != 0);
  assert(out.actuators.screw_pwm == 0 && !out.actuators.feeder_enable && out.actuators.cooling_pwm == 0);
  assert(purge_cooling_fault.process().material() == MaterialProfile::PLA);
  assert(purge_cooling_fault.clearAllFaults(in, true));
  assert(purge_cooling_fault.process().materialSession() == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(purge_cooling_fault.process().pendingMaterial() == MaterialProfile::PET);

  // Regression: preheat cooling loss is also latched instead of silently continuing heat.
  MachineSupervisor preheat_cooling_fault;
  calibrate(preheat_cooling_fault);
  assert(preheat_cooling_fault.selectMaterial(MaterialProfile::PLA));
  assert(preheat_cooling_fault.requestPreheat(in));
  completeCoolingStartupProbe(preheat_cooling_fault, in, 100);
  out = preheat_cooling_fault.update(purge_fan_failed, 2000);
  assert(preheat_cooling_fault.process().state() == MachineState::PREHEATING);
  out = preheat_cooling_fault.update(purge_fan_failed, 2000 + COOLING_FEEDBACK_DWELL_MS);
  assert(preheat_cooling_fault.process().state() == MachineState::FAULT);
  assert(out.actuators.cooling_pwm == 0);
  assert(preheat_cooling_fault.clearAllFaults(purge_fan_failed, true));
  assert(preheat_cooling_fault.process().state() == MachineState::IDLE);
  out = preheat_cooling_fault.update(purge_fan_failed, 4000);
  assert(out.actuators.cooling_pwm == 0);
  assert(preheat_cooling_fault.requestPreheat(purge_fan_failed));
  out = preheat_cooling_fault.update(purge_fan_failed, 4100);
  assert(preheat_cooling_fault.process().state() == MachineState::IDLE && out.actuators.cooling_pwm > 0);
  for (bool heater_on : out.actuators.heater_on) assert(!heater_on);

  // Regression: a persistent heater sensor fault blocks the entire clear transaction.
  MachineSupervisor heater_fault;
  calibrate(heater_fault);
  assert(heater_fault.selectMaterial(MaterialProfile::PLA));
  assert(heater_fault.requestPreheat(in));
  completeCoolingStartupProbe(heater_fault, in, 100);
  InputSnapshot sensor_open = in;
  sensor_open.temperatures[0] = {-273.0f, false, true, 2000};
  out = heater_fault.update(sensor_open, 2000);
  const uint16_t heater_bits = heater_fault.heaterFaults();
  assert(heater_bits != HEATER_FAULT_NONE);
  assert(out.actuators.cooling_pwm > 0);  // General fault retains only verified cooling.
  assert(out.actuators.screw_pwm == 0 && out.actuators.puller_pwm == 0 &&
         out.actuators.spooler_pwm == 0 && !out.actuators.feeder_enable);
  assert(!heater_fault.clearAllFaults(sensor_open, true));
  assert(heater_fault.heaterFaults() == heater_bits && heater_fault.process().state() == MachineState::FAULT);
  out = heater_fault.update(sensor_open, 2100);
  assert(out.view.ui_state == SupervisorUiState::FAULT_CLEAR_BLOCKED);
  InputSnapshot guard_open = in;
  guard_open.safety.service_guard_closed = false;
  assert(!heater_fault.clearAllFaults(guard_open, true));
  assert(heater_fault.heaterFaults() == heater_bits && heater_fault.process().state() == MachineState::FAULT);
  assert(heater_fault.clearAllFaults(in, true));

  // Regression: mechanical hard-stop contact is latched, never a normal controlled-stop success.
  MachineSupervisor hard_stop;
  calibrate(hard_stop);
  assert(hard_stop.selectMaterial(MaterialProfile::PLA));
  assert(hard_stop.requestPreheat(in));
  completeCoolingStartupProbe(hard_stop, in, 100);
  assert(hard_stop.armExtrusion(in, 1800));
  InputSnapshot impact = in;
  impact.dancer_angle_rad = DANCER_MECHANICAL_HARD_STOP_RAD + 0.01f;
  out = hard_stop.update(impact, 2000);
  assert(hard_stop.formingState() == FormingChainState::LATCHED_FAULT);
  assert(hard_stop.process().state() == MachineState::FAULT);
  assert(out.actuators.screw_pwm == 0 && out.actuators.puller_pwm == 0);

  // Regression: first puller command gets one bounded tach grace; running loss gets no new grace.
  MachineSupervisor puller_startup;
  calibrate(puller_startup);
  assert(puller_startup.selectMaterial(MaterialProfile::PLA));
  assert(puller_startup.requestPreheat(in));
  completeCoolingStartupProbe(puller_startup, in, 100);
  assert(puller_startup.armExtrusion(in, 1800));
  InputSnapshot no_puller_tach = in;
  no_puller_tach.puller_tach_ok = false;
  out = puller_startup.update(no_puller_tach, 2000);
  assert(puller_startup.formingState() == FormingChainState::REQUALIFYING && out.actuators.puller_pwm > 0);
  out = puller_startup.update(no_puller_tach, 2000 + PULLER_TACH_STARTUP_GRACE_MS - 1);
  assert(puller_startup.formingState() == FormingChainState::REQUALIFYING);
  assert(out.actuators.puller_pwm == 0);  // Inner loop fails zero before the supervisor grace expires.
  out = puller_startup.update(no_puller_tach, 2000 + PULLER_TACH_STARTUP_GRACE_MS);
  assert(puller_startup.formingState() == FormingChainState::RUNDOWN);
  assert((puller_startup.formingFaultReasons() & FORMING_PULLER_TACH_FAILURE) != 0);

  MachineSupervisor puller_running_loss;
  calibrate(puller_running_loss);
  assert(puller_running_loss.selectMaterial(MaterialProfile::PLA));
  assert(puller_running_loss.requestPreheat(in));
  completeCoolingStartupProbe(puller_running_loss, in, 100);
  assert(puller_running_loss.armExtrusion(in, 1800));
  puller_running_loss.update(no_puller_tach, 2000);  // First command edge; pre-command sample is ignored.
  out = puller_running_loss.update(in, 2100);        // First real tach feedback qualifies startup.
  assert(puller_running_loss.formingState() == FormingChainState::REQUALIFYING);
  out = puller_running_loss.update(no_puller_tach, 2200);
  assert(puller_running_loss.formingState() == FormingChainState::RUNDOWN);

  // Regression: cooling command loss uses bounded dwell, then disables cooling and enters common rundown.
  MachineSupervisor cooling_loss;
  calibrate(cooling_loss);
  assert(cooling_loss.selectMaterial(MaterialProfile::PLA));
  assert(cooling_loss.requestPreheat(in));
  completeCoolingStartupProbe(cooling_loss, in, 100);
  assert(cooling_loss.armExtrusion(in, 1800));
  InputSnapshot fan_failed = in;
  fan_failed.cooling_feedback_valid = false;
  out = cooling_loss.update(fan_failed, 1900);
  assert(cooling_loss.formingState() == FormingChainState::REQUALIFYING);
  out = cooling_loss.update(fan_failed, 1900 + COOLING_FEEDBACK_DWELL_MS);
  assert(cooling_loss.formingState() == FormingChainState::RUNDOWN);
  assert((cooling_loss.formingFaultReasons() & FORMING_COOLING_FAILURE) != 0);
  assert(out.actuators.cooling_pwm == 0 && out.actuators.spooler_pwm == 0);
  const uint32_t rundown_done = 1900 + COOLING_FEEDBACK_DWELL_MS + FORMING_SCREW_RUNDOWN_MS;
  out = cooling_loss.update(fan_failed, rundown_done);
  assert(cooling_loss.formingState() == FormingChainState::THERMAL_HOLD);
  const uint32_t probe_started = rundown_done + THERMAL_HOLD_MS;
  out = cooling_loss.update(fan_failed, probe_started);
  assert(cooling_loss.formingState() == FormingChainState::THERMAL_HOLD);
  assert(out.actuators.cooling_pwm > 0);  // Recovery probe is a real command after bounded hold.
  const uint32_t recovery_seen = probe_started + 1;
  cooling_loss.update(in, recovery_seen);
  const uint32_t requal_started = recovery_seen + COOLING_FEEDBACK_DWELL_MS;
  out = cooling_loss.update(in, requal_started);
  assert(cooling_loss.formingState() == FormingChainState::REQUALIFYING);
  for (uint32_t t = requal_started + 200; t <= requal_started + 4000; t += 200)
    out = cooling_loss.update(in, t);
  const uint32_t requal_done = requal_started + REQUALIFICATION_TRANSPORT_PLA_MS;
  out = cooling_loss.update(in, requal_done);
  assert(cooling_loss.formingState() == FormingChainState::READY_TO_RETHREAD);
  assert(cooling_loss.confirmManualRethread(in));
  out = cooling_loss.update(in, requal_done + 1);
  assert(cooling_loss.formingFaultReasons() == FORMING_FAULT_NONE);
  assert(out.actuators.cooling_pwm > 0 && cooling_loss.spoolEligible());

  // Regression: generated per-state caps are applied to actual heater commands.
  MachineSupervisor power;
  calibrate(power);
  assert(power.selectMaterial(MaterialProfile::PLA));
  InputSnapshot cold_heaters = in;
  for (auto &temperature : cold_heaters.temperatures) temperature = {25.0f, true, false, 0};
  assert(power.requestPreheat(cold_heaters));
  out = completeCoolingStartupProbe(power, cold_heaters, 100);
  assert(out.view.commanded_heater_power_w <= STATE_HEATER_PEAK_CAP_W[static_cast<uint8_t>(MachineState::PREHEATING)]);
  assert(out.view.commanded_heater_power_w + 45.0f <= NORMAL_PHASE_PEAK_LIMIT_W);
  assert(power.armExtrusion(cold_heaters, 1800));
  bool zone_seen[4]{};
  for (uint32_t t = 2000; t <= 2600; t += 200) {
    out = power.update(cold_heaters, t);
    assert(out.view.commanded_heater_power_w <= STATE_HEATER_PEAK_CAP_W[static_cast<uint8_t>(MachineState::REQUALIFYING)]);
    assert(out.view.commanded_heater_power_w + 135.0f <= NORMAL_PHASE_PEAK_LIMIT_W);
    for (uint8_t zone = 0; zone < 4; ++zone) zone_seen[zone] = zone_seen[zone] || out.actuators.heater_on[zone];
  }
  for (bool seen : zone_seen) assert(seen);  // rotating priority prevents cap-induced starvation.

  // Regression: cooldown completes automatically only at the canonical safe temperature with valid cooling.
  MachineSupervisor cooldown;
  calibrate(cooldown);
  assert(cooldown.selectMaterial(MaterialProfile::PLA));
  assert(cooldown.requestPreheat(in));
  completeCoolingStartupProbe(cooldown, in, 100);
  cooldown.requestStop(in);
  assert(cooldown.process().state() == MachineState::COOLDOWN);
  InputSnapshot hot = in;
  for (uint8_t channel = 0; channel < 4; ++channel) hot.temperatures[channel].celsius = 61.0f;
  assert(!cooldown.canCompleteCooldown(hot));
  out = cooldown.update(hot, 2000);
  assert(cooldown.process().state() == MachineState::COOLDOWN && out.actuators.cooling_pwm > 0);
  InputSnapshot cool = in;
  for (uint8_t channel = 0; channel < 4; ++channel) cool.temperatures[channel].celsius = COOLDOWN_SAFE_TEMPERATURE_C;
  assert(cooldown.canCompleteCooldown(cool));
  out = cooldown.update(cool, 2100);
  assert(cooldown.process().state() == MachineState::IDLE);
  assert(out.actuators.cooling_pwm == 0 && out.actuators.screw_pwm == 0);
  out = cooldown.update(cool, 2200);
  assert(cooldown.process().state() == MachineState::IDLE && out.actuators.screw_pwm == 0);

  // v0.6.2: the individual fan tach channels feed the common forming fault.
  MachineSupervisor single_fan_loss;
  const uint32_t fan_prod = enterProductionExtrusion(single_fan_loss, in);
  InputSnapshot fan1_stopped = in;
  fan1_stopped.fan1_rpm = 0;
  single_fan_loss.update(fan1_stopped, fan_prod + 1);
  out = single_fan_loss.update(fan1_stopped, fan_prod + COOLING_FEEDBACK_DWELL_MS + 2);
  assert(single_fan_loss.formingState() == FormingChainState::RUNDOWN);
  assert((single_fan_loss.formingFaultReasons() & FORMING_COOLING_FAILURE) != 0);
  assert(!out.actuators.feeder_enable && out.actuators.spooler_pwm == 0 &&
         !out.actuators.traverse_enable && out.actuators.waste_path_active);

  MachineSupervisor dual_fan_loss;
  const uint32_t dual_fan_prod = enterProductionExtrusion(dual_fan_loss, in);
  InputSnapshot both_fans_stopped = in;
  both_fans_stopped.fan1_rpm = 0;
  both_fans_stopped.fan2_rpm = 0;
  dual_fan_loss.update(both_fans_stopped, dual_fan_prod + 1);
  out = dual_fan_loss.update(both_fans_stopped,
                             dual_fan_prod + COOLING_FEEDBACK_DWELL_MS + 2);
  assert(dual_fan_loss.formingState() == FormingChainState::RUNDOWN);
  assert((out.view.cooling.fault_bits & COOLING_FAN1_STOPPED) != 0);
  assert((out.view.cooling.fault_bits & COOLING_FAN2_STOPPED) != 0);

  // v0.6.2: actual inner-loop saturation, not a hard-coded input, drives rundown.
  MachineSupervisor persistent_saturation;
  const uint32_t saturation_prod = enterProductionExtrusion(persistent_saturation, in);
  assert(persistent_saturation.configurePullerCalibration(
      {30.0f, 20.0f, 2.0f, 8.0f, 1.2f, 45, 255, 200, 600, 800, 2.0f}));
  InputSnapshot stalled_puller = in;
  stalled_puller.puller_rpm = 0;
  persistent_saturation.update(stalled_puller, saturation_prod + 201);
  persistent_saturation.update(stalled_puller, saturation_prod + 1002);
  persistent_saturation.update(stalled_puller, saturation_prod + 1803);
  out = persistent_saturation.update(stalled_puller, saturation_prod + 1804);
  assert(persistent_saturation.formingState() == FormingChainState::RUNDOWN);
  assert((persistent_saturation.formingFaultReasons() & FORMING_PULLER_SATURATION) != 0);
  assert(out.view.forming_fault_detected_ms != 0 && out.actuators.waste_path_active);

  // v0.6.2: purge/production state uses measured screw motion and faults slip.
  MachineSupervisor screw_stationary;
  const uint32_t screw_prod = enterProductionExtrusion(screw_stationary, in);
  InputSnapshot no_screw_motion = in;
  no_screw_motion.screw_rpm = 0;
  no_screw_motion.screw_tach_valid = false;
  screw_stationary.update(no_screw_motion, screw_prod + 1);
  out = screw_stationary.update(no_screw_motion, screw_prod + 1602);
  assert(screw_stationary.formingState() == FormingChainState::RUNDOWN);
  assert((screw_stationary.formingFaultReasons() & FORMING_SCREW_MOTION_MISMATCH) != 0);

  // v0.6.2: spool jam detection comes from closed-loop command/tach mismatch.
  MachineSupervisor real_spool_jam;
  const uint32_t spool_prod = enterProductionExtrusion(real_spool_jam, in);
  InputSnapshot stopped_spool = in;
  stopped_spool.spooler_rpm = 0;
  stopped_spool.spooler_tach_ok = false;
  real_spool_jam.update(stopped_spool, spool_prod + 1500);
  real_spool_jam.update(stopped_spool, spool_prod + 2601);
  out = real_spool_jam.update(stopped_spool, spool_prod + 2602);
  assert(real_spool_jam.formingState() == FormingChainState::RUNDOWN);
  assert((real_spool_jam.formingFaultReasons() & FORMING_SPOOL_JAM) != 0);

  std::cout << "MACHINE_SUPERVISOR_TRANSACTIONS_PURGE_RUNDOWN_REQUALIFICATION_OK\n";
}
