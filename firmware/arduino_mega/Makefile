CXX ?= g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -Isrc

.PHONY: test arduino clean
test: build/test_profiles build/test_shredder_control build/test_heater_control build/test_heater_power_allocator build/test_gauge_control build/test_forming_actuation build/test_ui_core build/test_machine_supervisor build/test_calibration_record build/test_tach_estimator build/test_hardware_adapter build/test_hardware_adapter_e2e build/test_traverse_homing build/test_feed_delivery_control
	./build/test_profiles
	./build/test_shredder_control
	./build/test_heater_control
	./build/test_heater_power_allocator
	./build/test_gauge_control
	./build/test_forming_actuation
	./build/test_ui_core
	./build/test_machine_supervisor
	./build/test_calibration_record
	./build/test_tach_estimator ../../validation/results/hardware_adapter_tach/tach_estimator_trace.csv
	./build/test_hardware_adapter ../../validation/results/hardware_adapter_tach/drive_adapter_trace.csv
	./build/test_hardware_adapter_e2e ../../validation/results/hardware_adapter_e2e/scenario_trace.csv
	./build/test_traverse_homing
	./build/test_feed_delivery_control

arduino:
	arduino-cli compile --fqbn arduino:avr:mega .

build/test_profiles: src/process_state.cpp tests/test_profiles.cpp src/process_state.h src/material_profile.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/process_state.cpp tests/test_profiles.cpp -o $@

build/test_shredder_control: src/shredder_control.cpp src/drive_speed_control.cpp tests/test_shredder_control.cpp src/shredder_control.h src/drive_speed_control.h src/material_profile.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/shredder_control.cpp src/drive_speed_control.cpp tests/test_shredder_control.cpp -o $@

build/test_heater_control: src/heater_control.cpp tests/test_heater_control.cpp src/heater_control.h src/hardware_interfaces.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/heater_control.cpp tests/test_heater_control.cpp -o $@

build/test_heater_power_allocator: src/heater_power_allocator.cpp tests/test_heater_power_allocator.cpp src/heater_power_allocator.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/heater_power_allocator.cpp tests/test_heater_power_allocator.cpp -o $@

build/test_gauge_control: src/gauge_control.cpp tests/test_gauge_control.cpp src/gauge_control.h src/hardware_interfaces.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/gauge_control.cpp tests/test_gauge_control.cpp -o $@

build/test_forming_actuation: src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/drive_speed_control.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp src/traverse_homing.cpp tests/test_forming_actuation.cpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/drive_speed_control.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp src/traverse_homing.cpp tests/test_forming_actuation.cpp -o $@

build/test_ui_core: src/ui_core.cpp tests/test_ui_core.cpp src/ui_core.h src/process_state.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/ui_core.cpp tests/test_ui_core.cpp -o $@

build/test_machine_supervisor: src/machine_supervisor.cpp src/process_state.cpp src/shredder_control.cpp src/drive_speed_control.cpp src/heater_control.cpp src/heater_power_allocator.cpp src/gauge_control.cpp src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp src/traverse_homing.cpp tests/test_machine_supervisor.cpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/machine_supervisor.cpp src/process_state.cpp src/shredder_control.cpp src/drive_speed_control.cpp src/heater_control.cpp src/heater_power_allocator.cpp src/gauge_control.cpp src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp src/traverse_homing.cpp tests/test_machine_supervisor.cpp -o $@

build/test_calibration_record: tests/test_calibration_record.cpp src/calibration_record.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) tests/test_calibration_record.cpp -o $@

build/test_tach_estimator: src/tach_estimator.cpp tests/test_tach_estimator.cpp src/tach_estimator.h src/tach_contract_generated.h
	mkdir -p build validation/results/hardware_adapter_tach
	$(CXX) $(CXXFLAGS) src/tach_estimator.cpp tests/test_tach_estimator.cpp -o $@

build/test_hardware_adapter: src/tach_estimator.cpp src/drive_speed_control.cpp src/shredder_control.cpp src/screw_motion_monitor.cpp src/puller_speed_control.cpp src/spooler_control.cpp tests/test_hardware_adapter.cpp
	mkdir -p build ../../validation/results/hardware_adapter_tach
	$(CXX) $(CXXFLAGS) src/tach_estimator.cpp src/drive_speed_control.cpp src/shredder_control.cpp src/screw_motion_monitor.cpp src/puller_speed_control.cpp src/spooler_control.cpp tests/test_hardware_adapter.cpp -o $@

build/test_hardware_adapter_e2e: src/machine_supervisor.cpp src/process_state.cpp src/shredder_control.cpp src/drive_speed_control.cpp src/heater_control.cpp src/heater_power_allocator.cpp src/gauge_control.cpp src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp src/traverse_homing.cpp src/tach_estimator.cpp tests/test_hardware_adapter_e2e.cpp
	mkdir -p build ../../validation/results/hardware_adapter_e2e
	$(CXX) $(CXXFLAGS) src/machine_supervisor.cpp src/process_state.cpp src/shredder_control.cpp src/drive_speed_control.cpp src/heater_control.cpp src/heater_power_allocator.cpp src/gauge_control.cpp src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp src/traverse_homing.cpp src/tach_estimator.cpp tests/test_hardware_adapter_e2e.cpp -o $@

build/test_traverse_homing: src/traverse_homing.cpp src/traverse_control.cpp tests/test_traverse_homing.cpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/traverse_homing.cpp src/traverse_control.cpp tests/test_traverse_homing.cpp -o $@

build/test_feed_delivery_control: src/feed_delivery_control.cpp tests/test_feed_delivery_control.cpp src/feed_delivery_control.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/feed_delivery_control.cpp tests/test_feed_delivery_control.cpp -o $@

clean:
	rm -f build/test_profiles build/test_shredder_control build/test_heater_control build/test_heater_power_allocator build/test_gauge_control build/test_forming_actuation build/test_ui_core build/test_machine_supervisor build/test_calibration_record build/test_tach_estimator build/test_hardware_adapter build/test_hardware_adapter_e2e build/test_traverse_homing build/test_feed_delivery_control
