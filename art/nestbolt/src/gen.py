"""Generate the Nestbolt card recipe: recipes/nestbolt.json (192x100, a 72-frame loop at 70 ms).

Python lays out drawing operations (shapes, lines, hand-placed pixels, dither and shade regions, copies) and places
the compiled fluid frames as layers. It never computes an effect pixel: every kerf, glow, shadow, outline and fluid
pixel is drawn by Pixelbolt when the recipe renders.

Frame order: sheet templates first (copy sources), then the static background, then the loop.
  tpl-fresh   an uncut plywood sheet at (0, 0)
  tpl-<part>  one part of the nest isolated (flood-filled between the kerf lines), for the 1 px settle
  tpl-done    a finished sheet: holes, settled parts, charred kerf
  bg          the workshop, the machine's back panel, the bed and the unload table
  loop-00..71 the animation, each built on bg

NESTBOLT_VARIANT=burst writes recipes/nestbolt-burst.json instead: the site's hover variant (see variant.py).
"""

import json
import sys
from pathlib import Path

import layout as L
import nest
import timing as T
from variant import BURST, SUFFIX
from ops import PALETTE, RAMPS, copy, dither, fill, grid, line, outline, polyline, px, rect, replace, shade

HERE = Path(__file__).parent
ROOT = HERE.parent
BUILD = ROOT / "out" / "build"
W, H = L.W, L.H
SW, SH = nest.SW, nest.SH
EDGE = 2               # the plywood's edge (two plies) below the sheet's face

# ---------------------------------------------------------------- the nest's parts
# Seeds inside each region between kerf lines (sheet-local).
PARTS = {
    "bolt": (44, 3),
    "flange": (22, 1),
    "cover": (34, 1),
    "ramp": (25, 25),
    "gusset": (53, 22),
    "lbar": (25, 40),
}
# When each part is freed (the contour that closes it), and the frame it settles: the remnant cut ends at the
# sheet's top edge, so the parts there settle first and the rest follow a frame later.
FREED = {
    "bolt": T.closed_at(0),
    "flange": T.DROP[0], "cover": T.DROP[0], "ramp": T.DROP[0],
    "gusset": T.DROP[1], "lbar": T.DROP[1],
}
WOOD = "K"             # plywood face, mid-dark, so the cut's light pool is the only light thing on the sheet
KERF = "H"             # charred kerf
# A settled part sits lower, in the skeleton's shade: one step down (tone A) or two (tone B), alternating so the
# pieces read apart, each with its moonlit cut edge (Q) back at the sheet's own tone.
SETTLED = {
    "A": {"L": "K", "K": "J", "J": "I", "Q": "K"},
    "B": {"L": "J", "K": "I", "J": "H", "Q": "J"},
}
TONE = {"flange": "A", "cover": "B", "bolt": "A", "ramp": "A", "gusset": "B", "lbar": "B"}
GAP = "H"              # the shadowed cut face a settled part leaves above it
# Two-tone kerf: glowing just behind the head (g, then f and e for a few frames), then charred: a KERF core with
# a CHAR burn edge one pixel below and right, so the parts' outlines build up clearly over the loop.
HEAT = [(0.5, "g"), (2.0, "f"), (4.0, "e")]
CHAR = "I"

# Plywood veneer grain, horizontal runs (x, y, length, colour): pale early-wood streaks (L) that step a row now
# and then, like the face veneer's figure, and a few short dark flecks (J). Light streaks, so it reads as one
# board and not as planks.
GRAIN = [
    (2, 3, 17, "L"), (19, 4, 12, "L"), (38, 3, 15, "L"),
    (8, 10, 20, "L"), (28, 9, 9, "L"), (44, 11, 10, "J"),
    (0, 17, 13, "L"), (13, 18, 18, "L"), (36, 17, 16, "L"),
    (4, 25, 9, "J"), (16, 24, 22, "L"), (38, 25, 14, "L"),
    (0, 31, 21, "L"), (21, 32, 13, "L"), (40, 31, 3, "J"),
    (6, 38, 18, "L"), (24, 39, 20, "L"), (47, 38, 7, "L"),
]


def grain(over=None):
    """The veneer grain on a sheet at (0, 0). `over` limits it to one part (templates), so the grain carries on
    across a settled part exactly, one pixel lower."""
    kw = {"over": over} if over else {}
    return [dither(x, y, n, 1, c, 1.0, **kw) for x, y, n, c in GRAIN]


def all_kerf(c):
    ops = []
    for _, pts in nest.ROUTE:
        ops += polyline(pts, c)
    return ops


def tpl_fresh():
    ops = [rect(0, 0, SW, SH, WOOD)] + grain()
    # the plywood edge: a pale face ply over a dark glue line, with the end grain of the core showing
    ops += [line(0, SH, SW - 1, SH, "L"), line(0, SH + 1, SW - 1, SH + 1, "I")]
    ops += [px(x, SH, "J") for x in range(3, SW, 7)]
    return {"name": "tpl-fresh", "duration": L.MS, "ops": ops}


def tpl_part(name, seed):
    # Marker colours (only here): A the sheet, 0 the kerf, z the part; all are replaced before the frame ends.
    m, k, p = "A", "0", "z"
    ops = [rect(0, 0, SW, SH, m)] + all_kerf(k) + [fill(seed[0], seed[1], p), replace(m, "transparent"),
                                                   replace(k, "transparent")]
    ops += grain(over=[p]) + [replace(p, WOOD)]
    # the part's cut edges facing the moon (top and left) catch light once it has settled: marked Q here and
    # remapped by settle()
    ops += [outline("Q", position="inside", directions=[".x.", "x..", "..."])]
    return {"name": f"tpl-{name}", "duration": L.MS, "ops": ops}


def sheet_copy(frame, x, y, **kw):
    """Copy a sheet template (it lies at 0, 0 in its frame, plywood edge included) to (x, y)."""
    return copy(frame, x, y, sx=0, sy=0, w=SW, h=SH + EDGE, **kw)


def settle(name, x, y):
    """A freed part at its settled position on a sheet at (x, y): the gap it leaves, then the part 1 px lower."""
    return [sheet_copy(f"tpl-{name}", x, y, remap={"L": GAP, "K": GAP, "J": GAP, "Q": GAP}),
            sheet_copy(f"tpl-{name}", x, y + 1, remap=SETTLED[TONE[name]])]


def tpl_done():
    ops = [sheet_copy("tpl-fresh", 0, 0)]
    for name in PARTS:
        ops += settle(name, 0, 0)
    ops += kerf_ops(10 ** 6, 0, 0, hot=False)
    return {"name": "tpl-done", "duration": L.MS, "ops": ops}


# ---------------------------------------------------------------- the kerf at time t
def heat_colour(age):
    for limit, c in HEAT:
        if age < limit:
            return c
    return KERF


def char_edge(a, b):
    """The burn edge of a straight kerf run from a to b: the same run one pixel down and right, trimmed to the
    sheet (or None)."""
    sx = (b[0] > a[0]) - (b[0] < a[0])
    sy = (b[1] > a[1]) - (b[1] < a[1])
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    pts = [(a[0] + sx * i + 1, a[1] + sy * i + 1) for i in range(n + 1)]
    pts = [p for p in pts if p[0] < SW and p[1] < SH]
    return (pts[0], pts[-1]) if pts else None


def kerf_ops(t, x0, y0, hot):
    """Kerf cut so far on the sheet at (x0, y0) at time t, as runs of equal colour drawn as lines: the charred part
    (hot=False, burn edges first, then the cores) or the still-glowing part (hot=True)."""
    runs = []
    for c in T.CONTOURS:
        if c["times"][0] > t:
            continue
        pix = [p for p in T.contour_pixels(c) if p[1] <= t and (heat_colour(t - p[1]) != KERF) == hot]
        run = None
        for (x, y), tc, seg in pix:
            col = heat_colour(t - tc)
            if run and run[2] == col and run[3] == seg and abs(x - run[1][0]) <= 1 and abs(y - run[1][1]) <= 1:
                run[1] = (x, y)
            else:
                if run:
                    runs.append(run)
                run = [(x, y), (x, y), col, seg]
        if run:
            runs.append(run)
    ops = []
    if not hot:
        for a, b, _, _ in runs:
            edge = char_edge(a, b)
            if edge:
                ops.append(line(edge[0][0] + x0, edge[0][1] + y0, edge[1][0] + x0, edge[1][1] + y0, CHAR))
    for a, b, col, _ in runs:
        ops.append(line(a[0] + x0, a[1] + y0, b[0] + x0, b[1] + y0, col))
    return ops


def cutting_sheet(k, x0, y0):
    """The sheet under the laser at frame k, charred kerf only (the glowing kerf is drawn after the light)."""
    ops = [sheet_copy("tpl-fresh", x0, y0)]
    for name in PARTS:
        if k >= FREED[name]:
            ops += settle(name, x0, y0)
    return ops + kerf_ops(k, x0, y0, hot=False)


# ---------------------------------------------------------------- background
def background():
    ops = [rect(0, 0, W, H, "2")]
    # workshop wall (quiet: the label sits top left), a faint panel seam
    ops += [line(0, 22, 85, 22, "3")]
    # the machine's back panel behind the cell, and its left edge
    ops += [rect(86, 0, W - 86, 29, "A"), line(86, 0, 86, 28, "B"), line(87, 0, 87, 28, "1"),
            line(88, 2, W - 1, 2, "B"), line(88, 3, W - 1, 3, "1"), line(88, 20, W - 1, 20, "1")]
    for x in (100, 128, 180):
        ops += [px(x, 5, "B"), px(x, 23, "B")]
    dx, dy, dw, dh = L.DUCT
    ops += [rect(dx, dy, dw, dh, "B"), rect(dx + 2, dy + 2, dw - 4, dh - 4, "0"),
            line(dx, dy, dx + dw - 1, dy, "C"), line(dx, dy, dx, dy + dh - 1, "C"),
            line(dx + 1, dy + dh - 1, dx + dw - 1, dy + dh - 1, "1")]
    # the bed: back lip, dark well, slats on edge (a few burnt tips), side walls, front lip
    ops += [rect(98, 29, 76, 57, "1"), line(98, 29, 173, 29, "B"), line(98, 30, 173, 30, "A")]
    for x in range(L.BED_X0, L.BED_X1 + 1, 4):
        ops += [line(x, 31, x, 83, "3")]
    ops += [line(98, 31, 98, 85, "A"), line(173, 31, 173, 85, "A"), line(99, 84, 172, 84, "A"),
            line(99, 85, 172, 85, "0")]
    # unload table: rollers along Y (lit left), rails front and back
    ops += [rect(0, 29, 86, 57, "1"), line(0, 29, 85, 29, "B"), line(0, 30, 85, 30, "A")]
    for x in range(4, 84, 9):
        ops += [rect(x, 31, 3, 53, "3"), line(x, 31, x, 83, "4"), line(x + 2, 31, x + 2, 83, "2")]
    ops += [line(0, 84, 85, 84, "A"), line(0, 85, 85, 85, "0")]
    # the machine's front: a dark panel with a lit lip, a seam between table and cell, screws, the warning label
    ops += [rect(0, 86, W, 14, "A"), line(0, 86, W - 1, 86, "C"), line(0, 87, W - 1, 87, "B"),
            line(0, 98, W - 1, 98, "1"), line(0, 99, W - 1, 99, "1"), line(89, 88, 89, 97, "1"),
            line(90, 88, 90, 97, "B")]
    for x in (10, 60, 120, 182):
        ops += [px(x, 92, "1"), px(x - 1, 91, "C")]
    # laser warning label: a small brass triangle with a dark sun mark
    ops += [grid(147, 89, ["..Q..", ".QPQ.", ".PNP.", "QPPPQ"]), px(149, 91, "N")]
    # status lamp housing
    ops += [rect(160, 90, 5, 4, "1"), line(160, 90, 164, 90, "B")]
    return {"name": "bg", "duration": L.MS, "ops": ops}


# ---------------------------------------------------------------- the machine (drawn over sheets and smoke)
def fan(k):
    """Extractor fan behind the grille: four blades turning 22.5 degrees every two frames (period 8)."""
    dx, dy, dw, dh = L.DUCT
    cx, cy = dx + dw // 2, dy + dh // 2
    poses = [
        [(4, 0), (0, 4), (-4, 0), (0, -4)],
        [(4, 2), (-2, 4), (-4, -2), (2, -4)],
        [(3, 3), (-3, 3), (-3, -3), (3, -3)],
        [(2, 4), (-4, 2), (-2, -4), (4, -2)],
    ]
    ops = []
    for (bx, by) in poses[(k // 2) % 4]:
        ops += [line(cx, cy, cx + bx, cy + by, "B"), px(cx + bx, cy + by, "C")]
    ops.append(px(cx, cy, "D"))
    return ops


def grille():
    dx, dy, dw, dh = L.DUCT
    ops = [line(dx + 2, dy + 2, dx + dw - 3, dy + 2, "1")]
    for y in range(dy + 4, dy + dh - 2, 3):
        ops += [line(dx + 2, y, dx + dw - 3, y, "A"), line(dx + 2, y, dx + 5, y, "B")]
    return ops


def rails():
    ops = []
    for x in (L.RAIL_L, L.RAIL_R):
        ops += [rect(x, 26, 6, 60, "A"), line(x, 26, x, 85, "C"), line(x + 1, 26, x + 1, 85, "B"),
                line(x + 5, 26, x + 5, 85, "1"), line(x, 26, x + 5, 26, "C")]
    return ops


def gantry(hx, cy):
    """The beam across the rails at the head's row: top face, front face, end blocks."""
    top = cy - 13
    x0, x1 = L.RAIL_L, L.RAIL_R + 5
    ops = [rect(x0, top, x1 - x0 + 1, 3, "B"), line(x0, top, x1, top, "C"),
           rect(x0, top + 3, x1 - x0 + 1, 5, "A"), line(x0, top + 3, x1, top + 3, "B"),
           line(x0, top + 7, x1, top + 7, "1")]
    for x in (x0 - 1, L.RAIL_R - 1):
        ops += [rect(x, top - 1, 8, 10, "B"), line(x, top - 1, x + 7, top - 1, "D"), line(x, top - 1, x, top + 8, "C"),
                line(x + 7, top, x + 7, top + 8, "1"), line(x + 1, top + 8, x + 7, top + 8, "1"),
                px(x + 2, top + 1, "A"), px(x + 5, top + 1, "A")]
    return ops


HEAD = [  # columns hx-4..hx+4, rows cy-18..cy-2; moonlit from the upper left, brass collar and nozzle
    "...DCB...",
    "..DCCBA..",
    ".DCCBBA1.",
    ".CBBBAA1.",
    ".C00BAA1.",
    ".C0FBAA1.",
    ".CBBBAA1.",
    "..PQOON..",
    "..CBBA1..",
    "..CBBA1..",
    "..CBBA1..",
    "..DBBA1..",
    "..OPPON..",
    "...QPN...",
    "...PON...",
    "....P....",
    "....O....",
]


def head(hx, cy, state, k):
    """Laser head on the beam's front: carriage plate, collimator body with a lens window, brass collar and nozzle,
    and the assist-gas hose looping back to the beam."""
    ops = [rect(hx - 5, cy - 12, 11, 6, "B"), line(hx - 5, cy - 12, hx + 5, cy - 12, "C"),
           line(hx + 5, cy - 11, hx + 5, cy - 7, "1"), px(hx - 4, cy - 11, "A"), px(hx + 4, cy - 11, "A"),
           px(hx - 4, cy - 7, "A"), px(hx + 4, cy - 7, "A")]
    ops += [grid(hx - 4, cy - 18, HEAD)]
    # the hose: from the cap over to the beam's top face
    ops += [px(hx + 2, cy - 19, "4"), px(hx + 3, cy - 19, "4"), px(hx + 4, cy - 18, "4"), px(hx + 5, cy - 17, "4"),
            px(hx + 6, cy - 16, "4"), px(hx + 6, cy - 15, "3"), px(hx + 3, cy - 20, "5")]
    # lens window: the pointer's red dot reflected in it (bright while cutting)
    firing = state in ("cut", "pierce")
    ops += [px(hx - 1, cy - 14, "f" if firing else "d")]
    if firing:
        # the cut lights the nozzle, the collar and the beam's underside around the head
        ops += [px(hx, cy - 2, "g"), px(hx - 1, cy - 4, "f"), px(hx + 1, cy - 4, "e"), px(hx - 1, cy - 3, "f")]
    return ops


def chain(cy):
    """The cable chain: fixed run along the left rail from the back, a U bend, and the run up to the beam end."""
    anchor, length = 31, 58
    end = cy - 9
    bend = (length + anchor + end) // 2
    x = L.RAIL_L - 5
    ops = []
    for y in range(anchor, bend - 1, 2):
        ops.append(line(x, y, x + 1, y, "B"))
        ops.append(line(x, y + 1, x + 1, y + 1, "1"))
    for y in range(end, bend - 1, 2):
        ops.append(line(x + 3, y, x + 4, y, "C"))
        ops.append(line(x + 3, y + 1, x + 4, y + 1, "A"))
    ops += [line(x, bend - 1, x + 4, bend - 1, "B"), line(x + 1, bend, x + 3, bend, "C"), px(x + 4, bend - 2, "C"),
            rect(x - 1, anchor - 2, 4, 3, "A"), px(x - 1, anchor - 2, "C")]
    return ops


def lamp(k, cutting):
    """Status lamp: steady amber while cutting, dim otherwise."""
    return [rect(161, 91, 3, 2, "e" if cutting else "b"), px(161, 91, "f" if cutting else "c")]


# ---------------------------------------------------------------- per-frame assembly
def shuttle_offset(k):
    """How far the sheets have moved left at frame k (see layout.SHUTTLE)."""
    i = k - L.SHUTTLE_START
    if i <= 0:
        return 0
    return L.SHUTTLE[i] if i < len(L.SHUTTLE) else L.PITCH


def fluid_frames(name, effect):
    recipe = json.loads((BUILD / f"{name}.json").read_text(encoding="utf-8"))
    return [f.get("ops", []) for f in recipe["frames"] if f["name"].rsplit("-", 1)[0] == effect]


def light_pool(cx, cy, big=1.0):
    """The cut lights the plywood around it in three rings: a gold core and a solid orange band shaded up the wood
    ramp (+4, +3), then an e ring and a sparse d ring in Bayer 4. Each only touches wood the inner rings left
    alone, and every ring is lighter than the wood under it."""
    wood = ["L", "K", "J", "I", "H"]
    w1, h1, w2, h2, w3, h3, w4, h4 = (round(v * big) for v in (1, 1, 3, 2, 7, 4, 12, 7))
    return [shade(cx - w1, cy - h1, 2 * w1 + 1, 2 * h1 + 1, 4, shape="ellipse", over=wood),
            shade(cx - w2, cy - h2, 2 * w2 + 1, 2 * h2 + 1, 3, shape="ellipse", over=wood),
            dither(cx - w3, cy - h3, 2 * w3 + 1, 2 * h3 + 1, "e", [0.85, 0.25], direction="radial", over=wood),
            dither(cx - w4, cy - h4, 2 * w4 + 1, 2 * h4 + 1, "d", [0.45, 0.0], direction="radial", over=wood)]


def cut_point(hx, cy, state):
    """The cut itself, the brightest pixels on the card; a pierce is one frame of a white plus."""
    if state == "pierce":
        return [px(hx - 1, cy, "*"), px(hx + 1, cy, "*"), px(hx, cy - 1, "*"), px(hx, cy + 1, "*"), px(hx, cy, "*"),
                px(hx - 2, cy, "g"), px(hx + 2, cy, "g"), px(hx, cy + 2, "g")]
    return [px(hx - 1, cy, "g"), px(hx + 1, cy, "g"), px(hx, cy + 1, "f"), px(hx, cy - 1, "g"), px(hx, cy, "R")]


def smoke_light(cx, cy):
    """Inside the smoke layer: a billow near the cut is lit from below as a solid warm band across the few rows just
    above the cut (each smoke tone to its own warm tone, lighter tones first); higher up the billows keep their grey,
    so they cool as they rise."""
    lx, ly = cx - L.SMOKE_X, cy - L.SMOKE_Y
    return [dither(lx - 9, ly - 5, 19, 5, c, 1.0, over=over)
            for c, over in (("f", ["x", "w"]), ("e", ["v"]), ("d", ["u"]))]


def cell_glow(hx, cy):
    """In the frame, under the machine: the cut's light spilling over the dark bed and back panel around it, two
    dithered molten rings (Bayer 4) that leave the wood to the light pool and the shadows to themselves."""
    dark = ["1", "2", "3", "A", "B"]
    return [dither(hx - 28, cy - 26, 57, 40, "a", [0.75, 0.0], direction="radial", over=dark),
            dither(hx - 16, cy - 16, 33, 26, "b", [0.85, 0.0], direction="radial", over=dark + ["a"])]


def warm_steps(x0, y0, length, centre, horizontal, steps, over):
    """Solid stepped segments of warm light along a 1 px edge, brightest at `centre`: steps is a list of
    (half-length, colour) from the inside out, each drawn under the inner ones."""
    ops = []
    for half, c in reversed(steps):
        a, b = max(x0 if horizontal else y0, centre - half), min((x0 if horizontal else y0) + length - 1, centre + half)
        if a > b:
            continue
        if horizontal:
            ops.append(dither(a, y0, b - a + 1, 1, c, 1.0, over=over))
        else:
            ops.append(dither(x0, a, 1, b - a + 1, c, 1.0, over=over))
    return ops


def machine_glow(hx, cy):
    """In the machine layer: the beam's underside and the rails' inner edges catch the cut's light in solid steps."""
    steel = ["1", "A", "B", "C"]
    ops = warm_steps(L.RAIL_L + 6, cy - 6, L.RAIL_R - L.RAIL_L - 6, hx, True, [(3, "e"), (6, "d")], steel)
    for inner in (L.RAIL_L + 5, L.RAIL_R):
        d = abs(hx - inner)
        if d <= 10:
            steps = [(1, "e"), (3, "d")] if d <= 5 else [(2, "d")]
            ops += warm_steps(inner, cy - 24, 30, cy - 9, False, steps, steel)
    return ops


def loop_frame(k, smoke, sprays, puffs):
    off = shuttle_offset(k)
    x, y, state, _ = T.head_at(k)
    hx, cy = L.card((round(x), round(y)))
    cutting = state in ("cut", "pierce")
    ops = []
    # sheets: the finished one, the one under the laser, and (while shuttling) the next one sliding in
    ops += [sheet_copy("tpl-done", L.FIN_X - off, L.SHEET_Y)]
    xs = [L.FIN_X - off]
    if off:
        ops += [sheet_copy("tpl-done", L.CUT_X - off, L.SHEET_Y), sheet_copy("tpl-fresh", L.CUT_X + L.PITCH - off,
                                                                              L.SHEET_Y)]
        xs += [L.CUT_X - off, L.CUT_X + L.PITCH - off]
    else:
        ops += cutting_sheet(k, L.CUT_X, L.SHEET_Y)
        xs += [L.CUT_X]
    # each sheet's shadow on the table or bed: below its edge and down its right side
    for sx in xs:
        ops += [shade(sx + 1, L.SHEET_Y + SH + EDGE, SW, 1, -1), shade(sx + SW, L.SHEET_Y + 1, 1, SH + EDGE, -1)]
    # the beam's shadow on whatever lies under it, a little right of it (moon from the upper left)
    ops += [shade(L.RAIL_L + 6, cy - 5, L.RAIL_R - L.RAIL_L - 6, 3, -1)]
    if cutting:
        ops += light_pool(hx, cy)
    # the kerf still glowing is light, not lit: it goes over the shading
    ops += kerf_ops(k, (L.CUT_X - off) if off else L.CUT_X, L.SHEET_Y, hot=True)
    if state in ("park", "rapid", "aim"):
        ops += [px(hx, cy, "d")]   # the red pointer dot
    ops += fan(k)
    # Draw order: the machine's frame, then the fumes (they rise from the cut in front of the beam), then the head,
    # the grille and the cut point itself, so the white pierce flash is never hidden by a spark.
    back = rails() + chain(cy) + gantry(hx, cy) + (machine_glow(hx, cy) if cutting else [])
    front = grille() + head(hx, cy, state, k) + lamp(k, cutting) + (cut_point(hx, cy, state) if cutting else [])
    layers = [
        {"name": "machine", "ops": back},
        {"name": "smoke", "x": L.SMOKE_X, "y": L.SMOKE_Y, "ops": smoke[k] + (smoke_light(hx, cy) if cutting else [])},
        {"name": "puff", "x": L.SMOKE_X, "y": L.SMOKE_Y, "ops": puffs[k]},
        {"name": "sparks", "x": L.SMOKE_X, "y": L.SMOKE_Y, "ops": [o for s in sprays for o in s[k]]},
        {"name": "head", "ops": front},
    ]
    return {"name": f"loop-{k:02d}", "duration": L.MS, "from": "bg", "ops": ops, "layers": layers}


def recipe():
    smoke_src = json.loads((ROOT / "out" / "fluids" / f"smoke{SUFFIX}.fluid.json").read_text(encoding="utf-8"))
    sims = [fluid_frames(f"smoke{SUFFIX}", e) for e in smoke_src["effects"]]
    smoke = [sum(ops, []) for ops in zip(*sims)]
    sprays = [fluid_frames(f"sparks{SUFFIX}", e) for e in ("spray-0", "spray-1")]
    puffs = fluid_frames(f"sparks{SUFFIX}", "puff")
    frames = [tpl_fresh()] + [tpl_part(n, s) for n, s in PARTS.items()] + [tpl_done(), background()]
    frames += [loop_frame(k, smoke, sprays, puffs) for k in range(L.FRAMES)]
    return {"version": 1, "name": f"nestbolt{SUFFIX}", "width": W, "height": H, "palette": PALETTE, "ramps": RAMPS,
            "frames": frames, "animations": {"loop": {"frames": [f"loop-{k:02d}" for k in range(L.FRAMES)]},
                                              "still": {"frames": [f"loop-{L.STILL:02d}"], "loop": False}}}


def main():
    out = ROOT / "out" / "recipes"
    out.mkdir(exist_ok=True)
    rec = recipe()
    (out / f"nestbolt{SUFFIX}.json").write_text(json.dumps(rec, separators=(",", ":")) + "\n", encoding="utf-8",
                                       newline="\n")
    nops = sum(len(f.get("ops", [])) + sum(len(l["ops"]) for l in f.get("layers", [])) for f in rec["frames"])
    (BUILD / f"still{SUFFIX}.txt").write_text(f"loop-{L.STILL:02d}\n", encoding="utf-8", newline="\n")
    print(f"recipe written: {len(rec['frames'])} frames, {nops} operations; still loop-{L.STILL:02d}")


if __name__ == "__main__":
    main()
