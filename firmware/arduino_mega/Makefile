CXX ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Werror -pedantic -O2
BUILD_DIR := build
TEST_BIN := $(BUILD_DIR)/test_control_core
UI_TEST_BIN := $(BUILD_DIR)/test_ui_core
SKETCH_TEST_BIN := $(BUILD_DIR)/test_sketch_compile

.PHONY: test clean

test: $(TEST_BIN) $(UI_TEST_BIN) $(SKETCH_TEST_BIN)
	$(TEST_BIN)
	$(UI_TEST_BIN)
	$(SKETCH_TEST_BIN)

$(TEST_BIN): src/control_core.cpp src/control_core.h src/protocol.cpp src/protocol.h tests/test_control_core.cpp
	mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -Isrc src/control_core.cpp src/protocol.cpp tests/test_control_core.cpp -o $(TEST_BIN)

$(UI_TEST_BIN): src/control_core.h src/ui_core.cpp src/ui_core.h tests/test_ui_core.cpp
	mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -Isrc src/ui_core.cpp tests/test_ui_core.cpp -o $(UI_TEST_BIN)

$(SKETCH_TEST_BIN): filament_recycler_mega.ino src/control_core.cpp src/control_core.h src/protocol.cpp src/protocol.h src/ui_core.cpp src/ui_core.h tests/test_sketch_compile.cpp tests/Arduino.h tests/avr/wdt.h
	mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -Itests -Isrc src/control_core.cpp src/protocol.cpp src/ui_core.cpp tests/test_sketch_compile.cpp -o $(SKETCH_TEST_BIN)

clean:
	rm -f $(TEST_BIN) $(UI_TEST_BIN) $(SKETCH_TEST_BIN)
