"""Card layout in card pixels (192x100). Shared by the fluid writer and the recipe generator.

Two planes. Near: your desk, lower left and cropped by the frame, a dark silhouette with a cool moon rim, lit blue by
your own screen. Far: the agent's desk at about 60% of that scale, higher in the frame, seen through an arched doorway
in the back wall, wrapped in pale drifting mist.
"""

import path

W, H = 192, 100
FRAMES, MS = 72, 70

# The doorway in the front wall: a flat-lintelled opening x 108-163 from y 12 down to the threshold at y 80. We see
# its right jamb's inner face (the reveal, x 160-163), lit mint by the agent's screen; the left one is turned away.
DOOR_X0, DOOR_X1 = 108, 164          # opening, x1 exclusive
DOOR_TOP = 12
REVEAL = 4
THRESHOLD = 80
TRIM = 3

# Mist canvases (x, y, w, h): the fog bank on the back floor, spilling out onto your floor; the wisps under the arch.
FOG = (90, 52, 82, 48)
WISPS = (90, 8, 82, 34)

# The agent's desk (far plane).
AM = (117, 37, 34, 22)               # monitor bezel x, y, w, h
AS = (119, 39, 30, 17)               # its screen
AD_TOP = 62                          # desk top
AD_X0, AD_X1 = 111, 157
BACK_FLOOR = 72                      # back room's floor line

# Your desk (near plane).
YM = (-2, 32, 66, 44)                # monitor bezel (cropped by the left edge)
YS = (1, 35, 60, 37)                 # screen
YD_TOP = 84                          # desk top
YD_X1 = 90                           # desk runs from the left edge to x 89
TOWER = (79, 68, 12, 32)             # the PC tower standing in front of your desk's end (the one machine)

# The agent cursor's loop round its desk: rest at P0 on the log window, swoop down in front of the desk and up to P1
# on the button it clicks; later swoop back over the top of the monitor. Both swoops are halves of one ellipse,
# centre (132, 49), 11 x 26 px, travelled anticlockwise: low through the fog, high through the wisps.
P0 = (121, 49)
P1 = (143, 49)
PATH = path.Path(P0, P1, rx=11, ry=26, sweep=-1)

# The hover burst's figure-eight: two 10 x 8 px lobes crossing at X, low in front of the desk, inside the fog.
BURST = path.Burst(P0, (133, 62), 10, 8)
