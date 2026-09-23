// PPR VP1 controller core — portable host-compiled logic only.
// NOT deployable firmware: no target build, no flash, no energization
// (build_firmware.py records target_cross_compile/flash/energization as
// DID_NOT_RUN/HOLD).
//
// VP1 Stage 5 (power-policy correction): the PSU is 24 V / 33 A = 792 W
// current-derived (800 W nameplate recorded alongside).  500 W is a SOFT
// scheduler target, NOT a hard cap: the staged allocator admits demands up
// to the hard ceiling; a modeled draw above the soft target is admitted and
// flagged WARN+logged (no immediate hard trip), and a demand that would
// exceed the hard ceiling is rejected and logged.  Hardware current
// limiting / the EL interlock requirements are unchanged.  The device
// table mirrors c2.1/results/electrical_load.json; M1/M2/fan values are
// UNRATED estimates (motors are not owned references), heaters are
// NAMEPLATE_SOURCE.  Mutual exclusion of the EX-H100 band heaters is a
// structural invariant of the allocator, so a firmware fault can never
// energize two bands; the EL_CURRENT_LIMITER hardware relay interlock
// requirement stands independently (defense in depth).
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>

enum class State { qualification_hold, fault_latched, ready, running };

struct Limits {
  double maximum_temperature_C;
  double jam_current_A;
  double jam_minimum_rpm;
  std::uint32_t stale_feedback_ms;
  double power_target_W;   // SOFT scheduler target (WARN when exceeded)
  double power_ceiling_W;  // absolute hard ceiling (demands above rejected)
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

constexpr double POWER_TARGET_W = 500.0;      // SOFT scheduler target
constexpr double PSU_HARD_CEILING_W = 792.0;  // 24 V x 33 A current-derived
constexpr double PSU_NAMEPLATE_W = 800.0;     // PSU nameplate (informational)

constexpr std::array<PowerDevice, DEV_COUNT> POWER_DEVICES{{
    {"COOL-FAN pair", 16.0},          // 2 x 8 W, UNRATED_ESTIMATE
    {"EX-H60 cartridge", 60.0},       // NAMEPLATE_SOURCE
    {"M1 shredder drive", 196.8},     // UNRATED_ESTIMATE (8.2 A @ 24 V)
    {"M2 extruder drive", 43.2},      // UNRATED_ESTIMATE (1.8 A @ 24 V)
    {"EX-H100 band A", 100.0},        // NAMEPLATE_SOURCE
    {"EX-H100 band B", 100.0},        // NAMEPLATE_SOURCE
    {"EX-H100 band C", 100.0},        // NAMEPLATE_SOURCE
}};
static_assert(POWER_DEVICES[DEV_FANS].W + POWER_DEVICES[DEV_H60].W +
                  POWER_DEVICES[DEV_M1].W + POWER_DEVICES[DEV_M2].W +
                  POWER_DEVICES[DEV_BAND_A].W <= POWER_TARGET_W,
              "staged schedule must fit inside the soft scheduler target");
static_assert(POWER_DEVICES[DEV_FANS].W + POWER_DEVICES[DEV_H60].W +
                  POWER_DEVICES[DEV_M1].W + POWER_DEVICES[DEV_M2].W +
                  POWER_DEVICES[DEV_BAND_A].W + POWER_DEVICES[DEV_BAND_B].W >
              POWER_TARGET_W,
              "two simultaneous bands exceed the soft target (mutual exclusion "
              "keeps the draw inside it or flags WARN)");

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
};

struct Outputs {
  State state{State::qualification_hold};
  bool m1_enable{};
  bool m2_enable{};
  std::array<bool, 3> h100_enable{};
  bool h60_enable{};
  bool fans_enable{};
  bool aux_enable{};
  double admitted_W{};
  bool over_target{};      // admitted draw above the SOFT target: WARN+logged
  int rejected_demands{};  // demands refused at the hard ceiling
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
    if (!in.run_command) return off(State::ready);

    Outputs out{State::running, false, false, {}, false, false};
    double load_W = 0.0;
    // Staged concurrency allocator: admit demands in priority order while the
    // instantaneous modeled draw stays inside the hard ceiling.  A draw above
    // the SOFT target is admitted and flagged (WARN+logged, no hard trip);
    // only the absolute ceiling rejects.
    const auto try_admit = [&](bool demanded, const PowerDevice& device,
                               bool* enable) {
      if (!demanded || *enable) return false;
      if (load_W + device.W > limits_.power_ceiling_W) {
        out.rejected_demands += 1;  // logged refusal at the hard ceiling
        return false;
      }
      *enable = true;
      load_W += device.W;
      if (load_W > limits_.power_target_W) out.over_target = true;
      return true;
    };
    try_admit(in.fan_required, POWER_DEVICES[DEV_FANS], &out.fans_enable);
    try_admit(in.h60_demand, POWER_DEVICES[DEV_H60], &out.h60_enable);
    try_admit(in.m1_run && !in.buffer_full, POWER_DEVICES[DEV_M1], &out.m1_enable);
    try_admit(in.m2_run, POWER_DEVICES[DEV_M2], &out.m2_enable);
    // Modeled auxiliary load (UNRATED, e.g. a future accessory): admitted
    // under the same semantics, lowest motor-side priority.
    try_admit(in.aux_demand_W > 0.0,
              PowerDevice{"modeled auxiliary load", in.aux_demand_W},
              &out.aux_enable);
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

    // Structural safety invariant: never more than one 100 W band, and the
    // admitted modeled draw never exceeds the current-derived hard ceiling.
    int bands = 0;
    for (bool b : out.h100_enable) bands += b ? 1 : 0;
    assert(bands <= 1);
    assert(load_W <= limits_.power_ceiling_W);
    (void)bands;
    return out;
  }

 private:
  static constexpr std::uint32_t BAND_ROTATION_PERIOD_MS = 30000;
  static Outputs off(State state) {
    return {state, false, false, {}, false, false};
  }
  Limits limits_;
  bool latched_{true};
};

static Inputs safe_inputs() {
  Inputs in;
  in.temperature_C.fill(30.0);
  in.qualification_enabled = true;
  in.estop_closed = in.guard_closed = in.independent_overtemp_closed = true;
  in.fan_required = in.fan_tach_ok = true;
  in.motor_rpm = 120.0;
  return in;
}

static int band_count(const Outputs& out) {
  int bands = 0;
  for (bool b : out.h100_enable) bands += b ? 1 : 0;
  return bands;
}

int main() {
  const Limits limits{60.0, 10.0, 5.0, 500, POWER_TARGET_W, PSU_HARD_CEILING_W};  // Test values, not certified limits.
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
  assert(out.admitted_W <= POWER_TARGET_W);
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
  out = controller.step(in, false);
  assert(out.state == State::running && !out.m1_enable && out.m2_enable);
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
  out = power.step(in, false);
  assert(out.state == State::running);
  assert(out.fans_enable && out.h60_enable && out.m1_enable && out.m2_enable);
  assert(band_count(out) == 1);
  assert(out.h100_enable[0]);
  assert(out.admitted_W == 16.0 + 60.0 + 196.8 + 43.2 + 100.0);
  assert(out.admitted_W <= POWER_TARGET_W && !out.over_target);
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
  // 17: soft target 400 W -> band ADMITTED and flagged WARN (no hard trip)
  const Limits tight{60.0, 10.0, 5.0, 500, 400.0, PSU_HARD_CEILING_W};
  Controller target_limited(tight);
  in = safe_inputs();
  assert(target_limited.step(in, true).state == State::ready);  // manual reset unlatches
  in.run_command = true;
  in.h60_demand = true;
  in.m1_run = in.m2_run = true;
  in.fan_required = true;
  in.h100_demand = {true, true, true};
  out = target_limited.step(in, false);
  assert(band_count(out) == 1);  // admitted: 416 W above the 400 W soft target
  assert(out.m1_enable && out.m2_enable && out.h60_enable && out.fans_enable);
  assert(out.admitted_W == 416.0);
  assert(out.over_target && out.rejected_demands == 0);  // WARN+logged, running

  // 18: modeled >500 W demand admitted under WARN (draw 566 W <= 792 W)
  const Limits soft{60.0, 10.0, 5.0, 500, POWER_TARGET_W, PSU_HARD_CEILING_W};
  Controller overload(soft);
  in = safe_inputs();
  assert(overload.step(in, true).state == State::ready);
  in.run_command = true;
  in.fan_required = true;
  in.h60_demand = true;
  in.m1_run = in.m2_run = true;
  in.h100_demand = {true, true, true};
  in.aux_demand_W = 150.0;
  out = overload.step(in, false);
  assert(out.state == State::running);
  assert(out.aux_enable && band_count(out) == 1);
  assert(out.admitted_W == 566.0);          // > 500 W soft target
  assert(out.over_target);                  // flagged WARN+logged, NOT tripped
  assert(out.rejected_demands == 0);        // inside the 792 W hard ceiling
  // 19: modeled >792 W demand rejected at the hard ceiling
  Controller hard{Limits{60.0, 10.0, 5.0, 500, POWER_TARGET_W, 792.0}};
  in.aux_demand_W = 500.0;  // 316 + 500 = 816 W > 792 W ceiling
  in.run_command = false;
  assert(hard.step(in, true).state == State::ready);  // manual reset unlatches
  in.run_command = true;
  out = hard.step(in, false);
  assert(out.state == State::running);
  assert(!out.aux_enable);                  // auxiliary demand refused
  assert(out.rejected_demands == 1);        // logged
  assert(out.admitted_W == 416.0);          // base 316 W + one band, hard ceiling held
  assert(out.admitted_W <= PSU_HARD_CEILING_W);

  std::cout << "controller_core_self_test: 19 cases passed; no reverse or "
               "auto-restart path; band mutual exclusion; soft target "
               << static_cast<int>(POWER_TARGET_W) << " W (WARN above), hard "
               "ceiling " << static_cast<int>(PSU_HARD_CEILING_W)
               << " W (PSU 24 V x 33 A; nameplate "
               << static_cast<int>(PSU_NAMEPLATE_W) << " W) enforced\n";
}