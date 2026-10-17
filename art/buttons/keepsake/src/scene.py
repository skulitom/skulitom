"""Keepsake tile (68x42, narrow 56x42): a cassette tape standing on a ledge of the workbench: a steel-blue shell, a
pale label hand-lettered KEEP with side A marked in pink, two reels behind the window, the write-protect notches and the
pinch-roller holes along its bottom edge, moonlit from the upper left. Once a cycle it saves: the reels spin up and
wind on, the label's record dot lights, and as they stop a sparkle flashes at its corner.

Frames (70 ms): 0-1 rest, 2-15 the reels turn (speeding up, then slowing), 3-12 the record dot, 13-16 the sparkle
(14 is the one white frame), 21 the hold (the still).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from pb import rect, ell, line, px, pxs, grid, shade  # noqa: E402
from bench import ledge_layer, contact_shadow  # noqa: E402

NAME, KIND = "keepsake", "tile"
FRAMES = 22
VARIANTS = {"regular": (68, 42), "narrow": (56, 42)}
TITLE = "Keepsake"
DESC = ("Pixel art made with Pixelbolt: a cassette tape labelled KEEP standing on a ledge of the workbench; its reels "
        "spin as it saves, and a sparkle flashes at its corner.")

LEDGE_Y = 23
W_, H_ = 26, 16                     # the cassette's size; its bottom row sits on the ledge top
LETTERS = {"K": ["x.x", "xx.", "x.x"], "E": ["xxx", "xx.", "xxx"], "P": ["xx.", "xxx", "x.."],
           "A": [".x.", "xxx", "x.x"]}
# Reel turns, in steps of a quarter of the fleck's circuit and half a hub tooth: one step a frame at speed (a 2-phase hub
# advanced two steps a frame would alias and look frozen), two frames a step as the reels start and stop; 12 steps in
# all, so both the hub (period 2) and the fleck (period 4) are back where they started.
STEPS = {2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9, 12: 10, 13: 11, 14: 11, 15: 12}
FLECK = [(2, 0), (4, 2), (2, 4), (0, 2)]          # on each tape pack's rim, turning clockwise


def step(i):
    return STEPS.get(i, 0 if i < 2 else 12)


def hub_phase(i):
    return step(i) % 2


HUBS = [[".E.", "E9E", ".E."], ["E.E", ".9.", "E.E"]]


def word(x, y, text, c):
    ops = []
    for k, ch in enumerate(text):
        ops.append(grid(x + 4 * k, y, [r.replace("x", c) for r in LETTERS[ch]]))
    return ops


def cassette(x0, y0, i):
    """The cassette's front, 26x16: rows 0-11 the shell with its label (title band 1-5, window band 6-10, a pink stripe
    on 11), rows 12-15 the bottom bridge."""
    x1, y1 = x0 + W_ - 1, y0 + H_ - 1
    ops = [
        # A blue shell: moonlit top and left edges, shadowed right and bottom, rounded corners.
        rect(x0, y0, W_, H_, "Z"), line(x0 + 1, y0, x1 - 1, y0, "@"), line(x0, y0 + 1, x0, y1 - 1, "@"),
        line(x0 + 1, y0, x0 + 8, y0, "#"), px(x0, y0 + 1, "#"), line(x1, y0 + 1, x1, y1 - 1, "W"),
        line(x0 + 1, y1, x1 - 1, y1, "W"),
        px(x0, y0, "2"), px(x1, y0, "2"), px(x0, y1, "2"), px(x1, y1, "2"),
        # Write-protect notches on the top edge; corner screws.
        px(x0 + 4, y0, "9"), px(x1 - 4, y0, "9"),
        px(x0 + 1, y0 + 1, "W"), px(x1 - 1, y0 + 1, "W"), px(x0 + 1, y1 - 1, "W"), px(x1 - 1, y1 - 1, "W"),
        # The label: pale, lit along its top, shadowed down its right; a pink stripe along its foot.
        rect(x0 + 2, y0 + 1, W_ - 4, 11, "x"), line(x0 + 2, y0 + 1, x1 - 2, y0 + 1, "G"),
        line(x1 - 2, y0 + 2, x1 - 2, y0 + 10, "w"), line(x0 + 2, y0 + 11, x1 - 2, y0 + 11, "V"),
    ]
    # Side A in pink, the title KEEP hand-lettered in ink.
    ops += [grid(x0 + 3, y0 + 2, [r.replace("x", "V") for r in LETTERS["A"]])]
    ops += word(x0 + 8, y0 + 2, "KEEP", "W")
    # The record dot on the label lights while it saves.
    ops.append(px(x1 - 3, y0 + 5, "d" if 3 <= i <= 12 else "w"))
    # The window: dark glass, two tape packs with their hubs, the tape run between them, a glint on the glass.
    wx0, wy0 = x0 + 5, y0 + 6
    ops += [rect(wx0, wy0, 16, 5, "9"), line(wx0, wy0, wx0 + 15, wy0, "8"), line(wx0, wy0, wx0, wy0 + 4, "8"),
            ell(wx0 + 1, wy0, 5, 5, "I"), ell(wx0 + 10, wy0, 5, 5, "I"), line(wx0 + 3, wy0 + 4, wx0 + 12, wy0 + 4, "H"),
            px(wx0 + 1, wy0 + 1, "J"), px(wx0 + 10, wy0 + 1, "J")]
    hub = HUBS[hub_phase(i)]
    fx, fy = FLECK[step(i) % 4]
    ops += [grid(wx0 + 2, wy0 + 1, hub), grid(wx0 + 11, wy0 + 1, hub), px(wx0 + 7, wy0 + 1, "W"), px(wx0 + 8, wy0 + 2, "W"),
            px(wx0 + 1 + fx, wy0 + fy, "H"), px(wx0 + 10 + fx, wy0 + fy, "H")]
    # The bottom bridge with its pinch-roller holes.
    bx0 = x0 + 5
    ops += [rect(bx0, y1 - 3, W_ - 10, 3, "W"), line(bx0, y1 - 3, bx0 + W_ - 11, y1 - 3, "@"), px(bx0, y1 - 3, "#"),
            px(bx0 + 2, y1 - 2, "8"), px(bx0 + 5, y1 - 2, "8"), px(bx0 + 10, y1 - 2, "8"), px(bx0 + 13, y1 - 2, "8")]
    return ops


def sparkle(x, y, i):
    if i == 13:
        return pxs([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], "E") + [px(x, y, "G")]
    if i == 14:
        return pxs([(x, y - 2), (x - 2, y), (x + 2, y), (x, y + 2)], "E") + \
            pxs([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], "G") + [px(x, y, "*")]
    if i == 15:
        return pxs([(x, y - 2), (x - 2, y), (x + 2, y), (x, y + 2)], "D") + [px(x, y, "F")]
    if i == 16:
        return [px(x, y, "D")]
    return []


def frame_ops(i, variant):
    w = VARIANTS[variant][0]
    dx = 0 if variant == "regular" else -6
    ledge = (14, 53) if variant == "regular" else (11, 45)
    x0, y0 = 21 + dx, LEDGE_Y - H_
    cx = x0 + W_ / 2
    on_ledge = contact_shadow(cx, LEDGE_Y, 12)
    layers = [ledge_layer(ledge[0], ledge[1], LEDGE_Y, on_ledge),
              {"name": "cassette", "ops": cassette(x0, y0, i)},
              {"name": "sparkle", "ops": sparkle(x0 + W_ + 1, y0 - 1, i)}]
    return {"ops": [rect(0, 0, w, 42, "2")], "layers": layers}
