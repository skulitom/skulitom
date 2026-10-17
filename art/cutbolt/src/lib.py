"""Op helpers for the Cutbolt card recipes.

Python only lays out Pixelbolt drawing operations here (shapes, lines, hand-placed pixels, dither and shade regions).
Every effect pixel (dither, shade, outline, fluid) is computed by Pixelbolt when the recipe renders.
"""

import os
from pathlib import Path

DIRECTION = Path(__file__).resolve().parents[2]  # art/, which holds palette.json


def palette_for(recipe_dir):
    """Shared palette reference relative to the folder the recipe is written to."""
    rel = os.path.relpath(DIRECTION / "palette.json", Path(recipe_dir).resolve())
    return {"$ref": rel.replace(os.sep, "/")}

# Recipe ramps. The wall's night colours continue into the pink ramp, so shade bands round the safelight turn the wall
# (and the film's dim night-coloured perforations) pink band by band; 5-7 are their own ramp.
RAMPS = [
    ["0", "1", "2", "3", "4", "S", "T", "U", "V", "X", "Y"],
    ["5", "6", "7"],
    ["s", "t", "u", "v", "w", "x"],
    ["A", "B", "C", "D", "E", "F", "G"],
    ["H", "I", "J", "K", "L", "M"],
    ["N", "O", "P", "Q", "R"],
    ["a", "b", "c", "d", "e", "f", "g"],
    ["h", "i", "j", "k", "l", "m", "n"],
    ["o", "p", "q", "r", "y", "z"],
    ["8", "9", "W", "Z", "@", "#", "$"],
    ["%", "&", "+", "="],
]


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


def grid(x, y, rows, **kw):
    o = {"op": "grid", "x": x, "y": y, "rows": rows}
    o.update(kw)
    return o


def clear(x, y, w, h):
    return {"op": "clear", "x": x, "y": y, "w": w, "h": h}


def text(x, y, s, c, **kw):
    o = {"op": "text", "x": x, "y": y, "text": s, "color": c}
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
