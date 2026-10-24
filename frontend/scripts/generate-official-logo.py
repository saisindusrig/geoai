from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import json
out=Path('frontend/public/brand');out.mkdir(exist_ok=True)
L='#8CB223';S='#B7C3AA';W='#F2F3ED';B='#080C08'
# One canonical structural S: six pinned joints, paired rails, and the crossing inner beam.
beams=f'<path d="M12 42V65L60 95L76 85M44 57L60 47L108 77V98" fill="none" stroke="{W}" stroke-width="10" stroke-linejoin="miter"/><path d="M12 42L60 12L108 42M12 42L108 98L60 128" fill="none" stroke="{L}" stroke-width="12" stroke-linejoin="round"/><path d="M12 98L60 128" fill="none" stroke="{S}" stroke-width="12"/><path d="M12 42L60 12L108 42M108 98L60 128M12 98L60 128" fill="none" stroke="{B}" stroke-width="3"/>'
nodes=[(60,12,L),(12,42,L),(108,42,L),(108,98,L),(60,128,S),(12,98,S)]
mask='<defs><mask id="j"><path d="M0 0H120V140H0Z" fill="white"/>'+''.join(f'<circle cx="{x}" cy="{y}" r="5" fill="black"/>' for x,y,c in nodes)+'</mask></defs>'
mark=mask+'<g mask="url(#j)">'+beams+'</g>'+''.join(f'<circle cx="{x}" cy="{y}" r="8" fill="none" stroke="{c}" stroke-width="5"/>' for x,y,c in nodes)
def textpath(text,size,x,y,font,color,spacing=0):
 f=TTFont(font);gs=f.getGlyphSet();cmap=f.getBestCmap();scale=size/f['head'].unitsPerEm;pen=SVGPathPen(gs);cursor=x
 for c in text:
  n=cmap[ord(c)];gs[n].draw(TransformPen(pen,(scale,0,0,-scale,cursor,y)));cursor+=f['hmtx'][n][0]*scale+spacing
 return f'<path d="{pen.getCommands()}" fill="{color}"/>',cursor
bold='C:/Windows/Fonts/segoeuib.ttf';regular='C:/Windows/Fonts/segoeuil.ttf';tagfont='C:/Windows/Fonts/segoeui.ttf'
def word(x,y,size,color):
 a,end=textpath('Struvo',size,x,y,bold,color);b,end=textpath('Civil',size,end,y,regular,color);return a+b
for tone in ['dark','light']:
 ink=W if tone=='dark' else B
 symbol=mark if tone=='dark' else mark.replace(B,'#FFFFFF').replace(W,S).replace(L,B).replace(S,B)
 for variant in ['main','secondary','simplified','submark','animated']:
  if variant=='submark':width,height=120,140;body=symbol
  elif variant=='main':width,height=380,260;body=f'<g transform="translate(138 0) scale(.86)">{symbol}</g>'+word(16,195,56,ink)+textpath('Model. Analyze. Design.',15,48,230,tagfont,S if tone=='dark' else B)[0]
  else:
   width,height=(470,140) if variant in ['secondary','animated'] else (360,110)
   scale=.8 if variant in ['secondary','animated'] else .66
   body=f'<g transform="translate(0 8) scale({scale})">{symbol}</g>'+word(115 if variant in ['secondary','animated'] else 92,86 if variant in ['secondary','animated'] else 72,60 if variant in ['secondary','animated'] else 47,ink)
  style=''
  if variant=='animated':
   grid='<path class="grid" d="M0 42H120M0 98H120M60 0V140M12 0V140M108 0V140" stroke="'+S+'" opacity=".2" fill="none"/>'
   style='<style>.grid{animation:grid 2.2s both}circle{animation:assemble .5s .3s both}g[mask]{animation:beam 1s .8s both}svg>path{animation:assemble .5s 1.7s both}@keyframes beam{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}@keyframes grid{0%{opacity:0}30%{opacity:.2}100%{opacity:0}}@keyframes assemble{0%,25%{opacity:0}100%{opacity:1}}@media(prefers-reduced-motion:reduce){*{animation:none!important}.grid{display:none}}</style>';body=grid+body
  (out/f'{variant}-{tone}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="StruvoCivil{": Model. Analyze. Design." if variant=="main" else ""}">{style}{body}</svg>',encoding='utf-8')
Path('frontend/app/icon.svg').write_bytes((out/'submark-dark.svg').read_bytes())
(out/'geometry.json').write_text(json.dumps({'nodes':nodes,'reference':'Reconstructed from approved raster; original vector master not supplied.'},indent=2))
