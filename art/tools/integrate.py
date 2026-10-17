"""Build the README's v4 art from the pieces in art/: each piece's wrapper specs (art/<piece>/*.wrap.json, layer paths
relative to art/<piece>/out/) plus the profile's vector text, chips, labels and panel frame. Writes animated and still
SVGs to ../assets/v4/ (next to art/), the link buttons to ../assets/v4/links/. Run art/build.sh first (it builds every
piece's out/, then runs this).

Usage: python art/tools/integrate.py [name ...]   (rows of PIECES, e.g. hero links/keepsake, or art/ folders such as
                                                   buttons; default: all)

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
    ("sans", 600): "C:/Windows/Fonts/seguisb.ttf",    # Segoe UI Semibold, as for 500: the buttons' labels
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


# ---------------------------------------------------------------- link buttons (assets/v4/links/)
# Matched to the v3 buttons (assets/links/v3/*.svg). v3 is in CSS px and the art is 2 CSS px per art px, so every
# coordinate and size below is v3's halved: tile labels Segoe UI 600 at 13 px (6.5), #f5f1ff, centred on the tile; one
# line at y 64 (32), two lines at 56 and 71 (28 and 35.5); the portfolio's 16 px 600 title at (51, 28) and 11 px 400
# subtitle at (51, 46) in #b6aecb, and its arrow; 24 s cycles with v3's --delay stagger (delay_ms); frame #353047
# (the portfolio's mint at 50%), radius 6 (v3's rx 12) from the wrap specs.
# Where v3's positions would put text on the new art, the text moves to the area the art keeps plain (set these to 0
# and 25.5 for v3's positions exactly):
TWO_LINE_DROP = 3   # v3's two-line labels reach up to row 23, over the ledges (rows 20-25); the tiles keep rows 26-41 plain
PORTFOLIO_X = 33    # v3's x 51 (25.5) runs into the terminal (x 2-30); the portfolio art keeps x 33-139 plain
LABEL_TOP = 26      # first plain row under the tiles' ledges
PORTFOLIO_FRAME = "#71efd280"
LINK_DELAYS = {"world-language-map": 0, "export-atlas": 4000, "london-in-minutes": 8000, "chinese-touch-typing": 12000,
               "chinese-radicals": 16000, "keepsake": 20000, "portfolio": 0}
LINK_LABELS = {"world-language-map": ["World Language", "Map"], "export-atlas": ["Export Atlas"],
               "london-in-minutes": ["London", "in minutes"], "chinese-touch-typing": ["Chinese", "Touch Typing"],
               "chinese-radicals": ["Chinese", "Radicals"], "keepsake": ["Keepsake"]}


def check_text(value, size, weight, x, lo, hi, what, centred=False):
    """Text-fit check for a label no geometry depends on (it is anchored, not measured into the layout): it must lie
    within x lo..hi. Measured where the font exists, else skipped."""
    path = FONTS[("sans", weight)]
    if not Path(path).is_file():
        _skipped.append(what)
        return
    if path not in _fonts:
        _fonts[path] = ImageFont.truetype(path, 200)
    w = _fonts[path].getlength(value) / 200 * size
    left = x - w / 2 if centred else x
    assert lo <= left and left + w <= hi, f"{what}: {value!r} spans x {left:.1f}-{left + w:.1f}, outside {lo}-{hi}"


def tile_overlay(name, w):
    lines = LINK_LABELS[name]
    ys = [32] if len(lines) == 1 else [28 + TWO_LINE_DROP, 35.5 + TWO_LINE_DROP]
    if ys[0] - 0.72 * 6.5 < LABEL_TOP:
        print(f"note: {name}'s label starts above row {LABEL_TOP}, on the art")
    parts = []
    for line, y in zip(lines, ys):
        check_text(line, 6.5, 600, w / 2, 2, w - 2, f"{name} label ({w} wide)", centred=True)
        parts.append(text(w / 2, y, line, 6.5, INK, 600, anchor="middle"))
    return "".join(parts)


def portfolio_overlay():
    x = PORTFOLIO_X
    if x < 33:
        print("note: the portfolio's text starts left of x 33, on the art")
    check_text("Explore my portfolio", 8, 600, x, 0, 122, "portfolio title")          # clear of the arrow (124.5)
    check_text("Projects, demos & writing samples", 5.5, 400, x, 0, 122, "portfolio subtitle")
    return (text(x, 14, "Explore my portfolio", 8, INK, 600) +
            text(x, 23, "Projects, demos & writing samples", 5.5, MUTED) +
            '<path d="M124.5 15h7m-2.5-2.5 2.5 2.5-2.5 2.5" fill="none" stroke="#71efd2" stroke-width=".75" '
            'stroke-linecap="round" stroke-linejoin="round"/>')


def link_rows():
    rows = [("links/portfolio", "buttons/portfolio", "portfolio.wrap.json", "portfolio-still.wrap.json",
             portfolio_overlay, {"frame": PORTFOLIO_FRAME, "delay_ms": LINK_DELAYS["portfolio"]})]
    for name in LINK_LABELS:
        for variant, w in (("", 68), ("-narrow", 56)):
            rows.append((f"links/{name}{variant}", f"buttons/{name}", f"{name}{variant}.wrap.json",
                         f"{name}{variant}-still.wrap.json", lambda n=name, w=w: tile_overlay(n, w),
                         {"delay_ms": LINK_DELAYS[name]}))
    return rows


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
    # here with its eyebrow when it is.
] + link_rows()   # links/<button>[-narrow][-still].svg; an optional 6th item overrides spec fields (frame, delay_ms)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])   # row names (hero, links/keepsake-narrow) or art/ folders (buttons, buttons/keepsake)
    known = {key for p in PIECES for key in (p[0], p[1], p[1].split("/")[0])}
    unknown = only - known
    if unknown:
        raise SystemExit(f"unknown piece(s): {', '.join(sorted(unknown))}")
    for name, folder, anim, still, overlay, *extra in PIECES:
        if only and not only & {name, folder, folder.split("/")[0]}:
            continue
        base = ART / folder / "out"
        if not base.is_dir():
            raise SystemExit(f"{base} is missing: run art/build.sh (or art/{folder.split('/')[0]}/build.sh) first")
        for spec_name, suffix in ((anim, ""), (still, "-still")):
            spec = json.loads((ART / folder / spec_name).read_text(encoding="utf-8"))
            spec["overlay"] = overlay()
            spec["frame"] = FRAME
            spec.update(*extra)
            target = OUT / f"{name}{suffix}.svg"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(build(spec, base), encoding="utf-8", newline="\n")
            print(f"{target.relative_to(ART.parent).as_posix()} {target.stat().st_size:,} bytes")
    if _skipped:
        print(f"skipped text-fit checks (Windows fonts not found): {', '.join(dict.fromkeys(_skipped))}")


if __name__ == "__main__":
    main()
