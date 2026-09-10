#include "drive_speed_control.h"

static_assert(sizeof(int16_t) == 2, "Drive PWM ABI requires a 16-bit signed value");
