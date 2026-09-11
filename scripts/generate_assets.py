"""Build the profile's original, self-contained animated SVG illustrations."""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

INK = "#f5f1ff"
MUTED = "#b6aecb"
PINK = "#ff7fc8"
MINT = "#71efd2"
GOLD = "#ffcd77"
VIOLET = "#b496ff"

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


def robot(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})"><g class="float">
<path d="M-29 32 L-45 53 M29 32 L45 17" fill="none" stroke="{VIOLET}" stroke-width="9" stroke-linecap="round"/>
<circle cx="46" cy="13" r="7" fill="{MINT}"/>
<rect x="-27" y="24" width="54" height="45" rx="15" fill="#302742" stroke="{VIOLET}" stroke-width="2"/>
<path d="M-13 72 L-17 84 M13 72 L17 84" stroke="{VIOLET}" stroke-width="10" stroke-linecap="round"/>
<path d="M0 -35 V-48" stroke="{VIOLET}" stroke-width="3"/>
<circle cx="0" cy="-51" r="5" fill="{GOLD}"/>
<rect x="-43" y="-33" width="86" height="62" rx="20" fill="#3b2f57" stroke="{VIOLET}" stroke-width="2"/>
<rect x="-33" y="-23" width="66" height="42" rx="13" fill="#0c1624"/>
<g class="blink" fill="{MINT}"><rect x="-22" y="-10" width="11" height="14" rx="5"/><rect x="11" y="-10" width="11" height="14" rx="5"/></g>
<path d="M-5 7 Q0 11 5 7" fill="none" stroke="{MINT}" stroke-width="2" stroke-linecap="round"/>
<path d="M-8 47 L-1 41 M-8 47 L-1 53 M8 41 L1 53" fill="none" stroke="{PINK}" stroke-width="2" stroke-linecap="round"/>
</g></g>'''


def galaxy(x, y, scale=1):
    parts = [f'<g transform="translate({x} {y}) scale({scale})">', '<circle r="198" fill="url(#halo)"/>']
    parts += ['<ellipse rx="159" ry="110" transform="rotate(-26)" fill="none" stroke="#4e3d70" stroke-width="1.5" stroke-dasharray="4 8" class="dash"/>', '<ellipse rx="136" ry="155" transform="rotate(35)" fill="none" stroke="#283e51"/>']
    parts += [robot(0, -10, 1.2)]
    code_label = text(-21,7,"{ }",26,MINT,600,extra='class="mono"')
    parts += [f'<g transform="translate(-126 -77)"><g class="float2"><rect x="-31" y="-24" width="62" height="48" rx="12" fill="#29382f" stroke="{MINT}"/>{code_label}</g></g>']
    parts += [f'<g transform="translate(132 53)"><g class="float"><circle r="24" fill="#573749" stroke="{PINK}"/><ellipse rx="36" ry="8" transform="rotate(-30)" fill="none" stroke="{PINK}" stroke-width="3"/></g></g>']
    parts += [f'<g transform="translate(100 -117)"><g class="float2"><path d="M-20 16 L-20 -16 Q-8 -20 0 -13 Q8 -20 20 -16 L20 16 Q8 12 0 20 Q-8 12 -20 16Z" fill="#514437" stroke="{GOLD}" stroke-width="2"/><path d="M0 -12 V19" stroke="{GOLD}" stroke-width="2"/></g></g>']
    for i, (sx,sy,c) in enumerate([(-92,100,PINK),(56,-64,MINT),(-45,-130,GOLD),(158,-30,VIOLET),(65,126,GOLD),(-151,31,MINT)]):
        parts.append(star(sx,sy,c,.8 + (i%2)*.3,-i*.4))
    parts += [f'<circle cx="-75" cy="-8" r="3" fill="{PINK}"/>',f'<circle cx="59" cy="76" r="3" fill="{MINT}"/>','</g>']
    return ''.join(parts)


def pill(x,y,w,label,color):
    label_svg = text(x+w/2,y+20,label,13,color,500,extra='text-anchor="middle"')
    return f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="15" fill="{color}" fill-opacity=".09" stroke="{color}" stroke-opacity=".38"/>{label_svg}'


body = panel(1000,390)
body += '<path d="M32 1 H968" stroke="url(#rainbow)" stroke-width="2"/>'
body += text(48,50,"SKULITOM  /  ENGINEER & EXPLORER",13,MINT,600,'class="mono" letter-spacing="1.8"')
body += text(48,140,"Hey, I'm Artem.",64,INK,700)
body += text(50,192,"Serious systems.",27,MUTED,400)
body += text(50,228,"Playful possibilities.",27,MUTED,400)
body += '<rect class="cursor" x="299" y="211" width="12" height="21" rx="2" fill="#ff7fc8"/>'
body += pill(48,266,133,"Python systems",MINT)+pill(190,266,101,"AI agents",VIOLET)+pill(300,266,127,"Creative code",PINK)
body += text(50,348,"SOFTWARE ENGINEER",12,MUTED,500,'class="mono" letter-spacing="1.6"')
body += '<circle cx="227" cy="344" r="2" fill="#6b627f"/>'
body += text(243,348,"LONDON, UK",12,MUTED,500,'class="mono" letter-spacing="1.6"')
body += galaxy(770,193)
svg("hello.svg",1000,390,body,"Hey, I'm Artem — serious systems, playful possibilities")

body = panel(520,600)+'<path d="M32 1 H488" stroke="url(#rainbow)" stroke-width="2"/>'
body += text(30,44,"SKULITOM / ENGINEER & EXPLORER",12,MINT,600,'class="mono" letter-spacing="1"')
body += text(28,113,"Hey, I'm Artem.",49,INK,700)
body += text(30,156,"Serious systems. Playful possibilities.",21,MUTED)
body += pill(30,184,141,"Python systems",MINT)+pill(180,184,111,"AI agents",VIOLET)+pill(300,184,150,"Creative code",PINK)
body += galaxy(264,393,.93)
body += text(260,568,"SOFTWARE ENGINEER · LONDON, UK",12,MUTED,500,'class="mono" text-anchor="middle" letter-spacing="1.1"')
svg("hello-mobile.svg",520,600,body,"Hey, I'm Artem — software engineer in London")


def card(name, label, title, lines, color, art, title_size=30):
    body = panel(480,250)
    body += f'<path d="M22 1 H458" stroke="{color}" stroke-width="2"/>'
    body += text(26,37,label,12,color,600,'class="mono" letter-spacing="1.5"')
    body += art
    body += text(26,143,title,title_size,INK,650)
    body += text(27,178,lines[0],16,MUTED)
    body += text(27,201,lines[1],16,MUTED)
    body += text(27,232,"OPEN THE EXPERIMENT",11,color,600,'class="mono" letter-spacing="1.2"')
    body += '<path d="M433 229 L447 215 M433 215 H447 V229" fill="none" stroke="'+color+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    svg(name,480,250,body,title)


book = f'''<g transform="translate(380 74)"><g class="float2">
<path d="M-41 18 L-41 -22 Q-20 -30 0 -16 Q20 -30 41 -22 L41 18 Q20 10 0 27 Q-20 10 -41 18Z" fill="#342b48" stroke="{VIOLET}" stroke-width="2"/>
<path d="M0 -15 V26 M-30 -10 Q-17 -14 -9 -5 M-30 0 Q-17 -4 -9 5 M10 -5 Q22 -13 32 -10 M10 5 Q22 -3 32 0" fill="none" stroke="{VIOLET}" stroke-width="2"/>
</g></g>'''+star(326,50,GOLD,.7)+star(430,36,PINK,.75,-1)+star(392,30,MINT,.6,-2)
card("litharness.svg","01 / AGENTS & STORY WORLDS","LitHarness",["A workshop of AI agents for serial fiction.","Planning, world state, drafting, revision."],VIOLET,book)

latent = '<g transform="translate(384 72)"><g class="orbit">'
for i,c in enumerate([PINK,VIOLET,MINT]):
    latent += f'<ellipse rx="48" ry="18" transform="rotate({i*60})" fill="none" stroke="{c}" stroke-width="2"/>'
latent += f'<circle cx="48" r="5" fill="{PINK}"/></g><circle r="9" fill="{GOLD}"/><circle r="4" fill="#fff0d2"/></g>'
card("latent-space.svg","02 / GENERATIVE PLAY","Latent Space Explorer",["Words + WASD → a world of images.","An interactive experiment with Flux."],PINK,latent,29)

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
card("cathode.svg","03 / RETRO COMPUTING","Cathode",["Your Windows apps, through a CRT lens.","Phosphor pixels, scanlines, and glow."],MINT,crt)

map_art = '<g transform="translate(383 69)">'
for r,c in [(45,PINK),(32,GOLD),(19,MINT)]:
    map_art += f'<path d="M{-r} 4 C{-r-8} {-r}, {-r/3} {-r}, 7 {-r} C{r} {-r+4}, {r+15} 1, {r} 20 C{r-15} {r+4}, {-r} {r}, {-r} 4Z" fill="{c}" fill-opacity=".09" stroke="{c}" stroke-opacity=".65"/>'
map_art += f'<path class="dash" d="M-53 3 Q-23 -12 -9 6 T22 11 T54 15" fill="none" stroke="#86c8ff" stroke-width="4" stroke-linecap="round" stroke-dasharray="6 4"/>'
map_art += f'<circle class="spark" cx="-5" cy="-7" r="10" fill="{MINT}" fill-opacity=".25"/><circle cx="-5" cy="-7" r="4" fill="{MINT}"/></g>'
card("london.svg","04 / MAPS & EXPLORATION","London in minutes",["What does London look like in travel time?","An interactive map. Pick a place and explore."],GOLD,map_art,30)

for name, number, titles, lines, color, art in [
    ("litharness", "01 / AGENTS", ["LitHarness"], ["AI agents for", "serial fiction."], VIOLET, book),
    ("latent-space", "02 / PLAY", ["Latent Space", "Explorer"], ["Words + WASD.", "Generative images."], PINK, latent),
    ("cathode", "03 / RETRO", ["Cathode"], ["Real Windows apps.", "Retro CRT glow."], MINT, crt),
    ("london", "04 / MAPS", ["London", "in minutes"], ["Explore the city", "by travel time."], GOLD, map_art),
]:
    body = panel(240,300)
    body += f'<path d="M22 1 H218" stroke="{color}" stroke-width="2"/>'
    body += text(18,28,number,12,color,600,'class="mono" letter-spacing="1"')
    body += '<g transform="translate(-127 24) scale(.65)">'+art+'</g>'
    for i,line in enumerate(titles):
        body += text(18,150+i*31,line,27,INK,650)
    for i,line in enumerate(lines):
        body += text(18,216+i*25,line,19,MUTED)
    body += text(18,278,"EXPLORE",12,color,600,'class="mono" letter-spacing="1"')
    body += f'<path d="M203 279 L216 266 M204 266 H216 V278" fill="none" stroke="{color}" stroke-width="2"/>'
    svg(name+"-mobile.svg",240,300,body,' '.join(titles))

body = '<path d="M10 1 H990" stroke="#353047"/>'
body += text(20,49,"THANKS FOR STOPPING BY",12,MUTED,500,'class="mono" letter-spacing="1.5"')
body += text(20,77,"See you in the next experiment.",18,INK,500)
body += '<path d="M637 54 Q727 14 800 54 T978 54" stroke="url(#rainbow)" stroke-width="2" fill="none" stroke-dasharray="5 8" class="dash"/>'
body += star(780,47,PINK,1.3)+star(927,61,MINT,1,-1)+star(691,38,GOLD,.8,-2)
svg("footer.svg",1000,100,body,"Thanks for stopping by — see you in the next experiment")

print(f"Generated {len(list(ASSETS.glob('*.svg')))} SVG assets in {ASSETS}")
