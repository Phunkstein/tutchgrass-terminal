# Hub pages. exec()'d at the end of build.py, so page(), E, B, T, ico, gbox, r1, sg, brands, c (COAs), meta, dispboard, nl_form are in scope.
import json as _j, datetime as _dt, random as _rnd, urllib.parse as _up, os as _os
HD='data/hub/'
TR=_j.load(open(HD+'terps.json')); TC=_j.load(open(HD+'terps_curated.json')); SC=_j.load(open(HD+'science.json')); NW=_j.load(open(HD+'news.json'))
TREC=_j.load(open(HD+'terps_records.json'))
SITE='https://tutchgrass.com'
DEC11=_dt.date(2026,12,11); NOV12=_dt.date(2026,11,12); TODAY=_dt.date.today()
D11=(DEC11-TODAY).days; N12=(NOV12-TODAY).days
GOALS=dict((g,(v['label'],v['emoji'])) for g,v in TR['goals'].items()); GOALS['entourage']=('Entourage effect (THC + terps)','🤝')
GORDER=['sleep','anxiety','pain','focus','mood','inflammation','appetite','nausea','entourage']
TERPS=TR['terpenes']; TERPS['several']={'name':'Terpene mixes','aroma':'blends','common_in':'various'}
EV={'human_trial':('Human trial','ev-ht'),'human_study':('Human study','ev-hs'),'review':('Review','ev-rv'),'preclinical':('Lab / animal','ev-pc')}
EVR={'human_trial':0,'human_study':1,'review':2,'preclinical':3}
TWIST={'40734690','41003922','42386544','42708292'}
NMA='<p class="nma">🧾 <b>Not medical advice.</b> Studies suggest or link; they don\'t prove a product will do anything for you. Many studies used essential oils or pure terpenes, not cannabis. Talk to a clinician about health decisions.</p>'
def xshare(text,url): return 'https://x.com/intent/post?'+_up.urlencode({'text':text,'url':url})
def sharebar(img,text,url,dl):
    return f'''<div class="sharebar"><img class="sharecard" src="{B}{img}" alt="Share card" loading="lazy" width="1200" height="675"><div class="row" style="flex-wrap:wrap;justify-content:center"><a class="btn p" href="{E(xshare(text,url))}" target="_blank" rel="noopener">𝕏 Share on X</a><a class="btn ghost" href="{B}{img}" download="{dl}">⬇ Save card</a><button class="btn ghost" data-copy="{E(url)}">🔗 Copy link</button></div></div>'''
def pm(p): return f'https://pubmed.ncbi.nlm.nih.gov/{p}/'
def rec(p): return TREC.get(p) or {}
def evb(e): l,k=EV.get(e,('Other','ev-pc')); return f'<span class="ev {k}">{l}</span>'
def countdown(big=False):
    return f'''<div class="cd{' big' if big else ''}" data-countdown="2026-12-11T00:00:00-05:00"><div class="cdk">⏳ Federal hemp change · Dec 11, 2026</div><div class="cdn"><div><b data-u="d">{D11}</b><span>days</span></div><div><b data-u="h">--</b><span>hrs</span></div><div><b data-u="m">--</b><span>min</span></div><div><b data-u="s">--</b><span>sec</span></div></div><div class="cds">Max <b>0.4 mg total THC per container</b> for final hemp products. Synthetic-cannabinoid exclusion starts <b>Nov 12</b> ({N12} days).</div></div>'''
# ---------------- TERPS
def terp_paper(x):
    r=rec(x['pmid']); tw=' twist' if x['pmid'] in TWIST else ''
    yr=(r.get('date') or '')[:7]
    return f'''<article class="paper{tw}">{'<div class="tw">🔄 Plot twist</div>' if tw else ''}<div class="row" style="gap:6px;flex-wrap:wrap">{evb(x['evidence'])}<span class="tag">{E(TERPS.get(x['terp'],{}).get('name',x['terp']))}</span></div>
<p class="tk">{E(x['takeaway'])}</p><p class="small muted subj">Studied: {E(x['subject'])}</p>
<a class="pmid" href="{pm(x['pmid'])}" target="_blank" rel="noopener">{E((r.get('first_author') or '').strip())} · {E(r.get('journal',''))} · {E(yr)} · PMID {x['pmid']} ↗</a></article>'''
def vol(goal,terp):
    for t in TR['goals'].get(goal,{}).get('terps',[]):
        if t['terp']==terp: return t['count']
    return None
goal_cards=''
for g in GORDER:
    L=TC['goals'].get(g,[]); lab,em=GOALS[g]; ht=sum(1 for x in L if x['evidence'] in('human_trial','human_study'))
    goal_cards+=f'<a class="goal" href="{B}terps/{g}/"><span class="em">{em}</span><b>{E(lab)}</b><small>{len(L)} studies · {ht} in humans</small></a>'
ncur=sum(len(v) for v in TC['goals'].values()); nhum=sum(1 for v in TC['goals'].values() for x in v if x['evidence'] in('human_trial','human_study'))
terps_land=f'''<section class="hhero"><div class="kick">🌿 Terps</div><h1>Pick a goal. <span class="g">See the science.</span></h1><p class="muted">Terpenes are the aroma compounds in cannabis (and lavender, citrus, pepper, pine). We read <b>{ncur}</b> recent PubMed studies ({E(TR['window']['from'])} → {E(TR['window']['to'])}) by hand and graded the evidence. Only <b>{nhum}</b> were done in humans.</p></section>
<div class="goals">{goal_cards}</div>
<section class="card legend"><h3>Evidence badges</h3><div class="row" style="flex-wrap:wrap;gap:6px">{evb('human_trial')}<span class="small">randomized/controlled study in people</span></div><div class="row" style="flex-wrap:wrap;gap:6px">{evb('human_study')}<span class="small">people, but no control group (survey, EEG, observational)</span></div><div class="row" style="flex-wrap:wrap;gap:6px">{evb('review')}<span class="small">summary of other studies</span></div><div class="row" style="flex-wrap:wrap;gap:6px">{evb('preclinical')}<span class="small">cells or animals; weakest for predicting what happens in you</span></div></section>
<a class="banner gold" href="{B}quiz/">{ico("star","var(--y)")}<div><b>Which terp are you?</b><span>60-second quiz · shareable result</span></div><div class="cta">Play →</div></a>
{NMA}'''
page('terps','Terpenes by goal: what recent studies actually found | Tutchgrass Terminal',terps_land,desc=f'{ncur} recent terpene studies, hand-graded by evidence: sleep, anxiety, pain, focus and more. PubMed links on every claim.',og='share/hub/terps.png')
for g in GORDER:
    L=sorted(TC['goals'].get(g,[]),key=lambda x:(EVR.get(x['evidence'],9)))
    lab,em=GOALS[g]; byt={}
    for x in L: byt.setdefault(x['terp'],[]).append(x)
    blocks=''
    for t,xs in byt.items():
        info=TERPS.get(t,{}); v=vol(g,t)
        vtxt=f'<span class="vol" title="PubMed papers in the window with this terpene in the title and this goal in the abstract (auto-counted)">{v} papers in 18 mo</span>' if v else ''
        blocks+=f'''<section class="terpblk"><div class="th"><b>{E(info.get('name',t))}</b>{vtxt}</div><div class="small muted">{('Aroma: '+E(info['aroma'])+' · Also in: '+E(info['common_in'])) if t!='several' else 'Studies that tested several terpenes together'}</div>{''.join(terp_paper(x) for x in xs)}</section>'''
    hum=sum(1 for x in L if x['evidence'] in('human_trial','human_study'))
    url=f'{SITE}{B}terps/{g}/'
    body=f'''<p class="small" style="margin-top:12px"><a href="{B}terps/">← All goals</a></p><section class="hhero"><div class="kick">{em} Terps × {E(lab)}</div><h1>{E(lab)}: <span class="g">what studies link</span></h1>
<div class="stats four"><div class="stat"><div class="n" style="color:var(--g)">{len(L)}</div><div class="l">Studies read</div></div><div class="stat"><div class="n" style="color:var(--y)">{hum}</div><div class="l">In humans</div></div><div class="stat"><div class="n">{len([t for t in byt if t!='several'])}</div><div class="l">Terpenes</div></div><div class="stat"><div class="n" style="color:var(--r)">{sum(1 for x in L if x['pmid'] in TWIST)}</div><div class="l">Plot twists</div></div></div></section>
{blocks}{sharebar(f'share/hub/terps_{g}.png',f'{em} {lab}: what recent terpene studies actually found (and how many were in humans). Every claim links to PubMed.',url,f'terps-{g}.png')}{NMA}'''
    page(f'terps/{g}',f'Terpenes for {lab}: recent studies, graded | Tutchgrass Terminal',body,desc=f'{len(L)} recent studies on terpenes and {lab.lower()}, graded by evidence ({hum} in humans). PubMed links.',og=f'share/hub/terps_{g}.png',active='terps/')
# ---------------- SCIENCE
items=SC['items']; cur=[i for i in items if i.get('curated')]; auto=[i for i in items if not i.get('curated')]
sow=next(i for i in items if i['pmid']==SC['study_of_week']['pmid'])
FIGHTS=[('Does cannabis help sleep?','42863850','42574897'),('Cannabinoids for dementia symptoms?','42704497','42315374')]
byp={i['pmid']:i for i in items}
def sitem(i,cls=''):
    return f'''<article class="study {cls}" data-k="{E((i.get('topic') or '').lower())}"><div class="row" style="gap:6px;flex-wrap:wrap"><span class="ev ev-ht">{E(i['kind'])}</span><span class="tag">{E(i.get('topic') or '')}</span><span class="small muted">{E(i['date'])}</span></div>
<p class="tk">{E(i['takeaway'])}</p><a class="pmid" href="{pm(i['pmid'])}" target="_blank" rel="noopener">{E(i['title'][:140])}{'…' if len(i['title'])>140 else ''} · {E(i['journal'])} · PMID {i['pmid']} ↗</a></article>'''
fights=''
for n,(q,a,b2) in enumerate(FIGHTS):
    if a in byp and b2 in byp:
        A,Bb=byp[a],byp[b2]
        fights+=f'''<section class="fight"><div class="fk">🥊 Science fight #{n+1}</div><h3>{E(q)}</h3><div class="fgrid"><div class="side l"><div class="ev ev-ht">{E(A['kind'])} · {E(A['date'][:7])}</div><p>{E(A['takeaway'])}</p><a class="pmid" href="{pm(a)}" target="_blank" rel="noopener">PMID {a} ↗</a></div><div class="vsx">VS</div><div class="side r"><div class="ev ev-ht">{E(Bb['kind'])} · {E(Bb['date'][:7])}</div><p>{E(Bb['takeaway'])}</p><a class="pmid" href="{pm(b2)}" target="_blank" rel="noopener">PMID {b2} ↗</a></div></div>
<div class="row" style="justify-content:center;flex-wrap:wrap"><a class="btn ghost" href="{E(xshare('🥊 Science fight: '+q+' Two recent reviews, two answers.',SITE+B+'science/'))}" target="_blank" rel="noopener">𝕏 Share this fight</a><a class="btn ghost" href="{B}share/hub/fight_{n+1}.png" download>⬇ Card</a></div></section>'''
topics=sorted({i.get('topic') for i in cur if i.get('topic')})
chips='<button data-chip="" aria-pressed="true">All</button>'+''.join(f'<button data-chip="{E(t.lower())}" aria-pressed="false">{E(t)}</button>' for t in topics)
autol=''.join(f'''<li><a href="{pm(i['pmid'])}" target="_blank" rel="noopener">{E(i['title'])}</a> <span class="small muted">{E(i['kind'])} · {E(i['journal'])} · {E(i['date'])}</span>{('<div class="small q">Authors\' conclusion: “'+E(i['authors_conclusion'][:260])+('…' if len(i['authors_conclusion'])>260 else '')+'”</div>') if i.get('authors_conclusion') else ''}</li>''' for i in auto)
sci=f'''<section class="hhero"><div class="kick">🔬 Science</div><h1>New cannabis science, <span class="g">in one line.</span></h1><p class="muted">Randomized trials, systematic reviews and meta-analyses from the last 18 months ({E(SC['window']['start'])} → {E(SC['window']['end'])}). PubMed found <b>{SC['total_matches']}</b>; we hand-wrote takeaways for the <b>{len(cur)}</b> most share-worthy.</p></section>
<section class="sow"><div class="fk">⭐ Study of the week</div><div class="row" style="gap:6px;flex-wrap:wrap"><span class="ev ev-ht">{E(sow['kind'])}</span><span class="small muted">{E(sow['journal'])} · {E(sow['date'])}</span></div><h2>{E(sow['title'])}</h2><p class="tk big">{E(sow['takeaway'])}</p>
<p class="small q">Authors' conclusion: “{E(sow['authors_conclusion'][:330])}{'…' if len(sow['authors_conclusion'])>330 else ''}”</p><a class="pmid" href="{pm(sow['pmid'])}" target="_blank" rel="noopener">Read it on PubMed · PMID {sow['pmid']} ↗</a>
{sharebar('share/hub/study_of_week.png','⭐ Study of the week: '+sow['takeaway'],SITE+B+'science/','study-of-the-week.png')}</section>
{fights}
<h2 style="margin-top:22px">Recent studies</h2><div class="search"><div class="chips" data-chipfilter="#slist">{chips}</div></div><div id="slist" class="grid c2">{''.join(sitem(i) for i in cur if i['pmid']!=sow['pmid'])}</div>
<details class="card" style="margin-top:14px"><summary><b>{len(auto)} more recent trials &amp; reviews</b> <span class="small muted">(auto-pulled, titles + authors' own conclusion, no takeaway written yet)</span></summary><ul class="autol">{autol}</ul></details>
{NMA}'''
page('science','Cannabis science in one line: newest trials &amp; reviews | Tutchgrass Terminal',sci,desc=f'{len(cur)} recent cannabis trials and reviews in plain English, plus study of the week. Every takeaway links to PubMed.',og='share/hub/study_of_week.png')
# ---------------- NEWS
def nrow(i): return f'<a class="news" href="{E(i["link"])}" target="_blank" rel="noopener nofollow"><b>{E(i["title"])}</b><span>{E(i["source"])} · {E(i["date"])}</span></a>'
KEYD=[('Nov 12, 2025','P.L. 119-37 (FY2026 Agriculture appropriations) rewrites the federal definition of hemp, effective in 365 days.'),
('Sep 2, 2026','Congress passes a continuing resolution, P.L. 119-103, delaying most of the new definition to Dec 11, 2026.'),
('Nov 12, 2026','Products with cannabinoids not capable of being naturally produced by the plant (certain synthetics) stop counting as hemp.'),
('Dec 11, 2026','The rest takes effect: total THC (including THCA) ≤ 0.3% dry weight, and final products over 0.4 mg combined total THC per container are excluded from hemp.')]
kd=''.join(f'<li><b>{d}</b><span>{t}</span></li>' for d,t in KEYD)
ok=sum(1 for s in NW['sources'] if s['status']=='ok')
news=f'''<section class="hhero"><div class="kick">📰 News</div><h1>Hemp &amp; cannabis <span class="g">headlines</span></h1></section>
{countdown(True)}
<section class="card keyd" style="border-color:var(--y)"><h2 style="color:var(--y)">Key dates</h2><ul class="tl">{kd}</ul><p class="small muted">Sources: Congressional Research Service <a href="https://www.congress.gov/crs-product/IF13136" target="_blank" rel="noopener">IF13136 ↗</a> · <a href="https://www.congress.gov/crs-product/IN12620" target="_blank" rel="noopener">IN12620 ↗</a> · <a href="https://uscode.house.gov/us/usc/119-136/t7/s1639o/" target="_blank" rel="noopener">7 U.S.C. §1639o ↗</a>. Not legal advice.</p>
<div class="row" style="flex-wrap:wrap;justify-content:center"><a class="btn p" href="{E(xshare(f'⏳ {D11} days until the federal hemp THC change (Dec 11, 2026): 0.4 mg total THC per container. Live countdown + sourced headlines:',SITE+B+'news/'))}" target="_blank" rel="noopener">𝕏 Share the countdown</a><a class="btn ghost" href="{B}share/hub/countdown.png" download="dec11-countdown.png">⬇ Countdown card</a></div></section>
<h2>🌿 Hemp rules</h2><div class="board solo nlist">{''.join(nrow(i) for i in NW['hemp'])}</div>
<h2>🏛️ Federal</h2><div class="board solo nlist">{''.join(nrow(i) for i in NW['federal'])}</div>
<h2>🗺️ States &amp; world</h2><div class="board solo nlist">{''.join(nrow(i) for i in NW['other'])}</div>
<p class="small muted">Updated {E(NW['generated'])} from {ok} of {len(NW['sources'])} public RSS feeds (Marijuana Moment, MJBizDaily, New Cannabis Ventures, Business of Cannabis, StratCann, Cannabis Health News, Google News searches). Headlines and links only, last {NW['max_age_days']} days, deduplicated. Google News links redirect to the publisher. We don't write or endorse these stories.</p>'''
page('news','Dec 11 hemp countdown + hemp &amp; cannabis news | Tutchgrass Terminal',news,desc=f'{D11} days to the Dec 11, 2026 federal hemp change (0.4 mg THC per container). Live countdown, key dates from CRS, and sourced headlines.',og='share/hub/countdown.png')
# ---------------- DISPENSARY
page('dispensary','Licensed dispensary data: CO/MI | Tutchgrass Terminal','<section class="hhero"><div class="kick">🏪 Dispensary</div><h1>Licensed <span class="g">dispensary</span> data</h1><p class="muted">State-licensed Colorado and Michigan brands, plus state benchmarks. No prices, no store links.</p></section>'+dispboard('dp').replace('<div class="hide" id="dp-disp">','<div id="dp-disp">',1),desc='Licensed Colorado & Michigan dispensary COAs and state potency benchmarks.')
# ---------------- REPORT CARDS
graded=sorted([b for b in brands if b.get('score') is not None],key=lambda b:(-b['score'],-b['scored_count']))
def rc_tile(b):
    on=b['on_label']; n=b['scored_count']
    return f'''<a class="rc" href="{B}report-cards/{b['slug']}/">{gbox(b['grade'],'big')}<div><b>{E(b['name'])}</b><small>{on}/{n} on label · avg {sg(b['mean_signed_dev'])}% · {b['coa_count']} COAs</small></div></a>'''
page('report-cards','Brand Honesty Report Cards: label vs lab | Tutchgrass Terminal',f'''<section class="hhero"><div class="kick">📋 Report Cards</div><h1>Brand honesty <span class="g">report cards</span></h1><p class="muted">One shareable card per graded brand: how close the label claim was to the brand's own posted lab result (COA). <b>{len(graded)}</b> brands graded from <b>{sum(b['scored_count'] for b in graded)}</b> scored COAs. Grades describe label-vs-lab numbers only, not safety or quality. <a href="{B}methodology/">How we grade →</a></p></section>
<div class="rcs">{''.join(rc_tile(b) for b in graded)}</div><p class="small muted">Small samples swing grades: brands with fewer than {MIN_N} scored COAs are marked “small sample”. Brands can <a href="{B}corrections/">request corrections</a>.</p>''',desc=f'{len(graded)} hemp brands graded on label vs lab accuracy from their own posted COAs. Shareable report cards.',og='share/hub/report_cards.png')
for b in graded:
    xs=[x for x in c if x['brand_slug']==b['slug'] and x['verdict']]
    rows=''.join(f'<a class="lrow" href="{B}p/{x["id"]}/"><b>{E(x["product"][:60])}</b><span class="sub">Label {r1(x["label_claim_value"])} → Lab {r1(x["tested_value"])} {E(x["label_claim_unit"])}</span><span class="val {vcls(x)}">{sg(x["deviation_pct"])}%<small>{VERD[x["verdict"]][1]}</small></span></a>' for x in sorted(xs,key=lambda x:x['deviation_pct']))
    ss=' · small sample' if b['scored_count']<MIN_N else ''
    url=f'{SITE}{B}report-cards/{b["slug"]}/'
    body=f'''<p class="small" style="margin-top:12px"><a href="{B}report-cards/">← All report cards</a></p><section class="hhero"><div class="kick">📋 Report card{ss}</div><h1>{E(b['name'])}</h1></section>
<div class="rcbig">{gbox(b['grade'],'big')}<div class="stats four"><div class="stat"><div class="n" style="color:var(--g)">{r1(b['score'])}</div><div class="l">Score</div></div><div class="stat"><div class="n">{b['on_label']}/{b['scored_count']}</div><div class="l">On label</div><div class="s">within ±10%</div></div><div class="stat"><div class="n" style="color:var(--y)">{sg(b['mean_signed_dev'])}%</div><div class="l">Avg vs label</div></div><div class="stat"><div class="n">{b['coa_count']}</div><div class="l">COAs on file</div></div></div></div>
<div class="board solo">{rows}</div>
{sharebar(f'share/hub/report_{b["slug"]}.png',f'📋 {b["name"]} label-vs-lab report card: {b["grade"]} ({b["on_label"]}/{b["scored_count"]} scored COAs on label). Numbers from the brand\'s own posted COAs.',url,f'report-{b["slug"]}.png')}
<p class="small muted">Numbers come from {E(b['name'])}'s publicly posted COAs, rounded to 1 decimal. A grade describes how close label claims were to lab results, nothing else. <a href="{B}{b['slug']}/">All {E(b['name'])} COAs →</a> · <a href="{B}corrections/">Request a correction</a></p>'''
    page(f'report-cards/{b["slug"]}',f'{b["name"]} honesty report card: {b["grade"]} | Tutchgrass Terminal',body,desc=f'{b["name"]}: {b["on_label"]} of {b["scored_count"]} scored COAs within ±10% of label. Grade {b["grade"]}.',og=f'share/hub/report_{b["slug"]}.png',active='report-cards/')
# ---------------- LAB DUEL
duel=[dict(b=x['brand'],p=x['product'][:70],t=x['product_type'],cl=x['label_claim_value'],lab=x['tested_value'],u=x['label_claim_unit'],acc=round(x['accuracy_pct'],1),dev=round(x['deviation_pct'],1),coa=x['coa_url'],id=x['id']) for x in c if x['verdict'] and x.get('accuracy_pct') is not None]
page('duel','Lab Duel: whose label was more honest? | Tutchgrass Terminal',f'''<section class="show duel" style="margin-top:14px"><div class="fk">⚔️ Lab Duel</div><h1 style="margin:4px 0">Whose label was <span style="color:var(--g)">more honest?</span></h1>
<div class="hud"><div><span>Streak</span><b id="d-streak">0</b></div><div><span>Best</span><b id="d-best">0</b></div><div><span>Played</span><b id="d-played">0</b></div></div>
<p class="muted small">Two real products. Tap the one whose lab result came closer to its label claim. {len(duel)} scored COAs in the deck.</p>
<div class="dgrid"><button class="dcard" data-side="0"></button><div class="vsx">VS</div><button class="dcard" data-side="1"></button></div>
<div id="d-res" class="hide"><div id="d-verdict" class="verdict"></div><div class="row" style="justify-content:center;flex-wrap:wrap"><button id="d-next" class="btn p">Next duel →</button><button id="d-share" class="btn ghost">𝕏 Share streak</button><a id="d-dl" class="btn ghost" download="lab-duel.png">⬇ Card</a></div><canvas id="d-card" class="hide" width="1200" height="675"></canvas></div></section>
<script type="application/json" id="duel-data">{_j.dumps(duel)}</script>
<p class="small muted">Numbers are copied from each brand's posted COA; tap “COA ↗” after a duel to check. Closer to label = smaller % gap between label claim and lab result.</p>''',scripts=('hub.js',),desc='Two real hemp products. Guess whose label was closer to the lab result. Real COA numbers.',og='share/hub/duel.png')
# ---------------- QUIZ
QT=['myrcene','limonene','linalool','caryophyllene','pinene']
PERS={'myrcene':('The Couch Captain','Earthy, mellow, zero rush. You treat “later” as a valid plan.'),
'limonene':('The Bright Side','Citrus energy. First to the group chat, last to leave the party.'),
'linalool':('The Calm Florist','Lavender-soft and unbothered. You are everyone\'s chill friend.'),
'caryophyllene':('The Spice Rack','Peppery and bold. You say what everyone was thinking.'),
'pinene':('The Trailhead','Fresh pine air. You already planned the hike and packed snacks.')}
def tstudies(t): return [(g,x) for g,L in TC['goals'].items() for x in L if x['terp']==t]
qd={}
for t in QT:
    st=tstudies(t); hum=[s for s in st if s[1]['evidence'] in('human_trial','human_study')]
    hl=(hum or st)[0]
    qd[t]=dict(name=TERPS[t]['name'],title=PERS[t][0],blurb=PERS[t][1],aroma=TERPS[t]['aroma'],also=TERPS[t]['common_in'],n=len(st),h=len(hum),goals=sorted({GOALS[g][0] for g,_ in st}),hl=hl[1]['takeaway'],hlp=hl[1]['pmid'])
Q=[('Pick a Saturday',[('Couch, blanket, movie marathon','myrcene'),('Brunch with way too many friends','limonene'),('Spa day, phone off','linalool'),('Trying the spiciest thing on the menu','caryophyllene'),('Sunrise hike','pinene')]),
('Pick a smell',[('Fresh-cut mango','myrcene'),('Lemon zest','limonene'),('Lavender','linalool'),('Cracked black pepper','caryophyllene'),('Pine forest after rain','pinene')]),
('Your group-chat role',[('Replies 6 hours later with “lol”','myrcene'),('Sends 40 memes before 9 a.m.','limonene'),('Calms everyone down','linalool'),('Starts the debate','caryophyllene'),('Makes the plan','pinene')]),
('Pick a playlist',[('Lo-fi beats','myrcene'),('Summer pop','limonene'),('Acoustic','linalool'),('Hip-hop','caryophyllene'),('Indie folk','pinene')]),
('Pick a superpower',[('Infinite naps','myrcene'),('Contagious good mood','limonene'),('Instant calm','linalool'),('Unshakeable confidence','caryophyllene'),('Perfect memory','pinene')])]
qdata=dict(q=[dict(q=a,o=[dict(t=t,k=k) for t,k in o]) for a,o in Q],r=qd)
page('quiz','Which terpene are you? 60-second quiz | Tutchgrass Terminal',f'''<section class="show quiz" style="margin-top:14px"><div class="fk">🎭 Terp Personality Quiz</div><h1 style="margin:4px 0">Which <span style="color:var(--g)">terpene</span> are you?</h1><p class="muted small">5 questions, just for fun. Your result comes with what real studies looked at for that terpene.</p>
<div id="qz"></div></section><script type="application/json" id="quiz-data">{_j.dumps(qdata)}</script>{NMA}''',scripts=('hub.js',),desc='5 questions. Find your terpene personality, then see what recent studies actually say about it.',og='share/hub/quiz.png')
for t in QT:
    r=qd[t]; url=f'{SITE}{B}quiz/{t}/'
    page(f'quiz/{t}',f'I\'m {r["name"]}: {r["title"]} | Terp Quiz | Tutchgrass Terminal',f'''<section class="show quiz" style="margin-top:14px"><div class="fk">🎭 Terp Personality</div><h1 style="margin:4px 0">{E(r['name'])}: <span style="color:var(--g)">{E(r['title'])}</span></h1><p>{E(r['blurb'])}</p><p class="small muted">Aroma: {E(r['aroma'])} · Also found in: {E(r['also'])}</p>
<div class="card"><b>What studies looked at:</b> {r['n']} recent studies we read mention {E(r['name'])} for {E(', '.join(r['goals']).lower())}; {r['h']} were in humans. Example: {E(r['hl'])} <a href="{pm(r['hlp'])}" target="_blank" rel="noopener">PMID {r['hlp']} ↗</a></div>
<a class="btn p full" href="{B}quiz/" style="margin-top:12px">Take the quiz →</a></section>{sharebar(f'share/hub/quiz_{t}.png',f'I got {r["name"]}: {r["title"]} 🌿 Which terpene are you?',url,f'terp-{t}.png')}{NMA}''',desc=f'{r["name"]}: {r["title"]}. {r["blurb"]}',og=f'share/hub/quiz_{t}.png',active='quiz/')
# ---------------- HUB LANDING
hl3=''.join(nrow(i) for i in NW['hemp'][:3])
gw=''.join(f'<a class="chip" href="{B}terps/{g}/">{GOALS[g][1]} {E(GOALS[g][0].split(" (")[0])}</a>' for g in GORDER)
hub=f'''<section class="hhero hubhero"><div class="verify">{ico('star','var(--y)')}<span>Real COAs · real studies · real headlines</span></div>
<h1 class="mega" style="font-size:clamp(52px,16vw,110px)"><span class="w">Hemp</span> <span class="v">Truth</span><br><span class="l">Hub</span></h1>
<div class="tagline"><i class="haz"></i><span>Tested. <span class="g">Sourced.</span> Shareable.</span><i class="haz"></i></div></section>
{countdown()}
<div class="tiles">
<a class="tile" href="{B}lab/"><span class="ti">🧪</span><b>Label vs Lab</b><small>{meta['coa_count']} COAs · {len(graded)} brands graded</small></a>
<a class="tile" href="{B}terps/"><span class="ti">🌿</span><b>Terps</b><small>{ncur} studies by goal</small></a>
<a class="tile" href="{B}science/"><span class="ti">🔬</span><b>Science</b><small>{len(cur)} one-line takeaways</small></a>
<a class="tile" href="{B}news/"><span class="ti">📰</span><b>News</b><small>{len(NW['hemp'])+len(NW['federal'])+len(NW['other'])} sourced headlines · Dec 11</small></a>
<a class="tile" href="{B}dispensary/"><span class="ti">🏪</span><b>Dispensary</b><small>CO/MI licensed data</small></a>
<a class="tile" href="{B}report-cards/"><span class="ti">📋</span><b>Report Cards</b><small>{len(graded)} shareable grades</small></a></div>
<section class="sow mini"><div class="fk">⭐ Study of the week</div><p class="tk">{E(sow['takeaway'])}</p><a class="pmid" href="{B}science/">More science →</a></section>
<div class="tiles two"><a class="tile play" href="{B}quiz/"><span class="ti">🎭</span><b>Which terp are you?</b><small>60-sec quiz</small></a><a class="tile play" href="{B}duel/"><span class="ti">⚔️</span><b>Lab Duel</b><small>Whose label lied less?</small></a></div>
<h2>Find your goal</h2><div class="chiprow">{gw}</div>
<h2>Hemp headlines</h2><div class="board solo nlist">{hl3}</div><p><a href="{B}news/">All headlines →</a></p>
<div class="sec">{nl_form('hub')}</div>'''
page('','Tutchgrass Terminal: hemp truth hub (lab data, terp science, Dec 11 news)',hub,desc=f'Label vs lab COA grades, terpene science by goal, one-line study takeaways, and a live countdown to the Dec 11, 2026 hemp change.',og='share/hub/hub.png',scripts=('hub.js',))
# hub.js also runs countdown/copy on other pages: add to every hub page via global script below
_j.dump(dict(d11=D11,graded=len(graded),duel=len(duel)),open(T+'/data/hub_meta.json','w'))
