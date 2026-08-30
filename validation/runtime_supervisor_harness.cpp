#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>

#include "machine_supervisor.h"

namespace {

const char *name(MachineState value) {
  switch (value) {
    case MachineState::IDLE: return "IDLE";
    case MachineState::SHREDDING: return "SHREDDING";
    case MachineState::PREHEATING: return "PREHEATING";
    case MachineState::EXTRUSION: return "EXTRUSION";
    case MachineState::MAINTENANCE_PURGE: return "MAINTENANCE_PURGE";
    case MachineState::FORMING_CHAIN_RUNDOWN: return "FORMING_CHAIN_RUNDOWN";
    case MachineState::THERMAL_HOLD: return "THERMAL_HOLD";
    case MachineState::REQUALIFYING: return "REQUALIFYING";
    case MachineState::COOLDOWN: return "COOLDOWN";
    case MachineState::FAULT: return "FAULT";
    case MachineState::ESTOP: return "ESTOP";
  }
  return "UNKNOWN";
}

const char *name(MaterialSession value) {
  switch (value) {
    case MaterialSession::CLEAN: return "CLEAN";
    case MaterialSession::PLA_ACTIVE: return "PLA_ACTIVE";
    case MaterialSession::PET_ACTIVE: return "PET_ACTIVE";
    case MaterialSession::PURGE_PREHEAT_REQUIRED: return "PURGE_PREHEAT_REQUIRED";
    case MaterialSession::PURGE_READY_CONFIRM_REQUIRED: return "PURGE_READY_CONFIRM_REQUIRED";
    case MaterialSession::PURGE_RUNNING: return "PURGE_RUNNING";
    case MaterialSession::SCREEN_CLEAN_REQUIRED: return "SCREEN_CLEAN_REQUIRED";
    case MaterialSession::HOPPER_CLEAN_REQUIRED: return "HOPPER_CLEAN_REQUIRED";
    case MaterialSession::TEMPERATURE_TRANSITION_REQUIRED: return "TEMPERATURE_TRANSITION_REQUIRED";
    case MaterialSession::FINAL_CONFIRM_REQUIRED: return "FINAL_CONFIRM_REQUIRED";
  }
  return "UNKNOWN";
}

const char *name(FormingChainState value) {
  switch (value) {
    case FormingChainState::NORMAL: return "NORMAL";
    case FormingChainState::RUNDOWN: return "RUNDOWN";
    case FormingChainState::THERMAL_HOLD: return "THERMAL_HOLD";
    case FormingChainState::REQUALIFYING: return "REQUALIFYING";
    case FormingChainState::READY_TO_RETHREAD: return "READY_TO_RETHREAD";
    case FormingChainState::LATCHED_FAULT: return "LATCHED_FAULT";
  }
  return "UNKNOWN";
}

const char *name(MaterialProfile value) {
  switch (value) {
    case MaterialProfile::NONE: return "NONE";
    case MaterialProfile::PLA: return "PLA";
    case MaterialProfile::PET: return "PET";
  }
  return "UNKNOWN";
}

const char *name(CoolingStartupRequest value) {
  switch (value) {
    case CoolingStartupRequest::NONE: return "NONE";
    case CoolingStartupRequest::PREHEAT: return "PREHEAT";
    case CoolingStartupRequest::PURGE_PREHEAT: return "PURGE_PREHEAT";
  }
  return "UNKNOWN";
}

const char *name(SupervisorUiState value) {
  switch (value) {
    case SupervisorUiState::CALIBRATION_REQUIRED: return "CALIBRATION_REQUIRED";
    case SupervisorUiState::READY_TO_PREHEAT: return "READY_TO_PREHEAT";
    case SupervisorUiState::COOLING_STARTUP_PROBE: return "COOLING_STARTUP_PROBE";
    case SupervisorUiState::READY_TO_EXTRUDE: return "READY_TO_EXTRUDE";
    case SupervisorUiState::RUNNING: return "RUNNING";
    case SupervisorUiState::MAINTENANCE_PURGE: return "MAINTENANCE_PURGE";
    case SupervisorUiState::FORMING_CHAIN_RUNDOWN: return "FORMING_CHAIN_RUNDOWN";
    case SupervisorUiState::REQUALIFYING: return "REQUALIFYING";
    case SupervisorUiState::READY_TO_RETHREAD: return "READY_TO_RETHREAD";
    case SupervisorUiState::FAULT_CLEAR_BLOCKED: return "FAULT_CLEAR_BLOCKED";
    case SupervisorUiState::FAULT: return "FAULT";
    case SupervisorUiState::ESTOP: return "ESTOP";
  }
  return "UNKNOWN";
}

InputSnapshot safeInput(uint32_t now_ms = 0) {
  InputSnapshot input;
  input.safety = {true, true, true, true, true, true, true, true, true};
  for (auto &temperature : input.temperatures) {
    temperature = {200.0f, true, false, now_ms};
  }
  input.gauge_x_adc = 975;
  input.gauge_y_adc = 975;
  input.gauge_optical_valid = true;
  input.shredder_current_amp = 2.0f;
  input.shredder_rpm = 32.0f;
  input.screw_rpm = 16.0f;
  input.cooling_feedback_valid = true;
  input.puller_driver_ok = true;
  input.puller_tach_ok = true;
  input.puller_saturated = false;
  input.spooler_driver_ok = true;
  input.traverse_permission_ok = true;
  input.dancer_angle_rad = 0.0f;
  return input;
}

void configure(MachineSupervisor &supervisor, bool gauge = true) {
  DriveCalibration drive = REFERENCE_DRIVE_CALIBRATION;
  drive.verified = true;
  assert(supervisor.configureDriveCalibration(drive));
  assert(supervisor.configureCurrentSensorCalibration(512.0f, 0.01f));
  assert(supervisor.configureCoolingFeedbackCalibration(100.0f, 0.01f));
  if (gauge) assert(supervisor.configureGaugeCalibration({100, 0.002f, 100, 0.002f, 0.02f, true}));
}

bool anyHeater(const ActuatorCommands &commands) {
  for (bool value : commands.heater_on) {
    if (value) return true;
  }
  return false;
}

bool hazardous(const ActuatorCommands &commands) {
  return commands.shredder_pwm != 0 || commands.feeder_enable || commands.screw_pwm != 0 ||
         commands.puller_pwm != 0 || commands.spooler_pwm != 0 || commands.traverse_enable ||
         commands.cooling_pwm != 0 || anyHeater(commands);
}

bool onlyCooling(const ActuatorCommands &commands) {
  return commands.cooling_pwm != 0 && commands.shredder_pwm == 0 &&
         !commands.feeder_enable && commands.screw_pwm == 0 &&
         commands.puller_pwm == 0 && commands.spooler_pwm == 0 &&
         !commands.traverse_enable && !commands.hopper_ptc_on && !anyHeater(commands);
}

bool purgeMotionStopped(const ActuatorCommands &commands) {
  return commands.screw_pwm == 0 && !commands.feeder_enable && commands.puller_pwm == 0 &&
         commands.spooler_pwm == 0 && !commands.traverse_enable;
}

struct TraceMeta {
  const char *scenario;
  const char *fault_reason{"NONE"};
  bool nominal_spool_jam{false};
  bool explicit_restart_issued{true};
};

void emit(const TraceMeta &meta, uint32_t now_ms, const InputSnapshot &input,
          const SupervisorOutput &output, const MachineSupervisor &supervisor) {
  const auto &c = output.actuators;
  const auto &v = output.view;
  const float diameter_error = ((input.gauge_x_adc - 100) * 0.002f +
                                (input.gauge_y_adc - 100) * 0.002f) /
                                   2.0f -
                               1.75f;
  const float ovality = ((input.gauge_x_adc > input.gauge_y_adc)
                             ? input.gauge_x_adc - input.gauge_y_adc
                             : input.gauge_y_adc - input.gauge_x_adc) *
                        0.002f;
  const uint32_t stable_ms = v.requalification_diameter_stable_ms < v.requalification_ovality_stable_ms
                                 ? v.requalification_diameter_stable_ms
                                 : v.requalification_ovality_stable_ms;
  const uint32_t required_transport_ms = supervisor.process().material() == MaterialProfile::PET
                                             ? REQUALIFICATION_TRANSPORT_PET_MS
                                             : REQUALIFICATION_TRANSPORT_PLA_MS;
  std::cout << meta.scenario << '|' << now_ms << '|' << name(v.ui_state) << '|'
            << name(v.process_phase) << '|'
            << name(v.material_session) << '|' << name(v.forming_chain_state) << '|'
            << meta.fault_reason << '|' << v.calibration.drive_calibration_valid << '|'
            << v.calibration.gauge_calibration_valid << '|'
            << v.calibration.current_sensor_calibration_valid << '|'
            << v.calibration.cooling_feedback_calibration_valid << '|'
            << v.calibration.temperature_channels_valid << '|' << input.safety.driver_fault_free << '|'
            << v.purge_feed_approved << '|' << input.purge_waste_path_confirmed << '|'
            << v.spool_eligible << '|'
            << v.waste_mode << '|' << (v.heater_faults != HEATER_FAULT_NONE) << '|'
            << v.shredder_fault_latched << '|'
            << (v.forming_chain_state == FormingChainState::LATCHED_FAULT) << '|'
            << (v.process_phase == MachineState::SHREDDING && c.shredder_pwm != 0) << '|'
            << name(supervisor.process().pendingMaterial()) << '|' << v.purge_run_completed << '|'
            << (c.cooling_pwm * 100.0f / 255.0f) << '|' << v.cooling_feedback_valid << '|'
            << (v.cooling_failure_dwell_ms >= COOLING_FEEDBACK_DWELL_MS) << '|'
            << name(v.cooling_startup_request) << '|' << v.cooling_startup_probe_elapsed_ms << '|'
            << v.cooling_startup_healthy_dwell_ms << '|' << input.dancer_angle_rad << '|'
            << DANCER_MECHANICAL_HARD_STOP_RAD << '|' << meta.nominal_spool_jam << '|'
            << static_cast<unsigned>(v.requalification_valid_samples) << '|' << 0.02f << '|'
            << diameter_error << '|' << ovality << '|' << stable_ms << '|'
            << (v.requalification_transport_elapsed_ms >= required_transport_ms) << '|'
            << input.puller_saturated << '|'
            << !input.safety.estop_ok << '|' << meta.explicit_restart_issued << '|'
            << v.purge_screw_revolutions << '|' << v.purge_screw_revolutions_measured << '|'
            << v.commanded_heater_power_w << '|' << 0.0f << '|'
            << (c.shredder_pwm != 0) << '|' << (c.screw_pwm != 0)
            << '|' << anyHeater(c) << '|' << c.feeder_enable << '|'
            << (c.puller_pwm != 0) << '|' << (c.spooler_pwm != 0) << '|'
            << c.traverse_enable << '|' << (c.cooling_pwm != 0) << '|'
            << output.invariants_ok << '\n';
}

void assertOutputInvariant(const SupervisorOutput &output) {
  assert(output.invariants_ok);
  assert(!(output.actuators.shredder_pwm != 0 &&
           (output.actuators.screw_pwm != 0 || anyHeater(output.actuators))));
  assert(!((output.actuators.spooler_pwm != 0 || output.actuators.traverse_enable) &&
           !output.view.spool_eligible));
  if (output.view.process_phase == MachineState::ESTOP) assert(!hazardous(output.actuators));
}

SupervisorOutput completeCoolingStartup(MachineSupervisor &supervisor, InputSnapshot &input,
                                        uint32_t &now_ms) {
  auto output = supervisor.update(input, now_ms);
  assert(output.view.process_phase == MachineState::IDLE);
  assert(output.view.cooling_startup_request != CoolingStartupRequest::NONE);
  assert(onlyCooling(output.actuators));
  output = supervisor.update(input, ++now_ms);
  assert(output.view.process_phase == MachineState::IDLE);
  assert(onlyCooling(output.actuators));
  now_ms += COOLING_FEEDBACK_DWELL_MS;
  output = supervisor.update(input, now_ms);
  assert(output.view.cooling_startup_request == CoolingStartupRequest::NONE);
  return output;
}

void coolingStartupProbe() {
  auto input = safeInput();
  input.cooling_feedback_valid = false;
  MachineSupervisor preheat;
  configure(preheat);
  assert(preheat.selectMaterial(MaterialProfile::PLA));
  assert(preheat.requestPreheat(input));
  auto output = preheat.update(input, 0);
  assert(output.view.process_phase == MachineState::IDLE);
  assert(output.view.cooling_startup_request == CoolingStartupRequest::PREHEAT);
  assert(onlyCooling(output.actuators));
  emit({"preheat_fan_first_startup_proof"}, 0, input, output, preheat);
  input.cooling_feedback_valid = true;
  output = preheat.update(input, 1);
  assert(output.view.process_phase == MachineState::IDLE && onlyCooling(output.actuators));
  emit({"preheat_fan_first_startup_proof"}, 1, input, output, preheat);
  output = preheat.update(input, 1 + COOLING_FEEDBACK_DWELL_MS);
  assert(output.view.process_phase == MachineState::PREHEATING);
  assert(output.view.cooling_startup_request == CoolingStartupRequest::NONE);
  emit({"preheat_fan_first_startup_proof"}, 1 + COOLING_FEEDBACK_DWELL_MS,
       input, output, preheat);

  input = safeInput();
  input.cooling_feedback_valid = false;
  MachineSupervisor purge;
  configure(purge);
  assert(purge.selectMaterial(MaterialProfile::PLA));
  assert(purge.requestMaterialChange(MaterialProfile::PET, input));
  assert(purge.requestPurgePreheat(input));
  output = purge.update(input, 0);
  assert(output.view.process_phase == MachineState::IDLE);
  assert(output.view.cooling_startup_request == CoolingStartupRequest::PURGE_PREHEAT);
  assert(onlyCooling(output.actuators));
  emit({"purge_fan_first_startup_proof"}, 0, input, output, purge);
  input.cooling_feedback_valid = true;
  output = purge.update(input, 1);
  assert(output.view.process_phase == MachineState::IDLE && onlyCooling(output.actuators));
  emit({"purge_fan_first_startup_proof"}, 1, input, output, purge);
  output = purge.update(input, 1 + COOLING_FEEDBACK_DWELL_MS);
  assert(output.view.process_phase == MachineState::MAINTENANCE_PURGE);
  assert(output.view.cooling_startup_request == CoolingStartupRequest::NONE);
  emit({"purge_fan_first_startup_proof"}, 1 + COOLING_FEEDBACK_DWELL_MS,
       input, output, purge);

  input = safeInput();
  input.cooling_feedback_valid = false;
  MachineSupervisor absent;
  configure(absent);
  assert(absent.selectMaterial(MaterialProfile::PLA));
  assert(absent.requestPreheat(input));
  output = absent.update(input, 0);
  assert(onlyCooling(output.actuators));
  emit({"startup_probe_feedback_absent_containment"}, 0, input, output, absent);
  output = absent.update(input, COOLING_FEEDBACK_DWELL_MS * 2UL);
  assert(output.view.process_phase == MachineState::FAULT && !hazardous(output.actuators));
  TraceMeta fault{"startup_probe_feedback_absent_containment"};
  fault.fault_reason = "COOLING_FAILURE";
  fault.explicit_restart_issued = false;
  emit(fault, COOLING_FEEDBACK_DWELL_MS * 2UL, input, output, absent);

  // Fan-off feedback is expected to remain invalid during a physical lockout clear.
  assert(absent.clearAllFaults(input, true));
  output = absent.update(input, COOLING_FEEDBACK_DWELL_MS * 2UL + 1);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  emit({"cooling_fault_clear_then_reprobe", "NONE", false, false},
       COOLING_FEEDBACK_DWELL_MS * 2UL + 1, input, output, absent);
  assert(absent.requestPreheat(input));
  output = absent.update(input, COOLING_FEEDBACK_DWELL_MS * 2UL + 2);
  assert(output.view.process_phase == MachineState::IDLE && onlyCooling(output.actuators));
  assert(output.view.cooling_startup_request == CoolingStartupRequest::PREHEAT);
  emit({"cooling_fault_clear_then_reprobe", "NONE", false, true},
       COOLING_FEEDBACK_DWELL_MS * 2UL + 2, input, output, absent);
}

void coldBootAndCalibration() {
  MachineSupervisor supervisor;
  auto input = safeInput();
  auto output = supervisor.update(input, 0);
  assert(output.view.process_phase == MachineState::IDLE);
  assert(!output.view.calibration.drive_calibration_valid);
  assert(!output.view.calibration.gauge_calibration_valid);
  emit({"cold_boot_no_calibration"}, 0, input, output, supervisor);

  configure(supervisor, false);
  output = supervisor.update(input, 1);
  assert(output.view.calibration.drive_calibration_valid);
  assert(output.view.calibration.current_sensor_calibration_valid);
  assert(!output.view.calibration.gauge_calibration_valid);
  emit({"separate_calibration_loading"}, 1, input, output, supervisor);
  assert(supervisor.configureGaugeCalibration({100, 0.002f, 100, 0.002f, 0.02f, true}));
  output = supervisor.update(input, 2);
  assert(output.view.calibration.gauge_calibration_valid);
  emit({"separate_calibration_loading"}, 2, input, output, supervisor);
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  output = supervisor.update(input, 3);
  assert(output.view.material_session == MaterialSession::PLA_ACTIVE);
  emit({"explicit_material_selection"}, 3, input, output, supervisor);
}

void calibrationReadinessPhaseGates() {
  auto input = safeInput();
  DriveCalibration drive = REFERENCE_DRIVE_CALIBRATION;
  drive.verified = true;

  MachineSupervisor missing_drive;
  assert(missing_drive.configureCurrentSensorCalibration(512.0f, 0.01f));
  assert(missing_drive.selectMaterial(MaterialProfile::PLA));
  assert(!missing_drive.requestShredding(input, 0));
  auto output = missing_drive.update(input, 0);
  emit({"calibration_readiness_phase_gates", "SHREDDING_MISSING_DRIVE_REJECTED"}, 0, input, output, missing_drive);

  MachineSupervisor missing_current;
  assert(missing_current.configureDriveCalibration(drive));
  assert(missing_current.selectMaterial(MaterialProfile::PLA));
  assert(!missing_current.requestShredding(input, 1));
  output = missing_current.update(input, 1);
  emit({"calibration_readiness_phase_gates", "SHREDDING_MISSING_CURRENT_REJECTED"}, 1, input, output, missing_current);

  MachineSupervisor missing_gauge;
  assert(missing_gauge.configureCoolingFeedbackCalibration(100.0f, 0.01f));
  assert(missing_gauge.selectMaterial(MaterialProfile::PLA));
  assert(!missing_gauge.requestPreheat(input));
  output = missing_gauge.update(input, 2);
  emit({"calibration_readiness_phase_gates", "PREHEATING_MISSING_GAUGE_REJECTED"}, 2, input, output, missing_gauge);

  MachineSupervisor missing_temperature;
  configure(missing_temperature);
  assert(missing_temperature.selectMaterial(MaterialProfile::PLA));
  input.temperatures[0].valid = false;
  assert(!missing_temperature.requestPreheat(input));
  output = missing_temperature.update(input, 3);
  emit({"calibration_readiness_phase_gates", "PREHEATING_MISSING_TEMPERATURE_REJECTED"}, 3, input, output, missing_temperature);

  input = safeInput();
  MachineSupervisor missing_purge_cooling;
  assert(missing_purge_cooling.selectMaterial(MaterialProfile::PLA));
  assert(missing_purge_cooling.requestMaterialChange(MaterialProfile::PET, input));
  assert(!missing_purge_cooling.requestPurgePreheat(input));
  output = missing_purge_cooling.update(input, 4);
  emit({"calibration_readiness_phase_gates", "PURGE_MISSING_COOLING_REJECTED"}, 4, input, output, missing_purge_cooling);

  MachineSupervisor missing_extrusion_cooling;
  configure(missing_extrusion_cooling);
  assert(missing_extrusion_cooling.selectMaterial(MaterialProfile::PLA));
  assert(missing_extrusion_cooling.requestPreheat(input));
  uint32_t now = 5;
  output = completeCoolingStartup(missing_extrusion_cooling, input, now);
  assert(output.view.process_phase == MachineState::PREHEATING);
  input.cooling_feedback_valid = false;
  assert(!missing_extrusion_cooling.armExtrusion(input, ++now));
  emit({"calibration_readiness_phase_gates", "EXTRUSION_REQUAL_INVALID_COOLING_REJECTED"}, now, input, output, missing_extrusion_cooling);
}

void phaseSpecificReadinessUi() {
  auto input = safeInput();
  MachineSupervisor supervisor;
  assert(supervisor.configureCoolingFeedbackCalibration(100.0f, 0.01f));
  assert(supervisor.configureGaugeCalibration({100, 0.002f, 100, 0.002f, 0.02f, true}));
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  assert(!supervisor.requestShredding(input, 0));
  assert(supervisor.requestPreheat(input));
  uint32_t now = 1;
  auto output = supervisor.update(input, now);
  assert(output.view.ui_state == SupervisorUiState::COOLING_STARTUP_PROBE);
  emit({"phase_specific_readiness_ui"}, now, input, output, supervisor);
  output = supervisor.update(input, ++now);
  now += COOLING_FEEDBACK_DWELL_MS;
  output = supervisor.update(input, now);
  assert(output.view.process_phase == MachineState::PREHEATING);
  assert(output.view.ui_state == SupervisorUiState::READY_TO_EXTRUDE);
  emit({"phase_specific_readiness_ui"}, now, input, output, supervisor);
}

void shredderTransactions() {
  auto input = safeInput();
  MachineSupervisor rejected;
  assert(rejected.selectMaterial(MaterialProfile::PLA));
  assert(!rejected.requestShredding(input, 0));
  auto output = rejected.update(input, 0);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  emit({"rejected_shredder_start_rollback"}, 0, input, output, rejected);

  MachineSupervisor supervisor;
  configure(supervisor);
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  assert(supervisor.requestShredding(input, 0));
  output = supervisor.update(input, 1);
  assert(output.view.process_phase == MachineState::SHREDDING);
  assert(output.actuators.shredder_pwm != 0);
  emit({"successful_shredder_start"}, 1, input, output, supervisor);

  input.shredder_current_amp = 12.0f;
  input.shredder_rpm = 0.0f;
  uint32_t now = JAM_STARTUP_GRACE_MS;
  for (unsigned retry = 0; retry < 3; ++retry) {
    output = supervisor.update(input, now);
    now += PLA_PROFILE.overload_ms;
    output = supervisor.update(input, now);
    now += JAM_STOP_MS;
    output = supervisor.update(input, now);
    now += PLA_PROFILE.reverse_ms;
    output = supervisor.update(input, now);
    if (retry != 2) now += JAM_STARTUP_GRACE_MS;
  }
  assert(output.view.process_phase == MachineState::FAULT);
  TraceMeta latched{"shredder_jam_three_retries_atomic_clear"};
  latched.fault_reason = "SHREDDER_JAM";
  emit(latched, now, input, output, supervisor);
  input.temperatures[0] = {-273.0f, false, true, now + 1};
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::FAULT && output.view.shredder_fault_latched &&
         output.view.heater_faults != HEATER_FAULT_NONE);
  latched.fault_reason = "SHREDDER_JAM_AND_HEATER_SENSOR_OPEN";
  emit(latched, now, input, output, supervisor);
  const uint16_t heater_faults_before = output.view.heater_faults;
  assert(!supervisor.clearAllFaults(input, true));
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::FAULT && output.view.shredder_fault_latched &&
         output.view.heater_faults == heater_faults_before);
  emit(latched, now, input, output, supervisor);
  input.temperatures[0] = {200.0f, true, false, now + 1};
  input.shredder_current_amp = 0.0f;
  input.shredder_rpm = 0.0f;
  assert(supervisor.clearAllFaults(input, true));
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  TraceMeta meta{"shredder_jam_three_retries_atomic_clear"};
  meta.explicit_restart_issued = false;
  emit(meta, now, input, output, supervisor);
}

MachineSupervisor qualifiedExtruder(InputSnapshot &input, uint32_t &now) {
  MachineSupervisor supervisor;
  configure(supervisor);
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  assert(supervisor.requestPreheat(input));
  auto output = completeCoolingStartup(supervisor, input, now);
  assert(output.view.process_phase == MachineState::PREHEATING);
  assert(output.view.extrusion_arm_required);
  assert(output.actuators.screw_pwm == 0);
  emit({"preheat_waits_explicit_arm"}, now, input, output, supervisor);
  assert(supervisor.armExtrusion(input, ++now));
  output = supervisor.update(input, now);
  assert(output.view.forming_chain_state == FormingChainState::REQUALIFYING);
  assert(!output.view.spool_eligible);
  for (unsigned sample = 1; sample <= 20; ++sample) {
    now += 200;
    output = supervisor.update(input, now);
  }
  now += REQUALIFICATION_TRANSPORT_PLA_MS;
  output = supervisor.update(input, now);
  assert(output.view.forming_chain_state == FormingChainState::READY_TO_RETHREAD);
  assert(!output.view.spool_eligible);
  TraceMeta ready{"gauge_requalification_manual_rethread"};
  emit(ready, now, input, output, supervisor);
  assert(supervisor.confirmManualRethread(input));
  output = supervisor.update(input, ++now);
  assert(output.view.spool_eligible && output.actuators.spooler_pwm != 0);
  TraceMeta meta{"normal_pla_extrusion"};
  emit(meta, now, input, output, supervisor);
  emit(ready, now, input, output, supervisor);
  return supervisor;
}

void heaterFaultAndAtomicClear() {
  MachineSupervisor supervisor;
  configure(supervisor);
  auto input = safeInput();
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  assert(supervisor.requestPreheat(input));
  uint32_t now = 0;
  auto output = completeCoolingStartup(supervisor, input, now);
  assert(output.view.process_phase == MachineState::PREHEATING);
  input.temperatures[0].sensor_open = true;
  input.temperatures[0].valid = false;
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::FAULT);
  assert(output.actuators.cooling_pwm != 0);
  TraceMeta fault{"heater_sensor_fault_atomic_clear"};
  fault.fault_reason = "HEATER_SENSOR_OPEN";
  emit(fault, now, input, output, supervisor);
  TraceMeta general_fault{"general_fault_valid_cooling"};
  general_fault.fault_reason = "HEATER_SENSOR_OPEN";
  emit(general_fault, now, input, output, supervisor);
  assert(!supervisor.clearAllFaults(input, true));
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::FAULT && output.view.heater_faults != HEATER_FAULT_NONE);
  emit(fault, now, input, output, supervisor);
  input.temperatures[0] = {200.0f, true, false, now + 1};
  assert(supervisor.clearAllFaults(input, true));
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  TraceMeta meta{"heater_sensor_fault_atomic_clear"};
  meta.explicit_restart_issued = false;
  emit(meta, now, input, output, supervisor);
}

void purgePlaToPet() {
  MachineSupervisor supervisor;
  configure(supervisor);
  auto input = safeInput();
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  assert(supervisor.requestMaterialChange(MaterialProfile::PET, input));
  assert(supervisor.process().material() == MaterialProfile::PLA);
  assert(supervisor.requestPurgePreheat(input));
  uint32_t now = 1;
  auto output = completeCoolingStartup(supervisor, input, now);
  assert(output.view.material_session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  assert(purgeMotionStopped(output.actuators));
  emit({"purge_ready_waits_ordered_confirmations"}, now, input, output, supervisor);
  assert(supervisor.approvePurgeFeed(true));
  output = supervisor.update(input, ++now);
  assert(output.view.purge_feed_approved && purgeMotionStopped(output.actuators));
  emit({"purge_ready_waits_ordered_confirmations"}, now, input, output, supervisor);
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  input.cooling_feedback_valid = false;
  assert(!supervisor.confirmPurgeWastePath(input, ++now));
  output = supervisor.update(input, now);
  assert(output.view.material_session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  assert(purgeMotionStopped(output.actuators));
  emit({"purge_ready_waits_ordered_confirmations", "LIVE_COOLING_PREFLIGHT_REJECTED"},
       now, input, output, supervisor);
  input.cooling_feedback_valid = true;
  assert(supervisor.confirmPurgeWastePath(input, ++now));
  output = supervisor.update(input, now);
  assert(output.view.process_phase == MachineState::MAINTENANCE_PURGE);
  assert(output.view.material_session == MaterialSession::PURGE_RUNNING);
  assert(output.actuators.screw_pwm != 0 && output.actuators.feeder_enable);
  assert(output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  TraceMeta running{"pla_to_pet_maintenance_purge"};
  emit(running, now, input, output, supervisor);
  now += 120001;
  output = supervisor.update(input, now);
  assert(supervisor.confirmPurgeComplete(true, input, now));
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::COOLDOWN);
  assert(output.view.material_session == MaterialSession::SCREEN_CLEAN_REQUIRED);
  assert(output.view.purge_run_completed && !output.view.purge_feed_approved);
  assert(onlyCooling(output.actuators));
  assert(!supervisor.acknowledgeMaterialStep(MaterialSession::SCREEN_CLEAN_REQUIRED, true));
  emit({"pla_to_pet_maintenance_purge", "HOT_PURGE_COMPLETE_COOLDOWN"}, now, input, output, supervisor);
  for (uint8_t zone = 0; zone < 4; ++zone) input.temperatures[zone].celsius = COOLDOWN_SAFE_TEMPERATURE_C;
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::SCREEN_CLEAN_REQUIRED, true));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::HOPPER_CLEAN_REQUIRED, true));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::TEMPERATURE_TRANSITION_REQUIRED, true));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::FINAL_CONFIRM_REQUIRED, true));
  output = supervisor.update(input, ++now);
  assert(output.view.material_session == MaterialSession::PET_ACTIVE);
  emit({"pla_to_pet_maintenance_purge"}, now, input, output, supervisor);

  assert(supervisor.requestMaterialChange(MaterialProfile::PLA, input));
  assert(supervisor.requestPurgePreheat(input));
  output = completeCoolingStartup(supervisor, input, ++now);
  assert(output.view.material_session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  assert(!output.view.purge_feed_approved);
  assert(!supervisor.confirmPurgeWastePath(input, ++now));
  output = supervisor.update(input, now);
  assert(output.view.material_session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  emit({"stale_purge_feed_approval_rejected", "STALE_APPROVAL_REJECTED"}, now, input, output, supervisor);
}

void purgePetToPla() {
  MachineSupervisor supervisor;
  configure(supervisor);
  auto input = safeInput();
  input.screw_rpm = 18.0f;
  input.temperatures[0].celsius = 245.0f;
  input.temperatures[1].celsius = 260.0f;
  input.temperatures[2].celsius = 270.0f;
  input.temperatures[3].celsius = 265.0f;
  input.temperatures[4].celsius = 60.0f;
  assert(supervisor.selectMaterial(MaterialProfile::PET));
  assert(supervisor.requestMaterialChange(MaterialProfile::PLA, input));
  assert(supervisor.requestPurgePreheat(input));
  uint32_t now = 1;
  auto output = completeCoolingStartup(supervisor, input, now);
  assert(output.view.material_session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED);
  assert(supervisor.approvePurgeFeed(true));
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  assert(supervisor.confirmPurgeWastePath(input, ++now));
  output = supervisor.update(input, now);
  assert(output.view.material_session == MaterialSession::PURGE_RUNNING);
  emit({"pet_to_pla_maintenance_purge"}, now, input, output, supervisor);
  now += 120001;
  output = supervisor.update(input, now);
  assert(supervisor.process().material() == MaterialProfile::PET);
  assert(supervisor.confirmPurgeComplete(true, input, now));
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::COOLDOWN);
  assert(output.view.material_session == MaterialSession::SCREEN_CLEAN_REQUIRED);
  assert(output.view.purge_run_completed && !output.view.purge_feed_approved);
  assert(onlyCooling(output.actuators));
  assert(!supervisor.acknowledgeMaterialStep(MaterialSession::SCREEN_CLEAN_REQUIRED, true));
  emit({"pet_to_pla_maintenance_purge", "HOT_PURGE_COMPLETE_COOLDOWN"}, now, input, output, supervisor);
  for (uint8_t zone = 0; zone < 4; ++zone) input.temperatures[zone].celsius = COOLDOWN_SAFE_TEMPERATURE_C;
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::SCREEN_CLEAN_REQUIRED, true));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::HOPPER_CLEAN_REQUIRED, true));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::TEMPERATURE_TRANSITION_REQUIRED, true));
  assert(supervisor.acknowledgeMaterialStep(MaterialSession::FINAL_CONFIRM_REQUIRED, true));
  output = supervisor.update(input, ++now);
  assert(supervisor.process().material() == MaterialProfile::PLA);
  emit({"pet_to_pla_maintenance_purge"}, now, input, output, supervisor);
}

void purgeScrewDriverFault() {
  MachineSupervisor supervisor;
  configure(supervisor);
  auto input = safeInput();
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  assert(supervisor.requestMaterialChange(MaterialProfile::PET, input));
  assert(supervisor.requestPurgePreheat(input));
  uint32_t now = 1;
  completeCoolingStartup(supervisor, input, now);
  assert(supervisor.approvePurgeFeed(true));
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  assert(supervisor.confirmPurgeWastePath(input, ++now));
  auto running = supervisor.update(input, ++now);
  assert(running.view.process_phase == MachineState::MAINTENANCE_PURGE);
  input.safety.driver_fault_free = false;
  auto faulted = supervisor.update(input, ++now);
  assert(faulted.view.process_phase == MachineState::FAULT);
  assert(onlyCooling(faulted.actuators));
  assert(supervisor.process().material() == MaterialProfile::PLA);
  assert(supervisor.process().pendingMaterial() == MaterialProfile::PET);
  TraceMeta meta{"purge_screw_driver_fault_containment"};
  meta.fault_reason = "PURGE_SCREW_DRIVER_FAULT";
  emit(meta, now, input, faulted, supervisor);
}

void purgeAbortEveryStage() {
  auto input = safeInput();

  MachineSupervisor probe;
  configure(probe);
  assert(probe.selectMaterial(MaterialProfile::PLA));
  assert(probe.requestMaterialChange(MaterialProfile::PET, input));
  assert(probe.requestPurgePreheat(input));
  auto output = probe.update(input, 0);
  assert(output.view.cooling_startup_request == CoolingStartupRequest::PURGE_PREHEAT);
  probe.requestStop(input);
  output = probe.update(input, 1);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  assert(output.view.material_session == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(!output.view.purge_feed_approved && !output.view.purge_run_completed);
  emit({"purge_panel_abort_all_stages", "PROBE_ABORTED"}, 1, input, output, probe);

  MachineSupervisor ready;
  configure(ready);
  assert(ready.selectMaterial(MaterialProfile::PLA));
  assert(ready.requestMaterialChange(MaterialProfile::PET, input));
  assert(ready.requestPurgePreheat(input));
  uint32_t now = 10;
  output = completeCoolingStartup(ready, input, now);
  assert(ready.approvePurgeFeed(true));
  ready.requestStop(input);
  output = ready.update(input, ++now);
  assert(output.view.process_phase == MachineState::COOLDOWN && onlyCooling(output.actuators));
  assert(output.view.material_session == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(!output.view.purge_feed_approved && !output.view.purge_run_completed);
  emit({"purge_panel_abort_all_stages", "READY_ABORTED"}, now, input, output, ready);
  for (uint8_t zone = 0; zone < 4; ++zone) input.temperatures[zone].celsius = COOLDOWN_SAFE_TEMPERATURE_C;
  output = ready.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  emit({"purge_panel_abort_all_stages", "READY_ABORT_COOLED_IDLE"}, now, input, output, ready);

  input = safeInput();
  MachineSupervisor running;
  configure(running);
  assert(running.selectMaterial(MaterialProfile::PLA));
  assert(running.requestMaterialChange(MaterialProfile::PET, input));
  assert(running.requestPurgePreheat(input));
  now = 20;
  completeCoolingStartup(running, input, now);
  assert(running.approvePurgeFeed(true));
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  assert(running.confirmPurgeWastePath(input, ++now));
  output = running.update(input, ++now);
  assert(output.view.material_session == MaterialSession::PURGE_RUNNING);
  running.requestStop(input);
  output = running.update(input, ++now);
  assert(output.view.process_phase == MachineState::COOLDOWN && onlyCooling(output.actuators));
  assert(output.view.material_session == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(!output.view.purge_feed_approved && !output.view.purge_run_completed);
  emit({"purge_panel_abort_all_stages", "RUNNING_ABORTED"}, now, input, output, running);
  for (uint8_t zone = 0; zone < 4; ++zone) input.temperatures[zone].celsius = COOLDOWN_SAFE_TEMPERATURE_C;
  output = running.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  emit({"purge_panel_abort_all_stages", "RUNNING_ABORT_COOLED_IDLE"}, now, input, output, running);
}

void preparePurgeForCompletion(MachineSupervisor &supervisor, InputSnapshot &input, uint32_t &now) {
  configure(supervisor);
  assert(supervisor.selectMaterial(MaterialProfile::PLA));
  assert(supervisor.requestMaterialChange(MaterialProfile::PET, input));
  assert(supervisor.requestPurgePreheat(input));
  completeCoolingStartup(supervisor, input, now);
  assert(supervisor.approvePurgeFeed(true));
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  assert(supervisor.confirmPurgeWastePath(input, ++now));
  supervisor.update(input, ++now);
  now += 120001;
  supervisor.update(input, now);
}

void purgeCompletionFreshFaultPreflight() {
  for (unsigned fault = 0; fault < 4; ++fault) {
    auto input = safeInput();
    MachineSupervisor supervisor;
    uint32_t now = 1;
    preparePurgeForCompletion(supervisor, input, now);
    const char *reason = "UNKNOWN";
    if (fault == 0) {
      input.safety.lid_closed = false;
      reason = "FRESH_LID_OPEN_REJECTED";
    } else if (fault == 1) {
      input.safety.estop_ok = false;
      reason = "FRESH_ESTOP_REJECTED";
    } else if (fault == 2) {
      input.safety.thermal_chain_ok = false;
      reason = "FRESH_THERMAL_CHAIN_REJECTED";
    } else {
      input.cooling_feedback_valid = false;
      reason = "FRESH_COOLING_INVALID_REJECTED";
    }
    assert(!supervisor.confirmPurgeComplete(true, input, ++now));
    assert(supervisor.process().material() == MaterialProfile::PLA);
    assert(supervisor.process().pendingMaterial() == MaterialProfile::PET);
    assert(supervisor.process().materialSession() == MaterialSession::PURGE_RUNNING);
    auto output = supervisor.update(input, now);
    assert(!output.view.purge_run_completed);
    assert(output.view.material_session != MaterialSession::PET_ACTIVE);
    assert(output.actuators.screw_pwm == 0 && !output.actuators.feeder_enable &&
           output.actuators.puller_pwm == 0 && output.actuators.spooler_pwm == 0 &&
           !output.actuators.traverse_enable && !anyHeater(output.actuators));
    emit({"purge_completion_fresh_fault_preflight", reason}, now, input, output, supervisor);
  }
}

void coolingLossContainment() {
  auto input = safeInput();
  MachineSupervisor preheat;
  configure(preheat);
  assert(preheat.selectMaterial(MaterialProfile::PLA));
  assert(preheat.requestPreheat(input));
  uint32_t now = 1;
  completeCoolingStartup(preheat, input, now);
  input.cooling_feedback_valid = false;
  preheat.update(input, ++now);
  now += COOLING_FEEDBACK_DWELL_MS;
  auto output = preheat.update(input, now);
  assert(output.view.process_phase == MachineState::FAULT && !hazardous(output.actuators));
  TraceMeta preheat_meta{"preheat_cooling_loss_containment"};
  preheat_meta.fault_reason = "COOLING_FAILURE";
  emit(preheat_meta, now, input, output, preheat);
  assert(preheat.clearAllFaults(input, true));
  output = preheat.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  preheat_meta.explicit_restart_issued = false;
  emit(preheat_meta, now, input, output, preheat);

  input = safeInput();
  MachineSupervisor purge;
  configure(purge);
  assert(purge.selectMaterial(MaterialProfile::PLA));
  assert(purge.requestMaterialChange(MaterialProfile::PET, input));
  assert(purge.requestPurgePreheat(input));
  now = 1;
  completeCoolingStartup(purge, input, now);
  assert(purge.approvePurgeFeed(true));
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  assert(purge.confirmPurgeWastePath(input, ++now));
  purge.update(input, ++now);
  input.cooling_feedback_valid = false;
  purge.update(input, ++now);
  now += COOLING_FEEDBACK_DWELL_MS;
  output = purge.update(input, now);
  assert(output.view.process_phase == MachineState::FAULT && !hazardous(output.actuators));
  assert(!output.view.purge_run_completed);
  assert(purge.process().material() == MaterialProfile::PLA);
  assert(purge.process().pendingMaterial() == MaterialProfile::PET);
  TraceMeta purge_meta{"purge_cooling_loss_containment"};
  purge_meta.fault_reason = "COOLING_FAILURE";
  emit(purge_meta, now, input, output, purge);
  assert(purge.clearAllFaults(input, true));
  output = purge.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE);
  assert(output.view.material_session == MaterialSession::PURGE_PREHEAT_REQUIRED);
  assert(purge.process().material() == MaterialProfile::PLA);
  assert(purge.process().pendingMaterial() == MaterialProfile::PET);
  assert(!output.view.purge_run_completed && !hazardous(output.actuators));
  purge_meta.explicit_restart_issued = false;
  emit(purge_meta, now, input, output, purge);
  assert(purge.requestPurgePreheat(input));
  output = purge.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && onlyCooling(output.actuators));
  emit({"purge_cooling_fault_clear_then_reprobe"}, now, input, output, purge);

  input = safeInput();
  MachineSupervisor cooldown;
  configure(cooldown);
  assert(cooldown.selectMaterial(MaterialProfile::PLA));
  assert(cooldown.requestPreheat(input));
  now = 1;
  completeCoolingStartup(cooldown, input, now);
  cooldown.requestStop(input);
  output = cooldown.update(input, ++now);
  assert(output.view.process_phase == MachineState::COOLDOWN);
  input.cooling_feedback_valid = false;
  cooldown.update(input, ++now);
  now += COOLING_FEEDBACK_DWELL_MS;
  output = cooldown.update(input, now);
  assert(output.view.process_phase == MachineState::FAULT && !hazardous(output.actuators));
  TraceMeta cooldown_meta{"cooldown_cooling_loss_containment"};
  cooldown_meta.fault_reason = "COOLING_FAILURE";
  emit(cooldown_meta, now, input, output, cooldown);
  assert(cooldown.clearAllFaults(input, true));
  output = cooldown.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  cooldown_meta.explicit_restart_issued = false;
  emit(cooldown_meta, now, input, output, cooldown);
  assert(cooldown.requestPreheat(input));
  output = cooldown.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && onlyCooling(output.actuators));
  emit({"cooldown_cooling_fault_clear_then_reprobe"}, now, input, output, cooldown);

  input = safeInput();
  MachineSupervisor completed_cooldown;
  configure(completed_cooldown);
  assert(completed_cooldown.selectMaterial(MaterialProfile::PLA));
  assert(completed_cooldown.requestPreheat(input));
  now = 1;
  completeCoolingStartup(completed_cooldown, input, now);
  completed_cooldown.requestStop(input);
  output = completed_cooldown.update(input, ++now);
  assert(output.view.process_phase == MachineState::COOLDOWN && output.actuators.cooling_pwm != 0);
  emit({"cooldown_to_idle_completion", "COOLDOWN_ABOVE_THRESHOLD"}, now, input, output, completed_cooldown);
  for (uint8_t zone = 0; zone < 4; ++zone) input.temperatures[zone].celsius = COOLDOWN_SAFE_TEMPERATURE_C;
  assert(completed_cooldown.canCompleteCooldown(input));
  output = completed_cooldown.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  emit({"cooldown_to_idle_completion", "COOLDOWN_AUTO_IDLE_COMPLETE"}, now, input, output, completed_cooldown);
}

void formingFaults() {
  auto input = safeInput();
  uint32_t now = 0;
  MachineSupervisor gauge_supervisor = qualifiedExtruder(input, now);
  input.gauge_optical_valid = false;
  auto output = gauge_supervisor.update(input, ++now);
  assert(output.view.forming_chain_state == FormingChainState::RUNDOWN);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0);
  TraceMeta gauge{"gauge_loss_controlled_rundown"};
  gauge.fault_reason = "GAUGE_INVALID";
  emit(gauge, now, input, output, gauge_supervisor);

  input = safeInput();
  now = 0;
  MachineSupervisor cooling_supervisor = qualifiedExtruder(input, now);
  input.cooling_feedback_valid = false;
  cooling_supervisor.update(input, ++now);
  now += COOLING_FEEDBACK_DWELL_MS;
  output = cooling_supervisor.update(input, now);
  assert(output.view.forming_chain_state == FormingChainState::RUNDOWN);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0);
  TraceMeta cooling{"cooling_loss_controlled_rundown"};
  cooling.fault_reason = "COOLING_FAILURE";
  emit(cooling, now, input, output, cooling_supervisor);

  input = safeInput();
  now = 0;
  MachineSupervisor dancer_supervisor = qualifiedExtruder(input, now);
  input.dancer_angle_rad = DANCER_CONTROLLED_STOP_RAD;
  output = dancer_supervisor.update(input, ++now);
  assert(output.view.forming_chain_state == FormingChainState::RUNDOWN);
  assert(input.dancer_angle_rad < DANCER_MECHANICAL_HARD_STOP_RAD);
  assert(output.actuators.spooler_pwm == 0);
  TraceMeta dancer{"spool_jam_before_hard_stop"};
  dancer.fault_reason = "DANCER_CONTROLLED_STOP";
  dancer.nominal_spool_jam = true;
  emit(dancer, now, input, output, dancer_supervisor);
}

void pullerTachStartupGrace() {
  auto input = safeInput();
  input.puller_tach_ok = false;
  MachineSupervisor absent;
  configure(absent);
  assert(absent.selectMaterial(MaterialProfile::PLA));
  assert(absent.requestPreheat(input));
  uint32_t now = 0;
  completeCoolingStartup(absent, input, now);
  assert(absent.armExtrusion(input, ++now));
  auto output = absent.update(input, now);
  assert(output.view.process_phase == MachineState::REQUALIFYING);
  now += PULLER_TACH_STARTUP_GRACE_MS - 1;
  output = absent.update(input, now);
  assert(output.view.forming_chain_state == FormingChainState::REQUALIFYING);
  emit({"puller_tach_startup_grace_and_loss", "PRE_GRACE_ZERO_RPM_ACCEPTED"}, now, input, output, absent);
  output = absent.update(input, ++now);
  assert(output.view.forming_chain_state == FormingChainState::RUNDOWN);
  TraceMeta timeout{"puller_tach_startup_grace_and_loss"};
  timeout.fault_reason = "PULLER_TACH_FAILURE_AFTER_GRACE";
  emit(timeout, now, input, output, absent);

  input = safeInput();
  input.puller_tach_ok = false;
  MachineSupervisor qualified;
  configure(qualified);
  assert(qualified.selectMaterial(MaterialProfile::PLA));
  assert(qualified.requestPreheat(input));
  now = 0;
  completeCoolingStartup(qualified, input, now);
  assert(qualified.armExtrusion(input, ++now));
  output = qualified.update(input, now);
  now += PULLER_TACH_STARTUP_GRACE_MS / 2;
  input.puller_tach_ok = true;
  output = qualified.update(input, now);
  assert(output.view.forming_chain_state == FormingChainState::REQUALIFYING);
  emit({"puller_tach_startup_grace_and_loss", "NORMAL_PULSE_QUALIFIED"}, now, input, output, qualified);
  input.puller_tach_ok = false;
  output = qualified.update(input, ++now);
  assert(output.view.forming_chain_state == FormingChainState::RUNDOWN);
  TraceMeta loss{"puller_tach_startup_grace_and_loss"};
  loss.fault_reason = "PULLER_TACH_FAILURE_AFTER_QUALIFICATION";
  emit(loss, now, input, output, qualified);
}

void productionQualityInterlocks() {
  auto input = safeInput();
  uint32_t now = 0;
  MachineSupervisor diameter = qualifiedExtruder(input, now);
  input.gauge_x_adc = 1010;
  input.gauge_y_adc = 1010;
  auto output = diameter.update(input, ++now);
  assert(output.view.process_phase == MachineState::REQUALIFYING);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  emit({"extrusion_quality_same_cycle_interlocks", "DIAMETER_OUT_OF_TOLERANCE"}, now, input, output, diameter);
  input = safeInput(now + 1);
  output = diameter.update(input, ++now);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  emit({"extrusion_quality_same_cycle_interlocks", "DIAMETER_ONE_SAMPLE_RECOVERY_BLOCKED"}, now, input, output, diameter);

  input = safeInput();
  now = 0;
  MachineSupervisor ovality = qualifiedExtruder(input, now);
  input.gauge_x_adc = 1000;
  input.gauge_y_adc = 950;
  output = ovality.update(input, ++now);
  assert(output.view.process_phase == MachineState::REQUALIFYING);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  emit({"extrusion_quality_same_cycle_interlocks", "OVALITY_OUT_OF_TOLERANCE"}, now, input, output, ovality);
  input = safeInput(now + 1);
  output = ovality.update(input, ++now);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  emit({"extrusion_quality_same_cycle_interlocks", "OVALITY_ONE_SAMPLE_RECOVERY_BLOCKED"}, now, input, output, ovality);

  input = safeInput();
  now = 0;
  MachineSupervisor saturated = qualifiedExtruder(input, now);
  input.puller_saturated = true;
  output = saturated.update(input, ++now);
  assert(output.view.process_phase == MachineState::REQUALIFYING);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  emit({"extrusion_quality_same_cycle_interlocks", "PULLER_SATURATED"}, now, input, output, saturated);
  input.puller_saturated = false;
  output = saturated.update(input, ++now);
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  emit({"extrusion_quality_same_cycle_interlocks", "PULLER_ONE_SAMPLE_RECOVERY_BLOCKED"}, now, input, output, saturated);

  input = safeInput();
  MachineSupervisor requal;
  configure(requal);
  assert(requal.selectMaterial(MaterialProfile::PLA));
  assert(requal.requestPreheat(input));
  now = 0;
  completeCoolingStartup(requal, input, now);
  assert(requal.armExtrusion(input, ++now));
  for (unsigned sample = 0; sample < 5; ++sample) {
    now += 200;
    output = requal.update(input, now);
  }
  assert(output.view.requalification_valid_samples > 0);
  input.gauge_x_adc = 1010;
  input.gauge_y_adc = 1010;
  output = requal.update(input, now + 200);
  assert(output.view.requalification_valid_samples == 0);
  assert(output.view.waste_mode && !output.view.spool_eligible);
  emit({"requalification_invalid_quality_resets_counter"}, now + 200, input, output, requal);

  input = safeInput();
  MachineSupervisor rethread;
  configure(rethread);
  assert(rethread.selectMaterial(MaterialProfile::PLA));
  assert(rethread.requestPreheat(input));
  now = 0;
  completeCoolingStartup(rethread, input, now);
  assert(rethread.armExtrusion(input, ++now));
  for (unsigned sample = 0; sample < 20; ++sample) {
    now += 200;
    output = rethread.update(input, now);
  }
  now += REQUALIFICATION_TRANSPORT_PLA_MS;
  output = rethread.update(input, now);
  assert(output.view.forming_chain_state == FormingChainState::READY_TO_RETHREAD);
  input.gauge_x_adc = 1010;
  input.gauge_y_adc = 1010;
  output = rethread.update(input, ++now);
  assert(!rethread.confirmManualRethread(input));
  assert(!output.view.spool_eligible && output.actuators.spooler_pwm == 0 && !output.actuators.traverse_enable);
  emit({"manual_rethread_fresh_invalid_rejected"}, now, input, output, rethread);
}

void estopScenario(const char *scenario, MachineSupervisor &supervisor,
                   InputSnapshot input, uint32_t now) {
  input.safety.estop_ok = false;
  auto output = supervisor.update(input, now);
  assert(output.view.process_phase == MachineState::ESTOP);
  assert(!hazardous(output.actuators));
  TraceMeta meta{scenario};
  meta.explicit_restart_issued = false;
  emit(meta, now, input, output, supervisor);
}

void estopEveryPhase() {
  auto input = safeInput();
  MachineSupervisor shredding;
  configure(shredding);
  assert(shredding.selectMaterial(MaterialProfile::PLA));
  assert(shredding.requestShredding(input, 0));
  estopScenario("estop_during_shredding", shredding, input, 1);

  MachineSupervisor preheat;
  configure(preheat);
  assert(preheat.selectMaterial(MaterialProfile::PLA));
  assert(preheat.requestPreheat(input));
  uint32_t now = 0;
  completeCoolingStartup(preheat, input, now);
  estopScenario("estop_during_preheating", preheat, input, ++now);

  MachineSupervisor purge;
  configure(purge);
  assert(purge.selectMaterial(MaterialProfile::PLA));
  assert(purge.requestMaterialChange(MaterialProfile::PET, input));
  assert(purge.requestPurgePreheat(input));
  now = 1;
  completeCoolingStartup(purge, input, now);
  assert(purge.approvePurgeFeed(true));
  input.purge_feed_approved = true;
  input.purge_waste_path_confirmed = true;
  assert(purge.confirmPurgeWastePath(input, ++now));
  estopScenario("estop_during_purge", purge, input, ++now);

  now = 0;
  MachineSupervisor extrusion = qualifiedExtruder(input, now);
  estopScenario("estop_during_extrusion", extrusion, input, ++now);

  MachineSupervisor cooldown;
  configure(cooldown);
  assert(cooldown.selectMaterial(MaterialProfile::PLA));
  assert(cooldown.requestPreheat(input));
  now = 0;
  completeCoolingStartup(cooldown, input, now);
  cooldown.requestStop(input);
  estopScenario("estop_during_cooldown", cooldown, input, ++now);
}

void estopClearNoImplicitRestart() {
  auto input = safeInput();
  uint32_t now = 0;
  MachineSupervisor supervisor = qualifiedExtruder(input, now);
  input.safety.estop_ok = false;
  auto output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::ESTOP && !hazardous(output.actuators));
  TraceMeta meta{"estop_clear_no_implicit_restart"};
  meta.explicit_restart_issued = false;
  emit(meta, now, input, output, supervisor);
  input.safety.estop_ok = true;
  assert(supervisor.clearAllFaults(input, true));
  output = supervisor.update(input, ++now);
  assert(output.view.process_phase == MachineState::IDLE && !hazardous(output.actuators));
  emit(meta, now, input, output, supervisor);
}

uint32_t xorshift32(uint32_t &state) {
  state ^= state << 13;
  state ^= state >> 17;
  state ^= state << 5;
  return state;
}

void boundedSequences() {
  constexpr uint32_t seeds[] = {0x13579bdfU, 0x2468ace1U, 0xc001d00dU, 0x5afe0ff1U};
  for (uint32_t seed : seeds) {
    MachineSupervisor supervisor;
    configure(supervisor);
    auto input = safeInput();
    assert(supervisor.selectMaterial(MaterialProfile::PLA));
    assert(supervisor.requestPreheat(input));
    uint32_t now = 0;
    completeCoolingStartup(supervisor, input, now);
    assert(supervisor.armExtrusion(input, ++now));
    uint32_t random = seed;
    for (uint32_t step = 1; step <= 64; ++step) {
      const uint32_t event = xorshift32(random) % 16;
      input.gauge_optical_valid = event != 0;
      input.cooling_feedback_valid = event != 1;
      input.dancer_angle_rad = event == 2 ? DANCER_CONTROLLED_STOP_RAD : 0.1f;
      input.puller_driver_ok = event != 3;
      input.spooler_driver_ok = event != 4;
      input.safety.estop_ok = event != 5;
      const auto output = supervisor.update(input, now + step * 250U);
      assertOutputInvariant(output);
      if (!input.safety.estop_ok || output.view.process_phase == MachineState::FAULT ||
          output.view.process_phase == MachineState::ESTOP) break;
    }
  }
  std::cout << "BOUNDED_SEQUENCE_OK|4|64\n";
}

}  // namespace

int main() {
  coldBootAndCalibration();
  calibrationReadinessPhaseGates();
  phaseSpecificReadinessUi();
  coolingStartupProbe();
  shredderTransactions();
  heaterFaultAndAtomicClear();
  purgePlaToPet();
  purgePetToPla();
  purgeScrewDriverFault();
  purgeAbortEveryStage();
  purgeCompletionFreshFaultPreflight();
  coolingLossContainment();
  formingFaults();
  pullerTachStartupGrace();
  productionQualityInterlocks();
  estopEveryPhase();
  estopClearNoImplicitRestart();
  boundedSequences();
  return 0;
}
