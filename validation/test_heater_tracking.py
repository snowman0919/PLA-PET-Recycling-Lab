"""Compile the production PI and preserve existing protection thresholds."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'firmware/arduino_mega'
OUT = ROOT/'.build/heater-tracking'
OUT.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(dir=OUT) as temp:
    binary = Path(temp)/'test'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
        '-I'+str(SOURCE/'src'),str(SOURCE/'src/heater_control.cpp'),
        str(SOURCE/'tests/test_heater_tracking.cpp'),'-o',str(binary)],
        check=True,timeout=60)
    subprocess.run([str(binary)],check=True,timeout=30)
print('PRODUCTION_HEATER_TRACKING_PASS physical=NOT_RUN')
