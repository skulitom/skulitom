"""Write the Inkbolt card's Pixelbolt fluid sources: the ink drop on the nib (liquid) and the plume in the tank (gas).

Python only lays out geometry and timing here (obstacle masks, emitter positions and windows). Every fluid pixel is
computed later by `pixelbolt compile`. Card coordinates are 192x100; each fluid canvas has an origin on the card.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from pb import write_json  # noqa: E402
from plume import plume_effect, plume_source  # noqa: E402

FLUIDS = HERE.parent / "out" / "fluids"
PALETTE = {"$ref": "../../../palette.json"}
FRAMES, MS = 72, 70
T0 = 25                       # the drop meets the water on this frame (the hit frame)

# Tank interior (water) on the card: x 32-139, surface row 36, floor row 83.
WATER_X0, WATER_X1, SURFACE, FLOOR = 32, 139, 36, 83
DROP_X = 66                   # where the drop falls (the nib tip's column)

PLUME_ORIGIN = (WATER_X0, SURFACE)
PLUME_W, PLUME_H = WATER_X1 - WATER_X0 + 1, FLOOR - SURFACE + 1   # 108 x 48
PLUME_CX = DROP_X - WATER_X0

DROP_W, DROP_H = 16, 18
DROP_TIP = 8                  # tip column in the drop canvas
DROP_SURF = 15                # canvas row of the water surface
DROP_ORIGIN = (DROP_X - DROP_TIP, SURFACE - DROP_SURF)             # (58, 21)


def plume():
    # Thin ink is a dark violet (p, a step below the water), body ink blue W, the rolled cores 9 and 8; a violet rim
    # where the ink faces the moon (upper left), from Pixelbolt's `light` field. Hard bands: no dither inside gas.
    look = [{"field": "density", "colors": ["p"], "thresholds": [0.11], "dither": 0},
            {"field": "density", "colors": ["W", "9", "8"], "thresholds": [0.15, 0.22, 0.42], "dither": 0},
            {"field": "light", "colors": ["r"], "thresholds": [0.85], "dither": 0}]
    eff = plume_effect(PLUME_W, PLUME_H, PLUME_CX, T0, frames=FRAMES, depth=18, spin=(3.4, 4.4), drift=0.8, g0=6,
                       g1=17, lr=6, lrate=0.6, ink_dx=1, ink_dy=1, lobe_ink_r=2.2, lobe_ink=1.2, lobe_for=34,
                       lobe_ink_at=4, blob_r=3, dens=1.2, stem=0.18, head_ink=1.0, blob_y=6, weight=0.08, vort=0.5, seed=11,
                       head_sway=2.5, trail=(10, 9, 3, 7, (1.2, 1.6), 0.0), clear=(54, 72, 0.2), look=look)
    eff["cleanup"] = {"strays": True}
    # The left lobe drifts into the upper-left corner and would linger as a bead: thin it there sooner.
    eff["emitters"].append({"name": "clear-left", "at": [9, 14], "area": [18, 24], "rate": 1, "start": 52,
                           "end": 72, "density": -0.15})
    return plume_source("plume", PLUME_W, PLUME_H, eff, palette=PALETTE)


def drop():
    """Modelled on examples/drip.fluid.json: flip 0, a bead held still under the nib by a zero-velocity emitter and
    a swell that fattens it, then gravity takes it. The water surface is an invisible floor; a drain just above it
    takes the drop into the tank in one frame, and whitewater throws a tiny crown off the impact."""
    nib = ["......BBBB......", ".......BB.......", ".......BB......."]
    floor = ["B" * DROP_W] * (DROP_H - DROP_SURF)
    eff = {"kind": "liquid", "frames": FRAMES, "duration": MS, "loop": True, "seed": 3, "warmup": 2,
           "walls": ["left", "right"], "gravity": [0, 0.45], "flip": 0, "drag": 0.04, "tension": 3.2,
           "obstacles": [{"symbol": "nib", "x": 0, "y": 0, "draw": "none"},
                         {"symbol": "floor", "x": 0, "y": DROP_SURF, "draw": "none"}],
           "emitters": [
               {"name": "bead", "at": [DROP_TIP, 3.8], "radius": 1.2, "rate": 1, "start": 7, "end": 20,
                "velocity": [0, 0]},
               {"name": "swell", "at": [DROP_TIP, 4.6], "radius": 1.7, "rate": 1, "start": 15, "end": 20,
                "velocity": [0, 0]},
               {"name": "drain", "at": [DROP_W / 2, DROP_SURF - 1], "area": [DROP_W, 2], "rate": 1, "start": 0,
                "end": FRAMES, "density": -1},
           ],
           "whitewater": [{"impact": 1.2, "chance": 0.9, "throw": 1.0, "spread": 35, "life": [5, 9],
                           "colors": ["F", "E", "D"], "size": 1, "trail": True}],
           "look": [{"field": "density", "colors": ["W"], "thresholds": [0.3], "dither": 0},
                    {"field": "shadow", "colors": ["9"], "thresholds": [0.8], "dither": 0},
                    {"field": "light", "colors": ["Z"], "thresholds": [0.8], "dither": 0}],
           "cleanup": {"strays": True}}
    return {"format": "pixelforge-fluid", "version": 1, "name": "drop", "width": DROP_W, "height": DROP_H,
            "palette": PALETTE, "symbols": {"nib": nib, "floor": floor}, "effects": {"drop": eff}}


def main():
    FLUIDS.mkdir(exist_ok=True)
    write_json(FLUIDS / "plume.fluid.json", plume(), compact=False)
    write_json(FLUIDS / "drop.fluid.json", drop(), compact=False)
    print("fluid sources written")


if __name__ == "__main__":
    main()
