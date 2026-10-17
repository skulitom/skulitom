"""The ink plume: a gas whose density is the ink, with weight so it sinks and vorticity so its lobes curl.

Pixelbolt's gas is well damped at one cell per pixel, so the ring is art-directed: a head emitter pushes the flow down
along a vertical 'orbit' (easing out as it sinks), and two lobe emitters spin the flow either side of it while they
spread apart, riding ellipse orbits. Ink is fed in at the head and just below each lobe core, and the spin wraps it into
the curls. Everything after the emitters stop is the simulation's own: the ring slows, sags and thins.
Python only places emitters and timings here.
"""

PALETTE = {"$ref": "../../../palette.json"}


def plume_effect(W, H, cx, t0, frames=72, depth=24, y0=7, push=1.2, spin=(2.8, 2.6), g0=6, g1=11, hr=4,
                 drive=18, lobe_for=26, ink_for=12, blob_r=4, dens=1.4, lr=4, lrate=0.5, weight=0.04, vort=0.5,
                 iterations=40, head_rate=0.6, lobe_ink=0.9, head_ink=0.8, ink_dy=0, clear=(62, 72, 0.3), seed=7,
                 drift=0.0, stem=0.6, blob_y=4, tendrils=None, ink_dx=0, lobe_ink_r=1.8, lobe_ink_at=2, trail=None, head_sway=0.0, look=None, walls=("left", "right", "top", "bottom")):
    ph = -360 * t0 / frames
    # head_sway bends the head's path: a quarter ellipse that drifts that many pixels left as it sinks, so the stem
    # it leaves is a gentle curve rather than a ruled line.
    head_orbit = {"radius": [head_sway, depth], "period": frames, "phase": ph}
    e = [
        {"name": "blob", "at": [cx, blob_y], "radius": blob_r, "rate": 1, "start": t0, "end": t0 + 3, "density": dens,
         "velocity": [0, 1.5], "falloff": 0.6},
        {"name": "stem", "at": [cx, 2], "radius": 1.2, "rate": 1, "start": t0, "end": t0 + 10, "density": stem,
         "velocity": [0, 0.5]},
        {"name": "head", "at": [cx + drift - head_sway, y0], "radius": hr, "rate": head_rate, "start": t0, "end": t0 + drive,
         "velocity": [0, push], "orbit": head_orbit},
        {"name": "head-ink", "at": [cx + drift - head_sway, y0], "radius": 3, "rate": 1, "start": t0 + 1, "end": t0 + ink_for,
         "density": head_ink, "orbit": head_orbit},
    ]
    spread = g1 if isinstance(g1, (tuple, list)) else (g1, g1)   # how far each lobe travels out: left, right
    for side, sgn, s, gs in (("l", -1, spin[0], spread[0]), ("r", 1, spin[1], spread[1])):
        orb = {"radius": [abs(gs - g0), depth], "period": frames if sgn < 0 else -frames,
               "phase": ph if sgn < 0 else 180 + 360 * t0 / frames}
        lx = cx + drift + sgn * gs
        e.append({"name": f"lobe-{side}", "at": [lx, y0], "radius": lr, "rate": lrate, "start": t0 + 2,
                  "end": t0 + lobe_for, "vortex": -sgn * s, "orbit": orb})
        if lobe_ink:
            e.append({"name": f"lobe-{side}-ink", "at": [lx + sgn * ink_dx, y0 + ink_dy], "radius": lobe_ink_r, "rate": 1, "start": t0 + lobe_ink_at,
                      "end": t0 + ink_for, "density": lobe_ink, "orbit": orb})
    # Follow-through: as the ring slows, a small head under each lobe pulls a tendril down with a little cap on it
    # (the secondary rings of an ink 'chandelier'). tendrils = (start, depth, push, ink, [(dx, spin), ...]).
    if tendrils:
        ts, tdepth, tpush, tink, arms = tendrils
        tph = -360 * ts / frames
        for i, (dx, tspin) in enumerate(arms):
            tx, ty = cx + drift + dx, y0 + depth + 1
            orb = {"radius": [0, tdepth], "period": frames, "phase": tph}
            e.append({"name": f"tendril-{i}", "at": [tx, ty], "radius": 2.5, "rate": 0.5, "start": ts, "end": ts + 14,
                      "velocity": [0, tpush], "vortex": tspin, "orbit": orb})
            if tink:
                e.append({"name": f"tendril-{i}-ink", "at": [tx, ty], "radius": 1.4, "rate": 1, "start": ts,
                          "end": ts + 6, "density": tink, "orbit": orb})
    # A smaller ring that follows the first down the stem, as ink that left the surface late rolls up on its own.
    # trail = (delay, depth, g0, g1, (spin_l, spin_r), ink).
    if trail:
        td, tdepth, tg0, tg1, tspin, tink = trail
        ts = t0 + td
        tph = -360 * ts / frames
        torb = {"radius": [0, tdepth], "period": frames, "phase": tph}
        e.append({"name": "trail-head", "at": [cx + drift, y0], "radius": 2.5, "rate": head_rate, "start": ts,
                  "end": ts + 12, "velocity": [0, push * 0.8], "orbit": torb})
        if tink:
            e.append({"name": "trail-ink", "at": [cx + drift, y0], "radius": 2, "rate": 1, "start": ts,
                      "end": ts + 6, "density": tink, "orbit": torb})
        for side, sgn, s in (("l", -1, tspin[0]), ("r", 1, tspin[1])):
            orb = {"radius": [abs(tg1 - tg0), tdepth], "period": frames if sgn < 0 else -frames,
                   "phase": tph if sgn < 0 else 180 + 360 * ts / frames}
            e.append({"name": f"trail-{side}", "at": [cx + drift + sgn * tg1, y0], "radius": 3, "rate": lrate,
                      "start": ts + 1, "end": ts + 16, "vortex": -sgn * s, "orbit": orb})
    if clear:
        a, b, amount = clear
        e.append({"name": "clear", "at": [W / 2, H / 2], "area": [W, H], "rate": 1, "start": a, "end": b,
                  "density": -amount})
    look = look or [{"field": "density", "colors": ["r", "Z", "W", "9"], "thresholds": [0.04, 0.12, 0.3, 0.6],
                     "dither": 0.3}]
    return {"frames": frames, "duration": 70, "loop": True, "seed": seed, "warmup": 1, "walls": list(walls),
            "buoyancy": 0, "dissipation": 0.005, "drag": 0.0, "weight": weight, "vorticity": vort,
            "iterations": iterations, "emitters": e, "look": look}


def plume_source(name, W, H, effect, palette=PALETTE, symbols=None):
    src = {"format": "pixelforge-fluid", "version": 1, "name": name, "width": W, "height": H, "palette": palette,
           "effects": {name: effect}}
    if symbols:
        src["symbols"] = symbols
    return src
