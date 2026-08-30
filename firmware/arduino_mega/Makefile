CXX ?= g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -Isrc

.PHONY: test arduino clean
test: build/test_profiles build/test_shredder_control build/test_heater_control build/test_gauge_control build/test_ui_core
	./build/test_profiles
	./build/test_shredder_control
	./build/test_heater_control
	./build/test_gauge_control
	./build/test_ui_core

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

build/test_gauge_control: src/gauge_control.cpp tests/test_gauge_control.cpp src/gauge_control.h src/hardware_interfaces.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/gauge_control.cpp tests/test_gauge_control.cpp -o $@

build/test_ui_core: src/ui_core.cpp tests/test_ui_core.cpp src/ui_core.h src/process_state.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/ui_core.cpp tests/test_ui_core.cpp -o $@

clean:
	rm -f build/test_profiles build/test_shredder_control build/test_heater_control build/test_gauge_control build/test_ui_core
