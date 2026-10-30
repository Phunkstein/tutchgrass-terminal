"""One-off: swap the old brand text on the published share/OG images for 'Cannabis Agent Terminal'.
Report cards (1200x675): top-left wordmark -> CANNABIS AGENT TERMINAL / BY TUTCHGRASS.
Findings (1600x900): bottom-right TUTCHGRASS LABS -> CANNABIS AGENT TERMINAL. Everything else in the image is untouched."""
import os,glob
from PIL import Image,ImageDraw,ImageFont
PUB=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","public","terminal")
BC="/usr/share/fonts/truetype/sand-box/google/Barlow Condensed/BarlowCondensed-"
INTER=glob.glob("/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont*.ttf")[0]
def clear_interp(im,x0,y0,x1,y1):
    px=im.load()
    for y in range(y0,y1+1):
        a,b=px[x0-1,y],px[x1+1,y]
        for x in range(x0,x1+1):
            t=(x-x0+1)/(x1-x0+2); px[x,y]=tuple(round(a[i]+(b[i]-a[i])*t) for i in range(3))
def spaced(d,xy,text,f,fill,sp):
    x,y=xy
    for ch in text: d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+sp
def report(p):
    im=Image.open(p).convert("RGB"); clear_interp(im,117,40,300,95); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(BC+"ExtraBoldItalic.ttf",33); l,t,r,b=d.textbbox((0,0),"CANNABIS AGENT TERMINAL",font=f)
    d.text((123-l,46-t),"CANNABIS AGENT TERMINAL",font=f,fill=(243,247,252))
    g=ImageFont.truetype(BC+"BoldItalic.ttf",15); l,t,r,b=d.textbbox((0,0),"B",font=g)
    spaced(d,(122,78-t),"BY TUTCHGRASS",g,(180,255,42),2.2); im.save(p,optimize=True)
def finding(p):
    im=Image.open(p).convert("RGB"); W,H=im.size; px=im.load()
    pts=[(x,y) for y in range(830,870) for x in range(1250,W) if min(px[x,y])>60]   # old wordmark only (source line ends left of x=1200)
    x0,y0,x1,y1=min(a for a,_ in pts),min(b for _,b in pts),max(a for a,_ in pts),max(b for _,b in pts)
    d=ImageDraw.Draw(im); d.rectangle([x0-2,y0-2,x1+2,y1+2],fill=px[x0-8,y0-8])
    f=ImageFont.truetype(INTER,21); f.set_variation_by_name("Bold"); s="CANNABIS AGENT TERMINAL"
    l,t,r,b=d.textbbox((0,0),s,font=f); d.text((x1-r,y0-t),s,font=f,fill=(255,255,255)); im.save(p,optimize=True)
    return x1-(r-l)
import sys
if "--reports" in sys.argv:
    for p in sorted(glob.glob(PUB+"/share/reports/*.png")): report(p)
for p in sorted(glob.glob(PUB+"/findings/img/*.png")): print(os.path.basename(p),"brand starts x=",finding(p))
