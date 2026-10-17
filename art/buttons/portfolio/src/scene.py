"""Portfolio button (140x32): a little terminal on a ledge of the workbench, its mint screen lighting the wood. Once a
cycle its cursor types a command, Enter scrolls the screen, and the listing prints: four chips in the four tool cards'
colours (mint Anode, violet Inkbolt, pink Cutbolt, molten Pixelbolt). The scene sits in x 3-29; the rest of the
button stays plain night for the integrator's two vector text lines and arrow.

Frames (70 ms): 0-1 rest, 2-9 typing (one key a frame, the drive LED ticking), 10-12 Enter scrolls the screen a line a
frame while the listing prints, 13 the new prompt, 15-16 the cursor blinks, 21 the hold (the still).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from pb import rect, line, px, pxs, dither, shade, shift  # noqa: E402
from bench import ledge_layer, pool, contact_shadow, halo  # noqa: E402

NAME, KIND = "portfolio", "portfolio"
FRAMES = 22
VARIANTS = {"regular": (140, 32)}
TITLE = "Explore my portfolio"
DESC = ("Pixel art made with Pixelbolt: a little terminal on a ledge of the workbench, its mint screen lighting the "
        "wood; its cursor types a command and the screen lists four projects.")

# Scene geometry (canvas coordinates).
MX0, MY0, MX1, MY1 = 5, 4, 26, 20            # monitor body
SX0, SY0, SX1, SY1 = 7, 6, 24, 17            # screen
LEDGE_Y = 26
TEXT_X = 11                                  # first column of typed text
ROWS = (7, 9, 11)                            # the three history rows
PROMPT_Y = 14                                # the prompt's middle row (chevron 13-15)

# One command and its two-line listing, as runs of (x offset, length, colour). The history at rest shows the same
# three lines, so the screen after Enter equals the screen before typing.
CMD = [(0, 2, "l"), (3, 1, "l"), (5, 3, "l")]
OUT1 = [(0, 2, "l"), (3, 2, "y"), (6, 2, "X"), (9, 2, "f")]     # the four tool cards' accents
OUT2 = [(0, 4, "k"), (5, 2, "k"), (8, 3, "j")]
TYPED_ORDER = [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)]  # which run and char appears on each typing frame
TYPE_FRAMES = [2, 3, 5, 6, 7, 9]                                # the space and a hesitation leave gaps


def runs(y, spec, x0=TEXT_X, upto=None):
    ops = []
    for k, (dx, n, c) in enumerate(spec):
        if upto is not None:
            if k > upto[0]:
                break
            if k == upto[0]:
                n = upto[1] + 1
        ops.append(line(x0 + dx, y, x0 + dx + n - 1, y, c))
    return ops


def history_mark(y):
    return [px(SX0 + 2, y, "j")]


def screen(i):
    """The screen's contents on frame i."""
    ops = [rect(SX0, SY0, SX1 - SX0 + 1, SY1 - SY0 + 1, "h"),
           # The glass catches the moon along its top edge and the corners round off into the bezel.
           line(SX0 + 1, SY0, SX0 + 5, SY0, "i"), px(SX0 + 1, SY0 + 1, "i")]
    lines = [("cmd", CMD), ("out1", OUT1), ("out2", OUT2)]
    scroll = 0
    if 10 <= i <= 12:
        scroll = i - 9
    elif i >= 13:
        scroll = 0                                # back to rest: the new history equals the old
    # History rows: the buffer is [cmd, out1, out2, cmd', out1', out2']; the view shows three lines from `scroll`.
    buf = lines + lines
    for r, y in enumerate(ROWS):
        k = r + scroll
        if k >= len(buf):
            continue
        name, spec = buf[k]
        if 10 <= i <= 12 and k >= 3 + (i - 10) + 1 and name != "cmd":
            continue                              # listing lines print one per frame after Enter
        ops += runs(y, spec)
        if name == "cmd":
            ops += history_mark(y)
    # The prompt row.
    if i < 10 or i >= 13:
        ops += pxs([(SX0 + 1, PROMPT_Y - 1), (SX0 + 2, PROMPT_Y), (SX0 + 1, PROMPT_Y + 1)], "l")
        typed = sum(1 for f in TYPE_FRAMES if f <= i) if i < 10 else 0
        if typed:
            run, ch = TYPED_ORDER[typed - 1]
            ops += runs(PROMPT_Y, CMD, upto=(run, ch))
            cx = TEXT_X + CMD[run][0] + ch + 2
        else:
            cx = TEXT_X
        blink_off = i in (15, 16)
        if not blink_off:
            ops += [rect(cx, PROMPT_Y - 1, 2, 3, "m"), px(cx, PROMPT_Y - 1, "n")]
    # Screen corners round into the bezel.
    ops += pxs([(SX0, SY0), (SX1, SY0), (SX0, SY1), (SX1, SY1)], "B")
    return ops


def monitor(i):
    ops = [
        # Body and its moonlit top-left edges, shadowed right and bottom.
        rect(MX0, MY0, MX1 - MX0 + 1, MY1 - MY0 + 1, "C"),
        line(MX0 + 1, MY0, MX1 - 1, MY0, "D"), line(MX0, MY0 + 1, MX0, MY1 - 1, "D"), px(MX0 + 1, MY0 + 1, "E"),
        line(MX0 + 2, MY0, MX0 + 6, MY0, "E"),
        line(MX1, MY0 + 1, MX1, MY1 - 1, "B"), line(MX0 + 1, MY1, MX1 - 1, MY1, "B"),
        px(MX0, MY0, "B"), px(MX1, MY0, "B"), px(MX0, MY1, "A"), px(MX1, MY1, "A"),
        # The bezel's inner lip: dark under the top edge, lit along the bottom (the screen lights it).
        line(SX0 - 1, SY0 - 1, SX1 + 1, SY0 - 1, "B"), line(SX0 - 1, SY0, SX0 - 1, SY1, "B"),
        line(SX0, SY1 + 1, SX1, SY1 + 1, "j"), line(SX1 + 1, SY0, SX1 + 1, SY1, "i"),
        # The chin: a vent line and the drive LED.
        line(MX0 + 3, MY1 - 1, MX0 + 8, MY1 - 1, "B"),
        # Neck and foot.
        rect(14, MY1 + 1, 4, 3, "B"), line(14, MY1 + 1, 14, MY1 + 3, "C"), line(17, MY1 + 1, 17, MY1 + 3, "A"),
        rect(10, MY1 + 4, 12, 2, "C"), line(10, MY1 + 4, 21, MY1 + 4, "D"), line(10, MY1 + 4, 13, MY1 + 4, "E"),
        line(11, MY1 + 5, 21, MY1 + 5, "B"), px(10, MY1 + 5, "A"), px(21, MY1 + 5, "A"),
    ]
    # The drive LED: dim brass at rest, ticking molten as keys are typed and the listing loads.
    lit = i in TYPE_FRAMES or i in (10, 11, 12)
    ops.append(px(MX1 - 3, MY1 - 1, "f" if lit else "c"))
    return ops + screen(i)


def frame_ops(i, variant):
    cx = (MX0 + MX1) / 2 + 0.5
    ops = [rect(0, 0, 140, 32, "2")]
    # The screen's mint light on the wall round the monitor (faint) and banded on the ledge in front of it.
    # The house glow: a solid band of the darkest mint behind the monitor with a Bayer feather round it.
    ops += halo(cx, 13.5, 10.5, "h", 0.5, rx=14.4) + halo(cx, 13.5, 9.5, "h", 1.0, over=("2", "h"), rx=13.5)
    on_ledge = pool(cx, LEDGE_Y, [("j", 9, 0.5), ("j", 6, 1.0)]) + contact_shadow(cx, LEDGE_Y, 6)
    return {"ops": ops, "layers": [ledge_layer(2, 30, LEDGE_Y, on_ledge), {"name": "terminal", "ops": monitor(i)}]}
