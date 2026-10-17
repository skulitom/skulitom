"""The phone hero (156x180, below 600 px): its own composition of the same workbench, at the desktop's scale.

The name block (eyebrow, name, two-line tagline, chips) is overlaid as vector text on the quiet wall at the top:
text-safe box x 6-150, y 6-80, with nothing bright above y 80 and nothing at all above y 70. The bench sits low
(y 170); the apparatus fills y 84-180: the flask right of centre is the hero, the coil drips into the beaker at the
left, the ink bottle stands in the moonlight's patch at the left end of the bench, the crucible between beaker and
tripod, the monitor at the right. The steam leaves the neck (y 96), rises to about y 72 and curls right toward
x 120-150 as it dissolves.

Reuses the desktop hero's compiled flask and drip (same canvases, same 96- and 48-frame loops, same beat) and adds its
own steam source. Writes recipes/hero-mobile-bg.json (one frame) and recipes/hero-mobile-fx.json (96 frames, 156x122
at (0, 58)), and build/hero-mobile-layout.json for the wrapper.
"""

import json
from pathlib import Path

import fluids
import gen
from gen import rect, line, px, dither, shade, shift

ROOT = Path(__file__).resolve().parent.parent
BUILD, RECIPES, SRC = ROOT / "out" / "build", ROOT / "out" / "recipes", ROOT / "out" / "fluids"
W, H = 156, 180
BENCH_Y = 170
QUIET = 80                                  # rows 0-79 stay quiet wall: the name block sits there
FRAMES, MS = fluids.FRAMES, fluids.MS
STILL = gen.STILL

# Where the desktop's apparatus (authored in right-half coordinates) lands on the phone canvas.
APP = (-28, BENCH_Y - gen.BENCH_Y)          # flask, tripod, burner and their light
COIL = (APP[0] + 3, APP[1])                 # stand, coil, beaker and drip, a little right to clear the ink bottle
INK = (APP[0] + 30, APP[1])                 # the ink bottle at the left end of the bench
CRUCIBLE = (APP[0] + 2, APP[1])
MONITOR = (APP[0] - 17, APP[1])             # pulled in: ends 7 px inside the right edge
FX_Y = 58                                   # the effects layer covers rows 58-179

# Phone steam: a 100x46 canvas at phone (56, 58) over the neck (vent at phone (100, 96)). Smaller billows rise about
# 20 px, then a draft curls them right; soak discs above and to the right dissolve them by y 72 and before the edge.
STEAM_AT = (56, 58)
STEAM_ORIGIN = (STEAM_AT[0] - APP[0], STEAM_AT[1] - APP[1])
STEAM_SIZE = (100, 46)
BILLOWS = tuple((s0, spin, side, round(r * 0.75, 2), d, up) for s0, spin, side, r, d, up in fluids.BILLOWS)
THIN = [{"at": [46, 0], "radius": 18, "density": -0.45}, {"at": [76, 2], "radius": 18, "density": -0.45},
        {"at": [100, 16], "radius": 14, "density": -0.35}, {"at": [50, 2], "area": [100, 22], "density": -0.6}]
DRAFT = {"at": [64, 20], "radius": 18, "rate": 0.08, "velocity": [1.1, -0.35], "expand": 0.4}


def steam_source():
    return fluids.steam_source(STEAM_ORIGIN, STEAM_SIZE, BILLOWS, THIN, DRAFT, name="phone-steam", wind=0.03)


def vent():
    return 128.0 - STEAM_ORIGIN[0], 54.0 - STEAM_ORIGIN[1]


# ---------------------------------------------------------------- background
def wall():
    ops = [rect(0, 0, W, BENCH_Y, "2")]
    for row, y in enumerate(range(3, BENCH_Y, 12)):
        ops.append(line(0, y, W - 1, y, "1"))
        off = 6 if row % 2 == 0 else 20
        for x in range(off, W, 28):
            ops.append(line(x, y + 1, x, min(y + 11, BENCH_Y - 1), "1"))
    ops.append(shade(0, 0, W, 24, -1, density=[0.6, 0.0], direction="down", over=["2"]))
    # One hairline crack with a moonlit lip, low on the right, below the name block.
    pts = ((147, 92), (144, 97), (146, 101), (143, 106))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        ops.append(line(ax, ay, bx, by, "1"))
    ops.append(px(145, 97, "3"))
    return ops


def clip_left(ops):
    """Drop row dithers that lie wholly left of the canvas and trim flat-density ones that start left of it (a
    canvas-anchored pattern is unchanged by trimming; gradient rows are left whole and clipped by Pixelbolt)."""
    out = []
    for o in ops:
        if o["x"] + o.get("w", 1) <= 0:
            continue
        if o["x"] < 0 and not isinstance(o.get("density"), list):
            o = dict(o, w=o["w"] + o["x"], x=0)
        out.append(o)
    return out


def moonlight():
    """Only where the desktop's moonbeam lands: the pane-shaped patch on the bench that the ink bottle stands in (the
    window and the beam itself are off-canvas; a beam cut by the left edge read as an unexplained box)."""
    return [o for o in clip_left(shift(gen.moonlight(), APP[0] - gen.R, APP[1])) if o["y"] >= BENCH_Y]


def bench():
    """The bench, low: its top (four rows), the lit lip and a shallow front with one grain line."""
    y = BENCH_Y
    ops = [rect(0, y - 1, W, 1, "H"), rect(0, y, W, 4, "I"), line(0, y + 4, W - 1, y + 4, "J"),
           rect(0, y + 5, W, H - y - 5, "H"), line(0, y + 5, W - 1, y + 5, "I"),
           line(8, y + 7, 70, y + 7, "I"), line(96, y + 7, 148, y + 7, "I")]
    ops.append(shade(0, y + 8, W, H - y - 8, -1, density=[0.0, 0.6], direction="down"))
    ops.append(dither(60, y + 4, 96, 1, "K", 0.5, over=["J"]))
    return ops


def stand_and_coil():
    """The desktop's stand and coil with a shorter rod (its finial now sits below the steam's band)."""
    ops = [o for o in gen.stand_and_coil() if not (o["op"] == "rect" and o.get("h") == 85) and
           not (o["op"] == "line" and o["x"] == o.get("x2") and o.get("y") == 40) and
           not (o["op"] == "rect" and o.get("y") == 38) and not (o["op"] == "line" and o.get("y") == 38)]
    rod = shift([rect(52, 58, 2, 67, "B"), line(52, 58, 52, 124, "C"), rect(51, 56, 4, 2, "C"),
                 line(51, 56, 54, 56, "D")], gen.COIL_DX)
    return shift(rod + ops, *COIL)


def side_arm():
    a, b = 145 + gen.FLASK_DX + APP[0], 86 + gen.COIL_DX + COIL[0]
    y0 = APP[1]
    return [line(a, 58 + y0, b, 62 + y0, "D"), line(a, 59 + y0, b, 63 + y0, "h"), line(a, 60 + y0, b, 64 + y0, "B"),
            line(a, 60 + y0, a - 27, 62 + y0, "j"), line(a, 60 + y0, a - 13, 61 + y0, "k")]


def background():
    ops = wall() + moonlight()
    ops += shift(gen.light_pools() + [gen.grid(*fluids.FLASK_ORIGIN, gen.flask_depth_rows())] + gen.tripod_and_burner(),
                 *APP)
    ops += bench() + shift(gen.bench_light() + gen.bench_front_light(), *APP)
    ops += stand_and_coil() + side_arm() + shift(gen.beaker_back(), *COIL)
    ops += shift(gen.crucible_body(), *CRUCIBLE) + shift(gen.monitor_body(), *MONITOR) + shift(gen.ink_bottle(), *INK)
    return ops


# ---------------------------------------------------------------- effects
def front(i):
    ops = (shift(gen.flask_front() + gen.flame(i), *APP) + shift(gen.beaker_front(), *COIL)
           + shift(gen.monitor_cursors(i), *MONITOR) + shift(gen.ember(i), *CRUCIBLE) + shift(gen.nib(i), *INK))
    return shift(ops, 0, -FX_Y)


def quiet_band():
    """Inside the steam layer: above y 80 (the name block) the steam keeps only its dim tones (everything brighter
    becomes v), and its lights fade to w through value-noise clumps over the next six rows, so the curl's dissolving
    head stays faint; above y 70 nothing is left."""
    q = QUIET - STEAM_AT[1]
    top = QUIET - 10 - STEAM_AT[1]          # y 70: the soaks leave only sparse dissolve pixels above it; clear them
    return [{"op": "clear", "x": 0, "y": 0, "w": STEAM_SIZE[0], "h": top},
            dither(0, 0, STEAM_SIZE[0], q, "v", 1.0, over=["x", "F", "G", "w"]),
            dither(0, q, STEAM_SIZE[0], 6, "w", [1.0, 0.0], direction="down", over=["x", "F", "G"], seed=11,
                   pattern="value", scale=3)]


def effects():
    steam = gen.fluid_frames("phone-steam")
    flask, drip = gen.fluid_frames("flask"), gen.fluid_frames("drip")
    fx, fy = fluids.FLASK_ORIGIN
    dx, dy = fluids.DRIP_ORIGIN
    frames = []
    for i in range(FRAMES):
        d = (i + fluids.DRIP_SHIFT) % fluids.DRIP_FRAMES
        frames.append({"name": f"loop-{i}", "duration": MS, "layers": [
            {"name": "steam", "x": STEAM_AT[0], "y": STEAM_AT[1] - FX_Y,
             "ops": steam[i] + quiet_band() + gen.steam_light(vent())},
            {"name": "liquid", "x": fx + APP[0], "y": fy + APP[1] - FX_Y, "ops": flask[i]},
            {"name": "drip", "x": dx + COIL[0], "y": dy + COIL[1] - FX_Y, "ops": drip[d]},
            {"name": "front", "ops": front(i)},
        ]})
    return frames


def write_source():
    (SRC / "phone-steam.fluid.json").write_text(json.dumps(steam_source(), indent=1) + "\n", encoding="utf-8",
                                                newline="\n")


def main():
    bg = gen.recipe("hero-mobile-bg", W, H, [{"name": "bg", "duration": MS, "ops": background()}], False)
    fx = gen.recipe("hero-mobile-fx", W, H - FX_Y, effects())
    review = gen.recipe("hero-mobile-review", W, H, [bg["frames"][0], {
        "name": "still", "duration": MS, "from": "bg",
        "layers": [dict(l, y=l.get("y", 0) + FX_Y) for l in fx["frames"][STILL]["layers"]]}], False)
    for rec in (bg, fx, review):
        (RECIPES / f"{rec['name']}.json").write_text(json.dumps(rec, separators=(",", ":")) + "\n", encoding="utf-8",
                                                      newline="\n")
    layout = {"still": STILL, "layers": [["hero-mobile-bg", 0, 0], ["hero-mobile-fx", 0, FX_Y]]}
    (BUILD / "hero-mobile-layout.json").write_text(json.dumps(layout) + "\n", encoding="utf-8", newline="\n")
    print("phone recipes written")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["source"]:
        write_source()
    else:
        main()
