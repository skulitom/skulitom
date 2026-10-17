"""Where everything sits on the 192x100 card, shared by the fluid sources and the recipe generator."""

from variant import BURST

W, H = 192, 100
FRAMES, MS = (48 if BURST else 72), 70
STILL = 18 if BURST else 40   # reduced-motion still: the head cuts the L-bar's edge in its warm pool, the bolt is cut,
                       # and two billowing plumes curl up past the beam into the extractor

SHEET_Y = 34           # sheets span rows 34..77, their plywood edge rows 78..79
CUT_X = 112            # the sheet under the gantry
PITCH = 88             # one shuttle step: the finished sheet waits at CUT_X - PITCH
FIN_X = CUT_X - PITCH

# The shuttle: sheet offset (px moved left) on each frame from its start; eases in, eases out 4-3 px, overshoots a
# pixel and settles back on its last frame, which matches the loop's first frame.
SHUTTLE_START = 38 if BURST else 60
SHUTTLE = [0, 4, 13, 28, 46, 64, 78, 86, 89, 88]

SMOKE_X, SMOKE_Y, SMOKE_W, SMOKE_H = 92, 0, 96, 88   # fluid canvas over the cell and the back wall

RAIL_L, RAIL_R = 92, 174      # left edges of the two Y rails (6 px wide)
BED_X0, BED_X1 = 100, 171     # slat bed inside the cell
DUCT = (134, 6, 40, 12)       # extractor grille frame on the back panel (x, y, w, h)


def card(p):
    """Sheet-local point on the cutting sheet -> card coordinates."""
    return CUT_X + p[0], SHEET_Y + p[1]


def smoke(p):
    """Sheet-local point on the cutting sheet -> smoke canvas coordinates."""
    x, y = card(p)
    return x - SMOKE_X, y - SMOKE_Y
