#include <cassert>
#include <cmath>
#include <iostream>

#include "traverse_control.h"
#include "traverse_homing.h"

namespace {
const TraverseHomingConfig kConfig{10.0f, 0.3f, 2, 100, 10};

void finishBackoff(TraverseHomingController &homing, uint32_t first_ms) {
  TraverseHomingOutput out{};
  for (uint32_t now = first_ms; now <= first_ms + 10; now += 2) {
    out = homing.update(false, false, true, now);
    if (out.homed) break;
    assert(out.enable && out.direction);
  }
  assert(out.state == TraverseHomingState::TRAVERSE_READY && out.homed && !out.enable);
  assert(std::fabs(out.estimated_position_mm - 0.3f) < 0.001f);
}

uint32_t stepsToHalfMillimetre(float steps_per_mm) {
  TraverseController traverse;
  assert(traverse.configure({5.0f, 0.5f, steps_per_mm, 100}));
  traverse.invalidatePosition();
  assert(!traverse.update(1.0f, false, false, true, 2).enable);
  traverse.setHomedPosition(0);
  uint32_t pulses = 0;
  for (uint32_t now = 2; now < 1000; now += 2) {
    const auto out = traverse.update(1.0f, false, false, true, now);
    if (out.step) ++pulses;
    if (out.estimated_position_mm >= 0.5f - 0.001f) break;
  }
  return pulses;
}
}

int main() {
  // Boot at the left endpoint: release the switch, back off a calibrated distance, then ready.
  TraverseHomingController left_boot;
  assert(left_boot.configure(kConfig));
  auto out = left_boot.update(true, false, true, 0);
  assert(out.state == TraverseHomingState::TRAVERSE_BACKOFF && out.enable && out.direction);
  finishBackoff(left_boot, 2);

  // Boot in the middle: seek left first.
  TraverseHomingController middle_boot;
  assert(middle_boot.configure(kConfig));
  out = middle_boot.update(false, false, true, 0);
  assert(out.state == TraverseHomingState::TRAVERSE_HOME_LEFT && out.enable && !out.direction);
  out = middle_boot.update(true, false, true, 20);
  assert(out.state == TraverseHomingState::TRAVERSE_BACKOFF);
  finishBackoff(middle_boot, 22);

  // Boot at the right endpoint: the right switch must release while seeking left.
  TraverseHomingController right_boot;
  assert(right_boot.configure(kConfig));
  out = right_boot.update(false, true, true, 0);
  assert(out.state == TraverseHomingState::TRAVERSE_HOME_LEFT && !out.direction);
  right_boot.update(false, false, true, 2);
  out = right_boot.update(true, false, true, 20);
  assert(out.state == TraverseHomingState::TRAVERSE_BACKOFF);
  finishBackoff(right_boot, 22);

  // Open left switch becomes a bounded homing timeout.
  TraverseHomingController open_left;
  assert(open_left.configure(kConfig));
  open_left.update(false, false, true, 0);
  out = open_left.update(false, false, true, 101);
  assert(out.state == TraverseHomingState::TRAVERSE_FAULT);
  assert(out.fault == TraverseHomingFault::HOME_TIMEOUT && !out.enable);

  TraverseHomingController stuck_left;
  assert(stuck_left.configure(kConfig));
  stuck_left.update(true, false, true, 0);
  out = stuck_left.update(true, false, true, 11);
  assert(out.fault == TraverseHomingFault::LEFT_SWITCH_STUCK);

  TraverseHomingController stuck_right;
  assert(stuck_right.configure(kConfig));
  stuck_right.update(false, true, true, 0);
  out = stuck_right.update(false, true, true, 11);
  assert(out.fault == TraverseHomingFault::RIGHT_SWITCH_STUCK);

  // An unexpected right endpoint while commanding left proves a direction/plausibility fault.
  TraverseHomingController wrong_direction;
  assert(wrong_direction.configure(kConfig));
  wrong_direction.update(false, false, true, 0);
  out = wrong_direction.update(false, true, true, 2);
  assert(out.fault == TraverseHomingFault::WRONG_DIRECTION);

  TraverseHomingController conflict;
  assert(conflict.configure(kConfig));
  out = conflict.update(true, true, true, 0);
  assert(out.fault == TraverseHomingFault::LIMIT_CONFLICT);

  // Power/position loss always returns to UNHOMED and removes motion eligibility.
  left_boot.setRunning(true);
  assert(left_boot.state() == TraverseHomingState::TRAVERSE_RUNNING);
  left_boot.losePosition();
  assert(left_boot.state() == TraverseHomingState::TRAVERSE_UNHOMED && !left_boot.homed());

  // The calibrated steps/mm changes the actual emitted step count; it is not metadata-only.
  const uint32_t steps_at_10 = stepsToHalfMillimetre(10.0f);
  const uint32_t steps_at_20 = stepsToHalfMillimetre(20.0f);
  assert(steps_at_10 == 5 && steps_at_20 == 10);

  // A homed running controller still detects a missed right endpoint.
  TraverseController missed_endpoint;
  assert(missed_endpoint.configure({2.0f, 0.5f, 2.0f, 10}));
  missed_endpoint.invalidatePosition();
  missed_endpoint.setHomedPosition(0);
  missed_endpoint.update(2.0f, false, false, true, 2);
  missed_endpoint.update(2.0f, false, false, true, 4);
  out = TraverseHomingOutput{};
  auto traverse_out = missed_endpoint.update(4.0f, false, false, true, 6);
  assert(!traverse_out.hard_fault);
  traverse_out = missed_endpoint.update(4.0f, false, false, true, 17);
  assert(traverse_out.hard_fault);

  std::cout << "TRAVERSE_EXPLICIT_HOMING_LIMIT_CALIBRATION_OK\n";
}
