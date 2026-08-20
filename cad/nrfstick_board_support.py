#!/usr/bin/env python3
"""
CadQuery board support for nrfstick.kicad_pcb.

The script parses the rectangular Edge.Cuts outline from the KiCad PCB file and
builds a 5 mm tall rectangular base with four 6 mm diameter corner posts plus
one shorter USB 
tor support post.  The corner posts rise 24 mm from the
bottom of the base and have 2 mm x 2 mm x 1.6 mm top cutouts for the PCB
corners, leaving the top of the PCB flush with the top of the corner posts.
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

USB_POST_Y_OFFSET = 8.0        # USB support post is this far below the PCB -Y edge
USB_POST_TOP_BELOW_PCB_TOP = 2.6
USB_POST_TOP_Z = POST_TOP_Z - USB_POST_TOP_BELOW_PCB_TOP

BASE_VERTICAL_EDGE_FILLET = 0.75
BASE_POST_CLEARANCE = 0.25     # extra rectangular base around post/chamfer footprint
POST_RADIUS = POST_DIAMETER / 2.0
POST_CENTER_OUTSET = POST_RADIUS - BOARD_CORNER_OVERLAP
POST_BASE_FILLET = 1.5
POST_FOOTPRINT_RADIUS = POST_RADIUS + POST_BASE_FILLET
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

def corner_post_centers(board_width: float, board_length: float) -> list[tuple[float, float]]:
    return [
        (-POST_CENTER_OUTSET, -POST_CENTER_OUTSET),
        (board_width + POST_CENTER_OUTSET, -POST_CENTER_OUTSET),
        (-POST_CENTER_OUTSET, board_length + POST_CENTER_OUTSET),
        (board_width + POST_CENTER_OUTSET, board_length + POST_CENTER_OUTSET),
    ]


def usb_post_center(board_width: float) -> tuple[float, float]:
    return (board_width / 2.0, -USB_POST_Y_OFFSET)


def support_post_centers(board_width: float, board_length: float) -> list[tuple[float, float]]:
    return corner_post_centers(board_width, board_length) + [usb_post_center(board_width)]


def base_bounds(board_width: float, board_length: float) -> tuple[float, float, float, float]:
    """Rectangular base bounds driven by the footprint of all posts/collars."""
    centers = support_post_centers(board_width, board_length)
    r = POST_FOOTPRINT_RADIUS + BASE_POST_CLEARANCE
    xs = [x for x, _ in centers]
    ys = [y for _, y in centers]
    return min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r


def base(board_width: float, board_length: float) -> cq.Workplane:
    min_x, min_y, max_x, max_y = base_bounds(board_width, board_length)
    return (
        cq.Workplane("XY")
        .box(
            max_x - min_x,
            max_y - min_y,
            BASE_HEIGHT,
            centered=(False, False, False),
        )
        .translate((min_x, min_y, 0))
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


def post(height: float = POST_TOP_Z) -> cq.Workplane:
    """6 mm post with a simple tapered collar where it leaves the base."""
    post_body = (
        cq.Workplane("XY")
        .circle(POST_RADIUS)
        .extrude(height)
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
    return post(POST_TOP_Z).cut(corner_cutout(x_dir, y_dir)).translate((post_x, post_y, 0))


def usb_support_post(board_width: float) -> cq.Workplane:
    x, y = usb_post_center(board_width)
    return post(USB_POST_TOP_Z).translate((x, y, 0))


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

    body = body.union(usb_support_post(board_width))

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
