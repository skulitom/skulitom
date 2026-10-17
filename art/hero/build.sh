#!/usr/bin/env bash
# Hero set: the desktop hero (416x162, two 208x162 halves, 96 frames), the phone hero (156x180) and the footer
# (416x42, 48 frames). Python writes the fluid sources and recipes, Pixelbolt compiles and renders them.
# Everything generated lands in out/: fluids/ (fluid sources), build/ (compiled fluids, layouts), recipes/, and one
# render bundle per recipe (out/<name>/<name>.png + .atlas.json + frames/), which the *.wrap.json specs here use.
set -euo pipefail
cd "$(dirname "$0")"
. ../tools/env.sh

rm -rf out
mkdir -p out/fluids out/build out/recipes

# ---- desktop hero: flask boil, steam, drip and clouds
"$PYTHON" src/fluids.py >/dev/null
for f in flask steam drip clouds; do
  pb compile "out/fluids/$f.fluid.json" --out "out/build/$f.json" --metadata "out/build/$f.meta.json" --force >/dev/null
done
"$PYTHON" src/gen.py >/dev/null
for r in hero-left-bg hero-right-bg hero-left-fx hero-right-fx; do
  pb render "out/recipes/$r.json" --out "out/$r" >/dev/null
done

# ---- phone hero: the desktop's flask and drip, its own steam
"$PYTHON" src/phone.py source
pb compile out/fluids/phone-steam.fluid.json --out out/build/phone-steam.json \
  --metadata out/build/phone-steam.meta.json --force >/dev/null
"$PYTHON" src/phone.py >/dev/null
for r in hero-mobile-bg hero-mobile-fx; do
  pb render "out/recipes/$r.json" --out "out/$r" >/dev/null
done

# ---- footer: drop-into-dish and wisp sims
"$PYTHON" src/footer.py source
for f in footer-drop footer-wisp; do
  pb compile "out/fluids/$f.fluid.json" --out "out/build/$f.json" --metadata "out/build/$f.meta.json" --force >/dev/null
done
"$PYTHON" src/footer.py >/dev/null
for r in footer-left-bg footer-right-bg footer-right-fx; do
  pb render "out/recipes/$r.json" --out "out/$r" >/dev/null
done

echo "hero: built (still frame $(tr -d '\r\n' < out/build/still.txt))"
