#!/usr/bin/env bash
# Anode card (192x100, 72 frames) and its site hover burst (48 frames): Python writes the fog and wisp fluid sources
# (out/build/*.fluid.json) and the two recipes, Pixelbolt compiles and renders them into out/anode/ and
# out/anode-burst/, which anode*.wrap.json use.
set -euo pipefail
cd "$(dirname "$0")"
. ../tools/env.sh

rm -rf out
mkdir -p out/build out/recipes

"$PYTHON" src/fluids.py >/dev/null
for f in fog wisps fog-burst wisps-burst; do
  pb compile "out/build/$f.fluid.json" --out "out/build/$f.json" --metadata "out/build/$f.meta.json" --force >/dev/null
done
"$PYTHON" src/gen.py >/dev/null

pb render out/recipes/anode.json --out out/anode >/dev/null
pb render out/recipes/anode-burst.json --out out/anode-burst >/dev/null

echo "anode: built (still frame $(tr -d '\r\n' < out/build/still.txt))"
