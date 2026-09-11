"""Render self-contained toolkit badges from local icon data; no network needed."""

from html import escape
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "toolkit"
OUTPUT = SOURCE / "v1"
OUTPUT.mkdir(parents=True, exist_ok=True)
ICONS = json.loads((SOURCE / "source-icons.json").read_text(encoding="utf-8"))["icons"]

BADGES = [
    ("codex", "Codex", "#8befd8", None),
    ("claude-code", "Claude Code", "#efa58b", "claude"),
    ("pytorch", "PyTorch", "#ff997b", "pytorch"),
    ("numpy", "NumPy", "#81b6f7", "numpy"),
    ("python", "Python", "#f6d477", "python"),
    ("typescript", "TypeScript", "#84bbff", "typescript"),
    ("react", "React", "#70dcf5", "react"),
    ("bash", "Bash", "#a8d887", "gnubash"),
    ("sql", "SQL", "#b8a1ff", None),
    ("postgresql", "PostgreSQL", "#91bdf1", "postgresql"),
    ("docker", "Docker", "#72c5ff", "docker"),
    ("linux", "Linux", "#eacb7b", "linux"),
]

for slug, label, color, icon_slug in BADGES:
    if icon_slug:
        paths = ''.join(f'<path d="{escape(path, quote=True)}"/>' for path in ICONS[icon_slug]["paths"])
        icon = f'<svg x="11" y="10" width="20" height="20" viewBox="{ICONS[icon_slug]["viewBox"]}" fill="{color}">{paths}</svg>'
    elif slug == "codex":
        icon = f'<g fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="11" y="11" width="20" height="18" rx="4"/><path d="M15 16 L19 20 L15 24 M22 24 H27"/></g>'
    else:
        icon = f'<g fill="none" stroke="{color}" stroke-width="1.6"><ellipse cx="21" cy="13" rx="8" ry="3"/><path d="M13 13 V27 C13 31 29 31 29 27 V13 M13 20 C13 24 29 24 29 20"/></g>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="132" height="40" viewBox="0 0 132 40" role="img" aria-label="{escape(label)}">
<title>{escape(label)}</title>
<defs><clipPath id="pill"><rect x="1" y="4" width="130" height="32" rx="10"/></clipPath></defs>
<g clip-path="url(#pill)">
<rect x="1" y="4" width="130" height="32" fill="#111721"/>
<rect x="40" y="4" width="91" height="32" fill="{color}" fill-opacity=".18"/>
<path d="M40 5 V35" stroke="{color}" stroke-opacity=".24"/>
</g>
<rect x="1" y="4" width="130" height="32" rx="10" fill="none" stroke="{color}" stroke-opacity=".48"/>
{icon}
<text x="85" y="24" text-anchor="middle" font-family="'Segoe UI',Arial,sans-serif" font-size="10.5" font-weight="700" letter-spacing=".75" fill="#f1f4fa">{escape(label.upper())}</text>
</svg>
'''
    (OUTPUT / f"{slug}.svg").write_text(svg, encoding="utf-8")

print(f"Generated {len(BADGES)} toolkit badges in {OUTPUT}")
