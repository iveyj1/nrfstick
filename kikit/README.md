# nrfstick panel build

Builds a 5 x 3 panel from `../nrfstick.kicad_pcb` with:

- 5 mm column spacing and 12 mm row spacing
- 3 mm mouse-bite tabs
- 0.5 mm holes at 0.8 mm spacing
- 10 mm top and bottom rails
- nRF module STEP models included; separately assembled USB connectors omitted

## Setup

Install Flatpak, then KiCad:

```sh
flatpak install flathub org.kicad.KiCad
```

Install KiKit into KiCad's Flatpak Python environment:

```sh
flatpak run --command=python3 org.kicad.KiCad \
  -m pip install --user kikit
```

Verify it:

```sh
flatpak run --command=python3 org.kicad.KiCad -m kikit.ui --version
```

## Build

```sh
cd kikit
./build.sh
```

Outputs are `nrfstick-panel.kicad_pcb`, `nrfstick-panel.json`,
`nrfstick-panel.png`, and the copied model `cad/fanstel_bm15c.step`. The panel
is approximately 90.1 x 115.6 mm.
