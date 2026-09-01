#include <cassert>
#include <cmath>
#include <iostream>

#include "feed_delivery_control.h"

namespace {

FeedDeliveryConfig config() {
  // Host-only commissioning fixture. Production must replace these with verified records.
  return {80.0f, 120.0f, 0.12f, 2.0f, 16.0f, 32.0f,
          2.2f, 1.4f, 3.2f, 2.4f, 0.35f, 0.70f,
          55, 60, 220, 500, 300, 200, 450, 600, 1200, 2, true};
}

FeedDeliveryInputs healthy(uint32_t now_ms = 0) {
  return {now_ms, 12.0f, 24.0f, 1.0f, 0.7f, true, true, true};
}

FeedDeliveryController running(float flow = 100.0f) {
  FeedDeliveryController controller;
  assert(controller.configure(config()));
  const auto input = healthy();
  assert(controller.start(flow, input));
  return controller;
}

void driveOneRecovery(FeedDeliveryController& controller, FeedDeliveryInputs& input,
                      bool bridge) {
  input.now_ms += config().startup_grace_ms;
  if (bridge) {
    input.agitator_rpm = 1.0f;
    input.agitator_current_a = config().agitator_bridge_current_a;
  } else {
    input.auger_rpm = 1.0f;
    input.auger_current_a = config().auger_jam_current_a;
  }
  auto out = controller.update(input);
  assert(out.state == FeedDeliveryState::ANOMALY_DWELL);
  assert(bridge ? out.bridge_detected : out.jam_detected);
  input.now_ms += config().anomaly_dwell_ms;
  out = controller.update(input);
  assert(out.state == FeedDeliveryState::RETRY_STOP && out.inhibited);
  input.now_ms += config().retry_stop_ms;
  out = controller.update(input);
  assert(out.state == FeedDeliveryState::REVERSING);
  assert(out.auger_pwm < 0 && out.agitator_pwm < 0);
  input.now_ms += config().reverse_ms;
  input.auger_rpm = 12.0f;
  input.agitator_rpm = 24.0f;
  input.auger_current_a = 1.0f;
  input.agitator_current_a = 0.7f;
  out = controller.update(input);
  assert(out.state == FeedDeliveryState::STARTING);
}

}  // namespace

int main() {
  // Normal 80--120 g/h equivalent commands remain bounded and command both actuators.
  for (const float flow : {80.0f, 100.0f, 120.0f}) {
    auto controller = running(flow);
    auto input = healthy();
    const auto out = controller.update(input);
    assert(std::fabs(out.commanded_mass_flow_g_h - flow) < 0.01f);
    assert(out.auger_target_rpm > 0.0f && out.auger_target_rpm <= config().auger_max_rpm);
    assert(out.agitator_target_rpm > 0.0f && out.agitator_target_rpm <= config().agitator_max_rpm);
    assert(out.auger_pwm > 0 && out.auger_pwm <= config().maximum_pwm);
    assert(out.agitator_pwm > 0 && out.agitator_pwm <= config().maximum_pwm);
  }

  // Auger tach loss makes delivery unknowable and therefore causes a controlled stop.
  auto tach_loss = running();
  auto input = healthy();
  tach_loss.update(input);
  input.auger_tach_valid = false;
  input.now_ms = config().startup_grace_ms + config().tach_loss_timeout_ms;
  auto out = tach_loss.update(input);
  assert(out.state == FeedDeliveryState::FAULT_LATCHED);
  assert(out.fault == FeedDeliveryFault::TACH_LOSS && out.inhibited);
  assert(out.auger_pwm == 0 && out.agitator_pwm == 0);

  // Agitator-only tach loss first permits bounded derating, then stops if feedback stays absent.
  auto degraded = running();
  input = healthy();
  degraded.update(input);
  input.agitator_tach_valid = false;
  input.now_ms = config().startup_grace_ms + config().tach_loss_timeout_ms;
  out = degraded.update(input);
  assert(out.state == FeedDeliveryState::DEGRADED_DERATE && out.derated);
  assert(out.commanded_mass_flow_g_h < out.requested_mass_flow_g_h);
  assert(out.auger_pwm > 0 && out.agitator_target_rpm == 0.0f && out.agitator_pwm == 0);
  input.now_ms += config().degraded_stop_ms;
  out = degraded.update(input);
  assert(out.state == FeedDeliveryState::FAULT_LATCHED && out.inhibited);

  // A hard current trip bypasses retry motion and immediately inhibits both motors.
  auto overcurrent = running();
  input = healthy();
  input.auger_current_a = config().auger_trip_current_a;
  out = overcurrent.update(input);
  assert(out.fault == FeedDeliveryFault::OVERCURRENT && out.inhibited);
  assert(out.auger_pwm == 0 && out.agitator_pwm == 0);

  // Low agitator speed plus elevated current is an explicit bridge and gets one bounded recovery.
  auto bridge = running();
  input = healthy();
  driveOneRecovery(bridge, input, true);
  assert(bridge.state() == FeedDeliveryState::STARTING);

  // Low auger speed plus elevated current is a jam; retries are finite and latch when exhausted.
  auto exhausted = running();
  input = healthy();
  driveOneRecovery(exhausted, input, false);
  driveOneRecovery(exhausted, input, false);
  input.now_ms += config().startup_grace_ms;
  input.auger_rpm = 1.0f;
  input.auger_current_a = config().auger_jam_current_a;
  out = exhausted.update(input);
  assert(out.state == FeedDeliveryState::ANOMALY_DWELL);
  input.now_ms += config().anomaly_dwell_ms;
  out = exhausted.update(input);
  assert(out.state == FeedDeliveryState::RETRY_STOP);
  input.now_ms += config().retry_stop_ms;
  out = exhausted.update(input);
  assert(out.state == FeedDeliveryState::FAULT_LATCHED);
  assert(out.fault == FeedDeliveryFault::RETRY_EXHAUSTED && out.inhibited);

  // E-stop/guard permission removal dominates all states in the same update call.
  auto permission = running();
  input = healthy();
  input.permission_chain_ok = false;
  out = permission.update(input);
  assert(out.state == FeedDeliveryState::FAULT_LATCHED);
  assert(out.fault == FeedDeliveryFault::PERMISSION_LOSS && out.inhibited);
  assert(out.auger_pwm == 0 && out.agitator_pwm == 0);
  assert(!permission.clearFault(true, input));
  input.permission_chain_ok = true;
  assert(permission.clearFault(true, input));

  std::cout << "FEED_DELIVERY_HOST_SIMULATION_ONLY_NORMAL_TACH_CURRENT_BRIDGE_RETRY_PERMISSION_OK\n";
}
