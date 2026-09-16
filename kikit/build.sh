#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/../nrfstick.kicad_pcb"
PANEL="$SCRIPT_DIR/nrfstick-panel.kicad_pcb"
CONFIG="$SCRIPT_DIR/nrfstick-panel.json"
PREVIEW="$SCRIPT_DIR/nrfstick-panel.png"
NRF_MODEL_SOURCE="$SCRIPT_DIR/../cad/fanstel_bm15c.step"
NRF_MODEL="$SCRIPT_DIR/cad/fanstel_bm15c.step"
KICAD_APP="org.kicad.KiCad"

command -v flatpak >/dev/null 2>&1 || {
    echo "error: flatpak is not installed" >&2
    exit 1
}
flatpak info "$KICAD_APP" >/dev/null 2>&1 || {
    echo "error: $KICAD_APP is not installed" >&2
    exit 1
}
[[ -f "$SOURCE" ]] || {
    echo "error: source PCB not found: $SOURCE" >&2
    exit 1
}
[[ -f "$NRF_MODEL_SOURCE" ]] || {
    echo "error: nRF STEP model not found: $NRF_MODEL_SOURCE" >&2
    exit 1
}
flatpak run --command=python3 "$KICAD_APP" -m kikit.ui --version >/dev/null 2>&1 || {
    echo "error: KiKit is not installed in the KiCad Flatpak; see README.md" >&2
    exit 1
}

# The panel's ${KIPRJMOD} is this directory, so copy only the populated model.
mkdir -p "$(dirname -- "$NRF_MODEL")"
cp "$NRF_MODEL_SOURCE" "$NRF_MODEL"

flatpak run --command=python3 "$KICAD_APP" -m kikit.ui panelize \
    --layout 'grid; cols: 5; rows: 3; hspace: 2mm; vspace: 6mm' \
    --tabs 'spacing; width: 3mm; spacing: 10mm' \
    --cuts 'mousebites; drill: 0.5mm; spacing: 0.8mm' \
    --framing 'railstb; width: 10mm' \
    --dump "$CONFIG" \
    "$SOURCE" "$PANEL"

# U5 is populated before panel separation; J1 is assembled separately.
flatpak run --command=python3 "$KICAD_APP" \
    "$SCRIPT_DIR/prepare_3d.py" "$PANEL"

flatpak run --command=kicad-cli "$KICAD_APP" pcb render \
    --output "$PREVIEW" --width 1600 --height 1400 "$PANEL"

echo "Built: $PANEL"
echo "Config: $CONFIG"
echo "Preview: $PREVIEW"
