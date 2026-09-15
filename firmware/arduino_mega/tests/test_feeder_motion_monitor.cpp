#include <assert.h>
#include <stdint.h>

#include "../src/feeder_motion_monitor.h"

int main() {
  FeederMotionMonitor monitor(2000);
  assert(monitor.update(false, false, 0));
  assert(monitor.update(true, false, 1));
  assert(monitor.update(true, true, 1900));
  assert(monitor.update(true, false, 3800));
  assert(!monitor.update(true, false, 3901));
  assert(monitor.update(false, false, 3902));
  assert(monitor.update(true, false, UINT32_MAX - 500));
  assert(monitor.update(true, false, 1000));
  assert(!monitor.update(true, false, 1600));
}
