#pragma once

// Commissioning locks are intentionally fail-safe. Change a flag to true only
// after the named front-end has a selected part number, calibration record and
// the corresponding wiring/fault-injection test has passed.
constexpr bool kTemperatureFrontendsQualified = false;
constexpr bool kPressureFrontendQualified = false;
constexpr bool kCurrentFrontendsQualified = false;
constexpr bool kAirflowFrontendQualified = false;
constexpr bool kShredderMotionFeedbackQualified = false;

// 80% of the user's nominal 600 W statement. This is a software ceiling, not
// a PSU or wire rating. Replace it with the lowest label/thermal/branch limit.
constexpr float kProvisionalDeratedPowerLimitW = 480.0F;

// Analog conversion coefficients are invalid until selected transducers are
// calibrated. NaN is returned while the corresponding qualification flag is
// false, keeping the safety FSM disarmed.
constexpr float kPressureMpaPerAdcCount = 0.0F;
constexpr float kPressureZeroAdcCount = 0.0F;

// These remain invalid until the current conditioner, tach target and
// vibration front-end are selected and calibrated.  The two-stage shred phase
// cannot arm while either qualification flag is false.
constexpr float kShredderAmpPerAdcCount = 0.0F;
constexpr float kShredderCurrentZeroAdcCount = 0.0F;
constexpr float kShredderVibrationGPerAdcCount = 0.0F;
constexpr float kShredderVibrationZeroAdcCount = 0.0F;
constexpr float kShredderEncoderPulsesPerRevolution = 0.0F;
constexpr float kShredderCommandRpm = 0.0F;

constexpr unsigned long kServiceSerialBaud = 115200UL;
constexpr uint32_t kLoopPeriodMs = 10;
constexpr uint32_t kTelemetryPeriodMs = 200;
