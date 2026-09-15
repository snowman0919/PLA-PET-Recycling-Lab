#pragma once
// These flags are NOT permission to bypass a test. Record evidence before changing.
namespace GgmCommissioning {
constexpr const char* PROFILE = "GGM-DRIVE-v0.8-r1";
constexpr bool RECEIPT_LIMITER_CURRENT_AND_WIRING_VERIFIED = false;
constexpr float SH_GEARBOX_NM_PER_AMP = 0.0f;
constexpr float EX_GEARBOX_NM_PER_AMP = 0.0f;
constexpr float SH_NO_LOAD_CURRENT_A = 0.0f;
constexpr float EX_NO_LOAD_CURRENT_A = 0.0f;
constexpr float EX_CURRENT_ZERO_ADC = 512.0f;
constexpr float EX_CURRENT_AMPS_PER_COUNT = 0.0f;
}
