from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from recycler.classifier import FusionClassifier, classify_color, srgb_to_lab
from recycler.dataset import append_sample
from recycler.diameter import DualViewGauge, Region, fit_view_scale
from recycler.history import ProductionHistory
from recycler.protocol import ProtocolError, decode_frame, encode_frame, sequence_is_newer
from recycler.runtime import ProductionRuntime
from recycler.supervisor import MegaSupervisor, parse_telemetry, parse_ui_command


class ProtocolTests(unittest.TestCase):
    def test_round_trip_crc_and_replay(self) -> None:
        raw = encode_frame("HB", 42, "uptime_ms=1000")
        self.assertEqual(raw, b"FRP1|HB|42|uptime_ms=1000|3692\n")
        frame = decode_frame(raw)
        self.assertEqual((frame.message_type, frame.sequence), ("HB", 42))
        corrupted = bytearray(raw)
        corrupted[6] ^= 1
        with self.assertRaises(ProtocolError):
            decode_frame(bytes(corrupted))
        self.assertTrue(sequence_is_newer(0, 0xFFFFFFFF))
        self.assertFalse(sequence_is_newer(7, 7))

    def test_supervisor_writes_bounded_commands(self) -> None:
        stream = io.BytesIO()
        supervisor = MegaSupervisor(stream, clock=lambda: 1.25)
        supervisor.heartbeat()
        supervisor.select_profile("PLA")
        supervisor.select_dryer_stage("PLA_45")
        supervisor.acknowledge_purge()
        supervisor.request_run("EXTRUDE_SPOOL")
        frames = stream.getvalue().splitlines(keepends=True)
        self.assertEqual(
            [decode_frame(frame).message_type for frame in frames],
            ["HB", "PROFILE", "DRY_STAGE", "PURGE_ACK", "RUN"],
        )
        with self.assertRaises(ValueError):
            supervisor.select_dryer_stage("PET_999")

    def test_camera_dropout_requests_pause_once(self) -> None:
        now = [0.0]
        stream = io.BytesIO()
        supervisor = MegaSupervisor(stream, clock=lambda: now[0])
        supervisor.record_camera_frame()
        supervisor.service_periodic(camera_required=True)
        now[0] = 3.01
        frames = supervisor.service_periodic(camera_required=True)
        self.assertIn("PAUSE", [decode_frame(frame).message_type for frame in frames])
        now[0] = 3.50
        frames = supervisor.service_periodic(camera_required=True)
        self.assertNotIn("PAUSE", [decode_frame(frame).message_type for frame in frames])

    def test_telemetry_parser(self) -> None:
        parsed = parse_telemetry(
            "state=3,phase=3,fault=00000020,p=2.50,t0=190.0,load=0.72,jam=1,retry=2"
        )
        self.assertEqual(parsed["fault"], 0x20)
        self.assertEqual(parsed["state"], 3)
        self.assertAlmostEqual(parsed["p"], 2.5)
        self.assertAlmostEqual(parsed["load"], 0.72)
        self.assertEqual(parsed["retry"], 2)

    def test_ui_snapshots_and_bounded_commands(self) -> None:
        stream = io.BytesIO()
        supervisor = MegaSupervisor(stream, clock=lambda: 0.0)
        supervisor.send_ui_classification(2, 92, 1, 3, 17, False, True)
        supervisor.send_ui_production(1.74, 1.76, 125.5, 372, 18, True)
        supervisor.send_ui_stock(65, 0x04)
        frames = [decode_frame(raw) for raw in stream.getvalue().splitlines(keepends=True)]
        self.assertEqual(
            [frame.message_type for frame in frames],
            ["UI_CLASS", "UI_PROD", "UI_STOCK"],
        )
        self.assertIn("dx_um=1740,dy_um=1760", frames[1].payload)
        self.assertEqual(parse_ui_command("MATERIAL=PET"), ("MATERIAL", "PET"))
        self.assertEqual(parse_ui_command("BATCH=17"), ("BATCH", "17"))
        with self.assertRaises(ProtocolError):
            parse_ui_command("MATERIAL=TPU")
        with self.assertRaises(ProtocolError):
            parse_ui_command("BATCH=017")
        with self.assertRaises(ValueError):
            supervisor.send_ui_stock(101, 0)


class DiameterTests(unittest.TestCase):
    def test_calibration_and_dual_view_measurement(self) -> None:
        calibration = fit_view_scale([(1.50, 216.0), (1.75, 252.0), (2.00, 288.0), (2.50, 360.0)])
        self.assertLessEqual(calibration.u95_mm, 0.020)
        width, height = 600, 60
        image = [[255 for _ in range(width)] for _ in range(height)]
        for row in image:
            row[14:266] = [0] * 252
            row[314:566] = [0] * 252
        gauge = DualViewGauge(
            Region(0, 0, 280, 60), Region(300, 0, 580, 60), calibration, calibration
        )
        measured = gauge.measure(image)
        self.assertAlmostEqual(measured.average_mm, 1.75, places=6)
        self.assertAlmostEqual(measured.ovality_mm, 0.0, places=6)
        self.assertFalse(measured.contaminated)


class ClassifierTests(unittest.TestCase):
    def test_material_fusion_and_fixed_color(self) -> None:
        prototypes = {
            "PLA": {"feature_names": ["transparency", "load"], "mean": [0.2, 0.7], "scale": [0.1, 0.1]},
            "PET": {"feature_names": ["transparency", "load"], "mean": [0.8, 0.3], "scale": [0.1, 0.1]},
        }
        classifier = FusionClassifier(prototypes)
        result = classifier.classify({"transparency": 0.21, "load": 0.69})
        self.assertEqual((result.label, result.disposition), ("PLA", "AUTO_APPROVE"))
        result = classifier.classify({"transparency": 0.5, "load": 0.5})
        self.assertEqual(result.label, "UNKNOWN")
        self.assertEqual(classify_color(srgb_to_lab(250, 250, 245)), "CLEAR_NATURAL_WHITE")


class HistoryTests(unittest.TestCase):
    def test_batch_generation_and_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            history = ProductionHistory(path)
            history.create_batch("B001", "PLA", "BLUE_PURPLE", "2026-08-28T00:00:00Z", recycling_generation=2)
            history.add_diameter("B001", 0, 1.74, 1.76, False)
            history.add_diameter("B001", 100, 1.73, 1.75, False)
            history.add_diameter("B001", 200, 1.60, 1.65, True)
            statistics = history.diameter_statistics("B001")
            self.assertEqual(statistics.count, 2)
            self.assertAlmostEqual(statistics.mean_mm, 1.745)
            self.assertEqual(statistics.off_spec_count, 0)
            self.assertAlmostEqual(statistics.maximum_ovality_mm, 0.02)
            intervals = history.off_spec_intervals("B001")
            self.assertEqual((intervals[0].start_ms, intervals[0].end_ms), (200, 200))
            self.assertEqual(history.suggested_generation(["B001"]), 3)
            history.close()

    def test_dataset_manifest_hash_and_group_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "sample.pgm"
            image.write_bytes(b"P5\n1 1\n255\n\x80")
            manifest = Path(directory) / "dataset.jsonl"
            record = append_sample(
                manifest,
                image,
                {
                    "sample_id": "S001",
                    "source_object_id": "OBJECT-A",
                    "material_truth": "PLA",
                    "color_truth": "BLUE_PURPLE",
                    "thickness_mm": 2.0,
                    "camera_exposure_us": 1000,
                    "camera_gain": 1.0,
                    "current_rms_a": 1.2,
                    "current_peak_a": 2.1,
                    "speed_drop_fraction": 0.1,
                    "vibration_peak_g": 0.4,
                },
            )
            self.assertEqual(record["source_object_id"], "OBJECT-A")
            self.assertEqual(len(record["image_sha256"]), 64)
            self.assertEqual(len(manifest.read_text().splitlines()), 1)

    def test_runtime_pauses_after_five_bad_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history = ProductionHistory(Path(directory) / "runtime.sqlite3")
            history.create_batch("B002", "PLA", "RED_ORANGE", "2026-08-28T00:00:00Z")
            calibration = fit_view_scale(
                [(1.50, 216.0), (1.75, 252.0), (2.00, 288.0), (2.50, 360.0)]
            )
            gauge = DualViewGauge(
                Region(0, 0, 280, 20), Region(300, 0, 580, 20), calibration, calibration
            )
            stream = io.BytesIO()
            supervisor = MegaSupervisor(stream, clock=lambda: 0.0)
            runtime = ProductionRuntime(supervisor, gauge, history, "B002")
            image = [[255 for _ in range(600)] for _ in range(20)]
            for row in image:
                row[5:275] = [0] * 270
                row[305:575] = [0] * 270
            for frame_id in range(5):
                runtime.process_camera_frame(image, frame_id * 100)
            sent_types = [decode_frame(frame).message_type for frame in stream.getvalue().splitlines(keepends=True)]
            self.assertEqual(sent_types.count("PAUSE"), 1)
            history.close()


if __name__ == "__main__":
    unittest.main()
