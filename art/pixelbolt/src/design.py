"""Layout and timeline of the Pixelbolt card, shared by the fluid, pose and recipe generators.

Card 192x100, 72 frames at 70 ms. Coordinates are card pixels, top-left origin.
CARD_VARIANT=burst selects the hover burst: the same scene and loop length, a bigger, faster pour with more sparks,
and the cast star doing a little hop on the rack. It starts and ends on the main loop's frame 0.
"""

import os

VARIANT = os.environ.get("CARD_VARIANT", "loop")
BURST = VARIANT == "burst"

W, H = 192, 100
FRAMES, MS = 72, 70

# The sprite being forged: a 7x7 star, cast at 4x. Keys: N darkest brass, O shade, P body, Q light, R specular.
STAR = ["...#...", "..###..", "#######", ".#####.", "..###..", ".##.##.", ".#...#."]
STAR_1X = ["...Q...", "..RQP..", "QQQQPPO", ".QQPPO.", "..QPO..", ".QP.OO.", ".P...N."]
SCALE = 4
STAR_W = 7 * SCALE

# Bench.
BENCH_Y = 82            # top surface rows 82-84, front from 85

# Mould: two steel halves on the bench, a 4x star cavity, a small chamfer at the top point.
MOULD = (84, 46, 36, 36)              # x, y, w, h -> x 84-119, y 46-81
CAVITY = (88, 50)                     # star cavity top-left (28x28)
PARTING = 102                         # first column of the right half
TOP_POINT = (100, 103)                # the star's top point columns (the gate)

# Crucible: hangs from a chain; the pot turns about its pivot boss.
PIVOT = (92, 26)
POSE_ORIGIN = (24, 24)     # the pose canvas origin that the compiled stamps are placed against

# Rack: brass shelf on the bench, slots 32 px apart.
RACK_SLOTS = (125, 157)               # left x of the cast star in slot 0 and slot 1

# Fluid canvases (origin x, y, width, height).
POUR_BOX = (84, 26, 36, 56)
SMOKE_BOX = (88, 0, 96, 50)
DUST_BOX = (108, 66, 64, 18)
EMBER_BOX = (70, 0, 40, 30)

# Timeline (card frames). Pose names come from poses.py.
CRUCIBLE = (["tilt0"] * 3 + ["tiltm8"] * 3 + ["tilt20", "tilt34"] + ["tilt45"] * 29 + ["tilt34", "tilt20"]
            + ["tiltm4"] * 2 + ["tilt0"] * 31)
POUR_START = 8           # pour sim frame 0 (the stream leaves the spout) lands on this card frame
POUR_FRAMES = 48         # length of the one-shot pour sim; its last frame holds afterwards
IMPACT = 16              # first impact on the cavity floor (sim frame 8)
STAGE_ORANGE = 42        # cooling: the liquid steps one ramp step down
STAGE_RED = 45           # the solid star covers the liquid, glowing red (held 6 frames)
STAGE_BRONZE = 51        # dull bronze
STAGE_GOLD = 53          # finished brass; its outline appears now it is cold
LATCH_UP = (54, 65)      # latch lifted on these frames (inclusive start, exclusive end)
OPEN = {55: 2, 56: 3, 57: 3, 58: 3, 59: 3, 60: 3, 61: 3, 62: 3, 63: 2}   # frame -> each half's shift
POP = {56: (88, 46), 57: (93, 39), 58: (100, 35), 59: (107, 34), 60: (114, 37), 61: (120, 43)}
LAND = 62                # lands in rack slot 0 (dust puff); 63 bounces up 2 px, 64 settles
GLINT = (64, 68)         # glint sweep frames (a white specular on the third)
ADVANCE = {68: 4, 69: 14, 70: 26, 71: 33}   # rack shift in px: eases in, overshoots 1 px, settles on 0
STILL = 33               # reduced motion: the stream still pouring, the star nearly full and glowing, smoke curling

# Pour emitter (radius, last sim frame), whitewater and smoke strength.
POUR_RADIUS, POUR_END = 2.15, 27
SPARKS = 1.0
SMOKE = 1.0
HOP = {63: -2}          # extra y offsets of the landed star (63: the bounce)

if BURST:
    POUR_RADIUS, POUR_END = 2.55, 19
    SPARKS, SMOKE = 1.8, 1.0   # same smoke as the loop, so the site can swap loops on frame 0 without a jump
    CRUCIBLE = (["tilt0"] * 3 + ["tiltm8"] * 3 + ["tilt20", "tilt34"] + ["tilt45"] * 21 + ["tilt34", "tilt20"]
                + ["tiltm4"] * 2 + ["tilt0"] * 39)
    STAGE_ORANGE, STAGE_RED, STAGE_BRONZE, STAGE_GOLD = 37, 40, 47, 50
    LATCH_UP = (51, 63)
    OPEN = {52: 2, **{f: 3 for f in range(53, 61)}, 61: 2}
    POP = {53: (88, 46), 54: (93, 39), 55: (100, 35), 56: (107, 34), 57: (114, 37), 58: (120, 43)}
    LAND = 59
    HOP = {60: -2, 61: 0, 62: -5, 63: -8, 64: -9, 65: -8, 66: -5}   # a bounce, then a little hop of joy
    GLINT = (63, 67)
