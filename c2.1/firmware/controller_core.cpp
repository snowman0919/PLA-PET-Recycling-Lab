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
};

struct Inputs {
  std::uint32_t now_ms{};
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
};

struct Outputs {
  State state{State::qualification_hold};
  bool m1_enable{};
  bool m2_enable{};
  bool heaters_enable{};
  bool auxiliaries_enable{};
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
    return {State::running, !in.buffer_full, true, true, true};
  }

 private:
  static Outputs off(State state) { return {state, false, false, false, false}; }
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

int main() {
  const Limits limits{60.0, 10.0, 5.0, 500};  // Test values, not certified limits.
  Controller controller(limits);
  auto in = safe_inputs();
  assert(controller.step(in, false).state == State::fault_latched);
  assert(controller.step(in, true).state == State::ready);
  in.run_command = true;
  auto out = controller.step(in, false);
  assert(out.state == State::running && out.m1_enable && out.heaters_enable);
  in.independent_overtemp_closed = false;
  out = controller.step(in, false);
  assert(out.state == State::fault_latched && !out.m1_enable && !out.heaters_enable);
  in.independent_overtemp_closed = true;
  assert(controller.step(in, false).state == State::fault_latched);
  in.run_command = false;
  assert(controller.step(in, true).state == State::ready);
  in.run_command = true;
  in.buffer_full = true;
  out = controller.step(in, false);
  assert(out.state == State::running && !out.m1_enable && out.m2_enable);
  in.buffer_full = false;
  in.motor_current_A = 11.0;
  in.motor_rpm = 0.0;
  assert(controller.step(in, false).state == State::fault_latched);

  Controller stale(limits);
  in = safe_inputs();
  in.now_ms = 501;
  assert(stale.step(in, false).state == State::fault_latched);
  Controller sensor(limits);
  in = safe_inputs();
  in.valid_temperature_mask = 0x1f;
  assert(sensor.step(in, false).state == State::fault_latched);
  Controller fan(limits);
  in = safe_inputs();
  in.fan_tach_ok = false;
  assert(fan.step(in, false).state == State::fault_latched);
  Controller temperature(limits);
  in = safe_inputs();
  in.temperature_C[2] = 60.1;
  assert(temperature.step(in, false).state == State::fault_latched);
  Controller qualification(limits);
  in = safe_inputs();
  in.qualification_enabled = false;
  assert(qualification.step(in, true).state == State::qualification_hold);
  std::cout << "controller_core_self_test: 11 cases passed; no reverse or auto-restart path\n";
}
