# Agent Guidance

## Project context
- This repository contains a KiCad PCB design for `nrfstick`.
- Main PCB file: `nrfstick.kicad_pcb`.
- CadQuery work lives in `cad/`.

## CadQuery workflow
- Use the helper script to run CadQuery files:

  ```bash
  ./cad/cq cad/<script>.py
  ```

- `cad/cq` activates the CadQuery virtualenv from `$HOME/cadquery/.venv_cadquery` and runs the given Python script.
- Prefer standalone CadQuery scripts for generated mechanical parts.
- Export STEP files from scripts so results can be checked outside cq-editor.
- For cq-editor visibility, keep `show_object(...)` calls at module scope rather than only inside `if __name__ == "__main__"`.

## Existing board support model
- Current support script: `cad/nrfstick_board_support.py`.
- It parses `nrfstick.kicad_pcb` Edge.Cuts to determine board size.
- It parses the KiCad title block and raises the title/date text on the base top surface.
- It exports:
  - `cad/nrfstick_board_support.step`
  - `cad/nrfstick_pcb_preview.step`

## Board support design assumptions
- PCB thickness: `1.6 mm`.
- Four 4 mm diameter posts are centered on PCB outline corners.
- PCB corner overlap into each post: `2 mm`.
- PCB drops in from the top and sits in corner cutouts.
- Top of PCB is flush with top of posts.
- Total post/top height from base bottom is currently `24 mm`.
- Base height is `5 mm`.
- Base is larger than the board by `BASE_EXTRA_XY` in X/Y, with margin `BASE_EXTRA_XY / 2` on each side.

## KiCad parsing notes
- Edge.Cuts are currently simple `gr_line` records forming a rectangle.
- If the board outline changes to arcs or non-rectangular geometry, update the parser/model accordingly.
- Title block currently uses fields like `(title "...")` and `(date "...")` near the top of `nrfstick.kicad_pcb`.

## Coding preferences
- Keep generated CAD parameters near the top of the script.
- Use clear constants for dimensions.
- Run `./cad/cq cad/nrfstick_board_support.py` after edits to verify the model exports.
