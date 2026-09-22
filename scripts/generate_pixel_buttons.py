"""Original pixel-art links; each small scene moves briefly every 24 seconds."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'links' / 'v3'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'static').mkdir(exist_ok=True)

# Artwork uses a 20 x 20 grid with crisp pixel edges. Motion occupies 2.4 seconds
# per cycle; positive delays separate the six apps by four seconds.
CSS = '''
.move{animation-duration:24s;animation-iteration-count:infinite;animation-delay:var(--delay,0s);animation-timing-function:steps(8,end)}
.globe{animation-name:globe}.ship{animation-name:ship;animation-timing-function:steps(1,end)}.train{animation-name:train}
.key-a{animation-name:key-a}.key-b{animation-name:key-b}.key-c{animation-name:key-c}
.stroke{animation-name:stroke;stroke-dasharray:20;stroke-dashoffset:0}
.reels{animation-name:reels;transform-origin:10px 10px}
.terminal-line{animation-name:terminal-line}.terminal-cursor{animation-name:terminal-cursor}
@keyframes globe{0%{transform:translateX(0)}10%{transform:translateX(-16px)}10.001%,100%{transform:translateX(0)}}
@keyframes ship{0%,10%,100%{transform:translate(0,0)}2%{transform:translate(1px,-1px)}4%{transform:translate(2px,0)}6%{transform:translate(1px,1px)}8%{transform:translate(0,1px)}}
@keyframes train{0%,100%{transform:translateX(0)}10%{transform:translateX(18px)}10.001%{transform:translateX(0)}}
@keyframes key-a{0%,1%,4%,100%{opacity:0}1.001%,3.999%{opacity:1}}
@keyframes key-b{0%,4%,7%,100%{opacity:0}4.001%,6.999%{opacity:1}}
@keyframes key-c{0%,7%,10%,100%{opacity:0}7.001%,9.999%{opacity:1}}
@keyframes stroke{0%,10%,100%{stroke-dashoffset:0}0.001%{stroke-dashoffset:20}9.999%{stroke-dashoffset:0}}
@keyframes reels{0%{transform:rotate(0)}10%,100%{transform:rotate(360deg)}}
@keyframes terminal-line{0%,10%,100%{transform:scaleX(1)}0.001%{transform:scaleX(0)}8%{transform:scaleX(1)}}
@keyframes terminal-cursor{0%,2%,4%,6%,8%,10%,100%{opacity:1}1%,3%,5%,7%,9%{opacity:0}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
'''

GLOBE = '''
<defs><clipPath id="planet"><path d="M7 1h6v2h4v3h2v8h-2v3h-4v2H7v-2H3v-3H1V6h2V3h4z"/></clipPath></defs>
<path d="M7 1h6v2h4v3h2v8h-2v3h-4v2H7v-2H3v-3H1V6h2V3h4z" fill="#82d9e8"/>
<g clip-path="url(#planet)"><path d="M2 3h16v14H2z" fill="#23505f"/>
<g class="move globe" fill="#a7f3d0"><path d="M3 4h5v2h3v3H7v3H4V8H2V6h1M12 12h4v4h-2v2h-2zM19 4h5v2h3v3h-4v3h-3V8h-2V6h1M28 12h4v4h-2v2h-2z"/></g>
<path d="M1 10h18M10 1v18" fill="none" stroke="#82d9e8" stroke-opacity=".3"/>
<path d="M15 3h4v14h-4z" fill="#121826" fill-opacity=".35"/></g>
<path d="M0 1h2v2H0M18 18h2v2h-2" fill="#eef1f8"/>
'''
TRADE = '''
<path d="M0 16h7v1H0m10-1h10v1H10M3 19h8v1H3m12-1h5v1h-5" fill="#568d98"/>
<g class="move ship"><path d="M1 11h17v2h-2v2H5v-1H3v-1H1z" fill="#a7f3d0"/>
<path d="M4 7h4v3H4m5-3h4v3H9m0-7h4v3H9" fill="#75b99c"/>
<path d="M14 5h3v6h-4V8h1z" fill="#eef1f8"/><path d="M15 6h1v1h-1" fill="#121826"/>
<path d="M5 8h2v1H5m5-1h2v1h-2m0-5h2v1h-2" fill="#d2ffe8"/></g>
<path d="M1 2h5v1H1m4-2h1v4H5m1-3h1v1H6" fill="#a7f3d0"/>
'''
ROUTE = '''
<defs><clipPath id="rail"><rect width="20" height="20"/></clipPath></defs>
<path d="M2 2h3v6H2m5-8h3v8H7m5-5h5v5h-5M0 17h20v1H0" fill="#665785"/>
<path d="M3 4h1v1H3m5-2h1v1H8m5 1h1v1h-1m2-1h1v1h-1M2 18h1v2H2m5-2h1v2H7m5-2h1v2h-1m5-2h1v2h-1" fill="#c5b2ff"/>
<g clip-path="url(#rail)"><g class="move train">
<path d="M0 10h14v1h2v4H0zM-18 10h14v1h2v4h-16z" fill="#c5b2ff"/>
<path d="M1 11h3v2H1m4-2h3v2H5m4-2h3v2H9m4-2h2v2h-2M-17 11h3v2h-3m4-2h3v2h-3m4-2h3v2h-3m4-2h2v2h-2" fill="#302742"/>
<path d="M2 15h2v1H2m8-1h2v1h-2M-16 15h2v1h-2m8-1h2v1h-2" fill="#eef1f8"/></g></g>
'''
KEYBOARD = '''
<path d="M2 4h16v1h2v12h-2v1H2v-1H0V5h2z" fill="#f3cc88"/>
<path d="M1 6h18v10H1z" fill="#403729"/>
<path d="M3 7h2v2H3m4-2h2v2H7m4-2h2v2h-2m4-2h2v2h-2M3 11h2v2H3m4-2h2v2H7m4-2h2v2h-2m4-2h2v2h-2M6 14h8v1H6" fill="#af986d"/>
<g fill="#fff1d2"><path class="move key-a" opacity="0" d="M3 7h2v2H3"/><path class="move key-b" opacity="0" d="M11 11h2v2h-2"/><path class="move key-c" opacity="0" d="M6 14h8v1H6"/></g>
<path d="M9 1h2v2H9" fill="#f3cc88"/>
'''
RADICALS = '''
<path d="M1 0h15v2h3v18H1z" fill="#633847"/><path d="M3 2h12v3h2v13H3z" fill="#251e2a"/>
<path d="M15 2v3h2" fill="none" stroke="#f3a5bc"/>
<path d="M5 8h10M10 4v12M10 8l-5 7M10 8l5 7" fill="none" stroke="#754b5c" stroke-width="2"/>
<path class="move stroke" d="M5 8h10M10 4v12M10 8l-5 7M10 8l5 7" fill="none" stroke="#f3a5bc" stroke-width="2"/>
'''
MUSIC = '''
<path d="M1 3h18v2h1v12h-1v2H1v-2H0V5h1z" fill="#a5bfff"/><path d="M2 5h16v9H2z" fill="#29354f"/><path d="M4 15h12v3H4z" fill="#526d9d"/>
<path d="M4 7h4v6H4v-1H3V8h1m8-1h4v1h1v4h-1v1h-4z" fill="#d8e4ff"/>
<g transform="translate(-4 0)"><path class="move reels" d="M9 8h2v1H9m0 2h2v1H9" fill="#29354f"/></g>
<g transform="translate(4 0)"><path class="move reels" d="M9 8h2v1H9m0 2h2v1H9" fill="#29354f"/></g>
<path d="M8 9h4v2H8M6 16h8v1H6" fill="#121826"/>
'''

BUTTONS = [
    ('world-language-map', 'World Language Map', 'Languages around the world', '#82d9e8', GLOBE),
    ('export-atlas', 'Export Atlas', 'Explore goods, services & trade', '#a7f3d0', TRADE),
    ('london-in-minutes', 'London in minutes', 'Compare journey times', '#c5b2ff', ROUTE),
    ('chinese-touch-typing', 'Chinese Touch Typing', 'Practise Mandarin pinyin', '#f3cc88', KEYBOARD),
    ('chinese-radicals', 'Chinese Radicals', 'Learn radicals & characters', '#f3a5bc', RADICALS),
    ('keepsake', 'Keepsake', 'Back up your song lists', '#a5bfff', MUSIC),
]

for index, (slug, title, description, accent, scene) in enumerate(BUTTONS):
    lines = {
        'world-language-map': ['World Language', 'Map'],
        'export-atlas': ['Export Atlas'],
        'london-in-minutes': ['London', 'in minutes'],
        'chinese-touch-typing': ['Chinese', 'Touch Typing'],
        'chinese-radicals': ['Chinese', 'Radicals'],
        'keepsake': ['Keepsake'],
    }[slug]
    for variant, width in [('', 136), ('-narrow', 112)]:
        text = ''.join(f'<text x="{width / 2}" y="{(56 + i * 15) if len(lines) == 2 else 64}" text-anchor="middle">{escape(line)}</text>' for i, line in enumerate(lines))
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="84" viewBox="0 0 {width} 84" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}. Original animated pixel art; reduced-motion preferences disable animation.</desc>
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#171426"/><stop offset="1" stop-color="#0e1423"/></linearGradient></defs>
<style>{CSS}</style>
<rect x="1" y="2" width="{width - 2}" height="78" rx="12" fill="url(#bg)" stroke="#353047"/>
<path d="M{width / 2 - 10} 2h20" stroke="{accent}" stroke-opacity=".65"/>
<g transform="translate({width / 2 - 14} 10) scale(1.4)" style="--delay:{index * 4}s" shape-rendering="crispEdges">{scene}</g>
<g font-family="'Segoe UI',Arial,sans-serif" font-size="13" font-weight="600" fill="#f5f1ff">{text}</g>
</svg>
'''
        (OUT / f'{slug}{variant}.svg').write_text(svg, encoding='utf-8')
        (OUT / 'static' / f'{slug}{variant}.svg').write_text(svg.replace(f'<style>{CSS}</style>', ''), encoding='utf-8')

PORTFOLIO = f'''<svg xmlns="http://www.w3.org/2000/svg" width="280" height="64" viewBox="0 0 280 64" role="img" aria-labelledby="title desc">
<title id="title">Explore my portfolio</title><desc id="desc">Projects, demos and writing samples by Artem Skulimovskiy. Original pixel terminal; reduced-motion preferences disable animation.</desc>
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#171426"/><stop offset="1" stop-color="#0e1423"/></linearGradient></defs>
<style>{CSS}</style>
<rect x="1" y="2" width="278" height="58" rx="12" fill="url(#bg)" stroke="#71efd2" stroke-opacity=".5"/>
<g shape-rendering="crispEdges">
<g transform="translate(12 17) scale(1.4)">
<path d="M1 0h18v1h1v16H0V1h1zM8 16h4v3H8M5 19h10v1H5" fill="#71efd2"/>
<path d="M2 2h16v12H2z" fill="#0b1d18"/>
<path d="M3 4h1v1h1v1H4v1H3V6h1V5H3z" fill="#71efd2"/>
<g transform="translate(7 5)"><path class="move terminal-line" d="M0 0h8v1H0M0 3h6v1H0" fill="#71efd2"/></g>
<path class="move terminal-cursor" d="M3 11h3v1H3" fill="#71efd2"/><path d="M16 15h2v1h-2" fill="#123e2d"/>
</g>
</g>
<path d="M249 30h14m-5-5 5 5-5 5" fill="none" stroke="#71efd2" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
<g font-family="'Segoe UI',Arial,sans-serif"><text x="51" y="28" font-size="16" font-weight="600" fill="#f5f1ff">Explore my portfolio</text>
<text x="51" y="46" font-size="11" fill="#b6aecb">Projects, demos &amp; writing samples</text></g>
</svg>
'''
(OUT / 'portfolio.svg').write_text(PORTFOLIO, encoding='utf-8')
(OUT / 'static' / 'portfolio.svg').write_text(PORTFOLIO.replace(f'<style>{CSS}</style>', ''), encoding='utf-8')
print(f'Generated {len(BUTTONS)} pixel web-app buttons and the portfolio link in {OUT}.')
