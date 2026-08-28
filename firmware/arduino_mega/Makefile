CXX ?= g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -Isrc

.PHONY: test clean
test: build/test_profiles build/test_shredder_control
	./build/test_profiles
	./build/test_shredder_control

build/test_profiles: src/process_state.cpp tests/test_profiles.cpp src/process_state.h src/material_profile.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/process_state.cpp tests/test_profiles.cpp -o $@

build/test_shredder_control: src/shredder_control.cpp tests/test_shredder_control.cpp src/shredder_control.h src/material_profile.h src/generated_profiles.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/shredder_control.cpp tests/test_shredder_control.cpp -o $@

clean:
	rm -f build/test_profiles build/test_shredder_control
