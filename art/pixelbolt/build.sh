#!/usr/bin/env bash
# Pixelbolt card (192x100, 72 frames): Python writes the pour, smoke, dust and ember fluid sources, the crucible's
# pose source and the recipe; Pixelbolt compiles and renders them into out/pixelbolt-card/. The reduced-motion still
# is Pixelbolt's own frame PNG, copied to out/pixelbolt-card-still-1x.png. Both are used by pixelbolt-card*.wrap.json.
# (The site's hover burst has no wrap spec, so it is not built. See NOTES.txt.)
set -euo pipefail
cd "$(dirname "$0")"
. ../tools/env.sh

rm -rf out
mkdir -p out/fluids out/build out/recipes

"$PYTHON" src/fluids.py >/dev/null
"$PYTHON" src/poses.py >/dev/null
for f in pour smoke dust embers; do
  pb compile "out/fluids/$f.fluid.json" --out "out/build/$f.json" --metadata "out/build/$f.meta.json" --force >/dev/null
done
pb compile out/fluids/crucible.poses.json --out out/build/crucible.json --metadata out/build/crucible.meta.json \
  --force >/dev/null
"$PYTHON" src/gen.py >/dev/null
pb render out/recipes/pixelbolt-card.json --out out/pixelbolt-card >/dev/null

STILL=$("$PYTHON" -c "import sys; sys.path.insert(0, 'src'); import design; print(design.STILL)")
cp "out/pixelbolt-card/frames/loop-$STILL.png" out/pixelbolt-card-still-1x.png

echo "pixelbolt: built (still frame loop-$STILL)"
