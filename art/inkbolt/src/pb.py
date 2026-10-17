"""Small helpers that write Pixelbolt recipe operations. They only lay out drawing instructions; every pixel is
produced by Pixelbolt when the recipe renders."""

import json
import os
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PB = os.environ.get("PIXELBOLT", "")  # path to pixelbolt.js; art/build.sh sets it


def rect(x, y, w, h, c, filled=True):
    o = {"op": "rect", "x": x, "y": y, "w": w, "h": h, "color": c}
    if not filled:
        o["filled"] = False
    return o


def ell(x, y, w, h, c, filled=True):
    o = {"op": "ellipse", "x": x, "y": y, "w": w, "h": h, "color": c}
    if not filled:
        o["filled"] = False
    return o


def line(x, y, x2, y2, c):
    return {"op": "line", "x": x, "y": y, "x2": x2, "y2": y2, "color": c}


def px(x, y, c):
    return {"op": "pixel", "x": x, "y": y, "color": c}


def grid(x, y, rows):
    return {"op": "grid", "x": x, "y": y, "rows": rows}


def dither(x, y, w, h, c, density, **kw):
    o = {"op": "dither", "x": x, "y": y, "w": w, "h": h, "color": c, "density": density}
    o.update(kw)
    return o


def shade(x, y, w, h, steps, **kw):
    o = {"op": "shade", "x": x, "y": y, "w": w, "h": h, "steps": steps}
    o.update(kw)
    return o


def at(ops, dx, dy):
    """Shift ops (compiled fluid grids, stamps) by dx, dy."""
    out = []
    for o in ops:
        o = dict(o)
        if "x" in o:
            o["x"] += dx
        if "y" in o:
            o["y"] += dy
        if "x2" in o:
            o["x2"] += dx
        if "y2" in o:
            o["y2"] += dy
        out.append(o)
    return out


def fluid_frames(path, effect):
    recipe = json.loads(Path(path).read_text(encoding="utf-8"))
    return [f.get("ops", []) for f in recipe["frames"] if f["name"].rsplit("-", 1)[0] == effect]


def bezier(p0, p1, p2, p3, n=400):
    """Sample a cubic Bezier and return a clean one-pixel 8-connected path: rounded samples, duplicates removed, then
    the corner pixel of every L-step dropped so the line never doubles (a pixel artist's 'pixel-perfect' stroke)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        x = a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0]
        y = a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]
        q = (int(math.floor(x + 0.5)), int(math.floor(y + 0.5)))
        if not pts or pts[-1] != q:
            # bridge gaps so the path stays 8-connected
            while pts and max(abs(q[0] - pts[-1][0]), abs(q[1] - pts[-1][1])) > 1:
                lx, ly = pts[-1]
                pts.append((lx + (q[0] > lx) - (q[0] < lx), ly + (q[1] > ly) - (q[1] < ly)))
            pts.append(q)
    out = []
    for q in pts:
        if len(out) >= 2:
            a, b = out[-2], out[-1]
            if abs(q[0] - a[0]) == 1 and abs(q[1] - a[1]) == 1 and (b[0] == a[0] or b[1] == a[1]):
                out.pop()  # b is the corner of an L between a and q
        out.append(q)
    return out


def path_len(p0, p1, p2, p3):
    return len(bezier(p0, p1, p2, p3))


def write_json(path, data, compact=True):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, separators=(",", ":")) if compact else json.dumps(data, indent=1)
    Path(path).write_text(text + "\n", encoding="utf-8", newline="\n")


def inside_poly(pts, x, y):
    """Even-odd test for the pixel centre (x + 0.5, y + 0.5)."""
    cx, cy, inside = x + 0.5, y + 0.5, False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > cy) != (y2 > cy) and cx < x1 + (cy - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def poly_pixels(pts):
    """The pixels whose centres lie inside an authored outline (a silhouette, drawn like a pixel artist's fill)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [(x, y) for y in range(int(min(ys)) - 1, int(max(ys)) + 2) for x in range(int(min(xs)) - 1, int(max(xs)) + 2)
            if inside_poly(pts, x, y)]
