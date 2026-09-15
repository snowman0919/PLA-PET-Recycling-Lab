#pragma once
#include <math.h>
#include <stdint.h>

struct GgmInput {
  uint32_t now_ms;
  int16_t shredder, screw;
  float motor_current_a, shredder_rpm, screw_rpm;
  float gearbox_nm_per_amp, no_load_current_a;
  uint32_t shredder_tach_startup_grace_ms, screw_tach_startup_grace_ms;
  bool profile_verified, safety_ok, current_feedback_valid;
  bool shredder_tach_valid, screw_tach_valid, shredder_stopped_observed;
};

struct GgmOutput { int16_t shredder, screw; bool fault; };

class GgmDriveGuard {
 public:
  GgmOutput update(const GgmInput &i) {
    GgmOutput out{0, 0, latched_};
    const bool shredder_requested = i.shredder != 0;
    const bool screw_requested = i.screw != 0;
    if (!shredder_requested && !screw_requested) {
      resetMotionTracking(); waiting_ = false; return out;
    }
    if (latched_) return out;
    if (!i.profile_verified || !i.safety_ok) return out;
    if ((shredder_requested && screw_requested) || i.screw < 0) return latch(out);
    if (!i.current_feedback_valid || !finiteActive(i, shredder_requested)) return latch(out);
    const float torque = fmaxf(0, fabsf(i.motor_current_a) - i.no_load_current_a) * i.gearbox_nm_per_amp;
    if (fabsf(i.motor_current_a) > 6.0f || torque > 8.0f) return latch(out);
    if (shredder_requested && fabsf(i.shredder_rpm) > 21.0f) return latch(out);
    if (screw_requested && fabsf(i.screw_rpm) > 20.0f) return latch(out);
    if (shredder_requested) {
      const int8_t requested_direction = i.shredder < 0 ? -1 : 1;
      if (requested_direction != direction_) {
        resetMotionTracking();
        if (!waiting_) { waiting_ = true; wait_start_ms_ = i.now_ms; }
        if (uint32_t(i.now_ms - wait_start_ms_) < 500 || fabsf(i.shredder_rpm) > 1.0f ||
            !i.shredder_stopped_observed) return out;
        direction_ = requested_direction;
        waiting_ = false;
      } else {
        waiting_ = false;
      }
      if (!tachAllows(Axis::SHREDDER, i.shredder_tach_valid,
                      i.shredder_tach_startup_grace_ms, i.now_ms)) return latch(out);
      out.shredder = clamp(i.shredder);
    } else {
      waiting_ = false;
      if (!tachAllows(Axis::SCREW, i.screw_tach_valid,
                      i.screw_tach_startup_grace_ms, i.now_ms)) return latch(out);
      out.screw = clamp(i.screw);
    }
    out.fault = latched_;
    return out;
  }

  bool faulted() const { return latched_; }

  bool clear(bool user_ack, float current, float sh_rpm, float ex_rpm) {
    if (!user_ack || !isfinite(current) || !isfinite(sh_rpm) || !isfinite(ex_rpm) ||
        fabsf(current) > .2f || fabsf(sh_rpm) > 1.0f || fabsf(ex_rpm) > 1.0f) return false;
    latched_ = false; waiting_ = false; resetMotionTracking(); return true;
  }

  static uint8_t heaterMask(uint8_t requested, bool motor_requested, uint8_t first) {
    const uint16_t watts[4] = {100, 100, 100, 60};
    const uint16_t cap = motor_requested ? 300 : 360;
    uint16_t sum = 0; uint8_t mask = 0;
    for (uint8_t n = 0; n < 4; ++n) {
      const uint8_t bit = (first + n) % 4;
      if ((requested & (1U << bit)) && sum + watts[bit] <= cap) {
        sum += watts[bit]; mask |= 1U << bit;
      }
    }
    return mask;
  }
 private:
  enum class Axis : uint8_t { NONE, SHREDDER, SCREW };

  static bool finiteActive(const GgmInput &i, bool shredder_requested) {
    const float active_rpm = shredder_requested ? i.shredder_rpm : i.screw_rpm;
    return isfinite(i.motor_current_a) && isfinite(active_rpm) &&
        isfinite(i.gearbox_nm_per_amp) && isfinite(i.no_load_current_a) &&
        i.gearbox_nm_per_amp > 0.0f && i.no_load_current_a >= 0.0f;
  }

  bool tachAllows(Axis axis, bool valid, uint32_t grace_ms, uint32_t now_ms) {
    if (grace_ms == 0) return false;
    if (motion_axis_ != axis) {
      motion_axis_ = axis;
      motion_started_ms_ = now_ms;
      tach_seen_ = false;
    }
    if (valid) {
      tach_seen_ = true;
      return true;
    }
    if (tach_seen_) return false;
    return uint32_t(now_ms - motion_started_ms_) < grace_ms;
  }

  GgmOutput latch(GgmOutput out) {
    latched_ = true;
    out.shredder = 0; out.screw = 0; out.fault = true;
    return out;
  }

  void resetMotionTracking() {
    motion_axis_ = Axis::NONE;
    motion_started_ms_ = 0;
    tach_seen_ = false;
  }

  static int16_t clamp(int16_t v) { return v > 255 ? 255 : (v < -255 ? -255 : v); }

  bool latched_ = false, waiting_ = false, tach_seen_ = false;
  uint32_t wait_start_ms_ = 0, motion_started_ms_ = 0;
  int8_t direction_ = 1;
  Axis motion_axis_ = Axis::NONE;
};
