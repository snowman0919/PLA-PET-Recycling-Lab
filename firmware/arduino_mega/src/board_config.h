#pragma once

#include <Arduino.h>

namespace Board {
constexpr uint8_t SHREDDER_RPM_PIN = 2;
constexpr uint8_t PULLER_TACH_PIN = 3;
constexpr uint8_t ENCODER_A_PIN = 18;
constexpr uint8_t ENCODER_B_PIN = 19;
constexpr uint8_t ESTOP_PIN = 20;
constexpr uint8_t LID_PIN = 21;
constexpr uint8_t SERVICE_GUARD_PIN = 22;
constexpr uint8_t THERMAL_CHAIN_PIN = 23;
constexpr uint8_t HEATER_PERMISSION_FEEDBACK_PIN = 24;
constexpr uint8_t START_PIN = 25;
constexpr uint8_t PAUSE_PIN = 26;
constexpr uint8_t BACK_PIN = 27;
constexpr uint8_t CONFIRM_PIN = 28;
constexpr uint8_t ENCODER_BUTTON_PIN = 29;
constexpr uint8_t SHREDDER_DIR_PIN = 30;
constexpr uint8_t SHREDDER_REVERSE_PIN = 31;
constexpr uint8_t SHREDDER_ENABLE_PIN = 32;
constexpr uint8_t SCREW_DIR_PIN = 33;
constexpr uint8_t SCREW_ENABLE_PIN = 34;
constexpr uint8_t PULLER_DIR_PIN = 35;
constexpr uint8_t PULLER_ENABLE_PIN = 36;
constexpr uint8_t SPOOLER_DIR_PIN = 37;
constexpr uint8_t SPOOLER_ENABLE_PIN = 38;
constexpr uint8_t TRAVERSE_STEP_PIN = 39;
constexpr uint8_t TRAVERSE_DIR_PIN = 40;
constexpr uint8_t TRAVERSE_ENABLE_PIN = 41;
constexpr uint8_t LOCKOUT_CONFIRM_PIN = 43;
constexpr uint8_t SHREDDER_PWM_PIN = 5;
constexpr uint8_t SCREW_PWM_PIN = 6;
constexpr uint8_t PULLER_PWM_PIN = 7;
constexpr uint8_t SPOOLER_PWM_PIN = 8;
constexpr uint8_t COOLING_PWM_PIN = 9;
constexpr uint8_t HEATER_PINS[4] = {10, 11, 12, 13};
constexpr uint8_t HOPPER_PTC_PIN = 4;
constexpr uint8_t THERMOCOUPLE_CS_PINS[5] = {44, 45, 46, 47, 48};
constexpr uint8_t THERMOCOUPLE_SO_PIN = 50;
constexpr uint8_t THERMOCOUPLE_SCK_PIN = 52;
constexpr uint8_t CURRENT_PIN = A0;
constexpr uint8_t DANCER_PIN = A1;
constexpr uint8_t GAUGE_X_PIN = A2;
constexpr uint8_t GAUGE_Y_PIN = A3;
constexpr uint8_t SHREDDER_FAULT_PIN = A8;
constexpr uint8_t SCREW_FAULT_PIN = A9;
constexpr uint8_t PULLER_FAULT_PIN = A10;
constexpr uint8_t SPOOLER_FAULT_PIN = A11;
constexpr uint8_t GAUGE_VALID_PIN = A12;
constexpr uint8_t SAFETY_INPUT_PINS[] = {ESTOP_PIN, LID_PIN, SERVICE_GUARD_PIN, THERMAL_CHAIN_PIN, HEATER_PERMISSION_FEEDBACK_PIN};
constexpr uint8_t MOTOR_PWM_PINS[] = {SHREDDER_PWM_PIN, SCREW_PWM_PIN, PULLER_PWM_PIN, SPOOLER_PWM_PIN, COOLING_PWM_PIN};
constexpr uint8_t DRIVER_FAULT_PINS[] = {SHREDDER_FAULT_PIN, SCREW_FAULT_PIN, PULLER_FAULT_PIN, SPOOLER_FAULT_PIN};
}
