#include "machine_supervisor.h"

#include <math.h>

namespace {
int16_t rpmToPwm(float rpm, float maximum_rpm) {
  if (rpm <= 0 || maximum_rpm <= 0) return 0;
  const float scaled = rpm / maximum_rpm * 255.0f;
  return static_cast<int16_t>(scaled > 255.0f ? 255.0f : scaled);
}

bool temperatureChannelsHealthy(const InputSnapshot &input) {
  for (uint8_t channel = 0; channel < 5; ++channel) {
    const TemperatureReading &reading = input.temperatures[channel];
    if (!reading.valid || reading.sensor_open || reading.celsius < HEATER_MIN_VALID_C ||
        reading.celsius > HEATER_MAX_VALID_C) return false;
  }
  return true;
}

bool gaugeWithinProductionTolerance(const GaugeReading &gauge) {
  return gauge.valid && gauge.u95_mm <= REQUALIFICATION_U95_MAX_MM &&
      fabsf(gauge.mean_mm - 1.75f) <= REQUALIFICATION_DIAMETER_ERROR_MAX_MM &&
      gauge.ovality_mm <= REQUALIFICATION_OVALITY_MAX_MM;
}
}

bool MachineSupervisor::configureDriveCalibration(const DriveCalibration &c) {
  calibration_.drive_calibration_valid = shredder_.configureDrive(c);
  return calibration_.drive_calibration_valid;
}

bool MachineSupervisor::configureGaugeCalibration(const GaugeCalibration &c) {
  calibration_.gauge_calibration_valid = gauge_.setCalibration(c);
  return calibration_.gauge_calibration_valid;
}

bool MachineSupervisor::configureCurrentSensorCalibration(float zero_adc, float amps_per_count) {
  calibration_.current_sensor_calibration_valid = zero_adc >= 0 && zero_adc <= 1023 && amps_per_count > 0;
  return calibration_.current_sensor_calibration_valid;
}

bool MachineSupervisor::configureCoolingFeedbackCalibration(float zero_adc, float amps_per_count) {
  calibration_.cooling_feedback_calibration_valid = zero_adc >= 0 && zero_adc <= 1023 && amps_per_count > 0;
  return calibration_.cooling_feedback_calibration_valid;
}

bool MachineSupervisor::selectMaterial(MaterialProfile material) {
  const bool accepted = process_.selectMaterial(material);
  if (accepted) {
    resetCoolingStartupProbe();
    purge_feed_approved_ = false;
    purge_run_completed_ = false;
  }
  return accepted;
}

bool MachineSupervisor::requestMaterialChange(MaterialProfile material, const InputSnapshot &input) {
  const bool accepted = process_.requestMaterialChange(material, input.safety);
  if (accepted) {
    resetCoolingStartupProbe();
    purge_feed_approved_ = false;
    purge_run_completed_ = false;
  }
  return accepted;
}

bool MachineSupervisor::guardsOk(const InputSnapshot &i) const {
  return i.safety.estop_ok && i.safety.lid_closed && i.safety.service_guard_closed &&
         i.safety.thermal_chain_ok && i.safety.driver_fault_free;
}

void MachineSupervisor::resetCoolingStartupProbe() {
  cooling_startup_request_ = CoolingStartupRequest::NONE;
  cooling_startup_probe_started_ = false;
  cooling_startup_healthy_started_ = false;
  cooling_startup_probe_started_ms_ = 0;
  cooling_startup_healthy_since_ms_ = 0;
}

void MachineSupervisor::updateCoolingStartupProbe(const InputSnapshot &input, uint32_t now_ms) {
  if (cooling_startup_request_ == CoolingStartupRequest::NONE) return;
  if (process_.state() != MachineState::IDLE || !guardsOk(input)) {
    resetCoolingStartupProbe();
    enterLatchedFormingFault(FORMING_COOLING_FAILURE);
    return;
  }
  const bool temperature_ready = temperatureChannelsHealthy(input);
  const bool request_preconditions_hold = cooling_startup_request_ == CoolingStartupRequest::PREHEAT
      ? calibration_.gauge_calibration_valid && process_.materialReady()
      : process_.materialSession() == MaterialSession::PURGE_PREHEAT_REQUIRED &&
        process_.material() != MaterialProfile::NONE &&
        process_.pendingMaterial() != MaterialProfile::NONE;
  if (!temperature_ready || !request_preconditions_hold) {
    cooling_startup_preflight_fault_ = !temperature_ready;
    resetCoolingStartupProbe();
    process_.reportFault();
    return;
  }
  if (!cooling_startup_probe_started_) {
    // The input sampled before this update cannot prove a fan command that has not yet been issued.
    cooling_startup_probe_started_ = true;
    cooling_startup_probe_started_ms_ = now_ms;
    return;
  }
  if (input.cooling_feedback_valid) {
    if (!cooling_startup_healthy_started_) {
      cooling_startup_healthy_started_ = true;
      cooling_startup_healthy_since_ms_ = now_ms;
    }
  } else {
    cooling_startup_healthy_started_ = false;
    cooling_startup_healthy_since_ms_ = 0;
  }
  const bool proven = cooling_startup_healthy_started_ &&
      now_ms - cooling_startup_healthy_since_ms_ >= COOLING_STARTUP_HEALTHY_DWELL_MS;
  if (proven) {
    const CoolingStartupRequest request = cooling_startup_request_;
    const bool committed = request == CoolingStartupRequest::PREHEAT
        ? process_.requestState(MachineState::PREHEATING, input.safety)
        : process_.requestPurgePreheat(input.safety);
    resetCoolingStartupProbe();
    if (!committed) {
      enterLatchedFormingFault(FORMING_COOLING_FAILURE);
      return;
    }
    if (request == CoolingStartupRequest::PREHEAT) {
      extrusion_arm_required_ = true;
      extrusion_ready_ = false;
    }
    return;
  }
  if (now_ms - cooling_startup_probe_started_ms_ >= COOLING_STARTUP_PROBE_TIMEOUT_MS) {
    resetCoolingStartupProbe();
    enterLatchedFormingFault(FORMING_COOLING_FAILURE);
  }
}

bool MachineSupervisor::pullerTachFault(const InputSnapshot &input, uint32_t now_ms) {
  if (!puller_command_active_) return false;
  if (input.puller_tach_ok) {
    puller_tach_qualified_ = true;
    return false;
  }
  return puller_tach_qualified_ || now_ms - puller_command_started_ms_ >= PULLER_TACH_STARTUP_GRACE_MS;
}

void MachineSupervisor::trackPullerCommand(const ActuatorCommands &commands, uint32_t now_ms) {
  if (commands.puller_pwm == 0) {
    puller_command_active_ = false;
    puller_tach_qualified_ = false;
    puller_command_started_ms_ = 0;
    return;
  }
  if (!puller_command_active_) {
    puller_command_active_ = true;
    puller_tach_qualified_ = false;
    puller_command_started_ms_ = now_ms;
  }
}

bool MachineSupervisor::requestShredding(const InputSnapshot &input, uint32_t now_ms) {
  if (!calibration_.drive_calibration_valid || !calibration_.current_sensor_calibration_valid ||
      cooling_startup_request_ != CoolingStartupRequest::NONE || !guardsOk(input) ||
      process_.state() != MachineState::IDLE || !process_.materialReady()) return false;
  const ShredderInputs shredder_input{now_ms, input.shredder_current_amp, input.shredder_rpm,
                                      input.safety.driver_fault_free, false};
  if (!shredder_.start(profileFor(process_.material()), shredder_input)) return false;
  if (!process_.requestState(MachineState::SHREDDING, input.safety)) {
    shredder_.stop();
    return false;
  }
  return true;
}

bool MachineSupervisor::requestPreheat(const InputSnapshot &input) {
  if (!calibration_.gauge_calibration_valid || !temperatureChannelsHealthy(input) ||
      !calibration_.cooling_feedback_calibration_valid || !guardsOk(input) ||
      process_.state() != MachineState::IDLE || !process_.materialReady() ||
      cooling_startup_request_ != CoolingStartupRequest::NONE) return false;
  cooling_startup_request_ = CoolingStartupRequest::PREHEAT;
  extrusion_ready_ = false;
  spool_eligible_ = false;
  waste_mode_ = true;
  return true;
}

bool MachineSupervisor::armExtrusion(const InputSnapshot &input, uint32_t now_ms) {
  if (process_.state() != MachineState::PREHEATING || !extrusion_arm_required_ || !extrusion_ready_ ||
      !input.safety.temperatures_ready || !input.safety.gauge_valid ||
      !calibration_.gauge_calibration_valid || !calibration_.cooling_feedback_calibration_valid ||
      !input.cooling_feedback_valid || !guardsOk(input)) return false;
  if (!process_.requestState(MachineState::REQUALIFYING, input.safety)) return false;
  extrusion_arm_required_ = false;
  extrusion_ready_ = false;
  resetRequalification(now_ms);
  return true;
}

bool MachineSupervisor::requestPurgePreheat(const InputSnapshot &input) {
  if (!calibration_.cooling_feedback_calibration_valid || !temperatureChannelsHealthy(input) ||
      !guardsOk(input) || process_.state() != MachineState::IDLE ||
      process_.materialSession() != MaterialSession::PURGE_PREHEAT_REQUIRED ||
      process_.material() == MaterialProfile::NONE ||
      process_.pendingMaterial() == MaterialProfile::NONE ||
      cooling_startup_request_ != CoolingStartupRequest::NONE) return false;
  cooling_startup_request_ = CoolingStartupRequest::PURGE_PREHEAT;
  extrusion_arm_required_ = false;
  spool_eligible_ = false;
  waste_mode_ = true;
  return true;
}

bool MachineSupervisor::approvePurgeFeed(bool explicit_confirmation) {
  if (!explicit_confirmation || process_.state() != MachineState::MAINTENANCE_PURGE ||
      process_.materialSession() != MaterialSession::PURGE_READY_CONFIRM_REQUIRED) return false;
  purge_feed_approved_ = true;
  return true;
}

bool MachineSupervisor::confirmPurgeWastePath(const InputSnapshot &input, uint32_t now_ms) {
  if (!purge_feed_approved_ || !input.purge_waste_path_confirmed ||
      !calibration_.cooling_feedback_calibration_valid || !input.cooling_feedback_valid ||
      !temperatureChannelsHealthy(input) || !guardsOk(input)) return false;
  if (!process_.startPurge(true, input.safety)) return false;
  purge_started_ms_ = now_ms;
  purge_screw_revolutions_ = 0;
  purge_screw_revolutions_measured_ = input.screw_speed_is_measured;
  purge_temperature_stable_ = input.safety.temperatures_ready;
  purge_feed_approved_ = true;
  purge_run_completed_ = false;
  return true;
}

bool MachineSupervisor::confirmPurgeComplete(bool visual, const InputSnapshot &input, uint32_t now_ms) {
  const bool run_evidence = visual && now_ms - purge_started_ms_ >= PURGE_MINIMUM_MS &&
                            purge_screw_revolutions_ >= PURGE_MINIMUM_SCREW_REVOLUTIONS &&
                            purge_temperature_stable_;
  if (!run_evidence) return false;
  if (!calibration_.cooling_feedback_calibration_valid || !input.cooling_feedback_valid) {
    enterLatchedFormingFault(FORMING_COOLING_FAILURE);
    return false;
  }
  const bool fresh_safety = input.safety.temperatures_ready && temperatureChannelsHealthy(input) &&
                            guardsOk(input) && heaters_.faults() == HEATER_FAULT_NONE;
  if (!fresh_safety) return false;
  const bool completed = process_.completePurgeRun(true);
  if (completed) {
    purge_feed_approved_ = false;
    purge_run_completed_ = true;
  }
  return completed;
}

bool MachineSupervisor::acknowledgeMaterialStep(MaterialSession expected, bool confirmation) {
  return process_.acknowledgeMaterialStep(expected, confirmation);
}

bool MachineSupervisor::confirmManualRethread(const InputSnapshot &input) {
  const GaugeReading gauge = gauge_.update(input.gauge_x_adc, input.gauge_y_adc,
                                           input.gauge_optical_valid);
  if (forming_state_ != FormingChainState::READY_TO_RETHREAD || !guardsOk(input) ||
      !input.cooling_feedback_valid || !input.safety.gauge_valid || input.puller_saturated ||
      !gaugeWithinProductionTolerance(gauge)) return false;
  if (!process_.requestState(MachineState::EXTRUSION, input.safety)) return false;
  forming_fault_reasons_ = FORMING_FAULT_NONE;
  cooling_failure_pending_ = false;
  cooling_failure_actioned_ = false;
  cooling_recovery_probe_active_ = false;
  cooling_recovery_since_ms_ = 0;
  spool_eligible_ = true;
  waste_mode_ = false;
  forming_state_ = FormingChainState::NORMAL;
  return true;
}

void MachineSupervisor::requestStop(const InputSnapshot &input) {
  resetCoolingStartupProbe();
  shredder_.stop();
  spool_eligible_ = false;
  waste_mode_ = true;
  extrusion_arm_required_ = false;
  extrusion_ready_ = false;
  const MachineState state = process_.state();
  if (state == MachineState::SHREDDING) process_.requestState(MachineState::IDLE, input.safety);
  else if (state == MachineState::MAINTENANCE_PURGE) {
    process_.abortPurge();
    purge_feed_approved_ = false;
    purge_run_completed_ = false;
  }
  else if (state != MachineState::IDLE && state != MachineState::FAULT && state != MachineState::ESTOP)
    process_.requestState(MachineState::COOLDOWN, input.safety);
}

bool MachineSupervisor::canClearFaults(const InputSnapshot &input, bool lockout) const {
  const ShredderInputs si{0, input.shredder_current_amp, input.shredder_rpm,
                           input.safety.driver_fault_free, false};
  bool temperature_sensors_healthy = true;
  for (uint8_t zone = 0; zone < 4; ++zone) {
    const TemperatureReading &reading = input.temperatures[zone];
    temperature_sensors_healthy = temperature_sensors_healthy && reading.valid && !reading.sensor_open &&
                                  reading.celsius >= HEATER_MIN_VALID_C && reading.celsius < HEATER_OVERTEMPERATURE_C;
  }
  const bool non_cooling_forming_inputs_healthy = input.safety.gauge_valid &&
                                 calibration_.gauge_calibration_valid &&
                                 input.puller_driver_ok &&
                                 input.puller_tach_ok && input.spooler_driver_ok &&
                                 fabsf(input.dancer_angle_rad) < DANCER_CONTROLLED_STOP_RAD;
  const uint16_t non_cooling_reasons = forming_fault_reasons_ & ~FORMING_COOLING_FAILURE;
  const bool cooling_reason_clearable = (forming_fault_reasons_ & FORMING_COOLING_FAILURE) == 0 ||
      calibration_.cooling_feedback_calibration_valid;
  const bool forming_can_clear = (non_cooling_reasons == FORMING_FAULT_NONE ||
                                  non_cooling_forming_inputs_healthy) && cooling_reason_clearable;
  const bool heater_can_clear = heaters_.faults() == HEATER_FAULT_NONE || temperature_sensors_healthy;
  const bool startup_preflight_can_clear = !cooling_startup_preflight_fault_ ||
      temperatureChannelsHealthy(input);
  return process_.canClearFault(input.safety, lockout) &&
         heaters_.canClearFault(lockout, input.safety.thermal_chain_ok, heater_can_clear) &&
         shredder_.canClearFault(lockout, si) && forming_can_clear && startup_preflight_can_clear;
}

bool MachineSupervisor::canCompleteCooldown(const InputSnapshot &input) const {
  if (process_.state() != MachineState::COOLDOWN || !input.cooling_feedback_valid ||
      !calibration_.cooling_feedback_calibration_valid) return false;
  for (uint8_t channel = 0; channel < 4; ++channel) {
    const TemperatureReading &reading = input.temperatures[channel];
    if (!reading.valid || reading.sensor_open || reading.celsius > COOLDOWN_SAFE_TEMPERATURE_C) return false;
  }
  return true;
}

bool MachineSupervisor::clearAllFaults(const InputSnapshot &input, bool lockout) {
  if (!canClearFaults(input, lockout)) {
    fault_clear_blocked_ = true;
    return false;
  }
  // Phase 2 has no conditional operations: every lower-level commit is private,
  // deterministic, and reachable only after the complete preflight above.
  shredder_.commitFaultClear();
  heaters_.commitFaultClear();
  diameter_.reset();
  gauge_.resetRecovery();
  forming_fault_reasons_ = FORMING_FAULT_NONE;
  forming_state_ = FormingChainState::NORMAL;
  spool_eligible_ = false;
  waste_mode_ = true;
  extrusion_arm_required_ = false;
  extrusion_ready_ = false;
  fault_clear_blocked_ = false;
  cooling_failure_pending_ = false;
  cooling_failure_actioned_ = false;
  cooling_failure_since_ms_ = 0;
  cooling_recovery_probe_active_ = false;
  cooling_recovery_since_ms_ = 0;
  resetCoolingStartupProbe();
  cooling_startup_preflight_fault_ = false;
  purge_started_ms_ = 0;
  purge_screw_revolutions_ = 0;
  purge_screw_revolutions_measured_ = false;
  purge_feed_approved_ = false;
  purge_run_completed_ = false;
  process_.commitFaultClear();
  return true;
}

void MachineSupervisor::enterEstop(const InputSnapshot &input) {
  resetCoolingStartupProbe();
  shredder_.stop();
  spool_eligible_ = false;
  waste_mode_ = true;
  extrusion_arm_required_ = false;
  extrusion_ready_ = false;
  process_.requestState(MachineState::ESTOP, input.safety);
}

bool MachineSupervisor::enterFormingRundown(uint16_t reason, const InputSnapshot &input, uint32_t now_ms) {
  forming_fault_reasons_ |= reason;
  spool_eligible_ = false;
  waste_mode_ = true;
  if (forming_state_ != FormingChainState::RUNDOWN) {
    forming_state_ = FormingChainState::RUNDOWN;
    forming_state_since_ms_ = now_ms;
    if (!process_.requestState(MachineState::FORMING_CHAIN_RUNDOWN, input.safety)) {
      forming_state_ = FormingChainState::LATCHED_FAULT;
      process_.reportFault();
      return false;
    }
  }
  return true;
}

void MachineSupervisor::enterLatchedFormingFault(uint16_t reason) {
  forming_fault_reasons_ |= reason;
  forming_state_ = FormingChainState::LATCHED_FAULT;
  spool_eligible_ = false;
  waste_mode_ = true;
  process_.reportFault();
}

void MachineSupervisor::resetRequalification(uint32_t now_ms) {
  forming_state_ = FormingChainState::REQUALIFYING;
  spool_eligible_ = false;
  waste_mode_ = true;
  consecutive_gauge_samples_ = 0;
  diameter_stable_since_ms_ = 0;
  ovality_stable_since_ms_ = 0;
  requalification_started_ms_ = now_ms;
  last_requalification_sample_ms_ = 0;
}

void MachineSupervisor::updateRequalification(const InputSnapshot &input, const GaugeReading &g, uint32_t now_ms) {
  if (forming_state_ != FormingChainState::REQUALIFYING) return;
  if (last_requalification_sample_ms_ != 0 && now_ms - last_requalification_sample_ms_ < 200UL) return;
  last_requalification_sample_ms_ = now_ms;
  if (input.puller_saturated) {
    consecutive_gauge_samples_ = 0;
    diameter_stable_since_ms_ = 0;
    ovality_stable_since_ms_ = 0;
    return;
  }
  if (gaugeWithinProductionTolerance(g)) {
    if (consecutive_gauge_samples_ < 255) ++consecutive_gauge_samples_;
  } else {
    consecutive_gauge_samples_ = 0;
  }
  if (g.valid && fabsf(g.mean_mm - 1.75f) <= REQUALIFICATION_DIAMETER_ERROR_MAX_MM) {
    if (diameter_stable_since_ms_ == 0) diameter_stable_since_ms_ = now_ms;
  } else diameter_stable_since_ms_ = 0;
  if (g.valid && g.ovality_mm <= REQUALIFICATION_OVALITY_MAX_MM) {
    if (ovality_stable_since_ms_ == 0) ovality_stable_since_ms_ = now_ms;
  } else ovality_stable_since_ms_ = 0;
  const uint32_t transport_ms = process_.material() == MaterialProfile::PET
      ? REQUALIFICATION_TRANSPORT_PET_MS : REQUALIFICATION_TRANSPORT_PLA_MS;
  if (consecutive_gauge_samples_ >= REQUALIFICATION_VALID_SAMPLES && diameter_stable_since_ms_ != 0 &&
      ovality_stable_since_ms_ != 0 && now_ms - diameter_stable_since_ms_ >= REQUALIFICATION_STABLE_MS &&
      now_ms - ovality_stable_since_ms_ >= REQUALIFICATION_STABLE_MS &&
      now_ms - requalification_started_ms_ >= transport_ms && !input.puller_saturated &&
      input.cooling_feedback_valid) {
    forming_state_ = FormingChainState::READY_TO_RETHREAD;
  }
}

ActuatorCommands MachineSupervisor::buildCommands(const InputSnapshot &input, const GaugeReading &g, uint32_t now_ms) {
  ActuatorCommands c{};
  const StatePermissions &p = process_.permissions();
  const ProcessProfile &profile = profileFor(process_.material());
  if (p.shredder) {
    const auto out = shredder_.update({now_ms, input.shredder_current_amp, input.shredder_rpm,
                                      input.safety.driver_fault_free, p.process_heaters || p.screw});
    if (out.command == ShredderCommand::FORWARD || out.command == ShredderCommand::OVERLOAD_DWELL)
      c.shredder_pwm = rpmToPwm(out.target_rpm, 40.0f);
    else if (out.command == ShredderCommand::REVERSE)
      c.shredder_pwm = -rpmToPwm(out.target_rpm, 40.0f);
    else if (out.command == ShredderCommand::FAULT_LATCHED) process_.reportFault();
  }
  float rundown_scale = 1.0f;
  if (forming_state_ == FormingChainState::RUNDOWN) {
    const uint32_t elapsed = now_ms - forming_state_since_ms_;
    rundown_scale = elapsed >= FORMING_SCREW_RUNDOWN_MS ? 0.0f : 1.0f - static_cast<float>(elapsed) / FORMING_SCREW_RUNDOWN_MS;
  }
  float screw_scale = rundown_scale;
  const bool maintenance_purge = process_.state() == MachineState::MAINTENANCE_PURGE;
  const bool purge_running = process_.materialSession() == MaterialSession::PURGE_RUNNING;
  const bool purge_motion_authorized = purge_running && purge_feed_approved_ && input.purge_feed_approved;
  if (purge_running) screw_scale = PURGE_SCREW_SCALE;
  const bool screw_authorized = !maintenance_purge || purge_motion_authorized;
  if (p.screw && screw_authorized && input.safety.driver_fault_free)
    c.screw_pwm = rpmToPwm(profile.screw_rpm * screw_scale, 25.0f);
  c.feeder_enable = p.feeder && !maintenance_purge &&
      (forming_state_ == FormingChainState::NORMAL || forming_state_ == FormingChainState::REQUALIFYING);
  if (maintenance_purge) c.feeder_enable = purge_motion_authorized;
  const float puller = diameter_.update(g, 1.75f, profile.puller_feedforward_mm_s,
                                         profile.diameter_kp, profile.diameter_ki, 0.1f);
  const bool waste_puller = forming_state_ == FormingChainState::RUNDOWN &&
                            now_ms - forming_state_since_ms_ < FORMING_PULLER_WASTE_MS &&
                            (forming_fault_reasons_ & FORMING_PULLER_FAILURE) == 0;
  const bool puller_authorized = p.puller &&
      (!maintenance_purge || purge_motion_authorized) &&
      (forming_state_ == FormingChainState::NORMAL || forming_state_ == FormingChainState::REQUALIFYING) &&
      puller > 0;
  if (puller_authorized || waste_puller)
    c.puller_pwm = waste_puller ? last_safe_puller_pwm_ : rpmToPwm(puller, 80.0f);
  if (forming_state_ == FormingChainState::NORMAL && c.puller_pwm > 0) last_safe_puller_pwm_ = c.puller_pwm;
  if (p.spooler && spool_eligible_ && forming_state_ == FormingChainState::NORMAL) {
    c.spooler_pwm = 96;
    c.traverse_enable = p.traverse && input.traverse_permission_ok;
    c.traverse_direction = ((now_ms / 4000UL) & 1U) != 0;
    c.traverse_step = c.traverse_enable && ((now_ms / 10UL) & 1U) != 0;
  }
  c.cooling_pwm = p.cooling ? static_cast<uint8_t>(profile.fan_percent * 255 / 100) : 0;
  if ((forming_fault_reasons_ & FORMING_COOLING_FAILURE) != 0 &&
      !cooling_recovery_probe_active_ && process_.state() != MachineState::REQUALIFYING)
    c.cooling_pwm = 0;
  const bool heater_permission = p.process_heaters && processHeaterPhaseAllowed(process_.state());
  const float targets[4] = {static_cast<float>(profile.zone_c[0]), static_cast<float>(profile.zone_c[1]),
                            static_cast<float>(profile.zone_c[2]), static_cast<float>(profile.die_c)};
  bool heater_requested[4]{};
  for (uint8_t zone = 0; zone < 4; ++zone) {
    float target = targets[zone];
    if (forming_state_ == FormingChainState::THERMAL_HOLD) target -= 20.0f;
    const auto out = heaters_.update(zone, input.temperatures[zone], target, heater_permission,
                                     input.safety.thermal_chain_ok, input.safety.heater_permission_feedback, now_ms);
    heater_requested[zone] = out.time_proportion_on;
    if (out.fault_bits != HEATER_FAULT_NONE) process_.reportFault();
  }
  constexpr float heater_watts[4] = {100.0f, 100.0f, 100.0f, 60.0f};
  const float heater_cap = STATE_HEATER_PEAK_CAP_W[static_cast<uint8_t>(process_.state())];
  commanded_heater_power_w_ = 0;
  for (uint8_t step = 0; step < 4; ++step) {
    const uint8_t zone = static_cast<uint8_t>((heater_priority_offset_ + step) % 4);
    if (heater_requested[zone] && commanded_heater_power_w_ + heater_watts[zone] <= heater_cap) {
      c.heater_on[zone] = true;
      commanded_heater_power_w_ += heater_watts[zone];
    }
  }
  heater_priority_offset_ = static_cast<uint8_t>((heater_priority_offset_ + 1) % 4);
  return c;
}

MachineViewState MachineSupervisor::buildView(uint32_t now_ms) const {
  SupervisorUiState ui = SupervisorUiState::RUNNING;
  if (process_.state() == MachineState::ESTOP) ui = SupervisorUiState::ESTOP;
  else if (process_.state() == MachineState::FAULT && fault_clear_blocked_) ui = SupervisorUiState::FAULT_CLEAR_BLOCKED;
  else if (process_.state() == MachineState::FAULT) ui = SupervisorUiState::FAULT;
  else if (cooling_startup_request_ != CoolingStartupRequest::NONE)
    ui = SupervisorUiState::COOLING_STARTUP_PROBE;
  else if (process_.state() == MachineState::PREHEATING && extrusion_ready_) ui = SupervisorUiState::READY_TO_EXTRUDE;
  else if (process_.state() == MachineState::MAINTENANCE_PURGE) ui = SupervisorUiState::MAINTENANCE_PURGE;
  else if (forming_state_ == FormingChainState::RUNDOWN || forming_state_ == FormingChainState::THERMAL_HOLD) ui = SupervisorUiState::FORMING_CHAIN_RUNDOWN;
  else if (forming_state_ == FormingChainState::REQUALIFYING) ui = SupervisorUiState::REQUALIFYING;
  else if (forming_state_ == FormingChainState::READY_TO_RETHREAD) ui = SupervisorUiState::READY_TO_RETHREAD;
  else if (process_.state() == MachineState::IDLE && calibration_.gauge_calibration_valid &&
           calibration_.cooling_feedback_calibration_valid && calibration_.temperature_channels_valid)
    ui = SupervisorUiState::READY_TO_PREHEAT;
  else if (process_.state() == MachineState::IDLE) ui = SupervisorUiState::CALIBRATION_REQUIRED;
  const uint32_t diameter_elapsed = diameter_stable_since_ms_ == 0 ? 0 : now_ms - diameter_stable_since_ms_;
  const uint32_t ovality_elapsed = ovality_stable_since_ms_ == 0 ? 0 : now_ms - ovality_stable_since_ms_;
  const uint32_t transport_elapsed = requalification_started_ms_ == 0 ? 0 : now_ms - requalification_started_ms_;
  const uint32_t cooling_dwell = cooling_failure_pending_ ? now_ms - cooling_failure_since_ms_ : 0;
  const uint32_t startup_elapsed = cooling_startup_probe_started_
      ? now_ms - cooling_startup_probe_started_ms_ : 0;
  const uint32_t startup_healthy = cooling_startup_healthy_started_
      ? now_ms - cooling_startup_healthy_since_ms_ : 0;
  return {ui, process_.state(), process_.materialSession(), forming_state_, forming_fault_reasons_,
          calibration_, cooling_feedback_valid_, extrusion_arm_required_, spool_eligible_, waste_mode_, dancer_warning_,
          purge_feed_approved_, heaters_.faults(), shredder_.faultLatched(), consecutive_gauge_samples_, diameter_elapsed,
          ovality_elapsed, transport_elapsed, cooling_dwell, cooling_startup_request_, startup_elapsed, startup_healthy,
          forming_state_ == FormingChainState::READY_TO_RETHREAD, commanded_heater_power_w_,
          purge_screw_revolutions_, purge_screw_revolutions_measured_, purge_run_completed_};
}

bool MachineSupervisor::invariantsHold(const ActuatorCommands &c) const {
  bool heaters_on = false;
  for (bool on : c.heater_on) heaters_on = heaters_on || on;
  const bool non_cooling_commanded = c.shredder_pwm != 0 || c.feeder_enable || c.screw_pwm != 0 ||
      c.puller_pwm != 0 || c.spooler_pwm != 0 || c.traverse_enable || c.hopper_ptc_on || heaters_on;
  return !(c.shredder_pwm != 0 && (c.screw_pwm != 0 || heaters_on)) &&
         !((c.spooler_pwm != 0 || c.traverse_enable) && !spool_eligible_) &&
         !(process_.state() == MachineState::FAULT && non_cooling_commanded) &&
         !(process_.state() == MachineState::ESTOP &&
           (non_cooling_commanded || c.cooling_pwm != 0));
}

SupervisorOutput MachineSupervisor::finalizeOutput(ActuatorCommands commands,
                                                   const InputSnapshot &input, uint32_t now_ms) {
  if (process_.state() == MachineState::ESTOP) {
    commands = ActuatorCommands{};
  } else if (process_.state() == MachineState::FAULT) {
    ActuatorCommands fault_commands{};
    if (process_.material() != MaterialProfile::NONE && input.cooling_feedback_valid &&
        (forming_fault_reasons_ & FORMING_COOLING_FAILURE) == 0 && !cooling_startup_preflight_fault_)
      fault_commands.cooling_pwm = commands.cooling_pwm;
    commands = fault_commands;
  }
  if (!invariantsHold(commands)) {
    process_.reportFault();
    commands = ActuatorCommands{};
    trackPullerCommand(commands, now_ms);
    return {commands, buildView(now_ms), false};
  }
  trackPullerCommand(commands, now_ms);
  return {commands, buildView(now_ms), true};
}

SupervisorOutput MachineSupervisor::update(const InputSnapshot &input, uint32_t now_ms) {
  cooling_feedback_valid_ = input.cooling_feedback_valid;
  calibration_.temperature_channels_valid = true;
  for (uint8_t i = 0; i < 5; ++i) calibration_.temperature_channels_valid =
      calibration_.temperature_channels_valid && input.temperatures[i].valid && !input.temperatures[i].sensor_open;
  const GaugeReading gauge = gauge_.update(input.gauge_x_adc, input.gauge_y_adc, input.gauge_optical_valid);
  if (!input.safety.estop_ok) {
    enterEstop(input);
    return finalizeOutput(ActuatorCommands{}, input, now_ms);
  }
  if (!guardsOk(input)) {
    if (cooling_startup_request_ != CoolingStartupRequest::NONE)
      cooling_startup_preflight_fault_ = true;
    resetCoolingStartupProbe();
    process_.reportFault();
  }

  updateCoolingStartupProbe(input, now_ms);

  if (process_.state() == MachineState::PREHEATING && input.safety.temperatures_ready && gauge.valid &&
      input.cooling_feedback_valid && calibration_.cooling_feedback_calibration_valid)
    extrusion_ready_ = true;
  if (process_.state() == MachineState::MAINTENANCE_PURGE &&
      process_.materialSession() == MaterialSession::PURGE_PREHEAT_REQUIRED && input.safety.temperatures_ready)
    process_.markPurgeReady(input.safety);

  if (last_update_ms_ != 0 && process_.materialSession() == MaterialSession::PURGE_RUNNING) {
    purge_screw_revolutions_ += input.screw_rpm * (now_ms - last_update_ms_) / 60000.0f;
    purge_temperature_stable_ = purge_temperature_stable_ && input.safety.temperatures_ready;
  }
  last_update_ms_ = now_ms;

  const MachineState cooling_phase = process_.state();
  const bool cooling_commanded = cooling_phase != MachineState::FAULT && cooling_phase != MachineState::ESTOP &&
      process_.permissions().cooling &&
      profileFor(process_.material()).fan_percent * 255 / 100 >= COOLING_COMMAND_THRESHOLD_PWM;
  if (cooling_commanded && !input.cooling_feedback_valid) {
    if (!cooling_failure_pending_) { cooling_failure_pending_ = true; cooling_failure_since_ms_ = now_ms; }
    else if (!cooling_failure_actioned_ && now_ms - cooling_failure_since_ms_ >= COOLING_FEEDBACK_DWELL_MS) {
      cooling_failure_actioned_ = true;
      if (cooling_phase == MachineState::EXTRUSION || cooling_phase == MachineState::REQUALIFYING)
        enterFormingRundown(FORMING_COOLING_FAILURE, input, now_ms);
      else
        enterLatchedFormingFault(FORMING_COOLING_FAILURE);
    }
  } else {
    cooling_failure_pending_ = false;
    if ((forming_fault_reasons_ & FORMING_COOLING_FAILURE) == 0) cooling_failure_actioned_ = false;
  }

  if (canCompleteCooldown(input)) process_.requestState(MachineState::IDLE, input.safety);

  dancer_warning_ = fabsf(input.dancer_angle_rad) >= DANCER_WARNING_RAD;
  if (process_.state() == MachineState::EXTRUSION || process_.state() == MachineState::REQUALIFYING) {
    const bool production_winding = process_.state() == MachineState::EXTRUSION &&
        forming_state_ == FormingChainState::NORMAL && spool_eligible_;
    if (production_winding) {
      if (!gauge.valid) enterFormingRundown(FORMING_GAUGE_INVALID, input, now_ms);
      else if (gauge.u95_mm > REQUALIFICATION_U95_MAX_MM)
        enterFormingRundown(FORMING_GAUGE_UNCERTAINTY, input, now_ms);
      else if (fabsf(gauge.mean_mm - 1.75f) > REQUALIFICATION_DIAMETER_ERROR_MAX_MM ||
               gauge.ovality_mm > REQUALIFICATION_OVALITY_MAX_MM || input.puller_saturated) {
        if (process_.requestState(MachineState::REQUALIFYING, input.safety)) resetRequalification(now_ms);
        else enterFormingRundown(FORMING_GAUGE_UNCERTAINTY, input, now_ms);
      }
    }
    if (!input.puller_driver_ok) enterFormingRundown(FORMING_PULLER_DRIVER_FAILURE, input, now_ms);
    if (pullerTachFault(input, now_ms)) enterFormingRundown(FORMING_PULLER_TACH_FAILURE, input, now_ms);
    if (!input.spooler_driver_ok) enterFormingRundown(FORMING_SPOOLER_FAILURE, input, now_ms);
    if (!input.traverse_permission_ok && spool_eligible_) enterFormingRundown(FORMING_TRAVERSE_PERMISSION_LOSS, input, now_ms);
    if (fabsf(input.dancer_angle_rad) >= DANCER_MECHANICAL_HARD_STOP_RAD) enterLatchedFormingFault(FORMING_DANCER_HARD_STOP);
    else if (fabsf(input.dancer_angle_rad) >= DANCER_CONTROLLED_STOP_RAD) enterFormingRundown(FORMING_DANCER_CONTROLLED_STOP, input, now_ms);
  }

  if (forming_state_ == FormingChainState::RUNDOWN && now_ms - forming_state_since_ms_ >= FORMING_SCREW_RUNDOWN_MS) {
    if (process_.requestState(MachineState::THERMAL_HOLD, input.safety)) {
      forming_state_ = FormingChainState::THERMAL_HOLD;
      forming_state_since_ms_ = now_ms;
    } else {
      enterLatchedFormingFault(forming_fault_reasons_);
    }
  } else if (forming_state_ == FormingChainState::THERMAL_HOLD &&
             now_ms - forming_state_since_ms_ >= THERMAL_HOLD_MS) {
    const bool cooling_fault = (forming_fault_reasons_ & FORMING_COOLING_FAILURE) != 0;
    if (cooling_fault) cooling_recovery_probe_active_ = true;
    if (cooling_recovery_probe_active_ && input.cooling_feedback_valid) {
      if (cooling_recovery_since_ms_ == 0) cooling_recovery_since_ms_ = now_ms;
    } else {
      cooling_recovery_since_ms_ = 0;
    }
    const bool cooling_recovered = !cooling_fault ||
        (cooling_recovery_since_ms_ != 0 && now_ms - cooling_recovery_since_ms_ >= COOLING_FEEDBACK_DWELL_MS);
    if (cooling_recovered && input.cooling_feedback_valid && gauge.valid &&
        input.safety.temperatures_ready && guardsOk(input)) {
      if (process_.requestState(MachineState::REQUALIFYING, input.safety)) resetRequalification(now_ms);
      else enterLatchedFormingFault(forming_fault_reasons_);
    }
  }
  updateRequalification(input, gauge, now_ms);
  ActuatorCommands commands = buildCommands(input, gauge, now_ms);
  if (cooling_startup_request_ != CoolingStartupRequest::NONE && process_.state() == MachineState::IDLE) {
    commands = ActuatorCommands{};
    commands.cooling_pwm = process_.material() == MaterialProfile::PET
        ? PET_COOLING_STARTUP_PROBE_PWM : PLA_COOLING_STARTUP_PROBE_PWM;
  }
  return finalizeOutput(commands, input, now_ms);
}
