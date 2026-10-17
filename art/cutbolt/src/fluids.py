"""Write the Cutbolt card's Pixelbolt fluid source: the developer in the shallow glass tray and the drops that fall
off the film's lower edge into it.

Python only lays out the emitters and their timing here; every fluid pixel is computed by `pixelbolt compile`.
Local coordinates: the fluid canvas is the tray's inside (scene x 17-144, y 50-87).
"""

import json
from pathlib import Path

import scene as S

HERE = Path(__file__).parent
FLUIDS = HERE.parent / "out" / "fluids"


def local(x, y):
    return [x - S.FLUID_X, y - S.FLUID_Y]


def drip_emitters(name, x, start, release, big=False):
    """A bead gathers under the film's lower edge and hangs still, small and round, held where it hangs (big: it
    grows a little at each pull, as the pull wipes developer down the edge). The pull at `release` shakes it off; for the big one that pull also wipes
    a slug of developer down the edge into it, so a full round drop falls and lands with a crown."""
    bx, by = local(x + 0.5, S.film_bottom(x) + 1)
    cy = by + 1.0
    em = [{"name": f"{name}-bead", "at": [bx, cy], "radius": 1.4 if big else 1.5, "rate": 1, "start": start,
           "end": release, "velocity": [0, 0]}]
    if big:
        for i, (g, r) in enumerate(zip(range(start + 6, release, 6), (1.7, 2.0))):
            em.append({"name": f"{name}-swell{i}", "at": [bx, cy + 0.3 * (i + 1)], "radius": r, "rate": 1,
                       "start": g, "end": release, "velocity": [0, 0]})
        em.append({"name": f"{name}-slug", "at": [bx, cy + 1.5], "radius": 2.5, "burst": 1, "start": release,
                   "velocity": [0, 0.9]})
    # Holds the bead still (adds no water), centred on it, so it hangs round instead of dribbling a point.
    em.append({"name": f"{name}-hold", "at": [bx, cy + 1.4], "radius": 3.6 if big else 2.6, "rate": 1,
               "start": start, "end": release, "density": 0, "velocity": [0, 0]})
    em.append({"name": f"{name}-flick", "at": [bx, cy + 1.0], "radius": 3.6 if big else 3.0, "rate": 1,
               "start": release, "end": release + 1, "density": 0, "velocity": [0, 0.9]})
    return em


def tray_source(burst=False):
    w, h = S.FLUID_W, S.FLUID_H
    surf = S.FILL_Y - S.FLUID_Y                   # the fill line; the surface settles 2 px above it
    rest = S.SURFACE - S.FLUID_Y
    body = [w / 2, surf + (h - surf) / 2]
    seam_x, seam_start, seam_release = S.DRIPS[0]
    sx = local(seam_x + 0.5, 0)[0]
    emitters = [
        # A slow rock of the whole bath, once a loop.
        {"name": "rock-r", "at": body, "area": [w, h - surf], "rate": 0.06, "density": 0, "velocity": [0.5, 0],
         "pulse": {"amplitude": 1, "period": S.FRAMES, "phase": 0}},
        {"name": "rock-l", "at": body, "area": [w, h - surf], "rate": 0.06, "density": 0, "velocity": [-0.5, 0],
         "pulse": {"amplitude": 1, "period": S.FRAMES, "phase": 180}},
        # The rebound after the seam drop: the crater closes and throws a little jet back up.
        {"name": "jet", "at": [sx, rest + 1.5], "area": [3, 3], "rate": 1, "start": 1, "end": 3, "density": 0,
         "velocity": [0, -2.2]},
        # Keep the level: drain what the drops add.
        {"name": "drain", "at": [w / 2, h - 1.5], "area": [w - 6, 2], "rate": 1, "density": -0.0025},
    ]
    if burst:
        emitters = [e for e in emitters if e["name"] != "jet"]
        # Hover burst: the film yanks every 3 frames and shakes a drop off at four of the pulls; the bath rocks harder.
        for e in emitters[:2]:
            e["rate"] = 0.06
        for i, (x, start, release) in enumerate(S.BURST_DRIPS):
            emitters += drip_emitters(f"drip{i}", x, start, release)
    else:
        emitters += drip_emitters("seam", seam_x, seam_start, seam_release, big=True)
        for i, (x, start, release) in enumerate(S.DRIPS[1:]):
            emitters += drip_emitters(f"drip{i + 1}", x, start, release)
    assert len(emitters) <= 16, len(emitters)
    spray = 1.25 if burst else 1.0           # the hover burst throws higher, fuller crowns
    return {
        "format": "pixelforge-fluid", "version": 1, "name": "tray-burst" if burst else "tray", "width": w, "height": h,
        "palette": {"$ref": "../../../palette.json"},
        "effects": {"tray": {
            "kind": "liquid", "frames": S.FRAMES, "duration": S.MS, "loop": True, "seed": 7, "warmup": 3,
            "walls": ["left", "right", "bottom"], "gravity": [0, 0.45], "flip": 0.2, "drag": 0.03, "tension": 2.3,
            "fill": [{"x": 0, "y": surf, "w": w, "h": h - surf}],
            "emitters": emitters,
            "whitewater": [
                # A small crown: spray thrown where a drop strikes the pool.
                {"impact": 1.5, "chance": min(0.9, 0.4 * spray), "throw": 1.35 * spray, "spread": 20, "life": [7, 12],
                 "colors": ["Y", "X", "V"]},
                # Foam that rides the ripples afterwards.
                {"impact": 1.2, "chance": 0.3, "throw": 0.3, "spread": 70, "life": [14, 24],
                 "colors": ["Y", "Y", "X"], "follow": 0.7},
            ],
            "look": [
                {"field": "density", "colors": ["T"], "thresholds": [0.5], "dither": 0},
                # Colours as seen through the tray's glass; the recipe lifts whatever is above the rim one step.
                # One dark body with a lit 2 px edge (so ripples read), and the deep floor of the bath.
                {"field": "depth", "colors": ["V", "U", "T", "S"], "thresholds": [1, 2, 3, 9], "dither": 0},
                # Fast water (the falling drop, the crown) brightens.
                {"field": "speed", "colors": ["V", "X"], "thresholds": [1.8, 3.0], "dither": 0},
            ],
            "cleanup": {"strays": True},
        }},
    }


def main():
    FLUIDS.mkdir(exist_ok=True)
    for name, burst in (("tray", False), ("tray-burst", True)):
        src = tray_source(burst)
        (FLUIDS / f"{name}.fluid.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("fluid sources written")


if __name__ == "__main__":
    main()
