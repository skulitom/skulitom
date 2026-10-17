"""Small helpers that write Pixelbolt drawing operations as JSON dicts.

Python only lays out geometry and timing here. Every pixel is drawn by Pixelbolt when the recipe renders.
"""

PALETTE = {"$ref": "../../../palette.json"}          # for out/recipes/*.json
FLUID_PALETTE = {"$ref": "../../../palette.json"}  # for out/fluids/*.fluid.json

# Recipe ramps (keys from dark to light). The plywood's ramp carries on into molten f, g and brass R, so the cut's
# light pool shades the wood up through orange to white-yellow band by band; night and steel stay apart.
RAMPS = [
    ["0", "1", "2", "3", "4", "5", "6", "7"],
    ["s", "t", "u", "v", "w", "x"],
    ["A", "B", "C", "D", "E", "F", "G"],
    ["H", "I", "J", "K", "L", "M", "f", "g", "R"],
    ["N", "O", "P", "Q"],
    ["a", "b", "c", "d", "e"],
    ["h", "i", "j", "k", "l", "m", "n"],
    ["o", "p", "q", "r", "y", "z"],
    ["S", "T", "U", "V", "X", "Y"],
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


def stamp(x, y, symbol, **kw):
    o = {"op": "stamp", "x": x, "y": y, "symbol": symbol}
    o.update(kw)
    return o


def dither(x, y, w, h, c, density, **kw):
    o = {"op": "dither", "x": x, "y": y, "w": w, "h": h, "color": c, "density": density}
    o.update(kw)
    return o


def shade(x, y, w, h, steps=-1, **kw):
    o = {"op": "shade", "x": x, "y": y, "w": w, "h": h, "steps": steps}
    o.update(kw)
    return o


def fill(x, y, c):
    return {"op": "fill", "x": x, "y": y, "color": c}


def replace(a, b):
    return {"op": "replace", "from": a, "to": b}


def copy(frame, x, y, **kw):
    o = {"op": "copy", "from": frame, "x": x, "y": y}
    o.update(kw)
    return o


def outline(c, **kw):
    o = {"op": "outline", "color": c}
    o.update(kw)
    return o


def polyline(points, c):
    """Lines between consecutive points; shared end points are simply drawn twice."""
    return [line(a[0], a[1], b[0], b[1], c) for a, b in zip(points, points[1:])]


def shift(ops, dx, dy=0):
    """Move ops by (dx, dy), carrying Bayer/noise pattern offsets so dithers travel with the drawing."""
    out = []
    for o in ops:
        o = dict(o)
        if "x" in o:
            o["x"] += dx
        if "x2" in o:
            o["x2"] += dx
        if "y" in o:
            o["y"] += dy
        if "y2" in o:
            o["y2"] += dy
        if o.get("op") in ("dither", "shade"):
            ox, oy = o.get("offset", [0, 0])
            o["offset"] = [ox - dx, oy - dy]
        out.append(o)
    return out
