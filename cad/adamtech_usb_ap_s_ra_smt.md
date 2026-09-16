# Adam Tech USB-AP-S-RA-SMT visualization model

Source: `../data/usb-ap-s-ra-smt-data-sheet.pdf`, S00167-T-1 revision J.
Generated with `./cad/cq cad/adamtech_usb_ap_s_ra_smt.py`.
Output: `adamtech_usb_ap_s_ra_smt.step`, a colored ten-solid assembly.

Includes hollow nickel shell, mounting tabs, simplified black insulator with
locating pegs, four tin solder tails and four gold mating contacts.

Drawing dimensions used (mm): shell 12 x 18.8 x 4.5, shell top 3.3 above the
solder plane, 5.8 overall height including tabs, tabs 2.0 long on 11.4 centers,
0.85 diameter pegs on 4.5 centers, 0.7 wide tails projecting 1.7 from the rear,
and signal X positions +/-3.5 and +/-1.0.

Coordinates: origin at locating-hole midpoint on the PCB top; +X matches the
footprint, model -Y points out toward the plug, +Z above PCB. Model settings
in KiCad are zero offset/rotation and unit scale. Assigned to the library
footprint and J1 on the main board; generated panel not updated.

Approximate details: rear edge is taken as 1.0 behind the mounting datum;
this registration is not explicitly dimensioned. Shell thickness, radii,
retention windows, plastic profile, peg length, and contact geometry are
visual approximations. The drawing's 12.57 maximum width at the formed shell
features is not modeled (shell width here is 12.0); allow at least that larger
width for clearance. Internal contact paths, spring fingers and stamped
features are omitted. This is not a manufacturer model or a tooling/precise
clearance model; verify mechanical fits with a sample.

The generator validates each solid, the shell bounding box, and STEP import
validity/solid count. Module-scope `show_object` supports cq-editor.
