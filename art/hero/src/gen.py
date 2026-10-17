"""Generate the desktop hero's recipes: a still background and a 96-frame effects layer for each 208x162 half.

hero-left-bg / hero-right-bg   one frame each: wall, window, moonlight, bench, apparatus (everything that never moves)
hero-left-fx                   24x104 at full (184, 16): the left pane's clouds under its transom, one mote
hero-right-fx                  208x130 at full (208, 0): clouds, steam, boiling flask, drip, flame, the four tools'
                               idle motions, motes, a star; drawn on transparent, stacked on the background

Python lays out the drawing operations (shapes, lines, hand-chosen pixels, dither/shade regions) and places the
compiled fluid frames as layers. It never computes an effect pixel: every dither, shade band, outline and fluid pixel is
produced by Pixelbolt when the recipe renders.

The wall, window and bench are authored once in full-width coordinates (416x162) and emitted into each half with an x
shift; Bayer patterns line up across the seam because 208 is a multiple of 8. The apparatus is authored in right-half
coordinates.
"""

import json
import math
from pathlib import Path

import fluids

HERE = Path(__file__).parent
ROOT = HERE.parent
BUILD = ROOT / "out" / "build"
RECIPES = ROOT / "out" / "recipes"
W, H, HALF = 416, 162, 208
R = HALF
FRAMES, MS = fluids.FRAMES, fluids.MS
# The surge has crested, the biggest billow is leaving the neck lit mint from below, big bubbles break the surface and
# the next drop hangs swollen at the coil tip.
STILL = 50

PALETTE = {"$ref": "../../../palette.json"}
# Recipe ramps. The wall's night colours continue into the mint ramp, so shade bands round the flask turn the wall
# teal band by band; 3-7 are their own ramp, so moonlight (drawn as night 4/5 dither) never turns teal.
RAMPS = [
    ["0", "1", "2", "h", "i", "j", "k", "l", "m", "n"],
    ["3", "4", "5", "6", "7"],
    ["s", "t", "u", "v", "w", "x"],
    ["A", "B", "C", "D", "E", "F", "G"],
    ["H", "I", "J", "K", "L", "M"],
    ["N", "O", "P", "Q", "R"],
    ["a", "b", "c", "d", "e", "f", "g"],
    ["o", "p", "q", "r", "y", "z"],
    ["S", "T", "U", "V", "X", "Y"],
    ["8", "9", "W", "Z", "@", "#", "$"],
    ["%", "&", "+", "="],
]

# Effects layers: where each sits (full coordinates) and its size.
LFX = (184, 16, 24, 104)
RFX = (R, 0, HALF, 130)


# ---------------------------------------------------------------- op helpers
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


def grid(x, y, rows):
    return {"op": "grid", "x": x, "y": y, "rows": rows}


def dither(x, y, w, h, c, density, **kw):
    o = {"op": "dither", "x": x, "y": y, "w": w, "h": h, "color": c, "density": density}
    o.update(kw)
    return o


def shade(x, y, w, h, steps, **kw):
    o = {"op": "shade", "x": x, "y": y, "w": w, "h": h, "steps": steps}
    o.update(kw)
    return o


def shift(ops, dx, dy=0):
    out = []
    for o in ops:
        o = dict(o)
        if "x" in o:
            o["x"] += dx
        if "x2" in o:
            o["x2"] += dx
        if dy:
            if "y" in o:
                o["y"] += dy
            if "y2" in o:
                o["y2"] += dy
        if o.get("op") in ("dither", "shade") and o.get("pattern") in ("noise", "value"):
            ox, oy = o.get("offset", [0, 0])
            o["offset"] = [ox - dx, oy - dy]
        out.append(o)
    return out


def span(o):
    op = o.get("op")
    if op == "line":
        return min(o["x"], o["x2"]), max(o["x"], o["x2"])
    if op == "pixel":
        return o["x"], o["x"]
    if op == "grid":
        return o["x"], o["x"] + len(o["rows"][0]) - 1
    if "w" in o:
        return o["x"], o["x"] + o["w"] - 1
    return None


def for_half(ops, x0, width=HALF):
    """Keep full-coordinate ops that touch the half at x0, trimmed where trimming can't change the drawing."""
    out = []
    for o in ops:
        s = span(o)
        if s is None:
            out.append(o)
            continue
        lo, hi = s
        if hi < x0 or lo > x0 + width - 1:
            continue
        a, b = max(lo, x0), min(hi, x0 + width - 1)
        op = o.get("op")
        if op == "line" and o["y"] == o["y2"]:
            o = dict(o, x=a, x2=b)
        elif op in ("rect", "dither", "shade") and o.get("shape") != "ellipse" and not (
                isinstance(o.get("density"), list) and o.get("direction") in ("left", "right", "radial")):
            o = dict(o, x=a, w=b - a + 1)
        out.append(o)
    return out


# ---------------------------------------------------------------- the static scene (full coordinates)
BENCH_Y = 128                    # top surface rows 128-132, then the front
WIN_X0, WIN_X1, WIN_Y0, WIN_Y1 = 182, 233, 12, 100
PANES = ((186, 205), (210, 229))  # glass columns; the mullion 206-209 straddles the seam
PANE_Y0, PANE_Y1 = 16, 96
MOON = (195, 40)                 # centre of the moon in the left pane
SLOPE, REACH, BEAM_Y0 = 0.75, 34, 30


def wall():
    ops = [rect(0, 0, W, BENCH_Y, "2")]
    # Ashlar courses: quiet mortar a step darker than the face, staggered joints.
    for row, y in enumerate(range(3, BENCH_Y, 12)):
        ops.append(line(0, y, W - 1, y, "1"))
        off = 0 if row % 2 == 0 else 14
        for x in range(off, W, 28):
            ops.append(line(x, y + 1, x, min(y + 11, BENCH_Y - 1), "1"))
    # Ceiling dark.
    ops.append(shade(0, 0, W, 20, -1, density=[0.6, 0.0], direction="down", over=["2"]))
    # Three deliberate marks: a crack low on the left, a crack high on the right with a damp stain under it,
    # and a hairline under the window. Each crack has its moonlit lip one step up.
    for pts in (((44, 101), (47, 106), (46, 110), (50, 114), (49, 118)),
                ((392, 16), (389, 21), (391, 25), (387, 31), (388, 35)),
                ((262, 110), (266, 113), (265, 117))):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            ops.append(line(ax, ay, bx, by, "1"))
        ops.append(px(pts[1][0] + 1, pts[1][1], "3"))
    ops.append(dither(382, 36, 14, 22, "1", [0.5, 0.0], direction="down", over=["2"]))
    return ops


def window_back():
    """Casing, night sky, the moon and its halo, stars (drawn before the clouds)."""
    x0, x1, y0, y1 = WIN_X0, WIN_X1, WIN_Y0, WIN_Y1
    w = x1 - x0 + 1
    ops = [ell(x0, y0, w, 52, "A"), rect(x0, y0 + 26, w, y1 - y0 - 25, "A")]
    gx0, gx1 = x0 + 4, x1 - 4
    gw = gx1 - gx0 + 1
    ops += [ell(gx0, PANE_Y0, gw, 44, "8"), rect(gx0, PANE_Y0 + 22, gw, PANE_Y1 - PANE_Y0 - 21, "8")]
    ops.append(dither(gx0, 60, gw, PANE_Y1 - 59, "9", [0.0, 0.8], direction="down", over="8"))
    ops.append(dither(gx0, PANE_Y1 - 12, gw, 13, "W", [0.0, 0.4], direction="down", over="9"))
    # Halo: two banded rings round the moon, moving the sky along its own ramp.
    mx, my = MOON
    ops.append(shade(mx - 11, my - 11, 23, 23, 1, shape="ellipse", density=0.5, over=["8", "9"]))
    ops.append(shade(mx - 8, my - 8, 17, 17, 1, shape="ellipse", over=["8", "9"]))
    # Full moon, lit steel-white, with two quiet maria.
    ops += [ell(mx - 4, my - 4, 9, 9, "F"), ell(mx - 3, my - 3, 5, 5, "G"), px(mx + 1, my + 1, "E"),
            px(mx + 2, my, "E"), px(mx - 1, my + 2, "E")]
    for sx, sy, c in ((224, 52, "C"), (190, 62, "C"), (218, 80, "B"), (200, 24, "C")):
        ops.append(px(sx, sy, c))
    return ops


def transoms():
    gx0, gx1 = WIN_X0 + 4, WIN_X1 - 4
    ops = []
    for ty in (48, 72):
        ops += [rect(gx0, ty, gx1 - gx0 + 1, 2, "A"), line(gx0, ty, gx1, ty, "B")]
    return ops


def window_bars():
    """Mullion, transoms, lit edges and sill (drawn after the clouds, so the bars stay in front of them)."""
    y0, y1 = WIN_Y0, WIN_Y1
    gx1 = WIN_X1 - 4
    ops = [rect(206, y0 + 2, 4, y1 - y0 - 1, "A")] + transoms()
    ops += [line(209, y0 + 6, 209, y1 - 2, "B"), line(206, y0 + 6, 206, y1 - 2, "1"),
            line(gx1 + 1, y0 + 24, gx1 + 1, y1 - 3, "C"), line(WIN_X0, y0 + 26, WIN_X0, y1, "B")]
    ops += [rect(WIN_X0 - 3, y1 + 1, WIN_X1 - WIN_X0 + 7, 3, "B"), line(WIN_X0 - 3, y1 + 1, WIN_X1 + 3, y1 + 1, "C"),
            line(WIN_X0 - 2, y1 + 4, WIN_X1 + 2, y1 + 4, "1")]
    return ops


def in_beam(x, y):
    """Is full-coordinate (x, y) inside a moonbeam (a pane swept down-right along the light)?"""
    for ax, bx in PANES:
        for d in range(0, REACH + 1):
            sx, sy = x - SLOPE * d, y - d
            if ax <= sx <= bx and BEAM_Y0 <= sy <= PANE_Y1:
                return True
    return False


def moonlight():
    """Beams: each pane swept down-right (0.75 px across per row), night 4/5 dither fading with distance. They cross
    the wall beside and below the window and land on the bench top as pane-shaped patches."""
    ops = []
    for (ax, bx) in PANES:
        for y in range(BEAM_Y0, BENCH_Y):
            far = bx + int(SLOPE * min(REACH, y - BEAM_Y0))
            if y <= PANE_Y1:
                if far > bx + 1:     # the strip beside the pane (outside the window it falls on the wall)
                    ops.append(dither(bx + 1, y, far - bx, 1, "5", [0.3, 0.0], direction="right", over="2"))
                    ops.append(dither(bx + 1, y, far - bx, 1, "4", [0.7, 0.05], direction="right", over="2"))
            else:
                d0 = y - PANE_Y1
                near = ax + int(SLOPE * d0)
                k = 1 - d0 / (BENCH_Y - PANE_Y1)
                ops.append(dither(near, y, far - near + 1, 1, "5", round(0.3 * k, 3), over="2"))
                ops.append(dither(near, y, far - near + 1, 1, "4", round(0.25 + 0.4 * k, 3), over="2"))
    # Pane-shaped patches on the bench top, with the mullion's shadow between them.
    d0 = BENCH_Y - PANE_Y1
    for (ax, bx) in PANES:
        near = ax + int(SLOPE * d0)
        far = bx + int(SLOPE * min(REACH, BENCH_Y - BEAM_Y0))
        for r in range(4):
            sx = near + int(SLOPE * r)
            ops.append(dither(sx, BENCH_Y + r, far - near - 1, 1, "J", 1.0 if r < 3 else 0.5, over=["I"]))
            ops.append(dither(sx + 3, BENCH_Y + r, far - near - 7, 1, "K", 0.5, over=["J"]))
    return ops


def bench():
    y = BENCH_Y
    ops = [rect(0, y - 1, W, 1, "H"), rect(0, y, W, 4, "I"), line(0, y + 4, W - 1, y + 4, "J"),
           rect(0, y + 5, W, H - y - 5, "H"), line(0, y + 5, W - 1, y + 5, "I")]
    for gy, segs in ((y + 9, ((8, 90), (120, 200), (236, 330), (350, 408))),
                     (y + 13, ((30, 140), (170, 260), (290, 380)))):
        for a, b in segs:
            ops.append(line(a, gy, b, gy, "I"))
    ops.append(line(0, y + 17, W - 1, y + 17, "1"))  # a plank seam
    for gy, segs in ((y + 21, ((0, 70), (100, 230), (260, 360))),):
        for a, b in segs:
            ops.append(line(a, gy, b, gy, "I"))
    ops.append(shade(0, y + 18, W, H - y - 18, -1, density=[0.0, 0.7], direction="down"))
    # The lip is a touch lighter where the light reaches it; two knots; a drawer with a brass pull that glints.
    ops.append(dither(220, y + 4, W - 220, 1, "K", 0.5, over=["J"]))
    for kx, ky in ((92, y + 11), (356, y + 23)):
        ops += [ell(kx, ky, 7, 3, "I", filled=False), px(kx + 3, ky + 1, "1"),
                line(kx - 9, ky - 1, kx - 1, ky - 1, "I"), line(kx + 7, ky + 3, kx + 16, ky + 3, "I")]
    ops += [rect(238, y + 8, 96, 19, "1", filled=False), line(239, y + 9, 332, y + 9, "I"),
            rect(283, y + 16, 7, 2, "N"), line(283, y + 16, 289, y + 16, "O"), px(284, y + 16, "P")]
    return ops


# ---------------------------------------------------------------- apparatus (right-half coordinates)
FX, FY = fluids.FLASK_ORIGIN
SX, SY = fluids.STEAM_ORIGIN
DX, DY = fluids.DRIP_ORIGIN
# Group offsets (revision 3 moved the set left for margin): authored at the old places, shifted as groups.
FLASK_DX, COIL_DX, INK_DX, REEL_DX, CRUCIBLE_DX, MON_DX = -22, -6, -8, -9, -12, -6
CX, CY = 150 + FLASK_DX, 85      # bulb centre (the light source)


def flask_glass_rows():
    """The flask's glass: the one-pixel ring round the simulated interior, coloured as a painter would: moonlit at the
    upper left, dark at the lower right, mint below the waterline where the glowing liquid lights it."""
    rows = []
    cx, cy = fluids.FLASK_C
    for y in range(fluids.FLASK_H):
        row = ""
        for x in range(fluids.FLASK_W):
            if not fluids.flask_glass(x, y):
                row += "."
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if y < 11:                                   # neck
                row += "E" if dx < 0 else "B"
            elif y >= fluids.LIQUID_TOP:                 # below the waterline
                row += "l" if (dx < -9 and dy < 10) else ("k" if dy < 15 else "j")
            elif dx < 0 and dy < 0:
                row += "E" if dx < -6 and dy < -6 else "D"
            elif dx >= 0 and dy < 0:
                row += "C"
            else:
                row += "D" if dx < 0 else "k"
        rows.append(row)
    return rows


def flask_depth_rows(y_from=36):
    """The bulb's interior below the liquid's lowest surface (flask-canvas row y_from = right-half y 92 and down),
    painted the deep liquid's own colour j behind the liquid layer: where the boil opens a void in the simulated
    liquid, it reads as a dark eddy in the liquid, not as a hole through to the wall."""
    return ["".join("j" if (y >= y_from and fluids.flask_interior(x, y)) else "." for x in range(fluids.FLASK_W))
            for y in range(fluids.FLASK_H)]


def light_pools():
    """Banded radial mint light on the wall behind the flask: concentric shade bands along the night->mint ramp."""
    ops = []
    for r, dens, over in ((42, 1.0, ["1", "2"]), (29, 1.0, ["2", "h"]), (49, 0.5, ["2"]), (35, 0.5, ["h"])):
        h = int(r * 1.8)
        ops.append(shade(CX - r, CY - h // 2, 2 * r + 1, h + 1, 1, shape="ellipse", density=dens, over=over))
    return ops


def bench_light():
    """An elliptical mint pool on the bench top round the burner, drawn row by row (rows 128-132)."""
    ops = []
    bands = ((60, "i", 0.5, ["I", "J", "K"]), (48, "i", 1.0, ["I", "J", "K"]), (34, "j", 1.0, ["i"]),
             (22, "k", 0.5, ["j"]))
    for a, c, dens, over in bands:
        for r, dy in enumerate((-2, -1, 0, 1, 2)):
            hw = int(a * math.sqrt(1 - (dy / 3.0) ** 2))
            ops.append(dither(CX - hw, BENCH_Y + r, 2 * hw + 1, 1, c, dens, over=over))
    return ops


def bench_front_light():
    """The flask's light reflected on the bench's front edge: mint on the lip, a short fading pool below it."""
    ops = [dither(CX - 30, BENCH_Y + 4, 61, 1, "k", 0.5, over=["J", "K"])]
    for r, (hw, dens) in enumerate(((34, 0.5), (24, 0.5), (14, 0.25))):
        ops.append(dither(CX - hw, BENCH_Y + 5 + r, 2 * hw + 1, 1, "i", dens, over=["H", "I"]))
    return ops


def stand_and_coil():
    ops = []
    # Stand: base plate, rod with a finial, a clamp holding the coil.
    ops += [rect(45, 125, 16, 3, "B"), line(45, 125, 60, 125, "C"), rect(52, 40, 2, 85, "B"),
            line(52, 40, 52, 124, "C"), rect(51, 38, 4, 2, "C"), line(51, 38, 54, 38, "D"),
            rect(54, 72, 7, 2, "B"), line(54, 72, 60, 72, "C"), rect(55, 71, 2, 4, "N"), px(55, 71, "O")]
    # Coil: five loops; back arcs dark, front arcs lit, left turns moonlit, right turns facing the flask in mint.
    loops = (63, 69, 75, 81, 87)
    for ly in loops:
        ops.append(ell(60, ly, 27, 7, "B", filled=False))
    for i, ly in enumerate(loops):
        ops += [line(63, ly + 6, 83, ly + 6, "D"), line(60, ly + 2, 60, ly + 4, "E"),
                line(86, ly + 2, 86, ly + 4, "k"), px(85, ly + 5, "j"), px(84, ly + 1, "j")]
        if i >= 2:
            ops.append(line(64, ly + 5, 82, ly + 5, "i"))      # condensate running down the coil
    ops += [rect(72, 94, 3, 6, "C"), line(73, 94, 73, 99, "h"), line(72, 94, 72, 99, "D"), px(74, 96, "k")]
    return shift(ops, COIL_DX)


def side_arm():
    """From the neck down to the coil: glass edges, a faint vapour core, its underside lit near the flask."""
    a, b = 145 + FLASK_DX, 86 + COIL_DX
    return [line(a, 58, b, 62, "D"), line(a, 59, b, 63, "h"), line(a, 60, b, 64, "B"),
            line(a, 60, a - 27, 62, "j"), line(a, 60, a - 13, 61, "k")]


def tripod_and_burner():
    ops = [line(130, 107, 126, 127, "B"), line(170, 107, 174, 127, "B"), line(131, 108, 128, 122, "j"),
           line(169, 108, 172, 122, "j"), rect(128, 105, 45, 2, "B"), line(128, 105, 172, 105, "k"),
           px(150, 105, "l")]
    # Spirit burner (brass): body, collar and wick; its shoulders catch the mint glow from above.
    ops += [ell(139, 116, 23, 14, "N"), rect(139, 122, 23, 6, "N"), line(140, 127, 160, 127, "I"),
            line(141, 119, 159, 119, "O"), line(143, 118, 157, 118, "O"), line(161, 120, 161, 126, "I"),
            line(141, 117, 146, 116, "k"), line(154, 116, 159, 117, "j"),
            rect(145, 112, 11, 4, "N"), line(145, 112, 155, 112, "l"), line(155, 113, 155, 115, "I"),
            rect(149, 111, 3, 1, "I")]
    return shift(ops, FLASK_DX)


def beaker_back():
    return shift([rect(61, 108, 25, 20, "1"), line(62, 109, 84, 109, "2")], COIL_DX)


def beaker_front():
    ops = [line(61, 108, 61, 127, "D"), line(85, 109, 85, 127, "k"), line(61, 127, 85, 127, "C"),
           line(60, 108, 86, 108, "C"), px(59, 107, "C"), px(86, 109, "j"),
           line(63, 111, 63, 123, "E")]
    for ty in (113, 118, 123):
        ops.append(line(82, ty, 83, ty, "C"))
    return shift(ops, COIL_DX)


def flask_front():
    ops = [rect(145, 55, 10, 2, "C"), line(145, 55, 154, 55, "D"), px(145, 56, "E"), px(154, 56, "k")]
    # Specular streak on the moonlit shoulder of the bulb, one white glint.
    ops += [px(137, 72, "n"), px(136, 73, "n"), px(135, 75, "n"), px(134, 77, "*"), px(134, 78, "n"),
            px(133, 80, "n"), px(140, 70, "n")]
    return [grid(FX, FY, flask_glass_rows())] + shift(ops, FLASK_DX)


FLAMES = [
    ["..z..", ".zyz.", ".yry.", ".ryr.", "..r.."],
    ["...z.", "..zy.", ".yyr.", ".ryr.", "..r.."],
    ["..z..", ".zyz.", "zyryz", ".ryr.", "..r.."],
    [".z...", ".yz..", ".yyr.", ".ryr.", "..r.."],
]


def flame(frame):
    return [grid(148 + FLASK_DX, 106, FLAMES[[0, 0, 1, 1, 0, 2, 2, 0, 3, 3, 0, 0][frame % 12]])]


# Inkbolt: an ink bottle (moonlit on its left) with a nib pen leaning out of it. Cutbolt: a film reel on edge with a
# strip of pink film curling off it along the bench. Pixelbolt: a crucible with an ember in it. Anode: a little monitor.
def ink_bottle():
    ops = [rect(12, 119, 13, 9, "9"), rect(13, 118, 11, 1, "9"), rect(16, 115, 5, 3, "W"), rect(15, 114, 7, 1, "@"),
           line(12, 119, 12, 127, "W"), line(13, 120, 13, 125, "@"), line(13, 118, 23, 118, "W"),
           line(24, 120, 24, 127, "8"), line(16, 123, 21, 123, "W"), line(16, 124, 21, 124, "8"),
           line(19, 114, 27, 102, "O"), line(20, 114, 28, 102, "N"), px(28, 101, "E"), px(29, 100, "F"),
           px(29, 101, "E")]
    return shift(ops, INK_DX)


def reel_body():
    ops = [ell(28, 113, 15, 15, "C"), ell(29, 114, 13, 13, "B"), ell(34, 119, 3, 3, "D"),
           line(29, 116, 29, 122, "E"), line(30, 115, 31, 114, "E"), px(32, 114, "D"),
           line(41, 126, 47, 126, "V"), line(42, 127, 48, 127, "U")]
    return shift(ops, REEL_DX)


def crucible_body():
    ops = [rect(96, 115, 13, 1, "D"), rect(97, 116, 11, 6, "C"), rect(98, 122, 9, 5, "C"), rect(99, 127, 7, 1, "B"),
           line(97, 116, 97, 121, "D"), line(107, 116, 107, 121, "k"), line(106, 122, 106, 126, "j"),
           line(98, 126, 105, 126, "B")]
    return shift(ops, CRUCIBLE_DX)


def monitor_body():
    ops = [rect(180, 108, 21, 14, "B"), rect(181, 109, 19, 12, "C"), rect(183, 110, 15, 9, "h"),
           line(180, 108, 200, 108, "D"), line(180, 109, 180, 121, "k"), rect(188, 122, 5, 3, "B"),
           rect(184, 125, 13, 3, "C"), line(184, 125, 196, 125, "D"),
           line(185, 112, 191, 112, "i"), line(185, 114, 194, 114, "i"), line(185, 116, 189, 116, "i")]
    return shift(ops, MON_DX)


def miniatures():
    return ink_bottle() + reel_body() + crucible_body() + monitor_body()


# ---------------------------------------------------------------- idle motions (staggered; right-half coordinates)
GHOST = ["j.", "jj", "j."]
CURSOR = ["m.", "mm", "m."]


def monitor_cursors(frame):
    """Anode: your cursor blinks (24 frames: on 0-13); a fainter agent cursor wanders the text on its own (48)."""
    ops = []
    if frame % 24 < 14:
        ops.append(px(190, 116, "m"))
    path = [(192, 111), (193, 111), (194, 111), (195, 112), (195, 113), (194, 114), (193, 115), (192, 115)]
    gx, gy = path[(frame // 6) % len(path)]
    ops += [grid(gx, gy, GHOST), grid(196, 115, CURSOR)]
    return shift(ops, MON_DX)


# The reel's five spoke holes in two poses a notch (36 degrees) apart, round the hub at (35, 120); the film strip's
# sprocket dots step one pixel along with each notch.
REEL_HOLES = (((34, 115), (30, 119), (38, 119), (31, 123), (37, 123)),
              ((36, 115), (31, 117), (39, 121), (34, 124), (30, 122)))
REEL_NOTCHES = (30, 78)          # the reel turns a notch on these frames (a two-frame move each time)


def reel_state(frame):
    turns = sum(1 for t in REEL_NOTCHES if frame >= t)
    moving = any(t <= frame < t + 2 for t in REEL_NOTCHES)
    return turns, moving


def reel(frame):
    turns, moving = reel_state(frame)
    holes = REEL_HOLES[turns % 2]
    ops = [rect(x, y, 2, 2, "1") for x, y in holes]
    if moving:
        ops.append(px(36, 116, "E"))          # the rim's glint slides as it turns
    dots = (44, 47) if turns % 2 == 0 else (45, 48)
    ops += [px(dots[0], 126, "U"), px(dots[1], 126, "U")]
    return shift(ops, REEL_DX)


def ember(frame):
    """Pixelbolt: the crucible's ember breathes on 24 frames, brightest at 18-20 of each cycle (off the cursor's
    blink), one hot pixel rising above it at the peak."""
    c = frame % 24
    hot = 18 <= c <= 20
    warm = c in (16, 17, 21, 22)
    ops = [rect(98, 116, 9, 1, "e" if not hot else "f"), rect(100, 116, 5, 1, "f" if not hot else "g"),
           px(102, 116, "g"), px(101, 115, "f" if not hot else "g"), px(103, 114, "e")]
    if warm or hot:
        ops.append(px(99, 116, "f"))
    if hot:
        ops.append(px(102 + (c - 19), 113 - (c - 18), "e"))
    return shift(ops, CRUCIBLE_DX)


# Inkbolt: a bead of ink gathers on the underside of the raised nib, swells, catches the moon for two frames, then is
# drawn back down the pen into the bottle (the slit wicks it). Frames 56-91 of the loop; quiet the rest.
NIB_BEAD = {56: [(29, 102, "W")], 62: [(29, 102, "Z")], 68: [(29, 102, "Z"), (29, 103, "W")],
            74: [(29, 102, "Z"), (29, 103, "Z")], 78: [(29, 102, "E"), (29, 103, "Z")],
            80: [(29, 102, "Z"), (29, 103, "Z")], 84: [(28, 104, "Z")], 86: [(27, 105, "Z")],
            88: [(26, 107, "W")], 90: [(25, 108, "W")], 92: []}


def nib(frame):
    if not 56 <= frame < 92:
        return []
    key = max(k for k in NIB_BEAD if k <= frame)
    return shift([px(x, y, c) for x, y, c in NIB_BEAD[key]], INK_DX)


def star(frame):
    c = {21: "E", 22: "F", 23: "E"}.get(frame % 48, "D")
    return [px(214 - R, 30, c)]


MOTES = ((8, 106, 3, 4, 48, 0), (20, 116, 4, 3, 48, 150), (34, 110, 3, 3, 24, 60), (-6, 112, 3, 3, 96, 200))


def motes(frame):
    """Dust motes turning on closed paths; each glints only while it is inside a moonbeam (right-half coords)."""
    ops = []
    for (cx, cy, rx, ry, period, phase) in MOTES:
        a = 2 * math.pi * frame / period + math.radians(phase)
        x, y = cx + round(rx * math.cos(a)), cy + round(ry * math.sin(a))
        if in_beam(x + R, y):
            ops.append(px(x, y, "x" if (frame + phase) % 12 < 6 else "w"))
    return ops


def steam_light(vent=fluids.VENT):
    """Inside the steam layer: the flask's mint light from below. Rings of light centred on the neck recolour only the
    steam's pixels (solid near the neck, Bayer-feathered further out, dim tones furthest), so the undersides of the
    billows leaving the neck turn mint while their moonlit tops stay pale."""
    vx, vy = vent
    # Only the shadow's sharpest rim (marked t by the look) takes the light, solid: the steam leaving the neck gets a
    # 1-2 px mint rim on its lower right and keeps its own body; elsewhere the marker becomes the plain shadow u.
    return (ring(vx, vy, 6.0, "l", 1.0, ["t"]) + ring(vx, vy, 9.5, "k", 1.0, ["t"])
            + [{"op": "dither", "color": "u", "density": 1.0, "over": ["t"]}])


def steam_fade(w, mute=(24, 34)):
    """Inside a steam layer w wide: near the top the billows lose their lights (x, F and G become w; solid above
    mute[0], then value-noise clumps down to mute[1], so no line or checker forms), so nothing bright is left where the
    steam dissolves. The dissolve itself is the sim's own: density falls toward the outline and the look feathers u
    into v there, so the plume frays from its edge (an erase op punched enclosed holes that read as eyes)."""
    y0, y1 = mute
    return [
        dither(0, 0, w, y0, "w", 1.0, over=["x", "F", "G"]),
        dither(0, y0, w, y1 - y0, "w", [1.0, 0.0], direction="down", over=["x", "F", "G"], seed=11,
               pattern="value", scale=3),
    ]


def ring(cx, cy, r, color, density, over):
    """A disc of light centred on (cx, cy), as one dither row per pixel row (the house glow: solid bands with Bayer
    feathers), limited to the listed colours. Only the rows above the centre: light leaving an opening."""
    ops = []
    for y in range(int(cy - r), int(cy) + 1):
        dy = y + 0.5 - cy
        if abs(dy) > r:
            continue
        hw = math.sqrt(r * r - dy * dy)
        x0, x1 = math.ceil(cx - hw - 0.5), math.floor(cx + hw - 0.5)
        if x1 >= x0:
            ops.append(dither(x0, y, x1 - x0 + 1, 1, color, density, over=over))
    return ops


def moonlit_clouds(cx, cy):
    """Inside a cloud layer whose canvas origin is (cx, cy) in full coordinates: cloud pixels crossing the moon and its
    halo lift along their own ramps (two steps on the disc, one on the halo), so a passing cloud glows silver at the
    moon instead of blotting it out."""
    mx, my = MOON[0] - cx, MOON[1] - cy
    return [shade(mx - 10, my - 10, 21, 21, 1, shape="ellipse", over=["9", "A", "B", "C"]),
            shade(mx - 5, my - 5, 11, 11, 1, shape="ellipse", over=["W", "B", "C", "D"])]


# ---------------------------------------------------------------- recipes
def fluid_frames(name, effect=None):
    recipe = json.loads((BUILD / f"{name}.json").read_text(encoding="utf-8"))
    effect = effect or name
    return [f.get("ops", []) for f in recipe["frames"] if f["name"].rsplit("-", 1)[0] == effect]


def at(ops, dx, dy):
    return [dict(o, x=o["x"] + dx, y=o["y"] + dy) for o in ops]


def recipe(name, w, h, frames, animated=True):
    rec = {"version": 1, "name": name, "width": w, "height": h, "palette": PALETTE, "ramps": RAMPS, "frames": frames}
    if animated:
        rec["animations"] = {"loop": {"frames": [f["name"] for f in frames]}}
    return rec


def left_bg():
    full = wall() + window_back() + window_bars() + moonlight() + bench()
    # One column wider than the half: the right half is drawn over an identical column 208, so browsers that
    # antialias image edges at fractional scales show no hairline at the seam.
    return recipe("hero-left-bg", HALF + 1, H, [{"name": "bg", "duration": MS, "ops": for_half(full, 0, HALF + 1)}],
                  False)


def right_bg():
    static = shift(for_half(wall() + window_back() + window_bars() + moonlight() + bench(), R), -R)
    ops = (static + light_pools() + [grid(FX, FY, flask_depth_rows())] + bench_light() + bench_front_light()
           + stand_and_coil() + side_arm()
           + tripod_and_burner() + miniatures() + beaker_back())
    return recipe("hero-right-bg", HALF, H, [{"name": "bg", "duration": MS, "ops": ops}], False)


def pane_transom(pane):
    """The upper transom across one pane only (full coordinates): redrawn over that pane's clouds."""
    ax, bx = pane
    return [rect(ax, 48, bx - ax + 1, 2, "A"), line(ax, 48, bx, 48, "B")]


def left_fx():
    x0, y0, w, h = LFX
    clouds = fluid_frames("clouds", "clouds-l")
    ccx, ccy = fluids.CLOUD_ORIGINS_FULL["clouds-l"]
    bars = shift(pane_transom(PANES[0]), -x0, -y0)
    frames = []
    for i in range(FRAMES):
        front = [o for o in shift(motes(i), R - x0, -y0) if 0 <= o["x"] < w]
        frames.append({"name": f"loop-{i}", "duration": MS, "layers": [
            {"name": "clouds", "x": ccx - x0, "y": ccy - y0, "ops": clouds[i] + moonlit_clouds(ccx, ccy)},
            {"name": "front", "ops": bars + front},
        ]})
    return recipe("hero-left-fx", w, h, frames)


def right_fx():
    steam, flask, drip = fluid_frames("steam"), fluid_frames("flask"), fluid_frames("drip")
    clouds = fluid_frames("clouds", "clouds-r")
    ccx, ccy = fluids.CLOUD_ORIGINS_FULL["clouds-r"]
    bars = shift(pane_transom(PANES[1]), -R)
    frames = []
    for i in range(FRAMES):
        d = (i + fluids.DRIP_SHIFT) % fluids.DRIP_FRAMES
        frames.append({"name": f"loop-{i}", "duration": MS, "layers": [
            {"name": "sky", "ops": star(i)},
            {"name": "clouds", "x": ccx - R, "y": ccy, "ops": clouds[i]},
            {"name": "steam", "x": SX, "y": SY, "ops": steam[i] + steam_fade(fluids.STEAM_W) + steam_light()},
            {"name": "liquid", "x": FX, "y": FY, "ops": flask[i]},
            {"name": "drip", "x": DX, "y": DY, "ops": drip[d]},
            {"name": "front", "ops": bars + flask_front() + beaker_front() + flame(i) + monitor_cursors(i)
             + reel(i) + ember(i) + nib(i) + [o for o in motes(i) if o["x"] >= 0]},
        ]})
    return recipe("hero-right-fx", RFX[2], RFX[3], frames)


def review(bg, fx, x, y, name):
    """A two-frame recipe for value checks: the background, then the still frame's effects layers stacked on it."""
    still = fx["frames"][STILL]
    layers = [dict(layer, x=layer.get("x", 0) + x, y=layer.get("y", 0) + y) for layer in still["layers"]]
    frames = [bg["frames"][0], {"name": "still", "duration": MS, "from": "bg", "layers": layers}]
    return recipe(name, HALF, H, frames, False)


def main():
    RECIPES.mkdir(exist_ok=True)
    lb, rb, lf, rf = left_bg(), right_bg(), left_fx(), right_fx()
    recs = (lb, rb, lf, rf, review(lb, lf, LFX[0], LFX[1], "hero-left-review"), review(rb, rf, 0, 0, "hero-right-review"))
    for rec in recs:
        (RECIPES / f"{rec['name']}.json").write_text(json.dumps(rec, separators=(",", ":")) + "\n",
                                                      encoding="utf-8", newline="\n")
    (BUILD / "still.txt").write_text(f"{STILL}\n", encoding="utf-8", newline="\n")
    print("recipes written; still frame", STILL)


if __name__ == "__main__":
    main()
