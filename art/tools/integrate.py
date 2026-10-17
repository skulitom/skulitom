"""Build the README's v4 art from the pieces in art/: each piece's wrapper specs (art/<piece>/*.wrap.json, layer paths
relative to art/<piece>/out/) plus the profile's vector text, chips and panel frame. Writes animated and still SVGs to
../assets/v4/ (next to art/). Run art/build.sh first (it builds every piece's out/, then runs this).

Usage: python art/tools/integrate.py [name ...]     (names as in PIECES, e.g. hero anode; default: all)

Chip widths come from Pillow's text measurements of the Windows fonts below. Where those fonts are missing (Linux,
macOS, CI) the widths recorded in MEASURED are used instead, so the SVGs come out the same, and the text-fit checks are
skipped.
"""

import json
import sys
from html import escape
from pathlib import Path

from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from wrap import build  # noqa: E402

ART = Path(__file__).resolve().parents[1]
OUT = ART.parent / "assets" / "v4"
FRAME = "#353047"
INK, MUTED, MINT, VIOLET, PINK, GOLD = "#f5f1ff", "#b6aecb", "#71efd2", "#b496ff", "#ff7fc8", "#ecc76a"

FONTS = {
    ("sans", 400): "C:/Windows/Fonts/segoeui.ttf",
    ("sans", 500): "C:/Windows/Fonts/seguisb.ttf",
    ("sans", 700): "C:/Windows/Fonts/segoeuib.ttf",
    ("mono", 600): "C:/Windows/Fonts/consolab.ttf",
    ("mono", 500): "C:/Windows/Fonts/consola.ttf",
}
# ImageFont.truetype(font, 200).getlength(text) with the fonts above (Pillow 12, basic layout), for machines without
# them. A new chip label or headline needs its entry added from a machine that has the fonts (this script prints it).
MEASURED = {
    ("sans", 500, "Python"): 643.0,
    ("sans", 500, "AI agents"): 853.0,
    ("sans", 500, "MCP tools"): 928.984375,
    ("sans", 700, "Artem Skulimovskiy"): 1882.078125,
}
_fonts = {}
_skipped = []


def have_font(family, weight):
    return Path(FONTS[(family, weight)]).is_file()


def length200(text, family, weight):
    key = (family, weight, text)
    if have_font(family, weight):
        path = FONTS[(family, weight)]
        if path not in _fonts:
            _fonts[path] = ImageFont.truetype(path, 200)
        n = _fonts[path].getlength(text)
        if MEASURED.get(key, n) != n:
            print(f"note: {key} measures {n!r} here, MEASURED records {MEASURED[key]!r}; update MEASURED")
        elif key not in MEASURED:
            print(f"note: add {key!r}: {n!r} to MEASURED for machines without the Windows fonts")
        return n
    if key in MEASURED:
        return MEASURED[key]
    raise SystemExit(f"{FONTS[(family, weight)]} is missing and MEASURED has no width for {key!r}; run this once on a "
                     "machine with the font and add the printed entry")


def width(text, size, family="sans", weight=400, spacing=0.0):
    return length200(text, family, weight) / 200 * size + spacing * max(len(text) - 1, 0)


def fits(right, limit, what, fonts):
    """The text-safe box check; it needs real font metrics, so it's skipped where the fonts are missing."""
    if not all(have_font(*f) for f in fonts):
        _skipped.append(what)
        return
    assert right <= limit, f"{what} runs to x {right:.1f}, past the text-safe box ({limit})"


def text(x, y, value, size, fill, weight=400, mono=False, spacing=0.0, anchor="start"):
    cls = ' class="mono"' if mono else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}"{cls}{ls} '
            f'text-anchor="{anchor}">{escape(value)}</text>')


def chips(x, y, items, size=5.4, h=12, pad=7, gap=4):
    out = []
    for label, colour in items:
        w = round(width(label, size, "sans", 500) + 2 * pad, 1)
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{colour}" fill-opacity=".1" '
                   f'stroke="{colour}" stroke-opacity=".45" stroke-width=".5"/>')
        out.append(text(round(x + w / 2, 2), round(y + h / 2 + size * 0.36, 2), label, size, colour, 500, anchor="middle"))
        x = round(x + w + gap, 2)
    return "".join(out), x


def hero_overlay():
    x = 14
    parts = [
        text(x, 22, "SKULITOM  /  AGENTIC ENGINEER", 5.2, MINT, 600, mono=True, spacing=0.75),
        text(x - 0.5, 54, "Artem Skulimovskiy", 16.5, INK, 700),
        text(x, 72, "Building tools for agents.", 10.5, MUTED),
        text(x, 86, "Desktop, graphics & video.", 10.5, MUTED),
    ]
    row, end = chips(x, 97, [("Python", MINT), ("AI agents", VIOLET), ("MCP tools", PINK)])
    parts.append(row)
    right = max(end, x + width("Artem Skulimovskiy", 16.5, "sans", 700))
    fits(right, 178, "hero text", [("sans", 500), ("sans", 700)])
    return "".join(parts)


def mobile_overlay():
    x = 8
    parts = [
        text(x, 15, "SKULITOM / AGENTIC ENGINEER", 4.6, MINT, 600, mono=True, spacing=0.5),
        text(x - 0.4, 34, "Artem Skulimovskiy", 13.2, INK, 700),
        text(x, 48, "Building tools for agents.", 8.6, MUTED),
        text(x, 59.5, "Desktop, graphics & video.", 8.6, MUTED),
    ]
    row, end = chips(x, 65, [("Python", MINT), ("AI agents", VIOLET), ("MCP tools", PINK)], size=4.6, h=10, pad=5, gap=3)
    parts.append(row)
    fits(max(end, x + width("Artem Skulimovskiy", 13.2, "sans", 700)), 150, "phone hero text", [("sans", 500), ("sans", 700)])
    return "".join(parts)


def footer_overlay():
    return (text(12, 11.5, "ARTEM SKULIMOVSKIY", 4.6, MUTED, 500, mono=True, spacing=0.6) +
            text(12, 21.5, "Agent tools · Creative workflows · Systems", 7, INK, 500))


def eyebrow(label, colour):
    return text(8, 11.5, label, 4.8, colour, 600, mono=True, spacing=0.55)


PIECES = [
    # name (assets/v4/<name>.svg and <name>-still.svg), art/ folder, animated spec, still spec, overlay
    ("hero", "hero", "hero.wrap.json", "hero-still.wrap.json", hero_overlay),
    ("hero-mobile", "hero", "hero-mobile.wrap.json", "hero-mobile-still.wrap.json", mobile_overlay),
    ("footer", "hero", "footer.wrap.json", "footer-still.wrap.json", footer_overlay),
    ("anode", "anode", "anode.wrap.json", "anode-still.wrap.json", lambda: eyebrow("DESKTOPS FOR AGENTS", MINT)),
    ("inkbolt", "inkbolt", "inkbolt.wrap.json", "inkbolt-still.wrap.json", lambda: eyebrow("GRAPHICS FOR AGENTS", VIOLET)),
    ("cutbolt", "cutbolt", "cutbolt.wrap.json", "cutbolt-still.wrap.json", lambda: eyebrow("VIDEO FOR AGENTS", PINK)),
    ("pixelbolt", "pixelbolt", "pixelbolt-card.wrap.json", "pixelbolt-card-static.wrap.json",
     lambda: eyebrow("PIXEL ART FOR AGENTS", GOLD)),
    # art/nestbolt builds too (nestbolt.wrap.json, nestbolt-still.wrap.json) but isn't in the README yet: add a row
    # here with its eyebrow when it is. New pieces (the button set) get their rows here the same way.
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    unknown = only - {p[0] for p in PIECES}
    if unknown:
        raise SystemExit(f"unknown piece(s): {', '.join(sorted(unknown))}")
    for name, folder, anim, still, overlay in PIECES:
        if only and name not in only:
            continue
        base = ART / folder / "out"
        if not base.is_dir():
            raise SystemExit(f"{base} is missing: run art/build.sh (or art/{folder}/build.sh) first")
        for spec_name, suffix in ((anim, ""), (still, "-still")):
            spec = json.loads((ART / folder / spec_name).read_text(encoding="utf-8"))
            spec["overlay"] = overlay()
            spec["frame"] = FRAME
            target = OUT / f"{name}{suffix}.svg"
            target.write_text(build(spec, base), encoding="utf-8", newline="\n")
            print(f"{target.relative_to(ART.parent).as_posix()} {target.stat().st_size:,} bytes")
    if _skipped:
        print(f"skipped text-fit checks (Windows fonts not found): {', '.join(dict.fromkeys(_skipped))}")


if __name__ == "__main__":
    main()
