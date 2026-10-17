"""Write the Nestbolt card's Pixelbolt fluid sources from the laser's timing.

smoke.fluid.json   the star: one gas sim over the cell. Emitters are chained along the head's path with start/end
                   windows, a suction emitter and a soak draw the smoke up into the extractor grille, vorticity curls
                   it, and embers ride the flow.
sparks.fluid.json  the cut point's spark spray (one short window per two frames, opposite to the head's travel), the
                   pierce blow-backs, and the tiny puffs when the bolt and then the whole nest settle.

Python only places emitters and timing here; every fluid pixel is computed later by `pixelbolt compile`.
"""

import json
import math
from pathlib import Path

import layout as L
import nest
import timing as T
from variant import BURST, SUFFIX
from ops import FLUID_PALETTE

HERE = Path(__file__).parent
FLUIDS = HERE.parent / "out" / "fluids"


def r1(v):
    return round(v, 1)


def at_frame(k):
    """Head state at frame k in smoke-canvas coordinates."""
    x, y, state, d = T.head_at(k)
    sx, sy = L.smoke((x, y))
    return sx, sy, state, d


# Spark-only effects carry no smoke: their density never reaches this layer's threshold.
NO_GAS = [{"field": "density", "colors": ["v"], "thresholds": [8]}]

# Settling dust: a thin burst that dissolves, no billow shading.
PUFF_LOOK = [
    {"field": "density", "colors": ["u", "v"], "thresholds": [0.05, 0.16], "dither": 0.7, "pattern": "noise"},
]

SMOKE_LOOK = [
    # the hero's steam look in smoke tones: flat billow bands (v body, w, x core) with no dither, the shadow side
    # falling to u, a light edge toward the moon, and only the thinnest smoke dissolving through a noise dither (the
    # warm underside near the cut is painted in the recipe, see gen.smoke_light)
    {"field": "density", "colors": ["u"], "thresholds": [0.08], "dither": 0.7, "pattern": "noise"},
    {"field": "density", "colors": ["v", "w", "x"], "thresholds": [0.22, 0.6, 1.35], "dither": 0},
    {"field": "shadow", "colors": ["u"], "thresholds": [0.4], "dither": 0},
    {"field": "light", "colors": ["x"], "thresholds": [0.6], "dither": 0},
]


def smoke_source():
    """The plume as billows, built like the hero's steam and the smoke-puff preset: a dense round puff born at the
    cut every four frames (a three-frame window, falloff 0.95, expanding, alternately spun so the stack rolls), hot
    when born so the sim's temperature lights it warm, cooling to grey as it rises and bends toward the extractor
    with vorticity curls, its thin edges dissolving by dither. Billows start with the bolt and run through the
    remnant cut (smaller there), so the nest is clear again when it settles. One sim carries them with the extractor's sink, a soak in the
    grille's upper slots and a draft along the back panel."""
    billows, spin = [], 1
    step, rad, dens, curl = (3, 3.8, 1.6, 1.0) if BURST else (4, 3.2, 1.5, 0.9)
    first = int(T.CONTOURS[0]["pierce"]) + 1
    last = int(T.CUT_END) - 9   # the last billows have risen clear by the settle
    for k in range(first, last + 1, step):
        f = next((f for f in (k + 1, k, k + 2, k + 3) if T.head_at(f)[2] in ("cut", "pierce")), None)
        if f is None:
            continue
        x, y, _, (ux, uy) = at_frame(f)
        # born just behind the head (on the fresh kerf), so a new billow never covers the nozzle; the remnant
        # cut's billows are smaller so the nest is clear again when it settles
        late = k >= T.CONTOURS[-1]["pierce"]
        e = {"name": f"billow-{k}", "at": [r1(x - 3 * ux), r1(y - 2 - 3 * uy)], "radius": rad * (0.8 if late else 1),
             "rate": 1, "start": k, "end": k + 3, "density": r1(dens * (0.7 if late else 1)), "temperature": 0.8,
             "falloff": 0.75, "expand": 1.1, "velocity": [0, -2.2 if late else -1.0],
             "noise": 0.3, "flicker": 0.2, "vortex": curl * spin}
        if len(billows) % 2 == 0:
            e["sparks"] = {"count": 0.6, "life": [8, 14], "colors": ["g", "f", "f", "e"], "angle": [235, 305],
                           "speed": [0.3, 0.8], "gravity": [0, -0.02], "drag": 0.05, "follow": 0.6}
        billows.append(e)
        spin = -spin
    dx, dy, dw, dh = L.DUCT
    cx, cy = dx + dw / 2 - L.SMOKE_X, dy + dh / 2 - L.SMOKE_Y
    draw_off = [
        # the extractor is a sink: it pulls the air in from all round, so the billows bend toward it
        {"name": "suction", "at": [r1(cx), r1(cy)], "radius": 28, "rate": 1, "density": 0, "expand": -2.4},
        # smoke is drawn in through the lower slots and vanishes in the upper ones
        {"name": "grille", "at": [r1(cx), r1(dy + 3.5 - L.SMOKE_Y)], "area": [dw - 6, 4], "rate": 1,
         "density": -0.9, "temperature": -0.9},
        # a draft along the back panel left of the grille (where most of the nest lies), so smoke rising there
        # bends in
        {"name": "draft-l", "at": [r1((dx - L.SMOKE_X) / 2), r1(cy + 4)], "area": [r1(dx - L.SMOKE_X), 18],
         "rate": 1, "density": 0, "velocity": [1.3, -0.5]},
    ]
    # The last billows (the L-bar's end, the remnant cut) get their own sim that rises harder and thins fast, so the sheet is clear when the
    # parts settle; the rest roll up slowly into the grille.
    split = T.CONTOURS[-2]["times"][-1] - 6   # billows born over the L-bar's last stretch and the remnant cut
    early = [b for b in billows if b["start"] < split]
    late = [b for b in billows if b["start"] >= split]
    common = {"frames": L.FRAMES, "duration": L.MS, "loop": True, "vorticity": 0.6, "cooling": 0.15, "drag": 0.05,
              "look": SMOKE_LOOK, "cleanup": {"strays": True, "corners": True}}
    effects = {"smoke-a": dict(common, seed=9, warmup=2, buoyancy=0.6, dissipation=0.08 if BURST else 0.065,
                               wind=[0.0, -0.06], emitters=early + draw_off)}
    if late:
        effects["smoke-b"] = dict(common, seed=10, warmup=2, iterations=24, buoyancy=1.0, dissipation=0.17,
                                  wind=[0.0, -0.1], emitters=late + draw_off)
    return {
        "format": "pixelforge-fluid", "version": 1, "name": "smoke", "width": L.SMOKE_W, "height": L.SMOKE_H,
        "palette": FLUID_PALETTE, "effects": effects,
    }


def spark_emitter(k, n):
    """Sparks thrown back along the cut from the head's position at frame k, for n frames."""
    x, y, state, (ux, uy) = at_frame(k + 0.5)
    back = math.degrees(math.atan2(-uy, -ux)) % 360 if (ux or uy) else 90
    return {"name": f"spray-{k}", "at": [r1(x), r1(y)], "radius": 0.5, "rate": 1, "start": k, "end": k + n,
            "sparks": {"count": 3.4 if BURST else 1.8, "life": [3, 8] if BURST else [3, 6],
                       "colors": ["R", "g", "f", "f"], "trail": True,
                       "angle": [r1(back - 55), r1(back + 55)], "speed": [1.2, 3.0], "drag": 0.15,
                       "gravity": [0, 0.22], "follow": 0}}


def sparks_source():
    cutting = [k for k in range(L.FRAMES) if T.head_at(k + 0.5)[2] == "cut"]
    sprays = []
    n = 1 if BURST else 2   # the racing head needs a spray window every frame
    k = cutting[0]
    while k <= cutting[-1]:
        if k in cutting:
            sprays.append(spark_emitter(k, n))
        k += n
    for c in T.CONTOURS:
        x, y = L.smoke(c["pts"][0])
        k = math.floor(c["pierce"])
        sprays.append({"name": f"pierce-{k}", "at": [r1(x), r1(y)], "radius": 0.5, "burst": 1, "start": k,
                       "sparks": {"count": 12 if BURST else 7, "life": [3, 7], "colors": ["R", "g", "g", "f", "f"],
                                  "trail": True,
                                  "angle": [195, 345], "speed": [1.4, 3.2], "drag": 0.1, "gravity": [0, 0.3],
                                  "follow": 0}})
    # A recipe holds 256 frames, so the sparks share two effects (16 emitters each) and the puffs take a third.
    effects = {}
    for i in range(0, len(sprays), 16):
        effects[f"spray-{i // 16}"] = {"frames": L.FRAMES, "duration": L.MS, "loop": True, "seed": 21 + i,
                                       "warmup": 1, "substeps": 1, "iterations": 1, "emitters": sprays[i:i + 16],
                                       "look": NO_GAS}
    # Tiny puffs where freed parts settle: the bolt first, then the whole nest along the remnant cut.
    bolt_close = T.closed_at(0)
    puffs = []
    bx, by = L.smoke((44, 8))
    puffs.append({"name": "puff-bolt", "at": [r1(bx), r1(by - 4)], "area": [6, 1], "rate": 1, "start": bolt_close,
                  "end": bolt_close + 2, "density": 0.35, "temperature": 0.5, "falloff": 0.9, "expand": 1.2,
                  "noise": 0.4})
    # (the corner puffs at the settle read as grey clumps at 2 CSS px, so the settle shows by the drop and its
    # shadowed gaps alone)
    effects["puff"] = {"frames": L.FRAMES, "duration": L.MS, "loop": True, "seed": 13, "warmup": 1,
                       "buoyancy": 0.5, "vorticity": 0.5, "dissipation": 0.38, "drag": 0.1, "emitters": puffs,
                       "look": PUFF_LOOK, "cleanup": {"strays": True}}
    return {"format": "pixelforge-fluid", "version": 1, "name": "sparks", "width": L.SMOKE_W, "height": L.SMOKE_H,
            "palette": FLUID_PALETTE, "effects": effects}


def main():
    FLUIDS.mkdir(parents=True, exist_ok=True)
    for name, src in (("smoke", smoke_source()), ("sparks", sparks_source())):
        src["name"] += SUFFIX
        (FLUIDS / f"{name}{SUFFIX}.fluid.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8",
                                                   newline="\n")
    print("fluid sources written:", ", ".join(sparks_source()["effects"]))


if __name__ == "__main__":
    main()
