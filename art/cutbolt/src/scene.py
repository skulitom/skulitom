"""Shared layout and timing for the Cutbolt card: one place for every coordinate the fluid source and the recipe share.

Canvas 192x100, 72 frames at 70 ms. Scene coordinates throughout; the fluid canvas has its own origin (FLUID_X, FLUID_Y).

The film path, in the direction the film travels: up out of the bath along a 2:1 diagonal, round a sprocket drum at
the upper left, then right along the top past the playhead gate and off the card. Strip coordinate p runs along that
path (0 at the top of the drum, positive along the top run, negative back round the drum and down the diagonal).
"""

import math

W, H = 192, 100
FRAMES, MS = 72, 70

BENCH_Y = 93                     # bench top rows 93-94, front 95-99

# A glass tray: walls at x 16 and 145 (inside 128 px, one fluid canvas), rim at y 78 (2 px above the developer, so
# a crown stands clear of the glass), glass bottom 91-92.
TRAY_X0, TRAY_X1, TRAY_RIM, TRAY_BOTTOM = 16, 145, 78, 91
SURFACE = 80                     # developer surface at rest (11 px deep)
FILL_Y = 82                      # where the sim's water is filled: FLIP settles about 2 px higher, at SURFACE

# The film: 16 px across. Rows from the outer edge: 0 edge, 1-2 perforations, 3 base, 4-11 the picture (8 rows),
# 12 base, 13-14 perforations, 15 edge. Frame pitch 12: a 1 px frame line, then an 11 px picture; three 2 px
# perforations a frame on each edge.
STRIP, PITCH = 16, 12
IMG_W, IMG_H, IMG_ROW = 11, 8, 4
HOLE_ROWS = (1, 2, 13, 14)
HOLE_OFFS = (1, 2, 5, 6, 9, 10)

# The drum and the runs.
RX, RY, R_IN = 34, 34, 6         # drum centre (a pixel corner) and radius; the film's inner edge wraps it
R_OUT = R_IN + STRIP             # 22
HY0 = RY - R_IN - STRIP          # 12: the top run's outer (upper) edge; rows 12-27
WRAP = 180 - math.degrees(math.atan2(1, 2))      # 153.4 degrees of drum the film wraps
R_MID = (R_IN + R_OUT) / 2
ARC_LEN = math.radians(WRAP) * R_MID            # about 37.5 px of film on the drum
TANGENT_X = 31                                  # the diagonal's inner edge leaves the drum at about x 31


def diag_top(x):
    """The diagonal's inner (upper) edge row at column x: it descends 1 px every 2 px to the right."""
    return (x + 48) // 2


DIAG_A = (31.5, (31.5 + 48) / 2)                # a point on the diagonal's inner edge line, by the drum
DIAG_D = (2 / math.sqrt(5), 1 / math.sqrt(5))  # along the diagonal, away from the drum
DIAG_N = (-1 / math.sqrt(5), 2 / math.sqrt(5)) # across it, from the inner edge to the outer
DIAG_W = STRIP * 2 / math.sqrt(5)              # its true width (the sheared band is 16 px tall)


def to_xy(seg, p, kc):
    """Scene position of film point p (along) and kc (across, from the outer edge; row k spans kc in [k, k+1)) on the
    drum or the diagonal: for placing whole marks (holes, frame lines, pictures) along the curve and the slope. On the
    diagonal, distance along the film is counted in columns (each 2 px right is 1 px down), so marks a fixed distance
    apart land on an exact 2:1 grid; across, they stand off the inner edge square to the film."""
    if seg == "drum":
        a = math.radians(-90 - math.degrees(-p / R_MID))
        r = R_OUT - kc
        return RX + r * math.cos(a), RY + r * math.sin(a)
    t = -ARC_LEN - p
    c = (STRIP - kc) / STRIP * DIAG_W
    return (DIAG_A[0] + t + DIAG_N[0] * c, DIAG_A[1] + t / 2 + DIAG_N[1] * c)


# The drum's outer edge, drawn as a pixel artist draws a circle: in the top octant the runs of each row shrink
# steadily (5, 3, 2, 2, 1, 1, 1 columns), and the side octant mirrors it, so the arc has no uneven steps or doubled
# corners. JT[i] is the edge's height (rows above the centre, from 0) in the i-th column left of the centre.
JT = [21] * 5 + [20] * 3 + [19] * 2 + [18] * 2 + [17, 16, 15]


def _quadrant(x, y):
    return RX - 1 - x, (RY - 1 - y) if y < RY else (y - RY)


def drum_inside(x, y):
    i, j = _quadrant(x, y)
    if i < 0:
        return False
    return (j <= 14 and i <= JT[j]) or (j >= 15 and i <= 14 and j <= JT[i])


def drum_edge(x, y):
    i, j = _quadrant(x, y)
    return i >= 0 and ((i <= 14 and j >= 15 and j == JT[i]) or (j <= 14 and i == JT[j]))


def locate(x, y):
    """Where pixel (x, y) lies on the film path: (segment, p, k) with p along the film and k the row from the outer
    edge, or None. Geometry only (which pixels the film covers, and where along it they fall)."""
    if y >= HY0 and y < HY0 + STRIP and x >= RX:
        return "top", float(x - RX), y - HY0
    dx, dy = x + 0.5 - RX, y + 0.5 - RY
    r = math.hypot(dx, dy)
    if r >= R_IN and drum_inside(x, y):
        sweep = (-90 - math.degrees(math.atan2(dy, dx))) % 360    # 0 at the top, growing round the left
        if sweep <= WRAP:
            k = 0 if drum_edge(x, y) else max(1, min(STRIP - 1, int(R_OUT - r)))
            return "drum", -math.radians(sweep) * R_MID, k
    if r >= R_IN and x >= 24:
        top = diag_top(x)
        if top <= y < top + STRIP:
            return "diag", -ARC_LEN - (x - TANGENT_X), STRIP - 1 - (y - top)
    return None


def film_bottom(x):
    """The lowest film pixel in column x above the bath (where a bead can hang), or None."""
    for y in range(SURFACE - 1, HY0 - 1, -1):
        if locate(x, y):
            return y
    return None


# The playhead gate frames one picture on the top run at p 84-95 (x 118-129).
GATE_P = 84
GATE_X = RX + GATE_P

# The safelight: a pendant hanging in the wedge between the two runs, its cable running up behind the top run.
LAMP = (64, 41)                  # the glass rim of the pendant (its bulb glows just below), over the drips

# Strip motion: 12 pulls a loop, one picture (12 px) each. Each 6-frame cycle holds 4 frames, then pulls over 2
# (4 px, 6 px, and the last 2 px land on the next cycle's first frame), like a film viewer's claw. PHASE puts the loop
# seam in the middle of a hold: pulls happen on frames 2-3, 8-9, ... 68-69.
PULL = (0, 0, 0, 0, 4, 10)
PHASE = 2
N_IMG = 6                        # a bouncing ball, six pictures a bounce, two bounces a loop
PERIOD = PITCH * 12              # the film advances 144 px a loop (12 frames); one frame line carries a splice


def offset(f, speed=1):
    """How far the film has advanced at frame f (px), modulo its pattern. speed 2 pulls every 3 frames (the hover
    burst): 24 pulls a loop, each a 1-frame yank (7 px, then 5) after a 2-frame hold."""
    if speed == 2:
        g = f % FRAMES + 1
        return (PITCH * (g // 3) + (0, 0, 7)[g % 3]) % PERIOD
    g = f % FRAMES + PHASE
    return (PITCH * (g // 6) + PULL[g % 6]) % PERIOD


def pull_frame(cycle):
    """The first moving frame of a pull (cycle 0 pulls at frame 2)."""
    return 6 * cycle + 4 - PHASE


# Picture numbers fall along the film (upstream frames come later), chosen so the gate holds picture 0, the ball's
# squash on the ground, on frames 70-1: the moment the seam drop lands in the bath.
IMG_K = GATE_P // PITCH


def picture(j):
    return (IMG_K - j) % N_IMG


# A splice: one frame line in twelve is a taped cut. It holds in the gate's bracket on frames 34-37, mid-loop.
SPLICE_J = IMG_K - 6

# A trim hanging on a pin in the editor's bin (right of the gate): a cut piece of the same film, still.
TRIM_X, TRIM_Y, TRIM_LEN = 160, 34, 25


# Drips: developer runs down the diagonal's lower edge and hangs in beads that the pulls shake off.
# (x of the bead, first frame it gathers, the pull that shakes it off). The first lands on the loop seam.
DRIPS = [
    (42, pull_frame(7), pull_frame(10)),   # the seam drop, the longest fall with room for its crown:
                                           # gathers from 44, grows at 50 and 56, off at 62, lands on the seam
    (48, pull_frame(1), pull_frame(3)),    # gathers from 8, off at 20
    (57, pull_frame(4), pull_frame(6)),    # a short plink by the lamp: gathers from 26, off at 38
]

# Hover burst: the film pulls every 3 frames (moving frames 1, 4, ... 70); four of those pulls shake drops off.
BURST_DRIPS = [(42, 58, 67), (48, 4, 13), (57, 22, 31), (34, 40, 49)]

# The fluid canvas is the tray's inside, from above the highest bead to the glass bottom.
FLUID_X, FLUID_Y = TRAY_X0 + 1, 50
FLUID_W, FLUID_H = TRAY_X1 - TRAY_X0 - 1, TRAY_BOTTOM - 50        # 128 x 38
