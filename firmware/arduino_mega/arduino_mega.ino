#include <EEPROM.h>
#include <stdlib.h>
#include <string.h>

#include "src/board_config.h"
#include "src/gauge_control.h"
#include "src/heater_control.h"
#include "src/process_state.h"
#include "src/shredder_control.h"
#include "src/ui_core.h"

namespace {
ProcessController process;
ShredderController shredder;
HeaterController heaterController;
GaugeController gaugeController;
DiameterController diameterController;
UiController ui;
MaterialProfile selected = MaterialProfile::PLA;
DriveCalibration driveCalibration = REFERENCE_DRIVE_CALIBRATION;
TemperatureReading temperatures[5]{};
ActuatorCommands commands{};
volatile uint32_t shredderPulses = 0;
volatile uint32_t pullerPulses = 0;
float shredderRPM = 0;
float pullerRPM = 0;
uint32_t lastSampleMs = 0;
uint32_t lastGaugeMs = 0;
uint32_t lastLogMs = 0;
uint32_t gaugePauseStartMs = 0;
bool gaugePause = false;
float currentZeroAdc = 0;
float currentAmpsPerCount = 0;
GaugeCalibration storedGaugeCalibration{0, 0, 0, 0, 1, false};
char serialLine[180]{};
uint8_t serialLength = 0;

struct CalibrationRecord {
  uint32_t magic;
  uint16_t version;
  GaugeCalibration gauge;
  DriveCalibration drive;
  float current_zero_adc;
  float current_amps_per_count;
  uint32_t crc;
};

constexpr uint32_t CALIBRATION_MAGIC = 0x50505236UL;
constexpr uint16_t CALIBRATION_VERSION = 1;

uint32_t calibrationCrc(const CalibrationRecord &record) {
  const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&record);
  uint32_t hash = 2166136261UL;
  for (size_t i = 0; i < sizeof(record) - sizeof(record.crc); ++i) hash = (hash ^ bytes[i]) * 16777619UL;
  return hash;
}

bool loadCalibration() {
  CalibrationRecord record{};
  EEPROM.get(0, record);
  if (record.magic != CALIBRATION_MAGIC || record.version != CALIBRATION_VERSION || record.crc != calibrationCrc(record)) return false;
  bool loaded = false;
  if (gaugeController.setCalibration(record.gauge)) {
    storedGaugeCalibration = record.gauge;
    loaded = true;
  }
  if (record.current_amps_per_count > 0 && record.current_zero_adc >= 0 && record.current_zero_adc <= 1023 && shredder.configureDrive(record.drive)) {
    driveCalibration = record.drive;
    currentZeroAdc = record.current_zero_adc;
    currentAmpsPerCount = record.current_amps_per_count;
    loaded = true;
  }
  return loaded;
}

void saveCalibration(const GaugeCalibration &gauge, const DriveCalibration &drive,
                     float zero_adc, float amps_per_count) {
  CalibrationRecord record{CALIBRATION_MAGIC, CALIBRATION_VERSION, gauge, drive, zero_adc, amps_per_count, 0};
  record.crc = calibrationCrc(record);
  EEPROM.put(0, record);
}

float nextFloat(char **context, bool &ok) {
  char *token = strtok_r(nullptr, " ", context);
  if (token == nullptr) { ok = false; return 0; }
  return static_cast<float>(atof(token));
}

void logStatus(uint32_t now);

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

void setSignedMotor(uint8_t pwmPin, uint8_t dirPin, uint8_t enablePin, int16_t value) {
  const uint8_t duty = static_cast<uint8_t>(constrain(abs(value), 0, 255));
  digitalWrite(dirPin, value >= 0 ? HIGH : LOW);
  digitalWrite(enablePin, duty > 0 ? HIGH : LOW);
  analogWrite(pwmPin, duty);
}

class BoardActuators final : public ActuatorBackend {
 public:
  void apply(const ActuatorCommands &c) override {
    digitalWrite(Board::SHREDDER_DIR_PIN, c.shredder_pwm >= 0 ? HIGH : LOW);
    digitalWrite(Board::SHREDDER_REVERSE_PIN, c.shredder_pwm < 0 ? HIGH : LOW);
    digitalWrite(Board::SHREDDER_ENABLE_PIN, c.shredder_pwm != 0 ? HIGH : LOW);
    analogWrite(Board::SHREDDER_PWM_PIN, constrain(abs(c.shredder_pwm), 0, 255));
    setSignedMotor(Board::SCREW_PWM_PIN, Board::SCREW_DIR_PIN, Board::SCREW_ENABLE_PIN, c.screw_pwm);
    setSignedMotor(Board::PULLER_PWM_PIN, Board::PULLER_DIR_PIN, Board::PULLER_ENABLE_PIN, c.puller_pwm);
    setSignedMotor(Board::SPOOLER_PWM_PIN, Board::SPOOLER_DIR_PIN, Board::SPOOLER_ENABLE_PIN, c.spooler_pwm);
    analogWrite(Board::COOLING_PWM_PIN, c.cooling_pwm);
    digitalWrite(Board::TRAVERSE_DIR_PIN, c.traverse_direction ? HIGH : LOW);
    digitalWrite(Board::TRAVERSE_ENABLE_PIN, c.traverse_enable ? HIGH : LOW);
    digitalWrite(Board::TRAVERSE_STEP_PIN, c.traverse_step ? HIGH : LOW);
    for (uint8_t zone = 0; zone < 4; ++zone) digitalWrite(Board::HEATER_PINS[zone], c.heater_on[zone] ? HIGH : LOW);
    digitalWrite(Board::HOPPER_PTC_PIN, c.hopper_ptc_on ? HIGH : LOW);
  }
} actuators;

void shredderPulse() { ++shredderPulses; }
void pullerPulse() { ++pullerPulses; }

bool allDriversHealthy() {
  for (uint8_t pin : Board::DRIVER_FAULT_PINS) if (digitalRead(pin) == LOW) return false;
  return true;
}

bool temperaturesReady() {
  const auto &profile = profileFor(selected);
  const float targets[4] = {static_cast<float>(profile.zone_c[0]), static_cast<float>(profile.zone_c[1]), static_cast<float>(profile.zone_c[2]), static_cast<float>(profile.die_c)};
  for (uint8_t i = 0; i < 4; ++i) if (!temperatures[i].valid || abs(temperatures[i].celsius - targets[i]) > 5.0f) return false;
  return true;
}

SafetyInputs safetyInputs() {
  const auto &gauge = gaugeController.reading();
  return {digitalRead(Board::ESTOP_PIN) == HIGH,
          digitalRead(Board::LID_PIN) == HIGH,
          digitalRead(Board::SERVICE_GUARD_PIN) == HIGH,
          digitalRead(Board::THERMAL_CHAIN_PIN) == HIGH,
          temperaturesReady(), gauge.valid, digitalRead(Board::LOCKOUT_CONFIRM_PIN) == LOW, allDriversHealthy(),
          digitalRead(Board::HEATER_PERMISSION_FEEDBACK_PIN) == HIGH};
}

bool pressed(uint8_t pin) {
  static uint8_t prior[70]{};
  const uint8_t now = digitalRead(pin);
  const bool edge = prior[pin] == HIGH && now == LOW;
  prior[pin] = now;
  return edge;
}

int8_t encoderDelta() {
  static uint8_t previous = HIGH;
  const uint8_t now = digitalRead(Board::ENCODER_A_PIN);
  if (previous == HIGH && now == LOW) {
    previous = now;
    return digitalRead(Board::ENCODER_B_PIN) == HIGH ? 1 : -1;
  }
  previous = now;
  return 0;
}

void handleUi(const SafetyInputs &safety) {
  UiEvent event{encoderDelta(), pressed(Board::START_PIN), pressed(Board::PAUSE_PIN),
                pressed(Board::BACK_PIN), pressed(Board::CONFIRM_PIN) || pressed(Board::ENCODER_BUTTON_PIN)};
  const UiIntent intent = ui.update(event, process.state(), process.materialSession(), process.state() == MachineState::FAULT || process.state() == MachineState::ESTOP);
  if (intent == UiIntent::SELECT_PLA || intent == UiIntent::SELECT_PET) {
    const MaterialProfile next = intent == UiIntent::SELECT_PLA ? MaterialProfile::PLA : MaterialProfile::PET;
    if (!process.selectMaterial(next)) process.requestMaterialChange(next, safety);
    selected = process.material();
  } else if (intent == UiIntent::CONFIRM) {
    process.acknowledgeMaterialStep(process.materialSession(), true);
    selected = process.material();
  } else if (intent == UiIntent::START_SHREDDING) {
    if (process.requestState(MachineState::SHREDDING, safety)) shredder.start(profileFor(selected), {millis(), 0, shredderRPM, true, false});
  } else if (intent == UiIntent::START_EXTRUSION) {
    process.requestState(MachineState::PREHEATING, safety);
  } else if (intent == UiIntent::PAUSE) {
    if (process.state() == MachineState::SHREDDING) process.requestState(MachineState::IDLE, safety);
    else if (process.state() == MachineState::PREHEATING || process.state() == MachineState::EXTRUSION) process.requestState(MachineState::COOLDOWN, safety);
  } else if (intent == UiIntent::CLEAR_FAULT) {
    process.clearFault(safety, safety.restart_permission);
  }
}

void executeSerialCommand(char *line) {
  char *context = nullptr;
  char *verb = strtok_r(line, " ", &context);
  if (verb == nullptr) return;
  if (strcmp(verb, "STATUS") == 0) {
    logStatus(millis() + 1000);
    return;
  }
  if (strcmp(verb, "ACK") == 0) {
    Serial.println(process.acknowledgeMaterialStep(process.materialSession(), true) ? F("ACK_OK") : F("ACK_REJECTED"));
    selected = process.material();
    return;
  }
  if (strcmp(verb, "MATERIAL") == 0) {
    char *name = strtok_r(nullptr, " ", &context);
    const MaterialProfile next = name != nullptr && strcmp(name, "PET") == 0 ? MaterialProfile::PET : MaterialProfile::PLA;
    const auto safety = safetyInputs();
    const bool accepted = process.selectMaterial(next) || process.requestMaterialChange(next, safety);
    Serial.println(accepted ? F("MATERIAL_REQUEST_OK") : F("MATERIAL_REQUEST_REJECTED"));
    selected = process.material();
    return;
  }
  if (strcmp(verb, "CLEAR") == 0) {
    const auto safety = safetyInputs();
    Serial.println(process.clearFault(safety, safety.restart_permission) ? F("FAULT_CLEAR_OK") : F("FAULT_CLEAR_REQUIRES_PHYSICAL_LOCKOUT_KEY"));
    return;
  }
  if (strcmp(verb, "CAL") != 0) { Serial.println(F("UNKNOWN_COMMAND")); return; }
  char *kind = strtok_r(nullptr, " ", &context);
  bool ok = kind != nullptr;
  if (ok && strcmp(kind, "GAUGE") == 0) {
    GaugeCalibration gauge{nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), true};
    ok = ok && gaugeController.setCalibration(gauge);
    if (ok) {
      storedGaugeCalibration = gauge;
      saveCalibration(storedGaugeCalibration, driveCalibration, currentZeroAdc, currentAmpsPerCount);
    }
    Serial.println(ok ? F("CAL_GAUGE_SAVED") : F("CAL_GAUGE_REJECTED_U95_OR_SCALE"));
  } else if (ok && strcmp(kind, "DRIVE") == 0) {
    const float zero = nextFloat(&context, ok);
    const float ampsPerCount = nextFloat(&context, ok);
    DriveCalibration drive{nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok),
                           nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), nextFloat(&context, ok), true};
    ok = ok && zero >= 0 && zero <= 1023 && ampsPerCount > 0 && shredder.configureDrive(drive);
    if (ok) {
      driveCalibration = drive;
      currentZeroAdc = zero;
      currentAmpsPerCount = ampsPerCount;
      saveCalibration(storedGaugeCalibration, driveCalibration, currentZeroAdc, currentAmpsPerCount);
    }
    Serial.println(ok ? F("CAL_DRIVE_SAVED") : F("CAL_DRIVE_REJECTED"));
  } else {
    Serial.println(F("CAL_USAGE GAUGE xo xs yo ys u95 | DRIVE adc0 A_per_count no_load_A Nm_per_A ratio efficiency continuous_A peak_A no_load_rpm thermal_C"));
  }
}

void pollSerial() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      if (serialLength > 0) {
        serialLine[serialLength] = '\0';
        executeSerialCommand(serialLine);
        serialLength = 0;
      }
    } else if (serialLength + 1 < sizeof(serialLine)) {
      serialLine[serialLength++] = c;
    } else {
      serialLength = 0;
      Serial.println(F("COMMAND_TOO_LONG"));
    }
  }
}

void sampleInputs(uint32_t now) {
  if (now - lastSampleMs >= HEATER_SAMPLE_PERIOD_MS) {
    const float dt = (now - lastSampleMs) / 1000.0f;
    noInterrupts();
    const uint32_t s = shredderPulses; shredderPulses = 0;
    const uint32_t p = pullerPulses; pullerPulses = 0;
    interrupts();
    shredderRPM = s * 60.0f / (7.0f * dt);
    pullerRPM = p * 60.0f / (20.0f * dt);
    for (uint8_t i = 0; i < 5; ++i) temperatures[i] = thermocouples.read(static_cast<TemperatureChannel>(i), now);
    lastSampleMs = now;
  }
  if (now - lastGaugeMs >= 100) {
    gaugeController.update(analogRead(Board::GAUGE_X_PIN), analogRead(Board::GAUGE_Y_PIN), digitalRead(Board::GAUGE_VALID_PIN) == HIGH);
    lastGaugeMs = now;
  }
}

void buildCommands(const SafetyInputs &safety, uint32_t now) {
  commands = {};
  const auto &permission = process.permissions();
  const auto &profile = profileFor(selected);
  const auto &gauge = gaugeController.reading();

  if (process.state() == MachineState::EXTRUSION && !gauge.valid && !gaugePause) {
    gaugePause = true;
    gaugePauseStartMs = now;
  }
  if (gaugePause && now - gaugePauseStartMs >= 60000) process.requestState(MachineState::COOLDOWN, safety);
  if (process.state() != MachineState::EXTRUSION) gaugePause = false;

  if (permission.shredder) {
    const float currentA = currentAmpsPerCount > 0 ? abs(analogRead(Board::CURRENT_PIN) - currentZeroAdc) * currentAmpsPerCount : 0;
    const auto output = shredder.update({now, currentA, shredderRPM, safety.driver_fault_free, permission.process_heaters || permission.screw});
    if (output.command == ShredderCommand::FORWARD || output.command == ShredderCommand::OVERLOAD_DWELL || output.command == ShredderCommand::REVERSE) {
      const float bias = selected == MaterialProfile::PET ? PET_SHREDDER_DUTY_BIAS : PLA_SHREDDER_DUTY_BIAS;
      const float kp = selected == MaterialProfile::PET ? PET_SHREDDER_SPEED_KP : PLA_SHREDDER_SPEED_KP;
      const float duty = constrain(bias + kp * (output.target_rpm - abs(shredderRPM)), 0.0f, 0.90f);
      commands.shredder_pwm = static_cast<int16_t>(duty * 255.0f) * (output.command == ShredderCommand::REVERSE ? -1 : 1);
    }
    else if (output.command == ShredderCommand::FAULT_LATCHED) process.reportFault();
  }

  if (permission.screw && safety.driver_fault_free) {
    const float ramp = gaugePause ? constrain(1.0f - (now - gaugePauseStartMs) / 10000.0f, 0.0f, 1.0f) : 1.0f;
    commands.screw_pwm = static_cast<int16_t>(160.0f * ramp);
  }
  const float pullerMmS = diameterController.update(gauge, 1.75f, profile.puller_feedforward_mm_s,
                                                    profile.diameter_kp, profile.diameter_ki, 0.1f);
  if (permission.puller && !gaugePause && pullerMmS > 0) commands.puller_pwm = static_cast<int16_t>(constrain(pullerMmS / 80.0f * 255.0f, 0.0f, 255.0f));
  const int dancerError = analogRead(Board::DANCER_PIN) - 512;
  const bool dancerSafe = abs(dancerError) < 410;
  if (permission.spooler && !gaugePause && dancerSafe) commands.spooler_pwm = constrain(96 + dancerError / 4, 30, 180);
  commands.traverse_enable = permission.spooler && !gaugePause && dancerSafe;
  commands.traverse_direction = ((now / 4000UL) & 1U) != 0;
  commands.traverse_step = commands.traverse_enable && ((now / 10UL) & 1U) != 0;
  commands.cooling_pwm = permission.cooling ? static_cast<uint8_t>(profile.fan_percent * 255 / 100) : 0;

  const bool phaseHeater = permission.process_heaters && processHeaterPhaseAllowed(process.state());
  const float targets[4] = {static_cast<float>(profile.zone_c[0]), static_cast<float>(profile.zone_c[1]), static_cast<float>(profile.zone_c[2]), static_cast<float>(profile.die_c)};
  for (uint8_t zone = 0; zone < 4; ++zone) {
    const float safeTarget = gaugePause ? targets[zone] - 20.0f : targets[zone];
    const auto output = heaterController.update(zone, temperatures[zone], safeTarget, phaseHeater,
                                                safety.thermal_chain_ok, safety.heater_permission_feedback, now);
    commands.heater_on[zone] = output.time_proportion_on;
    if (output.fault_bits != HEATER_FAULT_NONE) process.reportFault();
  }
  commands.hopper_ptc_on = ui.screen() == UiScreen::MAINTENANCE && safety.thermal_chain_ok && process.state() == MachineState::IDLE;
}

void logStatus(uint32_t now) {
  if (now - lastLogMs < 1000) return;
  lastLogMs = now;
  const auto &g = gaugeController.reading();
  Serial.print(F("phase=")); Serial.print(static_cast<uint8_t>(process.state()));
  Serial.print(F(" materialSession=")); Serial.print(static_cast<uint8_t>(process.materialSession()));
  Serial.print(F(" rpm=")); Serial.print(shredderRPM, 1);
  Serial.print(F(" pullerRPM=")); Serial.print(pullerRPM, 1);
  Serial.print(F(" T=")); for (uint8_t i = 0; i < 5; ++i) { Serial.print(temperatures[i].celsius, 1); Serial.print(i == 4 ? ' ' : '/'); }
  Serial.print(F(" gauge=")); Serial.print(g.mean_mm, 3);
  Serial.print(F(" ovality=")); Serial.print(g.ovality_mm, 3);
  Serial.print(F(" U95=")); Serial.print(g.u95_mm, 3);
  Serial.print(F(" valid=")); Serial.println(g.valid ? F("1") : F("0"));
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
  const uint8_t inputPins[] = {Board::START_PIN, Board::PAUSE_PIN, Board::BACK_PIN, Board::CONFIRM_PIN, Board::ENCODER_BUTTON_PIN, Board::ENCODER_A_PIN, Board::ENCODER_B_PIN, Board::GAUGE_VALID_PIN, Board::LOCKOUT_CONFIRM_PIN};
  for (uint8_t pin : inputPins) pinMode(pin, INPUT_PULLUP);
  const uint8_t outputPins[] = {Board::SHREDDER_DIR_PIN, Board::SHREDDER_REVERSE_PIN, Board::SHREDDER_ENABLE_PIN, Board::SCREW_DIR_PIN, Board::SCREW_ENABLE_PIN, Board::PULLER_DIR_PIN, Board::PULLER_ENABLE_PIN, Board::SPOOLER_DIR_PIN, Board::SPOOLER_ENABLE_PIN, Board::TRAVERSE_STEP_PIN, Board::TRAVERSE_DIR_PIN, Board::TRAVERSE_ENABLE_PIN, Board::HOPPER_PTC_PIN};
  for (uint8_t pin : outputPins) pinMode(pin, OUTPUT);
  pinMode(Board::SHREDDER_RPM_PIN, INPUT_PULLUP);
  pinMode(Board::PULLER_TACH_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(Board::SHREDDER_RPM_PIN), shredderPulse, RISING);
  attachInterrupt(digitalPinToInterrupt(Board::PULLER_TACH_PIN), pullerPulse, RISING);
  process.selectMaterial(selected);
  const bool calibrationLoaded = loadCalibration();
  Serial.print(F("PPR ")); Serial.print(CONFIG_REVISION); Serial.println(F(" READY SERIAL_TEXT_BACKEND"));
  Serial.println(calibrationLoaded ? F("CALIBRATION_RECORD_LOADED") : F("CALIBRATION_REQUIRED_OUTPUTS_INHIBITED"));
}

void loop() {
  const uint32_t now = millis();
  pollSerial();
  sampleInputs(now);
  const auto safety = safetyInputs();
  if (!safety.estop_ok) process.requestState(MachineState::ESTOP, safety);
  else if (!safety.lid_closed || !safety.service_guard_closed || !safety.thermal_chain_ok || !safety.driver_fault_free) process.reportFault();
  handleUi(safety);
  if (process.state() == MachineState::PREHEATING && safety.temperatures_ready && safety.gauge_valid) process.requestState(MachineState::EXTRUSION, safety);
  buildCommands(safety, now);
  actuators.apply(commands);
  logStatus(now);
}
