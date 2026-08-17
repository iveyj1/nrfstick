#!/usr/bin/env python3
"""Generate connector-down and connector-up versions of the inverted fixture.

The physical PCB -Z surface is the reference for the USB connector -Z
surface. Each run writes separate STEP and STL files for these variants:

* connector-down: USB -Z surface is 4.8 mm below the PCB -Z surface.
* connector-up:   USB -Z surface is 0.5 mm above the PCB -Z surface.

The highest fixture surface is Z=0 and the base bottom is Z=-TOTAL_HEIGHT,
so both variants retain the requested overall height. Dimensions are mm.
"""

from pathlib import Path

import cadquery as cq
from cadquery import exporters

from pcb_support_fixture import PCB_FILE, pcb_edge_bounds

OUTPUT_STEM = "pcb_support_fixture"

PCB_THICKNESS = 1.6
TOTAL_HEIGHT = 25.0
BASE_THICKNESS = 3.0
SURROUND = 5.0
LEG_DIAMETER = 5.0
CORNER_LEDGE = 1.0
PCB_LEG_INSET = 0.5
USB_LEG_INSET = 0.5
LEG_BASE_OVERLAP = 0.10

USB_WIDTH_X = 12.0
USB_LENGTH_Y = 19.0
USB_HEIGHT = 4.5
USB_EXTENSION_FROM_PCB_NEG_Y = 15.0
USB_RIM_ABOVE_CONNECTOR_BOTTOM = 1.5

# Signed offsets from the physical PCB -Z surface to the USB -Z surface.
# Positive is +Z (above the board); negative is -Z (below the board).
USB_NEG_Z_OFFSETS = {
    "connector_down": -4.8,
    "connector_up": 0.5,
}

FIT_CLEARANCE = 0.0
CUT_EPSILON = 0.05


def upward_box(x_size: float, y_size: float, z_bottom: float,
               z_top: float, center_x: float = 0.0,
               center_y: float = 0.0) -> cq.Workplane:
    """Create an axis-aligned box extending from z_bottom to z_top."""
    if z_top <= z_bottom:
        raise ValueError("Box top must be above its bottom")
    return (
        cq.Workplane("XY", origin=(center_x, center_y, z_bottom))
        .box(x_size, y_size, z_top - z_bottom, centered=(True, True, False))
    )


def make_inverted_fixture(pcb_x: float, pcb_y: float,
                           usb_neg_z_offset: float) -> cq.Workplane:
    if not 0 < CORNER_LEDGE <= 1.0:
        raise ValueError("CORNER_LEDGE must be greater than zero and at most 1 mm")
    if TOTAL_HEIGHT <= BASE_THICKNESS:
        raise ValueError("TOTAL_HEIGHT must be greater than BASE_THICKNESS")

    pcb_half_x = pcb_x / 2.0
    pcb_half_y = pcb_y / 2.0
    leg_radius = LEG_DIAMETER / 2.0

    usb_y_min = -pcb_half_y - USB_EXTENSION_FROM_PCB_NEG_Y
    usb_y_max = usb_y_min + USB_LENGTH_Y
    usb_center_y = (usb_y_min + usb_y_max) / 2.0

    # First calculate all vertical planes relative to the PCB top. If the
    # connector-up rim would be highest, shift the PCB downward so every
    # variant remains exactly TOTAL_HEIGHT tall.
    pcb_neg_z_relative = -PCB_THICKNESS
    usb_bottom_relative = pcb_neg_z_relative + usb_neg_z_offset
    usb_rim_relative = usb_bottom_relative + USB_RIM_ABOVE_CONNECTOR_BOTTOM
    datum_shift = -max(0.0, usb_rim_relative)

    pcb_top_z = datum_shift
    pcb_bottom_z = pcb_top_z - PCB_THICKNESS
    usb_bottom_z = pcb_bottom_z + usb_neg_z_offset
    usb_rim_z = usb_bottom_z + USB_RIM_ABOVE_CONNECTOR_BOTTOM

    combined_x_min = min(-pcb_half_x, -USB_WIDTH_X / 2.0)
    combined_x_max = max(pcb_half_x, USB_WIDTH_X / 2.0)
    combined_y_min = min(-pcb_half_y, usb_y_min)
    combined_y_max = max(pcb_half_y, usb_y_max)
    base_x = combined_x_max - combined_x_min + 2.0 * SURROUND
    base_y = combined_y_max - combined_y_min + 2.0 * SURROUND
    base_center_x = (combined_x_min + combined_x_max) / 2.0
    base_center_y = (combined_y_min + combined_y_max) / 2.0

    fixture = upward_box(
        base_x, base_y, -TOTAL_HEIGHT, -TOTAL_HEIGHT + BASE_THICKNESS,
        base_center_x, base_center_y,
    )

    # Pocket outlines remain fixed while all six leg centres retain their
    # requested 0.5 mm inward offsets.
    pcb_leg_x = pcb_half_x + leg_radius - CORNER_LEDGE - PCB_LEG_INSET
    pcb_leg_y = pcb_half_y + leg_radius - CORNER_LEDGE - PCB_LEG_INSET
    usb_leg_x = USB_WIDTH_X / 2.0 + leg_radius - CORNER_LEDGE - USB_LEG_INSET
    usb_far_leg_y = usb_y_min - leg_radius + CORNER_LEDGE + USB_LEG_INSET

    positive_y_pcb_legs = [(-pcb_leg_x, pcb_leg_y), (pcb_leg_x, pcb_leg_y)]
    shared_pcb_usb_legs = [(-pcb_leg_x, -pcb_leg_y), (pcb_leg_x, -pcb_leg_y)]
    far_usb_legs = [(-usb_leg_x, usb_far_leg_y), (usb_leg_x, usb_far_leg_y)]

    leg_bottom = -TOTAL_HEIGHT + BASE_THICKNESS - LEG_BASE_OVERLAP
    for centres, leg_top in (
        (positive_y_pcb_legs, pcb_top_z),
        (shared_pcb_usb_legs, max(pcb_top_z, usb_rim_z)),
        (far_usb_legs, usb_rim_z),
    ):
        if leg_top <= leg_bottom:
            raise ValueError("A support leg does not reach above the base")
        for x, y in centres:
            leg = (
                cq.Workplane("XY", origin=(x, y, leg_bottom))
                .circle(leg_radius)
                .extrude(leg_top - leg_bottom)
            )
            fixture = fixture.union(leg)

    pocket_top_z = max(pcb_top_z, usb_rim_z) + CUT_EPSILON
    pcb_pocket = upward_box(
        pcb_x + 2.0 * FIT_CLEARANCE,
        pcb_y + 2.0 * FIT_CLEARANCE,
        pcb_bottom_z,
        pocket_top_z,
    )
    usb_pocket = upward_box(
        USB_WIDTH_X + 2.0 * FIT_CLEARANCE,
        USB_LENGTH_Y + 2.0 * FIT_CLEARANCE,
        usb_bottom_z,
        pocket_top_z,
        center_y=usb_center_y,
    )

    if usb_bottom_z > pcb_bottom_z:
        # In the connector-up version, retain the higher USB support floor
        # where the connector and PCB outlines overlap. Elsewhere the PCB
        # corners still seat at the physical PCB -Z plane.
        usb_exclusion = upward_box(
            USB_WIDTH_X + 2.0 * FIT_CLEARANCE,
            USB_LENGTH_Y + 2.0 * FIT_CLEARANCE,
            pcb_bottom_z - CUT_EPSILON,
            pocket_top_z + CUT_EPSILON,
            center_y=usb_center_y,
        )
        pcb_pocket = pcb_pocket.cut(usb_exclusion)

    fixture = fixture.cut(pcb_pocket).cut(usb_pocket)
    return fixture.clean()


def output_paths(variant_name: str) -> tuple[Path, Path]:
    folder = Path(__file__).parent
    return (
        folder / f"{OUTPUT_STEM}_{variant_name}.step",
        folder / f"{OUTPUT_STEM}_{variant_name}.stl",
    )


def main() -> None:
    x_min, y_min, x_max, y_max = pcb_edge_bounds(PCB_FILE)
    pcb_x, pcb_y = x_max - x_min, y_max - y_min
    print(f"PCB: {pcb_x:.3f} x {pcb_y:.3f} x {PCB_THICKNESS:.3f} mm")

    for variant_name, offset in USB_NEG_Z_OFFSETS.items():
        fixture = make_inverted_fixture(pcb_x, pcb_y, offset)
        step_file, stl_file = output_paths(variant_name)
        exporters.export(fixture, str(step_file))
        exporters.export(
            fixture, str(stl_file), tolerance=0.02, angularTolerance=0.1
        )
        direction = "above" if offset >= 0 else "below"
        print(
            f"{variant_name}: USB -Z surface {abs(offset):.3f} mm {direction} "
            f"PCB -Z; wrote {step_file.name} and {stl_file.name}"
        )

    print(f"Overall height: {TOTAL_HEIGHT:.3f} mm; USB rim height: "
          f"{USB_RIM_ABOVE_CONNECTOR_BOTTOM:.3f} mm")


if __name__ == "__main__":
    main()
