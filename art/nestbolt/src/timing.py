"""The laser's timing: where the head is on every frame, and when each kerf pixel is cut.

The head follows nest.ROUTE: a rapid move (laser off) to each contour's start, a short pierce, then the cut at a
speed that eases into corners and runs faster on straights. After the last contour it rapids back to park. Times are
in frames (floats); frame k shows the state at time k. Python only plans positions and timing; Pixelbolt draws every
pixel.
"""

import math

import nest
from variant import BURST

PARK = (8, -3)         # sheet-local head position when parked (over the bed's back lip, clear of the extractor)
PIERCE = 1.0           # frames at a pierce: exactly one frame of each shows the white pierce flash
if BURST:              # the hover burst: the head races the nest
    LEAVE_PARK, AIM, V_CUT, V_SLOW, V_RAPID, DWELL, RETURN = 1.0, 1.0, 12.0, 7.5, 24.0, 2.0, 3.0
else:
    LEAVE_PARK = 2.0   # the head leaves park on this frame (69-2 is the opening hold)
    AIM = 1.5          # it settles over the first pierce point (pointer dot on) before firing: anticipation
    V_CUT = 6.4        # px per frame on a straight (the beam's Y speed on vertical cuts too)
    V_SLOW = 3.8       # px per frame into and out of a corner
    V_RAPID = 14.0     # px per frame with the laser off
    DWELL = 3.0        # after the last cut the head holds still while the parts settle
    RETURN = 3.0       # frames to rapid back to park


def seg_len(a, b):
    return max(abs(b[0] - a[0]), abs(b[1] - a[1]))


def turn(a, b, c):
    """Turning angle in degrees at b."""
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    d = v1[0] * v2[0] + v1[1] * v2[1]
    n = math.hypot(*v1) * math.hypot(*v2)
    return math.degrees(math.acos(max(-1.0, min(1.0, d / n))))


def segment_time(length, slow_in, slow_out):
    """Trapezoid profile: start and end speeds depend on the corners, cruise at V_CUT."""
    v0 = V_SLOW if slow_in else V_CUT
    v1 = V_SLOW if slow_out else V_CUT
    ramp = 1.5
    if length <= 2 * ramp:
        return length / ((v0 + v1) / 2)
    return ramp / ((v0 + V_CUT) / 2) + (length - 2 * ramp) / V_CUT + ramp / ((v1 + V_CUT) / 2)


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def plan():
    """Contours with per-vertex cut times, plus the head's moves as a list of timed pieces."""
    t = LEAVE_PARK
    pos = PARK
    contours, moves = [], []
    for kind, pts in nest.ROUTE:
        d = math.hypot(pts[0][0] - pos[0], pts[0][1] - pos[1])
        # never a one-frame jump, and the 88 px beam never moves more than about 5 px a frame in Y (an eased move
        # peaks at 1.5 times its mean speed)
        rapid = max(2.0, d / V_RAPID + 0.8, 0.3 * abs(pts[0][1] - pos[1]))
        moves.append(("rapid", t, t + rapid, pos, pts[0]))
        t += rapid
        if not contours:
            moves.append(("aim", t, t + AIM, pts[0], pts[0]))
            t += AIM
        moves.append(("pierce", t, t + PIERCE, pts[0], pts[0]))
        pierce_t = t
        t += PIERCE
        times = [t]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            slow_in = i == 0 or turn(pts[i - 1], a, b) > 30
            slow_out = i == len(pts) - 2 or turn(a, b, pts[i + 2]) > 30
            dt = segment_time(seg_len(a, b), slow_in, slow_out)
            moves.append(("cut", t, t + dt, a, b))
            t += dt
            times.append(t)
        contours.append({"kind": kind, "pts": pts, "times": times, "pierce": pierce_t})
        pos = pts[-1]
    moves.append(("aim", t, t + DWELL, pos, pos))
    moves.append(("rapid", t + DWELL, t + DWELL + RETURN, pos, PARK))
    return contours, moves


CONTOURS, MOVES = plan()
CUT_END = CONTOURS[-1]["times"][-1]
DROP = (math.ceil(CUT_END), math.ceil(CUT_END) + 1)   # the freed parts settle (those at the closing point first)


def head_at(t):
    """(x, y, state, direction) in sheet-local floats; state is park, rapid, aim (still, laser off), pierce or
    cut."""
    for kind, t0, t1, a, b in MOVES:
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            if kind in ("rapid", "aim"):
                u = smooth(u)
            x = a[0] + (b[0] - a[0]) * u
            y = a[1] + (b[1] - a[1]) * u
            n = max(1e-6, math.hypot(b[0] - a[0], b[1] - a[1]))
            return x, y, kind, ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
    return PARK[0], PARK[1], "park", (0.0, 0.0)


def contour_pixels(c):
    """Every kerf pixel of a contour in cutting order, with its cut time (linear within a segment)."""
    out = []
    pts, times = c["pts"], c["times"]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        n = seg_len(a, b)
        sx = (b[0] > a[0]) - (b[0] < a[0])
        sy = (b[1] > a[1]) - (b[1] < a[1])
        for k in range(n + (1 if i == len(pts) - 2 else 0)):
            out.append(((a[0] + sx * k, a[1] + sy * k), times[i] + (times[i + 1] - times[i]) * k / n, i))
    return out


def closed_at(index):
    """Frame from which contour `index` is fully cut."""
    return math.ceil(CONTOURS[index]["times"][-1])


if __name__ == "__main__":
    total = sum(seg_len(a, b) for c in CONTOURS for a, b in zip(c["pts"], c["pts"][1:]))
    for c in CONTOURS:
        print(f'{c["kind"]:8s} pierce {c["pierce"]:5.1f}  cut {c["times"][0]:5.1f} -> {c["times"][-1]:5.1f}  '
              f'len {sum(seg_len(a, b) for a, b in zip(c["pts"], c["pts"][1:]))}')
    print(f"kerf {total} px, first pierce {CONTOURS[0]['pierce']:.1f}, last cut ends at frame {CUT_END:.1f}, "
          f"drop {DROP}, parked again at {MOVES[-1][2]:.1f}")
    for k in range(0, 72, 4):
        x, y, s, _ = head_at(k)
        print(k, round(x, 1), round(y, 1), s)
