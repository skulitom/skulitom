"""The nest on each 56x44 sheet, and the laser's route through it.

Kerf lines use only horizontal, vertical and 45-degree segments, so a line cut part-way (start point to any point
along it) draws exactly the pixels of the full line up to there: Pixelbolt's Bresenham has no ties on those slopes.

Coordinates are sheet-local (0..55, 0..43). Parts are packed against the sheet's top, right and bottom edges, so
the left of the sheet stays a clean remnant; the remnant cut along the nest's left side is cut last and frees
every part at once (the event).

`python src/nest.py` prints an ASCII preview (design aid only; Pixelbolt draws every pixel of the art).
"""

SW, SH = 56, 44

# Contours in cutting order. Each is (kind, points): "hole" contours are closed and cut first (their slugs fall
# out), "line" contours are common-line cuts between parts, "remnant" is last.
def ring(x, y):
    """A 4x4 round hole kerf (2x2 slug) with its top-left corner at (x, y), cut clockwise from the top."""
    return [(x + 1, y), (x + 2, y), (x + 3, y + 1), (x + 3, y + 2), (x + 2, y + 3), (x + 1, y + 3), (x, y + 2),
            (x, y + 1), (x + 1, y)]


def bolt(x, y):
    """The lightning-bolt part's kerf, cut clockwise from its top-left; the slug inside is the part."""
    pts = [(5, -1), (10, -1), (10, 0), (8, 2), (11, 2), (11, 3), (4, 10), (3, 11), (2, 10), (2, 7), (5, 4), (2, 4),
           (2, 3), (5, 0), (5, -1)]
    return [(x + a, y + b) for a, b in pts]


ROUTE = [
    # the inner contour first: the bolt nested in the cover plate's window (part-in-part)
    ("part", bolt(38, 3)),
    # common lines, ordered so the gantry's moves between them stay short: flange | cover and on along the
    # ramp's top edge, the rest of that edge back to the remnant line, then the gusset and the L-bar's edge
    ("line", [(32, 0), (32, 18), (34, 20), (55, 20)]),
    ("line", [(32, 18), (26, 12), (20, 12)]),
    ("line", [(46, 20), (55, 29), (42, 29), (38, 33), (17, 33)]),
    # the remnant cut, last: it closes every part
    ("remnant", [(17, 43), (17, 30), (20, 27), (20, 0)]),
]


def trace(x, y, x2, y2):
    """Bresenham as in Pixelbolt's craft.js traceLine (design preview only)."""
    pts = []
    dx, sx = abs(x2 - x), (1 if x < x2 else -1)
    dy, sy = -abs(y2 - y), (1 if y < y2 else -1)
    err = dx + dy
    while True:
        pts.append((x, y))
        if x == x2 and y == y2:
            return pts
        e = 2 * err
        if e >= dy:
            err += dy
            x += sx
        if e <= dx:
            err += dx
            y += sy


def check_slopes():
    for kind, pts in ROUTE:
        for (x, y), (x2, y2) in zip(pts, pts[1:]):
            dx, dy = abs(x2 - x), abs(y2 - y)
            assert dx == 0 or dy == 0 or dx == dy, (kind, (x, y), (x2, y2))


def kerf_pixels():
    out = set()
    for _, pts in ROUTE:
        for a, b in zip(pts, pts[1:]):
            out.update(trace(*a, *b))
    return out


def regions(kerf):
    """Label 4-connected regions of the sheet outside the kerf (design preview only)."""
    label, n = {}, 0
    for y in range(SH):
        for x in range(SW):
            if (x, y) in kerf or (x, y) in label:
                continue
            stack = [(x, y)]
            while stack:
                p = stack.pop()
                if p in label or p in kerf or not (0 <= p[0] < SW and 0 <= p[1] < SH):
                    continue
                label[p] = n
                stack += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
            n += 1
    return label, n


def preview():
    check_slopes()
    kerf = kerf_pixels()
    label, n = regions(kerf)
    chars = ".abcdefghijklmnopqrstuvwxyz0123456789"
    sizes = {}
    for p, k in label.items():
        sizes[k] = sizes.get(k, 0) + 1
    rows = []
    for y in range(SH):
        rows.append("".join("#" if (x, y) in kerf else chars[label[(x, y)] % len(chars)] for x in range(SW)))
    print("\n".join(rows))
    print(n, "regions;", "sizes", sorted(sizes.items(), key=lambda kv: kv[0]))
    length = sum(max(abs(b[0] - a[0]), abs(b[1] - a[1])) for _, pts in ROUTE for a, b in zip(pts, pts[1:]))
    print("route length", length, "kerf pixels", len(kerf))


if __name__ == "__main__":
    preview()
