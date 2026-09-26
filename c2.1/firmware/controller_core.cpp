// PPR VP1 controller core — portable host-compiled logic only.
// NOT deployable firmware: no target build, no flash, no energization
// (build_firmware.py records target_cross_compile/flash/energization as
// DID_NOT_RUN/HOLD).
//
// VP1 Stage 5 (power policy): 500 W is the HARD modeled operating budget;
// the staged allocator refuses any demand that would exceed it. The PSU's
// 24 V / 33 A = 792 W current-derived maximum (800 W nameplate) is hardware
// information, not permission to operate above 500 W. Hardware current
// limiting / the EL interlock requirements are unchanged. The device
// table mirrors c2.1/results/electrical_load.json; M1/M2/fan values are
// UNRATED estimates (motors are not owned references), heaters are
// NAMEPLATE_SOURCE.  Mutual exclusion of the EX-H100 band heaters is a
// structural invariant of the allocator, so a firmware fault can never
// energize two bands; the EL_CURRENT_LIMITER hardware relay interlock
// requirement stands independently (defense in depth).
#include <array>
#include <cassert>
#include <algorithm>
#include <cmath>
#include <limits>
#include <cstdint>
#include <iostream>

enum class State {
  qualification_hold, fault_latched, ready, startup_reject, quality_hold, running
};

struct Limits {
  double maximum_temperature_C;
  double jam_current_A;
  double jam_minimum_rpm;
  std::uint32_t stale_feedback_ms;
  double operational_cap_W;  // hard modeled operating admission limit
};

// Nameplate device table (c2.1/results/electrical_load.json).  M1/M2/fans are
// UNRATED estimates (not-owned references, nameplate current x 24 V; fan
// model only); the EX-H100/EX-H60 heaters are NAMEPLATE_SOURCE values from
// design/assembly.json part names.  These are modeled consumption numbers for
// the allocator, not measured ratings.
struct PowerDevice {
  const char* name;
  double W;
};

enum DeviceIdx {
  DEV_FANS, DEV_H60, DEV_M1, DEV_M2,
  DEV_BAND_A, DEV_BAND_B, DEV_BAND_C, DEV_COUNT
};

constexpr double OPERATIONAL_CAP_W = 500.0;  // hard modeled operating limit
constexpr double PSU_CURRENT_DERIVED_W = 792.0;  // 24 V x 33 A hardware maximum
constexpr double PSU_NAMEPLATE_W = 800.0;     // PSU nameplate (informational)

constexpr std::array<PowerDevice, DEV_COUNT> POWER_DEVICES{{
    {"COOL-FAN triple", 24.0},        // 3 x 8 W (2 tray + 1 duct), UNRATED_ESTIMATE
    {"EX-H60 cartridge", 60.0},       // NAMEPLATE_SOURCE
    {"M1 shredder drive", 196.8},     // UNRATED_ESTIMATE (8.2 A @ 24 V)
    {"M2 extruder drive", 43.2},      // UNRATED_ESTIMATE (1.8 A @ 24 V)
    {"EX-H100 band A", 100.0},        // NAMEPLATE_SOURCE
    {"EX-H100 band B", 100.0},        // NAMEPLATE_SOURCE
    {"EX-H100 band C", 100.0},        // NAMEPLATE_SOURCE
}};
static_assert(POWER_DEVICES[DEV_FANS].W + POWER_DEVICES[DEV_H60].W +
                  POWER_DEVICES[DEV_M1].W + POWER_DEVICES[DEV_M2].W +
                  POWER_DEVICES[DEV_BAND_A].W <= OPERATIONAL_CAP_W,
              "staged schedule must fit inside the hard operating budget");
static_assert(POWER_DEVICES[DEV_FANS].W + POWER_DEVICES[DEV_H60].W +
                  POWER_DEVICES[DEV_M1].W + POWER_DEVICES[DEV_M2].W +
                  POWER_DEVICES[DEV_BAND_A].W + POWER_DEVICES[DEV_BAND_B].W >
              OPERATIONAL_CAP_W,
              "two simultaneous bands exceed the hard operating budget");

struct Inputs {
  std::uint32_t now_ms{};
  double aux_demand_W{};  // modeled auxiliary load (UNRATED, admitted last)
  std::uint32_t last_feedback_ms{};
  std::array<double, 6> temperature_C{};
  std::uint8_t valid_temperature_mask{0x3f};
  double motor_current_A{};
  double motor_rpm{};
  bool qualification_enabled{};
  bool estop_closed{};
  bool guard_closed{};
  bool independent_overtemp_closed{};
  bool fan_required{};
  bool fan_tach_ok{};
  bool buffer_full{};
  bool run_command{};
  // Per-device demand (thermostats closed / branch run commands).
  std::array<bool, 3> h100_demand{};  // band heater thermostat closed
  bool h60_demand{};
  bool m1_run{};
  bool m2_run{};
  std::uint32_t band_rotation_ms{};  // elapsed time driving band rotation
  // Two orthogonal gauge axes, calibrated outside this host-only core.
  // Die->gauge (269mm) is the feedback dead time; gauge->nip (20mm) is
  // material already committed to the puller. Both are tracked by the line
  // model, never replaced by an artificial 20mm control delay.
  bool gauge_valid{};
  std::uint32_t last_gauge_ms{};
  double gauge_major_mm{};
  double gauge_minor_mm{};
  double nominal_puller_speed_mm_s{9.3134338726879};  // PLA 100g/h design target
};

struct DiameterGate {
  // Quality-gate limits (operating, not safety): outside this window the
  // line cannot be producing verifiable in-spec filament.
  double min_plausible_mm{0.8};    // below: broken strand / sensor fault
  double max_plausible_mm{4.0};    // above: die drool / sensor fault
  std::uint32_t stale_ms{1000};
};

// Identical PI step is used by the host runtime and by the reference-feed
// process-model shared library. The state lives in the caller, not a heap.
static double diameter_pi_step(double nominal, double measured, double dt_s,
                               double& integral, double& command) {
  constexpr double target_mm = 1.75, kp = 2.0, ki = 0.15;
  const double error = measured - target_mm;
  const double candidate = integral + error * std::max(0.0, dt_s);
  const double lower = 0.6 * nominal, upper = 1.5 * nominal;
  const double raw = nominal + kp * error + ki * candidate;
  if ((raw > lower && raw < upper) ||
      (raw >= upper && error < 0) ||
      (raw <= lower && error > 0)) integral = candidate;
  command = std::clamp(nominal + kp * error + ki * integral, lower, upper);
  return command;
}

extern "C" double ppr_diameter_pi_step(double nominal, double measured,
                                        double dt_s, double* integral,
                                        double* command) {
  if (!integral || !command || !std::isfinite(nominal) ||
      !std::isfinite(measured) || nominal <= 0)
    return std::numeric_limits<double>::quiet_NaN();
  return diameter_pi_step(nominal, measured, dt_s, *integral, *command);
}

struct Outputs {
  State state{State::qualification_hold};
  bool m1_enable{};
  bool m2_enable{};
  std::array<bool, 3> h100_enable{};
  bool h60_enable{};
  bool fans_enable{};
  bool aux_enable{};
  bool puller_enable{};
  double puller_speed_cmd_mm_s{};
  bool gauge_in_tolerance{};  // gauge location only; not proof of nip/spool quality
  double admitted_W{};
  int rejected_demands{};  // demands refused at the operating budget
};

class Controller {
 public:
  explicit Controller(Limits limits) : limits_(limits) {}

  Outputs step(const Inputs& in, bool manual_reset) {
    if (!in.qualification_enabled) return off(State::qualification_hold);
    const bool stale = in.now_ms - in.last_feedback_ms > limits_.stale_feedback_ms;
    const bool sensor_fault = in.valid_temperature_mask != 0x3f;
    bool overtemperature = false;
    for (double temperature : in.temperature_C)
      overtemperature = overtemperature || temperature > limits_.maximum_temperature_C;
    const bool jam = in.motor_current_A > limits_.jam_current_A &&
                     in.motor_rpm < limits_.jam_minimum_rpm;
    const bool unsafe = !in.estop_closed || !in.guard_closed ||
                        !in.independent_overtemp_closed || stale || sensor_fault ||
                        overtemperature || jam || (in.fan_required && !in.fan_tach_ok);
    if (unsafe) latched_ = true;
    if (manual_reset && !unsafe && !in.run_command) latched_ = false;
    if (latched_) return off(State::fault_latched);
    const bool gauge_fresh = in.gauge_valid &&
        (in.now_ms - in.last_gauge_ms <= gauge_gate_.stale_ms);
    const bool gauge_plausible =
        std::isfinite(in.gauge_major_mm) && std::isfinite(in.gauge_minor_mm) &&
        in.gauge_major_mm >= gauge_gate_.min_plausible_mm &&
        in.gauge_major_mm <= gauge_gate_.max_plausible_mm &&
        in.gauge_minor_mm >= gauge_gate_.min_plausible_mm &&
        in.gauge_minor_mm <= gauge_gate_.max_plausible_mm;
    if (quality_hold_ && manual_reset && !in.run_command &&
        gauge_fresh && gauge_plausible) {
      quality_hold_ = false;
      startup_started_ = gauge_seen_ = pi_seen_ = false;
      integral_ = 0.0;
    }
    if (quality_hold_) return off(State::quality_hold);
    if (!in.run_command || !in.m2_run) {
      // Any stopped/restarted strand needs a new die-to-gauge transit.
      startup_started_ = gauge_seen_ = pi_seen_ = false;
      integral_ = 0.0;
      if (!in.run_command) return off(State::ready);
    }
    if (in.m2_run && (!std::isfinite(in.nominal_puller_speed_mm_s) ||
                      in.nominal_puller_speed_mm_s <= 0)) {
      quality_hold_ = true;
      return off(State::quality_hold);
    }
    // Puller and winder motor demand must be supplied by the selected
    // hardware budget. Unknown is not zero and cannot run M2.
    if (in.m2_run && !(std::isfinite(in.aux_demand_W) &&
                       in.aux_demand_W > 0))
      return off(State::qualification_hold);
    if (in.m2_run && !startup_started_) {
      startup_started_ = true;
      start_ms_ = in.now_ms;
      command_ = in.nominal_puller_speed_mm_s;
    }
    // Without strand at the gauge, refusing M2 creates a startup deadlock.
    // Run at fixed speed while marking ALL startup strand as reject. Only a
    // new sample after a full die->gauge transit can arm feedback. Once armed,
    // a lost or implausible axis latches quality_hold until operator reset.
    if (in.m2_run && !gauge_seen_) {
      const auto minimum_transit_ms = static_cast<std::uint32_t>(
          269000.0 / in.nominal_puller_speed_mm_s);
      if (in.now_ms - start_ms_ >= minimum_transit_ms &&
          in.last_gauge_ms > start_ms_ && gauge_fresh && gauge_plausible)
        gauge_seen_ = true;
    } else if (in.m2_run && (!gauge_fresh || !gauge_plausible)) {
      quality_hold_ = true;
      return off(State::quality_hold);
    }
    Outputs out;
    out.state = in.m2_run && !gauge_seen_ ? State::startup_reject : State::running;
    double load_W = 0.0;
    // Staged concurrency allocator: refuse each demand that would exceed the
    // hard modeled operating budget, without tripping the safety latch.
    const double budget_W = limits_.operational_cap_W < OPERATIONAL_CAP_W
                                ? limits_.operational_cap_W : OPERATIONAL_CAP_W;
    const auto try_admit = [&](bool demanded, const PowerDevice& device,
                               bool* enable) {
      if (!demanded || *enable) return false;
      if (!(device.W >= 0.0) || !(load_W + device.W <= budget_W)) {
        out.rejected_demands += 1;  // logged operating-budget refusal
        return false;
      }
      *enable = true;
      load_W += device.W;
      return true;
    };
    try_admit(in.fan_required, POWER_DEVICES[DEV_FANS], &out.fans_enable);
    try_admit(in.h60_demand, POWER_DEVICES[DEV_H60], &out.h60_enable);
    try_admit(in.m1_run && !in.buffer_full, POWER_DEVICES[DEV_M1], &out.m1_enable);
    try_admit(in.m2_run, POWER_DEVICES[DEV_M2], &out.m2_enable);
    // aux_demand_W covers the unselected puller+winder drives (and any
    // other named auxiliary). Refusing it must also refuse M2.
    try_admit(in.aux_demand_W > 0.0,
              PowerDevice{"modeled auxiliary load", in.aux_demand_W},
              &out.aux_enable);
    if (in.m2_run && (!out.m2_enable || !out.aux_enable)) {
      startup_started_ = false;
      return off(State::qualification_hold);
    }
    // EX-H100 bands are mutually exclusive: the first admitted band ends the
    // band loop, so no later band is even considered.  Bands rotate so heat-up
    // duty and wear share across A/B/C; only bands with thermostat demand are
    // candidates.  This makes count(h100_enable) <= 1 a structural invariant
    // on every path, including faults (off() zeroes every output).
    const int first = static_cast<int>((in.band_rotation_ms / BAND_ROTATION_PERIOD_MS) % 3);
    for (int k = 0; k < 3; ++k) {
      const int idx = (first + k) % 3;
      if (try_admit(in.h100_demand[idx], POWER_DEVICES[DEV_BAND_A + idx],
                    &out.h100_enable[idx]))
        break;
    }
    out.admitted_W = load_W;
    if (out.m2_enable) {
      out.puller_enable = true;
      out.puller_speed_cmd_mm_s = command_;
      if (gauge_seen_ && gauge_fresh && gauge_plausible) {
        if (!pi_seen_ || in.last_gauge_ms != pi_last_ms_) {
          const double dt_s = pi_seen_ ?
              (in.last_gauge_ms - pi_last_ms_) / 1000.0 : 0.0;
          diameter_pi_step(in.nominal_puller_speed_mm_s,
                           std::sqrt(in.gauge_major_mm * in.gauge_minor_mm),
                           dt_s, integral_, command_);
          pi_last_ms_ = in.last_gauge_ms;
          pi_seen_ = true;
        }
        out.puller_speed_cmd_mm_s = command_;
        out.gauge_in_tolerance =
            in.gauge_minor_mm >= 1.70 && in.gauge_major_mm <= 1.80 &&
            in.gauge_major_mm >= in.gauge_minor_mm &&
            in.gauge_major_mm - in.gauge_minor_mm <= 0.05;
      }
    }

    // Structural safety invariant: never more than one 100 W band, and the
    // admitted modeled draw never exceeds the hard operating budget.
    int bands = 0;
    for (bool b : out.h100_enable) bands += b ? 1 : 0;
    assert(bands <= 1);
    assert(load_W <= budget_W);
    (void)bands;
    return out;
  }

 private:
  static constexpr std::uint32_t BAND_ROTATION_PERIOD_MS = 30000;
  static Outputs off(State state) {
    Outputs out;
    out.state = state;
    return out;
  }
  Limits limits_;
  DiameterGate gauge_gate_{};
  bool latched_{true};
  bool quality_hold_{};
  bool startup_started_{};
  bool gauge_seen_{};
  bool pi_seen_{};
  std::uint32_t start_ms_{};
  std::uint32_t pi_last_ms_{};
  double integral_{};
  double command_{};
};

#ifndef PPR_CONTROLLER_LIBRARY
static Inputs safe_inputs() {
  Inputs in;
  in.temperature_C.fill(30.0);
  in.qualification_enabled = true;
  in.estop_closed = in.guard_closed = in.independent_overtemp_closed = true;
  in.fan_required = in.fan_tach_ok = true;
  in.motor_rpm = 120.0;
  // Gauge is unobserved until a new strand reaches x809.
  in.gauge_valid = false;
  in.gauge_major_mm = in.gauge_minor_mm = 1.75;
  return in;
}

static int band_count(const Outputs& out) {
  int bands = 0;
  for (bool b : out.h100_enable) bands += b ? 1 : 0;
  return bands;
}

int main() {
  const Limits limits{60.0, 10.0, 5.0, 500, OPERATIONAL_CAP_W};  // Test values, not certified limits.
  Controller controller(limits);

  // 1: boots latched
  auto in = safe_inputs();
  assert(controller.step(in, false).state == State::fault_latched);
  // 2: manual reset with no fault and no run command
  assert(controller.step(in, true).state == State::ready);
  // 3: run command -> running with admitted motor load
  in.run_command = true;
  in.m1_run = true;
  in.fan_required = true;
  auto out = controller.step(in, false);
  assert(out.state == State::running && out.m1_enable && out.fans_enable);
  assert(out.admitted_W <= OPERATIONAL_CAP_W);
  // 4: independent overtemp opens -> fault latched, everything off
  in.independent_overtemp_closed = false;
  out = controller.step(in, false);
  assert(out.state == State::fault_latched && !out.m1_enable && !out.fans_enable &&
         !out.h60_enable && band_count(out) == 0);
  // 5: fault stays latched after the input clears (manual reset only)
  in.independent_overtemp_closed = true;
  assert(controller.step(in, false).state == State::fault_latched);
  // 6: reset with run command held -> stays latched (no auto-restart)
  assert(controller.step(in, true).state == State::fault_latched);
  in.run_command = false;
  assert(controller.step(in, true).state == State::ready);
  // 7: buffer full -> M1 gated, M2 allowed
  in.run_command = true;
  in.buffer_full = true;
  in.m2_run = true;
  in.aux_demand_W = 20.0;  // screening-only combined puller/winder budget
  out = controller.step(in, false);
  assert(out.state == State::startup_reject && !out.m1_enable &&
         out.m2_enable && out.puller_enable && !out.gauge_in_tolerance);
  in.buffer_full = false;
  // 8: jam
  in.motor_current_A = 11.0;
  in.motor_rpm = 0.0;
  assert(controller.step(in, false).state == State::fault_latched);
  in = safe_inputs();
  // 9: stale feedback
  Controller stale(limits);
  in.now_ms = 501;
  assert(stale.step(in, false).state == State::fault_latched);
  // 10: sensor fault
  Controller sensor(limits);
  in = safe_inputs();
  in.valid_temperature_mask = 0x1f;
  assert(sensor.step(in, false).state == State::fault_latched);
  // 11: fan tach loss
  Controller fan(limits);
  in = safe_inputs();
  in.fan_tach_ok = false;
  assert(fan.step(in, false).state == State::fault_latched);
  // 12: band overtemperature
  Controller temperature(limits);
  in = safe_inputs();
  in.temperature_C[2] = 60.1;
  assert(temperature.step(in, false).state == State::fault_latched);
  // 13: qualification hold
  Controller qualification(limits);
  in = safe_inputs();
  in.qualification_enabled = false;
  assert(qualification.step(in, true).state == State::qualification_hold);

  // 14: full concurrent demand -> exactly one 100 W band, draw inside budget
  Controller power(limits);
  in = safe_inputs();
  assert(power.step(in, true).state == State::ready);  // manual reset unlatches
  in.run_command = true;
  in.fan_required = true;
  in.h60_demand = true;
  in.m1_run = in.m2_run = true;
  in.h100_demand = {true, true, true};
  in.aux_demand_W = 20.0;
  out = power.step(in, false);
  assert(out.state == State::startup_reject && out.puller_enable);
  assert(out.fans_enable && out.h60_enable && out.m1_enable && out.m2_enable);
  assert(band_count(out) == 1);
  assert(out.h100_enable[0]);
  assert(out.admitted_W == 24.0 + 60.0 + 196.8 + 43.2 + 20.0 + 100.0);
  assert(out.admitted_W <= OPERATIONAL_CAP_W);
  // 15: band rotation moves the admitted band, still never two
  in.band_rotation_ms = 30000;
  out = power.step(in, false);
  assert(band_count(out) == 1 && out.h100_enable[1]);
  in.band_rotation_ms = 60000;
  out = power.step(in, false);
  assert(band_count(out) == 1 && out.h100_enable[2]);
  in.band_rotation_ms = 90000;
  out = power.step(in, false);
  assert(band_count(out) == 1 && out.h100_enable[0]);
  // 16: fault under two-band demand energizes no band
  in.band_rotation_ms = 0;
  in.independent_overtemp_closed = false;
  out = power.step(in, false);
  assert(out.state == State::fault_latched && band_count(out) == 0 &&
         !out.h60_enable);
  // 17: reduced 400 W hard budget refuses the band, preserving base loads
  const Limits tight{60.0, 10.0, 5.0, 500, 400.0};
  Controller budget_limited(tight);
  in = safe_inputs();
  assert(budget_limited.step(in, true).state == State::ready);
  in.run_command = true;
  in.h60_demand = true;
  in.m1_run = in.m2_run = true;
  in.fan_required = true;
  in.h100_demand = {true, true, true};
  in.aux_demand_W = 20.0;
  out = budget_limited.step(in, false);
  assert(band_count(out) == 0);
  assert(out.m1_enable && out.m2_enable && out.h60_enable && out.fans_enable);
  assert(out.admitted_W == 344.0 && out.rejected_demands == 3);

  // 18: 574 W requested (324 W base + 150 W aux + 100 W band);
  //     accept the aux first and refuse every band at the 500 W budget
  Controller overload(limits);
  in = safe_inputs();
  assert(overload.step(in, true).state == State::ready);
  in.run_command = true;
  in.fan_required = true;
  in.h60_demand = true;
  in.m1_run = in.m2_run = true;
  in.h100_demand = {true, true, true};
  in.aux_demand_W = 150.0;
  out = overload.step(in, false);
  assert(out.state == State::startup_reject);
  assert(out.aux_enable && band_count(out) == 0);
  assert(out.admitted_W == 474.0 && out.rejected_demands == 3);
  // The PSU's 792 W hardware figure cannot override the operating cap.
  Controller psu_not_budget{Limits{60.0, 10.0, 5.0, 500, PSU_CURRENT_DERIVED_W}};
  in.run_command = false;
  assert(psu_not_budget.step(in, true).state == State::ready);
  in.run_command = true;
  const auto capped = psu_not_budget.step(in, false);
  assert(capped.admitted_W == 474.0 && band_count(capped) == 0);
  // 19: exact 500 W admission is permitted (324 W base + 176 W aux).
  in.aux_demand_W = 176.0;
  out = overload.step(in, false);
  assert(out.aux_enable && band_count(out) == 0);
  assert(out.admitted_W == OPERATIONAL_CAP_W);
  // 20: an unaffordable puller/winder demand cannot run M2 alone.
  in.aux_demand_W = 500.0;
  out = overload.step(in, false);
  assert(out.state == State::qualification_hold && !out.m2_enable &&
         !out.puller_enable && out.admitted_W == 0.0);

  // 21: no initial strand at the gauge: M2 and puller run at fixed speed,
  // but all startup filament is explicitly unverified, not sold as good.
  Controller gauge(limits);
  in = safe_inputs();
  assert(gauge.step(in, true).state == State::ready);
  in.run_command = in.m2_run = true;
  in.aux_demand_W = 20.0;
  out = gauge.step(in, false);
  assert(out.state == State::startup_reject && out.puller_enable &&
         !out.gauge_in_tolerance &&
         out.puller_speed_cmd_mm_s == in.nominal_puller_speed_mm_s);
  // 22: a NEW plausible sample after the 269mm die->gauge transit arms PI.
  in.now_ms = in.last_feedback_ms = in.last_gauge_ms = 30000;
  in.gauge_valid = true;
  out = gauge.step(in, false);
  assert(out.state == State::running && out.gauge_in_tolerance);
  // 23: thick strand speeds the puller; repeated identical sample does NOT
  // integrate repeatedly; both axes must be within tolerance for gauge_ok.
  in.now_ms = in.last_feedback_ms = in.last_gauge_ms = 31000;
  in.gauge_major_mm = in.gauge_minor_mm = 1.90;
  out = gauge.step(in, false);
  assert(out.puller_speed_cmd_mm_s > in.nominal_puller_speed_mm_s &&
         !out.gauge_in_tolerance);
  const double previous_command = out.puller_speed_cmd_mm_s;
  in.now_ms = in.last_feedback_ms = 31050;
  assert(gauge.step(in, false).puller_speed_cmd_mm_s == previous_command);
  in.now_ms = in.last_feedback_ms = in.last_gauge_ms = 31100;
  in.gauge_major_mm = 1.84;
  in.gauge_minor_mm = 1.66;
  assert(!gauge.step(in, false).gauge_in_tolerance); // ovality not hidden by mean
  // 24: a dropout after feedback is armed LATCHES quality hold. Restoring a
  // sample while run_command stays high never auto-restarts M2 or puller.
  in.now_ms = in.last_feedback_ms = 32000;
  in.gauge_valid = false;
  out = gauge.step(in, false);
  assert(out.state == State::quality_hold && !out.m2_enable &&
         !out.puller_enable && !out.h60_enable);
  in.gauge_valid = true;
  in.gauge_major_mm = in.gauge_minor_mm = 1.75;
  in.last_gauge_ms = in.last_feedback_ms = in.now_ms = 32100;
  assert(gauge.step(in, false).state == State::quality_hold);
  in.run_command = false;
  assert(gauge.step(in, true).state == State::ready);
  in.run_command = true;
  in.now_ms = in.last_feedback_ms = 32200;
  assert(gauge.step(in, false).state == State::startup_reject);
  in.now_ms = in.last_feedback_ms = in.last_gauge_ms = 61200;
  assert(gauge.step(in, false).state == State::running);
  // 25: stale sample triggers another hold, not an implicit good diameter.
  in.now_ms = in.last_feedback_ms = 62500;
  out = gauge.step(in, false);
  assert(out.state == State::quality_hold && !out.puller_enable);
  // 26: M2 cannot run if the unselected auxiliary motor budget is missing.
  Controller missing_aux(limits);
  in = safe_inputs();
  assert(missing_aux.step(in, true).state == State::ready);
  in.run_command = in.m2_run = true;
  out = missing_aux.step(in, false);
  assert(out.state == State::qualification_hold && !out.m2_enable);
  // 27: voluntary stop and restart re-rejects the entire new transit;
  // retained old gauge readings must not arm a freshly formed strand.
  Controller restart(limits);
  in = safe_inputs();
  assert(restart.step(in, true).state == State::ready);
  in.run_command = in.m2_run = true;
  in.aux_demand_W = 20.0;
  assert(restart.step(in, false).state == State::startup_reject);
  in.last_feedback_ms = in.last_gauge_ms = in.now_ms = 30000;
  in.gauge_valid = true;
  assert(restart.step(in, false).state == State::running);
  in.run_command = false;
  assert(restart.step(in, false).state == State::ready);
  in.run_command = true;
  in.last_feedback_ms = in.now_ms = 30100;
  assert(restart.step(in, false).state == State::startup_reject);
  // 28: shared PI kernel bounds persistent error and preserves finite output.
  double integral = 0.0, command = 9.3134338726879;
  for (int i = 0; i < 500; ++i)
    ppr_diameter_pi_step(9.3134338726879, 3.5, 0.1,
                         &integral, &command);
  assert(command <= 1.5 * 9.3134338726879 && command > 9.3134338726879);


  std::cout << "controller_core_self_test: 28 cases passed; quality hold "
               "has no auto-restart path; band mutual exclusion; hard operating budget "
               << static_cast<int>(OPERATIONAL_CAP_W) << " W; PSU "
               "current-derived maximum " << static_cast<int>(PSU_CURRENT_DERIVED_W)
               << " W (24 V x 33 A; nameplate "
               << static_cast<int>(PSU_NAMEPLATE_W) << " W) is not operating permission\n";
}
#endif  // PPR_CONTROLLER_LIBRARY