# PCB layout chronicle

Brief record of work, decisions, and reasons. Release readiness is tracked against
`release-package.txt`; it is a checklist, not an ordered procedure. Each applicable
item must be completed or explicitly dismissed with a reason before release.

## Session 1 — API setup and routing reset

- Confirmed KiCad 10.0.2 and connected to the open `nrfstick.kicad_pcb` using
  the IPC API (`kicad-python` in `/tmp/nrfstick-kicad-api-venv`). Use the live
  editor API rather than direct PCB text edits, per user preference.
- User confirmed the prior board state is committed in Git.
- Initial API inventory: 4 copper layers, 28 footprints, 277 trace segments,
  41 vias, and 2 zones.
- Removed all 277 trace segments and 41 vias through IPC at user request,
  grouped as one undoable operation. Verified zero traces/vias remained;
  28 footprints and 2 zones retained. Changes were left unsaved in the editor.

## Placement and review decisions

- Keep J1, SW4, D7, D8, and U5 on the front, per user requirement.
- Preserve J1's board-edge placement and connector overhang toward the user's
  “down Y” direction. Use its current orientation/position as the reference;
  do not infer the coordinate sign from that description alone.
- Provide six fiducials: three front and three back, preferably as matched
  front/back pairs at identical X/Y coordinates, per user preference.
- Keep D7 and D8 adjacent. Their overall location is flexible, but their
  orientations must be parallel or antiparallel; currently antiparallel.
- Defer silkscreen conflicts and errors until layout is near final to avoid
  spending effort on markings that placement changes may invalidate.
- Read `release-package.txt`. Track its items throughout the work rather than
  executing it sequentially. Project-specific examples and potentially unrelated
  requirements need applicability review, not automatic execution or dismissal.
- Maintain this chronicle with brief actions, decisions, and reasons at user
  request. No release checklist items have yet been marked complete or dismissed.

## Session 2 — First placement changes

- User upgraded to KiCad 10.0.6. Verified live IPC connection and that the
  routing reset persisted (zero traces/vias). Native API footprint flipping
  is now available; no UI flip automation was needed.
- Flipped J1 to front using the native left/right mirror, retaining its anchor
  at (106.8, 97.2) mm and its locked state. Verified signal-pad Y coordinates
  remain 94.6 mm, preserving the connector's longitudinal placement and
  overhang direction. Its orientation changes from 180° to 0° as part of the
  side flip; pin X positions mirror as required.
- Flipped Z1, C8, C16, R8, and R9 to back at their existing anchors to clear
  the front USB area. This is provisional placement, not routing optimization.
- Grouped these changes into one undoable API commit; left unsaved in editor.
- U5, SW4, D7/D8, and all six fiducials remain at their previous placements.
  Fiducial pairs already match X/Y. Switch and LED front-side requirements
  are still outstanding.
- Identified a placement constraint: U5's body/courtyard occupies most of the
  front width through Y≈93 mm; J1's signal-pad courtyard starts at Y≈93.35 mm.
  Simply flipping SW4 and D7/D8 in place would overlap U5. Preserved U5 and
  the board outline pending a mechanical-space decision. Full courtyard,
  copper, antenna-clearance, and 3D validation remains outstanding; silkscreen
  review is deferred as agreed.

## Session 3 — Board growth and required front-side placement

- User authorized growing the PCB upward as needed, with U5 still overhanging
  the antenna edge and that edge aligned to the footprint guide.
- Extended the upper Edge.Cuts boundary from Y=82.6 to Y=77.6 mm (upward is
  decreasing Y in this board's coordinates). Width remains 13.6 mm; board
  length increases from 17.4 to 22.4 mm. USB-end edge remains Y=100 mm.
  Chose 5 mm to create a component row with clearance to U5 and J1.
- Moved U5 from (106.8, 85.0) to (106.8, 80.0) mm without rotation or side
  change. Its edge guide moves from Y=82.6 to Y=77.6 mm with the board edge;
  the nominal 5.5 mm module-body overhang is unchanged. J1 remains fixed.
- Flipped SW4, D7, and D8 to front using the native API, then placed them:
  - SW4: (102.5, 90.6) mm, 0°.
  - D7: (106.6, 90.6) mm, 0°.
  - D8: (110.4, 90.6) mm, 180°.
  LEDs remain adjacent and antiparallel. All five required parts are now on
  front. Existing footprint lock states were retained.
- Moved the two upper fiducial pairs upward 5 mm to Y=80.8 mm; the lower pair
  stays at Y=94.6 mm. Verified three front/back pairs with matching X/Y.
- Moved J2 upward 5 mm to retain its position relative to the module/edge.
  Moved Y1 upward 5 mm to stay close to U5's crystal pins. Moved C16 to
  (102.7, 86.5) mm on back, close to the shifted module's VDD pads.
- Extended both copper-zone upper boundaries by 5 mm, retaining their nets,
  layers, and settings, then refilled using KiCad. No traces or vias added.
- Changes applied through IPC in one placement/outline undo transaction;
  zone refill followed separately. Did not explicitly save the working board.
- Initial attempts were rolled back before commit while adapting to the API:
  updates inside an open transaction are returned by UpdateItems but are not
  yet visible through GetItems. Final state was verified after commit.

### Preliminary validation and release follow-ups

- Exported live-board snapshots through IPC and ran KiCad CLI DRC using a
  copied project configuration and the project footprint library. Reports:
  `/tmp/nrfstick-layout-review/drc.json` and
  `/tmp/nrfstick-layout-before/drc.json` (temporary, not release artifacts).
- No courtyard-overlap violations reported. All four outline segments form
  the enlarged rectangle, and required front placements/fiducial pairing were
  checked via API. This is preliminary validation, not final release signoff.
- Two J1 shell-pad copper-to-board-edge clearance violations existed before
  growth and remain (actual 0 mm versus required 0.3 mm). Must resolve or
  explicitly justify against connector/manufacturer requirements before release.
- Isolated VDD-plane copper also existed before growth; revisit during routing.
  Current DRC reports 47 unconnected items, expected for the unrouted board.
- DRC now flags SW4 as differing from its library footprint after the flip/
  rotation. Review the difference before release; do not overwrite either
  footprint or library blindly. Other new reported issues are silkscreen,
  which remains deferred by agreement.
- Board-dependent mechanical support/preview exports in `cad/` are now stale
  relative to this live outline. Regenerate and review once board size is
  settled and saved. Full 3D/antenna clearance and manufacturing review remain
  open; no checklist item has been dismissed.

## Session 4 — Saved placement and first routing passes

- Saved the enlarged/placed board through IPC at user request, then started
  routing. Saved routing progress again after final DRC for this session.
- Added short crystal connections with one through-via per signal, connected
  C16 directly to U5's VDD escape, and connected ground/VDD pads to their
  existing planes. Joined U4's exposed ground pad to its ground pin without
  introducing open vias into the exposed solder pad.
- Routed switch, LED, programming, module reset, and UART connections. Explicitly
  connected both same-number switch pads rather than assuming an internal tie.
  Routed the local VBUS divider link; its connection to U4 is still outstanding.
- Used 0.15 mm control traces, 0.2–0.25 mm local power/ground traces,
  0.4/0.2 mm diameter/drill plane vias, and 0.35/0.15 mm signal/compact vias.
  These satisfy current project DRC settings; fabrication capability still
  needs release review. No blind/microvias or internal-plane signal tracks added.
- Placement refinement during routing:
  - Moved R15/R16 to front beside their LEDs at (106.6, 92.4) and
    (110.0, 92.4) mm, both 0°, to avoid long back-side resistor connections.
  - Moved R29 to back at (101.55, 88.1) mm, 0°, near the supervisor.
    Replaced its approximately 21.7 mm feed detour with a 2.39 mm connection.
  - Shared one VDD escape between adjacent U4 supply pins instead of retaining
    a redundant via that blocked the module UART escape.
- Routing uses live API objects; candidate paths were checked against pad
  polygons, existing copper, holes, and board-edge bounds before insertion.
  KiCad DRC remains authoritative. A short created by moving R29 across an
  existing reset trace was detected and repaired before the final save.
- Found stale polygon-query geometry for J1/Z1 after native side flips: queried
  pad polygons retained old X positions although pad positions had changed.
  Round-tripping those footprints through API UpdateItems refreshed the geometry;
  verified pad/polygon alignment before continuing. No PCB text edits used.
- Current saved board: **197 trace segments, 32 vias; 10 unconnected items**.
  Remaining connections: four +5V links, four USB data links through Z1, U4's
  VBUS sense connection, and U4's reset pull-up connection.
- Final saved-board DRC: no shorts, track-clearance, dangling-via, or isolated
  copper violations. The two existing J1 shell-pad edge-clearance violations
  remain. Four library-footprint mismatch warnings (SW4, R15, R16, R29) and
  deferred silkscreen issues also remain. Report:
  `/tmp/nrfstick-layout-review/drc-routing-saved.json` (temporary).
- This is **provisional routing, not a completed layout**. Several control routes
  still detour, including a roughly 27 mm reset section after moving R29.
  Next pass should shorten those with placement/layer-transition changes,
  reserve and route the USB corridor with appropriate geometry/reference-plane
  review, and finish +5V and U4 controls. Do not treat the current DRC result as
  signal-integrity, decoupling, manufacturing, or release signoff.

## Session 5 — USB-first restart; connectivity completed

- User approved ripping up the problematic routing and suggested moving C7 up,
  U3 left, and/or U4 right/down. Removed 221 routing items, retaining only the
  six crystal segments and two crystal vias. Preserved a temporary pre-restart
  snapshot at `/tmp/nrfstick-before-usb-restart.kicad_pcb`.
- Adopted the placement direction: U3 to (103.2, 89.8) mm, U4 to
  (109.8, 89.9) mm, C7 to (106.9, 85.3) mm and C8 to (108.7, 85.3) mm.
  Rotated Z1 to 90° at (106.8, 94.8) mm so its connector-side pads face J1.
  Regrouped the divider, pull-up and supervisor passives locally. Moved R15/R16
  to Y=88.8 mm, above the LEDs, to free the USB crossover area below them.
- Routed USB before other signals. Used a short front-side crossover to handle
  connector/ESD/bridge pin ordering, with back-side runs into U4. Both complete
  data paths have three through-vias. Track-only lengths are approximately
  11.053 mm (D−) and 11.018 mm (D+), a 0.035 mm difference. USB traces are
  0.2 mm wide, with 0.4/0.2 mm diameter/drill vias. This is geometric matching,
  not a verified differential-impedance claim; stackup/fabricator review remains.
- Added an In2 ground-reference zone beneath USB, retaining VDD in the upper
  part of In2 (VDD zone ends at Y=88.8 mm). In1 remains ground. Added local
  return stitches at the USB transitions; no vias were placed in solder pads.
- Routed +5V, bridge regulator/IO supply, the VBUS divider/sense connection,
  module decoupling, and plane returns before general controls. The divider's
  sense line now reaches U4; the +5V distribution and USB links are complete.
- Reworked control routing with legal layer transitions and prioritized both
  UART escapes. Rejected large perimeter detours rather than retaining the
  earlier approximately 27 mm reset section. UART RX is about 7.15 mm and TX
  about 14.64 mm; UART signals are not length-matched and do not require USB-style
  matching. Further aesthetic/length refinement is possible without claiming
  that every route is optimal.
- **Routing-policy adjustment:** used two In2 signal connections in the upper
  VDD region for U4 reset and LED_RED after outer-only routing became congested.
  These end at or above Y=88.0 mm and do not enter the lower USB ground-reference
  region. In1 is still continuous ground, with no signal tracks. Refilled and
  checked that the upper VDD fill remains connected (no isolated-copper report).
- Connected D8's return explicitly to a ground stitch outside the bridge pads;
  did not rely on a small, isolated front pour or introduce via-in-pad assembly
  requirements to obtain connectivity.
- **Saved result:** 195 trace segments, 51 vias, three zones. Final DRC run on
  the saved `nrfstick.kicad_pcb` reports **zero unconnected items** and no shorts,
  track-clearance, dangling-via, isolated-copper, or courtyard-overlap violations.
  Report: `/tmp/nrfstick-layout-review/drc-retry-saved.json` (temporary).
- Remaining DRC/release work: the two existing J1 shell-pad edge-clearance
  violations; eight footprint-library mismatches (R16, R15, SW4, U4, R29, R7,
  R8, Z1); and deferred silkscreen issues. Do not dismiss library differences
  without comparison. Zero unconnected items is not final release approval.
- Verified J1 and U5 anchors unchanged, all five required parts still on front,
  antenna-edge alignment retained, and all three fiducial pairs still matched.
  Chronicle and saved board now supersede Session 4's incomplete-routing status.

## Session 6 — Larger SW4 candidate (research only)

- User requested a slightly larger SMD pushbutton. Recommended evaluating Alps
  Alpine **SKRPABE010**: 4.2 × 3.2 mm body, 2.5 mm height, top push, 1.57 N
  operating force, 0.2 mm travel, 100,000-cycle rating. The manufacturer's drawing
  shows a wider stem, approximately 3.0 × 2.2 mm, and a recommended land pattern
  spanning 5.2 × 2.8 mm. This is a modest enlargement rather than a 6 mm switch.
- Verified specifications and drawings at
  `https://tech.alpsalpine.com/e/products/detail/SKRPABE010/` and its linked
  product specification/catalog PDFs. DigiKey blocked automated access, so
  current listing availability, stock and pricing were not verified.
- No schematic, footprint, or PCB changes made. Selection is pending user
  approval; check purchasing availability, pin mapping and placement clearances
  before substituting. No release checklist items dismissed.

## Session 7 — SW4 substitution completed and committed

- User confirmed stock/price, approved SKRPABE010, and requested a commit.
- Updated SW4 through the **Schematic Editor UI**: value, footprint, datasheet,
  description, MFR and MFR_PN. Saved and verified that the schematic diff contains
  only these six field changes; symbol, pins, wires and other components unchanged.
- Added `footprint.pretty/SW_Push_Alps_SKRPABE010.kicad_mod`, exported using
  KiCad's native Python API. Manufacturer land pattern: 1.05 × 0.65 mm pads at
  X=±2.075, Y=±1.075 mm; 4.2 × 3.2 mm body; 0.25 mm courtyard allowance.
  Verified the manufacturer's circuit diagram: physical terminals 1–2 form
  one pole and 3–4 the other. The footprint maps the upper pair to schematic
  pin 1/GND and the lower pair to pin 2/BUTTON. No connection is assumed between
  opposing poles when the button is released.
- Replaced geometry through live IPC, retaining SW4's UUID, schematic linkage,
  pin nets, front side and locked state. SW4 now sits at (102.95, 90.6) mm.
  Shifted D7, D8, R15 and R16 right by 1 mm to accommodate it; LED adjacency
  and antiparallel orientation are retained. J1, U5 and the outline stay fixed.
- Repaired the affected button/LED wiring and short local portions of reset,
  UART RX and +5V around the enlarged footprints. Preserved USB data routing
  and the upper In2 LED connection. Saved board: 197 segments and 51 vias.
- Exported the schematic netlist and checked SW4's part fields and GND/BUTTON
  mapping against the PCB. Final saved-board DRC: **zero unconnected items**,
  no new copper/short/hole-clearance errors, and no SW4 library mismatch.
  Seven older footprint mismatches, the two J1 edge-clearance violations and
  deferred silkscreen findings remain. Report:
  `/tmp/nrfstick-layout-review/drc-sw4-saved.json` (temporary).
- This was a selective SW4 substitution, not a full schematic-to-PCB update;
  the separately introduced RTS/CTS schematic changes still need their own
  PCB synchronization/review. No unrelated schematic changes were propagated.
