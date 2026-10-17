"""Write the desktop hero's Pixelbolt fluid sources: flask boil, steam, drip, and the clouds outside the window.

Python only lays out geometry here: obstacle masks for the glass, emitter positions and timing. Every fluid pixel is
computed later by `pixelbolt compile`.

Coordinates are the right half's (208x162) unless noted. Each fluid canvas has an origin in that space (ORIGINS).

The hero loops 96 frames (6.72 s at 70 ms). Its beat: the boil builds (0-35), the flask surges and blows the biggest
billow at 48 (36-56), then it settles (57-95). The drip runs on its own 48-frame cycle, shifted so the next drop hangs
at the coil tip during the surge and lands as the settle begins (frame 55), and again at frame 7.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
FLUIDS = HERE.parent / "out" / "fluids"
PALETTE = {"$ref": "../../../palette.json"}
FRAMES, MS = 96, 70
DRIP_FRAMES, DRIP_SHIFT = 48, 24  # hero frame i shows drip frame (i + DRIP_SHIFT) % 48

# Flask: round-bottom bulb 40 px across (interior radius 19 round a pixel corner), 6-px neck bore.
FLASK_ORIGIN = (106, 56)         # canvas (0,0) in right-half coordinates
FLASK_W, FLASK_H = 44, 50
FLASK_C = (22.0, 29.0)           # bulb centre (pixel corner) in the flask canvas -> right-half (128, 85)
FLASK_R = 19.0
NECK = (19, 24)                  # interior columns of the neck bore (inclusive)
LIQUID_TOP = 31                  # fill starts on this canvas row (right-half y 87)


def flask_interior(x, y):
    dx, dy = x + 0.5 - FLASK_C[0], y + 0.5 - FLASK_C[1]
    if dx * dx + dy * dy <= FLASK_R * FLASK_R:
        return True
    return NECK[0] <= x <= NECK[1] and y < FLASK_C[1]


def flask_glass(x, y):
    """One-pixel glass ring round the interior (8-connected): the shape drawn later as the flask."""
    if flask_interior(x, y):
        return False
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if 0 <= x + ox < FLASK_W and 0 <= y + oy < FLASK_H and flask_interior(x + ox, y + oy):
                return True
    return False


# The surge: a 32-frame pulse, opened at frame 30 (strength 0), cresting at 46, closed at 62. Phase puts the trough of
# sin(360 * c / 32 + phase) at c = 30.
SURGE = {"start": 30, "end": 62, "pulse": {"amplitude": 1, "period": 32, "phase": 292.5}}


def flask_source():
    solid = ["".join("." if flask_interior(x, y) else "B" for x in range(FLASK_W)) for y in range(FLASK_H)]
    cx = FLASK_C[0]
    bottom = FLASK_C[1] + FLASK_R - 2.5
    return {
        "format": "pixelforge-fluid", "version": 1, "name": "flask", "width": FLASK_W, "height": FLASK_H,
        "palette": PALETTE,
        "symbols": {"glass": solid},
        "effects": {"flask": {
            "kind": "liquid", "frames": FRAMES, "duration": MS, "loop": True, "seed": 11, "warmup": 3,
            "walls": ["bottom", "left", "right"], "gravity": [0, 0.25], "flip": 0.75, "drag": 0.04, "tension": 0.6,
            "obstacles": [{"symbol": "glass", "x": 0, "y": 0, "draw": "none"}],
            "fill": [{"at": [cx, FLASK_C[1]], "radius": FLASK_R, "x": 0, "y": LIQUID_TOP, "w": FLASK_W,
                      "h": FLASK_H - LIQUID_TOP}],
            "emitters": [
                # Rolling boil: heat pushes up under the centre in 12-frame heaves.
                {"name": "heat", "at": [cx, bottom], "area": [12, 3], "rate": 1, "density": 0,
                 "velocity": [0, -2.0], "pulse": {"amplitude": 1, "period": 12}},
                # The event: one big upwelling a loop, cresting at frame 46.
                # A soft disc, so the upwelling has no box edges (the speed look would draw them).
                dict({"name": "surge", "at": [cx, bottom - 3], "radius": 4.5, "rate": 1, "density": 0,
                      "velocity": [0, -2.2]}, **SURGE),
                {"name": "boil", "at": [cx, LIQUID_TOP + 1], "area": [28, 3], "rate": 1, "density": 0, "noise": 0.25},
                {"name": "roll-l", "at": [cx - 10, LIQUID_TOP + 7], "area": [8, 8], "rate": 1, "density": 0,
                 "velocity": [0.45, -0.3], "pulse": {"amplitude": 1, "period": 24}},
                {"name": "roll-r", "at": [cx + 10, LIQUID_TOP + 7], "area": [8, 8], "rate": 1, "density": 0,
                 "velocity": [-0.45, -0.3], "pulse": {"amplitude": 1, "period": 24, "phase": 180}},
                # Bubbles rise from the hot bottom and pop where they leave the liquid.
                {"name": "bubbles", "at": [cx, bottom], "area": [18, 2], "rate": 1, "density": 0,
                 "sparks": {"count": 0.45, "life": [22, 32], "colors": ["n", "m"], "size": 1, "angle": 270,
                            "speed": 0.75, "gravity": [0, -0.09], "drag": 0.05, "follow": 0.25, "pop": True}},
                dict({"name": "big-bubbles", "at": [cx, bottom - 1], "area": [8, 2], "rate": 1, "density": 0,
                      "sparks": {"count": 0.3, "life": [18, 24], "colors": ["n", "n", "m"], "size": 2, "angle": 270,
                                 "speed": 0.95, "gravity": [0, -0.12], "drag": 0.05, "follow": 0.3, "pop": True}},
                     **SURGE),
            ],
            # Seen through glass: one step darker than the liquid's own colours. Top row brightest (it glows).
            "look": [
                {"field": "density", "colors": ["k"], "thresholds": [0.5], "dither": 0},
                {"field": "depth", "colors": ["m", "l", "k", "j"], "thresholds": [1, 2, 5, 14], "dither": 0},
                {"field": "speed", "colors": ["l"], "thresholds": [2.1], "dither": 0},
            ],
            "cleanup": {"strays": True},
        }},
    }


# Steam: leaves the open neck at right-half (128, 55), climbs and leans left in a draft.
STEAM_ORIGIN = (42, 0)
STEAM_W, STEAM_H = 128, 60
VENT = (128.0 - STEAM_ORIGIN[0], 54.0)
NECK_COLS = (124, 131)           # neck glass columns, right half

# Billows: (start frame, spin, sideways push, radius, density, upward speed). Seven a loop at irregular intervals
# (14, 13, 12, 9, 14, 17, 17 frames) and sizes (0.75-1.35x), alternating sides and spin, so the plume never settles into
# an even, banded tube; dense and light ones alternate (about 2:1), so neighbours keep separate tones where they merge
# into rolls. A small one at 45 ramps the surge in before its biggest billow at 48. Between billows a thin breath keeps
# the plume attached to the neck.
BILLOWS = ((0, 0.3, -0.3, 3.0, 3.6, -1.4), (14, -0.3, 0.25, 2.25, 1.8, -1.4),
           (27, 0.3, -0.2, 3.3, 3.7, -1.4), (39, -0.3, 0.3, 2.7, 2.0, -1.4),
           (45, 0.2, 0.0, 2.2, 2.2, -1.4), (48, 0.3, -0.15, 4.05, 4.3, -1.7),
           (62, -0.3, 0.3, 2.4, 1.9, -1.4), (79, 0.3, -0.25, 3.0, 3.4, -1.4))

# Steam look. Density is a passive scalar here, so billows are blown dense and dissipate steadily: each billow is a
# clear factor thinner than its denser neighbour, and the bands step by about that factor, so billows keep their own
# tones as they grow and merge. Light and shadow are Pixelbolt's relative fields (how sharply density falls toward or
# away from the moon): the lit upper left of each billow is x, with F only on its sharpest 2-3 px rim and G rarer
# still; its lower right goes v then u. The thinnest steam thins out through a wide Bayer band (u feathered into v),
# an even pattern rather than speckle.
STEAM_LOOK = [
    {"field": "density", "colors": ["u", "v"], "thresholds": [0.16, 0.34], "dither": 0.85},
    {"field": "density", "colors": ["w"], "thresholds": [0.7], "dither": 0},
    {"field": "density", "colors": ["x"], "thresholds": [3.4], "dither": 0},
    {"field": "shadow", "colors": ["v", "t"], "thresholds": [0.25, 0.55], "dither": 0},
    {"field": "light", "colors": ["x", "F", "G"], "thresholds": [0.22, 0.5, 0.82], "dither": 0},
]
# The shadow's sharpest rim is drawn as t, a marker: gen.steam_light lights it mint near the neck and turns the rest to
# u, so no t is left in the art.


THIN = {"at": [56, -10], "area": [128, 64], "density": -0.45}
# A draft above the neck: an emitter with no amounts that eases the rising steam up and to the left and spreads it
# (expand), so the billows lean, widen with age and roll into each other (Pixelbolt has no height-varying wind).
DRAFT = {"at": [50, 24], "area": [100, 20], "rate": 0.05, "velocity": [-0.8, -0.45], "expand": 0.35}


def steam_source(origin=STEAM_ORIGIN, size=(STEAM_W, STEAM_H), billows=BILLOWS, thin=THIN, draft=DRAFT,
                 name="steam", wind=-0.035, breath=0.6, dissipation=0.04, buoyancy=0.2):
    """The steam over the flask's neck. `origin` is the canvas's top-left in the apparatus's (right-half) coordinates,
    so the phone hero can reuse it with its own canvas, billows, draft and dissolve."""
    ox, oy = origin
    w, h = size
    vx, vy = 128.0 - ox, 54.0 - oy
    rows = ["".join("A" if (y >= 56 - oy and NECK_COLS[0] - ox <= x <= NECK_COLS[1] - ox) else "." for x in range(w))
            for y in range(h)]
    # A thin, steady breath keeps the plume attached to the neck between billows.
    emitters = [{"name": "breath", "at": [vx, vy - 0.5], "radius": 2.0, "rate": 1, "density": breath, "temperature": 0.5,
                 "velocity": [0, -1.1], "noise": 0.15, "flicker": 0.2}]
    for i, (start, spin, side, radius, dens, up) in enumerate(billows, 1):
        emitters.append({"name": f"billow-{i}", "at": [vx, vy - 1], "radius": radius, "rate": 1, "start": start,
                         "end": start + 3, "density": dens, "temperature": 0.9, "falloff": 0.95,
                         "velocity": [side, up], "expand": 2.0, "noise": 0.1, "flicker": 0.15, "vortex": spin})
    emitters += [
        # Thin the steam smoothly with height (an ellipse centred above the canvas, strongest at the top edge), so
        # billows dissolve before the top margin instead of being cut flat by a band.
        *[dict({"name": f"thin-{k}" if isinstance(thin, list) else "thin", "rate": 1, "falloff": 1}, **t)
          for k, t in enumerate(thin if isinstance(thin, list) else [thin], 1)],
        *([dict({"name": "draft"}, **draft)] if draft else []),
    ]
    return {
        "format": "pixelforge-fluid", "version": 1, "name": name, "width": w, "height": h,
        "palette": PALETTE,
        "symbols": {"neck": rows},
        "effects": {name: {
            "frames": FRAMES, "duration": MS, "loop": True, "seed": 5, "warmup": 3,
            # Slow and heavy: modest lift, more drag, gentle swirl; no cooling, so the lift holds and billows roll into
            # each other in the draft rather than piling into one mass.
            "buoyancy": buoyancy, "vorticity": 0.35, "dissipation": dissipation, "cooling": 0, "drag": 0.09,
            "wind": [wind, 0],
            "obstacles": [{"symbol": "neck", "x": 0, "y": 0, "draw": "none"}],
            "emitters": emitters,
            "look": STEAM_LOOK,
            "cleanup": {"strays": True, "corners": True},
        }},
    }


# Drip: the coil's outlet tip over the beaker; the canvas is the beaker's inside, so its walls are the glass.
DRIP_ORIGIN = (56, 94)
DRIP_W, DRIP_H = 23, 33
TIP_X = 67 - DRIP_ORIGIN[0]      # bore column 11


def drip_source():
    rows = ["".join("A" if (y <= 5 and TIP_X - 1 <= x <= TIP_X + 1) else "." for x in range(DRIP_W))
            for y in range(DRIP_H)]
    tx = TIP_X + 0.5
    return {
        "format": "pixelforge-fluid", "version": 1, "name": "drip", "width": DRIP_W, "height": DRIP_H,
        "palette": PALETTE,
        "symbols": {"tip": rows},
        "effects": {"drip": {
            "kind": "liquid", "frames": DRIP_FRAMES, "duration": MS, "loop": True, "seed": 3, "warmup": 3,
            "walls": ["left", "right", "bottom"], "gravity": [0, 0.4], "flip": 0, "drag": 0.04, "tension": 2,
            "obstacles": [{"symbol": "tip", "x": 0, "y": 0, "draw": "none"}],
            "fill": [{"x": 0, "y": 23, "w": DRIP_W, "h": DRIP_H - 23}],
            "emitters": [
                {"name": "bead", "at": [tx, 7.0], "radius": 1.3, "rate": 1, "start": 16, "end": 26,
                 "velocity": [0, 0]},
                {"name": "swell", "at": [tx, 7.6], "radius": 1.5, "rate": 1, "start": 21, "end": 26,
                 "velocity": [0, 0]},
                {"name": "soak", "at": [DRIP_W / 2, 31], "area": [DRIP_W, 2], "rate": 1, "density": -0.004},
            ],
            "whitewater": [
                {"impact": 1.0, "chance": 0.5, "throw": 1.1, "spread": 35, "life": [6, 10],
                 "colors": ["n", "m"], "size": 1},
            ],
            "look": [
                {"field": "density", "colors": ["j"], "thresholds": [0.5], "dither": 0},
                {"field": "depth", "colors": ["l", "k", "j"], "thresholds": [1, 2, 4], "dither": 0},
                {"field": "speed", "colors": ["m"], "thresholds": [1.2], "dither": 0},
            ],
            "cleanup": {"strays": True},
        }},
    }


# Clouds outside the window: one canvas per pane (the mullion sits on the seam, so they can't share one).
# Full-width coordinates: left pane glass x 186-205, right pane x 210-229.
CLOUD_W, CLOUD_H = 20, 44
CLOUD_Y = 20
CLOUD_ORIGINS_FULL = {"clouds-l": (186, CLOUD_Y), "clouds-r": (210, CLOUD_Y)}


def clouds_source():
    def effect(seed, first, second):
        # Two banks a loop drift in from the left; the right pane's banks arrive about 24 frames after the left's,
        # as they would crossing the mullion. Bank 1 of the left pane crosses the moon (canvas rows 16-25).
        return {
            "frames": FRAMES, "duration": MS, "loop": True, "seed": seed, "warmup": 3,
            "buoyancy": 0, "vorticity": 0.7, "dissipation": 0.012, "cooling": 0.2, "drag": 0.02,
            "wind": [0.012, 0],
            "emitters": [
                # Each bank slides in from behind the casing: a short, fast push, so no half-disc sits at the edge.
                {"name": "bank-1", "at": [0.5, 18], "radius": 3.5, "rate": 1, "density": 0.4,
                 "start": first, "end": first + 4, "velocity": [1.1, -0.02],
                 "flicker": 0.5, "noise": 0.3, "falloff": 0.8},
                {"name": "bank-2", "at": [0.5, 31], "radius": 2.5, "rate": 1, "density": 0.32,
                 "start": second, "end": second + 3, "velocity": [1.0, 0.02],
                 "flicker": 0.5, "noise": 0.3, "falloff": 0.8},
                {"name": "leave", "at": [CLOUD_W - 1, CLOUD_H / 2], "area": [2, CLOUD_H], "rate": 1,
                 "density": -0.3},
            ],
            "look": [
                {"field": "density", "colors": ["9"], "thresholds": [0.05], "dither": 0.8, "pattern": "noise"},
                {"field": "density", "colors": ["A", "B"], "thresholds": [0.13, 0.28], "dither": 0.7, "pattern": "noise"},
                {"field": "light", "colors": ["C"], "thresholds": [0.55], "dither": 0.5},
            ],
        }
    return {
        "format": "pixelforge-fluid", "version": 1, "name": "clouds", "width": CLOUD_W, "height": CLOUD_H,
        "palette": PALETTE,
        "effects": {"clouds-l": effect(7, 8, 62), "clouds-r": effect(9, 32, 86)},
    }


ORIGINS = {"flask": FLASK_ORIGIN, "steam": STEAM_ORIGIN, "drip": DRIP_ORIGIN}


def main():
    FLUIDS.mkdir(exist_ok=True)
    for name, src in (("flask", flask_source()), ("steam", steam_source()), ("drip", drip_source()),
                      ("clouds", clouds_source())):
        (FLUIDS / f"{name}.fluid.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("fluid sources written")


if __name__ == "__main__":
    main()
