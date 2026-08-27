#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "control_core.h"
#include "protocol.h"

using namespace recycler;

SafetyInputs nominal(uint32_t now) {
  return {now, 0, true, true, true, true, true, true, false,
          false, false, false, false, false, false, 0.0F, Phase::IDLE};
}

void test_protocol() {
  char encoded[kMaximumFrameBytes];
  const size_t n = encode_frame(encoded, sizeof(encoded), "HB", 42, "uptime=1000");
  assert(n > 0);
  assert(strcmp(encoded, "FRP1|HB|42|uptime=1000|849D\n") == 0);
  ProtocolFrame frame{};
  assert(decode_frame(encoded, n, &frame) == ProtocolStatus::OK);
  assert(frame.sequence == 42);
  assert(strcmp(frame.type, "HB") == 0);
  assert(strcmp(frame.payload, "uptime=1000") == 0);
  encoded[6] = encoded[6] == 'H' ? 'X' : 'H';
  assert(decode_frame(encoded, n, &frame) == ProtocolStatus::BAD_CRC);
  assert(sequence_is_newer(1, 0));
  assert(!sequence_is_newer(1, 1));
  assert(sequence_is_newer(0, 0xFFFFFFFFUL));
}

void test_safety_fsm() {
  SafetyCore core;
  SafetyInputs in = nominal(0);
  in.reset_requested = true;
  assert(core.tick(in).state == SafetyState::SELF_TEST);
  in.reset_requested = false;
  in.now_ms = 500;
  assert(core.tick(in).state == SafetyState::READY);
  in.now_ms = 510;
  in.start_requested = true;
  in.requested_phase = Phase::EXTRUDE_SPOOL;
  SafetyOutputs out = core.tick(in);
  assert(out.state == SafetyState::RUNNING && out.contactor_request);
  in.start_requested = false;
  in.contactor_feedback_on = true;
  in.now_ms = 600;
  assert(core.tick(in).state == SafetyState::RUNNING);
  in.heartbeat_age_ms = 751;
  in.now_ms = 700;
  out = core.tick(in);
  assert(out.state == SafetyState::FAULT_LATCHED);
  assert(out.latched_faults & FAULT_HEARTBEAT);
  assert(!out.contactor_request && !out.heater_master_enable && !out.motor_master_enable);

  SafetyCore estop_core;
  in = nominal(0);
  in.estop_loop_closed = false;
  out = estop_core.tick(in);
  assert(out.state == SafetyState::ESTOP_LATCHED && (out.latched_faults & FAULT_ESTOP));
  in.estop_loop_closed = true;
  in.now_ms = 100;
  assert(estop_core.tick(in).state == SafetyState::ESTOP_LATCHED);
  in.reset_requested = true;
  assert(estop_core.tick(in).state == SafetyState::SELF_TEST);
}

void test_contactor_and_airflow() {
  SafetyCore core;
  SafetyInputs in = nominal(0);
  in.reset_requested = true;
  core.tick(in);
  in.reset_requested = false;
  in.now_ms = 500;
  core.tick(in);
  in.now_ms = 510;
  in.start_requested = true;
  in.requested_phase = Phase::EXTRUDE_SPOOL;
  core.tick(in);
  in.start_requested = false;
  in.now_ms = 800;
  SafetyOutputs out = core.tick(in);
  assert(out.state == SafetyState::FAULT_LATCHED);
  assert(out.latched_faults & FAULT_CONTACTOR);

  SafetyCore airflow_core;
  in = nominal(0);
  in.reset_requested = true;
  airflow_core.tick(in);
  in.reset_requested = false;
  in.now_ms = 500;
  airflow_core.tick(in);
  in.airflow_ok = false;
  in.start_requested = true;
  in.requested_phase = Phase::EXTRUDE_SPOOL;
  out = airflow_core.tick(in);
  assert(out.state == SafetyState::FAULT_LATCHED);
  assert(out.latched_faults & FAULT_AIRFLOW);
}

void test_heater() {
  const HeaterConfig config{0.08F, 0.005F, -20.0F, 330.0F, 230.0F,
                            30.0F, 2.0F, 60000};
  HeaterController heater(config);
  HeaterResult result = heater.update(0, 200.0F, 25.0F, true);
  assert(result.sensor_plausible && result.duty > 0.99F);
  result = heater.update(1000, 200.0F, 1000.0F, true);
  assert(!result.sensor_plausible && result.duty == 0.0F);

  HeaterController runaway(config);
  runaway.update(0, 200.0F, 25.0F, true);
  result = runaway.update(60001, 200.0F, 25.5F, true);
  assert(result.runaway_fault && result.duty == 0.0F);
}

void test_power_arbiter() {
  PowerGrant grant = arbitrate_power(
      {Phase::EXTRUDE_SPOOL, 396.0F, 300.0F, 0.0F, 0.0F}, 480.0F);
  assert(grant.valid);
  assert(fabsf(grant.extruder_heater_w - 84.0F) < 0.01F);
  assert(grant.total_w <= 480.01F);
  grant = arbitrate_power(
      {Phase::DRY_PREHEAT, 80.0F, 300.0F, 0.0F, 240.0F}, 480.0F);
  assert(!grant.valid && grant.heater_scale == 0.0F);
  grant = arbitrate_power(
      {Phase::DRY_PREHEAT, 80.0F, 0.0F, 60.0F, 240.0F}, 480.0F);
  assert(!grant.valid);
}

void test_bounded_jam_retry() {
  JamController jam;
  JamOutput out{};
  uint32_t now = 0;
  for (int retry = 0; retry < 4; ++retry) {
    out = jam.update(now, true, true);
    now += 251;
    out = jam.update(now, true, true);
    now += 501;
    out = jam.update(now, true, true);
    now += 301;
    out = jam.update(now, true, true);
    if (out.state == JamState::FAULT) break;
    assert(out.state == JamState::REVERSE);
    now += 801;
    out = jam.update(now, true, true);
    assert(out.state == JamState::RETRY);
    now += 1001;
    out = jam.update(now, true, true);
    assert(out.state == JamState::STOP);
  }
  assert(out.state == JamState::FAULT);
  assert(out.retry_count == 3);
}

int main() {
  test_protocol();
  test_safety_fsm();
  test_contactor_and_airflow();
  test_heater();
  test_power_arbiter();
  test_bounded_jam_retry();
  puts("MEGA_CONTROL_CORE_OK");
  return 0;
}
