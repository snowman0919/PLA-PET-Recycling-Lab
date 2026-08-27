#include <Arduino.h>
#include <avr/wdt.h>
#include <math.h>
#include <string.h>

#include "src/configuration.h"
#include "src/control_core.h"
#include "src/protocol.h"

using namespace recycler;

namespace pins {
constexpr uint8_t kSpoolEncoderA = 2;
constexpr uint8_t kSpoolEncoderB = 3;
constexpr uint8_t kExtruderHeater[4] = {4, 5, 6, 7};
constexpr uint8_t kDryerPlaHeater = 8;
constexpr uint8_t kDryerPetHeater = 9;
constexpr uint8_t kShredderPwm = 10;
constexpr uint8_t kExtruderPwm = 11;
constexpr uint8_t kPullerStepPwm = 12;
constexpr uint8_t kSpoolerStepPwm = 13;
constexpr uint8_t kStartPause = 16;
constexpr uint8_t kBackAbort = 17;
constexpr uint8_t kExtruderEncoderA = 18;
constexpr uint8_t kExtruderEncoderB = 19;
constexpr uint8_t kPullerEncoderA = 20;
constexpr uint8_t kPullerEncoderB = 21;
constexpr uint8_t kEstopAux = 22;
constexpr uint8_t kContactorFeedback = 23;
constexpr uint8_t kLidAux = 24;
constexpr uint8_t kServiceAux = 25;
constexpr uint8_t kThermalChainAux = 26;
constexpr uint8_t kPressureTripAux = 27;
constexpr uint8_t kAirflowAux = 28;
constexpr uint8_t kFormingGuardAux = 29;
constexpr uint8_t kContactorRequest = 30;
constexpr uint8_t kShredderEnable = 31;
constexpr uint8_t kSorterEnable = 32;
constexpr uint8_t kFeederEnable = 33;
constexpr uint8_t kExtruderEnable = 34;
constexpr uint8_t kPullerEnable = 35;
constexpr uint8_t kSpoolerEnable = 36;
constexpr uint8_t kCoolingFanEnable = 37;
constexpr uint8_t kShredderDirection = 38;
constexpr uint8_t kExtruderDirection = 39;
constexpr uint8_t kFeederDirection = 40;
constexpr uint8_t kTraverseDirection = 41;
constexpr uint8_t kSpoolerDirection = 42;
constexpr uint8_t kPullerDirection = 43;
constexpr uint8_t kTraverseStep = 44;
constexpr uint8_t kSorterPwm = 45;
constexpr uint8_t kFeederStepPwm = 46;
constexpr uint8_t kTftDc = 47;
constexpr uint8_t kTftCs = 48;
constexpr uint8_t kTftReset = 49;
constexpr uint8_t kBuzzer = 53;
constexpr uint8_t kRotaryA = 66;
constexpr uint8_t kRotaryB = 67;
constexpr uint8_t kRotaryPush = 68;

constexpr uint8_t kTemperatureAnalog[6] = {A0, A1, A2, A3, A4, A5};
constexpr uint8_t kAirflowAnalog = A6;
constexpr uint8_t kPressureAnalog = A7;
constexpr uint8_t kShredderCurrentAnalog = A8;
constexpr uint8_t kExtruderCurrentAnalog = A9;
constexpr uint8_t kFormingCurrentAnalog = A10;
constexpr uint8_t kDancerAnalog = A11;
}  // namespace pins

namespace {
SafetyCore safety;
JamController shredder_jam;
const HeaterConfig kPlaHeaterConfig{0.08F, 0.005F, -20.0F, 330.0F, 230.0F,
                                     30.0F, 2.0F, 60000UL};
const HeaterConfig kPetHeaterConfig{0.06F, 0.004F, -20.0F, 330.0F, 295.0F,
                                     30.0F, 2.0F, 60000UL};
HeaterController extruder_heaters[4] = {
    HeaterController(kPetHeaterConfig), HeaterController(kPetHeaterConfig),
    HeaterController(kPetHeaterConfig), HeaterController(kPetHeaterConfig)};

char receive_buffer[kMaximumFrameBytes];
size_t receive_length = 0;
uint32_t last_rx_sequence = 0;
bool have_rx_sequence = false;
uint32_t tx_sequence = 0;
uint32_t last_heartbeat_ms = 0;
uint32_t last_telemetry_ms = 0;
uint32_t last_loop_ms = 0;
uint8_t malformed_burst = 0;
bool pending_reset = false;
bool pending_start = false;
bool pending_pause = false;
Phase requested_phase = Phase::IDLE;
bool pet_profile = false;

float temperature_c[6] = {NAN, NAN, NAN, NAN, NAN, NAN};
float pressure_mpa = NAN;

bool loop_closed(uint8_t pin) { return digitalRead(pin) == LOW; }

float read_temperature_c(uint8_t channel) {
  (void)channel;
  if (!kTemperatureFrontendsQualified) return NAN;
  // Add the selected RTD/thermistor/thermocouple front-end conversion here.
  // Returning NaN is mandatory for ADC rail, open lead and shorted lead.
  return NAN;
}

float read_pressure_mpa() {
  if (!kPressureFrontendQualified) return NAN;
  const float adc = static_cast<float>(analogRead(pins::kPressureAnalog));
  return (adc - kPressureZeroAdcCount) * kPressureMpaPerAdcCount;
}

bool all_temperature_sensors_plausible() {
  for (uint8_t i = 0; i < 6; ++i) {
    temperature_c[i] = read_temperature_c(i);
    if (!isfinite(temperature_c[i]) || temperature_c[i] < -20.0F ||
        temperature_c[i] > 330.0F)
      return false;
  }
  return true;
}

Phase parse_phase(const char* payload) {
  if (!strcmp(payload, "SORT_SHRED")) return Phase::SORT_SHRED;
  if (!strcmp(payload, "DRY_PREHEAT")) return Phase::DRY_PREHEAT;
  if (!strcmp(payload, "EXTRUDE_SPOOL")) return Phase::EXTRUDE_SPOOL;
  if (!strcmp(payload, "COOLDOWN_CLEAN")) return Phase::COOLDOWN_CLEAN;
  return Phase::IDLE;
}

void handle_frame(const ProtocolFrame& frame) {
  if (have_rx_sequence && !sequence_is_newer(frame.sequence, last_rx_sequence)) {
    ++malformed_burst;
    return;
  }
  have_rx_sequence = true;
  last_rx_sequence = frame.sequence;
  malformed_burst = 0;
  if (!strcmp(frame.type, "HB")) {
    last_heartbeat_ms = millis();
  } else if (!strcmp(frame.type, "PROFILE")) {
    if (!strcmp(frame.payload, "PLA")) pet_profile = false;
    if (!strcmp(frame.payload, "PET")) pet_profile = true;
  } else if (!strcmp(frame.type, "RESET")) {
    pending_reset = true;
  } else if (!strcmp(frame.type, "RUN")) {
    requested_phase = parse_phase(frame.payload);
    pending_start = requested_phase != Phase::IDLE;
  } else if (!strcmp(frame.type, "PAUSE")) {
    pending_pause = true;
  }
}

void poll_serial() {
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      ProtocolFrame frame{};
      const ProtocolStatus status = decode_frame(receive_buffer, receive_length, &frame);
      if (status == ProtocolStatus::OK)
        handle_frame(frame);
      else if (malformed_burst < 255)
        ++malformed_burst;
      receive_length = 0;
    } else if (receive_length + 1 < sizeof(receive_buffer)) {
      receive_buffer[receive_length++] = c;
    } else {
      receive_length = 0;
      malformed_burst = 3;
    }
  }
}

void set_all_dangerous_outputs_off() {
  digitalWrite(pins::kContactorRequest, LOW);
  for (uint8_t pin : pins::kExtruderHeater) analogWrite(pin, 0);
  analogWrite(pins::kDryerPlaHeater, 0);
  analogWrite(pins::kDryerPetHeater, 0);
  analogWrite(pins::kShredderPwm, 0);
  analogWrite(pins::kExtruderPwm, 0);
  analogWrite(pins::kPullerStepPwm, 0);
  analogWrite(pins::kSpoolerStepPwm, 0);
  analogWrite(pins::kSorterPwm, 0);
  analogWrite(pins::kFeederStepPwm, 0);
  const uint8_t enables[] = {pins::kShredderEnable, pins::kSorterEnable,
                             pins::kFeederEnable, pins::kExtruderEnable,
                             pins::kPullerEnable, pins::kSpoolerEnable};
  for (uint8_t pin : enables) digitalWrite(pin, LOW);
}

void apply_outputs(const SafetyOutputs& safe) {
  if (!safe.contactor_request) {
    set_all_dangerous_outputs_off();
    digitalWrite(pins::kCoolingFanEnable, safe.cooldown_fan_request ? HIGH : LOW);
    return;
  }
  digitalWrite(pins::kContactorRequest, HIGH);
  digitalWrite(pins::kCoolingFanEnable, HIGH);

  const bool sort = safe.active_phase == Phase::SORT_SHRED;
  const bool extrude = safe.active_phase == Phase::EXTRUDE_SPOOL;
  digitalWrite(pins::kShredderEnable, sort ? HIGH : LOW);
  digitalWrite(pins::kSorterEnable, sort ? HIGH : LOW);
  digitalWrite(pins::kExtruderEnable, extrude ? HIGH : LOW);
  digitalWrite(pins::kFeederEnable, extrude ? HIGH : LOW);
  digitalWrite(pins::kPullerEnable, extrude ? HIGH : LOW);
  digitalWrite(pins::kSpoolerEnable, extrude ? HIGH : LOW);

  if (!safe.heater_master_enable || !extrude) {
    for (uint8_t pin : pins::kExtruderHeater) analogWrite(pin, 0);
    return;
  }
  const float pla_setpoint[4] = {180.0F, 190.0F, 200.0F, 190.0F};
  const float pet_setpoint[4] = {250.0F, 270.0F, 280.0F, 275.0F};
  const float* setpoint = pet_profile ? pet_setpoint : pla_setpoint;
  float requested_duty[4] = {0, 0, 0, 0};
  bool heater_fault = false;
  for (uint8_t i = 0; i < 4; ++i) {
    const HeaterResult result = extruder_heaters[i].update(
        millis(), setpoint[i], temperature_c[i], true);
    requested_duty[i] = result.duty;
    heater_fault |= !result.sensor_plausible || result.runaway_fault ||
                    result.overtemperature_fault;
  }
  if (heater_fault) {
    for (uint8_t pin : pins::kExtruderHeater) analogWrite(pin, 0);
    return;
  }
  const float requested_w = requested_duty[0] * 80.0F + requested_duty[1] * 80.0F +
                            requested_duty[2] * 80.0F + requested_duty[3] * 60.0F;
  const PowerGrant grant = arbitrate_power(
      {Phase::EXTRUDE_SPOOL, 396.0F, requested_w, 0.0F, 0.0F},
      kProvisionalDeratedPowerLimitW);
  const float scale = grant.valid ? grant.heater_scale : 0.0F;
  for (uint8_t i = 0; i < 4; ++i)
    analogWrite(pins::kExtruderHeater[i], static_cast<uint8_t>(255.0F * requested_duty[i] * scale));
}

void send_telemetry(const SafetyOutputs& safe) {
  char payload[96];
  snprintf(payload, sizeof(payload), "state=%u,phase=%u,fault=%08lX,p=%.2f,t0=%.1f",
           static_cast<unsigned>(safe.state), static_cast<unsigned>(safe.active_phase),
           static_cast<unsigned long>(safe.latched_faults), pressure_mpa,
           temperature_c[0]);
  char frame[kMaximumFrameBytes];
  const size_t length = encode_frame(frame, sizeof(frame), "TEL", ++tx_sequence, payload);
  if (length) Serial.write(reinterpret_cast<const uint8_t*>(frame), length);
}
}  // namespace

void setup() {
  set_all_dangerous_outputs_off();
  const uint8_t outputs[] = {
      pins::kContactorRequest, pins::kShredderEnable, pins::kSorterEnable,
      pins::kFeederEnable, pins::kExtruderEnable, pins::kPullerEnable,
      pins::kSpoolerEnable, pins::kCoolingFanEnable, pins::kShredderDirection,
      pins::kExtruderDirection, pins::kFeederDirection, pins::kTraverseDirection,
      pins::kSpoolerDirection, pins::kPullerDirection, pins::kTraverseStep,
      pins::kSorterPwm, pins::kFeederStepPwm, pins::kBuzzer};
  for (uint8_t pin : outputs) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
  }
  for (uint8_t pin : pins::kExtruderHeater) {
    pinMode(pin, OUTPUT);
    analogWrite(pin, 0);
  }
  pinMode(pins::kDryerPlaHeater, OUTPUT);
  pinMode(pins::kDryerPetHeater, OUTPUT);
  const uint8_t safety_inputs[] = {
      pins::kEstopAux, pins::kContactorFeedback, pins::kLidAux,
      pins::kServiceAux, pins::kThermalChainAux, pins::kPressureTripAux,
      pins::kAirflowAux, pins::kFormingGuardAux, pins::kStartPause,
      pins::kBackAbort, pins::kRotaryPush};
  for (uint8_t pin : safety_inputs) pinMode(pin, INPUT_PULLUP);
  Serial.begin(kPiBaud);
  last_heartbeat_ms = millis() - 10000UL;
  wdt_enable(WDTO_2S);
}

void loop() {
  poll_serial();
  const uint32_t now = millis();
  if (now - last_loop_ms < kLoopPeriodMs) {
    wdt_reset();
    return;
  }
  last_loop_ms = now;

  const bool sensors_ok = all_temperature_sensors_plausible();
  pressure_mpa = read_pressure_mpa();
  const bool local_reset_held = !digitalRead(pins::kBackAbort);
  const bool local_start_held = !digitalRead(pins::kStartPause);
  const bool pressure_discrete_ok = loop_closed(pins::kPressureTripAux);
  SafetyInputs in{
      now,
      now - last_heartbeat_ms,
      loop_closed(pins::kEstopAux),
      loop_closed(pins::kLidAux),
      loop_closed(pins::kServiceAux) && loop_closed(pins::kFormingGuardAux),
      loop_closed(pins::kThermalChainAux),
      sensors_ok && kPressureFrontendQualified && pressure_discrete_ok,
      kAirflowFrontendQualified && loop_closed(pins::kAirflowAux),
      loop_closed(pins::kContactorFeedback),
      pending_reset && local_reset_held,
      pending_start && local_start_held,
      pending_pause || (local_start_held && !pending_start),
      false,
      false,
      malformed_burst >= 3,
      isfinite(pressure_mpa) ? pressure_mpa : 999.0F,
      requested_phase,
  };
  const SafetyOutputs safe = safety.tick(in);
  apply_outputs(safe);
  if (in.reset_requested) pending_reset = false;
  if (in.start_requested) pending_start = false;
  pending_pause = false;

  if (now - last_telemetry_ms >= kTelemetryPeriodMs) {
    last_telemetry_ms = now;
    send_telemetry(safe);
  }
  wdt_reset();
}
