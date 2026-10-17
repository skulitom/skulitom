#!/usr/bin/env bash
# Cutbolt card (192x100): Python writes the developer-tray fluid source and the recipe, Pixelbolt compiles and renders
# them into out/cutbolt/, which cutbolt*.wrap.json use. (src/fluids.py also writes the hover burst's tray-burst
# source; the burst has no wrap spec, so it is not built. See NOTES.txt.)
set -euo pipefail
cd "$(dirname "$0")"
. ../tools/env.sh

rm -rf out
mkdir -p out/fluids out/build out/recipes

"$PYTHON" src/fluids.py >/dev/null
pb compile out/fluids/tray.fluid.json --out out/build/tray.json --metadata out/build/tray.meta.json --force >/dev/null
"$PYTHON" src/gen.py >/dev/null
pb render out/recipes/cutbolt.json --out out/cutbolt >/dev/null

echo "cutbolt: built (still frame $(tr -d '\r\n' < out/build/still.txt))"
