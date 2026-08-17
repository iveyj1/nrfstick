#!/usr/bin/env python3
"""Generate a four-legged support fixture for nrfstick.kicad_pcb.

Coordinate convention:
  * The PCB is centered in X/Y.
  * The PCB and fixture top surfaces are at Z = 0.
  * The 1.6 mm PCB occupies Z = -1.6 .. 0.
  * The legs extend downward in -Z.

All dimensions are millimetres. Run this file to create STEP and STL exports.
"""

from pathlib import Path
import re

import cadquery as cq
from cadquery import exporters

PCB_FILE = Path(__file__).with_name("nrfstick.kicad_pcb")
STEP_FILE = Path(__file__).with_name("pcb_support_fixture.step")
STL_FILE = Path(__file__).with_name("pcb_support_fixture.stl")

PCB_THICKNESS = 1.6
TOP_THICKNESS = 3.0
SURROUND = 5.0       # Table extends this far beyond every PCB edge.
LEDGE_WIDTH = 0.75    # Under-board support; deliberately less than 1 mm.
LEG_DIAMETER = 5.0
TOTAL_HEIGHT = 18.0     # Overall distance from leg bottoms to tabletop surface.
LEG_TOP_OVERLAP = 0.10
FIT_CLEARANCE = 0.0   # Increase for a looser real-world fit if desired.
CUT_EPSILON = 0.05


def pcb_edge_bounds(path: Path) -> tuple[float, float, float, float]:
    """Read a rectangular outline made from gr_line items on Edge.Cuts."""
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\(gr_line\s+"
        r"\(start\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)\s+"
        r"\(end\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)"
        r".*?\(layer\s+\"Edge\.Cuts\"\)",
        re.DOTALL,
    )
    segments = [tuple(map(float, match.groups())) for match in pattern.finditer(text)]
    if len(segments) != 4:
        raise ValueError(f"Expected four rectangular Edge.Cuts lines, found {len(segments)}")

    points = {(x1, y1) for x1, y1, _, _ in segments}
    points.update((x2, y2) for _, _, x2, y2 in segments)
    xs = sorted({point[0] for point in points})
    ys = sorted({point[1] for point in points})
    if len(points) != 4 or len(xs) != 2 or len(ys) != 2:
        raise ValueError("Edge.Cuts is not an axis-aligned rectangle")
    if any(x1 != x2 and y1 != y2 for x1, y1, x2, y2 in segments):
        raise ValueError("Edge.Cuts contains a non-axis-aligned side")
    return xs[0], ys[0], xs[1], ys[1]


def make_fixture(pcb_x: float, pcb_y: float) -> cq.Workplane:
    if not 0 < LEDGE_WIDTH <= 1.0:
        raise ValueError("LEDGE_WIDTH must be greater than zero and at most 1 mm")
    if TOP_THICKNESS <= PCB_THICKNESS:
        raise ValueError("The tabletop must be thicker than the PCB pocket")
    if TOTAL_HEIGHT <= TOP_THICKNESS:
        raise ValueError("TOTAL_HEIGHT must be greater than TOP_THICKNESS")

    leg_length = TOTAL_HEIGHT - TOP_THICKNESS
    pocket_x = pcb_x + 2.0 * FIT_CLEARANCE
    pocket_y = pcb_y + 2.0 * FIT_CLEARANCE
    opening_x = pocket_x - 2.0 * LEDGE_WIDTH
    opening_y = pocket_y - 2.0 * LEDGE_WIDTH
    outer_x = pocket_x + 2.0 * SURROUND
    outer_y = pocket_y + 2.0 * SURROUND

    # Start with a 3 mm slab whose upper face is Z=0.
    fixture = (
        cq.Workplane("XY")
        .box(outer_x, outer_y, TOP_THICKNESS, centered=(True, True, False))
        .translate((0, 0, -TOP_THICKNESS))
    )

    # Full PCB-sized recess. Its floor is at the bottom face of the PCB.
    pocket = (
        cq.Workplane("XY")
        .box(pocket_x, pocket_y, PCB_THICKNESS + CUT_EPSILON,
             centered=(True, True, False))
        .translate((0, 0, -PCB_THICKNESS))
    )
    fixture = fixture.cut(pocket)

    # Remove the centre all the way through, leaving only a narrow edge ledge.
    opening = (
        cq.Workplane("XY")
        .box(opening_x, opening_y, TOP_THICKNESS + 2.0 * CUT_EPSILON,
             centered=(True, True, False))
        .translate((0, 0, -TOP_THICKNESS - CUT_EPSILON))
    )
    fixture = fixture.cut(opening)

    # Put each 5 mm leg centrally beneath the surrounding 5 mm border.
    leg_x = outer_x / 2.0 - SURROUND / 2.0
    leg_y = outer_y / 2.0 - SURROUND / 2.0
    leg_top_z = -TOP_THICKNESS + LEG_TOP_OVERLAP
    for x in (-leg_x, leg_x):
        for y in (-leg_y, leg_y):
            leg = (
                cq.Workplane("XY", origin=(x, y, leg_top_z))
                .circle(LEG_DIAMETER / 2.0)
                .extrude(-(leg_length + LEG_TOP_OVERLAP))
            )
            fixture = fixture.union(leg)

    return fixture.clean()


def main() -> None:
    x_min, y_min, x_max, y_max = pcb_edge_bounds(PCB_FILE)
    pcb_x, pcb_y = x_max - x_min, y_max - y_min
    fixture = make_fixture(pcb_x, pcb_y)
    exporters.export(fixture, str(STEP_FILE))
    exporters.export(fixture, str(STL_FILE), tolerance=0.02, angularTolerance=0.1)
    print(f"PCB: {pcb_x:.3f} x {pcb_y:.3f} x {PCB_THICKNESS:.3f} mm")
    print(f"Fixture top: {pcb_x + 2*FIT_CLEARANCE + 2*SURROUND:.3f} x "
          f"{pcb_y + 2*FIT_CLEARANCE + 2*SURROUND:.3f} x {TOP_THICKNESS:.3f} mm")
    print(f"Total height: {TOTAL_HEIGHT:.3f} mm "
          f"(legs: {TOTAL_HEIGHT - TOP_THICKNESS:.3f} mm)")
    print(f"Wrote {STEP_FILE.name} and {STL_FILE.name}")


if __name__ == "__main__":
    main()
