"""Chinese Touch Typing tile (68x42, narrow 56x42): a three-key macropad on a ledge of the workbench, brass keycaps
lettered N, I and 3: the pinyin input for 你 (nǐ). A tone mark (the caron of the third tone) floats over the I. Once
a cycle the keys are typed in turn: the mark lifts away as N goes down, each key drops into its switch with a warm
backlight flash under it, and as 3 lands the caron drops back onto the I with a one-frame glint.

Frames (70 ms): 0 rest, 1-3 the caron lifts a pixel and fades, N down 2-3, I down 5-6, 3 down 8-9, caron back 10-12 (12 is the
glint), 21 the hold (the still: ǐ).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from pb import rect, line, px, pxs, grid, dither, shade, erase  # noqa: E402
from bench import ledge_layer, pool, contact_shadow  # noqa: E402

NAME, KIND = "chinese-touch-typing", "tile"
FRAMES = 22
VARIANTS = {"regular": (68, 42), "narrow": (56, 42)}
TITLE = "Chinese Touch Typing"
DESC = ("Pixel art made with Pixelbolt: a three-key macropad with brass keycaps lettered N, I and 3, the pinyin input "
        "for 你; the keys are typed in turn and the third-tone mark drops onto the I with a glint.")

LEDGE_Y = 23
CASE_TOP = 17                    # the case's top surface rows 17-18, front 19-22
KEY_TOP = 10                     # a key's top face rows 10-14, skirt 15-16
GLYPHS = {
    "N": ["x..x", "xx.x", "x.xx", "x..x"],
    "I": [".xxx", "..x.", "..x.", ".xxx"],
    "3": [".xxx", "..xx", "...x", ".xxx"],
}
PRESS = {"N": (2, 3), "I": (5, 6), "3": (8, 9)}       # frames each key is down
CARON = [".x...x", "..x.x.", "...x.."]             # the third-tone mark, 5 wide (padded)


def down(key, i):
    a, b = PRESS[key]
    if a <= i <= b:
        return 2
    if i == b + 1:
        return 1                                    # the key springs back over two frames
    return 0


def keycap(x, key, d):
    """A brass keycap 7 wide at x, shaped like a real cap: a dished top face 5 wide (lit along its top edge), sides that
    flare out to the full width as they come down, and a darker lip at the foot. d = how far it is pressed (0, 1, 2):
    the cap sinks into its switch and the flared skirt disappears into the case."""
    y = KEY_TOP + d
    ops = [
        # Top face with its moonlit top edge and left edge.
        rect(x + 1, y, 5, 5, "Q"), line(x + 1, y, x + 5, y, "R"), px(x + 1, y + 1, "R"),
        # The sides flare: one pixel out from the third row of the face, lit on the left, shadowed on the right.
        rect(x, y + 2, 1, 3, "P"), rect(x + 6, y + 2, 1, 3, "O"), px(x + 5, y + 4, "P"),
    ]
    if d < 2:
        # The skirt at full width and its darker lip; it shortens as the key sinks.
        ops += [line(x, y + 5, x + 6, y + 5, "P"), px(x + 6, y + 5, "O")]
        if d == 0:
            ops += [line(x, y + 6, x + 6, y + 6, "N")]
    else:
        ops += [line(x, y + 5, x + 6, y + 5, "N")]
    # The legend sits clear of the face's lit left edge (the N is four wide, so it sits a pixel right).
    gx = x + 2 if key == "N" else x + 1
    ops.append(grid(gx, y + 1, [r.replace("x", "N") for r in GLYPHS[key]]))
    return ops


def case(x0, x1):
    w = x1 - x0 + 1
    return [
        # Top surface (lit), front face, bevel and the moonlit left corner.
        rect(x0, CASE_TOP, w, 2, "B"), line(x0, CASE_TOP, x1, CASE_TOP, "C"), line(x0, CASE_TOP, x0 + 8, CASE_TOP, "D"),
        rect(x0, CASE_TOP + 2, w, 4, "A"), line(x0, CASE_TOP + 2, x0, CASE_TOP + 5, "B"),
        # A status LED and a USB port on the front.
        px(x1 - 3, CASE_TOP + 3, "c"), rect(x0 + 3, CASE_TOP + 4, 3, 1, "8"),
    ]


def backlight(x, d):
    """The warm light leaking from under a pressed key onto the case top round it."""
    if d == 0:
        return []
    ops = [line(x - 1, CASE_TOP, x + 7, CASE_TOP, "O"), line(x, CASE_TOP, x + 6, CASE_TOP, "P")]
    if d == 2:
        ops += [line(x + 1, CASE_TOP, x + 5, CASE_TOP, "g"), px(x - 1, CASE_TOP - 1, "N"), px(x + 7, CASE_TOP - 1, "N")]
    return ops


def caron(cx, i):
    """The tone mark over the I: it lifts a pixel and fades out over 1-3 (brass, darker brass, half gone), is gone 4-9,
    drops back in over 10-11, glints on 12 (the one white frame) and settles."""
    x, y = cx - 3, KEY_TOP - 6
    mark = lambda c: [r.replace("x", c) for r in CARON]
    if i == 1:
        return [grid(x, y - 1, mark("Q"))]
    if i == 2:
        return [grid(x, y - 1, mark("P"))]
    if i == 3:
        return [grid(x, y - 1, mark("O")), erase(x, y - 1, 6, 3, 0.5)]
    if 4 <= i <= 9:
        return []
    if i == 10:
        return [grid(x, y - 1, mark("O"))]
    if i == 11:
        return [grid(x, y, mark("P"))]
    ops = [grid(x, y, mark("Q")), px(x + 1, y, "R")]
    if i == 12:
        # The glint: a four-point sparkle centred on the mark's left arm.
        ops += [px(x + 1, y, "*"), px(x + 1, y - 1, "R"), px(x, y, "R"), px(x + 2, y, "R"), px(x + 1, y + 1, "R")]
    elif i == 13:
        ops += [px(x + 1, y - 1, "P")]
    return ops


def frame_ops(i, variant):
    w = VARIANTS[variant][0]
    dx = 0 if variant == "regular" else -6
    ledge = (14, 53) if variant == "regular" else (11, 45)
    x0, x1 = 20 + dx, 48 + dx
    keys = [("N", 22 + dx), ("I", 31 + dx), ("3", 40 + dx)]
    cx = (x0 + x1) / 2
    on_ledge = contact_shadow(cx, LEDGE_Y, 13)
    pad = case(x0, x1)
    for k, kx in keys:
        d = down(k, i)
        pad += backlight(kx, d) + keycap(kx, k, d)
    layers = [ledge_layer(ledge[0], ledge[1], LEDGE_Y, on_ledge),
              {"name": "pad", "ops": pad},
              {"name": "mark", "ops": caron(31 + dx + 3, i)}]
    return {"ops": [rect(0, 0, w, 42, "2")], "layers": layers}
