"""Adam Tech USB-AP-S-RA-SMT visualization model, drawing S00167-T-1 rev J.
Run: ./cad/cq cad/adamtech_usb_ap_s_ra_smt.py
See adamtech_usb_ap_s_ra_smt.md for approximations and coordinates.
"""
from pathlib import Path
import cadquery as cq

# Drawing dimensions, mm.
SHELL_WIDTH = 12.0
SHELL_LENGTH = 18.8
SHELL_HEIGHT = 4.5
TOP_ABOVE_PCB = 3.3
TOTAL_HEIGHT_WITH_TABS = 5.8
TAB_WIDTH = 2.0
TAB_X = 11.4 / 2
PEG_X = 4.5 / 2
PEG_DIAMETER = 0.85
TAIL_WIDTH = 0.7
TAIL_PROJECTION = 1.7
PIN_X = (3.5, 1.0, -1.0, -3.5)

# Undimensioned visualization details, not manufacturing geometry.
REAR = -1.0  # Approximate rear registration to mounting-hole datum.
SHELL_GAUGE = 0.3
CORNER_RADIUS = 0.35
INNER_RADIUS = 0.15
RELIEF_TOP = 1.25
PEG_LENGTH = 0.9
CONTACT_THICKNESS = 0.2
FRONT = REAR + SHELL_LENGTH
BOTTOM = TOP_ABOVE_PCB - SHELL_HEIGHT
TAB_BOTTOM = TOP_ABOVE_PCB - TOTAL_HEIGHT_WITH_TABS
RELIEF_END = FRONT - 14.7
OUTPUT = Path(__file__).with_suffix('.step')


def block(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1-x0, y1-y0, z1-z0).translate(
        ((x0+x1)/2, (y0+y1)/2, (z0+z1)/2))


outer = block(-6, 6, REAR, FRONT, BOTTOM, TOP_ABOVE_PCB).edges('|Y').fillet(CORNER_RADIUS)
inner = block(-6+SHELL_GAUGE, 6-SHELL_GAUGE, REAR-1, FRONT+1,
              BOTTOM+SHELL_GAUGE, TOP_ABOVE_PCB-SHELL_GAUGE).edges('|Y').fillet(INNER_RADIUS)
shell = outer.cut(inner)
shell = shell.cut(block(-7, 7, REAR-0.1, RELIEF_END, -4, RELIEF_TOP))
for x in (-TAB_X, TAB_X):
    tab = (cq.Workplane('YZ', origin=(x-SHELL_GAUGE/2, 0, 0))
           .moveTo(-TAB_WIDTH/2, RELIEF_TOP+0.2)
           .lineTo(-TAB_WIDTH/2, TAB_BOTTOM+TAB_WIDTH/2)
           .threePointArc((0, TAB_BOTTOM), (TAB_WIDTH/2, TAB_BOTTOM+TAB_WIDTH/2))
           .lineTo(TAB_WIDTH/2, RELIEF_TOP+0.2).close().extrude(SHELL_GAUGE))
    shell = shell.union(tab)
# Approximate top/bottom retention windows.
for x in (-3.0, 3.0):
    shell = shell.cut(block(x-1.3, x+1.3, 10.8, 13.6, BOTTOM-0.1, TOP_ABOVE_PCB+0.1))

# Simplified black insulator and locating pegs; no internal spring/contact detail.
insulator = block(-5.5, 5.5, REAR, 3.2, 0.2, 2.9)
insulator = insulator.union(block(-5.1, 5.1, 3.0, FRONT-0.8, 1.0, 2.9))
for x in (-PEG_X, PEG_X):
    peg = cq.Workplane('XY').center(x, 0).circle(PEG_DIAMETER/2).extrude(PEG_LENGTH+0.25).translate((0, 0, -PEG_LENGTH))
    insulator = insulator.union(peg)

# KiCad model Y is opposite footprint Y; Z=0 is PCB top. No placement transform needed.
parts = [('nickel_shell', shell.mirror('XZ'), cq.Color(0.72, 0.74, 0.77)),
         ('black_insulator', insulator.mirror('XZ'), cq.Color(0.08, 0.08, 0.08))]
for number, x in enumerate(PIN_X, 1):
    tail = block(x-TAIL_WIDTH/2, x+TAIL_WIDTH/2, REAR-TAIL_PROJECTION, REAR+0.4, 0, CONTACT_THICKNESS)
    # Mating contact faces on underside of the insulator tongue.
    contact = block(x-0.5, x+0.5, 4.0, FRONT-1.0, 0.85, 1.05)
    parts.append((f'tin_tail_{number}', tail.mirror('XZ'), cq.Color(0.8, 0.8, 0.82)))
    parts.append((f'gold_contact_{number}', contact.mirror('XZ'), cq.Color(0.85, 0.65, 0.2)))
assembly = cq.Assembly(name='AdamTech_USB_AP_S_RA_SMT')
for name, shape, color in parts:
    assembly.add(shape, name=name, color=color)

if 'show_object' in globals():
    show_object(assembly)


def export_and_check():
    for name, shape, _ in parts:
        assert shape.val().isValid(), f'Invalid BREP: {name}'
        assert len(shape.solids().vals()) == 1, f'Disconnected part: {name}'
    bounds = parts[0][1].val().BoundingBox()
    actual = (bounds.xmin, bounds.xmax, bounds.ymin, bounds.ymax, bounds.zmin, bounds.zmax)
    expected = (-6, 6, -17.8, 1, -2.5, 3.3)
    assert all(abs(a-b) < 1e-5 for a, b in zip(actual, expected)), actual
    assembly.export(str(OUTPUT))
    imported = cq.importers.importStep(str(OUTPUT))
    assert imported.val().isValid(), 'Invalid STEP round trip'
    assert len(imported.solids().vals()) == len(parts), 'Unexpected STEP solid count'
    print(f'Exported {OUTPUT}: {len(parts)} solids; shell 12 x 18.8 x 5.8 mm')


if __name__ == '__main__':
    export_and_check()
