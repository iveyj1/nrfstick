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
- Four 6 mm diameter corner posts are offset outward from the PCB corners so the board overlap into each post remains `2 mm`.
- PCB drops in from the top and sits in corner cutouts that conform to the PCB edges where they overlap the posts.
- Top of PCB is flush with top of the four corner posts.
- Total corner post/top height from base bottom is currently `24 mm`.
- A fifth 6 mm USB connector support post is on the PCB X centerline, `8 mm` below the PCB -Y edge, with top at `POST_TOP_Z - 2.6 mm`.
- Base height is `5 mm`.
- Base is rectangular and its X/Y bounds are driven by the footprint radius of all five posts plus their chamfer/collar dimensions.

## KiCad parsing notes
- Edge.Cuts are currently simple `gr_line` records forming a rectangle.
- If the board outline changes to arcs or non-rectangular geometry, update the parser/model accordingly.
- Title block currently uses fields like `(title "...")` and `(date "...")` near the top of `nrfstick.kicad_pcb`.

## Coding preferences
- Keep generated CAD parameters near the top of the script.
- Use clear constants for dimensions.
- Run `./cad/cq cad/nrfstick_board_support.py` after edits to verify the model exports.
