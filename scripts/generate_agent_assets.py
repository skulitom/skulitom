from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
gen=p/"scripts/generate_assets.py"
g=runpy.run_path(str(gen)); svg=g['svg']; panel=g['panel']; text=g['text']; star=g['star']
tools=[
('inkbolt','Inkbolt','Graphics for agents','Vector & raster editing.','Preview, revise, and export.','#b496ff','Rust Â· MCP Â· JSON CLI'),
('cutbolt','Cutbolt','Video for agents','Edit footage on exact timelines.','Inspect, undo, and render.','#88c8ff','Rust Â· FFmpeg Â· MCP'),
('pixelbolt','Pixelbolt','Pixel art for agents','Editable sprites and animation.','Recipes, previews, and atlases.','#ff7fc8','JavaScript Â· MCP Â· Local studio'),
('nestbolt','Nestbolt','Fabrication & agents','Arrange parts on fixed sheets.','Browser, command line, and MCP.','#ffcd77','Rust Â· WebAssembly Â· MCP'),
]
for slug,name,label,l1,l2,c,tags in tools:
    if slug=='inkbolt': art=f'<g class="float"><rect x="326" y="38" width="91" height="62" rx="7" fill="none" stroke="{c}" stroke-width="2"/><circle cx="343" cy="53" r="4" fill="{c}"/><path d="M333 91 L355 66 L370 80 L393 52 L411 91Z" fill="{c}" fill-opacity=".25" stroke="{c}"/><path d="M406 36 L432 62" stroke="#71efd2" stroke-width="3"/></g>'
    elif slug=='cutbolt': art=f'<g class="float"><rect x="325" y="34" width="104" height="61" rx="7" fill="none" stroke="{c}" stroke-width="2"/><path d="M365 48 L388 64 L365 79Z" fill="{c}"/><path d="M326 108 H432 M351 100 V116 M396 100 V116" stroke="{c}" stroke-width="3"/></g>'
    elif slug=='pixelbolt': art='<g class="float">'+''.join(f'<rect x="{330+x*13}" y="{35+y*13}" width="11" height="11" rx="1" fill="{c if (x+y)%3 else "#71efd2"}"/>' for y,row in enumerate(['0011100','0111110','1101011','1111111','0011100','0110110']) for x,v in enumerate(row) if v=='1')+'</g>'
    else: art=f'<g class="float"><rect x="326" y="30" width="103" height="84" rx="5" fill="none" stroke="{c}" stroke-width="2"/>'+''.join(f'<rect x="{x}" y="{y}" width="{a}" height="{b}" rx="3" fill="{c}" fill-opacity=".17" stroke="{c}"/>' for x,y,a,b in [(334,38,43,29),(383,38,37,45),(334,73,43,32),(383,89,37,16)])+'</g>'
    g['card'](slug+'.svg',label.upper(),name,[l1,l2],c,art)
