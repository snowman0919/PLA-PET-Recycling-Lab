#include <Arduino.h>
#include <avr/wdt.h>
#include <math.h>
#include <string.h>

#include "src/configuration.h"
#include "src/control_core.h"
#include "src/protocol.h"
#include "src/ui_core.h"

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
constexpr uint8_t kShredderSpeedPulse = 14;
constexpr uint8_t kHopperGateEnable = 15;
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
constexpr uint8_t kShredderVibrationAnalog = A15;
}  // namespace pins

namespace {
SafetyCore safety;
JamController shredder_jam;
UiCore ui;
UiInputFilter ui_inputs;
const HeaterConfig kPlaHeaterConfig{0.08F, 0.005F, -20.0F, 330.0F, 230.0F,
                                     30.0F, 2.0F, 60000UL};
const HeaterConfig kPetHeaterConfig{0.06F, 0.004F, -20.0F, 330.0F, 295.0F,
                                     30.0F, 2.0F, 60000UL};
HeaterController pet_extruder_heaters[4] = {
    HeaterController(kPetHeaterConfig), HeaterController(kPetHeaterConfig),
    HeaterController(kPetHeaterConfig), HeaterController(kPetHeaterConfig)};
HeaterController pla_extruder_heaters[4] = {
    HeaterController(kPlaHeaterConfig), HeaterController(kPlaHeaterConfig),
    HeaterController(kPlaHeaterConfig), HeaterController(kPlaHeaterConfig)};
const HeaterConfig kDryerPlaConfig{0.05F, 0.002F, -20.0F, 190.0F, 60.0F,
                                   10.0F, 1.0F, 60000UL};
const HeaterConfig kDryerPetConfig{0.04F, 0.0015F, -20.0F, 210.0F, 170.0F,
                                   10.0F, 1.0F, 60000UL};
HeaterController dryer_heaters[2] = {HeaterController(kDryerPlaConfig),
                                     HeaterController(kDryerPetConfig)};
const AdaptiveLoadConfig kPlaShredderLoad{8.0F, 12.0F, 20.0F, 0.70F,
                                           2.0F, 0.65F, 1.0F};
const AdaptiveLoadConfig kPetShredderLoad{6.0F, 10.0F, 18.0F, 0.72F,
                                           2.0F, 0.65F, 1.0F};

char receive_buffer[kMaximumFrameBytes];
size_t receive_length = 0;
uint32_t last_rx_sequence = 0;
bool have_rx_sequence = false;
uint32_t tx_sequence = 0;
uint32_t last_heartbeat_ms = 0;
uint32_t last_telemetry_ms = 0;
uint32_t last_ui_render_ms = 0;
uint32_t last_loop_ms = 0;
uint8_t malformed_burst = 0;
bool pending_reset = false;
bool pending_start = false;
bool pending_pause = false;
bool pending_purge_ack = false;
uint32_t pending_purge_ack_ms = 0;
Phase requested_phase = Phase::IDLE;
bool pet_profile = false;
float dryer_setpoint_c = 45.0F;
bool heater_fault_latched = false;
bool power_fault_latched = false;
JamOutput jam_output{JamState::NORMAL, false, false, false, 0};
AdaptiveLoadResult adaptive_load{false, false, false, 0.0F, 0.0F, 0.0F};
SafetyOutputs last_safe{SafetyState::SAFE_OFF, Phase::IDLE, FAULT_NONE,
                        false, false, false, false};
bool prior_sort_context = false;
uint32_t sort_started_ms = 0;

uint32_t load_window_start_ms = 0;
uint32_t load_previous_sample_ms = 0;
uint32_t load_pulse_count = 0;
uint16_t load_sample_count = 0;
bool prior_speed_pulse = false;
float load_current_square_sum = 0.0F;
float load_current_peak_a = 0.0F;
float load_derivative_peak_a_per_s = 0.0F;
float load_vibration_peak_g = 0.0F;
float load_previous_current_a = 0.0F;
LoadFeatures latest_load_features{false, NAN, NAN, NAN, NAN, NAN};

float temperature_c[6] = {NAN, NAN, NAN, NAN, NAN, NAN};
float pressure_mpa = NAN;
UiTelemetry ui_telemetry{};
UiFrame last_ui_frame{};

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

void reset_load_window(uint32_t now_ms) {
  load_window_start_ms = now_ms;
  load_previous_sample_ms = now_ms;
  load_pulse_count = 0;
  load_sample_count = 0;
  load_current_square_sum = 0.0F;
  load_current_peak_a = 0.0F;
  load_derivative_peak_a_per_s = 0.0F;
  load_vibration_peak_g = 0.0F;
}

void sample_shredder_load(uint32_t now_ms) {
  const bool pulse = digitalRead(pins::kShredderSpeedPulse) == HIGH;
  if (pulse && !prior_speed_pulse) ++load_pulse_count;
  prior_speed_pulse = pulse;
  const bool calibrated = kCurrentFrontendsQualified &&
                          kShredderMotionFeedbackQualified &&
                          kShredderAmpPerAdcCount > 0.0F &&
                          kShredderVibrationGPerAdcCount > 0.0F &&
                          kShredderEncoderPulsesPerRevolution > 0.0F &&
                          kShredderCommandRpm > 0.0F;
  if (!calibrated) {
    latest_load_features = {false, NAN, NAN, NAN, NAN, NAN};
    reset_load_window(now_ms);
    return;
  }

  const float current_a = fabsf(
      (static_cast<float>(analogRead(pins::kShredderCurrentAnalog)) -
       kShredderCurrentZeroAdcCount) *
      kShredderAmpPerAdcCount);
  const float vibration_g = fabsf(
      (static_cast<float>(analogRead(pins::kShredderVibrationAnalog)) -
       kShredderVibrationZeroAdcCount) *
      kShredderVibrationGPerAdcCount);
  const float elapsed_s = (now_ms - load_previous_sample_ms) / 1000.0F;
  if (load_sample_count && elapsed_s > 0.0F) {
    const float derivative = (current_a - load_previous_current_a) / elapsed_s;
    if (derivative > load_derivative_peak_a_per_s)
      load_derivative_peak_a_per_s = derivative;
  }
  load_previous_current_a = current_a;
  load_previous_sample_ms = now_ms;
  load_current_square_sum += current_a * current_a;
  if (current_a > load_current_peak_a) load_current_peak_a = current_a;
  if (vibration_g > load_vibration_peak_g) load_vibration_peak_g = vibration_g;
  ++load_sample_count;

  const uint32_t window_ms = now_ms - load_window_start_ms;
  if (window_ms >= 250 && load_sample_count > 0) {
    const float rpm = load_pulse_count * 60000.0F /
                      (window_ms * kShredderEncoderPulsesPerRevolution);
    latest_load_features = {
        true,
        sqrtf(load_current_square_sum / load_sample_count),
        load_current_peak_a,
        load_derivative_peak_a_per_s,
        rpm / kShredderCommandRpm,
        load_vibration_peak_g,
    };
    reset_load_window(now_ms);
  }
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
    if (!strcmp(frame.payload, "PLA")) {
      if (pet_profile) ui_telemetry.purge_required = true;
      pet_profile = false;
      dryer_setpoint_c = 45.0F;
    }
    if (!strcmp(frame.payload, "PET")) {
      if (!pet_profile) ui_telemetry.purge_required = true;
      pet_profile = true;
      dryer_setpoint_c = 140.0F;
    }
  } else if (!strcmp(frame.type, "DRY_STAGE")) {
    if (!pet_profile && !strcmp(frame.payload, "PLA_45")) dryer_setpoint_c = 45.0F;
    if (pet_profile && !strcmp(frame.payload, "PET_140")) dryer_setpoint_c = 140.0F;
    if (pet_profile && !strcmp(frame.payload, "PET_160")) dryer_setpoint_c = 160.0F;
  } else if (!strcmp(frame.type, "RESET")) {
    pending_reset = true;
  } else if (!strcmp(frame.type, "RUN")) {
    requested_phase = parse_phase(frame.payload);
    pending_start = requested_phase != Phase::IDLE;
  } else if (!strcmp(frame.type, "PAUSE")) {
    pending_pause = true;
  } else if (!strcmp(frame.type, "PURGE_ACK")) {
    const bool stopped = last_safe.state == SafetyState::SAFE_OFF ||
                         last_safe.state == SafetyState::READY ||
                         last_safe.state == SafetyState::PAUSED;
    pending_purge_ack = stopped;
    pending_purge_ack_ms = millis();
  } else if (!strcmp(frame.type, "UI_CLASS")) {
    unsigned detected = 0;
    unsigned confidence = 0;
    unsigned selected = 0;
    unsigned color = 7;
    unsigned batch = 0;
    unsigned purge = 0;
    unsigned qualified = 0;
    if (sscanf(frame.payload,
               "det=%u,conf=%u,selected=%u,color=%u,batch=%u,purge=%u,classok=%u",
               &detected, &confidence, &selected, &color, &batch, &purge,
               &qualified) == 7 &&
        detected <= static_cast<unsigned>(UiMaterial::REJECT) &&
        selected <= static_cast<unsigned>(UiMaterial::REJECT) &&
        confidence <= 100 && color <= 7 && batch <= 999 && purge <= 1 &&
        qualified <= 1) {
      ui_telemetry.detected_material = static_cast<UiMaterial>(detected);
      ui_telemetry.classifier_confidence_pct = static_cast<uint8_t>(confidence);
      ui_telemetry.selected_material = static_cast<UiMaterial>(selected);
      ui_telemetry.color_bin = static_cast<uint8_t>(color);
      ui_telemetry.batch_number = static_cast<uint16_t>(batch);
      if (purge == 1) ui_telemetry.purge_required = true;
      ui_telemetry.classifier_valid = qualified == 1;
    }
  } else if (!strcmp(frame.type, "UI_PROD")) {
    unsigned long dx_um = 0;
    unsigned long dy_um = 0;
    unsigned long length_mm = 0;
    unsigned long weight_g = 0;
    unsigned long eta_min = 0;
    unsigned long gauge_ok = 0;
    if (sscanf(frame.payload,
               "dx_um=%lu,dy_um=%lu,len_mm=%lu,weight_g=%lu,eta_min=%lu,gaugeok=%lu",
               &dx_um, &dy_um, &length_mm, &weight_g, &eta_min, &gauge_ok) == 6 &&
        dx_um <= 10000 && dy_um <= 10000 && eta_min <= 65535 && gauge_ok <= 1) {
      ui_telemetry.diameter_x_mm = dx_um / 1000.0F;
      ui_telemetry.diameter_y_mm = dy_um / 1000.0F;
      ui_telemetry.produced_length_m = length_mm / 1000.0F;
      ui_telemetry.produced_weight_g = static_cast<float>(weight_g);
      ui_telemetry.eta_minutes = static_cast<uint16_t>(eta_min);
      ui_telemetry.diameter_gauge_qualified = gauge_ok == 1;
    }
  } else if (!strcmp(frame.type, "UI_STOCK")) {
    unsigned hopper = 0;
    unsigned full_mask = 0;
    if (sscanf(frame.payload, "hopper=%u,full=%x", &hopper, &full_mask) == 2 &&
        hopper <= 100 && full_mask <= 0xFF) {
      ui_telemetry.hopper_fill_pct = static_cast<uint8_t>(hopper);
      ui_telemetry.full_bin_mask = static_cast<uint8_t>(full_mask);
    }
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
  digitalWrite(pins::kHopperGateEnable, LOW);
  digitalWrite(pins::kShredderDirection, LOW);
  const uint8_t enables[] = {pins::kShredderEnable, pins::kSorterEnable,
                             pins::kFeederEnable, pins::kExtruderEnable,
                             pins::kPullerEnable, pins::kSpoolerEnable};
  for (uint8_t pin : enables) digitalWrite(pin, LOW);
}

void reset_heater_if_finite(HeaterController& controller, uint32_t now_ms,
                            float measured_c) {
  if (isfinite(measured_c)) controller.reset(now_ms, measured_c);
}

void reset_all_heater_controllers(uint32_t now_ms) {
  for (uint8_t i = 0; i < 4; ++i) {
    reset_heater_if_finite(pla_extruder_heaters[i], now_ms, temperature_c[i]);
    reset_heater_if_finite(pet_extruder_heaters[i], now_ms, temperature_c[i]);
  }
  for (uint8_t i = 0; i < 2; ++i)
    reset_heater_if_finite(dryer_heaters[i], now_ms, temperature_c[4]);
}

void apply_outputs(const SafetyOutputs& safe, uint32_t now_ms) {
  if (!safe.contactor_request) {
    set_all_dangerous_outputs_off();
    reset_all_heater_controllers(now_ms);
    digitalWrite(pins::kCoolingFanEnable, safe.cooldown_fan_request ? HIGH : LOW);
    return;
  }
  digitalWrite(pins::kContactorRequest, HIGH);
  digitalWrite(pins::kCoolingFanEnable, HIGH);

  const bool sort = safe.active_phase == Phase::SORT_SHRED;
  const bool dry = safe.active_phase == Phase::DRY_PREHEAT;
  const bool extrude = safe.active_phase == Phase::EXTRUDE_SPOOL;
  const bool shredder_drive = sort && adaptive_load.sensor_plausible &&
                               jam_output.drive_enable;
  const bool hopper_feed = sort && adaptive_load.sensor_plausible &&
                           jam_output.feed_enable && adaptive_load.feed_scale > 0.0F;
  const uint8_t shredder_pwm = static_cast<uint8_t>(
      255.0F * (shredder_drive ? adaptive_load.drive_scale : 0.0F));
  const uint8_t gate_fraction = static_cast<uint8_t>(99.0F * adaptive_load.feed_scale);
  const bool gate_time_slot = static_cast<uint8_t>((now_ms / 10UL) % 100UL) <= gate_fraction;
  digitalWrite(pins::kShredderEnable, shredder_drive ? HIGH : LOW);
  digitalWrite(pins::kSorterEnable, sort ? HIGH : LOW);
  digitalWrite(pins::kExtruderEnable, extrude ? HIGH : LOW);
  digitalWrite(pins::kFeederEnable, extrude ? HIGH : LOW);
  digitalWrite(pins::kPullerEnable, extrude ? HIGH : LOW);
  digitalWrite(pins::kSpoolerEnable, extrude ? HIGH : LOW);
  digitalWrite(pins::kShredderDirection, jam_output.reverse ? HIGH : LOW);
  digitalWrite(pins::kHopperGateEnable, hopper_feed && gate_time_slot ? HIGH : LOW);
  analogWrite(pins::kShredderPwm, shredder_pwm);

  for (uint8_t pin : pins::kExtruderHeater) analogWrite(pin, 0);
  analogWrite(pins::kDryerPlaHeater, 0);
  analogWrite(pins::kDryerPetHeater, 0);

  if (!safe.heater_master_enable) return;

  if (dry) {
    const uint8_t heater_index = pet_profile ? 1 : 0;
    for (uint8_t i = 0; i < 4; ++i) {
      reset_heater_if_finite(pla_extruder_heaters[i], now_ms, temperature_c[i]);
      reset_heater_if_finite(pet_extruder_heaters[i], now_ms, temperature_c[i]);
    }
    reset_heater_if_finite(dryer_heaters[1U - heater_index], now_ms,
                           temperature_c[4]);
    const HeaterResult result = dryer_heaters[heater_index].update(
        now_ms, dryer_setpoint_c, temperature_c[4], true);
    if (!result.sensor_plausible || result.runaway_fault ||
        result.overtemperature_fault) {
      heater_fault_latched = true;
      return;
    }
    const float requested_w = result.duty * (pet_profile ? 240.0F : 60.0F);
    const PowerGrant grant = arbitrate_power(
        {Phase::DRY_PREHEAT, 80.0F, 0.0F,
         pet_profile ? 0.0F : requested_w,
         pet_profile ? requested_w : 0.0F},
        kProvisionalDeratedPowerLimitW);
    if (!grant.valid || (requested_w > 0.0F && grant.heater_scale <= 0.0F)) {
      power_fault_latched = true;
      return;
    }
    const uint8_t duty = static_cast<uint8_t>(255.0F * result.duty * grant.heater_scale);
    analogWrite(pet_profile ? pins::kDryerPetHeater : pins::kDryerPlaHeater, duty);
    return;
  }

  if (!extrude) {
    reset_all_heater_controllers(now_ms);
    return;
  }
  for (uint8_t i = 0; i < 2; ++i)
    reset_heater_if_finite(dryer_heaters[i], now_ms, temperature_c[4]);
  const float pla_setpoint[4] = {180.0F, 190.0F, 200.0F, 190.0F};
  const float pet_setpoint[4] = {250.0F, 270.0F, 280.0F, 275.0F};
  const float* setpoint = pet_profile ? pet_setpoint : pla_setpoint;
  HeaterController* controllers = pet_profile ? pet_extruder_heaters : pla_extruder_heaters;
  HeaterController* inactive_controllers =
      pet_profile ? pla_extruder_heaters : pet_extruder_heaters;
  float requested_duty[4] = {0, 0, 0, 0};
  bool heater_fault = false;
  for (uint8_t i = 0; i < 4; ++i) {
    reset_heater_if_finite(inactive_controllers[i], now_ms, temperature_c[i]);
    const HeaterResult result = controllers[i].update(
        now_ms, setpoint[i], temperature_c[i], true);
    requested_duty[i] = result.duty;
    heater_fault |= !result.sensor_plausible || result.runaway_fault ||
                    result.overtemperature_fault;
  }
  if (heater_fault) {
    heater_fault_latched = true;
    return;
  }
  const float requested_w = requested_duty[0] * 80.0F + requested_duty[1] * 80.0F +
                            requested_duty[2] * 80.0F + requested_duty[3] * 60.0F;
  const PowerGrant grant = arbitrate_power(
      {Phase::EXTRUDE_SPOOL, 396.0F, requested_w, 0.0F, 0.0F},
      kProvisionalDeratedPowerLimitW);
  if (!grant.valid || (requested_w > 0.0F && grant.heater_scale <= 0.0F)) {
    power_fault_latched = true;
    return;
  }
  const float scale = grant.valid ? grant.heater_scale : 0.0F;
  for (uint8_t i = 0; i < 4; ++i)
    analogWrite(pins::kExtruderHeater[i], static_cast<uint8_t>(255.0F * requested_duty[i] * scale));
}

void send_telemetry(const SafetyOutputs& safe) {
  char payload[120];
  snprintf(payload, sizeof(payload),
           "state=%u,phase=%u,fault=%08lX,p=%.2f,t0=%.1f,load=%.2f,jam=%u,retry=%u",
           static_cast<unsigned>(safe.state), static_cast<unsigned>(safe.active_phase),
           static_cast<unsigned long>(safe.latched_faults), pressure_mpa,
           temperature_c[0], adaptive_load.score,
           static_cast<unsigned>(jam_output.state),
           static_cast<unsigned>(jam_output.retry_count));
  char frame[kMaximumFrameBytes];
  const size_t length = encode_frame(frame, sizeof(frame), "TEL", ++tx_sequence, payload);
  if (length) Serial.write(reinterpret_cast<const uint8_t*>(frame), length);
}

void send_ui_action(const UiAction& action) {
  if (action.type == UiActionType::NONE) return;
  char payload[48];
  switch (action.type) {
    case UiActionType::ACK_STARTUP:
      snprintf(payload, sizeof(payload), "ACK_STARTUP=1");
      break;
    case UiActionType::SET_MATERIAL:
      ui_telemetry.selected_material = static_cast<UiMaterial>(action.value);
      snprintf(payload, sizeof(payload), "MATERIAL=%s",
               ui_material_name(ui_telemetry.selected_material));
      break;
    case UiActionType::SET_COLOR_BIN:
      ui_telemetry.color_bin = static_cast<uint8_t>(action.value);
      snprintf(payload, sizeof(payload), "COLOR=%d", action.value);
      break;
    case UiActionType::SELECT_BATCH:
      ui_telemetry.batch_number = static_cast<uint16_t>(action.value);
      snprintf(payload, sizeof(payload), "BATCH=%d", action.value);
      break;
    case UiActionType::REQUEST_CALIBRATION:
      snprintf(payload, sizeof(payload), "CALIBRATION=REQUEST");
      break;
    case UiActionType::REQUEST_MAINTENANCE:
      snprintf(payload, sizeof(payload), "MAINTENANCE=REQUEST");
      break;
    case UiActionType::NONE:
      return;
  }
  char frame[kMaximumFrameBytes];
  const size_t length = encode_frame(frame, sizeof(frame), "UI_CMD", ++tx_sequence,
                                     payload);
  if (length) Serial.write(reinterpret_cast<const uint8_t*>(frame), length);
}

void update_local_ui_telemetry(const SafetyOutputs& safe) {
  ui_telemetry.state = safe.state;
  ui_telemetry.phase = safe.active_phase;
  ui_telemetry.faults = safe.latched_faults;
  for (uint8_t i = 0; i < 6; ++i) ui_telemetry.temperatures_c[i] = temperature_c[i];
  ui_telemetry.motor_current_a[0] = latest_load_features.valid
                                        ? latest_load_features.rms_current_a
                                        : NAN;
  ui_telemetry.motor_current_a[1] = NAN;
  ui_telemetry.motor_current_a[2] = NAN;
}

void render_tft_frame(const UiFrame& frame) {
  (void)frame;
  // The deterministic frame is ready for a thin SPI driver adapter.  Keep CS
  // deselected and RESET asserted until the donor controller and logic level
  // are identified; never guess a controller command set or voltage.
}

void service_ui(uint32_t now_ms, bool render) {
  const UiEvent event = ui_inputs.update(
      {now_ms, digitalRead(pins::kRotaryA) == HIGH,
       digitalRead(pins::kRotaryB) == HIGH,
       digitalRead(pins::kRotaryPush) == LOW,
       digitalRead(pins::kBackAbort) == LOW});
  send_ui_action(ui.handle(event, ui_telemetry));
  if (render) {
    last_ui_frame = ui.compose(ui_telemetry);
    render_tft_frame(last_ui_frame);
  }
}
}  // namespace

void setup() {
  set_all_dangerous_outputs_off();
  const uint8_t outputs[] = {
      pins::kContactorRequest, pins::kShredderEnable, pins::kSorterEnable,
      pins::kFeederEnable, pins::kExtruderEnable, pins::kPullerEnable,
      pins::kSpoolerEnable, pins::kCoolingFanEnable, pins::kShredderDirection,
      pins::kHopperGateEnable,
      pins::kExtruderDirection, pins::kFeederDirection, pins::kTraverseDirection,
      pins::kSpoolerDirection, pins::kPullerDirection, pins::kTraverseStep,
      pins::kSorterPwm, pins::kFeederStepPwm, pins::kTftDc, pins::kTftCs,
      pins::kTftReset, pins::kBuzzer};
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
  digitalWrite(pins::kTftCs, HIGH);
  digitalWrite(pins::kTftReset, LOW);
  const uint8_t safety_inputs[] = {
      pins::kEstopAux, pins::kContactorFeedback, pins::kLidAux,
      pins::kServiceAux, pins::kThermalChainAux, pins::kPressureTripAux,
      pins::kAirflowAux, pins::kFormingGuardAux, pins::kStartPause,
      pins::kBackAbort, pins::kRotaryPush};
  for (uint8_t pin : safety_inputs) pinMode(pin, INPUT_PULLUP);
  pinMode(pins::kShredderSpeedPulse, INPUT_PULLUP);
  pinMode(pins::kRotaryA, INPUT_PULLUP);
  pinMode(pins::kRotaryB, INPUT_PULLUP);
  pinMode(pins::kShredderVibrationAnalog, INPUT);
  ui_telemetry.detected_material = UiMaterial::UNKNOWN;
  ui_telemetry.selected_material = UiMaterial::AUTO;
  ui_telemetry.color_bin = 7;
  ui_telemetry.purge_required = true;
  ui_telemetry.diameter_x_mm = NAN;
  ui_telemetry.diameter_y_mm = NAN;
  ui_telemetry.produced_length_m = NAN;
  ui_telemetry.produced_weight_g = NAN;
  for (float& value : ui_telemetry.temperatures_c) value = NAN;
  for (float& value : ui_telemetry.motor_current_a) value = NAN;
  reset_load_window(millis());
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

  sample_shredder_load(now);
  const bool load_frontends_ready =
      kCurrentFrontendsQualified && kShredderMotionFeedbackQualified &&
      kShredderAmpPerAdcCount > 0.0F &&
      kShredderVibrationGPerAdcCount > 0.0F &&
      kShredderEncoderPulsesPerRevolution > 0.0F &&
      kShredderCommandRpm > 0.0F;
  const bool sort_context = last_safe.state == SafetyState::RUNNING &&
                            last_safe.active_phase == Phase::SORT_SHRED;
  if (sort_context && !prior_sort_context) {
    sort_started_ms = now;
    shredder_jam.reset(now);
  }
  prior_sort_context = sort_context;
  const bool sort_startup_grace = sort_context && now - sort_started_ms < 500UL;
  if (sort_context && !sort_startup_grace) {
    adaptive_load = evaluate_adaptive_load(
        latest_load_features, pet_profile ? kPetShredderLoad : kPlaShredderLoad);
    jam_output = shredder_jam.update(
        now, adaptive_load.overload, adaptive_load.speed_drop);
  } else if (sort_context) {
    adaptive_load = {true, false, false, 0.0F, 1.0F, 1.0F};
    jam_output = shredder_jam.update(now, false, false);
  } else {
    shredder_jam.reset(now);
    jam_output = {JamState::NORMAL, false, false, false, 0};
    adaptive_load = {load_frontends_ready, false, false, 0.0F, 0.0F, 0.0F};
  }
  const bool load_signal_ok = !sort_context || sort_startup_grace ||
                              adaptive_load.sensor_plausible;
  const bool sensors_ok = all_temperature_sensors_plausible() &&
                          load_frontends_ready && load_signal_ok &&
                          !heater_fault_latched;
  pressure_mpa = read_pressure_mpa();
  const bool local_reset_held = !digitalRead(pins::kBackAbort);
  const bool local_start_held = !digitalRead(pins::kStartPause);
  const bool pressure_discrete_ok = loop_closed(pins::kPressureTripAux);
  update_local_ui_telemetry(last_safe);
  service_ui(now, false);
  const bool stopped_for_purge_ack =
      last_safe.state == SafetyState::SAFE_OFF ||
      last_safe.state == SafetyState::READY ||
      last_safe.state == SafetyState::PAUSED;
  if (pending_purge_ack && now - pending_purge_ack_ms > 5000UL)
    pending_purge_ack = false;
  if (pending_purge_ack && local_reset_held && stopped_for_purge_ack) {
    ui_telemetry.purge_required = false;
    pending_purge_ack = false;
  }
  if (!ui.startup_acknowledged()) {
    pending_reset = false;
    pending_start = false;
  }
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
      pending_reset && local_reset_held && ui.startup_acknowledged(),
      pending_start && local_start_held &&
          ui.run_permitted(requested_phase, ui_telemetry),
      pending_pause || (local_start_held && !pending_start),
      jam_output.state == JamState::FAULT,
      power_fault_latched,
      malformed_burst >= 3,
      isfinite(pressure_mpa) ? pressure_mpa : 999.0F,
      requested_phase,
  };
  const SafetyOutputs safe = safety.tick(in);
  apply_outputs(safe, now);
  last_safe = safe;
  update_local_ui_telemetry(safe);
  if (in.reset_requested) pending_reset = false;
  if (in.start_requested) pending_start = false;
  pending_pause = false;

  if (now - last_telemetry_ms >= kTelemetryPeriodMs) {
    last_telemetry_ms = now;
    send_telemetry(safe);
  }
  if (now - last_ui_render_ms >= kTelemetryPeriodMs) {
    last_ui_render_ms = now;
    service_ui(now, true);
  }
  wdt_reset();
}
