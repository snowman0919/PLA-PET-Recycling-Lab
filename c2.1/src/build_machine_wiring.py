"""Generate the review-only KiCad machine wiring schematic and pin/net ledger."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import uuid

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]
OUT = C21/"electrical"


def part(ref, value, x, y, pins, status="SELECTION_HOLD"):
    return {"ref": ref, "value": value, "x": x, "y": y, "pins": pins, "status": status}


P = lambda number, name, side, net: {"number": str(number), "name": name, "side": side, "net": net}

PARTS = [
    part("J1", "AC_INPUT_L_N_PE", 900, 900,
         [P(1,"L","R","AC_L_IN"),P(2,"N","R","AC_N_IN"),P(3,"PE","R","PE")], "FIELD_TERMINAL_HOLD"),
    part("QF1", "2P_MAINS_ISOLATOR_BREAKER_TBD", 2000, 900,
         [P(1,"L_IN","L","AC_L_IN"),P(2,"N_IN","L","AC_N_IN"),P(3,"L_OUT","R","AC_L_PROTECTED"),P(4,"N_OUT","R","AC_N_PROTECTED")]),
    part("PS1", "OWNED_24V_800W_PSU_RATING_MOUNT_VERIFY", 3300, 900,
         [P(1,"AC_L","L","AC_L_PROTECTED"),P(2,"AC_N","L","AC_N_PROTECTED"),P(3,"PE","L","PE"),P(4,"+24V","R","+24V_RAW"),P(5,"0V","R","0V")], "OWNED_RATING_VERIFY"),
    part("TB1", "PROTECTIVE_EARTH_BAR", 4800, 900,
         [P(1,"PSU_PE","L","PE"),P(2,"FRAME","R","PE"),P(3,"GUARDS","R","PE"),P(4,"BARREL","R","PE"),P(5,"MOTOR_FRAMES","R","PE")]),

    part("SR1", "DUAL_CHANNEL_SAFETY_RELAY_TBD", 1700, 2200,
         [P(1,"+24V","L","+24V_RAW"),P(2,"0V","L","0V"),
          P(3,"CH1_OUT","R","SAFE_CH1_OUT"),P(4,"CH1_RETURN","R","SAFE_CH1_RETURN"),
          P(5,"CH2_OUT","R","SAFE_CH2_OUT"),P(6,"CH2_RETURN","R","SAFE_CH2_RETURN"),
          P(7,"RESET_OUT","R","RESET_OUT"),P(8,"RESET_IN","R","RESET_IN"),
          P(9,"EDM_OUT","R","EDM_OUT"),P(10,"EDM_IN","R","EDM_IN"),
          P(11,"SAFE_OUT","R","SAFE_RELAY_OUT"),P(12,"SAFE_RETURN","R","0V")]),
    part("S1", "E_STOP_NC_CHANNEL_1", 3100, 1800,[P(1,"IN","L","SAFE_CH1_OUT"),P(2,"OUT","R","ESTOP_CH1")], "OWNED_CONTACT_VERIFY"),
    part("S2", "LID_INTERLOCK_NC_CHANNEL_1", 4100, 1800,[P(1,"IN","L","ESTOP_CH1"),P(2,"OUT","R","LID_CH1")]),
    part("S3", "SERVICE_INTERLOCK_NC_CHANNEL_1", 5100, 1800,[P(1,"IN","L","LID_CH1"),P(2,"OUT","R","SAFE_CH1_RETURN")]),
    part("S4", "E_STOP_NC_CHANNEL_2", 3100, 2300,[P(1,"IN","L","SAFE_CH2_OUT"),P(2,"OUT","R","ESTOP_CH2")], "OWNED_CONTACT_VERIFY"),
    part("S5", "LID_INTERLOCK_NC_CHANNEL_2", 4100, 2300,[P(1,"IN","L","ESTOP_CH2"),P(2,"OUT","R","LID_CH2")]),
    part("S6", "SERVICE_INTERLOCK_NC_CHANNEL_2", 5100, 2300,[P(1,"IN","L","LID_CH2"),P(2,"OUT","R","SAFE_CH2_RETURN")]),
    part("S7", "MANUAL_RESET_NO", 3600, 2800,[P(1,"IN","L","RESET_OUT"),P(2,"OUT","R","RESET_IN")]),
    part("K3", "K1_FORCE_GUIDED_NC_EDM", 4800, 2800,[P(1,"IN","L","EDM_OUT"),P(2,"OUT","R","EDM_IN")]),
    part("TS1", "MANUAL_RESET_OVERTEMP_NC_TBD", 3100, 3300,[P(1,"IN","L","SAFE_RELAY_OUT"),P(2,"OUT","R","K1_COIL_POS")]),
    part("K2", "K1_24V_DC_SAFETY_CONTACTOR_COIL_TBD", 4300, 3300,[P(1,"A1","L","K1_COIL_POS"),P(2,"A2","R","0V")]),
    part("D1", "K1_COIL_SUPPRESSOR_TBD", 5400, 3300,[P(1,"K","L","K1_COIL_POS"),P(2,"A","R","0V")]),
    part("K1", "DC_MAIN_CONTACT_35A_MIN_TBD", 6600, 2200,[P(1,"IN","L","+24V_RAW"),P(2,"OUT","R","+24V_SAFE")]),
    part("TVS1", "24V_BUS_OVERVOLTAGE_CLAMP_TBD", 7800, 2200,[P(1,"BUS","L","+24V_SAFE"),P(2,"RETURN","R","0V")]),

    part("F1", "CONTROL_BRANCH_FUSE_TBD", 1300, 4200,[P(1,"IN","L","+24V_RAW"),P(2,"OUT","R","+24V_CTRL_FUSED")]),
    part("U1", "24V_TO_5V_DC_DC_TBD", 2700, 4200,[P(1,"VIN","L","+24V_CTRL_FUSED"),P(2,"0V_IN","L","0V"),P(3,"+5V","R","+5V_CTRL"),P(4,"0V_OUT","R","0V")]),
    part("F2", "M1_BRANCH_FUSE_TBD", 1300, 5000,[P(1,"IN","L","+24V_SAFE"),P(2,"OUT","R","+24V_M1")]),
    part("DRV1", "M1_DRIVER_HW_CURRENT_LIMIT_TBD", 3000, 5000,
         [P(1,"PWR+","L","+24V_M1"),P(2,"0V","L","0V"),P(3,"MOTOR_A","R","M1_A"),P(4,"MOTOR_B","R","M1_B"),
          P(5,"ENABLE","L","M1_ENABLE"),P(6,"PWM","L","M1_PWM"),P(7,"CURRENT","R","M1_CURRENT"),P(8,"RPM","R","M1_RPM")]),
    part("M1", "SHARED_S1_S2_MOTOR_UNSELECTED", 4700, 5000,[P(1,"A","L","M1_A"),P(2,"B","L","M1_B"),P(3,"FRAME","R","PE")]),
    part("F3", "M2_BRANCH_FUSE_TBD", 6000, 5000,[P(1,"IN","L","+24V_SAFE"),P(2,"OUT","R","+24V_M2")]),
    part("DRV2", "M2_DRIVER_HW_CURRENT_LIMIT_TBD", 7600, 5000,
         [P(1,"PWR+","L","+24V_M2"),P(2,"0V","L","0V"),P(3,"MOTOR_A","R","M2_A"),P(4,"MOTOR_B","R","M2_B"),
          P(5,"ENABLE","L","M2_ENABLE"),P(6,"PWM","L","M2_PWM"),P(7,"CURRENT","R","M2_CURRENT"),P(8,"RPM","R","M2_RPM")]),
    part("M2", "EXTRUDER_MOTOR_UNSELECTED", 9300, 5000,[P(1,"A","L","M2_A"),P(2,"B","L","M2_B"),P(3,"FRAME","R","PE")]),

    part("F4", "HEATER_BRANCH_FUSE_TBD", 1300, 6200,[P(1,"IN","L","+24V_SAFE"),P(2,"OUT","R","+24V_HEAT")]),
    part("TF1", "ONE_SHOT_THERMAL_FUSE_TBD", 2600, 6200,[P(1,"IN","L","+24V_HEAT"),P(2,"OUT","R","+24V_HEAT_SAFE")]),
    part("H1", "BARREL_HEATER_100W_REQUIREMENT", 4100, 5900,[P(1,"+","L","+24V_HEAT_SAFE"),P(2,"-","R","H1_LOW")]),
    part("QH1", "HEATER1_LOW_SIDE_SWITCH_TBD", 5500, 5900,[P(1,"LOAD","L","H1_LOW"),P(2,"RETURN","R","0V"),P(3,"CTRL","L","H1_PWM"),P(4,"CTRL_GND","R","0V")]),
    part("H2", "BARREL_HEATER_100W_REQUIREMENT", 4100, 6400,[P(1,"+","L","+24V_HEAT_SAFE"),P(2,"-","R","H2_LOW")]),
    part("QH2", "HEATER2_LOW_SIDE_SWITCH_TBD", 5500, 6400,[P(1,"LOAD","L","H2_LOW"),P(2,"RETURN","R","0V"),P(3,"CTRL","L","H2_PWM"),P(4,"CTRL_GND","R","0V")]),
    part("H3", "BARREL_HEATER_100W_REQUIREMENT", 7100, 5900,[P(1,"+","L","+24V_HEAT_SAFE"),P(2,"-","R","H3_LOW")]),
    part("QH3", "HEATER3_LOW_SIDE_SWITCH_TBD", 8500, 5900,[P(1,"LOAD","L","H3_LOW"),P(2,"RETURN","R","0V"),P(3,"CTRL","L","H3_PWM"),P(4,"CTRL_GND","R","0V")]),
    part("H4", "DIE_HEATER_60W_REQUIREMENT", 7100, 6400,[P(1,"+","L","+24V_HEAT_SAFE"),P(2,"-","R","H4_LOW")]),
    part("QH4", "HEATER4_LOW_SIDE_SWITCH_TBD", 8500, 6400,[P(1,"LOAD","L","H4_LOW"),P(2,"RETURN","R","0V"),P(3,"CTRL","L","H4_PWM"),P(4,"CTRL_GND","R","0V")]),

    part("F5", "AUX_BRANCH_FUSE_TBD", 1000, 7300,[P(1,"IN","L","+24V_SAFE"),P(2,"OUT","R","+24V_AUX")]),
    part("AUX1", "FAN_PULLER_SPOOL_DRIVERS_TBD", 2700, 7300,
         [P(1,"+24V","L","+24V_AUX"),P(2,"0V","L","0V"),P(3,"FAN_CMD","L","FAN_CMD"),P(4,"PULL_CMD","L","PULLER_CMD"),P(5,"SPOOL_CMD","L","SPOOL_CMD"),
          P(6,"FAN_OUT","R","FAN_OUT"),P(7,"PULL_OUT","R","PULLER_OUT"),P(8,"SPOOL_OUT","R","SPOOL_OUT"),P(9,"FAN_TACH","R","FAN_TACH")]),
    part("J2", "AUX_LOAD_HARNESS", 4600, 7300,[P(1,"FAN","L","FAN_OUT"),P(2,"PULLER","L","PULLER_OUT"),P(3,"SPOOL","L","SPOOL_OUT"),P(4,"RETURN","R","0V")]),
    part("U2", "6CH_TEMPERATURE_FRONTEND_TBD", 6500, 7300,
         [P(1,"+5V","L","+5V_CTRL"),P(2,"0V","L","0V"),P(3,"S1","L","TEMP1_RAW"),P(4,"S2","L","TEMP2_RAW"),P(5,"S3","L","TEMP3_RAW"),P(6,"S4","L","TEMP4_RAW"),P(7,"S5","L","TEMP5_RAW"),P(8,"S6","L","TEMP6_RAW"),
          P(9,"BUS_CLK","R","TEMP_CLK"),P(10,"BUS_DATA","R","TEMP_DATA"),P(11,"FAULT","R","TEMP_FAULT")]),
    part("A1", "ARDUINO_MEGA_OWNED_LOGIC_ONLY", 9100, 7300,
         [P(1,"+5V","L","+5V_CTRL"),P(2,"0V","L","0V"),P(3,"M1_EN","L","M1_ENABLE"),P(4,"M1_PWM","L","M1_PWM"),P(5,"M2_EN","L","M2_ENABLE"),P(6,"M2_PWM","L","M2_PWM"),
          P(7,"H1_PWM","L","H1_PWM"),P(8,"H2_PWM","L","H2_PWM"),P(9,"H3_PWM","L","H3_PWM"),P(10,"H4_PWM","L","H4_PWM"),P(11,"FAN","L","FAN_CMD"),P(12,"PULL","L","PULLER_CMD"),P(13,"SPOOL","L","SPOOL_CMD"),
          P(14,"TEMP_CLK","R","TEMP_CLK"),P(15,"TEMP_DATA","R","TEMP_DATA"),P(16,"TEMP_FAULT","R","TEMP_FAULT"),P(17,"M1_CURRENT","R","M1_CURRENT"),P(18,"M1_RPM","R","M1_RPM"),P(19,"M2_CURRENT","R","M2_CURRENT"),P(20,"M2_RPM","R","M2_RPM"),P(21,"BUFFER","R","BUFFER_LEVEL"),P(22,"FAN_TACH","R","FAN_TACH"),P(23,"K1_FB","R","EDM_IN"),P(24,"RUN_CMD","R","RUN_COMMAND")], "OWNED_PIN_ASSIGNMENT_HOLD"),
    part("J3", "SIX_TEMPERATURE_SENSOR_HARNESS", 5000, 8200,
         [P(1,"T1","R","TEMP1_RAW"),P(2,"T2","R","TEMP2_RAW"),P(3,"T3","R","TEMP3_RAW"),P(4,"T4","R","TEMP4_RAW"),P(5,"T5","R","TEMP5_RAW"),P(6,"T6","R","TEMP6_RAW")]),
    part("J4", "BUFFER_AND_RUN_INPUTS", 7600, 8200,[P(1,"BUFFER","R","BUFFER_LEVEL"),P(2,"RUN","R","RUN_COMMAND"),P(3,"0V","R","0V")])
]


def uid(token):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "ppr-c2.1-machine-wiring/"+token))


def connector_symbol(source, pin_count):
    marker = f'\n\t(symbol "Conn_01x{pin_count:02d}"'
    start = source.index(marker)+1
    depth = 0
    quoted = escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start:index+1].replace(
                    f'(symbol "Conn_01x{pin_count:02d}"',
                    f'(symbol "Connector_Generic:Conn_01x{pin_count:02d}"', 1)
    raise ValueError(pin_count)


def write_schematic(path):
    root_uuid = uid("root")
    symbol_source = Path("/usr/share/kicad/symbols/Connector_Generic.kicad_sym").read_text()
    counts = sorted({len(component["pins"]) for component in PARTS})
    embedded = []
    for count in counts:
        block = connector_symbol(symbol_source, count)
        embedded.append("\n".join("\t"+line for line in block.splitlines()))
    lines = ["(kicad_sch", "\t(version 20250114)", '\t(generator "ppr_build_machine_wiring")',
             '\t(generator_version "1")', f'\t(uuid "{root_uuid}")', '\t(paper "A3")',
             "\t(title_block", '\t\t(title "PPR C2.1 machine wiring - REVIEW ONLY / RELEASE HOLD")',
             '\t\t(date "2026-09-21")', '\t\t(rev "C2.1-P6")', '\t\t(company "PPR")',
             '\t\t(comment 1 "Actual functional nets; all TBD ratings/MPNs must be resolved before energization")',
             '\t\t(comment 2 "24V 800W PSU owned; 500W operational cap; no automatic restart/reverse")',
             '\t\t(comment 3 "Independent safety relay/contactor/overtemp chain; MCU monitoring only")',
             '\t\t(comment 4 "Machine harness review schematic; no PCB or energization approval")', "\t)",
             "\t(lib_symbols", *embedded, "\t)"]
    for component in PARTS:
        x, y = component["x"]*0.0254, component["y"]*0.0254
        pin_count = len(component["pins"])
        symbol_uuid = uid("symbol/"+component["ref"])
        lines += ["\t(symbol", f'\t\t(lib_id "Connector_Generic:Conn_01x{pin_count:02d}")',
                  f"\t\t(at {x:.4f} {y:.4f} 0)", "\t\t(unit 1)", "\t\t(exclude_from_sim no)",
                  "\t\t(in_bom yes)", "\t\t(on_board yes)", "\t\t(dnp no)",
                  f'\t\t(uuid "{symbol_uuid}")',
                  f'\t\t(property "Reference" "{component["ref"]}"',
                  f"\t\t\t(at {x+3.81:.4f} {y-2.54:.4f} 0)",
                  "\t\t\t(effects (font (size 1.27 1.27)))", "\t\t)",
                  f'\t\t(property "Value" "{component["value"]}"',
                  f"\t\t\t(at {x+3.81:.4f} {y:.4f} 0)",
                  "\t\t\t(effects (font (size 0.9 0.9)))", "\t\t)",
                  f'\t\t(property "Footprint" "" (at {x:.4f} {y:.4f} 0) '
                  '(effects (font (size 1.27 1.27)) (hide yes)))',
                  f'\t\t(property "Datasheet" "~" (at {x:.4f} {y:.4f} 0) '
                  '(effects (font (size 1.27 1.27)) (hide yes)))',
                  f'\t\t(property "Description" "Machine equipment terminal representation" '
                  f'(at {x:.4f} {y:.4f} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
                  f'\t\t(property "Status" "{component["status"]}" (at {x:.4f} {y:.4f} 0) '
                  '(effects (font (size 1.27 1.27)) (hide yes)))']
        for pin in component["pins"]:
            lines += [f'\t\t(pin "{pin["number"]}" (uuid "{uid("pin/"+component["ref"]+"/"+pin["number"])}"))']
        lines += ["\t\t(instances", '\t\t\t(project "PPR_C2_1_machine_wiring"',
                  f'\t\t\t\t(path "/{root_uuid}" (reference "{component["ref"]}") (unit 1))',
                  "\t\t\t)", "\t\t)", "\t)"]
        start_y = (pin_count//2-(1 if pin_count % 2 == 0 else 0))*2.54
        for pin in component["pins"]:
            px = x-5.08
            py = y-start_y+(int(pin["number"])-1)*2.54
            lines += [f'\t(label "{pin["net"]}"', f"\t\t(at {px:.4f} {py:.4f} 180)",
                      "\t\t(effects (font (size 0.9 0.9)) (justify right bottom))",
                      f'\t\t(uuid "{uid("label/"+component["ref"]+"/"+pin["number"])}")', "\t)"]
    notes = [
        "SAFETY: SR1/K1 functional terminals are not manufacturer pin numbers; exact MPN/datasheet is mandatory.",
        "QF1, K1, all fuses, conductors, drivers, clamp and suppression values are unselected and remain HOLD.",
        "E-stop/interlocks/overtemp must de-energize K1 independently of A1; firmware is monitoring only.",
        "PE bonds PSU/frame/guards/barrel/motor frames. Verify site earthing and local mains rules before build.",
        "Heater TF1 is one-shot and physically coupled; TS1 is independent manual-reset. No auto restart.",
        "This sheet is an electrical connection source, not a PCB design or energization approval."
    ]
    for index, note in enumerate(notes):
        lines += ["\t(text", f'\t\t"{note}"', f"\t\t(exclude_from_sim no)",
                  f"\t\t(at 22.86 {243.84+index*4.572:.4f} 0)",
                  "\t\t(effects (font (size 1.27 1.27)) (justify left bottom))",
                  f'\t\t(uuid "{uid("note/"+str(index))}")', "\t)"]
    lines += ["\t(sheet_instances", '\t\t(path "/" (page "1"))', "\t)",
              "\t(embedded_fonts no)", ")"]
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    schematic = OUT/"PPR_C2_1_machine_wiring.kicad_sch"
    write_schematic(schematic)
    connections = OUT/"machine_wiring_connections.csv"
    with connections.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["reference", "value", "pin", "pin_role", "net", "selection_status"])
        for component in PARTS:
            for pin in component["pins"]:
                writer.writerow([component["ref"], component["value"], pin["number"], pin["name"],
                                 pin["net"], component["status"]])
    nets = {}
    for component in PARTS:
        for pin in component["pins"]:
            nets.setdefault(pin["net"], []).append(f'{component["ref"]}.{pin["number"]}:{pin["name"]}')
    dangling = {net: pins for net, pins in nets.items() if len(pins) < 2 and net not in {"PE"}}
    result = {
        "revision": "C2.1-P6",
        "schematic": str(schematic.relative_to(REPO)),
        "schematic_sha256": hashlib.sha256(schematic.read_bytes()).hexdigest(),
        "symbol_library": "KiCad Connector_Generic (system library; equipment terminal representation)",
        "connections": str(connections.relative_to(REPO)),
        "connections_sha256": hashlib.sha256(connections.read_bytes()).hexdigest(),
        "components": len(PARTS), "pins": sum(len(component["pins"]) for component in PARTS),
        "nets": len(nets), "single_endpoint_nets": dangling,
        "safety_chain": "DUAL_CHANNEL_FUNCTIONAL_TOPOLOGY_MPN_AND_TERMINAL_NUMBER_HOLD",
        "hardware_release": "HOLD", "energization": "HOLD"
    }
    (C21/"results/machine_wiring.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
