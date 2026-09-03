#!/usr/bin/env python3
"""Released source clean-build and HEX identity check."""
import hashlib, json, shutil, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cli():
    for p in [shutil.which("arduino-cli"), *sorted(Path("/nix/store").glob("*-arduino-cli-*/bin/arduino-cli"))]:
        if p and subprocess.run([str(p), "version"], capture_output=True).returncode == 0: return str(p)
    raise SystemExit("arduino-cli unavailable")
manifest = json.loads((ROOT / "build_manifest.json").read_text())
with tempfile.TemporaryDirectory(prefix="ppr-release-rebuild-") as out:
    result = subprocess.run([cli(), "compile", "--fqbn", "arduino:avr:mega", "--output-dir", out, str(ROOT/"source/arduino_mega")], text=True, capture_output=True)
    hexes = list(Path(out).glob("*.ino.hex"))
    if result.returncode or len(hexes) != 1: raise SystemExit(result.stdout + result.stderr)
    actual = sha(hexes[0])
expected = sha(ROOT / "binaries/filament_recycler_atmega2560.hex")
assert actual == expected == manifest["binary"]["sha256"], (actual, expected)
print(f"RELEASED_HEX_REPRODUCIBLE_OK sha256={actual}")
