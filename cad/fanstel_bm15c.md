# Fanstel BM15C 3D preview

Source: `data/BM15C+Product+Specifications.pdf`, **page 7**, mechanical drawing
explicitly labeled BM15C, draft version 0.53 (August 2024). The overview table
elsewhere in this draft swaps the BM15C/BM15M lengths; this model follows the
15.8 mm BM15C mechanical drawing and the existing project footprint.

## Geometry

- Substrate: **10.0 × 15.8 × 0.6 mm**.
- Overall height at shield: **2.0 mm**, including substrate, not 2.0 mm above it.
- Shield length: **10.3 mm**, flush with the rear substrate edge.
- Chip antenna: **5.5 × 2.0 × 1.0 mm**, mounted above the substrate;
  1.2 mm from the left edge and 0.2 mm from the antenna-end edge, in top view.
- Colored STEP assembly: green substrate, silver hollow shield, ceramic antenna.

Dimensions are nominal. The drawing specifies +0.5/−0.1 mm for module width
and length, ±0.05 mm for substrate thickness, ±0.1 mm for overall height,
±0.5 mm for shield length, and tolerances on the antenna. Account for these
separately in clearance design.

This is locally generated visualization geometry, **not vendor MCAD**. Shield
width is assumed to be 9.8 mm (0.1 mm inset per side); shield gauge is assumed
0.15 mm. Those two dimensions are not given in the drawing. Internal components,
shield embossing, antenna metallization, underside contacts and solder thickness
are omitted. No antenna/RF performance is implied by the simplified geometry.

## KiCad registration

- Footprint: `footprint:Fanstel_BM15C`.
- Model: `${KIPRJMOD}/cad/fanstel_bm15c.step`.
- Scale `(1,1,1)`, rotation `(0,0,0)`, offset `(0,0,0)`.
- Origin: module center in XY, module underside at Z=0 (host PCB top).
- Model +X is footprint +X; model +Y is footprint −Y, toward the antenna.
- STEP bounds: X ±5.0, Y ±7.9, Z 0…2.0 mm.
- Shield's antenna-side edge is at footprint Y=−2.4 mm, matching the footprint's
  existing host-board-edge guide. The antenna region extends beyond that guide.

The model is attached to the library footprint and the live U5 instance.
No pad, layer, placement, unit metadata or routing changes were needed.
Reload an already-open 3D Viewer to display the new model.

## Regeneration

```sh
./cad/cq cad/fanstel_bm15c.py
```

The script checks all three solids, validates the overall envelope, exports
STEP and reloads it to verify BREP validity and solid count. A KiCad STEP export
of U5 was also checked for model-path resolution, dimensions and antenna direction.
