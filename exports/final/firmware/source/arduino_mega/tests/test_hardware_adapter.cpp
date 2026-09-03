#include <assert.h>
#include <math.h>
#include <stdint.h>

#include <fstream>
#include <iostream>

#include "puller_speed_control.h"
#include "screw_motion_monitor.h"
#include "shredder_control.h"
#include "spooler_control.h"
#include "tach_contract_generated.h"
#include "tach_estimator.h"

namespace {
class QuantizedDrivePlant {
 public:
  QuantizedDrivePlant(const TachEstimatorConfig &tach_config, uint8_t dead_zone,
                      uint8_t maximum_pwm, float minimum_stable_rpm, float maximum_rpm)
      : config_(tach_config), dead_zone_(dead_zone), maximum_pwm_(maximum_pwm),
        minimum_stable_rpm_(minimum_stable_rpm), maximum_rpm_(maximum_rpm) {
    assert(tach_.configure(config_));
  }

  TachEstimate advance(uint32_t now_us, int16_t pwm, float load_scale = 1.0f,
                       bool feedback_connected = true) {
    const uint32_t dt_us = initialized_ ? now_us - last_us_ : 0U;
    initialized_ = true;
    last_us_ = now_us;
    const float magnitude = static_cast<float>(pwm < 0 ? -pwm : pwm);
    float target_rpm = 0.0f;
    if (magnitude >= dead_zone_) {
      target_rpm = (minimum_stable_rpm_ + (magnitude - dead_zone_) /
          static_cast<float>(maximum_pwm_ - dead_zone_) *
          (maximum_rpm_ - minimum_stable_rpm_)) * load_scale;
    }
    rpm_ += 0.16f * (target_rpm - rpm_);
    if (rpm_ < 0.01f) rpm_ = 0.0f;
    if (feedback_connected && dt_us > 0 && rpm_ > 0) {
      pulse_phase_ += rpm_ * config_.pulses_per_revolution * dt_us / 60000000.0f;
      while (pulse_phase_ >= 1.0f) {
        tach_.onPulse(now_us);
        pulse_phase_ -= 1.0f;
      }
    }
    return tach_.estimate(now_us);
  }

  float rpm() const { return rpm_; }

 private:
  TachEstimatorConfig config_;
  TachEstimator tach_;
  uint8_t dead_zone_;
  uint8_t maximum_pwm_;
  float minimum_stable_rpm_;
  float maximum_rpm_;
  float rpm_{0};
  float pulse_phase_{0};
  bool initialized_{false};
  uint32_t last_us_{0};
};

struct Trace {
  explicit Trace(const char *path) {
    if (path != nullptr) {
      stream.open(path);
      stream << "drive,scenario,time_ms,target_rpm,estimated_rpm,plant_rpm,pwm,tach_valid,"
                "adc_count,current_amp,radius_mm,wound_length_mm\n";
    }
  }
  void row(const char *drive, const char *scenario, uint32_t time_ms, float target,
           const TachEstimate &tach, float plant_rpm, int16_t pwm, int adc = 0,
           float current = 0, float radius = 0, float length = 0) {
    if (!stream.is_open() || (time_ms % 200U != 0U && pwm != 0)) return;
    stream << drive << ',' << scenario << ',' << time_ms << ',' << target << ','
           << tach.rpm << ',' << plant_rpm << ',' << pwm << ',' << tach.valid << ','
           << adc << ',' << current << ',' << radius << ',' << length << '\n';
  }
  std::ofstream stream;
};

void verifyShredder(Trace &trace) {
  ShredderController controller;
  DriveCalibration calibration = REFERENCE_DRIVE_CALIBRATION;
  calibration.verified = true;
  assert(controller.configureDrive(calibration));
  QuantizedDrivePlant plant(SHREDDER_TACH_CONFIG, 35, 255, 5.0f, 40.0f);
  ShredderInputs input{0, 2.0f, 0.0f, true, false, false};
  assert(controller.start(PLA_PROFILE, input));
  ShredderOutput output{};
  int16_t pwm = 0;
  for (uint32_t ms = 0; ms <= 12000; ms += 20) {
    const bool load_step = ms >= 6000;
    const int adc = 512 + static_cast<int>((load_step ? 4.0f : 2.0f) / 0.05f + 0.5f);
    input.current_amp = (adc - 512) * 0.05f;  // Same quantized value seen at the adapter boundary.
    const TachEstimate tach = plant.advance(ms * 1000U, pwm, load_step ? 0.82f : 1.0f);
    input.now_ms = ms;
    input.cutter_rpm = tach.rpm;
    input.tach_valid = tach.valid;
    output = controller.update(input);
    pwm = output.pwm;
    trace.row("shredder", load_step ? "load_step" : "nominal", ms, output.target_rpm,
              tach, plant.rpm(), pwm, adc, input.current_amp);
  }
  assert(output.command == ShredderCommand::FORWARD);
  assert(output.tach_valid && output.pwm > 0);
  assert(fabsf(output.target_rpm - plant.rpm()) / output.target_rpm < 0.20f);

  // Disconnecting feedback cannot leave a commanded drive running indefinitely.
  for (uint32_t ms = 12020; ms <= 18000 && !controller.faultLatched(); ms += 20) {
    const TachEstimate tach = plant.advance(ms * 1000U, pwm, 1.0f, false);
    input.now_ms = ms;
    input.cutter_rpm = tach.rpm;
    input.tach_valid = tach.valid;
    output = controller.update(input);
    pwm = output.pwm;
    trace.row("shredder", "tach_loss", ms, output.target_rpm, tach, plant.rpm(), pwm);
  }
  assert(controller.faultLatched() && pwm == 0);
}

void verifyScrew(Trace &trace) {
  ScrewMotionMonitor controller;
  QuantizedDrivePlant plant(SCREW_TACH_CONFIG, 38, 255, 1.0f, 25.0f);
  int16_t pwm = 0;
  ScrewMotionOutput output{};
  for (uint32_t ms = 0; ms <= 18000; ms += 20) {
    const TachEstimate tach = plant.advance(ms * 1000U, pwm, ms >= 9000 ? 0.85f : 1.0f);
    output = controller.update(18.0f, tach.rpm, tach.valid, ms);
    pwm = output.control_pwm;
    trace.row("screw", ms >= 9000 ? "load_step" : "nominal", ms, output.target_rpm,
              tach, plant.rpm(), pwm);
  }
  assert(output.tach_valid && !output.command_motion_mismatch);
  assert(output.cumulative_revolutions > 3.0f);
  assert(fabsf(18.0f - plant.rpm()) / 18.0f < 0.20f);

  for (uint32_t ms = 18020; ms <= 27000; ms += 20) {
    const TachEstimate tach = plant.advance(ms * 1000U, pwm, 1.0f, false);
    output = controller.update(18.0f, tach.rpm, tach.valid, ms);
    pwm = output.control_pwm;
    trace.row("screw", "tach_loss", ms, output.target_rpm, tach, plant.rpm(), pwm);
    if (output.command_motion_mismatch) break;
  }
  assert(output.tach_loss && output.command_motion_mismatch && output.control_pwm == 0);
}

void verifyPuller(Trace &trace) {
  PullerSpeedController controller;
  const PullerCalibration calibration{30.0f, 20.0f, 45.0f, 3.0f, 1.2f, 45, 255,
                                      800, 4000, 1000, 0.8f, 1.0f, 0.0f};
  assert(controller.configure(calibration));
  QuantizedDrivePlant plant(PULLER_TACH_CONFIG, 45, 255, 1.0f, 45.0f);
  int16_t pwm = 0;
  PullerSpeedOutput output{};
  for (uint32_t ms = 0; ms <= 25000; ms += 20) {
    const TachEstimate tach = plant.advance(ms * 1000U, pwm, ms >= 12000 ? 0.9f : 1.0f);
    output = controller.update(9.28f, tach.rpm, tach.valid, true, ms);
    pwm = output.pwm;
    trace.row("puller", ms >= 12000 ? "slip_load" : "nominal", ms, output.target_rpm,
              tach, plant.rpm(), pwm);
  }
  assert(output.tach_valid && !output.saturated);
  assert(fabsf(output.target_rpm - plant.rpm()) / output.target_rpm < 0.20f);

  PullerSpeedController saturation;
  assert(saturation.configure(calibration));
  PullerSpeedOutput saturated{};
  for (uint32_t ms = 0; ms <= 2400; ms += 200)
    saturated = saturation.update(200.0f, 0.0f, true, true, ms);
  assert(saturated.pwm == 255 && saturated.pwm_limited && saturated.saturated);

  // A command below the calibrated dead zone produces no pulse and is detected.
  QuantizedDrivePlant dead_zone(PULLER_TACH_CONFIG, 45, 255, 1.0f, 45.0f);
  TachEstimate tach{};
  for (uint32_t ms = 0; ms <= 5000; ms += 20)
    tach = dead_zone.advance(ms * 1000U, 44);
  assert(!tach.valid && dead_zone.rpm() == 0.0f);
}

void verifySpoolerAndRadius(Trace &trace) {
  const SpoolerConfig config{26.0f, 100.0f, 68.0f, 1.75f, 0.0f, 20.0f, 5.0f,
                             42, 220, 800, 1200, 0.88f, 0.5f, 8.0f,
                             4.0f, 1.0f, 7500, 1200, 1.0f};
  SpoolerController controller;
  assert(controller.configure(config));
  QuantizedDrivePlant plant(SPOOLER_TACH_CONFIG, 42, 220, 0.5f, 8.0f);
  int16_t pwm = 0;
  SpoolerOutput output{};
  for (uint32_t ms = 0; ms <= 35000; ms += 20) {
    const TachEstimate tach = plant.advance(ms * 1000U, pwm);
    output = controller.update(9.0f, 0.0f, tach.rpm, tach.valid, true, ms);
    pwm = output.pwm;
    trace.row("spooler", "empty_nominal", ms, output.target_rpm, tach, plant.rpm(), pwm,
              0, 0, output.estimated_radius_mm, output.wound_length_mm);
  }
  assert(output.tach_valid && !output.jam);
  assert(fabsf(output.target_rpm - plant.rpm()) / output.target_rpm < 0.25f);
  assert(output.target_rpm >= 0.8f && output.target_rpm <= 6.8f);

  // Empty/half/full volume-conservation references, packing-factor mutation,
  // and explicit reverse/unwind correction.
  SpoolerController radius;
  assert(radius.configure(config));
  assert(fabsf(radius.estimatedRadiusMm() - 26.0f) < 0.001f);
  const float half_radius = 63.0f;
  const float half_length = (half_radius * half_radius - 26.0f * 26.0f) *
      (4.0f * config.packing_factor * config.spool_width_mm) /
      (config.filament_diameter_mm * config.filament_diameter_mm);
  assert(radius.applyMeasuredLengthCorrection(half_length));
  assert(fabsf(radius.estimatedRadiusMm() - half_radius) < 0.01f);
  radius.update(9.0f, 0.0f, 0.0f, true, true, 0);
  const SpoolerOutput half = radius.update(9.0f, 0.0f, 1.36f, true, true, 1000);
  assert(fabsf(half.target_rpm - 9.0f * 60.0f / (2.0f * 3.14159265358979323846f * half_radius)) < 0.02f);
  const float removed_quarter_mutation = sqrtf(26.0f * 26.0f +
      half_length * config.filament_diameter_mm * config.filament_diameter_mm /
          (config.packing_factor * config.spool_width_mm));
  const float removed_packing_mutation = sqrtf(26.0f * 26.0f +
      half_length * config.filament_diameter_mm * config.filament_diameter_mm /
          (4.0f * config.spool_width_mm));
  assert(fabsf(removed_quarter_mutation - half_radius) > 1.0f);
  assert(fabsf(removed_packing_mutation - half_radius) > 1.0f);
  assert(radius.applyMeasuredLengthCorrection(-half_length));
  assert(fabsf(radius.estimatedRadiusMm() - 26.0f) < 0.01f);
  assert(radius.applyMeasuredLengthCorrection(1.0e9f));
  assert(fabsf(radius.estimatedRadiusMm() - 100.0f) < 0.01f);
  const SpoolerOutput full = radius.update(9.0f, 0.0f, 0.86f, true, true, 2000);
  assert(fabsf(full.target_rpm - 9.0f * 60.0f /
      (2.0f * 3.14159265358979323846f * 100.0f)) < 0.02f);
}
}  // namespace

int main(int argc, char **argv) {
  Trace trace(argc > 1 ? argv[1] : nullptr);
  verifyShredder(trace);
  verifyScrew(trace);
  verifyPuller(trace);
  verifySpoolerAndRadius(trace);
  std::cout << "HARDWARE_ADAPTER_PRODUCTION_DRIVES_OK\n";
  return 0;
}
