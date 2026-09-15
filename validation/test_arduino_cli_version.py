#!/usr/bin/env python3
"""Verify release-version locking independently of distributor banner metadata."""
from __future__ import annotations
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release"))
from build_electrical_firmware_release import rebuild_script


def version_reader():
    tree = ast.parse(rebuild_script())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cli_version")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<generated-cli-version>", "exec"), namespace)
    return namespace["cli_version"]


class ArduinoCliVersionTest(unittest.TestCase):
    def setUp(self):
        self.read = version_reader()
        self.recorded = "arduino-cli  Version: 1.5.1 Commit: unknown Date:"

    def test_distributor_metadata_does_not_change_release_version(self):
        official = "arduino-cli  Version: 1.5.1 Commit: 01f3d4f2b Date: 2026-06-05T10:22:17Z"
        self.assertEqual(self.read(official), self.read(self.recorded))

    def test_actual_version_changes_are_not_accepted(self):
        for version in ("1.5.0", "1.5.2", "1.6.0", "2.0.0"):
            with self.subTest(version=version):
                self.assertNotEqual(self.read(f"arduino-cli Version: {version}"), self.read(self.recorded))

    def test_prerelease_and_build_suffixes_are_not_stripped(self):
        for version in ("1.5.1-rc1", "1.5.1-nightly", "1.5.1+custom", "1.5.1-rc1+custom"):
            with self.subTest(version=version):
                self.assertEqual(self.read(f"arduino-cli Version: {version}"), version)
                self.assertNotEqual(version, self.read(self.recorded))

    def test_malformed_or_wrong_application_banners_fail_closed(self):
        for text in ("", "Version: 1.5.1", "other-cli Version: 1.5.1", "arduino-cli Version:",
                     "arduino-cli Version: 1.5", "arduino-cli Version: unknown", "arduino-cli Version: 1.5.1garbage"):
            with self.subTest(text=text):
                with self.assertRaises(AssertionError):
                    self.read(text)

    def test_generated_release_script_is_current(self):
        released = ROOT / "exports/final/firmware/reproducible_build/build_and_verify.py"
        self.assertEqual(released.read_text(), rebuild_script())


if __name__ == "__main__":
    unittest.main()
