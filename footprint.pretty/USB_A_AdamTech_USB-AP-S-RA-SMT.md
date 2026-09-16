# Adam Tech USB-AP-S-RA-SMT

Source: `data/usb-ap-s-ra-smt-data-sheet.pdf`, drawing S00167-T-1, revision J.
All dimensions in mm. Origin is the midpoint of the locating holes; plug points toward +Y.

- Signal pad centers: X = +3.5, +1.0, -1.0, -3.5 for pins 1–4; Y = -3.1.
- Signal lands: 1.2 x 3.0. Near edge is 1.6 from the locating-hole centerline.
- Locating holes: diameter 1.1, at X = +/-2.25, Y = 0.
- Shield slots: 1.0 x 2.5, at X = +/-5.7, Y = 0; copper ovals 1.6 x 4.0.
  The drawing's 1.60 dimension is NOT the slot length; it locates the signal land edge.
- USB pin numbering retained from J1: 1 VBUS, 2 D-, 3 D+, 4 GND; SH shield.
- Dwgs.User shell outline is nominal 12.0 x 18.8, with rear edge at Y = -1;
  rear-edge registration is approximate. Courtyard conservatively encloses the shell and lands.
- 3D model: `cad/adamtech_usb_ap_s_ra_smt.step`, zero offset/rotation, unit scale.
  See `cad/adamtech_usb_ap_s_ra_smt.md` for visualization approximations.

J1's board position and nets are retained. The larger lands overlap existing nearby routing/components;
placement/routing changes and a clean DRC are required before fabrication. The generated KiKit panel
has not been regenerated.
