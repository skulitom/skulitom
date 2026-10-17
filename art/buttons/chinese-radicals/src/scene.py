"""Chinese Radicals tile (68x42, narrow 56x42): a practice sheet propped on a ledge of the workbench, the radical 木
printed on it in pink for tracing inside a pink border, a red seal in its corner, a calligraphy brush lying on the ledge
beside it. Once a cycle the brush lifts, inks the radical's first stroke, the horizontal 横 (entering at the upper left,
pressing, drawing the stroke left to right and pausing at its end) and is laid down again; the wet ink glistens, then
dries matt and stays until the next cycle, when it fades into the paper as the brush returns.

The ink is a Pixelbolt liquid simulation (FLIP, zero gravity because the sheet faces us like a page, surface tension
1.3): a chain of short emitter windows lays the ink along the brush's path, tension rounds the press and the end bead
and keeps the stroke whole. Its wet sheen is the simulation's own `light` look; drying is a palette change on the ink
layer, the shape freezes once it starts to dry, and the old stroke fades by palette steps (1, t, v) as the next begins.

Frames (70 ms): 0-2 the old stroke fades as the brush lifts and sweeps up, 3-12 the stroke (press 3-5, travel 5-10,
pause 11-13), 13-16 the brush is laid down, 14-18 the ink dries, 21 the hold (the still).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from pb import rect, line, px, pxs, dither, shade, erase, fluid_frames  # noqa: E402
from bench import ledge_layer, contact_shadow  # noqa: E402

NAME, KIND = "chinese-radicals", "tile"
FRAMES = 22
VARIANTS = {"regular": (68, 42), "narrow": (56, 42)}
TITLE = "Chinese Radicals"
DESC = ("Pixel art made with Pixelbolt: a calligraphy practice sheet with the radical 木 printed in pink for tracing; "
        "a brush inks its first stroke in simulated wet ink, which glistens and dries matt.")

LEDGE_Y = 23
SW, SH = 20, 18                       # the sheet; its bottom row stands on the ledge
INK_W, INK_H = 20, 10                 # the ink simulation's canvas, at the sheet's top-left
# The brush tip's path in sheet coordinates, frame by frame: rest, the swoop, the stroke, the lift.
REST = (22.0, 17.0)                   # lying on the ledge beside the sheet, its tip towards it
PATH = {0: (22.0, 16.0), 1: (15.0, 10.0), 2: (6.0, 6.0), 3: (3.5, 6.0), 4: (4.0, 6.0), 5: (6.0, 6.2), 6: (8.0, 6.1),
        7: (10.0, 5.9), 8: (12.0, 5.7), 9: (14.0, 5.7), 10: (15.5, 6.0), 11: (16.2, 6.3), 12: (16.8, 6.6),
        13: (18.0, 6.5), 14: (20.0, 10.0), 15: (21.5, 14.0), 16: (22.0, 16.0)}
POSE = {0: "flat", 1: "low", 15: "low", 16: "flat"}   # the rest is upright from 2 to 14, flat from 17
SMEAR = {}


def pose(i):
    if i in POSE:
        return POSE[i]
    return "upright" if 2 <= i <= 14 else "flat"


def tip(i):
    return PATH.get(i, REST)


# ---------------------------------------------------------------- the ink (a liquid simulation)
def sources():
    def lay(name, at, r, s, e, v=(0.0, 0.0)):
        return {"name": name, "at": list(at), "radius": r, "rate": 1, "start": s, "end": e, "velocity": list(v)}

    emitters = [
        # The press: the brush comes in from the upper left and its heel swells a blot there, so the stroke's entry slants.
        lay("press", (3.4, 4.6), 1.0, 3, 4, (0.15, 0.1)),
        lay("swell", (3.9, 4.9), 1.6, 4, 6, (0.1, 0.1)),
    ]
    # The body thins as it runs right (the brush lifts a little), laid a frame or two behind the tip.
    for k, y in enumerate((5.9, 5.9, 5.8, 5.7, 5.55, 5.4, 5.3, 5.3, 5.45)):
        emitters.append(lay(f"lay-{k + 1}", (5.6 + 1.2 * k, y), 0.82, 5 + (k * 2) // 3, 8 + (k * 2) // 3))
    emitters += [
        # The pause: the brush presses down and to the right and the end swells into a round bead.
        lay("pause", (15.6, 6.1), 1.25, 11, 12, (0.2, 0.25)),
        lay("settle", (16.2, 6.4), 1.45, 12, 14, (0.1, 0.1)),
    ]
    effect = {
        "kind": "liquid", "frames": FRAMES, "duration": 70, "loop": False, "seed": 4,
        "walls": ["left", "right", "top", "bottom"], "gravity": [0, 0], "flip": 0.25, "drag": 0.3, "tension": 1.3,
        "emitters": emitters,
        # Wet ink: black, with the moon caught along its upper-left edge (the sheen) and a brighter glint.
        "look": [
            {"field": "density", "colors": ["1", "0"], "thresholds": [0.45, 0.8], "dither": 0},
            {"field": "light", "colors": ["D", "F"], "thresholds": [0.75, 0.92], "dither": 0}],
        "cleanup": {"strays": True},
    }
    return {"ink": {"format": "pixelforge-fluid", "version": 1, "name": "ink", "width": INK_W, "height": INK_H,
                    "palette": {"$ref": "../../../../palette.json"}, "effects": {"ink": effect}}}


INK = None


def ink(i):
    global INK
    if INK is None:
        INK = fluid_frames(Path(__file__).resolve().parents[1] / "out" / "build" / "ink.json", "ink")[0]
    return INK[min(i, FREEZE)]


def dryness(i):
    """0 wet, 1 drying, 2 dry."""
    if 3 <= i <= 14:
        return 0
    if 15 <= i <= 17:
        return 1
    return 2


DRY = [{}, {"F": "B", "D": "B"}, {"F": "1", "D": "1", "B": "1", "0": "1", "1": "1"}]
FADE = [{"F": "1", "D": "1", "B": "1", "0": "1", "1": "1"},          # frame 0: as dry as the hold
        {"F": "t", "D": "t", "B": "t", "0": "t", "1": "t"},          # frame 1: a step towards the paper
        {"F": "v", "D": "v", "B": "v", "0": "v", "1": "v"}]          # frame 2: almost the paper
FREEZE = 15                           # the ink stops moving as it starts to dry: later frames reuse this one


def ink_layer(ox, oy, i):
    if i < 3:
        # Last cycle's stroke, dry, fading into the paper a palette step a frame as the brush arrives.
        return {"name": "ink", "x": ox, "y": oy, "palette": FADE[i], "ops": ink(FRAMES - 1)}
    layer = {"name": "ink", "x": ox, "y": oy, "ops": ink(i)}
    if DRY[dryness(i)]:
        layer["palette"] = DRY[dryness(i)]
    return layer


# ---------------------------------------------------------------- sheet, brush
MU = [  # 木 printed for tracing (sheet coordinates): the horizontal, the vertical, the two falling strokes.
    ("line", 5, 5, 15, 5), ("line", 10, 3, 10, 14), ("line", 9, 6, 5, 10), ("line", 11, 6, 15, 10),
]


def sheet(x0, y0):
    x1, y1 = x0 + SW - 1, y0 + SH - 1
    ops = [
        # Paper (pale smoke), its moonlit top edge and a shadowed right edge and foot.
        rect(x0, y0, SW, SH, "w"), line(x0, y0, x1, y0, "x"), line(x0, y1, x1, y1, "v"), line(x1, y0 + 1, x1, y1, "v"),
        # The practice square's pink border (a dashed guide cross was tried and dropped: at 1x it hid the character).
        rect(x0 + 1, y0 + 1, SW - 2, SH - 2, "T", filled=False),
    ]
    # 木 printed in pink for tracing.
    for _, a, b, c, d in MU:
        ops.append(line(x0 + a, y0 + b, x0 + c, y0 + d, "V"))
    # The seal in the lower-right corner.
    ops += [rect(x1 - 5, y1 - 5, 3, 3, "c"), px(x1 - 4, y1 - 4, "v")]
    return ops


def brush(x, y, kind="upright", smear=None):
    """The brush with its tip at (x, y): a tapered head of wet black bristles with a moonlit upper-left edge, a brass
    ferrule and a bamboo handle (lit along its top). kind: 'upright' (writing, the handle up and to the right),
    'low' (a shallow angle, mid-swoop) or 'flat' (lying on the ledge, tip to the left). smear: where the tip was a frame
    earlier, drawn as a short streak of dark wood behind a fast move."""
    x, y = round(x), round(y)
    ops = []
    if smear:
        sx, sy = round(smear[0]), round(smear[1])
        mx, my = (sx + x) / 2, (sy + y) / 2
        ops += [line(round(mx) + 5, round(my) - 4, x + 5, y - 4, "I")]
    if kind == "upright":
        ops += [px(x, y, "0"), px(x + 1, y - 1, "0"), px(x + 1, y, "1"), px(x, y - 1, "t"),
                px(x + 2, y - 2, "1"), px(x + 2, y - 1, "1"), px(x + 1, y - 2, "u"),
                px(x + 3, y - 3, "O"), px(x + 3, y - 2, "N"), px(x + 2, y - 3, "P"),
                line(x + 4, y - 4, x + 8, y - 8, "L"), line(x + 5, y - 4, x + 8, y - 7, "K"), px(x + 8, y - 8, "J")]
    elif kind == "low":
        ops += [px(x, y, "0"), px(x + 1, y, "0"), px(x + 1, y - 1, "1"), px(x, y - 1, "t"), px(x + 2, y - 1, "1"),
                px(x + 2, y, "1"), px(x + 3, y - 1, "O"), px(x + 3, y - 2, "P"),
                line(x + 4, y - 2, x + 10, y - 5, "L"), px(x + 10, y - 5, "J")]
    else:
        ops += [px(x, y, "0"), px(x + 1, y, "0"), px(x + 2, y, "1"), px(x + 1, y - 1, "t"), px(x + 2, y - 1, "u"),
                px(x + 3, y, "O"), px(x + 3, y - 1, "P"),
                line(x + 4, y, x + 10, y, "L"), px(x + 5, y, "K"), px(x + 11, y, "J")]
    return ops


def smear(i, x0, y0):
    return (x0 + SMEAR[i][0], y0 + SMEAR[i][1]) if i in SMEAR else None


def frame_ops(i, variant):
    w = VARIANTS[variant][0]
    dx = 0 if variant == "regular" else -6
    ledge = (14, 55) if variant == "regular" else (11, 49)
    x0, y0 = 20 + dx, LEDGE_Y - SH
    tx, ty = tip(i)
    on_ledge = contact_shadow(x0 + SW / 2, LEDGE_Y, 10)
    if pose(i) == "flat" and i not in (0, 16):
        on_ledge += contact_shadow(x0 + REST[0] + 6, LEDGE_Y, 5)
    layers = [ledge_layer(ledge[0], ledge[1], LEDGE_Y, on_ledge),
              {"name": "sheet", "ops": sheet(x0, y0)},
              ink_layer(x0, y0, i),
              {"name": "brush", "ops": brush(x0 + tx, y0 + ty, pose(i), smear(i, x0, y0))}]
    return {"ops": [rect(0, 0, w, 42, "2")], "layers": layers}
