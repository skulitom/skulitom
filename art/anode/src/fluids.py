"""Write the Anode card's two mist sources from the cursor path in path.py.

build/fog.fluid.json   a pale fog bank rolling slowly along the back room's floor round the agent's desk (dry-ice
                       style: `weight` keeps it low), with billowy shaded tops, spilling out over the threshold onto
                       your floor; the cursor's low swoop cuts through it.
build/wisps.fluid.json thin pale wisps drifting under the arch above the monitor; the high swoop cuts through them.
The screen stays clear between the two. In both, the cursor's soak rides its swoop (`expand` parts the mist) and two
pulsed swirl emitters on the wake's edges shed alternating eddies, so the parted lips curl before the mist closes.
Canvas coordinates are card coordinates minus each canvas's origin.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import path as P  # noqa: E402
from layout import BURST, FOG, PATH, WISPS  # noqa: E402

BUILD = Path(__file__).resolve().parents[1] / "out" / "build"
PALETTE = {"$ref": "../../../palette.json"}

# Soft cushions in the smoke-puff look: a Bayer-dithered thin edge (u), a v rim, a w body, the moon lighting the
# upper-left faces (x, then steel F at the crest). Low cushions keep a v shadow underneath; high ones, hanging above
# the agent's screen, catch its light on their lower faces in mint (l) instead.
def look(underside, shadow=0.25):
    return [
        {"field": "density", "colors": ["u"], "thresholds": [0.11], "dither": 0.5},
        {"field": "density", "colors": ["v"], "thresholds": [0.18], "dither": 0.3},
        {"field": "density", "colors": ["w"], "thresholds": [0.35], "dither": 0.3},
        {"field": "shadow", "colors": [underside], "thresholds": [shadow], "dither": 0.4},
        {"field": "light", "colors": ["x", "F"], "thresholds": [0.3, 0.65], "dither": 0},
    ]


def to(canvas, pt):
    return [round(pt[0] - canvas[0], 3), round(pt[1] - canvas[1], 3)]


def wake(canvas, arc, start, end, tag, spin=0.4, expand=0.3):
    """The cursor's soak along one straight leg of a swoop (`start`-`end`), where it crosses its cushion: the dive
    through the low one, the climb through the high one. The swoops' tight turns stay out of the mist, so the wake is
    one clean channel, not a ring. Plus the two eddy shedders on the wake's edges."""
    at = to(canvas, arc.c)
    orbit = arc.orbit()
    turn = 1 if arc.period > 0 else -1
    out = [{"name": f"wake-{tag}", "at": at, "radius": 3.5, "rate": 1, "start": start, "end": end, "density": -0.5,
            "orbit": orbit}]
    if expand:
        out[0]["expand"] = expand
    gap, lag = 3, 20
    for k, (dr, s, ph) in enumerate(((-gap, spin, 0), (gap, -spin, 180))):
        # A steady counter-rotating pair either side of the path: forward flow down the channel, backward flow
        # outside it, so the lips roll in behind the cursor.
        out.append({"name": f"eddy-{tag}{k}", "at": at, "radius": 3, "rate": 1, "start": start, "end": end,
                    "vortex": s * turn,
                    "orbit": {"radius": [round(arc.rx + dr, 3), round(arc.ry + dr, 3)], "period": orbit["period"],
                              "phase": round((orbit["phase"] - lag * turn) % 360, 3)}})
    return out


def lobe_wake(canvas, lobe, start, end, tag, spin=2.0):
    """The burst's soak round one lobe of the figure-eight, with strong, quick eddy shedders on both edges."""
    at = to(canvas, lobe.c)
    orbit = lobe.orbit()
    turn = 1 if lobe.period > 0 else -1
    out = [{"name": f"zip-{tag}", "at": at, "radius": 3, "rate": 1, "start": start, "end": end, "density": -0.95,
            "expand": 1.0, "orbit": orbit}]
    for k, (dr, s, ph) in enumerate(((-3, spin, 0), (3, -spin, 180))):
        out.append({"name": f"curl-{tag}{k}", "at": at, "radius": 3, "rate": 1, "start": start, "end": end,
                    "vortex": s * turn, "pulse": {"amplitude": 1, "period": 4, "phase": ph},
                    "orbit": {"radius": [lobe.rx + dr, lobe.ry + dr], "period": orbit["period"],
                              "phase": round((orbit["phase"] - 30 * turn) % 360, 3)}})
    return out


def cushion(name, at, start, radius, lobes=None):
    """One soft cushion, cumulus-fashion: a domed middle billow over two lower ones either side (a flat-ish base)
    grown in the same short window behind the left wall (falloff 0.95, gentle `expand`), which then drift slowly right
    on the wind together and thin as they go."""
    x, y = at
    lobes = lobes or ((0, -0.5, 1), (-3, 2, 0.75), (3, 2, 0.7))
    return [{"name": f"{name}-{k}", "at": [x + dx, y + dy], "radius": round(radius * r, 2), "rate": 1, "start": start,
             "end": start + 4, "density": 1.3, "falloff": 0.95, "expand": 0.35, "noise": 0.06}
            for k, (dx, dy, r) in enumerate(lobes)]


def fades(w, h, bottom):
    # The right fade lives behind the right jamb (card x 160 on), so cushions leave whole instead of being eaten into
    # points while still in view.
    return [{"name": "fade-r", "at": [w, h / 2], "area": [26, 128], "rate": 1, "density": -0.6},
            {"name": "fade-t", "at": [w / 2, 0], "area": [w, 8], "rate": 1, "density": -0.4, "falloff": 1},
            {"name": "fade-b", "at": [w / 2, h], "area": [w, bottom], "rate": 1, "density": -0.35, "falloff": 1}]


def effect(frames, seed, emitters, underside, weight, shadow=0.25):
    return {"frames": frames, "duration": 70, "loop": True, "seed": seed, "warmup": 3, "buoyancy": 0.0,
            "weight": weight, "vorticity": 0.12, "dissipation": 0.012, "drag": 0.03, "wind": [0.011, 0],
            "emitters": emitters, "look": look(underside, shadow), "cleanup": {"strays": True, "corners": True}}


# Birth frames are timed so the low cushion is under the left of the agent's desk when the low swoop dives through it,
# and the high cushion is above the monitor's right half for the high swoop's climb.
LOW_BIRTH, HIGH_BIRTH = 26, 38
LOW_LEG = (P.ARC1[0], P.ARC1[0] + 8)      # the dive, x ~121-125
HIGH_LEG = (P.ARC2[0], P.ARC2[0] + 8)     # the climb, x ~143-138


def heal(canvas, centre, start, size, frames=P.FRAMES, length=8):
    """Behind the cursor the channel closes: a soft, low refill stretched along the cut (a box the cut's length, its
    density falling off to the rim) tops it up for a few frames; the drift closes the rest. No sink: a converging
    flow gathers the parted mist into a ball."""
    return [{"name": "refill", "at": to(canvas, centre), "area": size, "rate": 1, "start": start,
             "end": min(start + length, frames), "density": 0.3, "falloff": 0.9}]


def fog(burst=False):
    """The low cushions, rolling round the agent's desk; one is born each loop."""
    x, y, w, h = FOG
    frames = P.BURST_FRAMES if burst else P.FRAMES
    birth = 0 if burst else LOW_BIRTH
    emitters = cushion("cushion", [11, 17], birth, 7, lobes=((0, 0, 1), (-3.5, 1, 0.8), (3.5, 1, 0.75)))
    emitters += fades(w, h, 26)
    if burst:
        emitters += lobe_wake(FOG, BURST.a, *P.LOBE_A, "a") + lobe_wake(FOG, BURST.b, *P.LOBE_B, "b")
        emitters += heal(FOG, BURST.x, P.LOBE_B[1], [24, 10], frames=P.BURST_FRAMES)   # the mist settles after
    else:
        emitters += wake(FOG, PATH.arc1, *LOW_LEG, "a", spin=0.2, expand=0) + heal(FOG, (122, 66), LOW_LEG[1], [14, 10], length=16)
    return source("fog-burst" if burst else "fog", w, h, effect(frames, 7, emitters, "v", 0.02))


def wisps(burst=False):
    """The high cushions, drifting under the lintel above the monitor; one is born each loop."""
    x, y, w, h = WISPS
    frames = P.BURST_FRAMES if burst else P.FRAMES
    birth = 24 if burst else HIGH_BIRTH
    emitters = cushion("cushion", [11, 18], birth, 6.5, lobes=((0, 0, 1), (-3, 1.5, 0.8))) + fades(w, h, 10)
    if not burst:
        emitters += wake(WISPS, PATH.arc2, *HIGH_LEG, "b") + heal(WISPS, (141, 30), HIGH_LEG[1], [5, 14])
    e = effect(frames, 11, emitters, "l", 0.0, shadow=0.5)
    if burst:   # a 48-frame loop would line its cushions up into a bar: thin and hurry them so one shows at a time
        e.update(dissipation=0.035, wind=[0.03, 0])
    return source("wisps-burst" if burst else "wisps", w, h, e)


def source(name, w, h, effect):
    assert len(effect["emitters"]) <= 16, (name, len(effect["emitters"]))
    return {"format": "pixelforge-fluid", "version": 1, "name": name, "width": w, "height": h,
            "palette": PALETTE, "effects": {name: effect}}


def main():
    BUILD.mkdir(exist_ok=True)
    for src in (fog(), wisps(), fog(burst=True), wisps(burst=True)):
        name = src["name"]
        (BUILD / f"{name}.fluid.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"{name}: {len(src['effects'][name]['emitters'])} emitters")


if __name__ == "__main__":
    main()
