#!/usr/bin/env python3
"""Generate and validate contact-pad connectors using KiCad's pcbnew API.

Run with a Python interpreter that can import pcbnew, for example the KiCad
AppImage's mounted bin/python3.11 wrapper. Does not modify a schematic or board.
Existing footprints are verified, not overwritten, unless --overwrite is given.
"""
from argparse import ArgumentParser
from pathlib import Path

import pcbnew

PITCH_MM = 2.0
PAD_DIAMETER_MM = 1.0
COURTYARD_CLEARANCE_MM = 0.25
LIBRARY = Path(__file__).resolve().parents[1] / "footprint.pretty"


def point(x, y):
    return pcbnew.VECTOR2I(round(x * 1_000_000), round(y * 1_000_000))


def variants():
    yield from ((1, columns) for columns in range(1, 7))
    yield from ((2, columns) for columns in range(1, 4))


def name_for(rows, columns):
    return f"Conn_Pads_{rows}x{columns:02d}_P2.00mm_D1.00mm"


def pad_positions(rows, columns):
    for column in range(columns):
        for row in range(rows):
            # Two rows: top 1,3,5; bottom 2,4,6, viewed from the front.
            number = column * rows + row + 1
            x = (column - (columns - 1) / 2) * PITCH_MM
            y = (row - (rows - 1) / 2) * PITCH_MM
            yield str(number), x, y


def make_footprint(rows, columns):
    name = name_for(rows, columns)
    footprint = pcbnew.FOOTPRINT(None)
    footprint.SetFPID(pcbnew.LIB_ID("footprint", name))
    footprint.SetReference("REF**")
    footprint.SetValue(name)
    footprint.SetAttributes(pcbnew.FP_SMD)
    footprint.SetLibDescription(
        f"Contact pads, {rows} row(s) x {columns} column(s), "
        "1.00mm circular SMD pads on a 2.00mm grid; copper and mask only, "
        "no holes or solder paste. Centered origin. "
        "Column-wise numbering: single row left-to-right; two rows odd/even."
    )
    footprint.SetKeywords("connector contact pogo test pads 1mm 2mm")
    layers = pcbnew.LSET()
    layers.AddLayer(pcbnew.F_Cu)
    layers.AddLayer(pcbnew.F_Mask)
    positions = list(pad_positions(rows, columns))
    for number, x, y in positions:
        pad = pcbnew.PAD(footprint)
        pad.SetNumber(number)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(point(PAD_DIAMETER_MM, PAD_DIAMETER_MM))
        pad.SetDrillSize(point(0, 0))
        pad.SetPosition(point(x, y))
        pad.SetLayerSet(layers)
        footprint.Add(pad)

    xmin = min(x for _, x, _ in positions)
    xmax = max(x for _, x, _ in positions)
    ymin = min(y for _, _, y in positions)
    ymax = max(y for _, _, y in positions)
    margin = PAD_DIAMETER_MM / 2 + COURTYARD_CLEARANCE_MM
    courtyard = pcbnew.PCB_SHAPE(footprint)
    courtyard.SetShape(pcbnew.SHAPE_T_RECT)
    courtyard.SetStart(point(xmin - margin, ymin - margin))
    courtyard.SetEnd(point(xmax + margin, ymax + margin))
    courtyard.SetLayer(pcbnew.F_CrtYd)
    courtyard.SetWidth(50_000)
    footprint.Add(courtyard)

    # Pin 1 stays circular; a separate silk ring identifies it without
    # changing the contact geometry. It is clear of the mask opening.
    marker = pcbnew.PCB_SHAPE(footprint)
    marker.SetShape(pcbnew.SHAPE_T_CIRCLE)
    marker.SetStart(point(xmin - 0.8, ymin - 0.8))
    marker.SetEnd(point(xmin - 0.7, ymin - 0.8))
    marker.SetLayer(pcbnew.F_SilkS)
    marker.SetWidth(120_000)
    footprint.Add(marker)

    for field, y, layer in [
        (footprint.Reference(), ymin - 1.7, pcbnew.F_SilkS),
        (footprint.Value(), ymax + 1.7, pcbnew.F_Fab),
    ]:
        field.SetPosition(point(0, y))
        field.SetTextSize(point(0.8, 0.8))
        field.SetTextThickness(120_000)
        field.SetLayer(layer)
    return footprint


def verify(directory, rows, columns):
    name = name_for(rows, columns)
    footprint = pcbnew.FootprintLoad(str(directory), name)
    assert footprint is not None, f"Cannot load {name}"
    pads = list(footprint.Pads())
    assert len(pads) == rows * columns, name
    expected = {number: point(x, y) for number, x, y in pad_positions(rows, columns)}
    assert sorted(p.GetNumber() for p in pads) == sorted(expected), name
    for pad in pads:
        assert pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD, name
        assert pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE, name
        assert pad.GetSize() == point(PAD_DIAMETER_MM, PAD_DIAMETER_MM), name
        assert pad.GetPosition() == expected[pad.GetNumber()], name
        assert pad.GetDrillSize() == point(0, 0), name
        assert set(pad.GetLayerSet().Seq()) == {pcbnew.F_Cu, pcbnew.F_Mask}, name
    print(f"Verified {name}: {len(pads)} circular pads")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=LIBRARY)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Verify without writing")
    mode.add_argument("--overwrite", action="store_true", help="Regenerate existing files")
    args = parser.parse_args()
    if not args.check:
        args.output.mkdir(parents=True, exist_ok=True)
    for rows, columns in variants():
        path = args.output / (name_for(rows, columns) + ".kicad_mod")
        if not args.check and (args.overwrite or not path.exists()):
            pcbnew.FootprintSave(str(args.output), make_footprint(rows, columns))
        verify(args.output, rows, columns)


if __name__ == "__main__":
    main()
