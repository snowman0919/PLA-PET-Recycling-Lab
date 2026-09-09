#!/usr/bin/env python3
"""Compatibility entry point; the final tolerance generator owns both catalogs."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    runpy.run_path(str(ROOT / "calculations/tolerance_stack_final.py"), run_name="__main__")
