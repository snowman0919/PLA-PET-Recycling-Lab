"""Run production heater input/latch regression without powering hardware."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/'.build/heater-numeric-safety'
BUILD.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=BUILD) as directory:
    executable = Path(directory)/'numeric-safety'
    command = ['g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
        '-I'+str(ROOT/'firmware/arduino_mega/src'),
        str(ROOT/'firmware/arduino_mega/src/heater_control.cpp'),
        str(ROOT/'firmware/arduino_mega/tests/test_heater_numeric_safety.cpp'),
        '-o', str(executable)]
    subprocess.run(command, cwd=ROOT, check=True, timeout=60)
    subprocess.run([str(executable)], cwd=ROOT, check=True, timeout=30)
print('PRODUCTION_HEATER_NUMERIC_SAFETY_PASS physical=NOT_RUN')
