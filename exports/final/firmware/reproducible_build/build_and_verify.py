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
lock = json.loads((ROOT / "library_lock.json").read_text())
assert lock["fqbn"] == manifest["board_target"], "board lock mismatch"
assert lock["platforms"] == [manifest["arduino_core"]], "core lock mismatch"
assert lock["libraries"] == manifest["libraries"] == [], "external libraries not supported by this core-only build"
command = cli()
def output(*args): return subprocess.check_output([command, *args], text=True).strip()
assert output("version") == manifest["arduino_cli_version"], "CLI version mismatch"
cores = json.loads(output("core", "list", "--format", "json"))["platforms"]
core = next(p for p in cores if p["id"] == manifest["arduino_core"]["id"])
assert core["installed_version"] == manifest["arduino_core"]["version"], "installed core mismatch"
props = output("compile", "--fqbn", lock["fqbn"], "--show-properties", str(ROOT/"source/arduino_mega"))
compiler_path = next(line.split("=", 1)[1] for line in props.splitlines() if line.startswith("runtime.tools.avr-gcc.path="))
compiler = subprocess.check_output([str(Path(compiler_path)/"bin/avr-g++"), "--version"], text=True).splitlines()[0]
assert compiler == manifest["compiler_version"], "compiler mismatch"
for name, digest in manifest["source_files"].items():
    assert sha(ROOT/"source/arduino_mega"/name) == digest, "released source mismatch: " + name
with tempfile.TemporaryDirectory(prefix="ppr-release-rebuild-") as out:
    result = subprocess.run([command, "compile", "--fqbn", lock["fqbn"], "--clean", "--build-path", str(Path(out)/"build"), "--output-dir", out, str(ROOT/"source/arduino_mega")], text=True, capture_output=True)
    hexes = list(Path(out).glob("*.ino.hex"))
    if result.returncode or len(hexes) != 1: raise SystemExit(result.stdout + result.stderr)
    actual = sha(hexes[0])
expected = sha(ROOT / "binaries/filament_recycler_atmega2560.hex")
assert actual == expected == manifest["binary"]["sha256"], (actual, expected)
print(f"RELEASED_HEX_REPRODUCIBLE_OK sha256={actual}")
