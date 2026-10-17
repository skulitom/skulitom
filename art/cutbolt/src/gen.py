"""Generate the Cutbolt card recipe: a static base frame plus a 72-frame loop (and the hover burst, speed 2).

Python lays out drawing operations (shapes, lines, hand-placed pixels, the flipbook pictures, dither and shade
regions) and places the compiled fluid frames as a layer. It never computes an effect pixel: every dither, shade band,
glow ring, the film's translucency and every fluid pixel are produced by Pixelbolt when the recipe renders.

The film is drawn the way a pixel artist would lay a strip along a path: scene.locate() says which pixels the film
covers and where along the film each falls (geometry), and the film's own marks (edges, perforations, frame lines,
the hand-drawn pictures) are written at those places as palette rows. Its dark, translucent base is a Pixelbolt
`shade` of whatever lies behind it.
"""

import json
import math
import sys
from pathlib import Path

import scene as S
from lib import RAMPS, palette_for, rect, ell, line, px, grid, text, dither, shade

HERE = Path(__file__).parent
ROOT = HERE.parent
BUILD = ROOT / "out" / "build"
RECIPES = ROOT / "out" / "recipes"
W, H = S.W, S.H
STILL = 0   # the seam drop's crater and crown spray, the gate holding the squash, the timer at 00:00

# ---------------------------------------------------------------- the flipbook pictures (11 x 8)
# A bouncing ball, the animator's first exercise: a round 4 px ball, light pink on the dark film (lit top left, a
# step darker bottom right), a faint ground line, six pictures a bounce (squash, rising, high, top, high, falling).
# Picture 3 carries a caption line under the ball.
BALL = [".XX.", "XYXX", "XXXV", ".XV."]
SQUASH = [".XXXX.", "XYXXXV"]
POSES = {0: (2, 5, SQUASH), 1: (3, 3, BALL), 2: (3, 1, BALL), 3: (3, 0, BALL), 4: (3, 1, BALL), 5: (3, 3, BALL)}
CAPTION = "UU.UUU.UU"     # picture 3's caption line, row 5 from column 1
GROUND = "3"


def picture_rows(k):
    rows = [["."] * S.IMG_W for _ in range(S.IMG_H)]
    rows[S.IMG_H - 1] = [GROUND] * S.IMG_W
    x, y, shape = POSES[k]
    for r, line_ in enumerate(shape):
        for c, ch in enumerate(line_):
            rows[y + r][x + c] = ch
    if k == 3:
        for c, ch in enumerate(CAPTION):
            if ch != ".":
                rows[5][1 + c] = ch
    return ["".join(r) for r in rows]


PICS = [picture_rows(k) for k in range(S.N_IMG)]
# Film colours: edges and frame lines in smoke; perforations a dim night tone, turning pink only inside the safelight's
# pool, so the pictures are the brightest marks on the film. On the diagonal the film is still wet from the bath:
# everything a step down.
EDGE, FRAMELINE, HOLE = "t", "t", "4"
WET = {"t": "s", "4": "3", "X": "U", "Y": "V", "V": "T", "U": "T", "w": "v", "u": "t"}


def is_splice(j):
    return (j - S.SPLICE_J) % 12 == 0


def material(seg, p, k, s):
    """The film's own mark at strip position p (before the film has moved s) and row k, or '.' for bare base. Used
    pixel by pixel on the straight top run and the trim; the drum and the diagonal get whole marks (bend_marks)."""
    u = math.floor(p - s)
    o = u % S.PITCH
    j = (u - o) // S.PITCH
    ch = "."
    if k in (0, S.STRIP - 1):
        ch = EDGE
    elif k in S.HOLE_ROWS and o in S.HOLE_OFFS:
        ch = HOLE
    elif 3 <= k <= 12 and o == 0:
        ch = "v" if is_splice(j) else FRAMELINE                     # one frame line in twelve is a taped cut
    elif S.IMG_ROW <= k < S.IMG_ROW + S.IMG_H and o >= 1:
        ch = PICS[S.picture(j)][k - S.IMG_ROW][o - 1]
    if k in (3, 12) and ((is_splice(j) and o == 1) or (is_splice(j + 1) and o == 11)):
        ch = "u"                                                    # the splice tape's corners
    if seg in ("diag", "trim"):
        ch = WET.get(ch, ch)
    return ch


# Which pixels the film covers: the top run as one block, the drum and diagonal as row spans.
SPANS = {}
for _y in range(S.HY0, S.TRAY_BOTTOM):
    xs = [x for x in range(0, S.RX) if S.locate(x, _y)] + [x for x in range(S.RX, 150)
                                                            if _y >= S.HY0 + S.STRIP and S.locate(x, _y)]
    if xs:
        SPANS[_y] = (min(xs), max(xs))


def bend_marks(s):
    """The film's marks on the drum and the diagonal, placed whole along the film's own direction (scene.to_xy):
    perforations as 2x2 holes at even spacing (on the drum its brass teeth fill the inner track), frame lines straight
    across the film, ground lines along it, and each picture's ball stamped at its place (upside down once the film
    has turned past the drum's side)."""
    marks = {}

    def put(seg, x, y, ch):
        loc = S.locate(x, y)
        if loc and loc[0] == seg and 0 < loc[2] < S.STRIP - 1:
            marks[(x, y)] = ch

    for seg, lo, hi in (("drum", -S.ARC_LEN, 0.0), ("diag", -S.ARC_LEN - 150, -S.ARC_LEN)):
        col = (lambda c: WET.get(c, c)) if seg == "diag" else (lambda c: c)
        for j in range(math.floor((lo - s) / S.PITCH) - 1, math.floor((hi - s) / S.PITCH) + 2):
            base = S.PITCH * j + s                      # this frame's frame line, along the film
            pic = S.picture(j)
            pf = base + 0.5
            if lo <= pf <= hi:
                ch = col("v" if is_splice(j) else FRAMELINE)
                for x, y in line_pixels(S.to_xy(seg, pf, 3.0), S.to_xy(seg, pf, 13.0)):
                    put(seg, x, y, ch)
            for i in range(23):
                pg = base + 1.0 + i * 0.5
                if lo <= pg <= hi:
                    x, y = S.to_xy(seg, pg, 11.5)
                    put(seg, math.floor(x), math.floor(y), col(GROUND))
            if pic == 3:
                for c, ch in enumerate(CAPTION):
                    pc = base + 2.5 + c
                    if ch != "." and lo <= pc <= hi:
                        x, y = S.to_xy(seg, pc, 9.5)
                        put(seg, math.floor(x), math.floor(y), col(ch))
            bx, by, shape = POSES[pic]
            h, w = len(shape), len(shape[0])
            cu, ck = base + 1 + bx + w / 2, S.IMG_ROW + by + h / 2
            if lo <= cu <= hi:
                x, y = S.to_xy(seg, cu, ck)
                flip = seg == "diag" or -cu / S.R_MID > math.pi / 2
                rows = [r[::-1] for r in shape[::-1]] if flip else shape
                for r, line_ in enumerate(rows):
                    for c, ch in enumerate(line_):
                        put(seg, round(x - w / 2) + c, round(y - h / 2) + r, col(ch))
            for o in (1, 5, 9):
                pc = base + o + 1
                if not lo <= pc <= hi:
                    continue
                for kc, ch in ((2.0, HOLE), (14.0, "O" if seg == "drum" else HOLE)):
                    x, y = S.to_xy(seg, pc, kc)
                    x0, y0 = round(x - 1), round(y - 1)
                    for dx in (0, 1):
                        for dy in (0, 1):
                            put(seg, x0 + dx, y0 + dy, col(ch))
    # One glint on the drum's teeth, wherever a tooth sits nearest the key light (upper left); it stays put as they turn.
    teeth = [xy for xy, ch in marks.items() if ch == "O"]
    if teeth:
        gx, gy = min(teeth, key=lambda xy: (xy[0] - (S.RX - 6)) ** 2 + (xy[1] - (S.RY - 6)) ** 2)
        marks[(gx, gy)] = "Q"
    return marks


def line_pixels(a, b):
    """A clean 1 px line between two points: one pixel per step along its longer axis (no doubled corners)."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0))
    steps = max(1, int(round(n)))
    out = []
    for i in range(steps + 1):
        t = i / steps
        p = (math.floor(x0 + (x1 - x0) * t), math.floor(y0 + (y1 - y0) * t))
        if p not in out:
            out.append(p)
    return out


def film_ops(s):
    ops = []
    rows = []
    for y in range(S.HY0, S.HY0 + S.STRIP):
        rows.append("".join(material("top", float(x - S.RX), y - S.HY0, s) for x in range(S.RX, W)))
    ops.append(grid(S.RX, S.HY0, rows))
    marks = bend_marks(s)
    for y, (x0, x1) in SPANS.items():
        row = []
        for x in range(x0, x1 + 1):
            loc = S.locate(x, y)
            ch = "."
            if loc and loc[0] != "top":
                if loc[2] in (0, S.STRIP - 1):
                    ch = WET.get(EDGE, EDGE) if loc[0] == "diag" else EDGE
                else:
                    ch = marks.get((x, y), ".")
            row.append(ch)
        ops.append(grid(x0, y, ["".join(row)]))
    return ops


def film_base():
    """The film's dark translucent base: whatever lies behind it, one ramp step darker (static: the path is fixed)."""
    ops = [shade(S.RX, S.HY0, W - S.RX, S.STRIP, -1)]
    for x in range(0, 150):
        run = None
        for y in range(S.HY0, S.TRAY_BOTTOM + 1):
            on = (y < S.TRAY_BOTTOM and S.locate(x, y) is not None and not (x >= S.RX and y < S.HY0 + S.STRIP))
            if on and run is None:
                run = y
            elif not on and run is not None:
                ops.append(shade(x, run, 1, y - run, -1))
                run = None
    return ops


# ---------------------------------------------------------------- static base
LX, LY = S.LAMP
BULB = (LX, LY + 2)


def wall():
    ops = [rect(0, 0, W, S.BENCH_Y, "2")]
    for x in range(10, W, 26):
        y = 0
        while y <= S.TRAY_RIM:                       # the boards stop where the film crosses them
            if S.locate(x, y):
                y += 1
                continue
            y1 = y
            while y1 + 1 <= S.TRAY_RIM and not S.locate(x, y1 + 1):
                y1 += 1
            ops.append(line(x, y, x, y1, "1"))
            y = y1 + 1
    ops.append(line(0, S.TRAY_RIM + 1, W - 1, S.TRAY_RIM + 1, "1"))
    for row, y in enumerate(range(S.TRAY_RIM + 2, S.BENCH_Y, 5)):
        ops.append(line(0, y + 4, W - 1, y + 4, "1"))
        for x in range(4 if row % 2 else 0, W, 8):
            ops.append(line(x, y, x, min(y + 3, S.BENCH_Y - 1), "1"))
    ops.append(shade(0, 0, W, 12, -1, density=[0.7, 0.0], direction="down", over=["2"]))
    return ops


def lamp_glow():
    """The safelight's pool on the wall: banded ramp rings (bayer feathers) moving the wall along night -> pink."""
    bx, by = BULB
    ops = []
    for r, d in ((26, 0.5), (19, 1.0), (12, 0.5), (7, 1.0)):
        ops.append(shade(bx - r, by - r, 2 * r + 1, 2 * r + 1, 1, shape="ellipse", density=d,
                         over=["1", "2", "3", "4", "S"]))
    return ops


def lamp():
    """A pendant safelight: a steel cone shade on a cable (which runs up behind the top run), pink glass below it."""
    cx, gy = LX, LY
    ops = [line(cx, 0, cx, gy - 9, "A"), rect(cx - 1, gy - 8, 3, 2, "B"), px(cx, gy - 8, "C")]
    for i, half in enumerate((2, 3, 4, 5, 6, 7)):
        y = gy - 6 + i
        ops.append(line(cx - half, y, cx + half, y, "A"))
        ops.append(px(cx - half, y, "C" if i < 4 else "B"))
        ops.append(px(cx + half, y, "4"))
    ops += [line(cx - 7, gy, cx + 7, gy, "B"), px(cx - 7, gy, "C"), px(cx - 3, gy - 6, "D"),
            line(cx - 5, gy + 1, cx + 5, gy + 1, "U"), line(cx - 4, gy + 2, cx + 4, gy + 2, "V"),
            line(cx - 2, gy + 3, cx + 2, gy + 3, "U"), line(cx - 2, gy + 1, cx + 2, gy + 1, "V"),
            line(cx - 1, gy + 2, cx + 1, gy + 2, "X")]
    return ops


def bench():
    y = S.BENCH_Y
    ops = [rect(0, y, W, H - y, "I"), line(0, y, W - 1, y, "K"), line(0, y + 1, W - 1, y + 1, "J"),
           line(0, y + 2, W - 1, y + 2, "H")]
    for (x0, x1, yy) in ((4, 40, y + 4), (52, 96, y + 3), (60, 120, y + 5), (130, 186, y + 4), (150, 176, y + 6)):
        ops.append(line(x0, yy, x1, yy, "H"))
    ops.append(shade(LX - 40, y - 2, 81, 6, 1, shape="ellipse", density=0.5, over=["K", "J"]))
    ops.append(shade(LX - 22, y - 1, 45, 4, 1, shape="ellipse", over=["K", "J"]))
    return ops


def tray_back():
    x0, x1 = S.TRAY_X0 + 1, S.TRAY_X1 - 1
    return [shade(x0, S.TRAY_RIM + 1, x1 - x0 + 1, S.TRAY_BOTTOM - S.TRAY_RIM - 1, -1, over=["2", "3", "4", "S"])]


def gate_back():
    """The viewer's lamp behind the gate: the film in front of it (its translucent base darkens it one step) reads as
    dark wine, so the picture's light parts are what glow; two clean bands of spill above and below the film."""
    gx = S.GATE_X
    return [rect(gx - 2, S.HY0 - 3, S.PITCH + 4, 2, "a"), rect(gx - 2, S.HY0 + S.STRIP + 1, S.PITCH + 4, 2, "a"),
            rect(gx, S.HY0, S.PITCH, S.STRIP, "c")]


def timer_body():
    x, y = 150, S.BENCH_Y - 14
    return [rect(x, y, 32, 14, "A"), line(x + 1, y, x + 30, y, "C"), line(x, y + 1, x, y + 12, "B"),
            px(x, y, "B"), px(x + 31, y, "B"), line(x + 31, y + 1, x + 31, y + 13, "4"),
            rect(x + 3, y + 3, 26, 9, "a"), line(x + 3, y + 2, x + 28, y + 2, "1"),
            px(x + 2, y + 13, "4"), px(x + 29, y + 13, "4")]


def trim():
    """A cut trim of the same film hanging on a pin in the bin: its base a step darker than the wall, its marks dim,
    its pictures sideways, cut square at a frame line."""
    x0, y0, n = S.TRIM_X, S.TRIM_Y, S.TRIM_LEN
    rows = ["".join(material("trim", float(y - y0) + 36, x - x0, 0) for x in range(x0, x0 + S.STRIP))
            for y in range(y0, y0 + n)]
    cx = x0 + S.STRIP // 2
    return [shade(x0, y0, S.STRIP, n, -1), grid(x0, y0, rows),
            px(cx, y0 - 4, "C"), line(cx, y0 - 3, cx, y0 - 2, "B"), rect(cx - 2, y0 - 1, 4, 2, "O"),
            line(cx - 2, y0 - 1, cx + 1, y0 - 1, "P")]


def drum():
    """The sprocket drum the film wraps: brass, its teeth through the inner perforations, one bolt on its face."""
    cx, cy, r = S.RX, S.RY, S.R_IN
    return [ell(cx - r, cy - r, 2 * r, 2 * r, "N"),
            ell(cx - r + 1, cy - r + 1, 2 * r - 2, 2 * r - 2, "O", filled=False),
            ell(cx - 2, cy - 2, 4, 4, "O"), px(cx - 1, cy - 1, "P"),
            # The safelight (lower right) catches the drum's rim.
            px(cx + 2, cy + 4, "Q"), px(cx + 3, cy + 3, "Q"), px(cx + 4, cy + 2, "P"), px(cx + 1, cy + 5, "P")]


def base_ops():
    return (wall() + lamp_glow() + tray_back() + bench() + gate_back() + lamp() + timer_body() + drum()
            + film_base() + trim())


# ---------------------------------------------------------------- per-frame film light
def film_light():
    """Light on the film's marks: inside the safelight's pool the night perforations and the pictures warm a step
    pink band by band (solid bands); its lamp side catches a pink rim."""
    bx, by = BULB
    pinks = ["3", "4", "S", "T", "U", "V", "X"]
    return [shade(bx - r, by - r, 2 * r + 1, 2 * r + 1, 1, shape="ellipse", over=pinks) for r in (44, 30, 16)] + [
        dither(LX - 18, S.HY0 + S.STRIP - 1, 37, 1, "T", 1.0, over=["t"])]


def gate_light():
    """Whatever passes through the gate is lit from behind: perforations glow gold, the picture's ball and ground
    line glow molten on the dark wine base, frame lines and edges make a lit molten rim (also mid-pull, part-lit)."""
    gx, y0 = S.GATE_X, S.HY0
    ops = []
    for yy in (1, 13):
        ops.append(dither(gx, y0 + yy, S.PITCH + 1, 2, "g", 1.0, over=["3", "4", "T", "U", "V", "X", "Y", "S"]))
    for src, dst in (("X", "g"), ("Y", "g"), ("V", "f"), ("3", "d"), ("U", "f"), ("t", "e"), ("v", "g"), ("u", "f")):
        ops.append(dither(gx, y0, S.PITCH + 1, S.STRIP, dst, 1.0, over=[src]))
    return ops


# ---------------------------------------------------------------- liquid and glass
def fluid_frames():
    recipe = json.loads((BUILD / "tray.json").read_text(encoding="utf-8"))
    return [f["ops"] for f in recipe["frames"] if f["name"].rsplit("-", 1)[0] == "tray"]


def at(ops, dx, dy):
    return [dict(o, x=o["x"] + dx, y=o["y"] + dy) for o in ops]


SUBMERGED = []
for _x in range(60, S.TRAY_X1, 2):
    _top = S.diag_top(_x)
    _y0, _y1 = max(_top, S.TRAY_RIM + 1), min(_top + S.STRIP - 1, S.TRAY_BOTTOM - 1)
    if _y0 <= _y1:
        SUBMERGED.append((_x, _y0, _y1))


def liquid_post(f, drips):
    """Inside the liquid layer: the safelight's reflection on the surface under it, drops and spray above the rim a
    step brighter (out of the glass), and the film going into the bath seen through it as a darker band."""
    pinks = ["S", "T", "U", "V", "X", "Y"]
    bx = BULB[0]
    sy = S.SURFACE
    ops = [shade(bx - 4, sy - 2, 9, 5, 1, shape="ellipse", over=["V"]),
           shade(S.FLUID_X, S.FLUID_Y, S.FLUID_W, S.TRAY_RIM + 1 - S.FLUID_Y, 1, over=pinks),
           # Hanging and falling drops catch the safelight: their bodies a further step up, so they read whole (round)
           # against the pink glow on the wall instead of fading out at the bottom.
           shade(S.FLUID_X, S.FLUID_Y, S.FLUID_W, S.TRAY_RIM - S.FLUID_Y, 1, over=["T", "U"])]
    for x, y0, y1 in SUBMERGED:
        ops.append(shade(x, y0, 2, y1 - y0 + 1, -1, over=["T", "U", "V", "X"]))
    # Above the glass, a falling drop keeps a round bottom: a lone pixel hanging under a drop (empty on both sides and
    # below, the drop's own colour above) is the sim's stretched tail, so Pixelbolt rewrites it away.
    # A lone pixel hanging under any of the drop's colours goes (a tail); so does a lone pixel standing on top of one
    # (a nub), except over a bead still hanging from the film, whose top pixel is its neck. At most 16 rules a pass.
    drop = ("T", "U", "V", "X", "Y")
    tails = [{"match": [f".{a}.", f"_{c}_", "___"], "replace": ["...", "._.", "..."]} for a in drop for c in drop]
    nubs = [{"match": ["___", f"_{c}_", f".{a}."], "replace": ["...", "._.", "..."]} for a in drop for c in drop]
    y0, h = S.FLUID_Y, S.TRAY_RIM - 1 - S.FLUID_Y
    lo, hi = min(d[0] for d in drips) - 7, max(d[0] for d in drips) + 8     # only where drops fall
    for rules in (tails[:16], tails[16:]):
        ops.append({"op": "rewrite", "x": lo, "y": y0, "w": hi - lo, "h": h, "empty": "_", "rules": rules,
                    "steps": 2})
    hanging = sorted(x for x, start, release in drips if start <= f < release)
    spans, x = [], lo
    for hx in hanging:
        if hx - 4 > x:
            spans.append((x, hx - 4))
        x = hx + 5
    if hi > x:
        spans.append((x, hi))
    for a, b in spans:
        for rules in (nubs[:16], nubs[16:]):
            ops.append({"op": "rewrite", "x": a, "y": y0, "w": b - a, "h": h, "empty": "_", "rules": rules,
                        "steps": 2})
    return ops


def glass_front():
    x0, x1, top, bot = S.TRAY_X0, S.TRAY_X1, S.TRAY_RIM, S.TRAY_BOTTOM
    return [line(x0, top, x0, bot, "C"), line(x1, top, x1, bot, "B"), line(x0 + 1, bot, x1 - 1, bot, "C"),
            line(x0 + 1, bot + 1, x1 - 1, bot + 1, "B"), px(x0, bot, "B"), px(x1, bot, "A"),
            line(x0 - 1, top, x0 + 1, top, "D"), line(x1 - 1, top, x1 + 1, top, "C"),
            line(x0 + 1, top, x1 - 1, top, "B"),
            dither(LX - 30, top, 61, 1, "U", [1.0, 0.0], direction="radial", over=["B"]),
            line(x0 + 4, top + 3, x0 + 4, top + 5, "E"), line(x0 + 4, top + 8, x0 + 4, top + 11, "D"),
            line(x1 - 4, top + 3, x1 - 4, top + 5, "C")]


def playhead_and_gate():
    gx, y0, y1 = S.GATE_X, S.HY0, S.HY0 + S.STRIP - 1
    c = gx + 5
    return [grid(c - 2, 6, ["VXXXXV", "VVVVVV", ".VVVV.", "..VV.."]),
            # Brass gate brackets framing one picture above and below the film.
            line(gx - 1, y0 - 2, gx + 2, y0 - 2, "P"), px(gx - 1, y0 - 1, "O"), px(gx - 1, y0 - 2, "Q"),
            line(gx + S.PITCH - 3, y0 - 2, gx + S.PITCH, y0 - 2, "P"), px(gx + S.PITCH, y0 - 1, "O"),
            line(gx - 1, y1 + 2, gx + 2, y1 + 2, "O"), px(gx - 1, y1 + 1, "O"),
            line(gx + S.PITCH - 3, y1 + 2, gx + S.PITCH, y1 + 2, "O"), px(gx + S.PITCH, y1 + 1, "O"),
            px(gx + S.PITCH, y1 + 2, "N")]


def timecode(f):
    """Honest SMPTE-style SS:FF at 24 fps: the real time since the loop began (70 ms a frame)."""
    n = (f * 70 * 24) // 1000
    return f"{n // 24:02d}:{n % 24:02d}"


def timer_digits(f):
    return [text(154, S.BENCH_Y - 11, timecode(f), "b")]


# ---------------------------------------------------------------- recipe
def recipe(name, speed=1, fluid_name="tray"):
    fluid = fluid_frames() if fluid_name == "tray" else fluid_frames_named(fluid_name)
    frames = [{"name": "base", "duration": S.MS, "ops": base_ops()}]
    names = []
    for f in range(S.FRAMES):
        s = S.offset(f, speed)
        fname = f"{name}-{f}"
        names.append(fname)
        frames.append({"name": fname, "duration": S.MS, "from": "base",
                       "layers": [
                           {"name": "film", "ops": film_ops(s) + film_light() + gate_light()},
                           {"name": "liquid", "ops": at(fluid[f], S.FLUID_X, S.FLUID_Y)
                            + liquid_post(f, S.BURST_DRIPS if speed == 2 else S.DRIPS)},
                           {"name": "front", "ops": glass_front() + playhead_and_gate() + timer_digits(f)},
                       ]})
    return {"version": 1, "name": name, "width": W, "height": H, "palette": palette_for(RECIPES), "ramps": RAMPS,
            "frames": frames, "animations": {name: {"frames": names}}}


def fluid_frames_named(name):
    recipe_ = json.loads((BUILD / f"{name}.json").read_text(encoding="utf-8"))
    return [f["ops"] for f in recipe_["frames"] if f["name"].rsplit("-", 1)[0] == "tray"]


def main():
    RECIPES.mkdir(exist_ok=True)
    out = {"cutbolt": recipe("cutbolt")}
    if "--burst" in sys.argv and (BUILD / "tray-burst.json").exists():
        out["cutbolt-burst"] = recipe("cutbolt-burst", speed=2, fluid_name="tray-burst")
    for name, rec in out.items():
        (RECIPES / f"{name}.json").write_text(json.dumps(rec, separators=(",", ":")) + "\n", encoding="utf-8",
                                              newline="\n")
    (BUILD / "still.txt").write_text(f"cutbolt-{STILL}\n", encoding="utf-8", newline="\n")
    print("recipes written:", ", ".join(out), "; still frame", STILL)


if __name__ == "__main__":
    main()
