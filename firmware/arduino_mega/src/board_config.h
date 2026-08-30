#pragma once

#include <Arduino.h>

namespace Board {
constexpr uint8_t ESTOP_PIN = 2;
constexpr uint8_t LID_PIN = 3;
constexpr uint8_t SERVICE_GUARD_PIN = 18;
constexpr uint8_t ENCODER_A_PIN = 19;
constexpr uint8_t ENCODER_B_PIN = 20;
constexpr uint8_t ENCODER_BUTTON_PIN = 21;
constexpr uint8_t SHREDDER_PWM_PIN = 5;
constexpr uint8_t SCREW_PWM_PIN = 6;
constexpr uint8_t PULLER_PWM_PIN = 7;
constexpr uint8_t SPOOLER_PWM_PIN = 8;
constexpr uint8_t COOLING_PWM_PIN = 9;
constexpr uint8_t HEATER_PINS[4] = {10, 11, 12, 13};
constexpr uint8_t CURRENT_PIN = A0;
constexpr uint8_t DANCER_PIN = A1;
constexpr uint8_t SAFETY_INPUT_PINS[] = {ESTOP_PIN, LID_PIN, SERVICE_GUARD_PIN, ENCODER_BUTTON_PIN};
constexpr uint8_t MOTOR_PWM_PINS[] = {SHREDDER_PWM_PIN, SCREW_PWM_PIN, PULLER_PWM_PIN, SPOOLER_PWM_PIN, COOLING_PWM_PIN};
}
