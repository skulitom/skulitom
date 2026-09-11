"""Build the profile's original, self-contained animated SVG illustrations."""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "v2"
ASSETS.mkdir(parents=True, exist_ok=True)

INK = "#f5f1ff"
MUTED = "#b6aecb"
PINK = "#ff7fc8"
MINT = "#71efd2"
GOLD = "#ffcd77"
VIOLET = "#b496ff"
SKY = "#88c8ff"
CORAL = "#ffa88a"

CSS = """
text{font-family:'Segoe UI',Arial,sans-serif}
.mono{font-family:Consolas,'Liberation Mono',monospace}
.float{animation:float 5s ease-in-out infinite}
.float2{animation:float 6s ease-in-out -2s infinite}
.orbit{animation:orbit 20s linear infinite;transform-box:fill-box;transform-origin:center}
.spark{animation:spark 3s ease-in-out infinite}
.dash{animation:dash 9s linear infinite}
.blink{animation:blink 4.8s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.cursor{animation:cursor 1.5s step-end infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
@keyframes orbit{to{transform:rotate(360deg)}}
@keyframes spark{0%,100%{opacity:.35}50%{opacity:1}}
@keyframes dash{to{stroke-dashoffset:-100}}
@keyframes blink{0%,43%,47%,100%{transform:scaleY(1)}45%{transform:scaleY(.15)}}
@keyframes cursor{50%{opacity:0}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def text(x, y, value, size=16, color=INK, weight=400, extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" {extra}>{escape(value)}</text>'


def svg(name, width, height, body, title):
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title>
<desc id="desc">Original animated illustration. Motion is disabled when reduced motion is preferred.</desc>
<defs>
  <linearGradient id="bg" x2="1" y2="1"><stop stop-color="#171426"/><stop offset="1" stop-color="#0e1423"/></linearGradient>
  <linearGradient id="rainbow"><stop stop-color="{MINT}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
  <radialGradient id="halo"><stop stop-color="#7150ba" stop-opacity=".27"/><stop offset="1" stop-color="#7150ba" stop-opacity="0"/></radialGradient>
</defs>
<style>{CSS}</style>
{body}
</svg>
'''
    (ASSETS / name).write_text(content, encoding="utf-8")


def panel(w, h):
    return f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="url(#bg)" stroke="#353047"/>'


def star(x, y, color=MINT, scale=1, delay=0):
    return f'<g transform="translate({x} {y}) scale({scale})"><path class="spark" style="animation-delay:{delay}s" d="M0 -7 Q0 0 7 0 Q0 0 0 7 Q0 0 -7 0 Q0 0 0 -7" fill="{color}"/></g>'


def systems_diagram(x, y, scale=1):
    parts = [f'<g transform="translate({x} {y}) scale({scale})">', '<circle r="185" fill="url(#halo)"/>']
    for gy in range(-120, 121, 30):
        for gx in range(-150, 151, 30):
            parts.append(f'<circle cx="{gx}" cy="{gy}" r="1" fill="#5b526f" opacity=".5"/>')
    for nx,ny,color in [(-116,-84,MINT),(116,-84,VIOLET),(-116,91,VIOLET),(116,91,MINT)]:
        parts.append(f'<path d="M0 0 H{nx} V{ny}" fill="none" stroke="{color}" stroke-opacity=".45" stroke-width="1.5" stroke-dasharray="4 6" class="dash"/>')
        parts.append(f'<rect x="{nx-29}" y="{ny-24}" width="58" height="48" rx="10" fill="#1c2033" stroke="{color}" stroke-opacity=".75"/>')
        for offset in [-8,0,8]:
            parts.append(f'<path d="M{nx-14} {ny+offset} H{nx+14}" stroke="{color}" stroke-width="2" stroke-linecap="round" opacity=".8"/>')
    parts += [f'<rect x="-58" y="-48" width="116" height="96" rx="17" fill="#1c2135" stroke="{VIOLET}" stroke-width="1.5"/>', text(0,10,"{ }",38,MINT,500,'class="mono" text-anchor="middle"')]
    parts += [text(0,147,"DISTRIBUTED SYSTEMS",11,MUTED,500,'class="mono" text-anchor="middle" letter-spacing="2"'), '</g>']
    return ''.join(parts)


def pill(x,y,w,label,color):
    label_svg = text(x+w/2,y+20,label,13,color,500,extra='text-anchor="middle"')
    return f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="15" fill="{color}" fill-opacity=".09" stroke="{color}" stroke-opacity=".38"/>{label_svg}'


body = panel(1000,390)
body += '<path d="M32 1 H968" stroke="url(#rainbow)" stroke-width="2"/>'
body += text(48,50,"SKULITOM  /  SOFTWARE ENGINEER",13,MINT,600,'class="mono" letter-spacing="1.8"')
body += text(48,140,"Artem Skulimovskiy",48,INK,700)
body += text(50,192,"Backend & infrastructure.",27,MUTED,400)
body += text(50,228,"Distributed systems & AI.",27,MUTED,400)
body += pill(48,266,133,"Python",MINT)+pill(190,266,101,"AI agents",VIOLET)+pill(300,266,149,"Data engineering",PINK)
body += text(50,348,"SOFTWARE ENGINEER",12,MUTED,500,'class="mono" letter-spacing="1.6"')
body += '<circle cx="227" cy="344" r="2" fill="#6b627f"/>'
body += text(243,348,"LONDON, UK",12,MUTED,500,'class="mono" letter-spacing="1.6"')
body += systems_diagram(770,193)
svg("hello.svg",1000,390,body,"Artem Skulimovskiy — backend, infrastructure, and AI")

body = panel(520,600)+'<path d="M32 1 H488" stroke="url(#rainbow)" stroke-width="2"/>'
body += text(30,44,"SKULITOM / SOFTWARE ENGINEER",12,MINT,600,'class="mono" letter-spacing="1"')
body += text(28,105,"Artem Skulimovskiy",38,INK,700)
body += text(30,149,"Backend & infrastructure.",23,MUTED)
body += text(30,180,"Distributed systems & AI.",23,MUTED)
body += pill(30,209,115,"Python",MINT)+pill(154,209,111,"AI agents",VIOLET)+pill(274,209,175,"Data engineering",PINK)
body += systems_diagram(264,396,.85)
body += text(260,568,"SOFTWARE ENGINEER · LONDON, UK",12,MUTED,500,'class="mono" text-anchor="middle" letter-spacing="1.1"')
svg("hello-mobile.svg",520,600,body,"Artem Skulimovskiy — software engineer in London")


def card(name, label, title, lines, color, art, title_size=30):
    body = panel(480,250)
    body += f'<path d="M22 1 H458" stroke="{color}" stroke-width="2"/>'
    body += text(26,37,label,12,color,600,'class="mono" letter-spacing="1.5"')
    body += art
    body += text(26,143,title,title_size,INK,650)
    body += text(27,178,lines[0],16,MUTED)
    body += text(27,201,lines[1],16,MUTED)
    body += text(27,232,"OPEN LIVE MAP" if name in {"london.svg", "export-atlas.svg"} else "VIEW PROJECT",11,color,600,'class="mono" letter-spacing="1.2"')
    body += '<path d="M433 229 L447 215 M433 215 H447 V229" fill="none" stroke="'+color+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    svg(name,480,250,body,title)


book = f'''<g transform="translate(380 74)"><g class="float2">
<path d="M-41 18 L-41 -22 Q-20 -30 0 -16 Q20 -30 41 -22 L41 18 Q20 10 0 27 Q-20 10 -41 18Z" fill="#342b48" stroke="{VIOLET}" stroke-width="2"/>
<path d="M0 -15 V26 M-30 -10 Q-17 -14 -9 -5 M-30 0 Q-17 -4 -9 5 M10 -5 Q22 -13 32 -10 M10 5 Q22 -3 32 0" fill="none" stroke="{VIOLET}" stroke-width="2"/>
</g></g>'''+star(326,50,GOLD,.7)+star(430,36,PINK,.75,-1)+star(392,30,MINT,.6,-2)
card("litharness.svg","01 / AGENT ORCHESTRATION","LitHarness",["LLM agent orchestration for serial fiction.","Planning, persistent state, and revision."],VIOLET,book)

latent = '<g transform="translate(384 72)"><g class="orbit">'
for i,c in enumerate([PINK,VIOLET,MINT]):
    latent += f'<ellipse rx="48" ry="18" transform="rotate({i*60})" fill="none" stroke="{c}" stroke-width="2"/>'
latent += f'<circle cx="48" r="5" fill="{PINK}"/></g><circle r="9" fill="{GOLD}"/><circle r="4" fill="#fff0d2"/></g>'
card("latent-space.svg","02 / GENERATIVE MODELS","Latent Space Explorer",["Interactive navigation of generative images.","Built with Flux, PyTorch, and Pygame."],PINK,latent,29)

crt = f'''<g transform="translate(382 72)"><g class="float">
<rect x="-53" y="-37" width="106" height="70" rx="12" fill="#303b3b" stroke="{MINT}" stroke-width="2"/>
<rect x="-44" y="-29" width="80" height="52" rx="9" fill="#0b1b1c"/>
<path d="M-12 34 V43 M-31 45 H16" stroke="{MINT}" stroke-width="3" stroke-linecap="round"/>
<path d="M-32 -13 L-22 -6 L-32 1" fill="none" stroke="{MINT}" stroke-width="2"/>
<path class="cursor" d="M-16 2 H-4" stroke="{MINT}" stroke-width="2"/>
<circle cx="45" cy="15" r="3" fill="{GOLD}"/>
'''
for y in range(-22,23,5):
    crt += f'<path d="M-40 {y} H32" stroke="{MINT}" opacity=".08"/>'
crt += '</g></g>'+star(318,57,PINK,.7,-1)
card("cathode.svg","03 / DESKTOP APPLICATIONS","Cathode",["A CRT virtual monitor for Windows apps.","Phosphor rendering, scanlines, and glow."],MINT,crt)

map_art = '<g transform="translate(383 69)">'
for r,c in [(45,PINK),(32,GOLD),(19,MINT)]:
    map_art += f'<path d="M{-r} 4 C{-r-8} {-r}, {-r/3} {-r}, 7 {-r} C{r} {-r+4}, {r+15} 1, {r} 20 C{r-15} {r+4}, {-r} {r}, {-r} 4Z" fill="{c}" fill-opacity=".09" stroke="{c}" stroke-opacity=".65"/>'
map_art += f'<path class="dash" d="M-53 3 Q-23 -12 -9 6 T22 11 T54 15" fill="none" stroke="#86c8ff" stroke-width="4" stroke-linecap="round" stroke-dasharray="6 4"/>'
map_art += f'<circle class="spark" cx="-5" cy="-7" r="10" fill="{MINT}" fill-opacity=".25"/><circle cx="-5" cy="-7" r="4" fill="{MINT}"/></g>'
card("london.svg","04 / DATA VISUALISATION","London in minutes",["Interactive travel-time mapping for London.","Walking, public transport, and driving."],GOLD,map_art,30)

globe = f'''<g transform="translate(382 70)">
<circle r="41" fill="{SKY}" fill-opacity=".06" stroke="{SKY}" stroke-width="1.8"/>
<ellipse rx="19" ry="41" fill="none" stroke="{SKY}" stroke-opacity=".6"/>
<ellipse rx="41" ry="15" fill="none" stroke="{SKY}" stroke-opacity=".6"/>
<path d="M-37 -18 H37 M-37 18 H37 M0 -41 V41" fill="none" stroke="{SKY}" stroke-opacity=".3"/>
<path class="dash" d="M-45 18 Q-15 -54 45 -8" fill="none" stroke="{MINT}" stroke-width="2.5" stroke-dasharray="4 5"/>
<circle cx="-36" cy="2" r="4" fill="{MINT}"/>
<circle cx="32" cy="-17" r="4" fill="{GOLD}"/>
</g>'''
card("export-atlas.svg","05 / GLOBAL TRADE","Export Atlas",["Global exports across goods and services.","Compare countries, markets, and years."],SKY,globe)

controls = f'''<g transform="translate(382 72)"><g class="float2">
<rect x="-52" y="-36" width="104" height="72" rx="11" fill="#2c2530" stroke="{CORAL}" stroke-width="1.8"/>
<path d="M-52 -18 H52" stroke="{CORAL}" stroke-opacity=".4"/>
<circle cx="-40" cy="-27" r="2" fill="{CORAL}"/><circle cx="-32" cy="-27" r="2" fill="{VIOLET}"/>
<path d="M-35 -1 H35 M-35 17 H35" stroke="{CORAL}" stroke-width="2" stroke-opacity=".45" stroke-linecap="round"/>
<circle cx="-9" cy="-1" r="5" fill="{CORAL}"/>
<circle cx="19" cy="17" r="5" fill="{VIOLET}"/>
<path d="M32 3 L44 9 L37 12 L34 19Z" fill="{MINT}" stroke="#2c2530" stroke-width="1.5"/>
</g></g>'''
card("agentui.svg","06 / DEVELOPER TOOLS","AgentUI",["Interactive controls for coding agents.","An MCP server for forms and live previews."],CORAL,controls)

for name, number, titles, lines, color, art in [
    ("litharness", "01 / AGENTS", ["LitHarness"], ["AI agents for", "serial fiction."], VIOLET, book),
    ("latent-space", "02 / MODELS", ["Latent Space", "Explorer"], ["Interactive", "generative images."], PINK, latent),
    ("cathode", "03 / DESKTOP", ["Cathode"], ["A CRT monitor", "for Windows apps."], MINT, crt),
    ("london", "04 / MAPS", ["London", "in minutes"], ["Travel-time", "visualisation."], GOLD, map_art),
    ("export-atlas", "05 / TRADE", ["Export Atlas"], ["Global trade,", "mapped by market."], SKY, globe),
    ("agentui", "06 / TOOLS", ["AgentUI"], ["Forms and previews", "for coding agents."], CORAL, controls),
]:
    body = panel(240,300)
    body += f'<path d="M22 1 H218" stroke="{color}" stroke-width="2"/>'
    body += text(18,28,number,12,color,600,'class="mono" letter-spacing="1"')
    body += '<g transform="translate(-127 24) scale(.65)">'+art+'</g>'
    for i,line in enumerate(titles):
        body += text(18,150+i*31,line,27,INK,650)
    for i,line in enumerate(lines):
        body += text(18,216+i*25,line,19,MUTED)
    body += text(18,278,"OPEN MAP" if name in {"london", "export-atlas"} else "VIEW PROJECT",12,color,600,'class="mono" letter-spacing="1"')
    body += f'<path d="M203 279 L216 266 M204 266 H216 V278" fill="none" stroke="{color}" stroke-width="2"/>'
    svg(name+"-mobile.svg",240,300,body,' '.join(titles))

body = '<path d="M10 1 H990" stroke="#353047"/>'
body += text(20,49,"ARTEM SKULIMOVSKIY",12,MUTED,500,'class="mono" letter-spacing="1.5"')
body += text(20,77,"Backend engineering · Distributed systems · AI",18,INK,500)
body += '<path d="M637 54 Q727 14 800 54 T978 54" stroke="url(#rainbow)" stroke-width="2" fill="none" stroke-dasharray="5 8" class="dash"/>'
body += star(780,47,PINK,1.3)+star(927,61,MINT,1,-1)+star(691,38,GOLD,.8,-2)
svg("footer.svg",1000,100,body,"Artem Skulimovskiy — backend engineering, distributed systems, and AI")

print(f"Generated {len(list(ASSETS.glob('*.svg')))} SVG assets in {ASSETS}")
