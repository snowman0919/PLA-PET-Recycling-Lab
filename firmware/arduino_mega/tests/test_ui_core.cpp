#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "ui_core.h"

using namespace recycler;

UiTelemetry nominal_ui() {
  UiTelemetry telemetry{};
  telemetry.state = SafetyState::SAFE_OFF;
  telemetry.phase = Phase::IDLE;
  telemetry.detected_material = UiMaterial::PLA;
  telemetry.classifier_confidence_pct = 92;
  telemetry.selected_material = UiMaterial::AUTO;
  telemetry.color_bin = 2;
  telemetry.batch_number = 17;
  for (float& temperature : telemetry.temperatures_c) temperature = 25.0F;
  telemetry.motor_current_a[0] = 2.25F;
  telemetry.motor_current_a[1] = 1.50F;
  telemetry.motor_current_a[2] = 0.75F;
  telemetry.hopper_fill_pct = 65;
  telemetry.full_bin_mask = 0x04;
  telemetry.diameter_x_mm = 1.74F;
  telemetry.diameter_y_mm = 1.76F;
  telemetry.produced_length_m = 125.5F;
  telemetry.produced_weight_g = 372.0F;
  telemetry.eta_minutes = 18;
  telemetry.classifier_valid = true;
  telemetry.diameter_gauge_qualified = true;
  return telemetry;
}

void test_startup_acknowledgement_is_local_and_safe() {
  UiCore ui;
  UiTelemetry telemetry = nominal_ui();
  UiFrame frame = ui.compose(telemetry);
  assert(frame.page == UiPage::STARTUP_ACK);
  assert(frame.severity == UiSeverity::CAUTION);
  assert(strstr(frame.lines[0], "Ventilate") != nullptr);
  assert(strstr(frame.lines[2], "PVC/ABS/TPU") != nullptr);
  assert(strstr(frame.lines[3], "labels/metal") != nullptr);

  telemetry.state = SafetyState::RUNNING;
  assert(ui.handle(UiEvent::PUSH, telemetry).type == UiActionType::NONE);
  assert(!ui.startup_acknowledged());
  telemetry.state = SafetyState::SAFE_OFF;
  const UiAction action = ui.handle(UiEvent::PUSH, telemetry);
  assert(action.type == UiActionType::ACK_STARTUP);
  assert(ui.startup_acknowledged());
  assert(ui.page(telemetry) == UiPage::STATUS);
}

void test_material_and_color_are_requests_not_start_commands() {
  UiCore ui;
  UiTelemetry telemetry = nominal_ui();
  ui.handle(UiEvent::PUSH, telemetry);
  ui.handle(UiEvent::ROTATE_CW, telemetry);
  assert(ui.page(telemetry) == UiPage::MATERIAL);
  assert(ui.handle(UiEvent::PUSH, telemetry).type == UiActionType::NONE);
  ui.handle(UiEvent::ROTATE_CW, telemetry);
  UiAction action = ui.handle(UiEvent::PUSH, telemetry);
  assert(action.type == UiActionType::SET_MATERIAL);
  assert(action.value == static_cast<int16_t>(UiMaterial::PLA));

  ui.handle(UiEvent::ROTATE_CW, telemetry);
  assert(ui.page(telemetry) == UiPage::COLOR);
  ui.handle(UiEvent::PUSH, telemetry);
  ui.handle(UiEvent::ROTATE_CW, telemetry);
  action = ui.handle(UiEvent::PUSH, telemetry);
  assert(action.type == UiActionType::SET_COLOR_BIN && action.value == 3);

  ui.handle(UiEvent::ROTATE_CW, telemetry);
  assert(ui.page(telemetry) == UiPage::BATCH);
  ui.handle(UiEvent::PUSH, telemetry);
  ui.handle(UiEvent::ROTATE_CW, telemetry);
  action = ui.handle(UiEvent::PUSH, telemetry);
  assert(action.type == UiActionType::SELECT_BATCH && action.value == 18);
}

void test_fault_preemption_and_guidance() {
  UiCore ui;
  UiTelemetry telemetry = nominal_ui();
  ui.handle(UiEvent::PUSH, telemetry);
  telemetry.state = SafetyState::FAULT_LATCHED;
  telemetry.faults = FAULT_PRESSURE | FAULT_HEARTBEAT;
  UiFrame frame = ui.compose(telemetry);
  assert(frame.page == UiPage::FAULT && frame.severity == UiSeverity::STOP);
  assert(strstr(frame.lines[0], "pressure") != nullptr);
  assert(strstr(frame.lines[6], "cannot clear") != nullptr);
  assert(ui.handle(UiEvent::BACK, telemetry).type == UiActionType::NONE);
  assert(ui.page(telemetry) == UiPage::FAULT);
}

void test_startup_and_purge_gate_extrusion() {
  UiCore ui;
  UiTelemetry telemetry = nominal_ui();
  telemetry.purge_required = true;
  assert(!ui.run_permitted(Phase::SORT_SHRED, telemetry));
  ui.handle(UiEvent::PUSH, telemetry);
  assert(ui.run_permitted(Phase::SORT_SHRED, telemetry));
  assert(!ui.run_permitted(Phase::EXTRUDE_SPOOL, telemetry));
  telemetry.purge_required = false;
  assert(ui.run_permitted(Phase::EXTRUDE_SPOOL, telemetry));
  telemetry.faults = FAULT_SENSOR;
  assert(!ui.run_permitted(Phase::EXTRUDE_SPOOL, telemetry));
}

void test_calibration_and_maintenance_energy_gate() {
  UiCore ui;
  UiTelemetry telemetry = nominal_ui();
  ui.handle(UiEvent::PUSH, telemetry);
  for (int i = 0; i < 7; ++i) ui.handle(UiEvent::ROTATE_CW, telemetry);
  assert(ui.page(telemetry) == UiPage::CALIBRATION);
  telemetry.state = SafetyState::RUNNING;
  assert(ui.handle(UiEvent::PUSH, telemetry).type == UiActionType::NONE);
  UiFrame frame = ui.compose(telemetry);
  assert(strstr(frame.lines[2], "Pause") != nullptr);
  telemetry.state = SafetyState::PAUSED;
  assert(ui.handle(UiEvent::PUSH, telemetry).type ==
         UiActionType::REQUEST_CALIBRATION);
  ui.handle(UiEvent::ROTATE_CW, telemetry);
  assert(ui.page(telemetry) == UiPage::MAINTENANCE);
  assert(ui.handle(UiEvent::PUSH, telemetry).type ==
         UiActionType::REQUEST_MAINTENANCE);
}

void test_required_monitoring_pages_render() {
  UiCore ui;
  UiTelemetry telemetry = nominal_ui();
  ui.handle(UiEvent::PUSH, telemetry);
  const UiPage expected[] = {
      UiPage::STATUS, UiPage::MATERIAL, UiPage::COLOR, UiPage::BATCH,
      UiPage::THERMAL_DRIVE, UiPage::QUALITY, UiPage::PRODUCTION,
      UiPage::CALIBRATION, UiPage::MAINTENANCE,
  };
  constexpr uint8_t expected_count = sizeof(expected) / sizeof(expected[0]);
  for (uint8_t i = 0; i < expected_count; ++i) {
    UiFrame frame = ui.compose(telemetry);
    assert(frame.page == expected[i]);
    assert(frame.title[0] != '\0');
    if (i + 1U < expected_count)
      ui.handle(UiEvent::ROTATE_CW, telemetry);
  }
  for (int i = 0; i < 4; ++i) ui.handle(UiEvent::ROTATE_CCW, telemetry);
  UiFrame frame = ui.compose(telemetry);
  assert(frame.page == UiPage::THERMAL_DRIVE);
  assert(strstr(frame.lines[0], "25.00") != nullptr);
  telemetry.temperatures_c[0] = -5.25F;
  frame = ui.compose(telemetry);
  assert(strstr(frame.lines[0], "-5.25") != nullptr);
  for (int i = 0; i < 2; ++i) ui.handle(UiEvent::ROTATE_CW, telemetry);
  frame = ui.compose(telemetry);
  assert(frame.page == UiPage::PRODUCTION);
  assert(strstr(frame.lines[1], "372.00") != nullptr);
}

void test_rotary_and_button_debounce() {
  UiInputFilter filter;
  assert(filter.update({0, false, false, false, false}) == UiEvent::NONE);
  assert(filter.update({10, false, true, false, false}) == UiEvent::NONE);
  assert(filter.update({20, true, true, false, false}) == UiEvent::NONE);
  assert(filter.update({30, true, false, false, false}) == UiEvent::NONE);
  assert(filter.update({40, false, false, false, false}) == UiEvent::ROTATE_CCW);

  assert(filter.update({50, false, false, true, false}) == UiEvent::NONE);
  assert(filter.update({75, false, false, false, false}) == UiEvent::NONE);
  assert(filter.update({85, false, false, true, false}) == UiEvent::NONE);
  assert(filter.update({126, false, false, true, false}) == UiEvent::PUSH);
  assert(filter.update({140, false, false, true, true}) == UiEvent::NONE);
  assert(filter.update({181, false, false, true, true}) == UiEvent::BACK);
}

int main() {
  test_startup_acknowledgement_is_local_and_safe();
  test_material_and_color_are_requests_not_start_commands();
  test_fault_preemption_and_guidance();
  test_startup_and_purge_gate_extrusion();
  test_calibration_and_maintenance_energy_gate();
  test_required_monitoring_pages_render();
  test_rotary_and_button_debounce();
  puts("MEGA_UI_CORE_OK");
  return 0;
}
