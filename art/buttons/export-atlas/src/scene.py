"""Export Atlas tile (68x42, narrow 56x42): a little container ship on a strip of night water (the one tile without a
ledge: the water stands in for it, fading out at both ends the same way). Containers in the profile's accent colours,
a white bridge with a warm lit window whose light trails on the water, a masthead light. Once a cycle the ship powers
on: its stern churns and a wake of foam streams back behind it, its bow drops into a swell and throws spray, and the
water settles. The water is a Pixelbolt liquid simulation (FLIP): the hull is an invisible obstacle, the churn and the
bow's slam are velocity emitters, and the foam and spray are whitewater.

The view follows the ship, so the ship stays put and the sea moves past it: the wake current carries the foam back.

Frames (70 ms): 0-1 rest, 2-13 the churn, 2-16 the wake current, 6-7 the bow drops (the hull dips a pixel on 6-8),
21 the hold (the still).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from pb import rect, line, px, pxs, dither, shade, erase, fluid_frames  # noqa: E402

NAME, KIND = "export-atlas", "tile"
FRAMES = 22
VARIANTS = {"regular": (68, 42), "narrow": (56, 42)}
TITLE = "Export Atlas"
DESC = ("Pixel art made with Pixelbolt: a little container ship on a strip of night water; it powers on, its bow "
        "throws spray and a simulated wake of foam streams back behind it.")

WS = 19                                   # the fill line and the boot-top row (tile coordinates)
SURF = WS + 1                             # the row the water's surface settles on
SIM_W, SIM_H, SIM_SURF = 100, 13, 7       # the tank is wider than the tile so the wake's water has room to go
SIM_Y = WS - SIM_SURF                     # tank row 0 in tile coordinates
SHIP_LEN = 22
DIP = (6, 7, 8)                           # frames the bow drops a pixel into the swell


def layout(variant):
    """Stern x of the ship, the water strip's x range and the tank's x offset, per variant."""
    if variant == "regular":
        return 28, (11, 56), -28
    return 22, (8, 47), -34


# ---------------------------------------------------------------- the wake (a liquid simulation)
def sources():
    S, _, ox = layout("regular")
    hx0, hx1 = S - ox, S - ox + SHIP_LEN - 1          # hull in tank coordinates
    hull = []
    for y in range(SIM_H):
        row = ""
        for x in range(SIM_W):
            ty = y + SIM_Y
            inside = 15 <= ty <= WS and hx0 + (1 if ty == WS else 0) <= x <= hx1 - max(0, ty - 16)
            row += "A" if inside else "."
        hull.append(row)
    effect = {
        "kind": "liquid", "frames": FRAMES, "duration": 70, "loop": True, "seed": 3, "warmup": 3,
        "walls": ["left", "right", "bottom"], "gravity": [0, 0.35], "flip": 0.7, "drag": 0.05, "tension": 0.2,
        "obstacles": [{"symbol": "hull", "x": 0, "y": 0, "draw": "none"}],
        "fill": [{"x": 0, "y": SIM_SURF, "w": SIM_W, "h": SIM_H - SIM_SURF}],
        "emitters": [
            # The screw churns the water under the stern (down and a little back, with turbulence).
            {"name": "churn", "at": [hx0 - 3.0, SIM_SURF + 2.0], "area": [6, 3], "rate": 1, "start": 2, "end": 14,
             "density": 0, "velocity": [-1.2, 0.9], "noise": 0.9},
            {"name": "idle-churn", "at": [hx0 - 2.0, SIM_SURF + 2.0], "area": [3, 2], "rate": 0.25, "density": 0,
             "velocity": [-0.8, 1.0], "noise": 0.9},
            {"name": "idle-wake", "at": [hx0 - 19, SIM_SURF + 0.5], "area": [36, 2], "rate": 0.05, "density": 0,
             "velocity": [-1.2, 0]},
            # The bow drops into a swell: a short downward shove at the stem.
            {"name": "slam", "at": [hx1 + 1.5, SIM_SURF + 0.5], "area": [3, 2], "rate": 1, "start": 6, "end": 8,
             "density": 0, "velocity": [0.6, 3.0]},
            # Spray off the stem as it bites: droplets thrown up and forward, falling back into the sea.
            {"name": "spray", "at": [hx1 + 2.0, SIM_SURF + 0.5], "area": [3, 1], "burst": 1, "start": 7, "density": 0,
             "sparks": {"count": 10, "life": [6, 10], "colors": ["G", "F", "E", "D"], "angle": [250, 310],
                        "speed": [1.1, 1.9], "gravity": [0, 0.4], "drag": 0.02, "follow": 0}},
            # The view follows the ship: the surface behind it streams back (the wake current).
            {"name": "wake", "at": [hx0 - 19, SIM_SURF + 0.5], "area": [36, 2], "rate": 0.45, "start": 2, "end": 17,
             "density": 0, "velocity": [-2.0, 0]},
        ],
        "whitewater": [
            {"speed": 0.6, "chance": 0.75, "life": [14, 24], "colors": ["E", "E", "D", "C"], "follow": 1},
            {"impact": 0.9, "chance": 0.8, "throw": 1.1, "spread": 30, "life": [5, 9], "colors": ["G", "F", "E"]}],
        # Night water: a lit surface row, darker bands with depth, churned water a step lighter.
        "look": [
            {"field": "density", "colors": ["9"], "thresholds": [0.5], "dither": 0},
            {"field": "depth", "colors": ["Z", "W", "9", "8"], "thresholds": [1, 2, 3, 5], "dither": 0},
            {"field": "speed", "colors": ["W", "Z", "@"], "thresholds": [0.6, 1.1, 1.8], "dither": 0.5}],
        "cleanup": {"strays": True},
    }
    return {"wake": {"format": "pixelforge-fluid", "version": 1, "name": "wake", "width": SIM_W, "height": SIM_H,
                     "palette": {"$ref": "../../../../palette.json"}, "symbols": {"hull": hull},
                     "effects": {"wake": effect}}}


WAKE = None


def wake_ops(i):
    global WAKE
    if WAKE is None:
        WAKE = fluid_frames(Path(__file__).resolve().parents[1] / "out" / "build" / "wake.json", "wake")[0]
    return WAKE[i]


# ---------------------------------------------------------------- the ship (S = stern x; bow at S + 17)
CONTAINERS = [  # (x offset, row, width, colour, lit top colour, dark side colour); the stack steps down to the bow
    (7, 13, 4, "e", "f", "d"), (11, 13, 4, "V", "X", "U"), (15, 13, 4, "l", "m", "k"),
    (7, 11, 4, "P", "Q", "O"), (11, 11, 4, "r", "y", "q"), (15, 11, 3, "@", "#", "Z"),
    (7, 9, 4, "k", "l", "j"), (11, 9, 4, "e", "f", "d"),
]


def ship(S, dip):
    b = 1 if dip else 0                    # the bow's drop: the forecastle and mast sit a pixel lower
    ops = [
        # Hull: dark steel, a moonlit deck edge, the red boot-top at the waterline; the bow rakes forward.
        rect(S, 15, 20, 4, "B"), line(S + 18, 17, S + 18, 18, "B"), px(S + 19, 17, "B"),
        line(S, 15, S + 19, 15, "D"), line(S, 15, S + 6, 15, "E"),
        line(S + 1, WS, S + 18, WS, "c"), px(S, 18, "A"), px(S, 17, "A"), px(S + 19, 18, "A"),
        line(S + 1, 18, S + 17, 18, "A"),
        # Forecastle and stem (drop with the bow in the swell).
        rect(S + 18, 13 + b, 4, 3, "B"), line(S + 18, 13 + b, S + 21, 13 + b, "D"), px(S + 21, 14 + b, "C"),
        px(S + 20, 16 + b, "B"), px(S + 21, 15 + b, "A"),
        # Bridge at the stern: white, its moonlit left edge, a window row with one warm lit window, the wings above.
        rect(S + 1, 9, 5, 6, "E"), line(S + 1, 9, S + 1, 14, "F"), line(S + 5, 10, S + 5, 14, "D"),
        line(S + 1, 11, S + 5, 11, "A"), px(S + 3, 11, "Q"), px(S + 2, 11, "B"),
        line(S, 8, S + 6, 8, "F"), px(S + 6, 8, "D"), px(S, 8, "G"),
        # Funnel: molten, lit on its left, a dark top.
        rect(S + 2, 5, 2, 3, "d"), line(S + 2, 6, S + 2, 7, "e"), line(S + 2, 5, S + 3, 5, "a"),
        # Mast and masthead light at the bow.
        line(S + 20, 9 + b, S + 20, 12 + b, "C"), px(S + 20, 8 + b, "G"),
    ]
    for dx, row, w, c, lit, dark in CONTAINERS:
        x = S + dx
        ops += [rect(x, row, w, 2, c), line(x, row, x + w - 1, row, lit), px(x + w - 1, row + 1, dark)]
    # Dark seams between the boxes so each container reads.
    ops += [line(S + 11, 9, S + 11, 14, "A"), line(S + 15, 11, S + 15, 14, "A"), line(S + 6, 9, S + 6, 14, "A")]
    return ops


def crop(o, w):
    """Trim a compiled fluid grid to the tile's columns (the tank is wider than the tile), so nothing is drawn off the
    canvas. Only which columns of Pixelbolt's own grid are kept changes; no pixel does."""
    if o.get("op") != "grid" or o.get("scale", 1) != 1:
        return o
    a = max(0, -o["x"])
    b = min(len(o["rows"][0]), w - o["x"])
    return dict(o, x=o["x"] + a, rows=[r[a:b] for r in o["rows"]])


FOAM = [(-3, 3, "E"), (-7, 3, "D"), (-12, 2, "D"), (-16, 2, "C"), (-19, 1, "C")]   # (x from the stern, length, colour)
WATER = ["Z", "W", "9", "@", "#", "D", "C"]


def foam_trail(S):
    """Foam on the surface behind the stern: clumps over the water colours only, so they ride the simulated surface."""
    ops = [dither(S + dx, SURF, n, 1, c, 1.0, over=WATER) for dx, n, c in FOAM]
    return ops + [dither(S - 6, SURF + 1, 2, 1, "C", 1.0, over=WATER)]


def water(i, S, x0, x1, ox, w):
    """The wake layer: the simulation, the bridge window's warm light trailing on the surface, the masthead light's
    glint, and the strip's ends feathered out."""
    ops = [rect(x0, SURF, x1 - x0 + 1, 1, "W"), rect(x0, SURF + 1, x1 - x0 + 1, 3, "9")]
    ops += [crop(dict(o, x=o["x"] + ox, y=o["y"] + SIM_Y), w) for o in wake_ops(i)]
    # The water settles a row below the fill line, so the visible surface is row SURF. Reflections stretch down the
    # water: the warm bridge window and the masthead light; moon glints ride the surface ahead of the bow.
    ops += [dither(S + 3, SURF, 1, 1, "O", 1.0, over=["Z", "W", "9"]), dither(S + 3, SURF + 1, 1, 2, "N", 0.5, over=["W", "9", "8"]),
            dither(S + 20, SURF, 1, 2, "C", 0.5, over=["Z", "W", "9"]),
            dither(S + 23, SURF, 8, 1, "D", 0.25, over=["Z"]),
            # The wake's foam trail on the surface behind the stern, thinning away from it. The view follows the ship,
            # so the trail stays with it; the dither is limited to the simulated surface colours, so it rides the water.
            ] + foam_trail(S)
    ops += [dither(x0, SURF, x1 - x0 + 1, 1, "@", 0.3, pattern="value", scale=3, seed=11, over=["Z"]),
            dither(x0, SURF, x1 - x0 + 1, 1, "W", 0.2, pattern="value", scale=2, seed=29, over=["Z"]),
            dither(x0, SURF + 1, x1 - x0 + 1, 1, "Z", 0.15, pattern="value", scale=3, seed=5, over=["W"]),
            px(S + 1, WS, "Z"), px(S + 2, WS, "W"), px(S + 18, WS, "Z"), px(S + 17, WS, "W")]
    ops += [erase(max(0, x0 - 20), SIM_Y, x0 - max(0, x0 - 20), SIM_H, 1.0), erase(x1 + 1, SIM_Y, w - x1 - 1, SIM_H, 1.0),
            shade(x0, SIM_Y, 4, SIM_H, -1), shade(x0, SIM_Y, 2, SIM_H, -1),
            shade(x1 - 3, SIM_Y, 4, SIM_H, -1), shade(x1 - 1, SIM_Y, 2, SIM_H, -1),
            erase(x0, SIM_Y, 6, SURF - SIM_Y, 1.0), erase(x1 - 5, SIM_Y, 6, SURF - SIM_Y, 1.0),
            erase(x0, SURF + 4, x1 - x0 + 1, 2, [0.35, 0.9], direction="down", pattern="value", scale=3, seed=3),
            dither(x0, SURF + 4, x1 - x0 + 1, 2, "8", 1.0, over=["W", "9", "Z", "@", "#"])]
    return ops


def frame_ops(i, variant):
    w = VARIANTS[variant][0]
    S, (x0, x1), ox = layout(variant)
    layers = [{"name": "ship", "ops": ship(S, i in DIP)},
              {"name": "sea", "ops": water(i, S, x0, x1, ox, w)}]
    return {"ops": [rect(0, 0, w, 42, "2")], "layers": layers}
