CXX ?= g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -Isrc

.PHONY: test arduino clean
test: build/test_profiles build/test_shredder_control build/test_heater_control build/test_heater_power_allocator build/test_gauge_control build/test_forming_actuation build/test_ui_core build/test_machine_supervisor build/test_calibration_record
	./build/test_profiles
	./build/test_shredder_control
	./build/test_heater_control
	./build/test_heater_power_allocator
	./build/test_gauge_control
	./build/test_forming_actuation
	./build/test_ui_core
	./build/test_machine_supervisor
	./build/test_calibration_record

arduino:
	arduino-cli compile --fqbn arduino:avr:mega .

build/test_profiles: src/process_state.cpp tests/test_profiles.cpp src/process_state.h src/material_profile.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/process_state.cpp tests/test_profiles.cpp -o $@

build/test_shredder_control: src/shredder_control.cpp tests/test_shredder_control.cpp src/shredder_control.h src/material_profile.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/shredder_control.cpp tests/test_shredder_control.cpp -o $@

build/test_heater_control: src/heater_control.cpp tests/test_heater_control.cpp src/heater_control.h src/hardware_interfaces.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/heater_control.cpp tests/test_heater_control.cpp -o $@

build/test_heater_power_allocator: src/heater_power_allocator.cpp tests/test_heater_power_allocator.cpp src/heater_power_allocator.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/heater_power_allocator.cpp tests/test_heater_power_allocator.cpp -o $@

build/test_gauge_control: src/gauge_control.cpp tests/test_gauge_control.cpp src/gauge_control.h src/hardware_interfaces.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/gauge_control.cpp tests/test_gauge_control.cpp -o $@

build/test_forming_actuation: src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp tests/test_forming_actuation.cpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp tests/test_forming_actuation.cpp -o $@

build/test_ui_core: src/ui_core.cpp tests/test_ui_core.cpp src/ui_core.h src/process_state.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/ui_core.cpp tests/test_ui_core.cpp -o $@

build/test_machine_supervisor: src/machine_supervisor.cpp src/process_state.cpp src/shredder_control.cpp src/heater_control.cpp src/heater_power_allocator.cpp src/gauge_control.cpp src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp tests/test_machine_supervisor.cpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/machine_supervisor.cpp src/process_state.cpp src/shredder_control.cpp src/heater_control.cpp src/heater_power_allocator.cpp src/gauge_control.cpp src/puller_speed_control.cpp src/screw_motion_monitor.cpp src/cooling_monitor.cpp src/spooler_control.cpp src/traverse_control.cpp tests/test_machine_supervisor.cpp -o $@

build/test_calibration_record: tests/test_calibration_record.cpp src/calibration_record.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) tests/test_calibration_record.cpp -o $@

clean:
	rm -f build/test_profiles build/test_shredder_control build/test_heater_control build/test_heater_power_allocator build/test_gauge_control build/test_forming_actuation build/test_ui_core build/test_machine_supervisor build/test_calibration_record
