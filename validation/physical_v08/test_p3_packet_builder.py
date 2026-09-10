#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

B = load(HERE / "build_p3_inspection_packet.py", "p3_builder")
I = load(ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py", "ggm_inspection_test")

class P3PacketBuilderTest(unittest.TestCase):
    def test_csv_to_authoritative_packet(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            d = Path(td); evidence = d / "evidence.txt"; evidence.write_text("synthetic P3 evidence")
            digest = hashlib.sha256(evidence.read_bytes()).hexdigest(); rel = str(evidence.relative_to(ROOT))
            common = {"evidence_path": rel, "sha256": digest, "operator": "TEST", "measured_at": "2026-09-10T15:00+09:00"}
            def receipt(axis, gear):
                readings = {
                    "voltage_v": (24.0, 0.0, "V"), "shaft_diameter": (11.99, .002, "mm"),
                    "shaft_projection": (32.0, .05, "mm"), "bolt_pcd": (104.0, .01, "mm"),
                    "output_offset": (18.0, .01, "mm"), "case_width": (90.0, .1, "mm"), "rear_length": (209.0, .1, "mm")}
                return {"performed": True, "kind": "PHYSICAL_MEASUREMENT", "operator": "TEST", "part_serial": "SER-"+axis,
                    "instrument_id": "MEAS-01", "instrument_calibration_ref": "CAL-R", "measured_at": common["measured_at"],
                    "raw_files": {rel: digest}, "motor_model": "K9DG60N2", "gear_model": gear,
                    "readings": {k: {"value": v, "u95": u, "unit": unit} for k, (v, u, unit) in readings.items()}}
            bindings = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                "control/ggm_drive_contract.json", "analysis/drive_acceptance_v08/manufacturing/drawing_contract.json")}
            packet = {"all_physical_actions_authorized": False, "design_sha256": bindings,
                "receipt": {"performed": True, "data": {"SH": receipt("SH", "K9G75C"), "EX": receipt("EX", "K9G150C")}},
                "alignment": {"performed": False, "data": {}}, "protection_pin": {"performed": False, "data": {}},
                "current_calibration": {"performed": False, "data": {}}}
            self._write_current(d, common)
            self._write_no_load(d, common)
            self._write_torque(d, common)
            self._write_pins(d, common)
            out = B.build(packet, d)
            self.assertEqual(out["record_status"], "P3_RECORDS_COMPILED_NOT_STAGE_RELEASE")
            self.assertFalse(out["all_physical_actions_authorized"])
            self.assertFalse(out["packet_builder"]["stage_release_granted"])
            currents = I.currents(out["current_calibration"]["data"])
            self.assertLessEqual(currents["SH"]["holdout_error_bound_nm"], .40)
            self.assertEqual(I.pins(out["protection_pin"]["data"])["coupons"], 9)
            out["protection_pin"]["data"]["samples"][0]["hub_key_damage"] = "YES"
            with self.assertRaises(ValueError): I.pins(out["protection_pin"]["data"])

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
