#!/usr/bin/env python3
"""
CadQuery board support for nrfstick.kicad_pcb.

The script parses the rectangular Edge.Cuts outline from the KiCad PCB file and
builds a 5 mm tall base with four 6 mm diameter corner posts.  Each post rises
24 mm from the bottom of the base and has a 2 mm x 2 mm x 1.6 mm top cutout for
one PCB corner, leaving the top of the PCB flush with the top of the posts.
"""

from __future__ import annotations

import re
from pathlib import Path

import cadquery as cq
from cadquery import exporters


# ----------------------------
# Parameters
# ----------------------------

PCB_FILE = Path(__file__).resolve().parent.parent / "nrfstick.kicad_pcb"
OUTPUT_STEP = Path(__file__).with_suffix(".step")
PCB_PREVIEW_STEP = Path(__file__).with_name("nrfstick_pcb_preview.step")

BASE_HEIGHT = 5.0
POST_TOP_Z = 24.0              # total height from bottom of base to post top
POST_DIAMETER = 6.0
PCB_THICKNESS = 1.6
BOARD_CORNER_OVERLAP = 2.0     # how far each board corner enters its post
CUTOUT_CLEARANCE = 0.15        # XY clearance so the PCB drops in easily
CUTOUT_Z_OVERCUT = 0.5         # ensures cutout opens cleanly through post top

BASE_EXTRA_XY = 12            # base is 4 mm larger than PCB in X and Y
BASE_MARGIN = BASE_EXTRA_XY / 2.0
BASE_VERTICAL_EDGE_FILLET = 0.75
POST_RADIUS = POST_DIAMETER / 2.0
POST_CENTER_OUTSET = POST_RADIUS - BOARD_CORNER_OVERLAP
POST_BASE_FILLET_REQUESTED = 1.5
# Clamp the collar/chamfer so it stays inside the base margin even if post
# diameter, overlap, or base size changes.
POST_BASE_FILLET = max(
    0.0,
    min(
        POST_BASE_FILLET_REQUESTED,
        BASE_MARGIN - POST_CENTER_OUTSET - POST_RADIUS - 0.1,
    ),
)
TEXT_HEIGHT = .4
TEXT_SIZE = 3.5
TEXT_LINE_SPACING = 3


# ----------------------------
# KiCad Edge.Cuts parsing
# ----------------------------

def parse_edge_cuts_bounds(pcb_file: Path) -> tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) from Edge.Cuts gr_line segments."""
    text = pcb_file.read_text()
    points: list[tuple[float, float]] = []

    # KiCad writes each gr_line as a small s-expression that ends after its uuid.
    # This is intentionally lightweight and avoids depending on a KiCad parser.
    for match in re.finditer(r"\(gr_line\b[\s\S]*?\(uuid\s+\"[^\"]+\"\)\s*\)", text):
        block = match.group(0)
        if 'layer "Edge.Cuts"' not in block:
            continue

        start = re.search(r"\(start\s+([-+0-9.]+)\s+([-+0-9.]+)\)", block)
        end = re.search(r"\(end\s+([-+0-9.]+)\s+([-+0-9.]+)\)", block)
        if not start or not end:
            continue

        points.extend([
            (float(start.group(1)), float(start.group(2))),
            (float(end.group(1)), float(end.group(2))),
        ])

    if not points:
        raise ValueError(f"No Edge.Cuts gr_line points found in {pcb_file}")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def board_size_from_pcb(pcb_file: Path = PCB_FILE) -> tuple[float, float]:
    min_x, min_y, max_x, max_y = parse_edge_cuts_bounds(pcb_file)
    return max_x - min_x, max_y - min_y


def parse_title_block_text(pcb_file: Path = PCB_FILE) -> list[str]:
    """Extract printable title block lines from the KiCad PCB file."""
    text = pcb_file.read_text()
    match = re.search(r"\(title_block\b([\s\S]*?)\n\s*\)", text)
    if not match:
        return []

    block = match.group(1)
    lines: list[str] = []
    for field in ("title", "date", "rev", "company"):
        value = re.search(rf"\({field}\s+\"([^\"]*)\"\)", block)
        if value and value.group(1):
            lines.append(value.group(1))

    return lines


# ----------------------------
# Geometry
# ----------------------------

def base(board_width: float, board_length: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(
            board_width + 2 * BASE_MARGIN,
            board_length + 2 * BASE_MARGIN,
            BASE_HEIGHT,
            centered=(False, False, False),
        )
        .translate((-BASE_MARGIN, -BASE_MARGIN, 0))
        .edges("|Z")
        .fillet(BASE_VERTICAL_EDGE_FILLET)
    )


def title_block_text(lines: list[str], board_width: float, board_length: float) -> cq.Workplane:
    """Raised title-block lettering on the top surface of the base."""
    text_body = cq.Workplane("XY")
    if not lines:
        return text_body

    total_height = (len(lines) - 1) * TEXT_LINE_SPACING
    first_y = board_length / 2.0 + total_height / 2.0

    for index, line in enumerate(lines):
        y = first_y - index * TEXT_LINE_SPACING
        text_body = text_body.union(
            cq.Workplane("XY")
            .text(line, TEXT_SIZE, TEXT_HEIGHT, combine=True, halign="center", valign="center")
            .translate((board_width / 2.0, y, BASE_HEIGHT))
        )

    return text_body


def post() -> cq.Workplane:
    """6 mm post with a simple tapered collar where it leaves the base."""
    post_body = (
        cq.Workplane("XY")
        .circle(POST_RADIUS)
        .extrude(POST_TOP_Z)
    )

    if POST_BASE_FILLET <= 0:
        return post_body

    base_fillet = cq.Workplane("XY").newObject([
        cq.Solid.makeCone(
            POST_RADIUS + POST_BASE_FILLET,
            POST_RADIUS,
            POST_BASE_FILLET,
            pnt=(0, 0, BASE_HEIGHT),
            dir=(0, 0, 1),
        )
    ])
    return post_body.union(base_fillet)


def corner_cutout(x_dir: int, y_dir: int) -> cq.Workplane:
    """
    Cutout whose outer two vertical walls line up with the PCB edges.

    x_dir/y_dir point into the PCB from the corner: +1 for min side corners,
    -1 for max side corners.  The post center is offset outward from the PCB
    corner, so the cutout runs from the PCB edge to/past the far edge of the
    post while maintaining the requested 2 mm board/post overlap.
    """
    start = POST_CENTER_OUTSET
    end = POST_CENTER_OUTSET + BOARD_CORNER_OVERLAP + CUTOUT_CLEARANCE
    size = end - start
    z0 = POST_TOP_Z - PCB_THICKNESS

    x0 = start if x_dir > 0 else -end
    y0 = start if y_dir > 0 else -end

    return (
        cq.Workplane("XY")
        .box(
            size,
            size,
            PCB_THICKNESS + CUTOUT_Z_OVERCUT,
            centered=(False, False, False),
        )
        .translate((x0, y0, z0))
    )


def corner_post(board_corner_x: float, board_corner_y: float, x_dir: int, y_dir: int) -> cq.Workplane:
    post_x = board_corner_x - x_dir * POST_CENTER_OUTSET
    post_y = board_corner_y - y_dir * POST_CENTER_OUTSET
    return post().cut(corner_cutout(x_dir, y_dir)).translate((post_x, post_y, 0))


def board_support(
    board_width: float | None = None,
    board_length: float | None = None,
    title_lines: list[str] | None = None,
) -> cq.Workplane:
    if board_width is None or board_length is None:
        board_width, board_length = board_size_from_pcb()
    if title_lines is None:
        title_lines = parse_title_block_text()

    body = base(board_width, board_length).union(
        title_block_text(title_lines, board_width, board_length)
    )

    placements = [
        (0.0,         0.0,          1,  1),
        (board_width, 0.0,         -1,  1),
        (0.0,         board_length, 1, -1),
        (board_width, board_length, -1, -1),
    ]

    for x, y, x_dir, y_dir in placements:
        body = body.union(corner_post(x, y, x_dir, y_dir))

    return body


def pcb_preview(board_width: float, board_length: float) -> cq.Workplane:
    """A simple board-volume reference, not included in the exported support."""
    return (
        cq.Workplane("XY")
        .box(
            board_width,
            board_length,
            PCB_THICKNESS,
            centered=(False, False, False),
        )
        .translate((0, 0, POST_TOP_Z - PCB_THICKNESS))
    )


# ----------------------------
# Build/export
# ----------------------------

width, length = board_size_from_pcb()
title_lines = parse_title_block_text()
support = board_support(width, length, title_lines)
preview = pcb_preview(width, length)

# Show objects when run in CQ-editor/cw-editor.  Keep this at module scope because
# some editors execute the script without taking the normal __main__ path.
try:
    show_object(support, name="nrfstick_board_support")
    show_object(preview, name="pcb_preview")
except Exception:
    pass


if __name__ == "__main__":
    exporters.export(support, str(OUTPUT_STEP))
    exporters.export(preview, str(PCB_PREVIEW_STEP))
    print(f"Board outline: {width:.3f} mm x {length:.3f} mm")
    print(f"Title block text: {' | '.join(title_lines) if title_lines else '(none)'}")
    print(f"Exported: {OUTPUT_STEP}")
    print(f"Exported: {PCB_PREVIEW_STEP}")
