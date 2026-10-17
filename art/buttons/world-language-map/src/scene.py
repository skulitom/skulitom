"""World Language Map tile (68x42, narrow 56x42): a desk globe in a brass meridian ring on a ledge of the workbench,
moonlit from the upper left, with a speech bubble holding the character 文 ("language", "writing") beside it. Once a
cycle someone flicks the globe: the bubble pops, the globe spins one full turn and eases to a stop, and a new bubble
pops up with a one-frame bright overshoot.

The world map is a hand-drawn 48x15 grid (equirectangular, land 'k'). Each frame Python looks up which map pixel each
globe pixel shows (an orthographic lookup, the same job as rotating a sprite) and emits that as a grid of palette
keys; the globe's light, terminator and specular are Pixelbolt shade operations on the ink and mint ramps.

Frames (70 ms): 0-1 rest, 2-3 the bubble bursts, 2-3 the globe rocks back, 4-16 the flick (one turn and a little more,
fast start, ease out), 17 it settles back, 17-19 the new bubble pops in (18 is the overshoot), 21 the hold (the still).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from pb import rect, ell, line, px, pxs, grid, shade, dither, shift  # noqa: E402
from bench import ledge_layer, pool, contact_shadow  # noqa: E402

NAME, KIND = "world-language-map", "tile"
FRAMES = 22
VARIANTS = {"regular": (68, 42), "narrow": (56, 42)}
TITLE = "World Language Map"
DESC = ("Pixel art made with Pixelbolt: a desk globe in a brass meridian ring on a ledge of the workbench, with a "
        "speech bubble beside it; the globe is flicked, spins one turn and stops, and the bubble pops up again.")

LEDGE_Y = 23
# Regular layout (canvas x); the narrow layout is the same scene 6 px to the left with a shorter ledge.
GX, GY, R = 28, 12, 7.5            # globe centre pixel and radius: the disc spans GX-7..GX+7; the ring rows 3-21
RING_R = 9.5

# Land spans per map row (inclusive columns, 48 columns from 180W eastwards; 15 rows from the north pole).
LAND = [
    [(18, 20)],
    [(4, 12), (17, 20), (25, 26), (29, 45)],
    [(2, 15), (18, 19), (23, 28), (29, 46)],
    [(5, 16), (22, 28), (29, 43), (45, 45)],
    [(7, 15), (22, 29), (30, 41)],
    [(9, 13), (21, 30), (30, 32), (33, 35), (37, 40)],
    [(12, 13), (21, 28), (34, 34), (38, 39)],
    [(13, 18), (25, 28), (37, 41)],
    [(13, 19), (25, 29), (40, 43)],
    [(14, 18), (25, 28), (30, 30), (39, 44)],
    [(15, 17), (26, 27), (41, 43)],
    [(15, 16), (46, 46)],
    [(16, 16)],
    [(4, 9), (14, 21), (28, 40)],
    [(0, 47)],
]
MAP_W, MAP_H = 48, 15
REST_LON = -70.0                    # the meridian facing the viewer at rest: the Americas, ocean either side


def land_at(col, row):
    col %= MAP_W
    return any(a <= col <= b for a, b in LAND[row])


def spin(i):
    """The globe's turn on frame i, in degrees. Anticipation: it rocks back a little as the hand catches it (2-3);
    the flick (fast start, quadratic ease out) carries it a few degrees past the full turn (4-16), and it settles back (17)."""
    if i <= 1 or i >= 18:
        return 0.0 if i <= 1 else 360.0
    if i == 2:
        return -5.0
    if i == 3:
        return -9.0
    if i == 17:
        return 361.0
    t = (i - 3) / (16 - 3)
    return -9.0 + 373.0 * (1 - (1 - t) ** 2)


def disc(cx, cy, turn):
    """The globe's surface on this frame as grid rows: 'W' ocean, 'k' land (orthographic lookup of the map)."""
    x0, y0 = cx - 7, cy - 7
    rows = []
    for y in range(y0, y0 + 15):
        row = ""
        for x in range(x0, x0 + 15):
            nx, ny = (x + 0.5 - (cx + 0.5)) / R, (y + 0.5 - (cy + 0.5)) / R
            d = nx * nx + ny * ny
            if d > 1.0:
                row += "."
                continue
            nz = math.sqrt(1 - d)
            lon = math.degrees(math.atan2(nx, nz)) + REST_LON - turn
            lat = math.degrees(math.asin(-ny))
            col = int(math.floor((lon + 180.0) / 360.0 * MAP_W))
            r = min(MAP_H - 1, max(0, int((90.0 - lat) / 180.0 * MAP_H)))
            row += "k" if land_at(col, r) else "W"
        rows.append(row)
    return x0, y0, rows


def globe(cx, cy, turn):
    x0, y0, rows = disc(cx, cy, turn)
    ops = [grid(x0, y0, rows)]
    # Light: the moon lifts the upper-left of the sphere a step; the lower-right falls a step into the terminator and
    # its last crescent one more; a two-pixel varnish specular sits on the lit side.
    ops += [shade(x0 - 3, y0 - 3, 13, 13, 1, shape="ellipse", over=["W", "k"]),
            shade(x0 + 5, y0 + 5, 14, 14, -1, shape="ellipse", over=["W", "k", "Z", "l"]),
            shade(x0 + 9, y0 + 9, 10, 10, -1, shape="ellipse", over=["9", "j"]),
            px(x0 + 4, y0 + 3, "$"), px(x0 + 3, y0 + 4, "#")]
    return ops


def ring(cx, cy):
    """The brass meridian ring round the globe, with its two pins; moonlit on its upper-left arc, in shadow lower
    right."""
    return [ell(cx - 9, cy - 9, 19, 19, "O", filled=False),
            # Upper-left arc catches the moon.
            shade(cx - 10, cy - 10, 11, 11, 1, shape="ellipse", over=["O"]),
            shade(cx + 1, cy + 1, 10, 10, -1, shape="ellipse", over=["O"]),
            px(cx, cy - 9, "Q"), px(cx, cy - 8, "P"), px(cx, cy + 9, "N")]


def stand(cx, base_y):
    """A turned wooden foot on the ledge that the ring's bottom pin sits in (base_y is the foot's row)."""
    return [rect(cx - 4, base_y, 9, 1, "K"), line(cx - 4, base_y, cx - 2, base_y, "L"),
            px(cx + 4, base_y, "J"), px(cx - 5, base_y, "J"), px(cx + 5, base_y, "I"), px(cx, base_y, "N")]


GLYPH = ["...x...", "xxxxxxx", ".x...x.", "..x.x..", "...x...", ".xx.x..", "x....xx"]          # 文


def bubble(bx, by, state):
    """The speech bubble (10x7 plus its tail) at (bx, by). state: 'rest', 'burst1', 'burst2', 'gone', 'seed',
    'over' (the one bright overshoot frame), 'settle'."""
    if state == "gone":
        return []
    if state == "burst1":
        # The bubble breaks into four motes flying out from its centre.
        return pxs([(bx + 2, by + 1), (bx + 8, by + 1), (bx + 1, by + 6), (bx + 9, by + 5)], "w") + \
            [rect(bx + 3, by + 2, 4, 3, "v"), px(bx + 4, by + 3, "x")]
    if state == "burst2":
        return pxs([(bx + 1, by), (bx + 10, by), (bx, by + 7), (bx + 11, by + 6)], "u")
    if state == "seed":
        return [rect(bx + 1, by + 4, 3, 3, "v"), px(bx + 1, by + 4, "w"), px(bx, by + 7, "v")]
    fill, edge_lit, edge_dark, ink = "x", "x", "w", "W"
    x0, y0, w, h = bx, by, 11, 9
    if state == "over":
        x0, y0, w, h = bx - 1, by - 1, 13, 11
        fill, edge_lit, edge_dark, ink = "G", "*", "x", "Z"
    ops = [rect(x0 + 1, y0, w - 2, h, fill), rect(x0, y0 + 1, w, h - 2, fill),
           line(x0 + 1, y0, x0 + w - 2, y0, edge_lit), line(x0, y0 + 1, x0, y0 + h - 2, edge_lit),
           line(x0 + w - 1, y0 + 2, x0 + w - 1, y0 + h - 2, edge_dark), line(x0 + 2, y0 + h - 1, x0 + w - 2, y0 + h - 1, edge_dark),
           px(x0 + w - 2, y0 + h - 2, edge_dark),
           # The tail, pointing down-left at the globe.
           px(x0 + 1, y0 + h, edge_dark), px(x0, y0 + h + 1, "v")]
    if state != "over":
        # A smoke edge round the pale body so it sits on the night wall without glowing.
        ops += [line(x0 + 1, y0 - 1, x0 + w - 2, y0 - 1, "v"), line(x0 - 1, y0 + 1, x0 - 1, y0 + h - 2, "v"),
                line(x0 + w, y0 + 1, x0 + w, y0 + h - 2, "v"), line(x0 + 1, y0 + h, x0 + w - 2, y0 + h, "v"),
                px(x0 + 1, y0 + h, edge_dark)]
    gx = x0 + (w - 7) // 2
    gy = y0 + (h - 7) // 2
    ops.append(grid(gx, gy, [r.replace("x", ink) for r in GLYPH]))
    return ops


def bubble_state(i):
    return {2: "burst1", 3: "burst2", 17: "seed", 18: "over", 19: "settle"}.get(
        i, "gone" if 4 <= i <= 16 else "rest")


def scene(i, dx, ledge):
    cx, cy = GX + dx, GY
    ops = []
    on_ledge = contact_shadow(cx + 0.5, LEDGE_Y, 6)
    layers = [ledge_layer(ledge[0], ledge[1], LEDGE_Y, on_ledge),
              {"name": "globe", "ops": ring(cx, cy) + globe(cx, cy, spin(i)) + stand(cx, LEDGE_Y - 1)},
              {"name": "bubble", "ops": bubble(cx + 12, 4, bubble_state(i))}]
    return ops, layers


def frame_ops(i, variant):
    w = VARIANTS[variant][0]
    dx = 0 if variant == "regular" else -6
    ledge = (14, 53) if variant == "regular" else (11, 45)
    ops, layers = scene(i, dx, ledge)
    return {"ops": [rect(0, 0, w, 42, "2")] + ops, "layers": layers}
