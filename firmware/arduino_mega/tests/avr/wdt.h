#pragma once

constexpr int WDTO_2S = 0;
inline void wdt_enable(int) {}
inline void wdt_reset() {}
