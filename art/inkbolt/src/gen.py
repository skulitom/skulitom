"""Generate the Inkbolt card recipe: a static 'bg' frame plus the 72-frame loop 'ink-00'..'ink-71' (192x100).

Python lays out drawing operations (shapes, lines, hand-chosen pixels, dither and shade regions) and places the
compiled fluid frames. It never computes an effect pixel: every dither, shade, outline and fluid pixel is produced by
Pixelbolt when the recipe renders.
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import fluids as F  # noqa: E402
from pb import rect, ell, line, px, grid, dither, shade, at, fluid_frames, bezier, poly_pixels, write_json  # noqa: E402

ROOT = HERE.parent
BUILD, RECIPES = ROOT / "out" / "build", ROOT / "out" / "recipes"
W, H = 192, 100
FRAMES, MS = F.FRAMES, F.MS
T0 = F.T0
STILL = 51                      # beat frame of the reduced-motion still
# The sheet starts at beat frame 20 (the drop lets go), so a README visitor sees the hit within 0.35 s instead of
# 1.75 s of calm tank. Frame numbers in this file are the beat's own clock; sheet frame n is beat (n + PHASE) % 72.
PHASE = 20

PALETTE = {"$ref": "../../../palette.json"}
RAMPS = [
    ["0", "1", "2", "3", "4", "5", "6", "7"],
    ["s", "t", "u", "v", "w", "x"],
    ["A", "B", "C", "D", "E", "F", "G"],
    ["H", "I", "J", "K", "L", "M"],
    ["N", "O", "P", "Q", "R"],
    ["a", "b", "c", "d", "e", "f", "g"],
    ["h", "i", "j", "k", "l", "m", "n"],
    ["o", "p", "q", "r", "y", "z"],
    ["S", "T", "U", "V", "X", "Y"],
    ["8", "9", "W", "Z", "@", "#", "$"],
    ["%", "&", "+", "="],
]

# ---------------------------------------------------------------- layout
TX0, TX1, TY0, TY1 = 30, 141, 28, 85            # tank, outer
WX0, WX1, SURF, FLOOR = F.WATER_X0, F.WATER_X1, F.SURFACE, F.FLOOR
PX0, PX1, PY0, PY1 = 20, 181, 14, 85            # graph-paper sheet
GX, GY, STEP = 22, 16, 8                        # grid line origin and pitch
BENCH = 86
TIP = (F.DROP_X, 23)                            # nib tip pixel; the drop hangs below it


def wall():
    ops = [rect(0, 0, W, H, "2")]
    ops.append(shade(0, 0, W, 16, -1, density=[0.6, 0.0], direction="down", over=["2"]))
    return ops


def paper():
    """A sheet of dark graph paper pinned behind the tank. Lines are quiet: one step above the sheet."""
    ops = [rect(PX0, PY0, PX1 - PX0 + 1, PY1 - PY0 + 1, "3")]
    for x in range(GX, PX1 + 1, STEP):
        ops.append(line(x, PY0, x, PY1, "4"))
    for y in range(GY, PY1 + 1, STEP):
        ops.append(line(PX0, y, PX1, y, "4"))
    ops += [line(PX0, PY0, PX1, PY0, "4"), line(PX1 + 1, PY0 + 1, PX1 + 1, PY1, "1")]
    ops += [px(PX0 + 3, PY0 + 1, "P"), px(PX0 + 4, PY0 + 2, "N"), px(PX1 - 3, PY0 + 1, "P"), px(PX1 - 2, PY0 + 2, "N")]
    return ops


LIGHT_BAND, DEEP_BAND = SURF + 9, FLOOR - 1      # water bands: C above row 45, B to row 81, A on the floor rows


def tank_back():
    """What shows through the glass: the paper above the water (one step cooler), the water and its lines."""
    ops = []
    # Air inside the tank: the paper seen through two panes, shifted to the steel ramp.
    ops.append(rect(WX0, TY0 + 1, WX1 - WX0 + 1, SURF - TY0 - 1, "A"))
    for x in range(GX, WX1 + 1, STEP):
        if WX0 <= x <= WX1:
            ops.append(line(x, TY0 + 1, x, SURF - 1, "B"))
    for y in range(GY, SURF):
        if (y - GY) % STEP == 0 and y > TY0:
            ops.append(line(WX0, y, WX1, y, "B"))
    # Water: calm, in three flat bands that darken with depth (the light comes in at the surface).
    ops += [rect(WX0, SURF, WX1 - WX0 + 1, LIGHT_BAND - SURF, "C"),
            rect(WX0, LIGHT_BAND, WX1 - WX0 + 1, DEEP_BAND - LIGHT_BAND, "B"),
            rect(WX0, DEEP_BAND, WX1 - WX0 + 1, FLOOR - DEEP_BAND + 1, "A")]
    # Refraction: the grid seen through the water sits one pixel lower and to the right, one step down each band.
    for x in range(GX + 1, WX1 + 1, STEP):
        if WX0 <= x <= WX1:
            ops.append(shade(x, SURF + 2, 1, FLOOR - SURF - 2, -1))
    for y in range(GY + 1, FLOOR + 1, STEP):
        if y > SURF + 1:
            ops.append(shade(WX0, y, WX1 - WX0 + 1, 1, -1))
    return ops


def tank_glass():
    """Glass edges, rim, floor pane and the water's surface line, drawn over the water and the ink."""
    ops = []
    ops += [line(TX0, TY0, TX0, TY1, "D"), line(TX0, TY0, TX0, TY0 + 6, "E"), line(TX0 + 1, TY0 + 1, TX0 + 1, TY1 - 1, "A")]
    ops += [line(TX1, TY0, TX1, TY1, "B"), line(TX1 - 1, TY0 + 1, TX1 - 1, TY1 - 1, "C")]        # right wall
    ops += [line(TX0, TY0, TX1, TY0, "C"), line(TX0, TY0, TX0 + 30, TY0, "D"), line(TX0, TY0, TX0 + 2, TY0, "E")]  # rim
    ops += [line(TX0 + 1, TY1 - 1, TX1 - 1, TY1 - 1, "C"), line(TX0, TY1, TX1, TY1, "B")]        # floor pane
    ops += [line(WX0, SURF, WX1, SURF, "D"), line(WX0, SURF, WX0 + 22, SURF, "E")]              # surface line
    ops += [px(WX0, SURF - 1, "D"), px(WX1, SURF - 1, "C")]                                       # meniscus
    # A few clean front-glass highlights: two moonlit streaks on the left, a faint long one on the right.
    ops += [line(35, SURF + 3, 35, 58, "C"), line(35, SURF + 4, 35, 46, "D"), line(37, SURF + 6, 37, 42, "C"),
            line(136, SURF + 12, 136, 74, "C")]
    return ops


def bench():
    ops = [rect(0, BENCH, W, H - BENCH, "I"), line(0, BENCH, W - 1, BENCH, "K"),
           rect(0, BENCH + 1, W, 2, "J"), line(0, BENCH + 3, W - 1, BENCH + 3, "H")]
    for x0, x1, y in ((4, 40, 93), (60, 120, 92), (132, 186, 95), (20, 70, 97)):
        ops.append(line(x0, y, x1, y, "H"))
    # The tank's contact shadow and its moon shadow to the lower right.
    ops.append(shade(TX0, BENCH, TX1 - TX0 + 1, 2, -1))
    ops.append(shade(TX1 + 1, BENCH, 9, 3, -1))
    ops.append(shade(TX1 + 10, BENCH + 1, 2, 2, -1))
    ops.append(shade(TX1 + 12, BENCH + 2, 2, 1, -1))
    ops.append(shade(TX1 + 1, PY0 + 2, 3, BENCH - PY0 - 2, -1, over=["3", "4"]))
    return ops


def pen(tip=TIP):
    """A dip pen held at about 48 degrees: the nib points down-left over the tank, the shaft leaves the top edge right
    of x 76 (clear of the label). The silhouettes are authored outlines along the pen's axis; each pixel then takes
    its colour from which side of the axis it lies on (the upper-left side faces the moon)."""
    ux, uy = 8 / 145 ** 0.5, -9 / 145 ** 0.5
    nx, ny = -uy, ux                                   # perpendicular, pointing down-right (the shadow side)
    tx, ty = tip[0] + 0.5, tip[1] + 0.5

    def P(a, d):                                       # a along the axis from the tip, d across it
        return (tx + a * ux + d * nx, ty + a * uy + d * ny)

    def coords(x, y):
        dx, dy = x + 0.5 - tx, y + 0.5 - ty
        return dx * ux + dy * uy, dx * nx + dy * ny
    blade = poly_pixels([P(-0.4, 0), P(6, 1.5), P(10.6, 2.3), P(10.6, -2.3), P(6, -1.5)])
    ferrule = poly_pixels([P(10.4, 2.6), P(13.6, 2.6), P(13.6, -2.6), P(10.4, -2.6)])
    holder = poly_pixels([P(13.4, 1.9), P(40, 1.9), P(40, -1.9), P(13.4, -1.9)])
    taken = set()
    ops = []

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H and (x, y) not in taken:
            taken.add((x, y))
            ops.append(px(x, y, c))
    for x, y in holder:
        a, d = coords(x, y)
        if a < 13.6:
            continue
        put(x, y, "y" if d < -1.0 and a < 19 else "r" if d < -0.9 else "q" if d < 0.9 else "p")
    for x, y in ferrule:
        a, d = coords(x, y)
        put(x, y, "R" if d < -1.4 and 11.5 < a < 12.6 else "Q" if d < -1.0 else "N" if d > 1.2 or a > 13.0 else "O")
    edge = {(x, y) for x, y in blade if any((x + ox, y + oy) not in blade for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    blade_set = set(blade)
    for x, y in blade:
        a, d = coords(x, y)
        if a < 0.8:
            c = "N"                                    # the point
        elif abs(d) < 0.55 and 2.6 < a < 6.2:
            c = "N"                                    # the slit
        elif 6.6 < a < 7.8 and abs(d) < 0.8:
            c = "N"                                    # breather hole
        elif (x, y) in edge:
            c = "Q" if d < 0 else "N"
        else:
            c = "P" if d < 0 else "O"
        put(x, y, c)
    # The slit's lit lip: one pixel of the lightest brass just up-left of the slit, two thirds of the way up.
    for x, y in blade:
        a, d = coords(x, y)
        if 3.4 < a < 4.6 and -1.4 < d < -0.5:
            ops.append(px(x, y, "R"))
            break
    return ops


SQ = (147, 85, 25)          # set square: right-angle corner (x, y) and leg length


def set_square():
    """A clear violet acrylic set square standing on the bench, leaning on the paper: the grid shows through it
    tinted (night -> violet), through its cut-out it shows plain. Graduation ticks along its upright edge."""
    x0, y0, n = SQ
    ops = []
    inner = (x0 + 5, y0 - 5, n - 14)     # cut-out: right-angle corner and leg
    for k in range(n):                    # row y0 - k spans x0 .. x0 + (n - 1 - k)
        y, x1 = y0 - k, x0 + (n - 1 - k)
        spans = [(x0, x1)]
        ix, iy, m = inner
        kk = iy - y
        if 0 <= kk < m:
            spans = [(x0, ix - 1), (ix + (m - kk), x1)]
        for a, b in spans:
            if b >= a:
                ops.append(dither(a, y, b - a + 1, 1, "o", 1.0, over=["3"]))
                ops.append(dither(a, y, b - a + 1, 1, "p", 1.0, over=["4"]))
    # edges: upright edge lit by the moon, hypotenuse half-lit, base in shadow; the cut-out's rim
    ops += [line(x0, y0, x0, y0 - n + 1, "r"), line(x0, y0 - n + 1, x0 + n - 1, y0, "q"), line(x0, y0, x0 + n - 1, y0, "p")]
    ix, iy, m = inner
    ops += [line(ix, iy, ix, iy - m + 1, "p"), line(ix, iy - m + 1, ix + m - 1, iy, "r"), line(ix, iy, ix + m - 1, iy, "q")]
    for k in range(2, n - 2, 3):
        ops.append(px(x0 + 1, y0 - k, "q" if k % 15 else "y"))
    ops.append(px(x0, y0 - n + 1, "y"))                                  # glint on the tip
    ops.append(shade(x0 + n, y0 - 2, 2, 3, -1))                          # where it meets the paper
    return ops


# Caustic dashes on the tank floor: (x, length, phase). Moonlight focused by the surface; they sway a pixel or two,
# harder for 16 frames after the hit, when the ripple reaches them.
CAUSTICS = [(41, 3, 0), (52, 2, 3), (63, 4, 5), (77, 2, 1), (88, 3, 6), (101, 2, 2), (112, 3, 4), (125, 2, 7)]
SWAY = [0, 1, 1, 1, 0, -1, -1, -1]


def caustics(i, hits=(T0,), frames=FRAMES):
    k = min((i - t) % frames for t in hits)
    big = k < 16
    ops = []
    for x, n, ph in CAUSTICS:
        dx = SWAY[(i // (1 if big else 3) + ph) % 8] * (2 if big else 1)
        ops.append(dither(x + dx, FLOOR, n, 1, "B", 1.0, over=["A"]))
        ops.append(dither(x + dx - 1, TY1 - 1, n + 1, 1, "D", 1.0, over=["C"]))
    # the same light, through the water, lands on the bench inside the tank's moon shadow
    for x, n, ph in ((TX1 + 3, 2, 2), (TX1 + 7, 2, 5)):
        dx = SWAY[(i // (1 if big else 3) + ph) % 8]
        ops.append(dither(x + dx, BENCH + 1, n, 1, "J", 1.0, over=["I"]))
    return ops


def meniscus(i):
    """Before the simulated bead takes over (beat 7), ink collects at the nib's tip by hand: one pixel from beat 62,
    then two, then a 2x2 bead (lit side Z, shadow side 9), so the next drop is visibly on its way."""
    tx, ty = TIP[0], TIP[1] + 1
    k = (i - 62) % FRAMES
    if k >= 17:                       # beats 7..61: the simulation (or nothing)
        return []
    if k < 4:
        return [px(tx, ty, "9")]
    if k < 9:
        return [px(tx, ty, "W"), px(tx, ty + 1, "9")]
    return [px(tx - 1, ty, "Z"), px(tx, ty, "W"), px(tx - 1, ty + 1, "W"), px(tx, ty + 1, "9")]


def pen_lift(i):
    """Follow-through: relieved of the drop, the pen springs up a pixel for three frames, then settles."""
    return -1 if 21 <= i <= 23 else 0


def static_ops():
    return wall() + paper() + bench() + set_square() + tank_back()


def ripple(i, t0=T0, x0=None):
    """The surface after the hit: a one-pixel bump that runs out both ways and fades (secondary motion)."""
    x0 = F.DROP_X if x0 is None else x0
    k = i - t0
    if not 1 <= k <= 10:
        return []
    ops = []
    for sgn in (-1, 1):
        x = x0 + sgn * (1 + 2 * k)
        if WX0 + 1 < x < WX1 - 1:
            c = "E" if k <= 5 else "D"
            ops += [px(x, SURF - 1, c), px(x + sgn, SURF - 1, c)]
            ops += [px(x, SURF, "C"), px(x + sgn, SURF, "C")] if k <= 6 else []
    return ops


# ---------------------------------------------------------------- the vector curve
# The pen tool snaps onto the ink: four anchors land on the right lobe's edge one after another and the segments
# draw between them, from under the cap along the arm, up the lobe's outside, over its top and curling into it (the
# main swirl). While the lobe rises the curve rides it (anchors keyframed on the simulated frames 48, 52 and 56, read
# off Pixelbolt's palette grids); the ink thins away and leaves the clean curve, which dissolves last, by dither.
# Anchors are 3 px squares (the last placed is filled: selected), handles 3 px round knobs on dotted lines; all of it
# casts a 1 px shadow down-right onto the front glass.
KEYS = {  # frame: [(anchor, in-handle, out-handle), ...] for A0..A2
    46: [((66, 74), None, (77, 78)), ((92, 63), (92, 71), (92, 54)), ((84, 60), (82, 52), None)],
    50: [((68, 77), None, (79, 80)), ((95, 63), (95, 72), (95, 53)), ((87, 58), (85, 50), None)],
    54: [((68, 77), None, (80, 81)), ((98, 65), (98, 74), (99, 53)), ((90, 54), (87, 46), None)],
    58: [((68, 77), None, (80, 81)), ((100, 60), (100, 70), (101, 48)), ((93, 49), (90, 41), None)],
}
V_PLACE = [45, 47, 50]            # frames on which A0..A2 land; each segment draws over the frames before
V_HOLD, V_FADE0, V_FADE1 = 58, 68, 76   # the curve outlives the ink (gone by 61) and dissolves across the loop point


def unwrap(i):
    """Beats before the hit belong to the end of the previous cycle for the curve: 0..24 -> 72..96."""
    return i + FRAMES if i < T0 else i
CURVE, KNOB, DOT, HOLLOW, SHADOW = "z", "y", "r", "p", "9"


def lerp(a, b, t):
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))


def handle_line(a, h, reach=1.0):
    """Dotted line from anchor a toward knob h (every second pixel), drawn out to `reach` of its length."""
    n = max(abs(h[0] - a[0]), abs(h[1] - a[1]))
    return [lerp(a, h, k / n) for k in range(2, int(n * reach), 2)] if n else []


def knob(h):
    x, y = h
    return [(x, y - 1, KNOB), (x - 1, y, KNOB), (x, y, CURVE), (x + 1, y, KNOB), (x, y + 1, KNOB)]


def anchor(a, filled=False, pop=False):
    x, y = a
    pts = [(x + dx, y + dy, CURVE) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
    pts.append((x, y, CURVE if filled else HOLLOW))
    if pop:  # the frame an anchor lands: a 5 px ring flashes round it
        pts += [(x + dx, y + dy, KNOB) for dx in range(-2, 3) for dy in range(-2, 3) if max(abs(dx), abs(dy)) == 2]
    return pts


def keyed(i):
    """Anchor and handle positions on frame i: before 48 the first key, after 56 (the hold) the last, eased between."""
    ks = sorted(KEYS)
    f = min(max(i, ks[0]), min(ks[-1], V_HOLD))
    for k0, k1 in zip(ks, ks[1:]):
        if k0 <= f <= k1:
            t = (f - k0) / (k1 - k0)
            t = t * t * (3 - 2 * t)
            mix = lambda p, q: None if p is None else (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
            return [tuple(mix(p, q) for p, q in zip(A, B)) for A, B in zip(KEYS[k0], KEYS[k1])]
    return KEYS[ks[-1]]


def vector(i):
    i = unwrap(i)
    if not V_PLACE[0] <= i < V_FADE1:
        return []
    r = lambda p: (round(p[0]), round(p[1]))
    key = [tuple(None if p is None else r(p) for p in a) for a in keyed(i)]
    stroke = []
    for s in range(len(key) - 1):
        (a, _, ho), (b, hi, _) = key[s], key[s + 1]
        seg = bezier(a, ho, hi, b)
        t0, t1 = V_PLACE[s], V_PLACE[s + 1]
        n = len(seg) if i >= t1 else round(len(seg) * (i - t0 + 1) / (t1 - t0 + 1)) if i >= t0 else 0
        stroke += seg[:n]
    placed = [(s, k) for s, k in enumerate(key) if i >= V_PLACE[s]]
    squares = {(k[0][0] + dx, k[0][1] + dy) for _, k in placed for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    solid = set(stroke) | squares

    def clear_of(x, y):          # a handle pixel may not touch the stroke or an anchor, even diagonally
        return all((x + dx, y + dy) not in solid for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    pts = [(x, y, CURVE) for x, y in stroke]
    for s, (a, hi, ho) in placed:
        reach = min(1.0, (i - V_PLACE[s] + 1) / 2)
        for h in (hi, ho):
            if not h:
                continue
            pts += [(x, y, DOT) for x, y in handle_line(a, h, reach) if clear_of(x, y)]
            if reach >= 1:
                pts += [(x, y, c) for x, y, c in knob(h) if (x, y) not in solid]
    for s, (a, _, _) in placed:
        pts += anchor(a, filled=(s == len(key) - 1 and i < V_FADE0), pop=(i == V_PLACE[s]))
    drawn = {(x, y) for x, y, _ in pts}
    ops = [px(x + 1, y + 1, SHADOW) for x, y, _ in pts if (x + 1, y + 1) not in drawn]
    ops += [px(x, y, c) for x, y, c in pts]
    if i >= V_FADE0:
        d = (i - V_FADE0 + 1) / (V_FADE1 - V_FADE0 + 1)
        ops.append({"op": "dither", "erase": True, "pattern": "noise", "seed": 17, "density": round(d, 3)})
    return ops


def anchor_glow(i):
    i = unwrap(i)
    """The vector overlay is the piece's own light: each placed anchor lights the water and the ink round it, one
    ramp step in two rings (solid inside, Bayer half outside), fading as the curve dissolves."""
    if not V_PLACE[0] <= i < V_FADE1:
        return []
    key = keyed(i)
    lit = ["A", "B", "C"]
    ops = []
    for s, (a, _, _) in enumerate(key):
        if i < V_PLACE[s]:
            continue
        x, y = round(a[0]), round(a[1])
        outer = 0.5 if i < V_FADE0 else 0.5 * (V_FADE1 - i) / (V_FADE1 - V_FADE0)
        inner = 1.0 if i < V_FADE0 else (V_FADE1 - i) / (V_FADE1 - V_FADE0)
        if inner >= 0.5:
            ops.append(shade(x - 3, y - 3, 7, 7, 1, shape="ellipse", over=lit))
    return ops


def recipe():
    plume = fluid_frames(BUILD / "plume.json", "plume")
    drop = fluid_frames(BUILD / "drop.json", "drop")
    px0, py0 = F.PLUME_ORIGIN
    dx0, dy0 = F.DROP_ORIGIN
    frames = [{"name": "bg", "duration": MS, "ops": static_ops()}]
    for n in range(FRAMES):
        i = (n + PHASE) % FRAMES
        # The drop passes behind the front pane below the rim: drawn before the glass, then one step cooler there.
        ops = (caustics(i) + at(plume[i], px0, py0) + at(drop[i], dx0, dy0)
               + [shade(WX0, TY0 + 1, WX1 - WX0 + 1, SURF - TY0 - 1, -1, over=["W", "Z", "9", "D", "E"])]
               + anchor_glow(i) + tank_glass() + ripple(i) + meniscus(i)
               + pen((TIP[0], TIP[1] + pen_lift(i))))
        frame = {"name": f"ink-{n:02d}", "duration": MS, "from": "bg", "ops": ops}
        v = [] if os.environ.get("INK_NOVECTOR") else vector(i)
        if v:
            frame["layers"] = [{"name": "vector", "ops": v}]
        frames.append(frame)
    return {"version": 1, "name": "inkbolt", "width": W, "height": H, "palette": PALETTE, "ramps": RAMPS,
            "frames": frames, "animations": {"ink": {"frames": [f"ink-{i:02d}" for i in range(FRAMES)]}}}


def main():
    RECIPES.mkdir(exist_ok=True)
    write_json(RECIPES / "inkbolt.json", recipe())
    still = (STILL - PHASE) % FRAMES
    (BUILD / "still.txt").write_text(f"ink-{still:02d}\n", encoding="utf-8", newline="\n")
    print("recipe written; still frame", still, "= beat frame", STILL)


if __name__ == "__main__":
    main()
