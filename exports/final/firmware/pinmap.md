# Arduino Mega 2560 pin map — v0.8

Source commit `base:64f260eb851b3451563228cf56419e8b4bda7c7b; variant-builder:64f260eb851b3451563228cf56419e8b4bda7c7b`; `board_config.h` SHA-256 `bc919a9f40a6eac08d8c00fbd6c9d9b952d041a74c97f0f849b6c953f8a5cfbf`.

| Symbol | Mega pin | wire ID |
|---|---:|---|
| `SHREDDER_RPM_PIN` | `2` | `SIG-2` |
| `PULLER_TACH_PIN` | `3` | `SIG-3` |
| `ENCODER_A_PIN` | `18` | `SIG-18` |
| `ENCODER_B_PIN` | `19` | `SIG-19` |
| `ESTOP_PIN` | `20` | `SIG-20` |
| `LID_PIN` | `21` | `SIG-21` |
| `SERVICE_GUARD_PIN` | `22` | `SIG-22` |
| `THERMAL_CHAIN_PIN` | `23` | `SIG-23` |
| `HEATER_PERMISSION_FEEDBACK_PIN` | `24` | `SIG-24` |
| `START_PIN` | `25` | `SIG-25` |
| `PAUSE_PIN` | `26` | `SIG-26` |
| `BACK_PIN` | `27` | `SIG-27` |
| `CONFIRM_PIN` | `28` | `SIG-28` |
| `ENCODER_BUTTON_PIN` | `29` | `SIG-29` |
| `SHREDDER_ENABLE_PIN` | `32` | `SIG-32` |
| `SCREW_DIR_PIN` | `33` | `SIG-33` |
| `SCREW_ENABLE_PIN` | `34` | `SIG-34` |
| `PULLER_DIR_PIN` | `35` | `SIG-35` |
| `PULLER_ENABLE_PIN` | `36` | `SIG-36` |
| `SPOOLER_DIR_PIN` | `37` | `SIG-37` |
| `SPOOLER_ENABLE_PIN` | `38` | `SIG-38` |
| `TRAVERSE_STEP_PIN` | `39` | `SIG-39` |
| `TRAVERSE_DIR_PIN` | `40` | `SIG-40` |
| `TRAVERSE_ENABLE_PIN` | `41` | `SIG-41` |
| `LOCKOUT_CONFIRM_PIN` | `43` | `SIG-43` |
| `FAN_TACH_MUX_SELECT_PIN` | `49` | `SIG-49` |
| `FEEDER_DIR_PIN` | `42` | `SIG-42` |
| `FEEDER_STEP_PIN` | `44` | `SIG-44` |
| `FEEDER_ENABLE_PIN` | `46` | `SIG-46` |
| `FEEDER_FAULT_PIN` | `47` | `SIG-47` |
| `SHREDDER_LPWM_PIN` | `4` | `SIG-4` |
| `SHREDDER_PWM_PIN` | `5` | `SIG-5` |
| `SCREW_PWM_PIN` | `6` | `SIG-6` |
| `PULLER_PWM_PIN` | `7` | `SIG-7` |
| `SPOOLER_PWM_PIN` | `8` | `SIG-8` |
| `COOLING_PWM_PIN` | `9` | `SIG-9` |
| `THERMOCOUPLE_SO_PIN` | `50` | `SIG-50` |
| `THERMOCOUPLE_SCK_PIN` | `52` | `SIG-52` |
| `CURRENT_PIN` | `A0` | `SIG-A0` |
| `DANCER_PIN` | `A1` | `SIG-A1` |
| `GAUGE_X_PIN` | `A2` | `SIG-A2` |
| `GAUGE_Y_PIN` | `A3` | `SIG-A3` |
| `EX_CURRENT_PIN` | `A9` | `SIG-A9` |
| `PULLER_FAULT_PIN` | `A10` | `SIG-A10` |
| `SPOOLER_FAULT_PIN` | `A11` | `SIG-A11` |
| `GAUGE_VALID_PIN` | `A12` | `SIG-A12` |
| `COOLING_CURRENT_PIN` | `A4` | `SIG-A4` |
| `TRAVERSE_LEFT_LIMIT_PIN` | `A5` | `SIG-A5` |
| `TRAVERSE_RIGHT_LIMIT_PIN` | `A6` | `SIG-A6` |
| `FEEDER_TACH_PIN` | `A7` | `SIG-A7` |
| `SCREW_TACH_PIN` | `A13` | `SIG-A13` |
| `FAN_TACH_MUX_PIN` | `A14` | `SIG-A14` |
| `SPOOLER_TACH_PIN` | `A15` | `SIG-A15` |
| `HEATER_PINS_1` | `10` | `SIG-10` |
| `HEATER_PINS_2` | `11` | `SIG-11` |
| `HEATER_PINS_3` | `12` | `SIG-12` |
| `HEATER_PINS_4` | `13` | `SIG-13` |
| `THERMOCOUPLE_CS_PINS_1` | `14` | `SIG-14` |
| `THERMOCOUPLE_CS_PINS_2` | `15` | `SIG-15` |
| `THERMOCOUPLE_CS_PINS_3` | `16` | `SIG-16` |
| `THERMOCOUPLE_CS_PINS_4` | `17` | `SIG-17` |
| `THERMOCOUPLE_CS_PINS_5` | `48` | `SIG-48` |

`board_config.h` is authoritative for the released GGM/BTS7960 variant. Shredder bridge uses D5 RPWM / D4 LPWM / D32 enable; screw bridge uses D6 RPWM / D33 LPWM / D34 enable. Legacy D30/D31 generic shredder DIR/REVERSE pins are held low and intentionally absent from the field-wiring schedule. The GGM/BTS7960 current inputs are A0 for shredder motor-lead current and A9 for extruder motor-lead current; A8 and the legacy A9 screw-fault role are not field-wired in this variant. The active feeder reference drive is StepperOnline 17E1K-07 + EG17-G10 + CL42T-V41: D44 STEP, D42 DIR, D46 ENA, D47 ALM and A7 low-speed output-shaft tach. A received substitute exceeding the 5 A branch envelope requires redesign. Hardwired E-stop, lid/service, thermal cutoff and branch fuses are firmware-independent.
