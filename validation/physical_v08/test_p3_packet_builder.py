#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

B = load(HERE / "build_p3_inspection_packet.py", "p3_builder")
P = load(HERE / "analyze_p3_preflight.py", "p3_preflight_test")
I = load(ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py", "ggm_inspection_test")
S = load(HERE / "validate_p3_stage_release.py", "p3_stage_release_test")
F = load(HERE / "build_p3_firmware_profile.py", "p3_firmware_profile_test")
P2T = load(HERE / "test_p2_stage_release.py", "p2_stage_fixture_for_p3")

class P3PacketBuilderTest(unittest.TestCase):
    def test_csv_to_authoritative_packet(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            d = Path(td); evidence = d / "evidence.txt"; evidence.write_text("synthetic P3 evidence")
            digest = hashlib.sha256(evidence.read_bytes()).hexdigest(); rel = str(evidence.relative_to(ROOT))
            common = {"evidence_path": rel, "sha256": digest, "operator": "TEST", "measured_at": "2026-09-10T15:00+09:00"}
            p2_release, _, _, _, receipt_file, _, _, _ = P2T.make_release(d)
            packet = json.loads(receipt_file.read_text(encoding="utf-8"))
            pre_common = {"status":"PASS","operator":"TEST","reviewer":"REVIEW","checked_at":"2026-09-10T15:05+09:00",
                "evidence_path":rel,"sha256":digest,"notes":"synthetic preflight"}
            pre_rows = [{"check_id":check_id,"observed":sorted(accepted)[0],**pre_common} for check_id,accepted in P.EXPECTED.items()]
            p2row = next(row for row in pre_rows if row["check_id"] == "p2_applicable_cold_fit")
            p2row["evidence_path"] = str(p2_release.relative_to(ROOT)); p2row["sha256"] = hashlib.sha256(p2_release.read_bytes()).hexdigest()
            preflight = P.evaluate(pre_rows, packet, ROOT, receipt_packet_sha256=hashlib.sha256(receipt_file.read_bytes()).hexdigest())
            P.validate_result(preflight, ROOT)
            preflight_file = d / "p3_preflight_result.json"
            preflight_file.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            preflight_binding = B.bind_preflight(preflight_file, receipt_file)
            self._write_current(d, common)
            self._write_no_load(d, common)
            self._write_torque(d, common)
            self._write_pins(d, common)
            out = B.build(packet, d, preflight_binding)
            self.assertEqual(out["record_status"], "P3_RECORDS_COMPILED_NOT_STAGE_RELEASE")
            self.assertTrue(out["p3_preflight"]["performed"]); self.assertFalse(out["p3_preflight"]["motor_energization_authorized"])
            self.assertFalse(out["all_physical_actions_authorized"])
            self.assertFalse(out["packet_builder"]["stage_release_granted"])
            currents = I.currents(out["current_calibration"]["data"])
            self.assertLessEqual(currents["SH"]["holdout_error_bound_nm"], .40)
            self.assertEqual(I.pins(out["protection_pin"]["data"])["coupons"], 9)
            self.assertEqual(I.p3_preflight(out["p3_preflight"])["checks"], len(P.EXPECTED))
            authorized = json.loads(json.dumps(out)); authorized["all_physical_actions_authorized"] = True
            inspected = I.inspect(authorized)
            self.assertEqual(inspected["p3_preflight"]["status"], "NUMERIC_RECORD_CHECK_PASS")
            self.assertEqual(inspected["domains"]["receipt"]["status"], "NUMERIC_RECORD_CHECK_PASS")
            self.assertEqual(inspected["domains"]["current_calibration"]["status"], "NUMERIC_RECORD_CHECK_PASS")
            self.assertEqual(inspected["domains"]["protection_pin"]["status"], "NUMERIC_RECORD_CHECK_PASS")
            self.assertTrue(inspected["input_physical_authorization_present"])
            self.assertEqual(inspected["input_packet_canonical_sha256"], I.canonical_sha(authorized))

            packet_file = d / "authoritative_p3_packet.json"
            report_file = d / "authoritative_p3_report.json"
            packet_file.write_text(json.dumps(authorized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report_file.write_text(json.dumps(inspected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            release = {
                "stage": "P3", "status": "PASS", "release_scope": "P3_COMPLETE_P4_P6_ENTRY_ONLY",
                "approved_by": "APPROVER", "independent_reviewer": "REVIEWER", "reviewed_at": "2026-09-10T16:00+09:00",
                "inspection_packet": packet_file.name, "inspection_packet_sha256": hashlib.sha256(packet_file.read_bytes()).hexdigest(),
                "inspection_report": report_file.name, "inspection_report_sha256": hashlib.sha256(report_file.read_bytes()).hexdigest(),
                "p4_energization_authorized": False, "p6_energization_authorized": False, "machine_release": "HOLD", "notes": "synthetic stage-release test",
            }
            release_file = d / "p3_stage_release.json"
            release_file.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            stage = S.validate(release_file)
            self.assertEqual(stage["status"], "P3_STAGE_RELEASE_VALIDATED")
            self.assertTrue(stage["p4_entry_prerequisite"]); self.assertTrue(stage["p6_entry_prerequisite"])
            self.assertFalse(stage["p4_energization_authorized"]); self.assertFalse(stage["p6_energization_authorized"])

            source_header = ROOT / "firmware/ggm_drive_v08/ggm_commissioning.h"
            source_before = hashlib.sha256(source_header.read_bytes()).hexdigest()
            profile_dir = d / "firmware_profile_candidate"
            profile = F.generate(release_file, profile_dir)
            self.assertEqual(profile["status"], "REVIEW_CANDIDATE_ONLY")
            self.assertFalse(profile["firmware_built"]); self.assertFalse(profile["hardware_flashed"])
            self.assertFalse(profile["eeprom_command_applied"]); self.assertFalse(profile["p8_entry_prerequisite"])
            self.assertAlmostEqual(profile["calibration"]["SH"]["amps_per_adc"], .01, places=9)
            self.assertAlmostEqual(profile["calibration"]["SH"]["zero_adc"], 100.0, places=6)
            self.assertAlmostEqual(profile["calibration"]["SH"]["gearbox_nm_per_amp"], 2.0, places=6)
            self.assertAlmostEqual(profile["calibration"]["EX"]["amps_per_adc"], .01, places=9)
            self.assertEqual((profile_dir / "shredder_eeprom_command.txt").read_text().strip(), "CAL CURRENT 100.000000000 0.010000000")
            candidate = (profile_dir / "ggm_commissioning_generated.h").read_text()
            self.assertIn("RECEIPT_LIMITER_CURRENT_AND_WIRING_VERIFIED = true", candidate)
            self.assertIn("EX_CURRENT_ZERO_ADC = 100.000000000f", candidate)
            self.assertEqual(hashlib.sha256(source_header.read_bytes()).hexdigest(), source_before)

            bad = json.loads(json.dumps(release)); bad["independent_reviewer"] = bad["approved_by"]
            release_file.write_text(json.dumps(bad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError): S.validate(release_file)
            bad = json.loads(json.dumps(release)); bad["inspection_packet_sha256"] = "0" * 64
            release_file.write_text(json.dumps(bad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError): S.validate(release_file)

            out["protection_pin"]["data"]["samples"][0]["hub_key_damage"] = "YES"
            with self.assertRaises(ValueError): I.pins(out["protection_pin"]["data"])
            preflight["receipt_packet_sha256"] = "0" * 64
            preflight_file.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError): B.bind_preflight(preflight_file, receipt_file)

    def _write_current(self, d, common):
        fields = "axis point adc_count reference_current_a u95_a instrument_id calibration_ref evidence_path sha256 operator measured_at".split()
        with (d/"p3_current_sensor_calibration.csv").open("w", newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
            for axis in ("SH","EX"):
                for i,current in enumerate((0,1,2,3,4,5),1):
                    w.writerow({"axis":axis,"point":i,"adc_count":100+100*current,"reference_current_a":current,"u95_a":.01,"instrument_id":"CUR","calibration_ref":"CAL-CUR",**common})

    def _write_no_load(self, d, common):
        fields = "axis trial direction output_rpm reference_current_a motor_case_c gear_case_c duration_s tach_id tach_calibration_ref current_ref_id current_ref_calibration_ref evidence_path sha256 operator measured_at observation".split()
        with (d/"p3_no_load.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
            for axis,rpm in (("SH",30),("EX",15)):
                for trial in range(1,4):
                    w.writerow({"axis":axis,"trial":trial,"direction":"F","output_rpm":rpm,"reference_current_a":.5,"motor_case_c":25,"gear_case_c":25,"duration_s":5,"tach_id":"TACH","tach_calibration_ref":"CAL-TACH","current_ref_id":"CURREF","current_ref_calibration_ref":"CAL-CURREF","observation":"normal",**common})

    def _write_torque(self, d, common):
        fields = "axis sample_id subset direction target_nm force_n u95_force_n arm_mm u95_arm_mm rpm adc_count drum_temp_c force_ref_id force_calibration_ref tach_id tach_calibration_ref arm_instrument_id arm_calibration_ref evidence_path sha256 operator measured_at".split()
        with (d/"p3_torque_map.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
            fit=(1.5,3.0,4.5,6.0,7.8); hold=(2.25,5.25,7.2)
            for axis,rpm in (("SH",30),("EX",15)):
                for subset,loads in (("fit",fit),("holdout",hold)):
                    for i,t in enumerate(loads,1):
                        direction = "R" if axis=="SH" and ((subset=="fit" and i==4) or (subset=="holdout" and i==2)) else "F"
                        current=.5+t/2
                        w.writerow({"axis":axis,"sample_id":f"{axis}-{subset}-{i}","subset":subset,"direction":direction,"target_nm":t,"force_n":4*t,"u95_force_n":.02,"arm_mm":250,"u95_arm_mm":.1,"rpm":rpm,"adc_count":100+100*current,"drum_temp_c":30,"force_ref_id":"FORCE","force_calibration_ref":"CAL-FORCE","tach_id":"TACH","tach_calibration_ref":"CAL-TACH","arm_instrument_id":"ARM","arm_calibration_ref":"CAL-ARM",**common})

    def _write_pins(self, d, common):
        fields = "coupon_id axis direction material_lot drawing_revision neck_diameter_mm force_n u95_force_n arm_mm u95_arm_mm calculated_release_nm u95_nm free_after_release hub_key_damage force_ref_id force_calibration_ref arm_instrument_id arm_calibration_ref evidence_path sha256 operator measured_at".split()
        with (d/"p3_pin_release.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
            for axis,direction,prefix in (("SH","F","SHF"),("SH","R","SHR"),("EX","F","EXF")):
                for i in range(1,4):
                    w.writerow({"coupon_id":f"{prefix}-{i}","axis":axis,"direction":direction,"material_lot":"LOT-1","drawing_revision":"D08","neck_diameter_mm":2.45,"force_n":36.2,"u95_force_n":.02,"arm_mm":250,"u95_arm_mm":.1,"calculated_release_nm":"","u95_nm":"","free_after_release":"YES","hub_key_damage":"NO","force_ref_id":"FORCE","force_calibration_ref":"CAL-FORCE","arm_instrument_id":"ARM","arm_calibration_ref":"CAL-ARM",**common})

if __name__ == "__main__": unittest.main()
