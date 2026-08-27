#pragma once

// Commissioning locks are intentionally fail-safe. Change a flag to true only
// after the named front-end has a selected part number, calibration record and
// the corresponding wiring/fault-injection test has passed.
constexpr bool kTemperatureFrontendsQualified = false;
constexpr bool kPressureFrontendQualified = false;
constexpr bool kCurrentFrontendsQualified = false;
constexpr bool kAirflowFrontendQualified = false;

// 80% of the user's nominal 600 W statement. This is a software ceiling, not
// a PSU or wire rating. Replace it with the lowest label/thermal/branch limit.
constexpr float kProvisionalDeratedPowerLimitW = 480.0F;

// Analog conversion coefficients are invalid until selected transducers are
// calibrated. NaN is returned while the corresponding qualification flag is
// false, keeping the safety FSM disarmed.
constexpr float kPressureMpaPerAdcCount = 0.0F;
constexpr float kPressureZeroAdcCount = 0.0F;

constexpr unsigned long kPiBaud = 115200UL;
constexpr uint32_t kLoopPeriodMs = 10;
constexpr uint32_t kTelemetryPeriodMs = 200;
