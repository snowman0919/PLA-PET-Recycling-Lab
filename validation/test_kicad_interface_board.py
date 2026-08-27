#!/usr/bin/env python3
"""Validate the tracked native KiCad monitor/interface board."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = ROOT / "electronics" / "pcb" / "interface_board"


def run(*args: str) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    return output


def main() -> None:
    assert shutil.which("kicad-cli"), "kicad-cli is required"
    schematic = BOARD_DIR / "ppr_interface.kicad_sch"
    board = BOARD_DIR / "ppr_interface.kicad_pcb"
    for path in (schematic, board, BOARD_DIR / "ppr_interface.kicad_pro", BOARD_DIR / "ppr_interface.kicad_dru"):
        assert path.is_file() and path.stat().st_size > 100

    with tempfile.TemporaryDirectory(prefix="ppr-kicad-") as tmp:
        erc = run("kicad-cli", "sch", "erc", "--exit-code-violations", "--output", f"{tmp}/erc.rpt", str(schematic))
        drc = run("kicad-cli", "pcb", "drc", "--exit-code-violations", "--output", f"{tmp}/drc.rpt", str(board))
        assert "Found 0 violations" in erc
        assert "Found 0 violations" in drc and "Found 0 unconnected items" in drc

    board_text = board.read_text(encoding="utf-8")
    assert "MONITOR ONLY / NO SAFETY CREDIT" in board_text
    assert board_text.count("REFERENCE_PLANE") >= 2
    assert board_text.count('(footprint "Fiducial:') == 3
    assert board_text.count('(footprint "TestPoint:') == 12

    emc = json.loads((BOARD_DIR / "analysis" / "emc.json").read_text())
    spice = json.loads((BOARD_DIR / "analysis" / "spice.json").read_text())
    assert emc["target_standard"] == "cispr-class-a"
    assert spice["summary"]["fail"] == 0 and spice["summary"]["pass"] == 9

    required_fab = (
        "ppr_interface-F_Cu.gtl", "ppr_interface-B_Cu.gbl",
        "ppr_interface-Edge_Cuts.gm1", "ppr_interface-PTH.drl",
        "ppr_interface-NPTH.drl", "ppr_interface-job.gbrjob",
    )
    for name in required_fab:
        path = BOARD_DIR / "fabrication" / name
        assert path.is_file() and path.stat().st_size > 20, name
    print("KICAD_INTERFACE_BOARD_OK")


if __name__ == "__main__":
    main()
