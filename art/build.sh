#!/usr/bin/env bash
# Rebuild the profile README's pixel art (../assets/v4/*.svg) from the sources in this folder.
#
# Requirements: Node 20+, Python 3.11+ with Pillow, Git Bash on Windows (any bash elsewhere), and git when PIXELBOLT
# is unset. Pixelbolt itself has no dependencies.
#
#   bash art/build.sh                                            # fetches Pixelbolt 8c5f662 into art/.pixelbolt
#   PIXELBOLT=/path/to/Pixelbolt/bin/pixelbolt.js bash art/build.sh   # or use a checkout you already have
#   PYTHON=python3.13 bash art/build.sh                          # pick the Python (default: python, then python3)
#
# Builds every piece into art/<piece>/out/ (generated, gitignored), then runs tools/integrate.py, which writes
# ../assets/v4/<name>.svg and <name>-still.svg from each piece's *.wrap.json. See NOTES.txt.
set -euo pipefail
ART="$(cd "$(dirname "$0")" && pwd)"
export ART

PIXELBOLT_REPO="${PIXELBOLT_REPO:-https://github.com/skulitom/Pixelbolt}"
PIXELBOLT_COMMIT=8c5f662afa8a6e3191b3b895b567b575d11c55cb   # 8c5f662: the Pixelbolt the art was made and checked with

if [ -z "${PIXELBOLT:-}" ]; then
  dir="$ART/.pixelbolt"
  if [ ! -f "$dir/.git/HEAD" ] || [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" != "$PIXELBOLT_COMMIT" ]; then
    echo "fetching Pixelbolt ${PIXELBOLT_COMMIT:0:7} into $dir"
    rm -rf "$dir"
    git init -q "$dir"
    git -C "$dir" config core.autocrlf false
    git -C "$dir" remote add origin "$PIXELBOLT_REPO"
    # Shallow: just that commit. A server that refuses fetching by commit id gets a full fetch instead.
    git -C "$dir" fetch -q --depth 1 origin "$PIXELBOLT_COMMIT" || git -C "$dir" fetch -q origin
    git -C "$dir" -c advice.detachedHead=false checkout -q "$PIXELBOLT_COMMIT"
  fi
  PIXELBOLT="$dir/bin/pixelbolt.js"
fi
export PIXELBOLT

. "$ART/tools/env.sh"
node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)' ||
  { echo "need Node 20+ (found $(node --version))" >&2; exit 1; }
"$PYTHON" -c "import PIL" 2>/dev/null || { echo "need Pillow for $PYTHON (pip install Pillow)" >&2; exit 1; }

# Pieces in build order. A new piece (the button set, say) is a folder with its own build.sh that sources
# tools/env.sh and writes only to its out/: add its name here and its wrap specs to tools/integrate.py.
PIECES=(hero anode inkbolt cutbolt pixelbolt nestbolt)
for piece in "${PIECES[@]}"; do
  "$BASH" "$ART/$piece/build.sh"
done

"$PYTHON" "$ART/tools/integrate.py"
