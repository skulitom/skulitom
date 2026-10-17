"""The bench treatment shared by the buttons (concept B, picked at milestone 1): each subject stands on a short ledge of
the hero's workbench wood. The ledge fades out at both ends, its lip is moonlit at the left end only, the subject's own
light pools on its top, and the subject casts a contact shadow on it.

At this size dither reads as noise, so the ledge is solid bands: the top (J), the front (I) and the underside (H). Its
ends fade by value in two-pixel runs (one step darker over the last four pixels, two steps over the last two) rather
than through a dither, which left lone pixels at 2 CSS px.
"""

from pb import rect, line, dither, shade, disc_rows


def end_fade(x0, x1, y, h):
    """Darken both ends of a band of rows y..y+h-1 in two-pixel runs."""
    return [shade(x0, y, 4, h, -1), shade(x0, y, 2, h, -1), shade(x1 - 3, y, 4, h, -1), shade(x1 - 1, y, 2, h, -1)]


def ledge_layer(x0, x1, y, extra=(), name="ledge", lip=7):
    """A three-row ledge from x0 to x1 (inclusive) with its top surface at row y. `extra` operations (the subject's
    light pool and contact shadow) are drawn on the ledge inside its layer; then both ends fade."""
    w = x1 - x0 + 1
    ops = [rect(x0, y, w, 1, "J"), rect(x0, y + 1, w, 1, "I"), rect(x0, y + 2, w, 1, "H"),
           # A grain line along the front, broken once (the board's own grain).
           line(x0 + 5, y + 1, x0 + w // 2 - 4, y + 1, "J"),
           # The moon is upper left: the lip catches it at the left end and loses it a few pixels on.
           line(x0 + 4, y, x0 + 4 + lip - 1, y, "K"), dither(x0 + 4 + lip, y, 3, 1, "K", 0.5, over=["J"])]
    ops += list(extra)
    ops += end_fade(x0, x1, y, 3)
    return {"name": name, "ops": ops}


def pool(cx, y, bands, over=("J", "K")):
    """The subject's own light on the ledge top: bands = [(colour, half-width, density), ...], widest first; a density
    of 1 is a solid band, 0.5 its Bayer feather."""
    ops = []
    for c, hw, d in bands:
        ops.append(dither(round(cx - hw), y, round(2 * hw) + 1, 1, c, d, over=list(over)))
    return ops


def contact_shadow(cx, y, hw):
    """The subject's contact shadow on the ledge top."""
    return [shade(round(cx - hw), y, round(2 * hw) + 1, 1, -1)]


def halo(cx, cy, r, colour="3", density=0.25, over=("2",), rx=None):
    """A faint light pool on the wall behind a subject that gives off light."""
    return disc_rows(cx, cy, r, colour, density, over=list(over), rx=rx)
