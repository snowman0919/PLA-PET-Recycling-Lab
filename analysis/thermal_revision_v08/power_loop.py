"""Host-only heater component replay; no serial, GPIO, or hardware access."""
import ctypes as C
import hashlib
from pathlib import Path
import subprocess
import tempfile
import os

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'firmware/arduino_mega/src'
SOURCES = [Path(__file__).with_name('power_loop_bridge.cpp'),
           SOURCE/'heater_control.cpp', SOURCE/'heater_power_allocator.cpp']
DEPENDENCIES = SOURCES + [SOURCE/name for name in (
    'heater_control.h', 'heater_power_allocator.h', 'hardware_interfaces.h',
    'material_profile.h', 'generated_profiles.h')]

def source_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in DEPENDENCIES}


def build_library():
    before = source_hashes()
    key = hashlib.sha256(repr(sorted(before.items())).encode()).hexdigest()[:20]
    folder = ROOT/'.build/thermal-controller-replay'
    folder.mkdir(parents=True, exist_ok=True)
    output = folder/('power-loop-'+key+'.so')
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        built = Path(tmp)/'loop.so'
        subprocess.run(['g++', '-std=c++17', '-O2', '-fno-fast-math', '-Wall', '-Wextra',
                        '-Werror', '-shared', '-fPIC', '-I'+str(SOURCE),
                        *map(str, SOURCES), '-o', str(built)], check=True, timeout=60)
        if source_hashes() != before:
            raise RuntimeError('controller source changed during compilation')
        os.replace(built, output)
    return output


class PowerLoop:
    def __init__(self, library):
        self.lib = C.CDLL(str(library))
        self.lib.ppr_loop_create.restype = C.c_void_p
        self.lib.ppr_loop_destroy.argtypes = [C.c_void_p]
        self.lib.ppr_loop_destroy.restype = None
        self.lib.ppr_loop_cap.argtypes = [C.c_bool]
        self.lib.ppr_loop_cap.restype = C.c_float
        self.lib.ppr_loop_sample_ms.restype = C.c_uint
        self.lib.ppr_loop_fault_zone.argtypes = [C.c_void_p]
        self.lib.ppr_loop_fault_zone.restype = C.c_uint
        self.lib.ppr_loop_step.argtypes = [C.c_void_p, C.POINTER(C.c_float),
            C.POINTER(C.c_float), C.c_uint, C.c_float, C.c_bool, C.c_bool,
            C.POINTER(C.c_float), C.POINTER(C.c_ubyte)]
        self.lib.ppr_loop_step.restype = C.c_uint
        self.handle = self.lib.ppr_loop_create()
        if not self.handle:
            raise MemoryError('host controller allocation')
        self.sample_ms = self.lib.ppr_loop_sample_ms()
        self.lib.ppr_loop_targets.argtypes = [C.POINTER(C.c_float)]
        self.lib.ppr_loop_targets.restype = None
        target = (C.c_float * 4)()
        self.lib.ppr_loop_targets(target)
        self.targets = list(target)
        self.faults = 0
        self.fault_zone = 4

    def cap(self, extrusion=False):
        return float(self.lib.ppr_loop_cap(extrusion))

    def step(self, temperature, target, now_ms, *, extrusion=False, permit=True, chain=True):
        if not self.handle or len(temperature) != 4 or len(target) != 4:
            raise ValueError('closed controller or wrong input length')
        if type(now_ms) is not int or not 0 < now_ms < 2**32:
            raise ValueError('clock outside uint32 range')
        vector = C.c_float * 4
        duty, on = vector(), (C.c_ubyte * 4)()
        self.faults = int(self.lib.ppr_loop_step(self.handle, vector(*temperature),
            vector(*target), now_ms, self.cap(extrusion), permit, chain, duty, on))
        self.fault_zone = int(self.lib.ppr_loop_fault_zone(self.handle))
        if self.faults == 65535:
            raise RuntimeError('invalid host-loop invocation')
        return [float(v) for v in duty], [bool(v) for v in on]

    def close(self):
        if self.handle:
            self.lib.ppr_loop_destroy(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
