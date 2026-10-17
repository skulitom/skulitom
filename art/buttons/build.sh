#!/usr/bin/env bash
# The profile's link buttons: the portfolio button (140x32) and six tiles, each a regular (68x42) and a narrow (56x42)
# variant, 22 frames over a 24,000 ms cycle. Per button, src/scene.py lays out the scene and lib/button.py (run from
# the button's folder) writes its fluid sources and recipes; Pixelbolt compiles and renders them. Everything generated
# lands in <button>/out/: fluids/, build/ (compiled fluids), recipes/ (with -review recipes, unused here) and one
# render bundle per variant (out/<name>/<name>.png + .atlas.json), which <button>/*.wrap.json use.
set -euo pipefail
cd "$(dirname "$0")"
. ../tools/env.sh

BUTTONS=(portfolio world-language-map export-atlas london-in-minutes chinese-touch-typing chinese-radicals keepsake)
for b in "${BUTTONS[@]}"; do
  (
    cd "$b"
    rm -rf out
    mkdir -p out/fluids out/build out/recipes
    "$PYTHON" ../lib/button.py sources >/dev/null
    for f in out/fluids/*.fluid.json; do
      [ -e "$f" ] || continue
      stem=$(basename "$f" .fluid.json)
      pb compile "$f" --out "out/build/$stem.json" --metadata "out/build/$stem.meta.json" --force >/dev/null
    done
    "$PYTHON" ../lib/button.py recipes >/dev/null
    for r in out/recipes/*.json; do
      name=$(basename "$r" .json)
      case "$name" in *-review) continue ;; esac
      pb render "$r" --out "out/$name" >/dev/null
    done
  )
done

echo "buttons: built ${#BUTTONS[@]}"
