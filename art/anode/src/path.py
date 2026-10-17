"""The agent cursor's path through one 72-frame loop, shared by the mist emitters and the cursor sprite.

Beat (70 ms frames):
  0-14   rest at P0 on its screen, reading, while the last wake curls closed
  15     anticipation: 1 px against the coming move
  16-33  swoop P0 -> P1 down in front of its desk (half an ellipse): the wake parts the mist and curls
  34-35  arrive with a 1 px overshoot, settle
  36     click at P1, on the button (the event): a ripple, a puff that pushes the mist out, the gamepad's button lights
  44     the screen's status pip turns bright (the test passed); it dims again at frame 6
  51     anticipation
  52-69  swoop P1 -> P0 back over the top of the monitor; 70-71 overshoot and settle
Every move is half an orbit of period 36, so it takes 18 frames. The soak rides the orbit at constant speed; the
sprite eases in and out along the same orbit (half a sine ease: at most about 1.4 frames of lead or lag).
"""

import math

FRAMES = 72
HALF = 18           # frames per swoop (half an orbit of period 36)
PERIOD = 2 * HALF
ARC1 = (16, 34)     # start, end (exclusive)
CLICK = 36
PASS = 44
ARC2 = (52, 70)
EASE = 0.5          # 0 = constant speed; 1 = a full sine ease


class Arc:
    """Half an axis-aligned ellipse from a to b (antipodal points), taking HALF frames from frame `start`.

    With a and b level, the ellipse's height `ry` is free; otherwise it follows from rx."""

    def __init__(self, a, b, rx, start, sweep=1, ry=None):
        self.a, self.b, self.start, self.sweep = a, b, start, sweep
        self.c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        dx, dy = a[0] - self.c[0], a[1] - self.c[1]
        if abs(dx) > rx:
            raise ValueError("rx must reach half the horizontal span")
        cos0 = dx / rx
        if dy:
            sin0 = math.copysign(math.sqrt(1 - cos0 * cos0), dy)
            self.ry = dy / sin0
        else:
            sin0 = 0.0
            self.ry = ry
        self.rx = rx
        self.theta0 = math.degrees(math.atan2(sin0, cos0))
        # orbit: theta(t) = 360 t / period + phase; we want theta(start) = theta0.
        self.period = sweep * PERIOD
        self.phase = (self.theta0 - 360 * start / self.period) % 360

    def pos(self, t):
        th = math.radians(360 * t / self.period + self.phase)
        return self.c[0] + self.rx * math.cos(th), self.c[1] + self.ry * math.sin(th)

    def orbit(self):
        return {"radius": [round(self.rx, 3), round(self.ry, 3)], "period": self.period, "phase": round(self.phase, 3)}

    def tangent(self, t):
        x0, y0 = self.pos(t - 0.5)
        x1, y1 = self.pos(t + 0.5)
        return x1 - x0, y1 - y0


class Path:
    def __init__(self, p0, p1, rx, ry=None, sweep=1):
        self.p0, self.p1 = p0, p1
        self.arc1 = Arc(p0, p1, rx, ARC1[0], sweep, ry)
        self.arc2 = Arc(p1, p0, rx, ARC2[0], sweep, ry)

    @staticmethod
    def eased(t, start):
        p = (t - start) / HALF
        return start + HALF * (p - EASE * math.sin(2 * math.pi * p) / (2 * math.pi))

    def cursor(self, t):
        """The cursor's pixel position (its hotspot) at frame t."""
        t %= FRAMES
        if ARC1[0] <= t < ARC1[1]:
            x, y = self.arc1.pos(self.eased(t, ARC1[0]))
        elif ARC2[0] <= t < ARC2[1]:
            x, y = self.arc2.pos(self.eased(t, ARC2[0]))
        elif ARC1[1] <= t < ARC2[0]:
            x, y = self.p1
            if t == ARC1[1]:            # overshoot: it arrives moving up
                y -= 1
            elif t == ARC2[0] - 1:      # anticipation before rising
                y += 1
        else:
            x, y = self.p0
            if t == ARC2[1]:            # overshoot: it arrives moving down
                y += 1
            elif t == ARC1[0] - 1:      # anticipation before dropping
                y -= 1
        return round(x), round(y)

    def moving(self, t):
        t %= FRAMES
        return ARC1[0] <= t < ARC1[1] or ARC2[0] <= t < ARC2[1]


# ---------------------------------------------------------------- hover burst (site)
BURST_FRAMES = 48
LOBE_A = (4, 16)    # left lobe, clockwise
LOBE_B = (16, 28)   # right lobe, anticlockwise
DASH_IN = (2, 4)
DASH_OUT = (28, 32)


class Lobe:
    """A full ellipse in 12 frames from frame `start`, beginning and ending at the figure-eight's crossing point."""

    def __init__(self, centre, rx, ry, start, period, theta0):
        self.c, self.rx, self.ry, self.period = centre, rx, ry, period
        self.phase = (theta0 - 360 * start / period) % 360

    def pos(self, t):
        th = math.radians(360 * t / self.period + self.phase)
        return self.c[0] + self.rx * math.cos(th), self.c[1] + self.ry * math.sin(th)

    def orbit(self):
        return {"radius": [self.rx, self.ry], "period": self.period, "phase": round(self.phase, 3)}


class Burst:
    """The hover burst: from rest at P0 the cursor dashes to the crossing point X, zips a fast figure-eight (left lobe
    clockwise, right lobe anticlockwise, always heading down through X), dashes home and rests while the mist
    settles."""

    def __init__(self, p0, x, rx, ry):
        self.p0, self.x = p0, x
        self.a = Lobe((x[0] - rx, x[1]), rx, ry, LOBE_A[0], 12, 0)
        self.b = Lobe((x[0] + rx, x[1]), rx, ry, LOBE_B[0], -12, 180)

    def cursor(self, t):
        t %= BURST_FRAMES

        def lerp(a, b, u):
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        if LOBE_A[0] <= t < LOBE_A[1]:
            x, y = self.a.pos(t)
        elif LOBE_B[0] <= t < LOBE_B[1]:
            x, y = self.b.pos(t)
        elif DASH_IN[0] <= t < DASH_IN[1]:
            x, y = lerp(self.p0, self.x, (t - DASH_IN[0] + 1) / (DASH_IN[1] - DASH_IN[0] + 1))
        elif DASH_OUT[0] <= t < DASH_OUT[1]:
            x, y = lerp(self.x, self.p0, (t - DASH_OUT[0] + 1) / (DASH_OUT[1] - DASH_OUT[0]))
        else:
            x, y = self.p0
        return round(x), round(y)
