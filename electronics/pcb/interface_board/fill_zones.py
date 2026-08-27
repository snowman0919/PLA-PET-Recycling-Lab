#!/usr/bin/env python3
"""Fill generated copper zones using KiCad's own pcbnew engine."""

from __future__ import annotations

import sys
from pathlib import Path

import pcbnew


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fill_zones.py BOARD.kicad_pcb")
    board_path = Path(sys.argv[1]).resolve()
    board = pcbnew.LoadBoard(str(board_path))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(board_path), board)
    print(f"filled copper zones in {board_path}")


if __name__ == "__main__":
    main()
