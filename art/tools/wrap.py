"""Wrap Pixelbolt sprite sheets in a self-contained animated SVG for a GitHub README.

The SVG embeds each sheet as an exact-palette PNG data URI and steps through the atlas frames with CSS keyframes,
drawn with nearest-neighbour scaling, so the art stays crisp at any width. Reduced motion shows a chosen still frame.

Usage: python wrap.py spec.json
spec = {
  "out": "piece.svg", "width": 192, "height": 100, "scale": 2,
  "title": "...", "desc": "...",
  "background": "#171426",           # optional fill behind the art
  "radius": 0,                       # optional rounded clip, in art pixels
  "smooth_below": 0,                 # optional: rendered CSS width below which scaling turns smooth
  "delay_ms": 0,                     # optional start delay for every animated layer (staggered buttons)
  "debug": false,                    # draws a dot: green = pixelated rule active, red = smooth rule active
  "layers": [
    {"image": "bg.png", "x": 0, "y": 0},
    {"sheet": "out/name.png", "atlas": "out/name.atlas.json", "animation": "name", "x": 0, "y": 0, "still": 0}
  ]
}
"""

import base64
import io
import json
import sys
from html import escape
from pathlib import Path

from PIL import Image


def png_data_uri(path):
    """Encode a PNG losslessly, as an indexed PNG when it has at most 256 RGBA colours."""
    im = Image.open(path).convert("RGBA")
    colours = im.getcolors(maxcolors=256)
    buf = io.BytesIO()
    if colours is not None:
        table = [c for _, c in colours]
        index = {c: i for i, c in enumerate(table)}
        p = Image.frombytes("P", im.size, bytes(index[c] for c in im.getdata()))
        p.putpalette([v for c in table for v in c[:3]] + [0] * (3 * (256 - len(table))))
        p.info["transparency"] = bytes([c[3] for c in table])
        p.save(buf, "PNG", optimize=True, transparency=bytes([c[3] for c in table]))
        # Pillow can silently fall back; verify the round trip is exact.
        back = Image.open(io.BytesIO(buf.getvalue())).convert("RGBA")
        if back.tobytes() != im.tobytes():
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
    else:
        im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii"), im.size


def frames_of(atlas_path, animation):
    atlas = json.loads(Path(atlas_path).read_text(encoding="utf-8"))
    frames = atlas["frames"]
    names = None
    tags = atlas.get("meta", {}).get("frameTags") or []
    for tag in tags:
        if tag.get("name") == animation:
            names = [n for n in frames][tag["from"]: tag["to"] + 1]
    if names is None:
        names = [n for n in frames if n.rsplit("-", 1)[0] == animation] or list(frames)
        names.sort(key=lambda n: int(n.rsplit("-", 1)[1]) if n.rsplit("-", 1)[1].isdigit() else 0)
    return [(frames[n]["frame"], frames[n].get("duration", 100)) for n in names]


def keyframes(name, frames):
    total = sum(d for _, d in frames)
    lines, t = [], 0
    for rect, d in frames:
        pct = 100 * t / total
        lines.append(f"{pct:.4f}%{{transform:translate({-rect['x']}px,{-rect['y']}px)}}")
        t += d
    return f"@keyframes {name}{{{''.join(lines)}}}", total


def build(spec, base):
    w, h, scale = spec["width"], spec["height"], spec.get("scale", 2)
    css = [
        "image{image-rendering:pixelated;image-rendering:crisp-edges;image-rendering:pixelated}",
        ".a{animation-timing-function:step-end;animation-iteration-count:infinite}",
    ]
    defs, body = [], []
    if spec.get("background"):
        body.append(f'<rect width="{w}" height="{h}" fill="{spec["background"]}"/>')
    for i, layer in enumerate(spec["layers"]):
        x, y = layer.get("x", 0), layer.get("y", 0)
        if "image" in layer:
            uri, (iw, ih) = png_data_uri(base / layer["image"])
            body.append(f'<image x="{x}" y="{y}" width="{iw}" height="{ih}" href="{uri}" image-rendering="optimizeSpeed"/>')
            continue
        frames = frames_of(base / layer["atlas"], layer["animation"])
        if spec.get("static"):
            # A still needs one frame, so embed just that frame instead of the whole sheet.
            r = frames[layer.get("still", 0)][0]
            crop = Image.open(base / layer["sheet"]).convert("RGBA").crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]))
            buf = io.BytesIO()
            crop.save(buf, "PNG")
            uri, _ = png_data_uri(buf)
            body.append(f'<image x="{x}" y="{y}" width="{r["w"]}" height="{r["h"]}" href="{uri}" image-rendering="optimizeSpeed"/>')
            continue
        uri, (sw, sh) = png_data_uri(base / layer["sheet"])
        fw, fh = frames[0][0]["w"], frames[0][0]["h"]
        kf, total = keyframes(f"k{i}", frames)
        still = frames[layer.get("still", 0)][0]
        if spec.get("static"):
            # Motionless variant for <picture media="(prefers-reduced-motion: reduce)">: browsers don't pass the
            # viewer's reduced-motion setting into SVG images, so the README swaps files instead.
            css.append(f".l{i}{{transform:translate({-still['x']}px,{-still['y']}px)}}")
        else:
            css.append(kf)
            delay = f"animation-delay:{spec['delay_ms']}ms;" if spec.get("delay_ms") else ""
            css.append(f".l{i}{{animation-name:k{i};animation-duration:{total}ms;{delay}transform:translate({-frames[0][0]['x']}px,{-frames[0][0]['y']}px)}}")
            css.append(f"@media (prefers-reduced-motion:reduce){{.l{i}{{animation:none;transform:translate({-still['x']}px,{-still['y']}px)}}}}")
        defs.append(f'<clipPath id="c{i}"><rect x="{x}" y="{y}" width="{fw}" height="{fh}"/></clipPath>')
        body.append(
            f'<g clip-path="url(#c{i})"><g transform="translate({x} {y})">'
            f'<image class="a l{i}" width="{sw}" height="{sh}" href="{uri}" image-rendering="optimizeSpeed"/></g></g>'
        )
    if spec.get("smooth_below"):
        css.append(f"@media (max-width:{spec['smooth_below'] - 0.02}px){{image{{image-rendering:auto}}}}")
    if spec.get("debug"):
        css.append(".dbg{fill:#3c3}")
        if spec.get("smooth_below"):
            css.append(f"@media (max-width:{spec['smooth_below'] - 0.02}px){{.dbg{{fill:#e33}}}}")
        body.append('<rect class="dbg" x="1" y="1" width="4" height="4"/>')
    radius = spec.get("radius", 0)
    clip_all = ""
    if radius:
        defs.append(f'<clipPath id="r"><rect width="{w}" height="{h}" rx="{radius}"/></clipPath>')
        clip_all = ' clip-path="url(#r)"'
    # Integration overlays: vector text and chips drawn over the art (raw SVG in art-pixel units), and a 1 px frame
    # matching the profile's other panels.
    overlay = spec.get("overlay", "")
    if overlay:
        css.append("text{font-family:'Segoe UI',Arial,sans-serif}.mono{font-family:Consolas,'Liberation Mono',monospace}"
                   ".ov{shape-rendering:geometricPrecision;text-rendering:geometricPrecision}")
        overlay = f'<g class="ov">{overlay}</g>'
    frame = ""
    if spec.get("frame"):
        frame = (f'<rect x="0.25" y="0.25" width="{w - 0.5}" height="{h - 0.5}" rx="{radius}" fill="none" '
                 f'stroke="{spec["frame"]}" stroke-width="1" vector-effect="non-scaling-stroke" '
                 f'shape-rendering="geometricPrecision"/>')
    title, desc = escape(spec.get("title", "")), escape(spec.get("desc", ""))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * scale}" height="{h * scale}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d" shape-rendering="crispEdges">\n'
        f'<title id="t">{title}</title><desc id="d">{desc}</desc>\n'
        f'<style>{"".join(css)}</style>\n<defs>{"".join(defs)}</defs>\n<g{clip_all}>{"".join(body)}{overlay}</g>{frame}\n</svg>\n'
    )


def main():
    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out = spec_path.parent / spec["out"]
    out.write_text(build(spec, spec_path.parent), encoding="utf-8", newline="\n")
    print(f"{out} {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
