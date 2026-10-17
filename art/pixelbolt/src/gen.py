"""Generate recipes/pixelbolt-card.json: a static "bg" frame plus the 72-frame loop "loop-0".."loop-71".

Python lays out drawing operations, stamps and compiled fluid frames. Every pixel, including every dither, shade band,
outline and fluid pixel, is drawn by Pixelbolt when the recipe renders.
"""

import json
from pathlib import Path

import design as D
from lib import (ROOT, rect, ell, line, hline, vline, px, grid, stamp, dither, shade, text, outline, at,
                 compiled_frames, write_json)

BUILD = ROOT / "out" / "build"
FLUIDS = BUILD / "burst" if D.BURST else BUILD
NAME = "pixelbolt-card-burst" if D.BURST else "pixelbolt-card"
ANIM = "burst" if D.BURST else "loop"
PALETTE = {"$ref": "../../../palette.json"}
# Recipe ramps. Night 0-2 continue into the molten ramp, so shade bands round the hot metal turn the navy wall a
# deep forge red band by band; night 3-7 are their own ramp. Every other ramp is the master palette's.
RAMPS = [["0", "1", "2", "a", "b", "c", "d", "e", "f", "g"], ["3", "4", "5", "6", "7"], ["s", "t", "u", "v", "w", "x"],
         ["A", "B", "C", "D", "E", "F", "G"], ["H", "I", "J", "K", "L", "M"], ["N", "O", "P", "Q", "R"],
         ["h", "i", "j", "k", "l", "m", "n"], ["o", "p", "q", "r", "y", "z"], ["S", "T", "U", "V", "X", "Y"],
         ["8", "9", "W", "Z", "@", "#", "$"], ["%", "&", "+", "="]]

W, H, BY = D.W, D.H, D.BENCH_Y
MX, MY, MW, MH = D.MOULD
CX, CY = D.CAVITY
SW = D.STAR_W
SLOT0, SLOT1 = D.RACK_SLOTS
RAIL_Y = 79                      # top row of the rack rail; a star standing in a slot has its top at RAIL_Y - 28
STAR_Y = RAIL_Y - SW


def silhouette(rows, ch="#", fill="k"):
    return ["".join(fill if c == ch else "." for c in r) for r in rows]


def scaled(rows, s):
    """A symbol's rows at s times (the cavity outline shared with the fluid obstacle)."""
    return ["".join(c * s for c in r) for r in rows for _ in range(s)]


SYMBOLS = {
    "star": D.STAR_1X,                                  # the sprite, 1x; stamped at scale 4
    "star-sil": silhouette(D.STAR, fill="1"),           # its silhouette, for the cavity and heat ring
    "cavity": scaled(silhouette(D.STAR, fill="1"), D.SCALE),
}

# Glint: a two-pixel diagonal band (x + y = p, p + 1 inside the star), one shade op per row; p per glint frame.
GLINT_BAND = [8, 20, 30, 44]


# ------------------------------------------------------------------ static background
def wall():
    ops = [rect(0, 0, W, BY, "2")]
    for row, y in enumerate(range(9, BY, 12)):
        ops.append(hline(0, W - 1, y, "1"))
        off = 0 if row % 2 == 0 else 12
        for x in range(off, W, 24):
            ops.append(vline(x, y + 1, min(y + 11, BY - 1), "1"))
    ops.append(vline(0, 0, 8, "1"))
    for x in range(12, W, 24):
        ops.append(vline(x, 0, 8, "1"))
    ops.append(shade(0, 0, W, 22, -1, density=[0.75, 0.0], direction="down", over=["2"]))
    # Two quiet marks: a hairline crack low left of the mould, a scorch above the rack.
    for pts in (((64, 60), (66, 64), (65, 67), (68, 71)), ((171, 40), (174, 43), (173, 46))):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            ops.append(line(ax, ay, bx, by, "1"))
    return ops


CHECKER = [[0, 1], [1, 0]]
COOLING_ROW = [{"R": "g", "Q": "g", "P": "f", "O": "f", "N": "e"}, {"R": "f", "Q": "f", "P": "e", "O": "e", "N": "d"},
               {"R": "e", "Q": "d", "P": "d", "O": "c", "N": "c"}, {}]
# More of the forge's sprites, 1x, in its own metals: a key, a coin, a cut gem.
KEY = [".......", ".OO....", "O..O...", "O..OPPP", ".OO..P.", ".....PP", "......."]
COIN = [".......", "..OPO..", ".OQRPN.", ".OQPPN.", ".OPPPN.", "..NNN..", "......."]
GEM = [".......", ".efffe.", "dgffeec", ".deedc.", "..ddc..", "...c...", "......."]


def poster():
    """A sprite-sheet poster pinned to the wall: 7x7 cells on a transparency checker, ruled into a 4x2 grid. Top row:
    the star's cooling frames (white-hot to brass), this card's own animation. Bottom: a key, a coin, a gem and an
    empty cell, the forge's next jobs."""
    x0, y0 = 16, 24
    cols, rows, cell = 4, 2, 9
    w, h = cols * (cell + 1) + 3, rows * (cell + 1) + 3
    ops = [rect(x0 + 1, y0 + 1, w, h, "1"),                        # its shadow on the wall
           rect(x0, y0, w, h, "B"), hline(x0, x0 + w - 1, y0, "C"), vline(x0, y0, y0 + h - 1, "C")]
    gx, gy = x0 + 1, y0 + 1
    ops += [rect(gx, gy, w - 2, h - 2, "A"),
            rect(gx + 1, gy + 1, w - 4, h - 4, "3")]
    for r in range(rows):
        for c in range(cols):
            cx, cy = gx + 1 + c * (cell + 1), gy + 1 + r * (cell + 1)
            ops.append(dither(cx, cy, cell, cell, "4", 0.5, pattern=CHECKER, over=["3"]))
        ops.append(hline(gx + 1, gx + w - 4, gy + 1 + (r + 1) * (cell + 1) - 1, "A"))
    for c in range(1, cols):
        ops.append(vline(gx + c * (cell + 1), gy + 1, gy + h - 4, "A"))
    for c, remap in enumerate(COOLING_ROW):
        op = stamp(gx + 2 + c * (cell + 1), gy + 2, "star")
        if remap:
            op["remap"] = remap
        ops.append(op)
    for c, rows_ in enumerate((KEY, COIN, GEM)):
        ops.append(grid(gx + 2 + c * (cell + 1), gy + 2 + cell + 1, rows_))
    # Out of the forge light: the sheet sits a step down; its brass tacks catch the moon.
    ops.append(shade(gx, gy, w - 2, h - 2, -1, over=["g", "f", "e", "d", "c", "R", "Q", "P", "O", "N"]))
    ops += [px(x0 + 1, y0 + 1, "Q"), px(x0 + w - 2, y0 + 1, "P"), px(x0 + 1, y0 + h - 2, "P"),
            px(x0 + w - 2, y0 + h - 2, "O")]
    return ops


def bench():
    ops = [rect(0, BY, W, 3, "K"), hline(0, W - 1, BY, "L"), rect(0, BY + 3, W, H - BY - 3, "I"),
           hline(0, W - 1, BY + 3, "H"), hline(0, W - 1, H - 1, "H")]
    for (x0, x1, y) in ((70, 118, 90), (124, 176, 96), (8, 40, 97), (150, 190, 88)):
        ops.append(hline(x0, x1, y, "J"))
    ops += [px(118, 89, "J"), px(119, 89, "H"), px(176, 95, "J")]
    return ops


def ruler():
    """A steel rule on the bench front: a 7 px span marked 1x and a 28 px span marked 4x, etched dark."""
    x0, y0, w = 10, 86, 58
    ops = [rect(x0, y0, w, 9, "B"), hline(x0, x0 + w - 1, y0, "C"), hline(x0, x0 + w - 1, y0 + 8, "A"),
           vline(x0 + w - 1, y0, y0 + 8, "B"), hline(x0 + 1, x0 + w, y0 + 9, "H")]
    for k in range(0, w - 2, 2):
        ops.append(vline(x0 + 1 + k, y0 + 1, y0 + (1 if k % 4 else 2), "A"))
    a, b = x0 + 2, x0 + 26                       # the two spans start here
    ops += [vline(a, y0 + 1, y0 + 6, "A"), vline(a + 7, y0 + 1, y0 + 6, "A"),
            vline(b, y0 + 1, y0 + 6, "A"), vline(b + 28, y0 + 1, y0 + 6, "A")]
    ops += [text(a + 11, y0 + 1, "1×", "A"), text(b + 9, y0 + 1, "4×", "A")]
    return ops


HOOK_X = 89


def chain():
    """The chain from the ceiling, its hook, and the gooseneck hanger: a top bar and an arm down the pot's left side
    (the arm that carries the pivot is drawn in front of the pot, in crucible())."""
    cx = HOOK_X
    ops = []
    for y in range(0, 8, 4):
        ops += [rect(cx - 1, y, 3, 3, "C", filled=False), px(cx - 1, y, "D"), px(cx, y + 3, "B")]
    ops += [rect(cx - 1, 8, 3, 3, "C", filled=False), px(cx - 1, 8, "D")]
    px0, py0 = D.PIVOT
    ops += [rect(75, 11, cx - 75 + 2, 2, "C"), hline(75, cx + 1, 11, "D"), hline(76, cx + 1, 12, "B"),
            rect(75, 11, 2, py0 - 11, "C"), vline(75, 11, py0 - 1, "D"), vline(76, 13, py0 - 1, "B")]
    return ops


def background():
    return wall() + poster() + bench() + ruler() + chain()


# ------------------------------------------------------------------ per-frame parts
def stage(i):
    if i < D.STAGE_ORANGE:
        return "hot"
    if i < D.STAGE_RED:
        return "orange"
    if i < D.STAGE_BRONZE:
        return "red"
    if i < D.STAGE_GOLD:
        return "bronze"
    return "gold"


def poured(i):
    """True while the cavity holds metal (from the first impact until the star leaves)."""
    return D.IMPACT <= i < min(D.POP)


WALL_KEYS = ["1", "2", "a", "b"]
WOOD_KEYS = ["H", "I", "J", "K", "L"]


def pool(cx, cy, rx, ry, over, steps=1, feather=True):
    """One band of a light pool: a checkered feather ring, then a solid ellipse (shade moves colours along their
    ramps). Stacked bands make a banded radial pool."""
    solid = [shade(cx - rx, cy - ry, 2 * rx, 2 * ry, steps, shape="ellipse", over=over)]
    if not feather:
        return solid
    return [shade(cx - rx - 4, cy - ry - 4, 2 * rx + 8, 2 * ry + 8, steps, shape="ellipse", density=0.25, over=over),
            shade(cx - rx - 2, cy - ry - 2, 2 * rx + 4, 2 * ry + 4, steps, shape="ellipse", density=0.5, over=over)] + solid


def glow(i):
    """Warm light from the crucible (always) and from the cast metal (as hot as it is): banded radial pools on the
    wall (night runs into the molten ramp) and the bench (wood steps lighter)."""
    px0, py0 = D.PIVOT
    ops = pool(px0, py0 - 2, 12, 10, ["1", "2"])
    if mouth_remap(i) is None:
        ops += pool(px0 + 2, py0 - 2, 16, 13, ["1", "2"])
    gx, gy = 102, 64
    level = 0
    if D.POUR_START + 2 <= i < D.IMPACT:
        level = 1 if i < D.POUR_START + 5 else 2
    elif poured(i):
        # the rings go out from the outside in, one at a time, a beat after each cooling step
        if i < D.STAGE_RED + 2:
            level = 3
        elif i < D.STAGE_BRONZE - 1:
            level = 2
        elif i < D.STAGE_GOLD + 1:
            level = 1
    # the outermost lit ring loses its feathers one frame before it goes out
    fading = poured(i) and i in (D.STAGE_RED + 1, D.STAGE_BRONZE - 2, D.STAGE_GOLD)
    # innermost first: level 1 lights the small band, each level adds the next ring out
    for band, (rx, ry, brx, bry) in enumerate(((16, 14, 18, 3), (22, 18, 28, 5), (30, 23, 38, 6))):
        if band < level:
            ops += pool(gx, gy, rx, ry, WALL_KEYS, feather=band > 0 and not (fading and band == level - 1))
            if band < 2:
                ops += pool(gx, BY + 2, brx, bry, WOOD_KEYS)
    return ops


# The pot's mouth: crusted dark red at rest, warming as it tips, white-hot through the pour, crusting again after.
CRUST = {"g": "c", "f": "b", "e": "b", "d": "a"}
WARM = {"g": "e", "f": "d", "e": "c", "d": "b"}
WARMER = {"g": "f", "f": "e", "e": "d", "d": "c"}
# Hand-corrected pour poses: start from the pose compiler's rotation of the dry pot (pot-dry-r38, pot-dry-r52), keep
# its silhouette, band and lip, and paint the metal by hand: a flat g surface row across the mouth with f below it,
# running to the beak; above the surface the dark inner wall (H, I) stays. (row, first col, last col, key)
HAND_POOL = {
    "tilt34": [(7, 14, 16, "g"), (8, 15, 17, "f"), (9, 17, 17, "e")],
    "tilt45": [(0, 10, 10, "K"), (0, 11, 12, "M"), (1, 10, 10, "K"), (1, 11, 12, "I"),
               (7, 15, 18, "g"), (8, 16, 19, "f"), (9, 17, 19, "f"), (10, 18, 19, "e"), (11, 19, 19, "e"),
               (9, 20, 20, "M"), (10, 20, 20, "M")],
}


def hand_pot(pose, rows):
    rows = [list(r) for r in rows]
    for (y, a, b, k) in HAND_POOL[pose]:
        for x in range(a, b + 1):
            rows[y][x] = k
    return ["".join(r) for r in rows]


# Tilted poses: how many of the lowest rows of the pot's visible inside are under the metal (the pool deepens toward
# the lip as the pot tips; at the pour angle it reaches the spout).
LEVEL = {"tilt20": 2}


def mouth_remap(i):
    pours = [f for f in range(D.FRAMES) if D.CRUCIBLE[f] != "tilt0"]
    first, last = pours[0], pours[-1]
    if i < first or i > last + 6:
        return CRUST
    if i < first + 2:
        return WARM
    if i > last + 4:
        return WARM
    if i > last + 2:
        return WARMER
    return None


def crucible(i):
    pose = D.CRUCIBLE[i]
    frames, symbols = CRUCIBLE
    ox, oy = D.PIVOT[0] - D.POSE_ORIGIN[0], D.PIVOT[1] - D.POSE_ORIGIN[1]
    ops = at(frames[pose], ox, oy)
    remap = mouth_remap(i)
    if remap:
        ops[0] = dict(ops[0], remap=remap)
    if pose in HAND_POOL:
        ops[0] = dict(ops[0], symbol=f"pot-hand-{pose}")
    if pose in LEVEL:
        # The metal inside a tipped pot stays level: recolour the inside below a level line.
        stamp_op = ops[0]
        rows = symbols[stamp_op["symbol"]]
        inside = [y for y, r in enumerate(rows) if "H" in r or "I" in r]
        ly = stamp_op["y"] + max(inside) - LEVEL[pose] + 1
        ops += [dither(ox, ly, 48, 1, "g", 1.0, over=["H", "I"]), dither(ox, ly + 1, 48, 2, "f", 1.0, over=["H", "I"]),
                dither(ox, ly + 3, 48, 8, "e", 1.0, over=["H", "I"])]
    # The hanger's lower arm grips the pot's pivot boss, in front of the pot; it glows red where it meets the heat.
    bx, by = D.PIVOT
    ops += [rect(75, by, bx - 75, 2, "C"), hline(75, bx - 1, by, "D"), hline(77, bx - 1, by + 1, "B"),
            dither(bx - 8, by, 4, 2, "c", 0.5, over=["C", "D", "B"]), rect(bx - 4, by, 3, 2, "c"),
            hline(bx - 2, bx - 1, by, "d"),
            rect(bx - 1, by - 1, 3, 3, "O"), px(bx - 1, by - 1, "Q"), px(bx + 1, by + 1, "N")]
    return ops


LIP_COOL = ["f", "e", "d", "d", "c", "c"]       # frames after the pour pose ends


def lip(i):
    """The spout glows where the metal runs over it: white-hot through the pour, cooling a few frames after."""
    pose = D.CRUCIBLE[i]
    sx, sy = CRUCIBLE_SPOUT[pose]
    sx, sy = sx + D.PIVOT[0] - D.POSE_ORIGIN[0], sy + D.PIVOT[1] - D.POSE_ORIGIN[1]
    pours = [f for f in range(D.FRAMES) if D.CRUCIBLE[f] == "tilt45"]
    if pose == "tilt45":
        c = "g"
    elif i < pours[0]:
        c = {pours[0] - 2: "e", pours[0] - 1: "f"}.get(i)
    else:
        k = i - pours[-1] - 1
        c = LIP_COOL[k] if k < len(LIP_COOL) else None
    if not c:
        return []
    ops = [px(sx - 1, sy, c), px(sx - 2, sy - 1, c)]
    if c in "gf":
        ops += [px(sx - 1, sy - 1, "f"), px(sx - 2, sy, "e")]
    if pose == "tilt45" and D.POUR_START <= i < D.POUR_START + D.POUR_END:
        # the metal pours over the beak and joins the stream below it
        ops += [hline(sx - 2, sx, sy + 1, "g"), hline(sx - 2, sx + 1, sy + 2, "g"), px(sx - 2, sy + 2, "f")]
    return ops


def crucible_layer(i):
    """The pot, its bail and boss. While the cast metal below glows, the pot's underside catches its light."""
    ops = crucible(i)
    ops[1:1] = lip(i)
    if (poured(i) or D.POUR_START <= i) and i < D.STAGE_BRONZE:
        c = "c" if stage(i) in ("hot", "orange") else "b"
        ops.insert(1, outline(c, position="inside", directions=["...", "...", ".x."]))
    return {"name": "crucible", "ops": ops}


def mould(i):
    """Two steel halves; each slides out by D.OPEN[i] px. Face D with an etched dot grid on the cast star's 4 px
    pitch, moonlit top and left edges, a dark parting line, a brass latch over the gate."""
    o = D.OPEN.get(i, 0)
    ops = []
    for side, x0, x1, shift in (("l", MX, D.PARTING - 1, -o), ("r", D.PARTING, MX + MW - 1, o)):
        a, b = x0 + shift, x1 + shift
        w = b - a + 1
        ops += [rect(a, MY, w, MH, "C"), hline(a, b, MY, "D"), hline(a, b, MY + MH - 1, "A"),
                hline(a, b, MY + MH - 2, "B")]
        if side == "l":
            ops += [vline(a, MY, MY + MH - 1, "D"), vline(b, MY + 1, MY + MH - 2, "B")]
        else:
            ops += [vline(a, MY + 1, MY + MH - 2, "B"), vline(b, MY, MY + MH - 1, "A")]
        ops.append(dither(a + 1, MY + 1, w - 2, MH - 3, "B", 0.5, pattern=[[0, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1],
                                                                            [1, 1, 1, 1]],
                          offset=[-shift, 2], over=["C"]))
        # brass bolts at the outer top and bottom corners
        bx = a + 2 if side == "l" else b - 2
        ops += [px(bx, MY + 2, "P"), px(bx, MY + MH - 4, "O")]
    # Parting line (closed) or the gap (open).
    if o == 0:
        ops.append(vline(D.PARTING - 1, MY + 4, MY + MH - 2, "A"))
    return ops


def cavity(i):
    """The gate's chamfer and the star cavity, each half's share, dark; its upper-left inner walls in shadow."""
    o = D.OPEN.get(i, 0)
    ops = []
    g0, g1 = D.TOP_POINT
    for (lo, hi, y) in ((g0 - 3, g1 + 3, MY), (g0 - 2, g1 + 2, MY + 1), (g0 - 1, g1 + 1, MY + 2), (g0, g1, MY + 3)):
        ops.append(hline(lo - o, D.PARTING - 1 - o, y, "1"))
        ops.append(hline(D.PARTING + o, hi + o, y, "1"))
    half = D.PARTING - CX
    ops += [{"op": "copy", "x": CX - o, "y": CY, "symbol": "cavity", "sx": 0, "sy": 0, "w": half, "h": SW},
            {"op": "copy", "x": D.PARTING + o, "y": CY, "symbol": "cavity", "sx": half, "sy": 0, "w": SW - half,
             "h": SW}]
    ops.append(outline("0", position="inside", directions=[".x.", "x..", "..."]))
    layer = {"name": "cavity", "ops": ops}
    # Lit from inside: once the stream enters, the cavity walls glow with the metal's light (and bubbles the plunge
    # traps show that glow, not the dark steel).
    if D.POUR_START + 4 <= i < D.IMPACT:
        layer["palette"] = {"1": "a", "0": "1"}
    elif poured(i) and stage(i) in ("hot", "orange"):
        layer["palette"] = {"1": "d", "0": "c"}
    return layer


def mould_rim(i):
    """The mould's top edge round the gate catches the light of the stream and the hot metal."""
    if not (D.POUR_START + 4 <= i < D.STAGE_RED):
        return []
    g0, g1 = D.TOP_POINT
    ops = [hline(g0 - 9, g1 + 9, MY, "c")]
    if stage(i) == "hot":
        ops += [hline(g0 - 6, g1 + 6, MY, "d"), px(g0 - 10, MY, "b"), px(g1 + 10, MY, "b")]
    return ops


def latch(i):
    g0, g1 = D.TOP_POINT
    if D.LATCH_UP[0] <= i < D.LATCH_UP[1]:
        return [rect(g0 - 11, MY - 4, 8, 2, "C"), hline(g0 - 11, g0 - 4, MY - 4, "E"), vline(g0 - 4, MY - 2, MY - 1, "B"),
                px(g0 - 10, MY - 3, "P")]
    return [rect(g0 - 11, MY - 2, 9, 2, "C"), hline(g0 - 11, g0 - 3, MY - 2, "E"), px(g0 - 11, MY - 1, "B"),
            px(g0 - 10, MY - 1, "P")]


COOL_LIQUID = {"hot": None, "orange": {"g": "f", "f": "e", "e": "e", "d": "d"},
               "red": {"g": "e", "f": "d", "e": "d", "d": "c"}, "bronze": {"g": "P", "f": "O", "e": "O", "d": "N"},
               "gold": {"g": "Q", "f": "P", "e": "O", "d": "N"}}
COOL_STAR = {"red": {"R": "f", "Q": "e", "P": "d", "O": "d", "N": "c"},
             "bronze": {"R": "Q", "Q": "P", "P": "O", "O": "N", "N": "N"}, "gold": None}


def liquid(i):
    """The pour, placed on its card frames; it holds its last frame until the solid star replaces it."""
    if i < D.POUR_START or i >= min(D.POP):
        return None
    k = min(i - D.POUR_START, len(POUR) - 1)
    ops = at([o for o in POUR[k] if o["op"] == "grid"], D.POUR_BOX[0], D.POUR_BOX[1])
    layer = {"name": "liquid", "ops": ops}
    pal = COOL_LIQUID[stage(i)]
    if pal:
        layer["palette"] = pal
    return layer


def heat_ring(i):
    """While the metal is hot, the steel round the cavity glows: the star's silhouette outlined, then removed."""
    if not poured(i) or stage(i) in ("bronze", "gold"):
        return None
    c = {"hot": "c", "orange": "b", "red": "a"}[stage(i)]
    return {"name": "heat", "ops": [stamp(CX, CY, "star-sil", scale=D.SCALE), outline(c),
                                     {"op": "replace", "from": "1", "to": "transparent"}]}


def star_ops(x, y, st, glint_k=None):
    ops = [stamp(x, y, "star", scale=D.SCALE)]
    if st == "gold":
        ops.append(outline("N", position="inside", directions=["...", "..x", ".xx"]))
    if glint_k is not None:
        p = GLINT_BAND[glint_k]
        width = 3 if glint_k in (1, 2) else 2
        for r in range(SW):
            lo, hi = max(0, p - r), min(SW - 1, p - r + width - 1)
            if lo <= hi:
                ops.append(shade(x + lo, y + r, hi - lo + 1, 1, 2))
    return ops


def cast_star(i):
    """The solid star: in the cavity from STAGE_RED, then popping out and landing in rack slot 0."""
    if D.STAGE_RED <= i < min(D.POP):
        x, y = CX, CY
    elif i in D.POP:
        x, y = D.POP[i]
    elif D.LAND <= i < min(D.ADVANCE):
        x, y = SLOT0, STAR_Y + D.HOP.get(i, 0)
    else:
        return None
    st = stage(i)
    gk = i - D.GLINT[0] if D.GLINT[0] <= i < D.GLINT[1] else None
    layer = {"name": "cast", "ops": star_ops(x, y, st, gk)}
    if COOL_STAR.get(st):
        layer["palette"] = COOL_STAR[st]
    if gk == 2:
        layer["ops"].append(px(x + 15, y + 15, "*"))
    return layer


def rack(i):
    """Brass rail with slot posts; earlier stars stand in it. Moves one slot (32 px) on D.ADVANCE frames."""
    shift = D.ADVANCE.get(i, 0)
    ops = [rect(121, RAIL_Y, 71, 3, "O"), hline(121, 191, RAIL_Y, "P"), hline(121, 191, RAIL_Y + 2, "N"),
           vline(121, RAIL_Y, RAIL_Y + 2, "P")]
    for k in range(-1, 3):
        x = 121 + 32 * k + shift
        if x >= 121:
            ops += [rect(x, RAIL_Y - 5, 2, 5, "O"), vline(x, RAIL_Y - 5, RAIL_Y - 1, "Q")]
    # The far end of the rack is out of the forge light (rail and posts; the stars dim whole, below).
    ops.append(shade(155, RAIL_Y - 6, 37, 9, -2))
    # Stars standing in the rack: slot 1 always; slot 0 holds the new star only while it rides the advance. A star
    # dims whole once its middle has crossed into the shadow, never half and half.
    stars = [SLOT1 + shift] if SLOT1 + shift < W - 4 else []
    if i in D.ADVANCE:
        stars.append(SLOT0 + shift)
    for x in stars:
        star = star_ops(x, STAR_Y, "gold")
        moved = x - SLOT0
        if x >= SLOT1 - 4 or moved >= 30:
            star[0] = dict(star[0], remap=DIM)
        elif moved >= 20:
            star[0] = dict(star[0], remap=DIM1)
        ops += star
    return {"name": "rack", "ops": ops}


DIM = {"R": "P", "Q": "O", "P": "N", "O": "N", "N": "N"}
DIM1 = {"R": "Q", "Q": "P", "P": "O", "O": "N", "N": "N"}


def smoke(i):
    """The smoke sim. Its undersides (the sim's light field, a thin rim drawn d) catch the hot metal's light only
    within 8 px of the gate, d with e at the gate itself; elsewhere the rim takes the body's own grey, so no dark line
    traces a billow. Below y 20 the moonlit tops are held at v, so the smoke never outshines the metal."""
    ops = at(SMOKE[i], D.SMOKE_BOX[0], D.SMOKE_BOX[1])
    gy = MY
    st = stage(i) if poured(i) else "cold"
    if st in ("hot", "orange", "red"):
        # the hot gate lights a new billow from below: its lowest rows take a dithered warm cast
        ops.append(dither(96, gy - 3, 28, 3, "d" if st == "hot" else "c", 0.5, over=["u", "v", "w"]))
    # below y 20 the brightest grey is held a step down, so smoke never outshines the metal
    ops.append(dither(0, 20, W, gy - 20, "v", 1.0, over=["w"]))
    return {"name": "smoke", "ops": ops}


def dust(i):
    k = i - D.LAND
    if 0 <= k < len(DUST):
        return {"name": "dust", "ops": at(DUST[k], D.DUST_BOX[0], D.DUST_BOX[1])}
    return None


def embers(i):
    return {"name": "embers", "ops": at(EMBERS[i % len(EMBERS)], D.EMBER_BOX[0], D.EMBER_BOX[1])}


# ------------------------------------------------------------------ assembly
def load():
    global POUR, SMOKE, DUST, EMBERS, CRUCIBLE
    POUR, _ = compiled_frames(FLUIDS / "pour.json", "pour")
    SMOKE, _ = compiled_frames(FLUIDS / "smoke.json", "smoke")
    DUST, _ = compiled_frames(FLUIDS / "dust.json", "dust")
    EMBERS, _ = compiled_frames(FLUIDS / "embers.json", "embers")
    rec = json.loads((BUILD / "crucible.json").read_text(encoding="utf-8"))
    frames = {f["name"]: [o for layer in f["layers"] for o in layer["ops"]] for f in rec["frames"]}
    global CRUCIBLE_SPOUT
    CRUCIBLE_SPOUT = {f["name"]: f["points"]["spout"] for f in rec["frames"]}
    global CRUCIBLE_POINTS
    CRUCIBLE_POINTS = {f["name"]: f["points"] for f in rec["frames"]}
    syms = {k: v for k, v in rec["symbols"].items() if k.startswith("pot")}
    for pose in HAND_POOL:
        stamp_op = frames[pose][0]
        syms[f"pot-hand-{pose}"] = hand_pot(pose, rec["symbols"][stamp_op["symbol"]])
    CRUCIBLE = (frames, syms)
    SYMBOLS.update(syms)


def frame(i):
    layers = [embers(i), smoke(i), crucible_layer(i), {"name": "mould", "ops": mould(i) + mould_rim(i) + latch(i)},
              cavity(i), heat_ring(i), liquid(i), rack(i), cast_star(i), dust(i)]
    return {"name": f"{ANIM}-{i}", "duration": D.MS, "from": "bg", "ops": glow(i), "layers": [l for l in layers if l]}


def recipe():
    load()
    frames = [{"name": "bg", "duration": D.MS, "ops": background()}] + [frame(i) for i in range(D.FRAMES)]
    animations = {ANIM: {"frames": [f"{ANIM}-{i}" for i in range(D.FRAMES)]}}
    if not D.BURST:
        animations["still"] = {"frames": [f"loop-{D.STILL}"], "loop": False}
    return {"version": 1, "name": NAME, "width": W, "height": H, "palette": PALETTE, "ramps": RAMPS,
            "symbols": SYMBOLS, "frames": frames, "animations": animations}


if __name__ == "__main__":
    write_json(ROOT / "out" / "recipes" / f"{NAME}.json", recipe())
    print("recipe written")
