"""Shared helpers for the profile's link buttons: Pixelbolt operation builders, the house glow, recipe writing.

Python only lays out drawing operations (shapes, lines, hand-placed pixels, grids of hand-drawn symbols, dither and
shade regions) and places compiled fluid frames as layers. Every dither, shade band, outline and fluid pixel is made by
Pixelbolt when the recipe renders.
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # art/buttons
# art/, which holds the master palette.
ART = Path(__file__).resolve().parents[2]
PALETTE_FILE = ART / "palette.json"
MS = 70
CYCLE = 24000

# Recipe ramps: the shared ramps, with night split so glows can be written as explicit dither rings.
RAMPS = [
    ["0", "1", "2", "3", "4", "5", "6", "7"],
    ["s", "t", "u", "v", "w", "x"],
    ["A", "B", "C", "D", "E", "F", "G"],
    ["H", "I", "J", "K", "L", "M"],
    ["N", "O", "P", "Q", "R"],
    ["a", "b", "c", "d", "e", "f", "g"],
    ["h", "i", "j", "k", "l", "m", "n"],
    ["o", "p", "q", "r", "y", "z"],
    ["S", "T", "U", "V", "X", "Y"],
    ["8", "9", "W", "Z", "@", "#", "$"],
    ["%", "&", "+", "="],
]


def palette_ref(recipe_dir):
    """A relative $ref from a recipe folder to the master palette."""
    import os
    return {"$ref": os.path.relpath(PALETTE_FILE, recipe_dir).replace("\\", "/")}


# ---------------------------------------------------------------- op builders
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


def px(x, y, c):
    return {"op": "pixel", "x": x, "y": y, "color": c}


def pxs(points, c):
    return [px(x, y, c) for x, y in points]


def grid(x, y, rows, **kw):
    o = {"op": "grid", "x": x, "y": y, "rows": rows}
    o.update(kw)
    return o


def stamp(x, y, symbol, **kw):
    o = {"op": "stamp", "x": x, "y": y, "symbol": symbol}
    o.update(kw)
    return o


def text(x, y, s, c, **kw):
    o = {"op": "text", "x": x, "y": y, "text": s, "color": c}
    o.update(kw)
    return o


def dither(x, y, w, h, c, density, **kw):
    o = {"op": "dither", "x": x, "y": y, "w": w, "h": h, "color": c, "density": density}
    o.update(kw)
    return o


def erase(x, y, w, h, density, **kw):
    o = {"op": "dither", "x": x, "y": y, "w": w, "h": h, "erase": True, "density": density}
    o.update(kw)
    return o


def shade(x, y, w, h, steps, **kw):
    o = {"op": "shade", "x": x, "y": y, "w": w, "h": h, "steps": steps}
    o.update(kw)
    return o


def outline(c, **kw):
    o = {"op": "outline", "color": c}
    o.update(kw)
    return o


def replace(a, b):
    return {"op": "replace", "from": a, "to": b}


def clear(x, y, w, h):
    return {"op": "clear", "x": x, "y": y, "w": w, "h": h}


def flat(ops):
    """Flatten nested lists of operations."""
    out = []
    for o in ops:
        if isinstance(o, list):
            out += flat(o)
        else:
            out.append(o)
    return out


def shift(ops, dx, dy=0):
    """Move operations by (dx, dy)."""
    out = []
    for o in flat(ops):
        o = dict(o)
        if "x" in o:
            o["x"] += dx
        if "x2" in o:
            o["x2"] += dx
        if "y" in o:
            o["y"] += dy
        if "y2" in o:
            o["y2"] += dy
        out.append(o)
    return out


# ---------------------------------------------------------------- the house glow
def disc_rows(cx, cy, r, c, density, over=None, half=None, rx=None, **kw):
    """A disc (or ellipse with rx) of dither centred on (cx, cy), one dither row per pixel row: solid bands with Bayer
    feathers, limited to the listed colours. half='top' keeps only the rows above the centre."""
    rx = r if rx is None else rx
    ops = []
    for y in range(math.floor(cy - r), math.ceil(cy + r) + 1):
        dy = y + 0.5 - cy
        if abs(dy) > r or (half == "top" and dy > 0) or (half == "bottom" and dy < 0):
            continue
        hw = rx * math.sqrt(max(0.0, 1 - (dy / r) ** 2))
        x0, x1 = math.ceil(cx - hw - 0.5), math.floor(cx + hw - 0.5)
        if x1 >= x0:
            o = dither(x0, y, x1 - x0 + 1, 1, c, density, **kw)
            if over:
                o["over"] = over
            ops.append(o)
    return ops


def glow(cx, cy, rings, over, rx_scale=1.0):
    """Two or three dithered ramp rings (Bayer 4) from the outside in: rings = [(radius, colour, density), ...]."""
    ops = []
    for r, c, d in rings:
        ops += disc_rows(cx, cy, r, c, d, over=over, rx=r * rx_scale)
    return ops


# ---------------------------------------------------------------- recipes
def recipe(name, w, h, frames, recipe_dir, animations=None, symbols=None, ramps=None, sheet=None):
    rec = {"version": 1, "name": name, "width": w, "height": h, "palette": palette_ref(recipe_dir),
           "ramps": ramps or RAMPS}
    if symbols:
        rec["symbols"] = symbols
    rec["frames"] = frames
    if animations:
        rec["animations"] = animations
    if sheet:
        rec["sheet"] = sheet
    return rec


def write_json(path, obj, compact=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text_ = json.dumps(obj, separators=(",", ":")) if compact else json.dumps(obj, indent=1)
    path.write_text(text_ + "\n", encoding="utf-8", newline="\n")


def fluid_frames(path, effect):
    """The ops of each compiled fluid frame of one effect, in order."""
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    frames = [f for f in rec["frames"] if f["name"].rsplit("-", 1)[0] == effect]
    frames.sort(key=lambda f: int(f["name"].rsplit("-", 1)[1]))
    return [f.get("ops", []) for f in frames], rec.get("symbols", {})


def ease(t):
    """Smoothstep ease in-out on 0..1."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
