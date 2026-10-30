"""One-off: stamp a small AI disclosure tag on share/OG images that carry a grade.
Findings images (1600x900): 'AI-GRADED' under the grade badge. Report-card images (1200x675): 'AI-SCORED' under the badge.
Run once; it records stamped files in .ai_tagged so a re-run does not stamp twice."""
import os,json
from PIL import Image,ImageDraw,ImageFont
PUB=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","public","terminal")
F="/usr/share/fonts/truetype/sand-box/google/Barlow Condensed/BarlowCondensed-Bold.ttf"
LOG=os.path.join(PUB,"share",".ai_tagged")
done=set(json.load(open(LOG))) if os.path.exists(LOG) else set()
def stamp(path,text,right,top,size,fg,bg,border):
    im=Image.open(path).convert("RGB"); d=ImageDraw.Draw(im); f=ImageFont.truetype(F,size)
    l,t,r,b=d.textbbox((0,0),text,font=f); w,h=r-l,b-t; px,py=int(size*.45),int(size*.28)
    x1=right; x0=x1-w-2*px; y0=top; y1=y0+h+2*py
    d.rounded_rectangle([x0,y0,x1,y1],radius=int(size*.25),fill=bg,outline=border,width=2)
    d.text((x0+px-l,y0+py-t),text,font=f,fill=fg); im.save(path,optimize=True)
for n in sorted(os.listdir(os.path.join(PUB,"findings","img"))):
    p=f"findings/img/{n}"
    if n.endswith(".png") and p not in done: stamp(os.path.join(PUB,p),"AI-GRADED  ⓘ".replace("  ⓘ",""),1530,132,26,(235,235,235),(10,10,10),(150,150,150)); done.add(p)
for n in sorted(os.listdir(os.path.join(PUB,"share","reports"))):
    p=f"share/reports/{n}"
    if n.endswith(".png") and p not in done: stamp(os.path.join(PUB,p),"AI-SCORED",1150,112,22,(200,210,225),(15,27,48),(110,125,150)); done.add(p)
json.dump(sorted(done),open(LOG,"w"),indent=0); print(len(done),"images tagged")
