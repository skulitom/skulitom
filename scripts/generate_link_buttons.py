"""Generate compact, self-contained SVG links for the GitHub profile."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'links' / 'v1'
OUT.mkdir(parents=True, exist_ok=True)

GLOBE = '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6.5c4 2 10 2 14 0M5 17.5c4-2 10-2 14 0"/>'
TRADE = '<path d="M4 20V12h4v8M10 20V8h4v12M16 20V4h4v16M3 5h7M7 2l3 3-3 3"/>'
ROUTE = '<circle cx="5" cy="5" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="M7.5 5H16a4 4 0 0 1 0 8H8a3 3 0 0 0 0 6h8.5"/>'
KEYBOARD = '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M6 9h1m4 0h1m4 0h1M6 12h1m4 0h1m4 0h1M7 16h10"/>'
RADICALS = '<path d="M5 5h14M12 2v18M3 10h18M12 10c-2 4-5 7-9 9M12 10c2 4 5 7 9 9"/>'
MUSIC = '<path d="M9 17V5l11-2v12M9 9l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2.5"/><ellipse cx="17" cy="16" rx="3" ry="2.5"/>'

buttons = [
    ('world-language-map', 'World Language Map', 'Languages around the world', '#82d9e8', GLOBE),
    ('export-atlas', 'Export Atlas', 'Explore goods, services & trade', '#a7f3d0', TRADE),
    ('london-in-minutes', 'London in minutes', 'Compare journey times', '#c5b2ff', ROUTE),
    ('chinese-touch-typing', 'Chinese Touch Typing', 'Practise Mandarin pinyin', '#f3cc88', KEYBOARD),
    ('chinese-radicals', 'Chinese Radicals', 'Learn radicals & characters', '#f3a5bc', RADICALS),
    ('keepsake', 'Keepsake', 'Back up your song lists', '#a5bfff', MUSIC),
]

for slug, title, description, accent, icon in buttons:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="266" height="80" viewBox="0 0 266 80" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(description)}. Open the web app.</desc>
<rect x="1" y="3" width="264" height="70" rx="13" fill="#121826" stroke="{accent}" stroke-opacity=".48"/>
<rect x="13" y="19" width="38" height="38" rx="11" fill="{accent}" fill-opacity=".11"/>
<g transform="translate(20 26)" fill="none" stroke="{accent}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
<g font-family="'Segoe UI',Arial,sans-serif">
<text x="62" y="34" font-size="15" font-weight="600" fill="#eef1f8">{escape(title)}</text>
<text x="62" y="54" font-size="11.5" fill="#b4bed0">{escape(description)}</text>
</g>
<path d="M242 21h8v8m-8 0 8-8" fill="none" stroke="{accent}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''
    (OUT / f'{slug}.svg').write_text(svg, encoding='utf-8')

portfolio = '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="88" viewBox="0 0 400 88" role="img" aria-labelledby="title desc">
<title id="title">Explore my portfolio</title>
<desc id="desc">Projects, demos and writing samples by Artem Skulimovskiy. Open skulitom.github.io.</desc>
<rect x="1" y="4" width="398" height="76" rx="16" fill="#a7f3d0" stroke="#caffdf"/>
<rect x="17" y="22" width="40" height="40" rx="12" fill="#102e25" fill-opacity=".10"/>
<g transform="translate(25 30)" fill="none" stroke="#123e2d" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
<rect x="1" y="2" width="22" height="19" rx="3"/><path d="M1 8h22M5 5h.1M8 5h.1M8 12l-3 3 3 3M16 12l3 3-3 3"/>
</g>
<g font-family="'Segoe UI',Arial,sans-serif" fill="#102e25">
<text x="72" y="37" font-size="23" font-weight="700">Explore my portfolio</text>
<text x="72" y="59" font-size="13.5">Projects, demos &amp; writing samples</text>
</g>
<circle cx="370" cy="42" r="16" fill="#102e25" fill-opacity=".10"/>
<path d="M363 42h14m-6-6 6 6-6 6" fill="none" stroke="#123e2d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''
(OUT / 'portfolio.svg').write_text(portfolio, encoding='utf-8')
print(f'Generated {len(buttons)} web-app buttons and the portfolio link in {OUT}.')
