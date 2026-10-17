"""Write out/fluids/crucible.poses.json: the crucible pot as one pose-compiler part, turned about its pivot boss.

Pixelbolt's pose compiler rotates the part (RotSprite-style, with doubled-corner cleanup) into editable symbols
pot-r<degrees>; gen.py stamps those symbols. The bail and chain don't turn, so gen.py draws them itself.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent

# A fireclay crucible, the foundry kind: tall, tapered, flat-based, terracotta (wood ramp J-M, lit from the upper
# left, dark J on its shadow side and base), a lipped mouth with a pouring beak on the right, a steel band where the
# hanger grips its pivot. The mouth shows the molten surface (g f e d). 18 x 20; the pivot is the band's centre.
POT = [
    ".JLMMMMMMMMMMMLJL.",
    "JMggggggggggggfLML",
    "JLffgggggggggfeLJ.",
    ".KMMLLLLLLLLLLKJ..",
    "..KMLLLLLLLLLLKJ..",
    "..KMLLLLLLLLLKKJ..",
    "..BEDDDDDDDDDCCA..",
    "..ACDDDDDDDDCCBA..",
    "..KMLLLLLLLLLKKJ..",
    "..KMLLLLLLLLLKKJ..",
    "..KMLLLLLLLLKKKJ..",
    "...KMLLLLLLLKKJ...",
    "...KMLLLLLLLKKJ...",
    "...KMLLLLLLKKKJ...",
    "...KMLLLLLLKKKJ...",
    "...KMLLLLLKKKJJ...",
    "....KMLLLLKKKJ....",
    "....KLLLLKKKJJ....",
    "....JKKKKKKJJJ....",
    "....JJJJJJJJJJ....",
]
# The same pot with its mouth's inside marked by two keys found nowhere else on it (H, I: the dark inner wall),
# for the tilted poses: the recipe recolours the part of that inside below a level line to molten, so the metal
# surface stays level while the pot turns.
_DRY = str.maketrans({"g": "I", "f": "I", "e": "H", "d": "H"})
POT_DRY = [r.translate(_DRY) for r in POT]
ANCHOR = [8, 6]
SPOUT = [17, 1]
POINTS = {"spout": SPOUT, "rimL": [1, 0], "baseL": [4, 19], "baseR": [13, 19]}

# Angles used by the card (whole degrees clockwise): rest, lean back, two in-betweens, pour, overshoot.
ANGLES = [0, -8, 20, 34, 45, -4]


def pose_name(a):
    return f"tilt{a}" if a >= 0 else f"tiltm{-a}"


def main():
    src = {
        "format": "pixelforge-poses", "version": 1, "name": "crucible", "width": 48, "height": 48,
        "palette": {"$ref": "../../../palette.json"},
        "parts": {"pot": {"rows": POT, "anchor": ANCHOR, "points": POINTS},
                  "pot-dry": {"rows": POT_DRY, "anchor": ANCHOR, "points": POINTS}},
        "poses": [{"name": pose_name(a), "duration": 70, "origin": [24, 24],
                   "parts": [{"name": "pot", "part": "pot-dry" if a >= 20 else "pot", "rotate": a}],
                   "markers": [{"name": k, "part": "pot", "point": k} for k in POINTS]} for a in ANGLES],
    }
    (HERE.parent / "out" / "fluids" / "crucible.poses.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
