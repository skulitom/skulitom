"""Write the card's fluid sources (src/fluids/*.fluid.json): the pour, the smoke, the dust puff and the embers.

Positions come from design.py. Each source is an ordinary pixelforge-fluid file that Pixelbolt compiles; this script
only writes JSON.
"""

import json
from pathlib import Path

import design as D

HERE = Path(__file__).parent
OUT = HERE.parent / "out" / "fluids"
PALETTE = {"$ref": "../../../palette.json"}
SUFFIX = "-burst" if D.BURST else ""


def mould_obstacle():
    """The closed mould in pour-canvas coordinates: solid block, star cavity at 4x, a two-step chamfer at the gate."""
    bx, by, bw, bh = D.POUR_BOX
    mx, my, mw, mh = D.MOULD
    cx, cy = D.CAVITY
    rows = []
    for y in range(by, by + bh):
        r = []
        for x in range(bx, bx + bw):
            solid = mx <= x < mx + mw and my <= y < my + mh
            sx, sy = (x - cx) // D.SCALE, (y - cy) // D.SCALE
            if x >= cx and y >= cy and sx < 7 and sy < 7 and D.STAR[sy][sx] == "#":
                solid = False
            g0, g1 = D.TOP_POINT
            if y == my and g0 - 3 <= x <= g1 + 3:
                solid = False
            if y == my + 1 and g0 - 2 <= x <= g1 + 2:
                solid = False
            if y == my + 2 and g0 - 1 <= x <= g1 + 1:
                solid = False
            if my + 2 <= y < cy and g0 <= x <= g1:
                solid = False
            r.append("C" if solid else ".")
        rows.append("".join(r))
    return rows


# Spout tip at the pour angle, in card pixels (matches the crucible pose; see poses.py).
SPOUT = (101.5, 30.0)


def pour():
    bx, by, bw, bh = D.POUR_BOX
    return {
        "kind": "liquid", "frames": D.POUR_FRAMES, "duration": D.MS, "seed": 11,
        "walls": ["bottom"], "gravity": [0, 0.42], "flip": 0.3, "drag": 0.02, "tension": 1.2, "substeps": 3,
        "obstacles": [{"symbol": "mould", "x": 0, "y": 0, "draw": "none"}],
        "emitters": [
            {"name": "spout", "at": [SPOUT[0] - bx, SPOUT[1] - by], "radius": D.POUR_RADIUS, "rate": 1, "start": 0, "end": D.POUR_END,
             "velocity": [0.1, 4.4]},
            # Once the cavity is nearly full, calm its body so trapped air can rise out (adds no metal).
            {"name": "calm", "at": [D.CAVITY[0] + 14 - bx, D.CAVITY[1] + 18 - by], "area": [20, 12], "rate": 1,
             "start": 33, "end": D.POUR_FRAMES, "density": 0, "velocity": [0, 0]},
            {"name": "calm-gate", "at": [D.CAVITY[0] + 14 - bx, D.CAVITY[1] + 1 - by], "area": [12, 12], "rate": 1,
             "start": 36, "end": D.POUR_FRAMES, "density": 0, "velocity": [0, 0]},
        ],
        "whitewater": [
            {"impact": 1.7, "chance": min(1.0, round(0.6 * D.SPARKS, 3)), "throw": 1.6 * D.SPARKS ** 0.5, "spread": 40,
             "life": [5, 9], "colors": ["g", "f", "e", "d"]},
            {"impact": 2.9, "chance": min(1.0, round(0.35 * D.SPARKS, 3)), "throw": 1.4 * D.SPARKS ** 0.5, "spread": 25,
             "life": [5, 8], "colors": ["g", "g", "f", "e"], "size": 2},
            # the crown: slower drops thrown up and out round the plunge point as the cavity fills
            {"impact": 1.25, "chance": min(1.0, round(0.3 * D.SPARKS, 3)), "throw": 1.0, "spread": 50, "life": [5, 8],
             "colors": ["g", "f", "f", "e"]},
        ],
        "look": [
            {"field": "density", "colors": ["e"], "thresholds": [0.2], "dither": 0},
            {"field": "depth", "colors": ["g", "f", "e"], "thresholds": [1, 2, 5], "dither": 0},
            {"field": "speed", "colors": ["f", "g"], "thresholds": [1.8, 3.2], "dither": 0},
        ],
        "cleanup": {"strays": True},
    }


GATE = (101.5, 45.5)                     # top of the gate, where the hot metal breathes smoke
PUFFS = [(17, 1.2, 0.35, 0.6), (28, 1.15, 0.5, -0.6), (39, 0.85, 0.3, 0.5)]   # (card frame, strength, drift, spin)
# Built the way Pixelbolt's steam-vent preset builds its puffs: each billow is a soft ball with a dense core and a
# body, given a little drift and spin, and a hard gap after it (density and heat both cut at the vent) parts it from
# the next; a wide, gentle updraft over the whole canvas keeps them rising apart. The look is plain dithered density
# bands, no lit caps or rims, so nothing outlines the gas. The vent sits at the gate's right edge, in open air.


def smoke():
    bx, by, bw, bh = D.SMOKE_BOX
    vx, vy = GATE[0] + 4 - bx, GATE[1] - 1 - by
    emitters = [{"name": "updraft", "at": [vx + 14, vy - 20], "radius": 22, "rate": 0.2, "velocity": [0.35, -2.2],
                 "expand": 4}]
    for i, (start, k, drift, spin) in enumerate(PUFFS):
        emitters += [
            {"name": f"puff{i}", "at": [vx, vy], "radius": 4.5, "rate": 1, "start": start, "end": start + 2,
             "density": round(0.32 * k * D.SMOKE, 3), "temperature": 0.8, "velocity": [drift, -2], "expand": 1,
             "noise": 0.8, "flicker": 0.3, "vortex": spin},
            {"name": f"body{i}", "at": [vx, vy], "radius": 3, "rate": 1, "start": start, "end": start + 2,
             "density": round(0.45 * k * D.SMOKE, 3), "flicker": 0.3},
            {"name": f"core{i}", "at": [vx, vy], "radius": 1.5, "rate": 1, "start": start, "end": start + 1,
             "density": round(1.6 * k * D.SMOKE, 3)},
            {"name": f"gap{i}", "at": [vx, vy - 1], "area": [16, 6], "rate": 1, "start": start + 3, "end": start + 8,
             "density": -1, "temperature": -1},
        ]
    emitters += [{"name": "thin", "at": [bw / 2, 15], "area": [bw, 30], "rate": 1, "density": -0.1},
                 {"name": "fade", "at": [bw / 2, 2], "area": [bw, 5], "rate": 1, "density": -0.4},
                 {"name": "clear", "at": [bw / 2 + 6, bh / 2 - 6], "area": [bw - 12, bh - 12], "rate": 1,
                  "start": 54, "density": -0.1}]
    return {
        "frames": D.FRAMES, "duration": D.MS, "loop": True, "seed": 2, "warmup": 2,
        "buoyancy": 0.25, "vorticity": 0.6, "dissipation": 0.11, "cooling": 0.1, "drag": 0.04,
        "wind": [0.02, 0], "emitters": emitters,
        "look": [
            {"field": "density", "colors": ["t"], "thresholds": [0.22], "dither": 0.65},
            {"field": "density", "colors": ["u"], "thresholds": [0.27], "dither": 0.45},
            {"field": "density", "colors": ["v", "w"], "thresholds": [0.42, 1], "dither": 0.6},
        ],
        "cleanup": {"strays": True, "corners": True},
    }


FEET = (130.5, 146.5)                   # the landed star's two feet, card x
FLOOR_Y = 78.5


def dust():
    """A low haze of bench dust where the star lands: two flat kicks thrown fast sideways along the bench, drawn only
    as ordered dither in two greys, gone in 4 frames."""
    bx, by, bw, bh = D.DUST_BOX
    emitters = []
    for i, (x, side) in enumerate(((FEET[0] - 2, -1), (FEET[1] + 2, 1))):
        emitters.append({"name": f"kick{i}", "at": [x - bx, FLOOR_Y - 1 - by], "area": [12, 2], "rate": 1, "end": 2,
                         "density": 0.9, "falloff": 0.6, "expand": 0.2, "velocity": [2.6 * side, 0],
                         "noise": 0.15})
    return {
        "frames": 4, "duration": D.MS, "seed": 3, "buoyancy": 0.0, "weight": 0.02, "vorticity": 0.05,
        "dissipation": 0.45, "drag": 0.15, "walls": ["bottom"], "emitters": emitters,
        "look": [
            {"field": "density", "colors": ["u", "v"], "thresholds": [0.25, 0.6], "dither": 1.0},
        ],
        "cleanup": {"strays": True},
    }


def embers():
    bx, by, bw, bh = D.EMBER_BOX
    return {
        "frames": 24, "duration": D.MS, "loop": True, "seed": 5, "buoyancy": 0.3, "vorticity": 0.4,
        "dissipation": 0.2, "cooling": 0.1,
        "emitters": [{"name": "mouth", "at": [D.PIVOT[0] - bx, 21 - by], "area": [10, 2], "rate": 1, "density": 0,
                      "temperature": 0.5, "noise": 0.3,
                      "sparks": {"count": 0.8, "life": [12, 22], "colors": ["g", "f", "e", "d", "c"],
                                 "speed": [0.2, 0.5], "angle": [255, 285], "gravity": [0, -0.03], "drag": 0.05}}],
        "look": [{"field": "density", "colors": ["t"], "thresholds": [5], "dither": 0}],
    }


def write(name, effects, symbols=None):
    box = {"pour": D.POUR_BOX, "smoke": D.SMOKE_BOX, "dust": D.DUST_BOX, "embers": D.EMBER_BOX}[name]
    src = {"format": "pixelforge-fluid", "version": 1, "name": name, "width": box[2], "height": box[3],
           "palette": PALETTE}
    if symbols:
        src["symbols"] = symbols
    src["effects"] = effects
    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}{SUFFIX}.fluid.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8", newline="\n")


def main():
    write("pour", {"pour": pour()}, {"mould": mould_obstacle()})
    write("smoke", {"smoke": smoke()})
    write("dust", {"dust": dust()})
    write("embers", {"embers": embers()})


if __name__ == "__main__":
    main()
