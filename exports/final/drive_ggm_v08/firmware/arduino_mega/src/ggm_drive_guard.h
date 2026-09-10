#pragma once
#include <stdint.h>
#include <math.h>

struct GgmInput {
  uint32_t now_ms, feedback_ms;
  int16_t shredder, screw;
  float motor_current_a, shredder_rpm, screw_rpm;
  float gearbox_nm_per_amp, no_load_current_a;
  bool profile_verified, safety_ok, feedback_valid, stopped_observed;
};
struct GgmOutput { int16_t shredder, screw; bool fault; };
class GgmDriveGuard {
 public:
  GgmOutput update(const GgmInput &i) {
    GgmOutput o{0,0,latched_};
    const bool finite = isfinite(i.motor_current_a) && isfinite(i.shredder_rpm) &&
        isfinite(i.screw_rpm) && isfinite(i.gearbox_nm_per_amp) && isfinite(i.no_load_current_a);
    if (!i.profile_verified || !i.safety_ok || !finite || !i.feedback_valid ||
        uint32_t(i.now_ms-i.feedback_ms)>100 || i.gearbox_nm_per_amp<=0 || i.no_load_current_a<0) return o;
    const float torque=fmaxf(0, fabsf(i.motor_current_a)-i.no_load_current_a)*i.gearbox_nm_per_amp;
    if ((i.shredder && i.screw) || i.screw<0 || fabsf(i.motor_current_a)>6.0f ||
        torque>8.0f || fabsf(i.shredder_rpm)>21 || fabsf(i.screw_rpm)>20) latched_=true;
    o.fault=latched_; if (latched_) return o;
    const int8_t next=i.shredder<0 ? -1 : 1;
    if (i.shredder && next!=direction_) {
      if (!waiting_) {waiting_=true; wait_start_=i.now_ms;}
      if (uint32_t(i.now_ms-wait_start_)<500 || fabsf(i.shredder_rpm)>1 || !i.stopped_observed) return o;
      direction_=next; waiting_=false;
    } else if (i.shredder) waiting_=false;
    o.shredder=clamp(i.shredder); o.screw=clamp(i.screw); return o;
  }
  bool faulted() const { return latched_; }
  bool clear(bool user_ack, float current, float sh_rpm, float ex_rpm) {
    if (!user_ack || !isfinite(current) || !isfinite(sh_rpm) || !isfinite(ex_rpm) ||
        fabsf(current)>.2f || fabsf(sh_rpm)>1 || fabsf(ex_rpm)>1) return false;
    latched_=false; waiting_=false; return true;
  }
  static uint8_t heaterMask(uint8_t requested, bool motor_requested, uint8_t first) {
    const uint16_t watts[4]={100,100,100,60};
    const uint16_t cap=motor_requested ? 300 : 360;
    uint16_t sum=0; uint8_t mask=0;
    for (uint8_t n=0;n<4;++n) {
      const uint8_t bit=(first+n)%4;
      if ((requested & (1U<<bit)) && sum+watts[bit]<=cap) {sum+=watts[bit];mask|=1U<<bit;}
    }
    return mask;
  }
 private:
  static int16_t clamp(int16_t v) {return v>255 ? 255 : v< -255 ? -255 : v;}
  bool latched_=false, waiting_=false;
  uint32_t wait_start_=0;
  int8_t direction_=1;
};
