"""Generate the Anode card recipes: recipes/anode.json (the 72-frame loop) and recipes/anode-burst.json (the site's
48-frame hover burst), each with two static frames (bg, near) before its loop.

Python lays out drawing operations (shapes, lines, hand-placed pixels, symbol stamps, dither and shade regions, glow
bands built row by row) and places the compiled mist frames as layers. It never computes an effect pixel: every
dither, shade band and fluid pixel is drawn by Pixelbolt when the recipe renders.

Frames: `bg` is everything behind the mist (the back room, its desk and monitor, the near floor and its light pool);
`near` is everything in front of it on a transparent canvas (the front wall with the doorway cut out, your desk). Each
loop frame starts from bg, then draws the agent's screen, the wisps, the fog, the agent cursor, a copy of `near`
(transparent pixels skipped, so the doorway shows the mist), and the near plane's few moving pixels.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import path as P  # noqa: E402
from kit import dither, fluid_frames, line, px, rect, shade, write_json  # noqa: E402
from layout import (AD_TOP, AD_X0, AD_X1, AM, AS, BACK_FLOOR, BURST, DOOR_TOP, DOOR_X0, DOOR_X1, FOG,  # noqa: E402
                    FRAMES, H, MS, P1, PATH, REVEAL, THRESHOLD, TOWER, TRIM, W, WISPS, YD_TOP, YD_X1, YM, YS)

PIECE = Path(__file__).resolve().parents[1]
BUILD, RECIPES = PIECE / "out" / "build", PIECE / "out" / "recipes"
STILL = 58

PALETTE = {"$ref": "../../../palette.json"}
# The mist's smoke steps each pair with a lighter mint step, so one `shade` +1 tints the mist mint, and lighter, where
# the agent's screen lights it (t->i, u->j, v->k, w->l). Other materials keep their own ramps.
RAMPS = [
    ["t", "i"], ["u", "j"], ["v", "k"], ["w", "l"], ["x", "m"],
    ["0", "1", "2", "3", "4", "5", "6", "7"],
    ["A", "B", "C", "D", "E", "F", "G"],
    ["H", "I", "J", "K", "L", "M"],
    ["N", "O", "P", "Q", "R"],
    ["8", "9", "W", "Z", "@", "#", "$"],
]

SYMBOLS = {
    # The agent's cursor: a mint arrow with its stem, outlined in the darkest teal of its own ramp. Hotspot = top-left.
    "agent": [
        "h.....",
        "hh....",
        "hnh...",
        "hnnh..",
        "hnnnh.",
        "hnnnnh",
        "hnmhhh",
        "hhhmh.",
        "...hmh",
        "....h.",
    ],
    # Your pointer: pale steel, outlined in steel, idling on the current line of your editor.
    "yours": [
        "B.....",
        "BB....",
        "BEB...",
        "BEEB..",
        "BEEEB.",
        "BEEEEB",
        "BEEBBB",
        "BEB...",
        "BB....",
    ],
    "yours-shadow": [
        "0.....",
        "00....",
        "000...",
        "0000..",
        "00000.",
        "000000",
        "000...",
        "00....",
        "0.....",
    ],
    "gamepad": [
        ".BBBBB.",
        "BCBBBiB",
        "BBBBBBB",
        ".B...B.",
    ],
}


# ------------------------------------------------------------------ helpers
def ellipse_rows(cx, cy, rx, ry):
    """(y, x0, x1) spans of a pixel ellipse, for glow bands built row by row (the house glow)."""
    out = []
    for y in range(math.floor(cy - ry), math.ceil(cy + ry) + 1):
        dy = (y + 0.5 - cy) / ry
        if abs(dy) >= 1:
            continue
        half = rx * math.sqrt(1 - dy * dy)
        x0, x1 = round(cx - half), round(cx + half)
        if x1 > x0:
            out.append((y, x0, x1))
    return out


def glow_band(cx, cy, rx, ry, color, over, density=1, clip=None):
    ops = []
    for (y, x0, x1) in ellipse_rows(cx, cy, rx, ry):
        if clip:
            x0, x1 = max(x0, clip[0]), min(x1, clip[1])
            if y < clip[2] or y >= clip[3] or x1 <= x0:
                continue
        ops.append(dither(x0, y, x1 - x0, 1, color, density, over=over))
    return ops


# ------------------------------------------------------------------ bg: behind the mist
def back_room():
    """The back room through the doorway: a darker wall, its floor, the screen's glow on the wall and floor."""
    x0, x1 = DOOR_X0 - TRIM, DOOR_X1 + TRIM
    ops = [rect(x0, 0, x1 - x0, BACK_FLOOR, "1"), rect(x0, BACK_FLOOR, x1 - x0, THRESHOLD - BACK_FLOOR, "2")]
    cx, cy = AM[0] + AM[2] / 2, AM[1] + AM[3] / 2
    # Glow on the back wall round the monitor: night 1 -> 2 -> mint, two bands, each with a Bayer feather.
    ops += glow_band(cx, cy, 30, 21, "2", ["1"], 0.5) + glow_band(cx, cy, 26, 18, "2", ["1"])
    ops += glow_band(cx, cy, 21, 14, "h", ["2"], 0.5) + glow_band(cx, cy, 18, 12, "h", ["2"])
    # The pool under the desk on the back floor.
    ops += glow_band(cx, BACK_FLOOR + 3, 30, 5, "h", ["2"], 0.5, clip=(0, W, BACK_FLOOR, THRESHOLD))
    ops += glow_band(cx, BACK_FLOOR + 3, 22, 4, "h", ["2"], 1, clip=(0, W, BACK_FLOOR, THRESHOLD))
    return ops


def agent_desk():
    """The agent's desk at about 60% of yours: dark wood with the screen's light on its top."""
    ops = [rect(AD_X0, AD_TOP, AD_X1 - AD_X0, 2, "I"), line(AD_X0, AD_TOP, AD_X1 - 1, AD_TOP, "J"),
           rect(AD_X0, AD_TOP + 2, AD_X1 - AD_X0, 3, "H"),
           rect(AD_X0 + 2, AD_TOP + 5, 2, BACK_FLOOR - AD_TOP - 4, "H"),
           rect(AD_X1 - 4, AD_TOP + 5, 2, BACK_FLOOR - AD_TOP - 4, "H")]
    ops += [dither(AD_X0 + 8, AD_TOP, AD_X1 - AD_X0 - 16, 1, "i", 1, over=["J"]),
            dither(AD_X0 + 3, AD_TOP, AD_X1 - AD_X0 - 6, 1, "i", 0.5, over=["J"])]
    # Monitor: bezel, an inner rim lit by the screen, the screen (the brightest mint in the card), a stand.
    x, y, w, h = AM
    sx, sy, sw, sh = AS
    ops += [rect(x, y, w, h, "A"), line(x, y, x + w - 1, y, "B"), line(x, y, x, y + h - 1, "B"),
            rect(sx - 1, sy - 1, sw + 2, sh + 2, "i"), rect(sx, sy, sw, sh, "k")]
    cx = x + w // 2
    ops += [rect(cx - 1, y + h, 3, AD_TOP - (y + h), "A"), line(cx - 4, AD_TOP - 1, cx + 4, AD_TOP - 1, "B")]
    # The agent's desktop: a log window it reads (left) and a panel with the button it clicks (right).
    ops += [rect(sx + 2, sy + 2, 14, 11, "j"), rect(sx + 2, sy + 2, 14, 1, "l")]
    for k, (n, col) in enumerate(((10, "l"), (7, "l"), (11, "m"), (6, "l"))):
        ops.append(line(sx + 4, sy + 5 + 2 * k, sx + 3 + n, sy + 5 + 2 * k, col))
    ops += [rect(sx + 19, sy + 3, 9, 9, "j"), rect(sx + 19, sy + 3, 9, 1, "l"), rect(sx + 21, sy + 9, 5, 2, "l")]
    # Keyboard and gamepad.
    kx = AD_X0 + 12
    ops += [rect(kx, AD_TOP - 2, 16, 2, "A"), line(kx + 1, AD_TOP - 2, kx + 14, AD_TOP - 2, "C")]
    ops += [{"op": "stamp", "x": GAMEPAD[0], "y": GAMEPAD[1], "symbol": "gamepad"}]
    return ops


GAMEPAD = (AD_X0 + 32, AD_TOP - 4)
BUTTON = (GAMEPAD[0] + 5, GAMEPAD[1] + 1)


def near_floor():
    """Your room's floor, and the mint light that spills through the doorway onto it as a widening banded pool."""
    ops = [rect(0, THRESHOLD, W, H - THRESHOLD, "1")]
    rows = 13
    for y in range(THRESHOLD, THRESHOLD + rows):
        far = y - THRESHOLD
        spread = far * 1.3
        trim = 3 if far >= rows - 3 else 0            # round the far corners
        x0, x1 = round(DOOR_X0 - spread) + trim, round(DOOR_X1 - REVEAL + spread) - trim
        density = 1 if far < 6 else 0.5 if far < rows - 1 else 0.25
        ops.append(dither(x0, y, x1 - x0, 1, "h", density, over=["1"]))
        if far < 5:
            ops.append(dither(x0 + 10, y, x1 - x0 - 20, 1, "i", 1 if far < 3 else 0.5, over=["h"]))
    # The cable from the tower runs across the floor and through the doorway to the agent's desk.
    tx = TOWER[0] + TOWER[2]
    ops += [line(tx, 95, DOOR_X0 + 3, 81, "B"), line(DOOR_X0 + 4, 80, AD_X0 + 3, BACK_FLOOR + 1, "A")]
    return ops


def bg_frame():
    return [rect(0, 0, W, H, "2")] + back_room() + agent_desk() + near_floor()


# ------------------------------------------------------------------ near: in front of the mist
def front_wall():
    """The front wall with a flat-lintelled doorway cut out. The trim is lit by the moon on its upper-left edges; the
    right jamb's inner face (the reveal) catches the agent's screen in mint bands; the lintel's underside is dark."""
    x0, x1 = DOOR_X0 - TRIM, DOOR_X1 + TRIM
    top = DOOR_TOP - TRIM - 1
    ops = [rect(0, 0, W, THRESHOLD, "2"), line(0, THRESHOLD - 1, W - 1, THRESHOLD - 1, "3"),
           rect(x0, top, x1 - x0, THRESHOLD - top, "3"),
           line(x0, top, x1 - 1, top, "4"), line(x0, top, x0, THRESHOLD - 1, "4"),
           line(x1 - 1, top + 1, x1 - 1, THRESHOLD - 1, "1"),
           {"op": "clear", "x": DOOR_X0, "y": DOOR_TOP, "w": DOOR_X1 - DOOR_X0, "h": THRESHOLD - DOOR_TOP}]
    # The lintel's underside and the right reveal, drawn back into the opening (in front of the mist).
    rx = DOOR_X1 - REVEAL
    ops += [rect(DOOR_X0, DOOR_TOP, DOOR_X1 - DOOR_X0, 2, "1"), line(DOOR_X0, DOOR_TOP + 1, rx - 1, DOOR_TOP + 1, "h"),
            rect(rx, DOOR_TOP, REVEAL, THRESHOLD - DOOR_TOP, "h"),
            rect(rx, 24, REVEAL - 1, 48, "i"), rect(rx, 34, 1, 28, "j"), rect(rx + REVEAL - 1, DOOR_TOP, 1, 68, "1")]
    # The threshold: a quiet step the fog spills over.
    ops.append(line(DOOR_X0, THRESHOLD, rx - 1, THRESHOLD, "3"))
    return ops


def moon_patch():
    """The moon, through a window off the frame's upper left, lays a two-pane patch on the front wall between your
    monitor and the doorway: night 3, sheared down-right with the light, soft-edged, the mullion and transom dark."""
    ops = []
    top, bottom, transom = 18, 58, (36, 37)
    for y in range(top, bottom):
        if y in transom:
            continue
        x0 = 68 + round((y - top) * 0.45)
        edge = y in (top, top + 1, bottom - 2, bottom - 1)
        for (a, b) in ((x0, x0 + 10), (x0 + 12, x0 + 22)):
            ops.append(dither(a, y, b - a, 1, "3", 0.5 if edge else 1, over=["2"]))
            if not edge:
                ops += [dither(a, y, 1, 1, "2", 1, over=["3"]), dither(b - 1, y, 1, 1, "2", 1, over=["3"])]
                ops.append(dither(a, y, 1, 1, "3", 0.5, over=["2"]))
    return ops


CURRENT_LINE = 4


def editor():
    """Your screen: a calm code editor in night and steel (mint stays the card's only accent): a tab bar, a gutter,
    indented lines, the current line highlighted."""
    sx, sy, sw, sh = YS
    ops = [rect(sx, sy, sw, sh, "1"), rect(sx, sy, sw, 3, "3"), rect(sx + 2, sy, 14, 3, "A"),
           rect(sx, sy + 3, 6, sh - 3, "2")]
    lines = [(0, 4, 12, "C"), (4, 3, 18, "C"), (4, 5, 10, "B"), (8, 3, 16, "C"), (8, 4, 8, "C"), (4, 2, 0, "C"),
             (0, 0, 0, ""), (0, 4, 14, "C"), (4, 3, 20, "C"), (4, 6, 9, "B"), (0, 2, 0, "C")]
    for k, (indent, kw, rest, col) in enumerate(lines):
        y = sy + 5 + 3 * k
        if y >= sy + sh - 1:
            break
        ops.append(px(sx + 3, y, "B"))
        if k == CURRENT_LINE:
            ops.append(rect(sx + 6, y - 1, sw - 6, 3, "A"))
        x = sx + 9 + indent
        if kw:
            ops.append(line(x, y, x + kw - 1, y, "D"))
        if rest:
            ops.append(line(x + kw + 1, y, x + kw + rest, y, col))
    return ops


def your_desk():
    ops = []
    # Monitor: a dark bezel with a cool moon rim along its top, then the editor.
    x, y, w, h = YM
    vis = max(x, 0)                                    # the frame crops the bezel's left edge
    ops += [rect(vis, y, w - (vis - x), h, "A"), line(vis, y, x + w - 1, y, "C"), line(x + 2, y, x + 24, y, "D"),
            line(x + w - 1, y + 1, x + w - 1, y + h - 1, "1"), rect(YS[0] - 1, YS[1] - 1, YS[2] + 2, YS[3] + 2, "B")]
    ops += editor()
    cx = x + w // 2
    ops += [rect(cx - 3, y + h, 6, YD_TOP - (y + h), "A"), line(cx - 3, y + h, cx - 3, YD_TOP - 1, "B")]
    # Desk: top, a moonlit lip, a dark face cropped by the frame.
    ops += [rect(0, YD_TOP, YD_X1, 3, "I"), line(0, YD_TOP, YD_X1 - 1, YD_TOP, "H"),
            line(0, YD_TOP + 3, YD_X1 - 1, YD_TOP + 3, "K"), line(0, YD_TOP + 3, 30, YD_TOP + 3, "L"),
            rect(0, YD_TOP + 4, YD_X1, H - YD_TOP - 4, "H"), line(YD_X1 - 1, YD_TOP, YD_X1 - 1, H - 1, "I")]
    # Your screen's cool light on the desk top in front of it, Bayer-feathered.
    ops += [dither(8, YD_TOP + 1, 46, 2, "A", 1, over=["I"]), dither(2, YD_TOP + 1, 58, 2, "A", 0.5, over=["I"])]
    # Keyboard (its top row catching the screen) and a mug (its left side lit by the screen, its rim by the moon).
    ops += [rect(16, YD_TOP + 1, 30, 2, "1"), line(17, YD_TOP + 1, 44, YD_TOP + 1, "C")]
    ops += [rect(68, YD_TOP - 6, 6, 7, "A"), line(68, YD_TOP - 6, 73, YD_TOP - 6, "C"),
            line(68, YD_TOP - 5, 68, YD_TOP, "C"), rect(74, YD_TOP - 4, 2, 3, "A"), px(75, YD_TOP - 3, "2")]
    # The one machine: the tower standing in front of your desk's end; its cable runs into the doorway.
    tx, ty, tw, th = TOWER
    ops += [rect(tx, ty, tw, th, "A"), line(tx, ty, tx + tw - 1, ty, "C"), line(tx, ty + 1, tx, H - 1, "B"),
            line(tx + tw - 1, ty + 1, tx + tw - 1, H - 1, "1"),
            line(tx + 3, ty + 8, tx + tw - 4, ty + 8, "B"), line(tx + 3, ty + 10, tx + tw - 4, ty + 10, "B"),
            px(tx + 3, ty + 4, "D")]
    return ops


def near_frame():
    return front_wall() + moon_patch() + your_desk()


# ------------------------------------------------------------------ animated
def agent_screen(t):
    """What changes on the agent's screen: the button it clicks, the status pip once the test passes."""
    sx, sy = AS[0], AS[1]
    ops = []
    if P.CLICK <= t < P.CLICK + 3:
        ops.append(rect(sx + 21, sy + 9, 5, 2, "n" if t == P.CLICK else "m"))
    lit = t >= P.PASS or t < 6
    ops.append(rect(sx + 13, sy + 3, 2, 1, "n" if lit else "l"))
    return ops


def burst_cursor(t):
    """The hover burst: the figure-eight; the gamepad's button blips each time the cursor crosses the middle."""
    x, y = BURST.cursor(t)
    ops = [{"op": "stamp", "x": x, "y": y, "symbol": "agent"}]
    if t in (P.LOBE_A[0], P.LOBE_B[0], P.DASH_OUT[0]):
        ops.append(px(*BUTTON, "n"))
    elif t - 1 in (P.LOBE_A[0], P.LOBE_B[0], P.DASH_OUT[0]):
        ops.append(px(*BUTTON, "m"))
    return ops


def agent_cursor(t):
    x, y = PATH.cursor(t)
    ops = [{"op": "stamp", "x": x, "y": y, "symbol": "agent"}]
    if t == P.CLICK:                # the click: a one-frame ripple round the hotspot
        ops += [px(x - 2, y, "n"), px(x + 2, y - 2, "n"), px(x, y - 2, "n"), px(x - 2, y - 2, "n")]
    elif t == P.CLICK + 1:
        ops += [px(x - 3, y + 1, "l"), px(x + 1, y - 3, "l"), px(x - 3, y - 3, "l")]
    if P.CLICK <= t < P.CLICK + 3:  # the gamepad's button lights with the click
        ops.append(px(*BUTTON, "n" if t == P.CLICK else "m"))
    return ops


def near_motion(t):
    """Your side's quiet motion: the caret blinks (24 frames), your pointer idles with its shadow, the tower's LED
    works (8 frames)."""
    sx, sy = YS[0], YS[1]
    ops = []
    cy = sy + 5 + 3 * CURRENT_LINE
    if t % 24 < 14:
        ops.append(line(sx + 37, cy - 1, sx + 37, cy + 1, "F"))
    ops += [{"op": "stamp", "x": 46, "y": cy, "symbol": "yours-shadow"},
            {"op": "stamp", "x": 44, "y": cy - 2, "symbol": "yours"}]
    tx, ty = TOWER[0], TOWER[1]
    ops.append(px(tx + 8, ty + 4, "l" if t % 8 < 3 else "i"))
    return ops


def mist_light(canvas, cx, cy, rx, ry):
    """Inside the fog layer: the low cushions' moonlit upper faces turn mint (x->m along the paired ramps) where they
    face the agent's screen, in an ellipse under it with a Bayer ring."""
    cx, cy = cx - canvas[0], cy - canvas[1]
    return [shade(round(cx - rx - 3), round(cy - ry - 2), 2 * rx + 6, 2 * ry + 4, 1, shape="ellipse", density=0.5,
                  over=["x"]),
            shade(round(cx - rx), round(cy - ry), 2 * rx, 2 * ry, 1, shape="ellipse", over=["x"])]


# Light and mint belong on the cushions' bodies, not on thin mist: any lit (x, F) or mint (l, m) pixel that touches
# empty space falls back to plain mist (v). Pixelbolt's light and shadow fields have no minimum-density gate, so a
# one-step rewrite does it inside each mist layer.
def thin_edges(canvas):
    """The rewrite, limited to the part of a mist canvas seen through the doorway."""
    x0 = DOOR_X0 - canvas[0]
    return {"op": "rewrite", "x": x0, "y": 0, "w": DOOR_X1 - REVEAL - DOOR_X0, "h": canvas[3], "empty": "_",
            "rotate": True, "seed": 3, "rules": [{"match": ["_" + c], "replace": [".v"]} for c in ("x", "F", "l", "m")]}


# ------------------------------------------------------------------ recipe
def recipe(burst=False):
    """The main loop, or (burst=True) the site's hover burst, on the same bg and near frames."""
    tag = "-burst" if burst else ""
    fog = fluid_frames(BUILD / f"fog{tag}.json", f"fog{tag}")
    wisps = fluid_frames(BUILD / f"wisps{tag}.json", f"wisps{tag}")
    sx = AS[0] + AS[2] / 2
    fog_light = mist_light(FOG, sx, AD_TOP, 24, 8)              # the low cushions' tops under the screen
    frames = [{"name": "bg", "duration": MS, "ops": bg_frame()},
              {"name": "near", "duration": MS, "ops": near_frame()}]
    names, prefix, count = [], "burst" if burst else "loop", P.BURST_FRAMES if burst else FRAMES
    for t in range(count):
        name = f"{prefix}-{t}"
        names.append(name)
        frames.append({"name": name, "duration": MS, "from": "bg", "layers": [
            {"name": "screen", "ops": agent_screen(P.PASS if burst else t)},
            {"name": "wisps", "x": WISPS[0], "y": WISPS[1], "ops": wisps[t] + [thin_edges(WISPS)]},
            {"name": "fog", "x": FOG[0], "y": FOG[1], "ops": fog[t] + fog_light + [thin_edges(FOG)]},
            {"name": "agent", "ops": burst_cursor(t) if burst else agent_cursor(t)},
            {"name": "near", "ops": [{"op": "copy", "from": "near", "x": 0, "y": 0}] + near_motion(t)},
        ]})
    return {"version": 1, "name": f"anode{tag}", "width": W, "height": H, "palette": PALETTE, "ramps": RAMPS,
            "symbols": SYMBOLS, "frames": frames, "animations": {prefix: {"frames": names}}}


def main():
    assert (P1[0] - 3, P1[1]) <= (AS[0] + 25, AS[1] + 10), "P1 should sit on the button"
    write_json(RECIPES / "anode.json", recipe())
    write_json(RECIPES / "anode-burst.json", recipe(burst=True))
    (BUILD / "still.txt").write_text(f"loop-{STILL}\n", encoding="utf-8", newline="\n")
    print("recipes written; still frame", STILL)


if __name__ == "__main__":
    main()
