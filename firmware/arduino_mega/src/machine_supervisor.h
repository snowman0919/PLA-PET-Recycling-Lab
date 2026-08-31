#pragma once

#include <stdint.h>

#include "gauge_control.h"
#include "heater_control.h"
#include "heater_power_allocator.h"
#include "puller_speed_control.h"
#include "screw_motion_monitor.h"
#include "cooling_monitor.h"
#include "spooler_control.h"
#include "traverse_control.h"
#include "process_state.h"
#include "shredder_control.h"

enum FormingFaultReason : uint16_t {
  FORMING_FAULT_NONE = 0,
  FORMING_GAUGE_INVALID = 1 << 0,
  FORMING_GAUGE_UNCERTAINTY = 1 << 1,
  FORMING_COOLING_FAILURE = 1 << 2,
  FORMING_PULLER_DRIVER_FAILURE = 1 << 3,
  FORMING_PULLER_TACH_FAILURE = 1 << 4,
  FORMING_SPOOLER_FAILURE = 1 << 5,
  FORMING_DANCER_CONTROLLED_STOP = 1 << 6,
  FORMING_DANCER_HARD_STOP = 1 << 7,
  FORMING_TRAVERSE_PERMISSION_LOSS = 1 << 8,
  FORMING_PULLER_SATURATION = 1 << 9,
  FORMING_SPOOL_JAM = 1 << 10,
  FORMING_TRAVERSE_HARD_FAULT = 1 << 11,
  FORMING_SCREW_MOTION_MISMATCH = 1 << 12,
  FORMING_PULLER_FAILURE = FORMING_PULLER_DRIVER_FAILURE | FORMING_PULLER_TACH_FAILURE,
};

enum class FormingChainState : uint8_t {
  NORMAL,
  RUNDOWN,
  THERMAL_HOLD,
  REQUALIFYING,
  READY_TO_RETHREAD,
  LATCHED_FAULT,
};

enum class SupervisorUiState : uint8_t {
  CALIBRATION_REQUIRED,
  READY_TO_PREHEAT,
  COOLING_STARTUP_PROBE,
  READY_TO_EXTRUDE,
  RUNNING,
  MAINTENANCE_PURGE,
  FORMING_CHAIN_RUNDOWN,
  REQUALIFYING,
  READY_TO_RETHREAD,
  FAULT_CLEAR_BLOCKED,
  FAULT,
  ESTOP,
};

enum class CoolingStartupRequest : uint8_t {
  NONE,
  PREHEAT,
  PURGE_PREHEAT,
};

struct CalibrationReadiness {
  bool drive_calibration_valid{false};
  bool gauge_calibration_valid{false};
  bool current_sensor_calibration_valid{false};
  bool cooling_feedback_calibration_valid{false};
  bool puller_calibration_valid{false};
  bool temperature_channels_valid{false};
};

struct InputSnapshot {
  SafetyInputs safety{true, true, true, true, false, false, false, true, true};
  TemperatureReading temperatures[5]{};
  uint16_t gauge_x_adc{0};
  uint16_t gauge_y_adc{0};
  bool gauge_optical_valid{false};
  float shredder_current_amp{0};
  float shredder_rpm{0};
  float screw_rpm{0};
  bool screw_tach_valid{true};
  bool cooling_feedback_valid{false};
  float fan1_rpm{1800.0f};
  float fan2_rpm{1800.0f};
  bool fan1_tach_valid{true};
  bool fan2_tach_valid{true};
  bool puller_driver_ok{true};
  bool puller_tach_ok{true};
  bool puller_saturated{false};
  float puller_rpm{6.0f};
  bool spooler_driver_ok{true};
  bool spooler_tach_ok{true};
  float spooler_rpm{12.0f};
  bool traverse_permission_ok{true};
  bool traverse_left_limit{false};
  bool traverse_right_limit{false};
  bool purge_feed_approved{false};
  bool purge_waste_path_confirmed{false};
  bool screw_speed_is_measured{false};
  float dancer_angle_rad{0};
};

struct MachineViewState {
  SupervisorUiState ui_state;
  MachineState process_phase;
  MaterialSession material_session;
  FormingChainState forming_chain_state;
  uint16_t forming_fault_reasons;
  CalibrationReadiness calibration;
  bool cooling_feedback_valid;
  bool extrusion_arm_required;
  bool spool_eligible;
  bool waste_mode;
  bool dancer_warning;
  bool purge_feed_approved;
  uint16_t heater_faults;
  bool shredder_fault_latched;
  uint8_t requalification_valid_samples;
  uint32_t requalification_diameter_stable_ms;
  uint32_t requalification_ovality_stable_ms;
  uint32_t requalification_transport_elapsed_ms;
  uint32_t cooling_failure_dwell_ms;
  CoolingStartupRequest cooling_startup_request;
  uint32_t cooling_startup_probe_elapsed_ms;
  uint32_t cooling_startup_healthy_dwell_ms;
  bool requalification_satisfied;
  float commanded_heater_power_w;
  float purge_screw_revolutions;
  bool purge_screw_revolutions_measured;
  bool purge_run_completed;
  PullerSpeedOutput puller;
  ScrewMotionOutput screw_motion;
  CoolingMonitorOutput cooling;
  SpoolerOutput spooler;
  TraverseOutput traverse;
  HeaterAllocation heater_allocation;
  uint32_t forming_fault_detected_ms;
  uint32_t forming_state_changed_ms;
};

struct SupervisorOutput {
  ActuatorCommands actuators;
  MachineViewState view;
  bool invariants_ok;
};

struct MachineSupervisorTestAccess;

class MachineSupervisor {
 public:
  MachineSupervisor();
  bool configureDriveCalibration(const DriveCalibration &calibration);
  bool configureGaugeCalibration(const GaugeCalibration &calibration);
  bool configureCurrentSensorCalibration(float zero_adc, float amps_per_count);
  bool configureCoolingFeedbackCalibration(float zero_adc, float amps_per_count);
  bool configurePullerCalibration(const PullerCalibration &calibration);

  bool selectMaterial(MaterialProfile material);
  bool requestMaterialChange(MaterialProfile material, const InputSnapshot &input);
  bool requestShredding(const InputSnapshot &input, uint32_t now_ms);
  bool requestPreheat(const InputSnapshot &input);
  bool armExtrusion(const InputSnapshot &input, uint32_t now_ms);
  bool requestPurgePreheat(const InputSnapshot &input);
  bool approvePurgeFeed(bool explicit_confirmation);
  bool confirmPurgeWastePath(const InputSnapshot &input, uint32_t now_ms);
  bool confirmPurgeComplete(bool visual_confirmation, const InputSnapshot &input, uint32_t now_ms);
  bool acknowledgeMaterialStep(MaterialSession expected, bool explicit_confirmation);
  bool confirmManualRethread(const InputSnapshot &input);
  void requestStop(const InputSnapshot &input);

  bool canClearFaults(const InputSnapshot &input, bool physical_lockout_confirmed) const;
  bool canCompleteCooldown(const InputSnapshot &input) const;
  bool clearAllFaults(const InputSnapshot &input, bool physical_lockout_confirmed);
  SupervisorOutput update(const InputSnapshot &input, uint32_t now_ms);

  const ProcessController &process() const { return process_; }
  const CalibrationReadiness &calibrationReadiness() const { return calibration_; }
  FormingChainState formingState() const { return forming_state_; }
  uint16_t formingFaultReasons() const { return forming_fault_reasons_; }
  bool spoolEligible() const { return spool_eligible_; }
  bool wasteMode() const { return waste_mode_; }
  bool extrusionArmRequired() const { return extrusion_arm_required_; }
  uint16_t heaterFaults() const { return heaters_.faults(); }
  bool shredderFaultLatched() const { return shredder_.faultLatched(); }
  bool lastPullerSaturated() const { return puller_output_.saturated; }

 private:
  bool guardsOk(const InputSnapshot &input) const;
  void resetCoolingStartupProbe();
  void updateCoolingStartupProbe(const InputSnapshot &input, uint32_t now_ms);
  bool pullerTachFault(const InputSnapshot &input, uint32_t now_ms);
  void trackPullerCommand(const ActuatorCommands &commands, uint32_t now_ms);
  void enterEstop(const InputSnapshot &input);
  bool enterFormingRundown(uint16_t reason, const InputSnapshot &input, uint32_t now_ms);
  void enterLatchedFormingFault(uint16_t reason);
  void resetRequalification(uint32_t now_ms);
  void updateRequalification(const InputSnapshot &input, const GaugeReading &gauge, uint32_t now_ms);
  ActuatorCommands buildCommands(const InputSnapshot &input, const GaugeReading &gauge, uint32_t now_ms);
  MachineViewState buildView(uint32_t now_ms) const;
  bool invariantsHold(const ActuatorCommands &commands) const;
  SupervisorOutput finalizeOutput(ActuatorCommands commands, const InputSnapshot &input, uint32_t now_ms);

  friend struct MachineSupervisorTestAccess;

  ProcessController process_;
  ShredderController shredder_;
  HeaterController heaters_;
  HeaterPowerAllocator heater_allocator_;
  GaugeController gauge_;
  DiameterController diameter_;
  PullerSpeedController puller_speed_;
  ScrewMotionMonitor screw_motion_;
  CoolingMonitor cooling_monitor_;
  SpoolerController spooler_control_;
  TraverseController traverse_control_;
  CalibrationReadiness calibration_;
  FormingChainState forming_state_{FormingChainState::NORMAL};
  uint16_t forming_fault_reasons_{FORMING_FAULT_NONE};
  bool extrusion_arm_required_{false};
  bool extrusion_ready_{false};
  bool fault_clear_blocked_{false};
  bool spool_eligible_{false};
  bool waste_mode_{true};
  bool dancer_warning_{false};
  bool cooling_feedback_valid_{false};
  bool cooling_failure_pending_{false};
  bool cooling_failure_actioned_{false};
  uint32_t cooling_failure_since_ms_{0};
  bool cooling_recovery_probe_active_{false};
  uint32_t cooling_recovery_since_ms_{0};
  CoolingStartupRequest cooling_startup_request_{CoolingStartupRequest::NONE};
  bool cooling_startup_probe_started_{false};
  bool cooling_startup_healthy_started_{false};
  uint32_t cooling_startup_probe_started_ms_{0};
  uint32_t cooling_startup_healthy_since_ms_{0};
  bool cooling_startup_preflight_fault_{false};
  uint32_t forming_state_since_ms_{0};
  uint32_t requalification_started_ms_{0};
  uint32_t last_requalification_sample_ms_{0};
  uint32_t diameter_stable_since_ms_{0};
  uint32_t ovality_stable_since_ms_{0};
  uint8_t consecutive_gauge_samples_{0};
  uint32_t purge_started_ms_{0};
  float purge_screw_revolutions_{0};
  float purge_start_screw_revolutions_{0};
  bool purge_screw_revolutions_measured_{false};
  uint32_t last_update_ms_{0};
  bool purge_temperature_stable_{false};
  bool purge_feed_approved_{false};
  bool purge_run_completed_{false};
  uint8_t heater_priority_offset_{0};
  float commanded_heater_power_w_{0};
  int16_t last_safe_puller_pwm_{0};
  bool puller_command_active_{false};
  bool puller_tach_qualified_{false};
  uint32_t puller_command_started_ms_{0};
  uint8_t last_cooling_pwm_{0};
  PullerSpeedOutput puller_output_{};
  ScrewMotionOutput screw_motion_output_{};
  CoolingMonitorOutput cooling_output_{};
  SpoolerOutput spooler_output_{};
  TraverseOutput traverse_output_{};
  HeaterAllocation heater_allocation_{};
  uint32_t forming_fault_detected_ms_{0};
};
