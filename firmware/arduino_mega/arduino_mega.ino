#include <EEPROM.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <avr/interrupt.h>

#include "src/board_config.h"
#include "src/calibration_record.h"
#include "src/machine_supervisor.h"
#include "src/tach_contract_generated.h"
#include "src/ui_core.h"

namespace {
constexpr const char *ACTUATION_REVISION = "parallel-actuation-hardening-v0.6.2";
MachineSupervisor supervisor;
UiController ui;
TemperatureReading temperatures[5]{};
ActuatorCommands last_commands{};
CalibrationRecord calibration_record{};
TachEstimator shredder_tach;
TachEstimator puller_tach;
TachEstimator screw_tach;
TachEstimator spooler_tach;
TachEstimate shredder_tach_sample{};
TachEstimate puller_tach_sample{};
TachEstimate screw_tach_sample{};
TachEstimate spooler_tach_sample{};
volatile uint32_t fan_pulses[2] = {0, 0};
volatile bool fan_mux_channel = false;
volatile uint8_t portk_previous = 0;
float shredder_rpm = 0;
float puller_rpm = 0;
float screw_rpm = 0;
float spooler_rpm = 0;
float fan_rpm[2] = {0, 0};
uint32_t last_tach_sample_ms = 0;
uint32_t last_fan_sample_ms = 0;
uint32_t last_temperature_sample_ms = 0;
uint32_t last_log_ms = 0;
#ifdef PPR_DEBUG
uint32_t deadline_overruns = 0;
uint32_t maximum_loop_us = 0;
#endif
bool purge_feed_approved = false;
char serial_line[180]{};
uint8_t serial_length = 0;
SupervisorOutput telemetry_snapshot{};
uint32_t telemetry_snapshot_ms = 0;
uint8_t telemetry_segment = 0;
uint8_t telemetry_length = 0;
uint8_t telemetry_offset = 0;
bool telemetry_active = false;
char telemetry_buffer[160]{};

class Max6675Backend final : public TemperatureBackend {
 public:
  TemperatureReading read(TemperatureChannel channel, uint32_t now_ms) override {
    const uint8_t index = static_cast<uint8_t>(channel);
    if (index >= 5) return {0, false, true, now_ms};
    const uint8_t cs = Board::THERMOCOUPLE_CS_PINS[index];
    digitalWrite(cs, LOW);
    delayMicroseconds(2);
    uint16_t value = 0;
    for (uint8_t bit = 0; bit < 16; ++bit) {
      digitalWrite(Board::THERMOCOUPLE_SCK_PIN, HIGH);
      delayMicroseconds(1);
      value = static_cast<uint16_t>((value << 1) | (digitalRead(Board::THERMOCOUPLE_SO_PIN) ? 1 : 0));
      digitalWrite(Board::THERMOCOUPLE_SCK_PIN, LOW);
      delayMicroseconds(1);
    }
    digitalWrite(cs, HIGH);
    const bool open = (value & 0x0004U) != 0;
    const float celsius = static_cast<float>((value >> 3) & 0x0FFFU) * 0.25f;
    return {celsius, !open && celsius >= HEATER_MIN_VALID_C && celsius <= HEATER_MAX_VALID_C, open, now_ms};
  }
} thermocouples;

// A4 feedback remains invalid until its donor-specific ADC calibration is loaded.
class BoardFanCurrentFeedback final : public CoolingFeedbackBackend {
 public:
  CoolingFeedback read(uint32_t) override {
    if ((calibration_record.readiness_flags & CALIBRATION_HAS_COOLING) == 0 ||
        calibration_record.cooling_amps_per_count <= 0) return {0, false};
    const float current = abs(analogRead(Board::COOLING_CURRENT_PIN) - calibration_record.cooling_zero_adc) *
                          calibration_record.cooling_amps_per_count;
    return {current, current >= COOLING_FEEDBACK_MIN_A && current <= COOLING_FEEDBACK_MAX_A};
  }
} cooling_feedback;

class BoardActuators final : public ActuatorBackend {
 public:
  void apply(const ActuatorCommands &c) override {
    setMotor(Board::SHREDDER_PWM_PIN, Board::SHREDDER_DIR_PIN, Board::SHREDDER_ENABLE_PIN, c.shredder_pwm);
    digitalWrite(Board::SHREDDER_REVERSE_PIN, c.shredder_pwm < 0 ? HIGH : LOW);
    digitalWrite(Board::FEEDER_ENABLE_PIN, c.feeder_enable ? HIGH : LOW);
    setMotor(Board::SCREW_PWM_PIN, Board::SCREW_DIR_PIN, Board::SCREW_ENABLE_PIN, c.screw_pwm);
    setMotor(Board::PULLER_PWM_PIN, Board::PULLER_DIR_PIN, Board::PULLER_ENABLE_PIN, c.puller_pwm);
    setMotor(Board::SPOOLER_PWM_PIN, Board::SPOOLER_DIR_PIN, Board::SPOOLER_ENABLE_PIN, c.spooler_pwm);
    analogWrite(Board::COOLING_PWM_PIN, c.cooling_pwm);
    digitalWrite(Board::TRAVERSE_DIR_PIN, c.traverse_direction ? HIGH : LOW);
    digitalWrite(Board::TRAVERSE_ENABLE_PIN, c.traverse_enable ? HIGH : LOW);
    digitalWrite(Board::TRAVERSE_STEP_PIN, c.traverse_step ? HIGH : LOW);
    for (uint8_t zone = 0; zone < 4; ++zone) digitalWrite(Board::HEATER_PINS[zone], c.heater_on[zone] ? HIGH : LOW);
    digitalWrite(Board::HOPPER_PTC_PIN, c.hopper_ptc_on ? HIGH : LOW);
  }

 private:
  static void setMotor(uint8_t pwm, uint8_t direction, uint8_t enable, int16_t value) {
    const uint8_t duty = static_cast<uint8_t>(constrain(abs(value), 0, 255));
    digitalWrite(direction, value >= 0 ? HIGH : LOW);
    digitalWrite(enable, duty > 0 ? HIGH : LOW);
    analogWrite(pwm, duty);
  }
} actuators;

void shredderPulse() { shredder_tach.onPulse(micros()); }
void pullerPulse() { puller_tach.onPulse(micros()); }

ISR(PCINT2_vect) {
  const uint8_t current = PINK;
  const uint8_t rising = static_cast<uint8_t>(current & static_cast<uint8_t>(~portk_previous));
  const uint32_t now_us = micros();
  if ((rising & _BV(PK5)) != 0) screw_tach.onPulse(now_us);   // A13 / PCINT21
  if ((rising & _BV(PK6)) != 0) ++fan_pulses[fan_mux_channel ? 1 : 0]; // A14 / PCINT22
  if ((rising & _BV(PK7)) != 0) spooler_tach.onPulse(now_us); // A15 / PCINT23
  portk_previous = current;
}

bool allDriversHealthy() {
  for (uint8_t pin : Board::DRIVER_FAULT_PINS) if (digitalRead(pin) == LOW) return false;
  return true;
}

bool temperaturesReady() {
  if (supervisor.process().material() == MaterialProfile::NONE) return false;
  const ProcessProfile &profile = profileFor(supervisor.process().material());
  const float target[4] = {static_cast<float>(profile.zone_c[0]), static_cast<float>(profile.zone_c[1]),
                           static_cast<float>(profile.zone_c[2]), static_cast<float>(profile.die_c)};
  for (uint8_t zone = 0; zone < 4; ++zone)
    if (!temperatures[zone].valid || abs(temperatures[zone].celsius - target[zone]) > 5.0f) return false;
  return temperatures[4].valid;
}

InputSnapshot readInputs(uint32_t now_ms) {
  InputSnapshot input;
  input.safety = {digitalRead(Board::ESTOP_PIN) == HIGH,
                  digitalRead(Board::LID_PIN) == HIGH,
                  digitalRead(Board::SERVICE_GUARD_PIN) == HIGH,
                  digitalRead(Board::THERMAL_CHAIN_PIN) == HIGH,
                  temperaturesReady(),
                  digitalRead(Board::GAUGE_VALID_PIN) == HIGH,
                  digitalRead(Board::LOCKOUT_CONFIRM_PIN) == LOW,
                  allDriversHealthy(),
                  digitalRead(Board::HEATER_PERMISSION_FEEDBACK_PIN) == HIGH};
  for (uint8_t channel = 0; channel < 5; ++channel) input.temperatures[channel] = temperatures[channel];
  input.gauge_x_adc = analogRead(Board::GAUGE_X_PIN);
  input.gauge_y_adc = analogRead(Board::GAUGE_Y_PIN);
  input.gauge_optical_valid = digitalRead(Board::GAUGE_VALID_PIN) == HIGH;
  input.shredder_current_amp = calibration_record.current_amps_per_count > 0
      ? abs(analogRead(Board::CURRENT_PIN) - calibration_record.current_zero_adc) * calibration_record.current_amps_per_count : 0;
  input.shredder_rpm = shredder_rpm;
  input.shredder_tach_valid = calibrationDomainReady(calibration_record, CAL_SHREDDER_TACH) &&
      shredder_tach_sample.valid;
  input.screw_rpm = screw_rpm;
  input.screw_tach_valid = calibrationDomainReady(calibration_record, CAL_SCREW_TACH) &&
      screw_tach_sample.valid;
  input.screw_speed_is_measured = input.screw_tach_valid;
  const CoolingFeedback fan_current = cooling_feedback.read(now_ms);
  input.cooling_feedback_valid = fan_current.valid;
  input.fan1_rpm = fan_rpm[0];
  input.fan2_rpm = fan_rpm[1];
  input.fan1_tach_valid = calibrationDomainReady(calibration_record, CAL_FAN1_TACH);
  input.fan2_tach_valid = calibrationDomainReady(calibration_record, CAL_FAN2_TACH);
  input.puller_driver_ok = digitalRead(Board::PULLER_FAULT_PIN) == HIGH;
  input.puller_tach_ok = calibrationDomainReady(calibration_record, CAL_PULLER_TACH) &&
      (last_commands.puller_pwm == 0 || puller_tach_sample.valid);
  input.puller_rpm = puller_rpm;
  input.puller_saturated = supervisor.lastPullerSaturated();
  input.spooler_driver_ok = digitalRead(Board::SPOOLER_FAULT_PIN) == HIGH;
  input.spooler_tach_ok = calibrationDomainReady(calibration_record, CAL_SPOOLER_TACH) &&
      (last_commands.spooler_pwm == 0 || spooler_tach_sample.valid);
  input.spooler_rpm = spooler_rpm;
  input.traverse_permission_ok = true;
  input.traverse_left_limit = digitalRead(Board::TRAVERSE_LEFT_LIMIT_PIN) == LOW;
  input.traverse_right_limit = digitalRead(Board::TRAVERSE_RIGHT_LIMIT_PIN) == LOW;
  input.purge_feed_approved = purge_feed_approved;
  const float dancer_scale = calibrationDomainReady(calibration_record, CAL_DANCER)
      ? calibration_record.records[CAL_DANCER].value : 0.0f;
  input.dancer_angle_rad = (analogRead(Board::DANCER_PIN) - 512) * dancer_scale;
  return input;
}

bool configureTachEstimator(TachEstimator &estimator, TachChannel channel,
                            CalibrationId calibration_id) {
  TachEstimatorConfig config = tachConfig(channel);
  if (calibrationDomainReady(calibration_record, calibration_id)) {
    const float ppr = calibration_record.records[calibration_id].value;
    const uint16_t rounded = static_cast<uint16_t>(ppr + 0.5f);
    if (rounded == 0 || fabsf(ppr - rounded) > 0.01f) return false;
    config.pulses_per_revolution = rounded;
  }
  return estimator.configure(config);
}

bool configureTachEstimators() {
  return configureTachEstimator(shredder_tach, TachChannel::SHREDDER, CAL_SHREDDER_TACH) &&
      configureTachEstimator(screw_tach, TachChannel::SCREW, CAL_SCREW_TACH) &&
      configureTachEstimator(puller_tach, TachChannel::PULLER, CAL_PULLER_TACH) &&
      configureTachEstimator(spooler_tach, TachChannel::SPOOLER, CAL_SPOOLER_TACH);
}

bool loadCalibration() {
  EEPROM.get(0, calibration_record);
  if (!sanitizeCalibrationRecord(calibration_record)) return false;
  return supervisor.configureCalibrationRecord(calibration_record) && configureTachEstimators();
}

void saveCalibration() {
  finalizeCalibrationRecord(calibration_record);
  EEPROM.put(0, calibration_record);
}

bool recordCommissioned(CalibrationId id, float value, float valid_min,
                        float valid_max, uint32_t revision) {
  return setCalibrationValueRecord(calibration_record.records[id], id, value,
      calibrationUnitsForId(id), revision == 0 ? 1 : revision,
      CalibrationSource::COMMISSIONING_MEASUREMENT, true, valid_min, valid_max);
}

float nextFloat(char **context, bool &ok) {
  char *token = strtok_r(nullptr, " ", context);
  if (token == nullptr) { ok = false; return 0; }
  return static_cast<float>(atof(token));
}

void executeCommand(char *line, InputSnapshot input, uint32_t now_ms) {
  char *context = nullptr;
  char *verb = strtok_r(line, " ", &context);
  if (verb == nullptr) return;
  bool accepted = false;
  if (strcmp(verb, "MATERIAL") == 0) {
    char *name = strtok_r(nullptr, " ", &context);
    MaterialProfile material = MaterialProfile::NONE;
    if (name != nullptr && strcmp(name, "PLA") == 0) material = MaterialProfile::PLA;
    else if (name != nullptr && strcmp(name, "PET") == 0) material = MaterialProfile::PET;
    accepted = material != MaterialProfile::NONE &&
               (supervisor.selectMaterial(material) || supervisor.requestMaterialChange(material, input));
    if (accepted) purge_feed_approved = false;
  } else if (strcmp(verb, "SHRED") == 0) accepted = supervisor.requestShredding(input, now_ms);
  else if (strcmp(verb, "PREHEAT") == 0) accepted = supervisor.requestPreheat(input);
  else if (strcmp(verb, "ARM") == 0) accepted = supervisor.armExtrusion(input, now_ms);
  else if (strcmp(verb, "PURGE_PREHEAT") == 0) accepted = supervisor.requestPurgePreheat(input);
  else if (strcmp(verb, "PURGE_FEED_APPROVED") == 0) {
    accepted = supervisor.approvePurgeFeed(true);
    if (accepted) purge_feed_approved = true;
  } else if (strcmp(verb, "PURGE_WASTE_READY") == 0) {
    input.purge_waste_path_confirmed = true;
    accepted = supervisor.confirmPurgeWastePath(input, now_ms);
  } else if (strcmp(verb, "PURGE_COMPLETE_VISUAL") == 0) {
    accepted = supervisor.confirmPurgeComplete(true, input, now_ms);
    if (accepted) purge_feed_approved = false;
  }
  else if (strcmp(verb, "RETHREAD") == 0) accepted = supervisor.confirmManualRethread(input);
  else if (strcmp(verb, "HOME_TRAVERSE") == 0) accepted = supervisor.requestTraverseHoming(input);
  else if (strcmp(verb, "ACK") == 0)
    accepted = supervisor.acknowledgeMaterialStep(supervisor.process().materialSession(), true);
  else if (strcmp(verb, "STOP") == 0) {
    supervisor.requestStop(input);
    purge_feed_approved = false;
    accepted = true;
  } else if (strcmp(verb, "CLEAR") == 0) {
    accepted = supervisor.clearAllFaults(input, input.safety.restart_permission);
    if (accepted) purge_feed_approved = false;
  } else if (strcmp(verb, "CAL") == 0) {
    char *kind = strtok_r(nullptr, " ", &context);
    bool ok = kind != nullptr;
    if (ok && strcmp(kind, "GAUGE") == 0) {
      GaugeCalibration gauge{nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok),
                             nextFloat(&context, ok), nextFloat(&context, ok), true};
      accepted = ok && supervisor.configureGaugeCalibration(gauge);
      if (accepted) {
        calibration_record.gauge = gauge;
        accepted = recordCommissioned(CAL_GAUGE_XY,
            (fabsf(gauge.x_mm_per_count) + fabsf(gauge.y_mm_per_count)) * 0.5f,
            0.00001f, 10.0f, now_ms);
        saveCalibration();
      }
    } else if (ok && strcmp(kind, "DRIVE") == 0) {
      DriveCalibration drive{nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok),
                             nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), true};
      accepted = ok && supervisor.configureDriveCalibration(drive);
      if (accepted) {
        calibration_record.drive = drive;
        accepted = recordCommissioned(CAL_SHREDDER_DRIVE, drive.no_load_cutter_rpm,
                                       1.0f, 1000.0f, now_ms);
        saveCalibration();
      }
    } else if (ok && strcmp(kind, "CURRENT") == 0) {
      const float zero = nextFloat(&context, ok);
      const float scale = nextFloat(&context, ok);
      accepted = ok && supervisor.configureCurrentSensorCalibration(zero, scale);
      if (accepted) {
        calibration_record.current_zero_adc = zero;
        calibration_record.current_amps_per_count = scale;
        accepted = recordCommissioned(CAL_CURRENT_SENSOR, scale, 0.000001f,
                                       10.0f, now_ms);
        saveCalibration();
      }
    } else if (ok && strcmp(kind, "COOLING") == 0) {
      const float zero = nextFloat(&context, ok);
      const float scale = nextFloat(&context, ok);
      accepted = ok && supervisor.configureCoolingFeedbackCalibration(zero, scale);
      if (accepted) {
        calibration_record.cooling_zero_adc = zero;
        calibration_record.cooling_amps_per_count = scale;
        accepted = recordCommissioned(CAL_COOLING_CURRENT, scale, 0.000001f,
                                       10.0f, now_ms);
        saveCalibration();
      }
    } else if (ok && strcmp(kind, "ACTUATION") == 0) {
      const float roller_mm = nextFloat(&context, ok);
      const float puller_ppr = nextFloat(&context, ok);
      const float screw_ppr = nextFloat(&context, ok);
      const float spooler_ppr = nextFloat(&context, ok);
      const float traverse_steps = nextFloat(&context, ok);
      PullerCalibration puller;
      puller.roller_diameter_mm = roller_mm;
      puller.tach_pulses_per_revolution = puller_ppr;
      puller.maximum_rpm = 160.0f;
      puller.kp = 3.0f;
      puller.ki = 1.2f;
      puller.minimum_useful_pwm = 45;
      puller.maximum_pwm = 255;
      puller.startup_ramp_ms = 800;
      puller.tach_loss_timeout_ms = 600;
      puller.saturation_dwell_ms = 800;
      puller.saturation_error_mm_s = 2.0f;
      accepted = ok && screw_ppr >= 1.0f && spooler_ppr >= 1.0f && traverse_steps > 1.0f &&
          supervisor.configurePullerCalibration(puller);
      if (accepted) {
        calibration_record.puller = puller;
        calibration_record.screw_tach_pulses_per_revolution = screw_ppr;
        calibration_record.spooler_tach_pulses_per_revolution = spooler_ppr;
        calibration_record.traverse_steps_per_mm = traverse_steps;
        calibration_record.traverse = {68.0f, 1.85f, traverse_steps, 1200};
        accepted = recordCommissioned(CAL_PULLER_DRIVE, puller.maximum_rpm, 1.0f, 500.0f, now_ms) &&
            recordCommissioned(CAL_PULLER_TACH, puller_ppr, 0.1f, 4096.0f, now_ms) &&
            recordCommissioned(CAL_SCREW_TACH, screw_ppr, 0.1f, 4096.0f, now_ms) &&
            recordCommissioned(CAL_SPOOLER_TACH, spooler_ppr, 0.1f, 4096.0f, now_ms) &&
            recordCommissioned(CAL_TRAVERSE, traverse_steps, 1.0f, 5000.0f, now_ms);
        saveCalibration();
      }
    } else if (ok && strcmp(kind, "TACH") == 0) {
      char *channel = strtok_r(nullptr, " ", &context);
      const float ppr = nextFloat(&context, ok);
      CalibrationId id = CAL_COUNT;
      if (channel != nullptr && strcmp(channel, "SHREDDER") == 0) id = CAL_SHREDDER_TACH;
      else if (channel != nullptr && strcmp(channel, "SCREW") == 0) id = CAL_SCREW_TACH;
      else if (channel != nullptr && strcmp(channel, "PULLER") == 0) id = CAL_PULLER_TACH;
      else if (channel != nullptr && strcmp(channel, "SPOOLER") == 0) id = CAL_SPOOLER_TACH;
      accepted = ok && id != CAL_COUNT && recordCommissioned(id, ppr, 0.1f, 4096.0f, now_ms);
      if (accepted) {
        if (id == CAL_SHREDDER_TACH) calibration_record.shredder_tach_pulses_per_revolution = ppr;
        else if (id == CAL_SCREW_TACH) calibration_record.screw_tach_pulses_per_revolution = ppr;
        else if (id == CAL_PULLER_TACH) calibration_record.puller.tach_pulses_per_revolution = ppr;
        else calibration_record.spooler_tach_pulses_per_revolution = ppr;
        saveCalibration();
        accepted = configureTachEstimators();
      }
    } else if (ok && strcmp(kind, "FANS") == 0) {
      const float fan1_ppr = nextFloat(&context, ok);
      const float fan2_ppr = nextFloat(&context, ok);
      accepted = ok && recordCommissioned(CAL_FAN1_TACH, fan1_ppr, 0.1f, 100.0f, now_ms) &&
          recordCommissioned(CAL_FAN2_TACH, fan2_ppr, 0.1f, 100.0f, now_ms);
      if (accepted) {
        calibration_record.fan1_tach_pulses_per_revolution = fan1_ppr;
        calibration_record.fan2_tach_pulses_per_revolution = fan2_ppr;
        saveCalibration();
      }
    } else if (ok && strcmp(kind, "DANCER") == 0) {
      const float radians_per_count = nextFloat(&context, ok);
      accepted = ok && supervisor.configureDancerCalibration(radians_per_count) &&
          recordCommissioned(CAL_DANCER, radians_per_count, 0.000001f, 0.1f, now_ms);
      if (accepted) {
        calibration_record.dancer_radians_per_count = radians_per_count;
        saveCalibration();
      }
    } else if (ok && strcmp(kind, "SPOOLER") == 0) {
      const float core_radius = nextFloat(&context, ok);
      const float full_radius = nextFloat(&context, ok);
      const float width = nextFloat(&context, ok);
      const float filament = nextFloat(&context, ok);
      const float max_rpm = nextFloat(&context, ok);
      SpoolerConfig spooler;
      spooler.core_radius_mm = core_radius;
      spooler.full_radius_mm = full_radius;
      spooler.spool_width_mm = width;
      spooler.filament_diameter_mm = filament;
      spooler.dancer_target_rad = 0.0f;
      spooler.kp = 180.0f;
      spooler.ki = 45.0f;
      spooler.minimum_useful_pwm = 42;
      spooler.maximum_pwm = 220;
      spooler.startup_ramp_ms = 1200;
      spooler.jam_dwell_ms = 1000;
      spooler.packing_factor = 0.87f;
      spooler.minimum_stable_rpm = 0.5f;
      spooler.maximum_rpm = max_rpm;
      spooler.speed_kp = 4.0f;
      spooler.speed_ki = 1.0f;
      spooler.tach_loss_timeout_ms = 7500;
      spooler.saturation_dwell_ms = 1200;
      spooler.saturation_error_rpm = 1.0f;
      accepted = ok && supervisor.configureSpoolerDriveCalibration(spooler) &&
          recordCommissioned(CAL_SPOOLER_DRIVE, max_rpm, 0.5f, 30.0f, now_ms);
      if (accepted) {
        calibration_record.spooler = spooler;
        saveCalibration();
      }
    }
    if (accepted) accepted = supervisor.configureCalibrationRecord(calibration_record);
  }
  Serial.println(accepted ? F("COMMAND_OK") : F("COMMAND_REJECTED"));
}

void pollSerial(const InputSnapshot &input, uint32_t now_ms) {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      if (serial_length > 0) {
        serial_line[serial_length] = '\0';
        executeCommand(serial_line, input, now_ms);
        serial_length = 0;
      }
    } else if (serial_length + 1 < sizeof(serial_line)) serial_line[serial_length++] = c;
    else serial_length = 0;
  }
}

bool pressed(uint8_t pin) {
  static uint8_t previous[70]{};
  const uint8_t current = digitalRead(pin);
  const bool falling_edge = previous[pin] == HIGH && current == LOW;
  previous[pin] = current;
  return falling_edge;
}

int8_t encoderDelta() {
  static uint8_t previous = HIGH;
  const uint8_t current = digitalRead(Board::ENCODER_A_PIN);
  int8_t delta = 0;
  if (previous == HIGH && current == LOW) delta = digitalRead(Board::ENCODER_B_PIN) == HIGH ? 1 : -1;
  previous = current;
  return delta;
}

void handlePhysicalUi(InputSnapshot input, uint32_t now_ms) {
  const UiEvent event{encoderDelta(), pressed(Board::START_PIN), pressed(Board::PAUSE_PIN),
                      pressed(Board::BACK_PIN), pressed(Board::CONFIRM_PIN) || pressed(Board::ENCODER_BUTTON_PIN)};
  const bool fault = supervisor.process().state() == MachineState::FAULT ||
                     supervisor.process().state() == MachineState::ESTOP;
  const UiIntent intent = ui.update(event, supervisor.process().state(),
                                    supervisor.process().materialSession(), fault);
  if (intent == UiIntent::APPROVE_PURGE_FEED) {
    if (supervisor.approvePurgeFeed(true)) purge_feed_approved = true;
    return;
  }
  if (event.confirm_pressed && supervisor.extrusionArmRequired()) {
    supervisor.armExtrusion(input, now_ms);
    return;
  }
  if (event.confirm_pressed && supervisor.formingState() == FormingChainState::READY_TO_RETHREAD) {
    supervisor.confirmManualRethread(input);
    return;
  }
  if (intent == UiIntent::SELECT_PLA || intent == UiIntent::SELECT_PET) {
    const MaterialProfile material = intent == UiIntent::SELECT_PLA ? MaterialProfile::PLA : MaterialProfile::PET;
    const bool accepted = supervisor.selectMaterial(material) || supervisor.requestMaterialChange(material, input);
    if (accepted) purge_feed_approved = false;
  } else if (intent == UiIntent::START_SHREDDING) {
    supervisor.requestShredding(input, now_ms);
  } else if (intent == UiIntent::START_EXTRUSION) {
    supervisor.requestPreheat(input);
  } else if (intent == UiIntent::PAUSE || intent == UiIntent::BACK) {
    supervisor.requestStop(input);
    purge_feed_approved = false;
  } else if (intent == UiIntent::CLEAR_FAULT) {
    if (supervisor.clearAllFaults(input, input.safety.restart_permission)) purge_feed_approved = false;
  } else if (intent == UiIntent::CONFIRM) {
    const MaterialSession session = supervisor.process().materialSession();
    if (session == MaterialSession::PURGE_PREHEAT_REQUIRED) supervisor.requestPurgePreheat(input);
    else if (session == MaterialSession::PURGE_READY_CONFIRM_REQUIRED) {
      input.purge_feed_approved = purge_feed_approved;
      input.purge_waste_path_confirmed = true;
      supervisor.confirmPurgeWastePath(input, now_ms);
    } else if (session == MaterialSession::PURGE_RUNNING) {
      if (supervisor.confirmPurgeComplete(true, input, now_ms)) purge_feed_approved = false;
    } else {
      supervisor.acknowledgeMaterialStep(session, true);
    }
  }
}

void sampleTachs(uint32_t now_ms) {
  if (now_ms - last_tach_sample_ms < 20) return;
  const uint32_t now_us = micros();
  noInterrupts();
  shredder_tach_sample = shredder_tach.estimate(now_us);
  puller_tach_sample = puller_tach.estimate(now_us);
  screw_tach_sample = screw_tach.estimate(now_us);
  spooler_tach_sample = spooler_tach.estimate(now_us);
  interrupts();
  shredder_rpm = shredder_tach_sample.rpm;
  puller_rpm = puller_tach_sample.rpm;
  screw_rpm = screw_tach_sample.rpm;
  spooler_rpm = spooler_tach_sample.rpm;
  last_tach_sample_ms = now_ms;
}

void sampleFans(uint32_t now_ms) {
  if (now_ms - last_fan_sample_ms < 250) return;
  const bool completed_channel = fan_mux_channel;
  noInterrupts();
  const uint32_t count = fan_pulses[completed_channel ? 1 : 0];
  fan_pulses[completed_channel ? 1 : 0] = 0;
  interrupts();
  const CalibrationId fan_id = completed_channel ? CAL_FAN2_TACH : CAL_FAN1_TACH;
  const float fan_ppr = calibrationDomainReady(calibration_record, fan_id)
      ? calibration_record.records[fan_id].value : 0.0f;
  fan_rpm[completed_channel ? 1 : 0] = fan_ppr > 0 ? count * 60.0f / (fan_ppr * 0.25f) : 0.0f;
  fan_mux_channel = !fan_mux_channel;
  digitalWrite(Board::FAN_TACH_MUX_SELECT_PIN, fan_mux_channel ? HIGH : LOW);
  last_fan_sample_ms = now_ms;
}

void sampleTemperatures(uint32_t now_ms) {
  if (now_ms - last_temperature_sample_ms < HEATER_SAMPLE_PERIOD_MS) return;
  for (uint8_t channel = 0; channel < 5; ++channel)
    temperatures[channel] = thermocouples.read(static_cast<TemperatureChannel>(channel), now_ms);
  last_temperature_sample_ms = now_ms;
}

long milli(float value) {
  return static_cast<long>(value * 1000.0f);
}

void formatTelemetrySegment() {
  const MachineViewState &v = telemetry_snapshot.view;
  int written = 0;
  switch (telemetry_segment) {
    case 0:
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "ts=%lu phase=%u ui=%u session=%u forming=%u fault=%u fault_ms=%lu state_ms=%lu ",
          static_cast<unsigned long>(telemetry_snapshot_ms), static_cast<unsigned>(v.process_phase),
          static_cast<unsigned>(v.ui_state), static_cast<unsigned>(v.material_session),
          static_cast<unsigned>(v.forming_chain_state), static_cast<unsigned>(v.forming_fault_reasons),
          static_cast<unsigned long>(v.forming_fault_detected_ms),
          static_cast<unsigned long>(v.forming_state_changed_ms));
      break;
    case 1:
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "spool_eligible=%u waste_mode=%u waste_path=%u cal=%u/%u/%u/%u/%u cooling_feedback=%u ",
          v.spool_eligible, v.waste_mode, telemetry_snapshot.actuators.waste_path_active,
          v.calibration.drive_calibration_valid, v.calibration.gauge_calibration_valid,
          v.calibration.current_sensor_calibration_valid,
          v.calibration.cooling_feedback_calibration_valid,
          v.calibration.temperature_channels_valid, v.cooling_feedback_valid);
      break;
    case 2:
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "puller_mm_s_milli=%ld/%ld puller_rpm_milli=%ld/%ld puller_error_milli=%ld ",
          milli(v.puller.target_mm_s), milli(v.puller.measured_mm_s), milli(v.puller.target_rpm),
          milli(v.puller.measured_rpm), milli(v.puller.speed_error_mm_s));
      break;
    case 3:
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "puller_pwm=%d puller_sat=%u puller_tach=%u puller_limited=%u puller_sat_ms=%lu ",
          v.puller.pwm, v.puller.saturated, v.puller.tach_valid, v.puller.pwm_limited,
          static_cast<unsigned long>(v.puller.saturation_duration_ms));
      break;
    case 4:
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "screw_rpm_milli=%ld screw_rev_milli=%ld screw_tach=%u screw_mismatch=%u fans=%u/%u fan_fault=%u ",
          milli(v.screw_motion.actual_rpm), milli(v.screw_motion.cumulative_revolutions),
          v.screw_motion.tach_valid, v.screw_motion.command_motion_mismatch,
          v.cooling.fan1_running, v.cooling.fan2_running, v.cooling.fault_bits);
      break;
    case 5:
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "spooler_pwm=%d radius_milli=%ld spool_rpm_milli=%ld/%ld turns_milli=%ld spool_tach=%u jam=%u ",
          v.spooler.pwm, milli(v.spooler.estimated_radius_mm), milli(v.spooler.target_rpm),
          milli(v.spooler.measured_rpm), milli(v.spooler.cumulative_turns),
          v.spooler.tach_valid, v.spooler.jam);
      break;
    case 6:
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "traverse=%u/%u/%u target_milli=%ld pos_milli=%ld hard_fault=%u pitch_sync=%u requal_samples=%u ",
          v.traverse.enable, v.traverse.direction, v.traverse.step,
          milli(v.traverse.target_position_mm), milli(v.traverse.estimated_position_mm),
          v.traverse.hard_fault, v.traverse.pitch_synchronized,
          static_cast<unsigned>(v.requalification_valid_samples));
      break;
    case 7:
    case 8:
    case 9:
    case 10: {
      const uint8_t zone = telemetry_segment - 7;
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "heater%u_milli=%ld/%ld/%ld/%ld sat=%u on=%u ", static_cast<unsigned>(zone),
          milli(v.heater_allocation.requested_duty[zone]),
          milli(v.heater_allocation.allocated_duty[zone]),
          milli(v.heater_allocation.allocation_deficit[zone]),
          milli(v.heater_allocation.integrator_state[zone]),
          v.heater_allocation.saturated[zone],
          v.heater_allocation.actual_time_proportion_command[zone]);
      break;
    }
    default:
#ifdef PPR_DEBUG
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "cooling_probe=%u/%lu/%lu purge=%u/%u invariants=%u deadline_overruns=%lu max_loop_us=%lu\n",
          static_cast<unsigned>(v.cooling_startup_request),
          static_cast<unsigned long>(v.cooling_startup_probe_elapsed_ms),
          static_cast<unsigned long>(v.cooling_startup_healthy_dwell_ms),
          v.purge_feed_approved, v.purge_run_completed, telemetry_snapshot.invariants_ok,
          static_cast<unsigned long>(deadline_overruns), static_cast<unsigned long>(maximum_loop_us));
#else
      written = snprintf(telemetry_buffer, sizeof(telemetry_buffer),
          "cooling_probe=%u/%lu/%lu purge=%u/%u invariants=%u\n",
          static_cast<unsigned>(v.cooling_startup_request),
          static_cast<unsigned long>(v.cooling_startup_probe_elapsed_ms),
          static_cast<unsigned long>(v.cooling_startup_healthy_dwell_ms),
          v.purge_feed_approved, v.purge_run_completed, telemetry_snapshot.invariants_ok);
#endif
      break;
  }
  telemetry_length = written <= 0 ? 0 : static_cast<uint8_t>(
      written < static_cast<int>(sizeof(telemetry_buffer)) ? written : sizeof(telemetry_buffer) - 1);
  telemetry_offset = 0;
}

void logStatus(const SupervisorOutput &output, uint32_t now_ms) {
  if (!telemetry_active) {
    if (now_ms - last_log_ms < 1000) return;
    last_log_ms = now_ms;
    telemetry_snapshot_ms = now_ms;
    telemetry_snapshot = output;
    telemetry_segment = 0;
    telemetry_active = true;
  }
  if (telemetry_length == 0) formatTelemetrySegment();
  const int available = Serial.availableForWrite();
  if (available <= 0 || telemetry_length == 0) return;
  const uint8_t remaining = telemetry_length - telemetry_offset;
  const uint8_t write_count = remaining < available ? remaining : static_cast<uint8_t>(available);
  Serial.write(reinterpret_cast<const uint8_t *>(telemetry_buffer + telemetry_offset), write_count);
  telemetry_offset += write_count;
  if (telemetry_offset < telemetry_length) return;
  telemetry_length = 0;
  if (++telemetry_segment > 11) telemetry_active = false;
}
}

void setup() {
  Serial.begin(115200);
  for (uint8_t pin : Board::SAFETY_INPUT_PINS) pinMode(pin, INPUT_PULLUP);
  for (uint8_t pin : Board::DRIVER_FAULT_PINS) pinMode(pin, INPUT_PULLUP);
  for (uint8_t pin : Board::THERMOCOUPLE_CS_PINS) { pinMode(pin, OUTPUT); digitalWrite(pin, HIGH); }
  pinMode(Board::THERMOCOUPLE_SO_PIN, INPUT);
  pinMode(Board::THERMOCOUPLE_SCK_PIN, OUTPUT);
  for (uint8_t pin : Board::HEATER_PINS) pinMode(pin, OUTPUT);
  for (uint8_t pin : Board::MOTOR_PWM_PINS) pinMode(pin, OUTPUT);
  const uint8_t inputs[] = {Board::START_PIN, Board::PAUSE_PIN, Board::BACK_PIN, Board::CONFIRM_PIN,
                            Board::ENCODER_BUTTON_PIN, Board::ENCODER_A_PIN, Board::ENCODER_B_PIN,
                            Board::GAUGE_VALID_PIN, Board::LOCKOUT_CONFIRM_PIN,
                            Board::TRAVERSE_LEFT_LIMIT_PIN, Board::TRAVERSE_RIGHT_LIMIT_PIN,
                            Board::SCREW_TACH_PIN, Board::FAN_TACH_MUX_PIN, Board::SPOOLER_TACH_PIN};
  for (uint8_t pin : inputs) pinMode(pin, INPUT_PULLUP);
  const uint8_t outputs[] = {Board::SHREDDER_DIR_PIN, Board::SHREDDER_REVERSE_PIN, Board::SHREDDER_ENABLE_PIN,
                             Board::FEEDER_ENABLE_PIN, Board::SCREW_DIR_PIN, Board::SCREW_ENABLE_PIN,
                             Board::PULLER_DIR_PIN, Board::PULLER_ENABLE_PIN, Board::SPOOLER_DIR_PIN,
                             Board::SPOOLER_ENABLE_PIN, Board::TRAVERSE_STEP_PIN, Board::TRAVERSE_DIR_PIN,
                             Board::TRAVERSE_ENABLE_PIN, Board::HOPPER_PTC_PIN};
  for (uint8_t pin : outputs) pinMode(pin, OUTPUT);
  pinMode(Board::FAN_TACH_MUX_SELECT_PIN, OUTPUT);
  digitalWrite(Board::FAN_TACH_MUX_SELECT_PIN, LOW);
  pinMode(Board::SHREDDER_RPM_PIN, INPUT_PULLUP);
  pinMode(Board::PULLER_TACH_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(Board::SHREDDER_RPM_PIN), shredderPulse, RISING);
  attachInterrupt(digitalPinToInterrupt(Board::PULLER_TACH_PIN), pullerPulse, RISING);
  portk_previous = PINK;
  PCICR |= _BV(PCIE2);
  PCMSK2 |= _BV(5) | _BV(6) | _BV(7);
  const bool loaded = loadCalibration();
  if (!loaded) configureTachEstimators();
  Serial.print(F("PPR ")); Serial.print(ACTUATION_REVISION); Serial.print(F(" base="));
  Serial.print(CONFIG_REVISION); Serial.println(F(" READY SERIAL_TEXT_BACKEND"));
  Serial.println(loaded ? F("CALIBRATION_RECORD_V4_LOADED") : F("CALIBRATION_REQUIRED_OUTPUTS_INHIBITED"));
  Serial.println(F("MATERIAL_SELECTION_REQUIRED"));
}

void loop() {
#ifdef PPR_DEBUG
  const uint32_t loop_started_us = micros();
#endif
  const uint32_t now_ms = millis();
  sampleTachs(now_ms);
  sampleFans(now_ms);
  sampleTemperatures(now_ms);
  const InputSnapshot input = readInputs(now_ms);
  pollSerial(input, now_ms);
  handlePhysicalUi(input, now_ms);
  const SupervisorOutput output = supervisor.update(input, now_ms);
  last_commands = output.invariants_ok ? output.actuators : ActuatorCommands{};
  actuators.apply(last_commands);
  logStatus(output, now_ms);
#ifdef PPR_DEBUG
  const uint32_t loop_us = micros() - loop_started_us;
  if (loop_us > maximum_loop_us) maximum_loop_us = loop_us;
  if (loop_us > 10000UL) ++deadline_overruns;
#endif
}
