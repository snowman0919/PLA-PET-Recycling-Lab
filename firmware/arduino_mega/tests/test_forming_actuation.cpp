#include <cassert>
#include <cmath>
#include <iostream>

#include "cooling_monitor.h"
#include "puller_speed_control.h"
#include "screw_motion_monitor.h"
#include "spooler_control.h"
#include "traverse_control.h"

int main() {
  PullerSpeedController puller;
  const PullerCalibration puller_cal{30.0f, 20.0f, 160.0f, 3.0f, 1.2f, 45, 255,
                                     500, 600, 800, 2.0f};
  assert(puller.configure(puller_cal));
  auto po = puller.update(200.0f, 0.0f, false, true, 1);
  assert(!po.saturated);  // startup ramp/grace must resist a one-sample false positive.
  po = puller.update(200.0f, 0.0f, false, true, 501);
  assert(!po.saturated);
  po = puller.update(200.0f, 0.0f, false, true, 1402);
  assert(po.pwm_limited && po.saturated && !po.tach_valid && po.saturation_duration_ms >= 800);
  po = puller.update(20.0f, 12.7f, true, true, 1422);
  assert(!po.saturated && po.tach_valid && std::fabs(po.speed_error_mm_s) < 0.2f);

  ScrewMotionMonitor screw;
  auto so = screw.update(4.0f, 0.0f, false, 1);
  assert(!so.command_motion_mismatch);
  so = screw.update(4.0f, 0.0f, false, 1602);
  assert(so.command_motion_mismatch && !so.tach_valid);
  screw.reset();
  screw.update(4.0f, 4.0f, true, 100);
  so = screw.update(4.0f, 4.0f, true, 60100);
  assert(so.tach_valid && so.cumulative_revolutions > 3.9f);

  CoolingMonitor cooling;
  auto co = cooling.update(200, 1800.0f, true, 1700.0f, true, 1);
  assert(co.valid && co.fault_bits == COOLING_FAULT_NONE);
  co = cooling.update(200, 0.0f, true, 1700.0f, true, 2);
  assert(!co.valid && (co.fault_bits & COOLING_FAN1_STOPPED));
  co = cooling.update(200, 0.0f, true, 0.0f, true, 1603);
  assert(!co.valid && (co.fault_bits & COOLING_FAN1_STOPPED) &&
         (co.fault_bits & COOLING_FAN2_STOPPED));
  cooling.reset();
  cooling.update(0, 1200.0f, true, 0.0f, true, 1);
  co = cooling.update(0, 1200.0f, true, 0.0f, true, 1602);
  assert(!co.valid && (co.fault_bits & COOLING_IMPLAUSIBLE_WHILE_OFF));

  SpoolerController spooler;
  assert(spooler.configure({26.0f, 100.0f, 68.0f, 1.75f, 0.0f, 180.0f, 45.0f,
                            42, 220, 800, 900}));
  auto spo = spooler.update(35.0f, 0.05f, 12.0f, true, true, 1);
  assert(!spo.jam && spo.estimated_radius_mm >= 26.0f);
  for (uint32_t t = 21; t < 4021; t += 20)
    spo = spooler.update(35.0f, 0.02f, 12.0f, true, true, t);
  assert(spo.cumulative_turns > 0.5f && spo.estimated_radius_mm >= 26.0f);
  spooler.reset();
  spooler.update(35.0f, 0.3f, 0.0f, false, true, 1);
  spooler.update(35.0f, 0.3f, 0.0f, false, true, 1902);
  spo = spooler.update(35.0f, 0.3f, 0.0f, false, true, 2903);
  assert(spo.jam);  // controlled-stop policy can act before the mechanical dancer limit.

  TraverseController traverse;
  assert(traverse.configure({68.0f, 1.85f, 80.0f, 1000}));
  auto tr = traverse.update(1.0f, false, false, true, 2);
  assert(tr.enable && tr.pitch_synchronized && tr.direction);
  const float first_target = tr.target_position_mm;
  tr = traverse.update(40.0f, false, false, true, 4);
  assert(tr.target_position_mm != first_target);  // target is tied to turns, not wall-clock reversal.
  tr = traverse.update(1.0f, false, false, false, 6);
  assert(!tr.enable && !tr.step);

  TraverseController missed_limit;
  assert(missed_limit.configure({2.0f, 0.5f, 2.0f, 10}));
  // Cross the interior and reach the right endpoint without feedback.
  missed_limit.update(2.0f, false, false, true, 2);
  missed_limit.update(2.0f, false, false, true, 4);
  tr = missed_limit.update(4.0f, false, false, true, 6);
  assert(!tr.hard_fault);
  tr = missed_limit.update(4.0f, false, false, true, 17);
  assert(tr.hard_fault);

  std::cout << "FORMING_ACTUATION_CLOSED_LOOPS_OK\n";
}
