#!/usr/bin/env python3
"""Verify populated module and USB connector models in the panel."""

import sys
from pathlib import Path

import pcbnew


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} PANEL.kicad_pcb")

    panel_path = Path(sys.argv[1])
    board = pcbnew.LoadBoard(str(panel_path))
    module_count = 0
    usb_count = 0

    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if reference == "U5":
            module_count += 1
            if len(footprint.Models()) == 0:
                raise RuntimeError("U5 has no 3D model")
        elif reference == "J1":
            usb_count += 1
            if len(footprint.Models()) == 0:
                raise RuntimeError("J1 has no 3D model")

    if module_count == 0:
        raise RuntimeError("no U5 nRF modules found in panel")

    pcbnew.SaveBoard(str(panel_path), board)
    print(f"3D assembly: kept {module_count} nRF modules and {usb_count} USB connectors")


if __name__ == "__main__":
    main()
