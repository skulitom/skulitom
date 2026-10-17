"""The hover burst for the site card: two drops in quick succession, 22 px apart, and their rings collide.

The pen dabs at x 66, slides to x 88 and dabs again. Each drop blooms into its own art-directed ring (the same
emitter rig as the main loop, see plume.py). The two facing lobes spin in opposite directions, so where they meet
they pair up and shoot upward between the rings: the collision is the simulation's own. 48 frames x 70 ms, starting
and ending on the main loop's calm frame so the site can swap in and out.

  python src/burst.py fluids   -> burst/fluids/*.fluid.json
  python src/burst.py recipe   -> burst/recipes/inkbolt-burst.json
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import fluids as F  # noqa: E402
import gen as G  # noqa: E402
from pb import at, fluid_frames, shade, write_json  # noqa: E402
from plume import plume_effect, plume_source  # noqa: E402

ROOT = HERE.parent
OUT = ROOT / "out"
FRAMES = 48
X1, X2 = 66, 98                 # the two dab points (nib tip columns)
HIT1, HIT2 = 10, 18             # the frames each drop meets the water
PALETTE = {"$ref": "../../../palette.json"}
DROP_W = 48                     # one liquid canvas spans both dab points
DROP_ORIGIN = (X1 - F.DROP_TIP, F.DROP_ORIGIN[1])


def pen_x(i):
    """The pen's tip column: dab at X1, slide to X2 (eased), dab, slide back for the calm close."""
    def ease(t):
        return t * t * (3 - 2 * t)
    if i < 5:
        return X1
    if i < 9:
        return round(X1 + (X2 - X1) * ease((i - 5) / 4))
    if i < 34:
        return X2
    if i < 44:
        return round(X2 + (X1 - X2) * ease((i - 34) / 10))
    return X1


def plume():
    look = [{"field": "density", "colors": ["p"], "thresholds": [0.11], "dither": 0},
            {"field": "density", "colors": ["W", "9", "8"], "thresholds": [0.15, 0.22, 0.42], "dither": 0},
            {"field": "light", "colors": ["r"], "thresholds": [0.75], "dither": 0}]
    common = dict(frames=FRAMES, depth=16, drift=0.0, g0=5, lr=5.5, lrate=0.6, ink_dx=2, ink_dy=1,
                  lobe_ink_r=1.6, lobe_ink=1.0, lobe_for=20, lobe_ink_at=3, blob_r=3, dens=0.9, stem=0.25, blob_y=4,
                  weight=0.08, vort=0.5, seed=13, look=look)
    # The facing lobes travel further, toward each other, and meet near x 84; the outer ones stay closer in.
    a = plume_effect(F.PLUME_W, F.PLUME_H, X1 - F.WATER_X0, HIT1, spin=(3.2, 4.4), g1=(11, 19), clear=(34, 48, 0.16),
                     **common)
    b = plume_effect(F.PLUME_W, F.PLUME_H, X2 - F.WATER_X0, HIT2, spin=(4.4, 3.2), g1=(15, 10), clear=None, **common)
    ems = [e for e in a["emitters"] if e["name"] != "stem"]
    ems += [dict(e, name="b-" + e["name"]) for e in b["emitters"] if e["name"] != "stem"]
    a["emitters"] = ems
    a["cleanup"] = {"strays": True}
    return plume_source("burst", F.PLUME_W, F.PLUME_H, a, palette=PALETTE)


def drop():
    src = F.drop()
    src["name"] = "burst-drop"
    src["width"] = DROP_W
    src["palette"] = PALETTE
    off = X2 - X1
    rows = []
    for r in src["symbols"]["nib"]:
        new = ["."] * DROP_W
        for x, c in enumerate(r):
            if c == "B":
                new[x] = new[x + off] = "B"
        rows.append("".join(new))
    src["symbols"]["nib"] = rows
    src["symbols"]["floor"] = ["B" * DROP_W] * (F.DROP_H - F.DROP_SURF)
    eff = src["effects"].pop("drop")
    eff["frames"] = FRAMES
    t = F.DROP_TIP
    eff["emitters"] = [
        {"name": "bead-1", "at": [t, 3.8], "radius": 1.2, "rate": 1, "start": 0, "end": 5, "velocity": [0, 0]},
        {"name": "swell-1", "at": [t, 4.6], "radius": 1.7, "rate": 1, "start": 1, "end": 5, "velocity": [0, 0]},
        {"name": "bead-2", "at": [t + off, 3.8], "radius": 1.2, "rate": 1, "start": 9, "end": 13, "velocity": [0, 0]},
        {"name": "swell-2", "at": [t + off, 4.6], "radius": 1.7, "rate": 1, "start": 10, "end": 13, "velocity": [0, 0]},
        {"name": "drain", "at": [DROP_W / 2, F.DROP_SURF - 1], "area": [DROP_W, 2], "rate": 1, "start": 0,
         "end": FRAMES, "density": -1},
    ]
    src["effects"] = {"burst-drop": eff}
    return src


def fluids():
    (OUT / "fluids").mkdir(parents=True, exist_ok=True)
    write_json(OUT / "fluids" / "burst-plume.fluid.json", plume(), compact=False)
    write_json(OUT / "fluids" / "burst-drop.fluid.json", drop(), compact=False)
    print("burst fluid sources written")


def recipe():
    plume_f = fluid_frames(OUT / "build" / "burst-plume.json", "burst")
    drop_f = fluid_frames(OUT / "build" / "burst-drop.json", "burst-drop")
    px0, py0 = F.PLUME_ORIGIN
    dx0, dy0 = DROP_ORIGIN
    frames = [{"name": "bg", "duration": F.MS, "ops": G.static_ops()}]
    for i in range(FRAMES):
        tip = (pen_x(i), G.TIP[1])
        ops = (G.caustics(i, hits=(HIT1, HIT2), frames=FRAMES) + at(plume_f[i], px0, py0) + at(drop_f[i], dx0, dy0)
               + [shade(G.WX0, G.TY0 + 1, G.WX1 - G.WX0 + 1, G.SURF - G.TY0 - 1, -1, over=["W", "Z", "9", "D", "E"])]
               + G.tank_glass() + G.ripple(i, HIT1, X1) + G.ripple(i, HIT2, X2) + G.pen(tip))
        frames.append({"name": f"burst-{i:02d}", "duration": F.MS, "from": "bg", "ops": ops})
    rec = {"version": 1, "name": "inkbolt-burst", "width": G.W, "height": G.H,
           "palette": {"$ref": "../../../palette.json"}, "ramps": G.RAMPS, "frames": frames,
           "animations": {"burst": {"frames": [f"burst-{i:02d}" for i in range(FRAMES)]}}}
    write_json(OUT / "recipes" / "inkbolt-burst.json", rec)
    print("burst recipe written")


if __name__ == "__main__":
    {"fluids": fluids, "recipe": recipe}[sys.argv[1]]()
