#include "screw_motion_monitor.h"

namespace {
constexpr uint32_t TACH_LOSS_TIMEOUT_MS = 1000;
constexpr uint32_t MOTION_MISMATCH_DWELL_MS = 1500;
constexpr float MIN_COMMAND_RPM = 1.0f;
constexpr float MIN_MOTION_RATIO = 0.35f;
}

ScrewMotionMonitor::ScrewMotionMonitor() {
  configureSpeedControl({1.0f, 25.0f, 38, 255, 5.0f, 1.0f, 1000, TACH_LOSS_TIMEOUT_MS,
                         1000, 1.5f});
}

bool ScrewMotionMonitor::configureSpeedControl(const DriveSpeedConfig &config) {
  return speed_controller_.configure(config);
}

void ScrewMotionMonitor::reset() {
  cumulative_revolutions_ = 0;
  last_ms_ = 0;
  mismatch_since_ms_ = 0;
  last_valid_tach_ms_ = 0;
  speed_controller_.reset();
}

ScrewMotionOutput ScrewMotionMonitor::update(float commanded_rpm, float actual_rpm,
                                             bool tach_sample_valid, uint32_t now_ms) {
  const uint32_t dt_ms = last_ms_ == 0 ? 0 : now_ms - last_ms_;
  last_ms_ = now_ms;
  if (tach_sample_valid) {
    last_valid_tach_ms_ = now_ms == 0 ? 1 : now_ms;
    if (actual_rpm > 0) cumulative_revolutions_ += actual_rpm * dt_ms / 60000.0f;
  }
  const bool commanded = commanded_rpm >= MIN_COMMAND_RPM;
  const bool recent_tach = last_valid_tach_ms_ != 0 && now_ms - last_valid_tach_ms_ <= TACH_LOSS_TIMEOUT_MS;
  const bool motion_low = actual_rpm < commanded_rpm * MIN_MOTION_RATIO;
  if (commanded && (!recent_tach || motion_low)) {
    if (mismatch_since_ms_ == 0) mismatch_since_ms_ = now_ms == 0 ? 1 : now_ms;
  } else {
    mismatch_since_ms_ = 0;
  }
  const uint32_t mismatch_ms = mismatch_since_ms_ == 0 ? 0 : now_ms - mismatch_since_ms_;
  const DriveSpeedOutput speed = speed_controller_.update(
      commanded_rpm, actual_rpm, tach_sample_valid, commanded, now_ms);
  return {actual_rpm, cumulative_revolutions_, !commanded || recent_tach,
          commanded && mismatch_ms >= MOTION_MISMATCH_DWELL_MS, mismatch_ms,
          speed.target_rpm, speed.pwm, speed.saturated, speed.tach_loss};
}
