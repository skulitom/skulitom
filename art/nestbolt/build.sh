#!/usr/bin/env bash
# Nestbolt card (192x100) and its site hover burst (48 frames): Python writes the smoke and spark fluid sources and
# the recipes, Pixelbolt compiles and renders them into out/nestbolt/ and out/nestbolt-burst/, which
# nestbolt*.wrap.json use. NESTBOLT_VARIANT=burst switches the generators to the burst.
set -euo pipefail
cd "$(dirname "$0")"
. ../tools/env.sh

rm -rf out
mkdir -p out/fluids out/build out/recipes

for variant in loop burst; do
  export NESTBOLT_VARIANT=$variant
  suffix=""; [ "$variant" = burst ] && suffix="-burst"
  "$PYTHON" src/fluids.py >/dev/null
  for f in smoke sparks; do
    pb compile "out/fluids/$f$suffix.fluid.json" --out "out/build/$f$suffix.json" \
      --metadata "out/build/$f$suffix.meta.json" --force >/dev/null
  done
  "$PYTHON" src/gen.py >/dev/null
  pb render "out/recipes/nestbolt$suffix.json" --out "out/nestbolt$suffix" >/dev/null
done
unset NESTBOLT_VARIANT

echo "nestbolt: built (still frame $(tr -d '\r\n' < out/build/still.txt), burst $(tr -d '\r\n' < out/build/still-burst.txt))"
