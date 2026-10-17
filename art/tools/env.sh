# Shared setup for the piece build scripts (sourced, not run): the art/ root, Pixelbolt, Python and a `pb` helper.
# art/build.sh exports all of this; a piece's build.sh can also be run on its own with PIXELBOLT set.

ART="${ART:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export ART
: "${PIXELBOLT:?set PIXELBOLT to the path of bin/pixelbolt.js in a Pixelbolt checkout (art/build.sh fetches one when it is unset)}"
export PIXELBOLT

# The first Python 3.11+ on PATH, preferring one with Pillow (only tools/integrate.py needs Pillow).
if [ -z "${PYTHON:-}" ]; then
  for want in "import PIL" ""; do
    for candidate in python python3; do
      if command -v "$candidate" >/dev/null 2>&1 &&
         "$candidate" -c "import sys; assert sys.version_info >= (3, 11); $want" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break 2
      fi
    done
  done
fi
: "${PYTHON:?need Python 3.11+ on PATH (or set PYTHON)}"
export PYTHON
export PYTHONDONTWRITEBYTECODE=1   # keep src/ free of __pycache__

pb() { node "$PIXELBOLT" "$@"; }
