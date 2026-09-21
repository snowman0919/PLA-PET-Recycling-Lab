"""Host-build the portable controller core; no target flash or energization."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]
SOURCE = C21/"firmware/controller_core.cpp"
BUILD = REPO/".codex-run/ppr_controller_core_selftest"


def main():
    BUILD.parent.mkdir(exist_ok=True)
    compiler = shutil.which("g++")
    if not compiler:
        raise RuntimeError("g++ not found")
    command = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
               str(SOURCE), "-o", str(BUILD)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    executed = subprocess.run([str(BUILD)], capture_output=True, text=True) if compiled.returncode == 0 else None
    version = subprocess.run([compiler, "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    result = {
        "target": "HOST_X86_64_CONTROLLER_CORE_SELF_TEST_NOT_DEPLOYABLE_FIRMWARE",
        "compiler": version,
        "compile_command": command,
        "compile_return_code": compiled.returncode,
        "compile_stderr": compiled.stderr,
        "self_test_return_code": None if executed is None else executed.returncode,
        "self_test_stdout": "" if executed is None else executed.stdout,
        "source": str(SOURCE.relative_to(REPO)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "binary_sha256": None if executed is None else hashlib.sha256(BUILD.read_bytes()).hexdigest(),
        "cases": 11,
        "arduino_cli": "DID_NOT_FIND_EXECUTABLE",
        "target_cross_compile": "DID_NOT_RUN",
        "flash": "DID_NOT_RUN",
        "energization": "HOLD",
        "qualification_limits": "TEST_VALUES_ONLY_NOT_CERTIFIED"
    }
    (C21/"results/firmware_build.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
    if compiled.returncode or executed is None or executed.returncode:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
