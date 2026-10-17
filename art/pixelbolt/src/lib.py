"""Small helpers that write Pixelbolt drawing operations. Python only lays out ops; Pixelbolt draws every pixel."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "out" / "build"
PB = os.environ.get("PIXELBOLT", "")  # path to pixelbolt.js; art/build.sh sets it


def rect(x, y, w, h, c, filled=True):
    o = {"op": "rect", "x": x, "y": y, "w": w, "h": h, "color": c}
    if not filled:
        o["filled"] = False
    return o


def ell(x, y, w, h, c, filled=True):
    o = {"op": "ellipse", "x": x, "y": y, "w": w, "h": h, "color": c}
    if not filled:
        o["filled"] = False
    return o


def line(x, y, x2, y2, c):
    return {"op": "line", "x": x, "y": y, "x2": x2, "y2": y2, "color": c}


def hline(x, x2, y, c):
    return line(x, y, x2, y, c)


def vline(x, y, y2, c):
    return line(x, y, x, y2, c)


def px(x, y, c):
    return {"op": "pixel", "x": x, "y": y, "color": c}


def grid(x, y, rows, **kw):
    o = {"op": "grid", "x": x, "y": y, "rows": rows}
    o.update(kw)
    return o


def stamp(x, y, symbol, **kw):
    o = {"op": "stamp", "x": x, "y": y, "symbol": symbol}
    o.update(kw)
    return o


def dither(x, y, w, h, c, density, **kw):
    o = {"op": "dither", "x": x, "y": y, "w": w, "h": h, "color": c, "density": density}
    o.update(kw)
    return o


def shade(x, y, w, h, steps, **kw):
    o = {"op": "shade", "x": x, "y": y, "w": w, "h": h, "steps": steps}
    o.update(kw)
    return o


def text(x, y, s, c, **kw):
    o = {"op": "text", "x": x, "y": y, "text": s, "color": c}
    o.update(kw)
    return o


def outline(c, **kw):
    o = {"op": "outline", "color": c}
    o.update(kw)
    return o


def at(ops, dx, dy):
    """Move ops that have x/y (grids from compiled fluids, shapes) by dx, dy."""
    out = []
    for o in ops:
        o = dict(o)
        if "x" in o:
            o["x"] += dx
        if "y" in o:
            o["y"] += dy
        if "x2" in o:
            o["x2"] += dx
        if "y2" in o:
            o["y2"] += dy
        out.append(o)
    return out


def compiled_frames(path, effect):
    recipe = json.loads(Path(path).read_text(encoding="utf-8"))
    return [f.get("ops", []) for f in recipe["frames"] if f["name"].rsplit("-", 1)[0] == effect], recipe.get("symbols", {})


def write_json(path, obj, compact=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        s = json.dumps(obj, separators=(",", ":"))
    else:
        s = json.dumps(obj, indent=1)
    path.write_text(s + "\n", encoding="utf-8", newline="\n")
