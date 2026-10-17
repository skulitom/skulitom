#!/usr/bin/env bash
# Inkbolt card (192x100, 72 frames) and its site hover burst (48 frames): Python writes the plume and drop fluid
# sources and the recipes, Pixelbolt compiles and renders them into out/inkbolt/ and out/inkbolt-burst/, which
# inkbolt*.wrap.json use.
set -euo pipefail
cd "$(dirname "$0")"
. ../tools/env.sh

rm -rf out
mkdir -p out/fluids out/build out/recipes

"$PYTHON" src/fluids.py >/dev/null
for f in plume drop; do
  pb compile "out/fluids/$f.fluid.json" --out "out/build/$f.json" --metadata "out/build/$f.meta.json" --force >/dev/null
done
"$PYTHON" src/gen.py >/dev/null
pb render out/recipes/inkbolt.json --out out/inkbolt >/dev/null

# The hover burst: two drops, colliding rings.
"$PYTHON" src/burst.py fluids >/dev/null
for f in burst-plume burst-drop; do
  pb compile "out/fluids/$f.fluid.json" --out "out/build/$f.json" --metadata "out/build/$f.meta.json" --force >/dev/null
done
"$PYTHON" src/burst.py recipe >/dev/null
pb render out/recipes/inkbolt-burst.json --out out/inkbolt-burst >/dev/null

echo "inkbolt: built (still frame $(tr -d '\r\n' < out/build/still.txt))"
