"""Small helpers that write Pixelbolt drawing operations. They only lay out ops; Pixelbolt draws every pixel."""

import json
import os
import subprocess
from pathlib import Path

PB = os.environ.get("PIXELBOLT", "")  # path to pixelbolt.js; art/build.sh sets it
PIECE = Path(__file__).resolve().parents[1]
RAMPS_MASTER = [
    ["0", "1", "2", "3", "4", "5", "6", "7"],
    ["s", "t", "u", "v", "w", "x"],
    ["A", "B", "C", "D", "E", "F", "G"],
    ["H", "I", "J", "K", "L", "M"],
    ["N", "O", "P", "Q", "R"],
    ["a", "b", "c", "d", "e", "f", "g"],
    ["h", "i", "j", "k", "l", "m", "n"],
    ["o", "p", "q", "r", "y", "z"],
    ["S", "T", "U", "V", "X", "Y"],
    ["8", "9", "W", "Z", "@", "#", "$"],
    ["%", "&", "+", "="],
]


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


def grid(x, y, rows, **kw):
    o = {"op": "grid", "x": x, "y": y, "rows": rows}
    o.update(kw)
    return o


def dither(x, y, w, h, c, density, **kw):
    o = {"op": "dither", "x": x, "y": y, "w": w, "h": h, "color": c, "density": density}
    o.update(kw)
    return o


def shade(x, y, w, h, steps, **kw):
    o = {"op": "shade", "x": x, "y": y, "w": w, "h": h, "steps": steps}
    o.update(kw)
    return o


def text(x, y, s, c, **kw):
    o = {"op": "text", "x": x, "y": y, "text": s, "color": c}
    o.update(kw)
    return o


def at(ops, dx, dy):
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


def write_json(path, data, compact=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    s = json.dumps(data, separators=(",", ":")) if compact else json.dumps(data, indent=1)
    path.write_text(s + "\n", encoding="utf-8", newline="\n")


def pb(*args, check=True):
    r = subprocess.run(["node", PB, *map(str, args)], capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"pixelbolt {' '.join(map(str, args))} failed:\n{r.stderr[:2000]}\n{r.stdout[:2000]}")
    return r


def fluid_frames(recipe_path, effect):
    recipe = json.loads(Path(recipe_path).read_text(encoding="utf-8"))
    return [f.get("ops", []) for f in recipe["frames"] if f["name"].rsplit("-", 1)[0] == effect]
