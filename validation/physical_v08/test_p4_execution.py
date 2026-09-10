#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

P4 = load("analyze_p4_records")

class P4ExecutionTest(unittest.TestCase):
    def build_records(self, d: Path):
        evidence = d / "p4_raw_evidence.txt"; evidence.write_text("synthetic P4 evidence only\n", encoding="utf-8")
        digest = hashlib.sha256(evidence.read_bytes()).hexdigest(); rel = str(evidence.relative_to(ROOT))
        common = {"operator":"TEST_OPERATOR","reviewer":"TEST_REVIEWER","evidence_path":rel,"sha256":digest}
        numeric = {
            "cutter_coupon_count":(2,0,"count"), "shaft_tir_left":(.05,.01,"mm"), "shaft_tir_right":(.06,.01,"mm"),
            "phase_error":(.50,.05,"deg"), "min_cutter_screen_clearance":(2.10,.05,"mm"), "hand_rotation_contacts":(0,0,"count"),
            "pe_bond_worst":(.05,.01,"ohm"), "chain_alignment_150":(.10,.02,"mm"),
            "chain_midspan_slack_percent":(2.5,.1,"percent"), "drive_guard_clearance":(4.0,.1,"mm"),
        }
        pre=[]
        for check,(value,u95,unit) in numeric.items():
            pre.append({"check_id":check,"value":value,"u95":u95,"unit":unit,"instrument_id":"MEAS-P4","calibration_ref":"CAL-P4","checked_at":"2026-09-10T16:20+09:00","notes":"synthetic",**common})
        for check,expected in P4.PRE_BOOLEAN.items():
            pre.append({"check_id":check,"value":"YES" if expected else "NO","u95":"","unit":"boolean","instrument_id":"","calibration_ref":"","checked_at":"2026-09-10T16:20+09:00","notes":"synthetic",**common})
        self.write(d/"p4_preflight.csv", pre)

        quasi=[]
        for sid in sorted(P4.EXPECTED_SPECIMENS):
            mat="PLA" if sid.startswith("PLA") else "PET"
            thickness=1.2 if sid.startswith("PLA12") else 2.0 if sid.startswith("PLA20") else 3.0 if sid.startswith("PLA30") else 2.5
            quasi.append({"measured_at":"2026-09-10T16:25+09:00","material":mat,"specimen_id":sid,"actual_thickness_or_fold_mm":thickness,
                "force_n":20.0,"u95_force_n":.05,"arm_mm":250.0,"u95_arm_mm":.1,"force_angle_error_deg":0.0,"u95_angle_deg":.1,
                "force_instrument_id":"FORCE","force_calibration_ref":"CAL-FORCE","arm_instrument_id":"ARM","arm_calibration_ref":"CAL-ARM",
                "failure_mode":"capture-cut","permanent_damage":"NO","notes":"synthetic",**common})
        self.write(d/"p4_quasistatic.csv", quasi)

        jams=[]
        for mat in ("PLA","PET"):
            for trial in range(1,4):
                jams.append({"measured_at":"2026-09-10T16:30+09:00","material":mat,"trial":trial,"pre_jam_cutter_rpm":16.0,"u95_rpm":.1,
                    "rpm_instrument_id":"RPM","rpm_calibration_ref":"CAL-RPM","max_gearbox_torque_nm":7.8,"u95_torque_nm":.1,
                    "torque_reference_id":"TORQUE","torque_calibration_ref":"CAL-TORQUE","retry_count":1,"jam_cleared":"YES",
                    "latched_fault_after_third_failure":"NO","guard_lockout_required_for_reset":"YES","automatic_restart":"NO","permanent_damage":"NO",
                    "notes":"synthetic",**common})
        self.write(d/"p4_jam.csv", jams)

        chips=[]
        for mat in ("PLA","PET"):
            chips.append({"measured_at":"2026-09-10T16:35+09:00","material":mat,"batch_id":mat+"-CHIP-01","screen_hole_mm":5.0,
                "oversize_recirc_count":1,"input_mass_g":100.0,"mass_3_6_g":75.0,"mass_6_20_g":20.0,"mass_gt20_g":1.0,"fines_lt3_g":1.0,
                "u95_mass_g":.05,"longest_strip_mm":18.0,"max_gearbox_torque_nm":6.5,"u95_torque_nm":.1,"software_torque_limit_events":0,
                "scale_instrument_id":"SCALE","scale_calibration_ref":"CAL-SCALE","torque_reference_id":"TORQUE","torque_calibration_ref":"CAL-TORQUE",
                "notes":"synthetic",**common})
        self.write(d/"p4_chip.csv", chips)

    def write(self, path: Path, rows):
        with path.open("w", newline="", encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

    def mutate(self, path: Path, fn):
        with path.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
        fn(rows)
        self.write(path, rows)

    def test_p4_records_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            d=Path(td); self.build_records(d)
            result=P4.evaluate_records(d,ROOT)
            self.assertEqual(result["status"],"NUMERIC_RECORD_CHECK_PASS")
            self.assertFalse(result["stage_p4_pass"]); self.assertFalse(result["hardware_authorization"])
            self.assertEqual(result["preflight"]["checks"],19)
            self.assertEqual(result["quasistatic"]["PLA"]["samples"],15); self.assertEqual(result["quasistatic"]["PET"]["samples"],10)
            self.assertGreater(result["chip"]["PLA"]["recovery_lower_percent"],95)

            self.mutate(d/"p4_chip.csv", lambda rows: rows[0].update(software_torque_limit_events="1"))
            with self.assertRaises(ValueError): P4.evaluate_records(d,ROOT)
            self.build_records(d)
            self.mutate(d/"p4_jam.csv", lambda rows: rows[0].update(automatic_restart="YES"))
            with self.assertRaises(ValueError): P4.evaluate_records(d,ROOT)
            self.build_records(d)
            self.mutate(d/"p4_preflight.csv", lambda rows: next(r for r in rows if r["check_id"]=="min_cutter_screen_clearance").update(value="1.90",u95="0.05"))
            with self.assertRaises(ValueError): P4.evaluate_records(d,ROOT)
            self.build_records(d)
            self.mutate(d/"p4_quasistatic.csv", lambda rows: rows[0].update(sha256="0"*64))
            with self.assertRaises(ValueError): P4.evaluate_records(d,ROOT)
            self.build_records(d)
            self.mutate(d/"p4_chip.csv", lambda rows: rows[0].update(mass_3_6_g="65"))
            with self.assertRaises(ValueError): P4.evaluate_records(d,ROOT)

if __name__ == "__main__": unittest.main()
