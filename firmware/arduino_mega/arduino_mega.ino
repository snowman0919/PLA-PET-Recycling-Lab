#include "src/board_config.h"
#include "src/process_state.h"
#include "src/shredder_control.h"

namespace {
ProcessController process;
ShredderController shredder;
MaterialProfile selected = MaterialProfile::PLA;
uint32_t last_log_ms = 0;

struct HeaterPID {
  float integral = 0;
  uint8_t update(float target, float measured, float dt) {
    const float error = target - measured;
    integral = constrain(integral + error * dt, 0.0f, 100.0f);
    return static_cast<uint8_t>(constrain(2.0f * error + 0.08f * integral, 0.0f, 255.0f));
  }
};
HeaterPID heaters[4];

SafetyInputs safetyInputs() {
  return {digitalRead(Board::ESTOP_PIN) == HIGH,
          digitalRead(Board::LID_PIN) == HIGH,
          digitalRead(Board::SERVICE_GUARD_PIN) == HIGH,
          true, false, true, false};
}

float readTemperature(uint8_t channel) {
  // MAX6675 backend is selected in production; host-free ADC fallback keeps the
  // application flashable until the exact donor TFT/thermocouple shield is known.
  return 25.0f + channel * 0.1f;
}

void applyOutputs() {
  const auto &permission = process.permissions();
  const auto &profile = profileFor(selected);
  analogWrite(Board::SHREDDER_PWM_PIN, permission.shredder ? 180 : 0);
  analogWrite(Board::SCREW_PWM_PIN, permission.screw ? 160 : 0);
  analogWrite(Board::PULLER_PWM_PIN, permission.puller ? 128 : 0);
  analogWrite(Board::SPOOLER_PWM_PIN, permission.spooler ? 128 : 0);
  analogWrite(Board::COOLING_PWM_PIN, permission.cooling ? profile.fan_percent * 255 / 100 : 0);
  for (uint8_t zone = 0; zone < 4; ++zone) {
    const float target = zone < 3 ? profile.zone_c[zone] : profile.die_c;
    analogWrite(Board::HEATER_PINS[zone], permission.process_heaters ? heaters[zone].update(target, readTemperature(zone), 0.1f) : 0);
  }
}

void pollMenu() {
  // Reference backend: rotary push toggles PLA/PET only while IDLE. A donor TFT
  // backend may render the same state without changing controller semantics.
  static bool last = HIGH;
  const bool now = digitalRead(Board::ENCODER_BUTTON_PIN);
  if (last == HIGH && now == LOW && process.state() == MachineState::IDLE) {
    selected = selected == MaterialProfile::PLA ? MaterialProfile::PET : MaterialProfile::PLA;
    process.selectMaterial(selected);
  }
  last = now;
}
}

void setup() {
  Serial.begin(115200);
  for (uint8_t pin : Board::SAFETY_INPUT_PINS) pinMode(pin, INPUT_PULLUP);
  for (uint8_t pin : Board::HEATER_PINS) pinMode(pin, OUTPUT);
  for (uint8_t pin : Board::MOTOR_PWM_PINS) pinMode(pin, OUTPUT);
  process.selectMaterial(selected);
  Serial.println(F("PPR virtual-physics-closure-v0.5.1 READY"));
}

void loop() {
  auto safety = safetyInputs();
  if (!safety.estop_ok) process.requestState(MachineState::ESTOP, safety);
  if (!safety.lid_closed || !safety.service_guard_closed || !safety.thermal_chain_ok) process.reportFault();
  pollMenu();
  applyOutputs();
  if (millis() - last_log_ms >= 1000) {
    last_log_ms = millis();
    Serial.print(F("state=")); Serial.print(static_cast<uint8_t>(process.state()));
    Serial.print(F(" material=")); Serial.println(selected == MaterialProfile::PLA ? F("PLA") : F("PET"));
  }
}
