"""The footer (416x42 as two 208x42 halves, 48 frames): the edge of the same workbench, under the hero.

The coil's glass drip-tip enters from the top edge on the right. A drop gathers on it (frames 10-20), falls and lands
at frame 24 in a shallow glass dish of mint distillate: a splash crown, a jet, spray and ripples running to the dish's
walls and back, settling by 40-47. As it lands, a wisp of vapour leaves the pool, rises and is gone by frame 42. The left two-thirds stay calm: the bench edge, the wall and a moonbeam landing on the bench as two
pane-shaped patches, as in the hero.

Writes src/fluids/footer-drop.fluid.json and footer-wisp.fluid.json and the recipes footer-left-bg, footer-right-bg
(one frame each) and footer-right-fx (the drop, the dish's liquid, the vapour and the glass), plus
build/footer-layout.json.
"""

import json
import sys
from pathlib import Path

import gen
from gen import rect, ell, line, px, dither, shade, shift

ROOT = Path(__file__).resolve().parent.parent
BUILD, RECIPES, SRC = ROOT / "out" / "build", ROOT / "out" / "recipes", ROOT / "out" / "fluids"
W, H, HALF = 416, 42, 208
FRAMES, MS = 48, 70
STILL = 24                       # the beat: the crown stands round the crater, spray in the air
PALETTE = {"$ref": "../../../palette.json"}
LIP = 21                         # bench: lip line 21, top surface 22-26, front edge 27, front 28-41
TIP_X = 364                      # the drip-tip's bore column (full coordinates)
DISH = (340, 380, 13)            # dish x range and rim row: walls 13-19, corners 20, base 21, liquid 17-20
LAND = 22                        # the drop reaches the surface on this frame; the crown stands at 23-25

# Fluid canvases (full coordinates).
DROP_AT, DROP_W, DROP_H = (330, 0), 60, 24
WISP_AT, WISP_W, WISP_H = (350, 0), 28, 16
# Effects layers (full coordinates): x, y, w, h.
RFX = (326, 0, 68, 26)


# ---------------------------------------------------------------- fluids
def dish_rows(x0, y0, w, h):
    """The dish's glass in a canvas at (x0, y0) as an obstacle mask: walls (rows 13-19), the rounded corners (row 20),
    the base (row 21) and the bench below it."""
    a, b, rim = DISH
    rows = []
    for y in range(y0, y0 + h):
        row = ""
        for x in range(x0, x0 + w):
            glass = ((rim <= y <= rim + 6 and x in (a, b)) or (y == rim + 7 and x in (a, a + 1, b - 1, b))
                     or (y == rim + 8 and a <= x <= b) or y > rim + 8)
            row += "A" if glass else "."
        rows.append(row)
    return rows


def drop_effect():
    x0, y0 = DROP_AT
    tx = TIP_X - x0 + 0.5
    a, b, rim = DISH
    return {
        "kind": "liquid", "frames": FRAMES, "duration": MS, "loop": True, "seed": 8, "warmup": 3,
        "walls": ["left", "right", "bottom"], "gravity": [0, 0.4], "flip": 0.35, "drag": 0.03, "tension": 2.4,
        "obstacles": [{"symbol": "tip", "x": 0, "y": 0, "draw": "none"},
                      {"symbol": "dish", "x": 0, "y": 0, "draw": "none"}],
        "fill": [{"x": a + 1 - x0, "y": rim + 4 - y0, "w": b - a - 1, "h": 4}],
        "emitters": [
            {"name": "bead", "at": [tx, 5.0], "radius": 1.4, "rate": 1, "start": 5, "end": 15, "velocity": [0, 0]},
            {"name": "swell", "at": [tx, 5.6], "radius": 1.6, "rate": 1, "start": 10, "end": 15,
             "velocity": [0, 0]},
            # The rebound: as the drop hits, a short upward push at the impact makes the jet that rises out of the
            # crater and falls back (as the splash preset does).
            {"name": "rebound", "at": [tx, rim + 5.5 - y0], "area": [3, 2], "rate": 1, "start": LAND + 1,
             "end": LAND + 3, "density": 0, "velocity": [0, -1.9]},
            {"name": "crown-l", "at": [tx - 3.5, rim + 4.5 - y0], "area": [2, 2], "rate": 1, "start": LAND,
             "end": LAND + 2, "density": 0, "velocity": [-0.9, -1.4]},
            {"name": "crown-r", "at": [tx + 3.5, rim + 4.5 - y0], "area": [2, 2], "rate": 1, "start": LAND,
             "end": LAND + 2, "density": 0, "velocity": [0.9, -1.4]},
            # The dish keeps its level: what each drop adds evaporates (as the wisp) by the next.
            {"name": "evaporate", "at": [(a + b) / 2 - x0, rim + 6.5 - y0], "area": [b - a - 5, 1], "rate": 1,
             "density": -0.003},
        ],
        "whitewater": [{"impact": 0.8, "chance": 0.8, "throw": 1.6, "spread": 35, "life": [8, 14],
                        "colors": ["n", "m", "l"], "size": 1}],
        # Seen through the glass: the surface row glows, the body is a step darker, deepest darkest.
        "look": [
            {"field": "density", "colors": ["j"], "thresholds": [0.5], "dither": 0},
            {"field": "depth", "colors": ["l", "k", "j"], "thresholds": [1, 2, 3], "dither": 0},
            {"field": "speed", "colors": ["m"], "thresholds": [1.0], "dither": 0},
        ],
        "cleanup": {"strays": True},
    }


def wisp_effect():
    """A wisp of vapour on the beat: as the drop lands, a small puff leaves the pool at the landing point (frames
    24-29), rises about 10 px and thins out through an even Bayer dither; a soak over the whole canvas from frame 34
    clears what is left, so frames 37-47 and 0-23 are empty."""
    a, b, rim = DISH
    x0, y0 = WISP_AT
    sx, sy = TIP_X - x0 + 0.5, rim + 2 - y0
    return {
        "frames": FRAMES, "duration": MS, "loop": True, "seed": 12, "warmup": 3,
        "buoyancy": 0.2, "vorticity": 0, "dissipation": 0.14, "cooling": 0, "drag": 0.1, "wind": [-0.004, 0],
        "emitters": [
            {"name": "puff", "at": [sx, sy], "area": [3, 2], "rate": 1, "start": LAND + 2, "end": LAND + 8,
             "density": 0.7, "temperature": 0.6, "falloff": 0.6, "velocity": [0, -1.0], "noise": 0.05,
             "flicker": 0.2},
            {"name": "clear", "at": [WISP_W / 2, WISP_H / 2], "area": [WISP_W, WISP_H], "rate": 1, "start": 34,
             "end": 48, "density": -0.6},
            {"name": "thin", "at": [WISP_W / 2, 1], "area": [WISP_W, 3], "rate": 1, "density": -0.5},
        ],
        # Vapour, not a shape: dim tones through an even Bayer feather, no solid colour to draw a silhouette.
        "look": [
            {"field": "density", "colors": ["u", "v"], "thresholds": [0.12, 0.3], "dither": 0.85},
        ],
        "cleanup": {"strays": True, "corners": True},
    }


def sources():
    """Two sources: one canvas size per source (Pixelbolt ask 2)."""
    x0, y0 = DROP_AT
    tip = ["".join("A" if (y <= 3 and TIP_X - 1 <= x + x0 <= TIP_X + 1) else "." for x in range(DROP_W))
           for y in range(DROP_H)]
    return {
        "footer-drop": {"format": "pixelforge-fluid", "version": 1, "name": "footer-drop", "width": DROP_W,
                        "height": DROP_H, "palette": PALETTE,
                        "symbols": {"tip": tip, "dish": dish_rows(x0, y0, DROP_W, DROP_H)},
                        "effects": {"drop": drop_effect()}},
        "footer-wisp": {"format": "pixelforge-fluid", "version": 1, "name": "footer-wisp", "width": WISP_W,
                        "height": WISP_H, "palette": PALETTE, "effects": {"wisp": wisp_effect()}},
    }


# ---------------------------------------------------------------- the static strip (full coordinates)
PANES = ((60, 79), (84, 103))    # where the window's two panes throw their light (the window is above, off-frame)


def wall():
    ops = [rect(0, 0, W, LIP, "2")]
    for row, y in enumerate((2, 14)):
        ops.append(line(0, y, W - 1, y, "1"))
        for x in range(10 if row % 2 == 0 else 24, W, 28):
            ops.append(line(x, y + 1, x, min(y + 11, LIP - 1), "1"))
    return ops


def beam():
    """The moonbeam from the window above: each pane's light comes in at the top edge and runs down-right to the bench
    as a continuous shaft (night 4 dither, a night 5 core), brighter where it lands."""
    ops = []
    for ax, bx in PANES:
        for y in range(0, LIP):
            d = (LIP - y) * 0.75
            near, far = int(ax - d), int(bx - d)
            k = round(0.22 + 0.3 * y / LIP, 3)
            ops.append(dither(near, y, far - near + 1, 1, "4", k, over=["2", "1"]))
            ops.append(dither(near + 4, y, far - near - 7, 1, "5", round(k * 0.5, 3), over=["2", "1", "4"]))
    return ops


def patches():
    """Where the beam lands: two pane-shaped patches on the bench top with the mullion's shadow between them (drawn
    after the bench): the wood lifts a step (J), its centre two (K)."""
    ops = []
    for ax, bx in PANES:
        for r in range(4):
            sx = ax + int(0.75 * r)
            ops.append(dither(sx, LIP + 1 + r, bx - ax - 1, 1, "J", 1.0 if r < 3 else 0.5, over=["I"]))
            ops.append(dither(sx + 3, LIP + 1 + r, bx - ax - 7, 1, "K", 0.5, over=["J"]))
    return ops


def bench():
    y = LIP
    ops = [rect(0, y, W, 1, "H"), rect(0, y + 1, W, 5, "I"), line(0, y + 6, W - 1, y + 6, "J"),
           rect(0, y + 7, W, H - y - 7, "H"), line(0, y + 7, W - 1, y + 7, "I")]
    for gy, segs in ((y + 11, ((6, 120), (150, 262), (300, 410))), (y + 15, ((40, 190), (222, 350)))):
        for a, b in segs:
            ops.append(line(a, gy, b, gy, "I"))
    ops.append(shade(0, y + 16, W, H - y - 16, -1, density=[0.0, 0.8], direction="down"))
    for kx, ky in ((196, y + 12), (330, y + 16)):
        ops += [ell(kx, ky, 7, 3, "I", filled=False), px(kx + 3, ky + 1, "1"),
                line(kx - 8, ky - 1, kx - 1, ky - 1, "I"), line(kx + 7, ky + 3, kx + 15, ky + 3, "I")]
    return ops


def dish_light():
    """The distillate glows faintly: a small banded mint pool on the wall behind the dish, on the bench top round it
    and on the bench lip below it; a contact shadow under the dish's base."""
    a, b, rim = DISH
    cx = (a + b) // 2
    return [shade(cx - 34, rim - 12, 69, 22, 1, shape="ellipse", density=0.5, over=["1", "2"]),
            shade(cx - 26, rim - 6, 53, 13, 1, shape="ellipse", over=["1", "2"]),
            dither(cx - 32, LIP + 1, 65, 5, "i", 0.5, over=["I"]), dither(cx - 20, LIP + 2, 41, 3, "j", 0.5, over=["i"]),
            dither(cx - 26, LIP + 6, 53, 1, "k", 0.5, over=["J"]),
            shade(a + 1, LIP + 1, b - a - 1, 1, -1)]


def drip_tip():
    """The coil's outlet, entering from the top edge: a glass tube with a mint condensate thread."""
    x = TIP_X
    return [rect(x - 1, 0, 3, 4, "C"), line(x, 0, x, 3, "h"), line(x - 1, 0, x - 1, 3, "D"), px(x + 1, 2, "k"),
            px(x, 3, "i")]


def dish_front():
    """The dish's glass drawn over the liquid: the front rim (moonlit at the left, mint-lit at the right where the
    liquid's glow reaches it), the walls, rounded corners, the base, and a specular streak on the left wall."""
    a, b, rim = DISH
    return [line(a, rim + 1, a, rim + 6, "D"), line(b, rim + 1, b, rim + 6, "k"), px(a + 1, rim + 7, "D"),
            px(b - 1, rim + 7, "j"), line(a + 2, rim + 8, b - 2, rim + 8, "C"), line(a + 2, rim + 8, a + 8, rim + 8, "D"),
            line(a + 2, rim + 3, a + 2, rim + 5, "l"), px(a + 2, rim + 2, "n")]


def dish_rim():
    """The dish's rim line, moonlit at the left and mint-lit at the right; drawn with the background, behind the
    splash and the vapour that rise over it."""
    a, b, rim = DISH
    return [line(a, rim, b, rim, "D"), line(a, rim, a + 9, rim, "E"), line(b - 8, rim, b, rim, "k")]


def background(x0, width=HALF):
    ops = wall() + beam() + bench() + patches() + dish_light() + dish_rim()
    ops = gen.for_half(ops, x0, width)
    return shift(ops, -x0) if x0 else ops


# ---------------------------------------------------------------- effects
def wisp_light():
    """Inside the wisp layer: its base, just over the liquid, is lit mint from below (a small ring over its colours)."""
    a, b, rim = DISH
    cx, cy = TIP_X - WISP_AT[0] + 0.5, rim + 3 - WISP_AT[1]
    lit = ["x", "w", "v", "u", "F"]
    return gen.ring(cx, cy, 2.5, "l", 1.0, lit) + gen.ring(cx, cy, 5.0, "k", 0.5, lit)


def effects():
    drop, wisp = gen.fluid_frames("footer-drop", "drop"), gen.fluid_frames("footer-wisp", "wisp")
    x0, y0, w, h = RFX
    frames = []
    for i in range(FRAMES):
        frames.append({"name": f"loop-{i}", "duration": MS, "layers": [
            {"name": "drop", "x": DROP_AT[0] - x0, "y": DROP_AT[1] - y0, "ops": drop[i]},
            {"name": "wisp", "x": WISP_AT[0] - x0, "y": WISP_AT[1] - y0, "ops": wisp[i] + wisp_light()},
            {"name": "glass", "ops": shift(drip_tip() + dish_front(), -x0, -y0)},
        ]})
    return frames


def main():
    if sys.argv[1:] == ["source"]:
        for name, src in sources().items():
            (SRC / f"{name}.fluid.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8",
                                                    newline="\n")
        return
    # The left background is one column wider, so the right half covers an identical column at the seam.
    recs = [gen.recipe("footer-left-bg", HALF + 1, H, [{"name": "bg", "duration": MS, "ops": background(0, HALF + 1)}],
                       False),
            gen.recipe("footer-right-bg", HALF, H, [{"name": "bg", "duration": MS, "ops": background(HALF)}], False),
            gen.recipe("footer-right-fx", RFX[2], RFX[3], effects())]
    for rec in recs:
        (RECIPES / f"{rec['name']}.json").write_text(json.dumps(rec, separators=(",", ":")) + "\n", encoding="utf-8",
                                                      newline="\n")
    layout = {"still": STILL, "layers": [["footer-left-bg", 0, 0], ["footer-right-bg", HALF, 0],
                                         ["footer-right-fx", RFX[0], RFX[1]]]}
    (BUILD / "footer-layout.json").write_text(json.dumps(layout) + "\n", encoding="utf-8", newline="\n")
    print("footer recipes written")


if __name__ == "__main__":
    main()
