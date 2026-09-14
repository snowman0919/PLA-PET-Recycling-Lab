"""Host execution of released HeaterController; no safety/physical certification."""
import ctypes
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [ROOT/'analysis/thermal_revision_v08/controller_bridge.cpp',
           ROOT/'firmware/arduino_mega/src/heater_control.cpp']


def build_library(output):
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError('build must stay inside repository')
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['g++', '-std=c++17', '-O2', '-shared', '-fPIC',
                    '-I'+str(ROOT/'firmware/arduino_mega/src'),
                    *map(str, SOURCES), '-o', str(output)], check=True, timeout=60)
    return output


class FirmwareController:
    def __init__(self, library):
        self.library = ctypes.CDLL(str(library))
        self.library.ppr_heater_create.restype = ctypes.c_void_p
        self.library.ppr_heater_destroy.argtypes = [ctypes.c_void_p]
        self.library.ppr_heater_step.restype = ctypes.c_uint
        self.library.ppr_heater_step.argtypes = [ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
            ctypes.c_uint, ctypes.POINTER(ctypes.c_float), ctypes.c_bool, ctypes.c_bool]
        self.handle = self.library.ppr_heater_create()
        if not self.handle:
            raise RuntimeError('heater allocation failed')
        self.faults = 0

    def __call__(self, temperature, target, now_s, permit=True, chain=True):
        vector = ctypes.c_float * 4
        temperatures, targets, duty = vector(*temperature), vector(*target), vector()
        self.faults = self.library.ppr_heater_step(self.handle, temperatures, targets,
            max(1, round(now_s*1000)), duty, permit, chain)
        return [float(value)/100 for value in duty]

    def close(self):
        if self.handle:
            self.library.ppr_heater_destroy(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
