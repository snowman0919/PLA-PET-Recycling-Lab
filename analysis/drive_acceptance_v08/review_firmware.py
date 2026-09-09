"""Rebuild the GGM Arduino variant and bind the exact binary/source snapshot."""
from pathlib import Path
import hashlib, json, shutil, subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIRMWARE = ROOT / "exports/final/drive_ggm_v08/firmware"
SKETCH = FIRMWARE / "arduino_mega"
CLI = Path("/nix/store/7gx4b6cn5k07q20ws2gxg8brxk771qsv-arduino-cli-1.5.1/bin/arduino-cli")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not CLI.is_file():
        raise RuntimeError("recorded standalone arduino-cli missing")
    builder = ROOT / "firmware/ggm_drive_v08/build_variant.py"
    built = subprocess.run(["python3", str(builder)], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if built.returncode:
        raise RuntimeError("GGM firmware variant generation failed")
    manifest = json.loads((FIRMWARE / "manifest.json").read_text())
    for relative, digest in manifest["source_payload"].items():
        path = SKETCH / relative
        if sha(path) != digest:
            raise RuntimeError("stale firmware payload: " + relative)
    build = HERE / "raw/avr_guard20"
    binaries = HERE / "raw/avr_guard20_binaries"
    shutil.rmtree(build, ignore_errors=True)
    shutil.rmtree(binaries, ignore_errors=True)
    build.mkdir(parents=True); binaries.mkdir(parents=True)
    command = [str(CLI), "compile", "--fqbn", "arduino:avr:mega",
               "--build-path", str(build), "--output-dir", str(binaries), str(SKETCH)]
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
    log = HERE / "raw/avr_guard20.log"
    log.write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError("AVR build failed")
    built_hex = binaries / "arduino_mega.ino.hex"
    released_hex = FIRMWARE / "binaries/arduino_mega.ino.hex"
    if sha(built_hex) != sha(released_hex):
        raise RuntimeError("independent HEX differs from released GGM binary")
    guard = SKETCH / "src/ggm_drive_guard.h"
    contract = json.loads((ROOT / "control/ggm_drive_contract.json").read_text())
    guard_text = guard.read_text()
    hard_limit = contract["screw"]["hard_speed_limit_rpm"]
    expected = f"fabsf(i.screw_rpm)>{hard_limit:g}"
    if expected not in guard_text:
        raise RuntimeError("screw hard-speed guard does not match contract")
    result = {
        "status": "INDEPENDENT_AVR_BUILD_MATCHES_CURRENT_GGM_BINARY",
        "physical_validation": "NOT_RUN",
        "hardware_enabled": False,
        "command": command,
        "compiler_cli": "arduino-cli 1.5.1",
        "board": "arduino:avr:mega",
        "hex_sha256": sha(built_hex),
        "released_hex_sha256": sha(released_hex),
        "screw_hard_limit_rpm": hard_limit,
        "guard_source_sha256": sha(guard),
        "contract_sha256": sha(ROOT / "control/ggm_drive_contract.json"),
        "build_log_sha256": sha(log),
        "source_sha256": {
            str(p.relative_to(ROOT)): sha(p)
            for p in [Path(__file__).resolve(), builder, ROOT / "firmware/ggm_drive_v08/ggm_commissioning.h",
                      ROOT / "firmware/arduino_mega/src/ggm_drive_guard.h", FIRMWARE / "manifest.json",
                      ROOT / "control/ggm_drive_contract.json", guard]
        },
        "limitations": [
            "No upload to Arduino Mega",
            "No BTS7960 or motor energization",
            "Current-to-torque coefficients remain zero until physical calibration",
        ],
    }
    (HERE / "firmware_review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
