#!/usr/bin/env python3
"""Compile the real Arduino Mega target and record reproducible evidence."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cli_candidates() -> list[str]:
    """Return Arduino CLI candidates, preferring explicit and ordinary PATH tools.

    Some Nix installations put a bubblewrap launcher on PATH.  That launcher is
    unsuitable in restricted build environments even though the unwrapped CLI
    from the same store is usable, so retain it only as a fallback candidate.
    """
    candidates: list[str] = []
    configured = os.environ.get("ARDUINO_CLI")
    discovered = shutil.which("arduino-cli")
    for candidate in (configured, discovered):
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    for candidate in sorted(Path("/nix/store").glob("*-arduino-cli-*/bin/arduino-cli")):
        value = str(candidate)
        if value not in candidates:
            candidates.append(value)
    return candidates


def resolve_cli() -> str:
    failures: list[str] = []
    for cli in cli_candidates():
        probe = subprocess.run(
            [cli, "version"], cwd=ROOT, text=True, capture_output=True
        )
        if probe.returncode == 0:
            return cli
        failures.append(f"{cli}: {(probe.stderr or probe.stdout).strip()}")
    detail = "\n".join(failures) if failures else "no candidate found"
    raise SystemExit(f"ARDUINO_MEGA_COMPILE_FAIL arduino-cli unavailable\n{detail}")


def main() -> None:
    cli = resolve_cli()
    command = [cli, "compile", "--fqbn", "arduino:avr:mega", "firmware/arduino_mega"]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    passed = result.returncode == 0 and "Sketch uses" in output and "Global variables use" in output
    source_paths = [ROOT / "firmware/arduino_mega/arduino_mega.ino"] + sorted(
        path for path in (ROOT / "firmware/arduino_mega/src").iterdir()
        if path.suffix in {".h", ".cpp"}
    )
    evidence = {
        "revision": "safety-orchestration-closure-v0.6.1",
        "fqbn": "arduino:avr:mega",
        "target": "firmware/arduino_mega/arduino_mega.ino",
        "status": "PASS" if passed else "FAIL",
        "tool_output": output.strip(),
        "source_hashes": {
            str(path.relative_to(ROOT)): sha256(path) for path in source_paths
        },
        "validator_hashes": {
            str(Path(__file__).resolve().relative_to(ROOT)): sha256(Path(__file__).resolve())
        },
    }
    path = ROOT / "validation/results/arduino_mega_compile.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    if not passed:
        raise SystemExit(output)
    print("ARDUINO_MEGA_2560_COMPILE_OK")


if __name__ == "__main__":
    main()
