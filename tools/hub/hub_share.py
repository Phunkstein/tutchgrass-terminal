"""Render 1200x675 X/OG share cards for the hub from data/hub/*.json + data/brands.json -> site/terminal/share/hub/*.png"""
import json,html,os,base64,datetime as dt,sys
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
E=html.escape; H='data/hub/'
TR=json.load(open(H+'terps.json')); TC=json.load(open(H+'terps_curated.json')); SC=json.load(open(H+'science.json')); brands=json.load(open('data/brands.json')); meta=json.load(open('data/meta.json'))
OUT='site/terminal/share/hub'; os.makedirs(OUT,exist_ok=True)
FD='site/terminal/assets/fonts/'
ff=''.join(f"@font-face{{font-family:{fam};font-weight:{w};font-style:{st};src:url(data:font/woff;base64,{base64.b64encode(open(FD+f,'rb').read()).decode()})}}" for fam,w,st,f in [('BC',900,'italic','BarlowCondensed-BlackItalic.woff'),('BC',800,'italic','BarlowCondensed-ExtraBoldItalic.woff'),('BC',700,'normal','BarlowCondensed-Bold.woff'),('B',600,'normal','Barlow-SemiBold.woff'),('B',400,'normal','Barlow-Regular.woff')])
LOGO=open('site/terminal/assets/logo.svg').read()
CSS=ff+'''*{box-sizing:border-box;margin:0}body{width:1200px;height:675px;overflow:hidden;background:radial-gradient(ellipse at 50% 0,#15305a 0,#0a1a2f 45%,#06101d 100%);color:#f3f7fc;font-family:B,'Noto Color Emoji';display:flex;flex-direction:column}
.haz{height:20px;flex:none;background:repeating-linear-gradient(-45deg,#ffc21a 0 18px,#06101d 18px 36px)}
.hd{display:flex;align-items:center;gap:14px;padding:18px 50px 0}.hd svg{width:56px;height:56px}.hd b{font:900 italic 34px/1 BC;letter-spacing:1px}.hd i{display:block;font:800 italic 16px BC;color:#b4ff2a;letter-spacing:5px}
.hd .k{margin-left:auto;font:900 italic 26px BC;text-transform:uppercase;letter-spacing:2px;padding:6px 14px;border-radius:8px;background:#ffc21a;color:#1b1300}
.main{flex:1;padding:14px 50px 0;display:flex;flex-direction:column;min-height:0}
h1{font:900 italic 76px/.92 BC;text-transform:uppercase;letter-spacing:-.5px}.g{color:#b4ff2a}.y{color:#ffc21a}.r{color:#ff3b4a}.m{color:#93a6c1}
.ft{display:flex;justify-content:space-between;align-items:center;padding:10px 50px 16px;font:700 22px BC;color:#93a6c1;letter-spacing:1px;text-transform:uppercase}.ft b{color:#b4ff2a;font:900 italic 26px BC}
.rows{display:flex;flex-direction:column;gap:9px;margin-top:14px}.rw{display:flex;align-items:center;gap:14px;background:#0d1d33;border:2px solid #1f3a60;border-radius:12px;padding:9px 16px}
.rw .t{font:900 italic 32px/1 BC;text-transform:uppercase;color:#b4ff2a;min-width:210px}.rw .s{font:600 22px/1.2 B;color:#dfe7f2;flex:1}
.ev{font:800 18px/1 BC;text-transform:uppercase;padding:6px 9px;border-radius:6px;white-space:nowrap}.ht{background:#b4ff2a;color:#08120a}.hs{background:#ffc21a;color:#1b1300}.rv{background:#3d7bff;color:#fff}.pc{background:#2a3d59;color:#cfd8e3}
.big{font:900 italic 230px/.8 BC}.tk{font:600 38px/1.22 B}.sm{font:600 22px/1.3 B;color:#b9c6d8}
.stats{display:flex;gap:14px;margin-top:16px}.st{flex:1;background:#0d1d33;border:2px solid #1f3a60;border-radius:12px;padding:10px;text-align:center}.st b{display:block;font:900 italic 58px/1 BC}.st span{font:700 20px BC;text-transform:uppercase;color:#93a6c1;letter-spacing:1px}
.gr{width:230px;height:230px;border:8px solid;border-radius:26px;display:grid;place-items:center;font:900 italic 150px/1 BC}'''
GC={'A':'#b4ff2a','B':'#ffc21a','C':'#ff8f1f','D':'#ff6a2a','F':'#ff3b4a'}
EVC={'human_trial':('Human trial','ht'),'human_study':('Human study','hs'),'review':('Review','rv'),'preclinical':('Lab/animal','pc')}
def doc(kick,main,foot='tutchgrass.com/terminal'):
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="haz"></div><div class="hd">{LOGO}<div><b>TUTCHGRASS</b><i>TERMINAL</i></div><div class="k">{kick}</div></div><div class="main">{main}</div><div class="ft"><b>{foot}</b><span>Sourced · not medical advice</span></div></body></html>'
TODAY=dt.date.today(); D11=(dt.date(2026,12,11)-TODAY).days
GOALS={g:(v['label'],v['emoji']) for g,v in TR['goals'].items()}; GOALS['entourage']=('Entourage effect','🤝')
NAMES={k:v['name'] for k,v in TR['terpenes'].items()}; NAMES['several']='Terp mixes'
cards={}
ncur=sum(len(v) for v in TC['goals'].values()); nh=sum(1 for v in TC['goals'].values() for x in v if x['evidence'] in('human_trial','human_study'))
graded=sorted([b for b in brands if b.get('score') is not None],key=lambda b:(-b['score'],-b['scored_count']))
cards['hub']=doc('Hemp truth hub',f'''<h1>Label vs lab.<br><span class="g">Terp science.</span><br><span class="y">Dec 11 countdown.</span></h1><div class="stats"><div class="st"><b class="g">{meta['coa_count']}</b><span>COAs read</span></div><div class="st"><b class="y">{ncur}</b><span>terp studies graded</span></div><div class="st"><b class="r">{D11}</b><span>days to Dec 11</span></div></div>''')
cards['terps']=doc('Terps by goal',f'''<h1>Terpenes:<br><span class="g">what studies link</span></h1><div class="stats"><div class="st"><b class="g">{ncur}</b><span>recent studies read</span></div><div class="st"><b class="y">{nh}</b><span>done in humans</span></div><div class="st"><b>9</b><span>goals</span></div></div><p class="sm" style="margin-top:14px">Sleep · anxiety · pain · focus · mood · inflammation · appetite · nausea · entourage effect</p>''')
ER={'human_trial':0,'human_study':1,'review':2,'preclinical':3}
for g,L in TC['goals'].items():
    lab,em=GOALS[g]; best={}
    for x in sorted(L,key=lambda x:ER[x['evidence']]): best.setdefault(x['terp'],x)
    rows=''.join(f'<div class="rw"><div class="t">{E(NAMES.get(t,t))}</div><div class="s">{E(x["subject"][:70])}</div><span class="ev {EVC[x["evidence"]][1]}">{EVC[x["evidence"]][0]}</span></div>' for t,x in list(best.items())[:4])
    h=sum(1 for x in L if x['evidence'] in('human_trial','human_study'))
    cards[f'terps_{g}']=doc(f'Terps × {lab}',f'<h1 style="font-size:64px">{em} {E(lab)}: <span class="g">{len(L)} studies</span>, <span class="y">{h} in humans</span></h1><div class="rows">{rows}</div>',f'tutchgrass.com/terminal/terps/{g}')
sow=next(i for i in SC['items'] if i['pmid']==SC['study_of_week']['pmid'])
cards['study_of_week']=doc('⭐ Study of the week',f'<p class="sm">{E(sow["kind"])} · {E(sow["journal"])} · {E(sow["date"])}</p><h1 style="font-size:52px;margin:8px 0 14px">{E(sow["title"][:90])}</h1><p class="tk">{E(sow["takeaway"])}</p><p class="sm" style="margin-top:12px">PubMed PMID {sow["pmid"]}</p>','tutchgrass.com/terminal/science')
byp={i['pmid']:i for i in SC['items']}
for n,(q,a,b) in enumerate([('Does cannabis help sleep?','42863850','42574897'),('Cannabinoids for dementia symptoms?','42704497','42315374')]):
    if a in byp and b in byp:
        A,Bb=byp[a],byp[b]
        cards[f'fight_{n+1}']=doc('🥊 Science fight',f'<h1 style="font-size:64px">{E(q)}</h1><div style="display:grid;grid-template-columns:1fr 70px 1fr;gap:12px;margin-top:16px;align-items:center"><div class="rw" style="flex-direction:column;align-items:flex-start;border-color:#b4ff2a"><span class="ev ht">{E(A["kind"])}</span><div class="s" style="font-size:24px">{E(A["takeaway"][:150])}</div><span class="m" style="font:700 18px BC">PMID {a}</span></div><div class="r" style="font:900 italic 54px BC;text-align:center">VS</div><div class="rw" style="flex-direction:column;align-items:flex-start;border-color:#ffc21a"><span class="ev hs">{E(Bb["kind"])}</span><div class="s" style="font-size:24px">{E(Bb["takeaway"][:150])}</div><span class="m" style="font:700 18px BC">PMID {b}</span></div></div>','tutchgrass.com/terminal/science')
cards['countdown']=doc('Dec 11, 2026',f'<div style="display:flex;gap:40px;align-items:center"><div class="big r">{D11}</div><div><h1 style="font-size:70px">days until the<br><span class="y">federal hemp</span><br>THC change</h1></div></div><p class="tk" style="font-size:32px;margin-top:10px">Final hemp products: max <b class="g">0.4 mg total THC per container</b>. Synthetic-cannabinoid exclusion starts Nov 12.</p><p class="sm">As of {TODAY.strftime("%b %d, %Y")} · Source: CRS IF13136</p>','tutchgrass.com/terminal/news')
top=graded[:5]
cards['report_cards']=doc('📋 Report cards',f'<h1 style="font-size:64px">Brand honesty <span class="g">report cards</span></h1><div class="rows">{"".join(f"<div class=rw><div class=t style=min-width:330px>{E(b['name'])}</div><div class=s>{b['on_label']}/{b['scored_count']} on label · avg {('+' if b['mean_signed_dev']>0 else '')}{b['mean_signed_dev']:.1f}%</div><span class=ev style=background:{GC[b['grade'][0]]};color:#08120a;font-size:26px>{E(b['grade'])}</span></div>" for b in top[:4])}</div>','tutchgrass.com/terminal/report-cards')
for b in graded:
    col=GC[b['grade'][0]]; ss=' · small sample' if b['scored_count']<3 else ''
    cards[f'report_{b["slug"]}']=doc('📋 Report card'+ss,f'''<div style="display:flex;gap:40px;align-items:center;margin-top:8px"><div class="gr" style="color:{col};border-color:{col};background:{col}1a">{E(b['grade'])}</div><div style="flex:1;min-width:0"><h1 style="font-size:{72 if len(b['name'])<16 else 54}px">{E(b['name'])}</h1><p class="sm" style="font-size:26px;margin-top:8px">Label claim vs. lab result, from the brand's own posted COAs</p></div></div>
<div class="stats"><div class="st"><b class="g">{b['score']:.1f}</b><span>score</span></div><div class="st"><b>{b['on_label']}/{b['scored_count']}</b><span>on label (±10%)</span></div><div class="st"><b class="y">{('+' if b['mean_signed_dev']>0 else '')}{b['mean_signed_dev']:.1f}%</b><span>avg vs label</span></div><div class="st"><b>{b['coa_count']}</b><span>COAs on file</span></div></div>''',f'tutchgrass.com/terminal/report-cards/{b["slug"]}')
cards['duel']=doc('⚔️ Lab Duel','<h1 style="font-size:96px">Whose label was<br><span class="g">more honest?</span></h1><p class="tk" style="margin-top:18px">Two real hemp products. Guess which one\'s lab result came closer to its label. Build a streak.</p>','tutchgrass.com/terminal/duel')
PERS={'myrcene':'The Couch Captain','limonene':'The Bright Side','linalool':'The Calm Florist','caryophyllene':'The Spice Rack','pinene':'The Trailhead'}
cards['quiz']=doc('🎭 Terp quiz','<h1 style="font-size:110px">Which <span class="g">terpene</span><br>are you?</h1><p class="tk" style="margin-top:14px">5 questions. Then see what real studies looked at.</p>','tutchgrass.com/terminal/quiz')
for t,ttl in PERS.items():
    st=[x for L in TC['goals'].values() for x in L if x['terp']==t]; h=sum(1 for x in st if x['evidence'] in('human_trial','human_study'))
    cards[f'quiz_{t}']=doc('🎭 My terp personality',f'<p class="sm" style="font-size:28px">I got…</p><h1 style="font-size:120px">{E(NAMES[t])}</h1><h1 class="g" style="font-size:72px">{E(ttl)}</h1><p class="sm" style="font-size:26px;margin-top:14px">Aroma: {E(TR["terpenes"][t]["aroma"])} · {len(st)} recent studies read, {h} in humans</p>',f'tutchgrass.com/terminal/quiz/{t}')
only=set(sys.argv[1:])
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path='/usr/bin/google-chrome'); pg=br.new_page(viewport={'width':1200,'height':675})
    for k,d in cards.items():
        if only and k not in only: continue
        pg.set_content(d); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(150)
        ov=pg.evaluate('(m=>m.scrollHeight-m.clientHeight)(document.querySelector(".main"))')
        if ov>2: print('OVERFLOW',k,ov)
        pg.screenshot(path=f'{OUT}/{k}.png')
    br.close()
print('cards',len(cards))
