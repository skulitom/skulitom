"""London in minutes tile (68x42, narrow 56x42): a little violet steam locomotive and one carriage on a track along a
ledge of the workbench, a faint London skyline (Elizabeth Tower with its lit clock face, the Eye) on the wall behind.
Once a cycle the train runs: the view follows it, so the sleepers and rail joints stream past under it, the coupling
rods turn, and the chimney chuffs three puffs of steam (a Pixelbolt gas simulation, shaded billows lit by the moon)
that the train's own wind lays back over the carriage. Then it eases to a stop and the last of the steam thins away.

Frames (70 ms): 0 rest, 1-17 the run (ease in and out, 24 px of track, a whole number of sleeper and joint pitches so
the track loops), chuffs at 2, 6 and 10, 21 the hold (the still).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from pb import rect, ell, line, px, pxs, grid, dither, shade, erase, fluid_frames  # noqa: E402
from bench import contact_shadow, end_fade  # noqa: E402

NAME, KIND = "london-in-minutes", "tile"
FRAMES = 22
VARIANTS = {"regular": (68, 42), "narrow": (56, 42)}
TITLE = "London in minutes"
DESC = ("Pixel art made with Pixelbolt: a little violet steam train on a track along a ledge of the workbench, a "
        "faint London skyline behind; it runs, chuffing three puffs of simulated steam, and eases to a stop.")

RAIL_Y = 22
LEDGE_Y = 23
RUN_FROM, RUN_TO, RUN = 1, 17, 24          # frames of the run and the track travelled (a multiple of both pitches)
SLEEPER, JOINT = 6, 8               # both wider than twice the top speed (2 px a frame): nothing seems to run backwards
CHUFFS = (2, 6, 10)
STEAM_W, STEAM_H = 40, 14
STEAM_EMIT = (30.0, 11.5)                  # chimney mouth in the steam canvas


def travel(i):
    """Track travelled by frame i: smoothstep from RUN_FROM to RUN_TO, whole pixels."""
    if i <= RUN_FROM:
        return 0
    if i >= RUN_TO:
        return RUN
    t = (i - RUN_FROM) / (RUN_TO - RUN_FROM)
    return round(RUN * t * t * (3 - 2 * t))


def speed(i):
    return travel(i) - travel(i - 1) if i > 0 else 0


# ---------------------------------------------------------------- the steam (a gas simulation)
def sources():
    cx, cy = STEAM_EMIT

    def billow(name, s, r, d, vx, vort):
        return {"name": name, "at": [cx, cy], "radius": r, "rate": 1, "start": s, "end": s + 2, "density": d,
                "temperature": 0.9, "falloff": 0.95, "velocity": [vx, -1.6], "expand": 2.0, "noise": 0.1,
                "flicker": 0.1, "vortex": vort}

    def draft(name, s, e, k):
        # The train's own wind: a velocity-only emitter over the whole canvas, on only while the train runs.
        return {"name": name, "at": [STEAM_W / 2, STEAM_H / 2], "area": [STEAM_W, STEAM_H], "rate": k, "start": s,
                "end": e, "velocity": [-2.4, 0]}

    effect = {
        "frames": FRAMES, "duration": 70, "loop": True, "seed": 5, "warmup": 3,
        "buoyancy": 0.18, "vorticity": 0.3, "dissipation": 0.16, "cooling": 0.04, "drag": 0.1,
        "emitters": [
            billow("chuff-1", CHUFFS[0], 1.3, 1.7, 0.0, 0.3),
            billow("chuff-2", CHUFFS[1], 1.15, 1.45, 0.1, -0.3),
            billow("chuff-3", CHUFFS[2], 1.4, 1.8, 0.0, 0.3),
            draft("draft-1", 1, 4, 0.12), draft("draft-2", 4, 12, 0.25), draft("draft-3", 12, 16, 0.1),
            {"name": "thin-top", "rate": 1, "falloff": 1, "at": [20, 4], "radius": 7, "density": -0.8},
            {"name": "thin-left", "rate": 1, "falloff": 1, "at": [-2, 7], "radius": 16, "density": -0.6},
            {"name": "clear-late", "rate": 1, "falloff": 1, "start": 15, "end": 22, "at": [12, 5], "radius": 14,
             "density": -0.3},
        ],
        # Shaded billows: dim feathered edges, a solid body, dense cores, a shadow underside and moonlit tops.
        "look": [
            {"field": "density", "colors": ["u", "v"], "thresholds": [0.16, 0.3], "dither": 0},
            {"field": "density", "colors": ["w"], "thresholds": [0.6], "dither": 0},
            {"field": "density", "colors": ["x"], "thresholds": [1.6], "dither": 0},
            {"field": "shadow", "colors": ["v", "u"], "thresholds": [0.3, 0.6], "dither": 0},
            {"field": "light", "colors": ["x", "F", "G"], "thresholds": [0.22, 0.5, 0.82], "dither": 0}],
        "cleanup": {"strays": True, "corners": True},
    }
    return {"steam": {"format": "pixelforge-fluid", "version": 1, "name": "steam", "width": STEAM_W,
                      "height": STEAM_H, "palette": {"$ref": "../../../../palette.json"},
                      "effects": {"steam": effect}}}


STEAM = None


def steam_ops(i):
    global STEAM
    if STEAM is None:
        STEAM = fluid_frames(Path(__file__).resolve().parents[1] / "out" / "build" / "steam.json", "steam")[0]
    return STEAM[i]


# ---------------------------------------------------------------- the train (L0 = the cab's back wall)
WHEELS = {
    5: [".DDo.", "Dqppo", "DpCpo", "opppo", ".ooo."],
    4: [".Do.", "Dqpo", "opCo", ".oo."],
}


def wheel(x, y, d, phase):
    """A round wheel d px across (5 for the loco's drivers, 4 for the rest) at (x, y): a violet face lit on its upper
    left, a moonlit steel rim at the top left, a dark rim lower right, a steel hub. Its crank pin turns through four
    positions (the coupling rod's ends)."""
    ops = [grid(x, y, WHEELS[d])]
    c = (d - 1) / 2
    pins = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    dx, dy = pins[phase % 4]
    pin = (round(x + c + dx), round(y + c + dy))
    return ops, pin


BODY = {"o": "p", "p": "q", "q": "r", "r": "y", "y": "z"}       # the body one ramp step lighter than the wheels


def lift(ops):
    """Recolour body operations one step up the violet ramp (brass, steel and lights stay as drawn)."""
    return [dict(o, color=BODY.get(o["color"], o["color"])) if "color" in o else o for o in ops]


def loco(L0, phase):
    ops = lift([
        # Cab: walls, its moonlit back edge, the roof with a lit top.
        rect(L0, 10, 5, 6, "q"), line(L0, 10, L0, 15, "r"), line(L0 + 4, 11, L0 + 4, 15, "p"),
        line(L0 - 1, 8, L0 + 4, 8, "r"), px(L0 - 1, 8, "y"), px(L0, 8, "y"), line(L0 - 1, 9, L0 + 5, 9, "p"),
        # Boiler with its moonlit top and a shadowed belly.
        rect(L0 + 5, 12, 8, 4, "q"), line(L0 + 5, 12, L0 + 12, 12, "r"), line(L0 + 5, 12, L0 + 8, 12, "y"),
        line(L0 + 5, 15, L0 + 12, 15, "p"),
        # Chimney with a capped lip.
        rect(L0 + 11, 10, 2, 2, "p"), line(L0 + 10, 9, L0 + 13, 9, "q"), px(L0 + 10, 9, "r"), px(L0 + 13, 9, "p"),
        # Smokebox front.
        rect(L0 + 13, 12, 2, 4, "p"), line(L0 + 14, 12, L0 + 14, 15, "o"),
        # Footplate.
        line(L0, 16, L0 + 15, 16, "o"),
    ])
    ops += [
        # A warm lit cab window; brass boiler bands and dome; the headlamp; the buffer beam and buffer.
        rect(L0 + 1, 11, 2, 2, "Q"), px(L0 + 1, 11, "R"),
        line(L0 + 7, 12, L0 + 7, 15, "O"), line(L0 + 10, 12, L0 + 10, 15, "O"), px(L0 + 7, 12, "P"), px(L0 + 10, 12, "P"),
        rect(L0 + 8, 11, 2, 1, "O"), px(L0 + 8, 11, "Q"),
        px(L0 + 14, 11, "R"), px(L0 + 13, 11, "O"), px(L0 + 16, 16, "c"), px(L0 + 17, 16, "C"),
    ]
    w1, p1 = wheel(L0 + 1, 17, 5, phase)
    w2, p2 = wheel(L0 + 7, 17, 5, phase)
    w3, _ = wheel(L0 + 12, 18, 4, phase)
    ops += w1 + w2 + w3
    # The coupling rod between the two drivers' crank pins.
    ops += [line(p1[0], p1[1], p2[0], p2[1], "D"), px(p1[0], p1[1], "E"), px(p2[0], p2[1], "E")]
    return ops


def carriage(L0, phase):
    x0, x1 = L0 - 12, L0 - 2
    ops = lift([rect(x0, 11, 11, 6, "q"), line(x0, 11, x0, 16, "r"), line(x1, 12, x1, 16, "p"),
                line(x0 + 1, 10, x1 - 1, 10, "r"), line(x0 + 1, 10, x0 + 4, 10, "y"), px(x0, 11, "r"), px(x1, 11, "p"),
                line(x0, 16, x1, 16, "p"), line(x0 + 1, 17, x1 - 1, 17, "o")])
    # Three warm windows; the coupling to the loco.
    ops += [rect(x0 + 1, 12, 2, 2, "Q"), rect(x0 + 4, 12, 2, 2, "Q"), rect(x0 + 7, 12, 2, 2, "Q"),
            px(x0 + 1, 12, "R"), px(x0 + 4, 12, "R"), px(x0 + 7, 12, "R"), line(x1 + 1, 16, L0 - 1, 16, "C")]
    for wx in (x0 + 1, x1 - 4):
        w, _ = wheel(wx, 18, 4, phase)
        ops += w
    return ops


# ---------------------------------------------------------------- track, ledge and skyline
def track(w, scroll, x0, x1):
    """Rails on the ledge: the rail line with joints every 24 px, sleepers every 3 px on the ledge top; both stream
    left as the view follows the train. Drawn inside the ledge layer, so its ends fade with the ledge."""
    ops = [line(x0, RAIL_Y, x1, RAIL_Y, "C"), line(x0 + 4, RAIL_Y, x0 + 11, RAIL_Y, "D")]  # the rail, moonlit at its left
    for x in range(x0 - 3, x1 + 3):
        if (x + scroll) % SLEEPER in (0, 1):
            ops.append(px(x, LEDGE_Y, "K"))
        if (x + scroll) % JOINT == 0:
            ops.append(px(x, RAIL_Y, "E"))
    return ops


def ledge(x0, x1, scroll, extra):
    w = x1 - x0 + 1
    ops = [rect(x0, LEDGE_Y, w, 1, "J"), rect(x0, LEDGE_Y + 1, w, 1, "I"), rect(x0, LEDGE_Y + 2, w, 1, "H"),
           line(x0 + 4, LEDGE_Y, x0 + 10, LEDGE_Y, "K"), dither(x0 + 11, LEDGE_Y, 3, 1, "K", 0.5, over=["J"])]
    ops += track(w, scroll, x0, x1) + list(extra)
    ops += end_fade(x0, x1, RAIL_Y, 4)
    return {"name": "ledge", "ops": ops}


def skyline(variant):
    """The wall behind: night-3 silhouettes, moonlit on their left edges (night 4), barely above the wall."""
    if variant == "regular":
        tower, eye, blocks = 15, (49, 7), [(19, 17, 6, 5), (40, 16, 5, 6), (57, 18, 4, 4)]
    else:
        tower, eye, blocks = 10, (39, 10), [(14, 17, 5, 5), (33, 17, 4, 5)]
    ex, ey = eye
    d = 13 if variant == "regular" else 11
    ops = []
    for bx, by, bw, bh in blocks:
        ops += [rect(bx, by, bw, bh, "3"), line(bx, by, bx, by + bh - 1, "4")]
    ops += [
        # Elizabeth Tower: shaft, belfry, spire, and its lit clock face.
        rect(tower, 8, 3, 14, "3"), line(tower, 8, tower, 21, "4"), rect(tower - 1, 7, 5, 1, "3"),
        line(tower + 1, 3, tower + 1, 6, "3"), px(tower, 5, "3"), px(tower + 2, 5, "3"),
        px(tower + 1, 9, "O"),
        # The Eye: the wheel's rim, hub and legs.
        ell(ex, ey, d, d, "3", filled=False), px(ex + d // 2, ey + d // 2, "4"),
        line(ex + d // 2, ey + d // 2 + 1, ex + d // 2 - 3, 21, "3"),
        line(ex + d // 2, ey + d // 2 + 1, ex + d // 2 + 3, 21, "3"),
        shade(ex - 1, ey - 1, 8, 8, 1, shape="ellipse", over=["3"]),
    ]
    return ops


def steam_ceiling(oy):
    """Keep the plume 3 px clear of the tile's top edge: in the steam layer's coordinates, rows above tile row 3 are
    cleared (a soak centred just below that row dissolves the plume before it gets there)."""
    return [erase(0, 0, STEAM_W, 3 - oy, 1.0)]


def frame_ops(i, variant):
    w = VARIANTS[variant][0]
    L0 = 33 if variant == "regular" else 27
    lx0, lx1 = (12, 55) if variant == "regular" else (9, 46)
    scroll = travel(i)
    phase = scroll // 3
    on_ledge = contact_shadow(L0 + 2, LEDGE_Y, 12)
    ops = [rect(0, 0, w, 42, "2")] + skyline(variant)
    # The steam sits behind the train: the chimney's lip hides the base of each puff as it leaves the mouth.
    layers = [ledge(lx0, lx1, scroll, on_ledge),
              {"name": "steam", "x": L0 + 12 - round(STEAM_EMIT[0]), "y": 9 - round(STEAM_EMIT[1]),
               "ops": steam_ops(i) + steam_ceiling(9 - round(STEAM_EMIT[1]))},
              {"name": "train", "ops": carriage(L0, phase) + loco(L0, phase)}]
    return {"ops": ops, "layers": layers}
