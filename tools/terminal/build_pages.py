"""Static light-style pages: My Condition, unsubscribe, Brand Report Cards (18 graded brands), privacy, disclaimer, corrections.
Report-card numbers come only from public/terminal/data/brands.json + coas.json (brands' own published COAs)."""
import json,os,urllib.parse
from tgsite import head,header,DISC,foot,E,SITE,aitag,AI_BRAND
HERE=os.path.dirname(os.path.abspath(__file__)); PUB=os.path.normpath(os.path.join(HERE,"..","..","public","terminal"))
MYJS='<script src="/terminal/assets/terminal.js" defer></script><script type="module" src="/terminal/assets/my.js"></script>'
MIN_N=3
def w(rel,html):
    p=os.path.join(PUB,rel,"index.html"); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,"w").write(html)
def xint(text,url): return "https://x.com/intent/post?"+urllib.parse.urlencode({"text":text,"url":url},quote_via=urllib.parse.quote)
def my():
    w("my",head("My Condition: new cannabis studies for your condition | Cannabis Agent Terminal","Pick a condition and see its newest cannabis studies in plain words, graded honestly. Sign up free for alerts when new studies drop.",SITE+"/terminal/my/",SITE+"/terminal/findings/img/sleep-cbn.png",1600,900)
      +header("my")+DISC+'<main class="wrap mypage"><h1>🩺 My Condition</h1><div id="my"><p class="mute">Loading studies…</p></div>'
      '<p class="small mute" style="margin-top:22px">Studies suggest; they do not prove. Grades are AI-graded from the published study: software rules written with AI tools read the PubMed record and abstract. No person checks each grade. Always check the source. Not medical advice; talk to a doctor.</p></main>'+foot(MYJS))
def unsub():
    js='''<script type="module">import {SB_URL,SB_KEY} from '/terminal/assets/app.js';const t=new URLSearchParams(location.search).get('t'),m=document.getElementById('um');
if(!t||!/^[0-9a-f-]{36}$/i.test(t)){m.textContent='This unsubscribe link is missing its code. Sign in and turn emails off under My Condition.';}
else{fetch(SB_URL+'/rest/v1/rpc/digest_unsubscribe',{method:'POST',headers:{apikey:SB_KEY,Authorization:'Bearer '+SB_KEY,'Content-Type':'application/json'},body:JSON.stringify({token:t})}).then(r=>r.json()).then(ok=>{m.innerHTML=ok===true?'<b>Done.</b> You will not get new-study alerts or the weekly digest any more. You can turn them back on under <a class="mylink" href="/terminal/my/"><svg class="hx" viewBox="0 0 16 16" aria-hidden="true"><path d="M5.5 1h5v4.5H15v5h-4.5V15h-5v-4.5H1v-5h4.5z"/></svg>My Condition</a>.':'That link has already been used or is not valid. Sign in to check your email settings.'}).catch(()=>{m.textContent='Could not reach the server. Try again in a minute.'})}</script>'''
    w("unsubscribe",head("Unsubscribe | Cannabis Agent Terminal","Stop Cannabis Agent Terminal new-study emails.",SITE+"/terminal/unsubscribe/").replace("<head>",'<head><meta name="robots" content="noindex">',1)
      +header()+'<main class="wrap fpage"><h1>Unsubscribe</h1><div class="card"><p id="um" role="status">Unsubscribing…</p></div></main>'+foot(js))
def prose(rel,title,desc,body,extra=""):
    w(rel,head(title+" | Cannabis Agent Terminal",desc,f"{SITE}/terminal/{rel}/")+header()+f'<main class="wrap fpage"><h1>{E(title)}</h1>{body}</main>'+foot(extra))
def legal():
    prose("privacy","Privacy","What Cannabis Agent Terminal stores and why.",'''<div class="card"><p><b>What we store.</b> If you make an account: your email (handled by our auth provider, Supabase), your 21+ confirmation, an optional public username, the conditions you pick, the studies, findings and conditions you save, and your email settings (new-study alerts and the weekly digest, on by default, with the time you agreed). Choices you make before signing up stay in your own browser until you sign in.</p>
<p><b>What we don't store.</b> Payment details, health records, or anything about whether you use cannabis. Picking a condition is not a diagnosis, and we never share or sell your list.</p>
<p><b>Who can see it.</b> Only you. Row-level security in our database limits every row to its owner.</p>
<p><b>Email.</b> Alerts and the digest are sent through Brevo. Every email has a one-click unsubscribe link. You can also switch them off under <a class="mylink" href="/terminal/my/"><svg class="hx" viewBox="0 0 16 16" aria-hidden="true"><path d="M5.5 1h5v4.5H15v5h-4.5V15h-5v-4.5H1v-5h4.5z"/></svg>My Condition</a> or your <a href="/terminal/account/">account</a>.</p>
<p><b>Delete.</b> Your account page has a delete button. It removes your account and everything linked to it.</p></div>''')
    prose("disclaimer","Disclaimer","Research summaries, not medical or legal advice.",'''<div class="card"><p>Cannabis Agent Terminal summarizes published research (PubMed), news, markets and public posts for education. Studies suggest; they do not prove. Animal and cell results often do not hold in people.</p>
<p><b>Not medical advice.</b> Nothing here tells you to use, stop or change any treatment. Talk to a doctor or pharmacist, especially if you take other medicines, are pregnant, or are under 21.</p>
<p><b>Not legal advice.</b> The Dec 11 tracker reports dates from the Congressional Research Service. State law differs.</p>
<p><b>Brand Report Cards</b> compare a product's label claim with the brand's own published lab result (COA). A grade describes that number match only, not safety, quality or legality. Values are copied by hand, so always check the linked COA.</p>
<p>We do not sell products, take payment from brands, or link to stores.</p></div>''')
    prose("corrections","Corrections","Report an error in a Cannabis Agent Terminal report card or summary.",'''<div class="card"><p>We copy numbers by hand, and mistakes happen. If something is wrong, tell us what and point to the source (a newer COA, a lab amendment, the actual label, or the paper). Corrections we confirm get updated, with a note of what changed. Brands can also ask us to swap in a newer batch COA.</p>
<form data-submit="correction"><label for="f-brand">Brand or page</label><input id="f-brand" type="text" name="brand" required maxlength="120"><label for="f-prod">Product or study</label><input id="f-prod" type="text" name="product" required maxlength="200">
<label for="f-notes">What is wrong, and what is the correct value? (Link the source.)</label><textarea id="f-notes" name="notes" rows="4" maxlength="2000"></textarea>
<label class="chk"><input type="checkbox" name="confirm" value="1"><span>I represent the brand or have a source for this correction.</span></label>
<button class="btn" type="submit">Send correction</button><div class="msg" role="status"></div></form></div>''','<script type="module" src="/terminal/assets/submit.js"></script>')
def gcls(g): return "rc-"+g[0]
def sg(v): return ("+" if v>0 else "")+(f"{v:.1f}".rstrip("0").rstrip("."))
METHOD=f'''<div class="card" style="margin-top:16px"><div class="lbl" style="margin-top:0">Method (short)</div><p class="small">AI tools read each COA a brand published on its own site and copy the label claim and the lab's measured value. <b>Accuracy</b> = tested ÷ claim × 100; deviation = accuracy − 100. <b>On label</b> = within ±10%. <b>Score</b> = 100 − the average size of the deviation (never below 0). Grades: A+ ≥97, A ≥93, A− ≥90, B+ ≥87, B ≥83, B− ≥80, C+ ≥77, C ≥73, C− ≥70, D+ ≥67, D ≥63, D− ≥60, F below 60. Fewer than {MIN_N} scored COAs = small sample. COAs with no label number to compare are listed but not scored.</p>
<p class="small mute" style="margin:0">A grade describes label-vs-lab numbers only. It says nothing about safety, quality, legality or health effects. Not medical or legal advice. Brands can <a href="/terminal/corrections/">request a correction</a>.</p></div>'''
def report_cards():
    B=json.load(open(os.path.join(PUB,"data","brands.json"))); C=json.load(open(os.path.join(PUB,"data","coas.json")))
    graded=sorted([b for b in B if b.get("score") is not None],key=lambda b:-b["score"])
    by={}; [by.setdefault(c.get("brand_slug"),[]).append(c) for c in C]
    tiles=""
    for b in graded:
        url=f'{SITE}/terminal/report-cards/{b["slug"]}/'; img=f'{SITE}/terminal/share/reports/report_{b["slug"]}.png'
        ss=" · small sample" if b["scored_count"]<MIN_N else ""
        tiles+=f'<a class="rccard" href="/terminal/report-cards/{E(b["slug"])}/"><span class="rc-grade {gcls(b["grade"])}">{E(b["grade"])}</span><div><b>{E(b["name"])}</b><div class="small mute">{b["on_label"]}/{b["scored_count"]} on label · avg {sg(b["mean_signed_dev"])}% · {b["coa_count"]} COAs{ss}</div></div></a>'
        share=f'📋 {b["name"]} label-vs-lab report card: {b["grade"]} ({b["on_label"]}/{b["scored_count"]} scored COAs on label). Numbers from the brand\'s own posted COAs.'
        rows=sorted(by.get(b["slug"],[]),key=lambda c:(c.get("verdict") is None,c.get("test_date") or ""),reverse=False)
        tr="".join(f'<tr><td>{E(c["product"])}<div class="small mute">{E(c.get("lab") or "")}</div></td><td class="mono">{E(c.get("test_date") or "—")}</td>'
            f'<td class="mono">{E(c["label_claim_value"]) if c.get("label_claim_value") is not None else "—"} <span class="mute">{E(c.get("label_claim_unit") or "")}</span></td>'
            f'<td class="mono">{E(round(c["tested_value"],2)) if c.get("tested_value") is not None else "—"}</td><td class="mono">{(sg(c["deviation_pct"])+"%") if c.get("deviation_pct") is not None else "—"}</td>'
            f'<td>{E(c["verdict"]) if c.get("verdict") else "<span class=mute>not scored</span>"}</td><td><a href="{E(c["coa_url"])}" target="_blank" rel="noopener nofollow">COA ↗</a></td></tr>' for c in rows if c.get("coa_url"))
        body=f'''<main class="wrap fpage" style="max-width:1000px"><p class="eyebrow"><a href="/terminal/report-cards/">← All Brand Report Cards</a></p>
<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap"><span class="rc-grade {gcls(b["grade"])}">{E(b["grade"])}</span><div><h1 style="margin:0">{E(b["name"])}</h1><p class="dim" style="margin:2px 0 0">Report card{ss} · from the brand's own published COAs</p></div></div><p class="ainote">{aitag(AI_BRAND,"AI-scored")} {E(AI_BRAND)}</p>
<img class="fimg" src="/terminal/share/reports/report_{E(b["slug"])}.png" width="1200" height="675" alt="{E(b["name"])} report card: grade {E(b["grade"])}">
<div class="factions"><a class="btn xbtn" href="{E(xint(share,url))}" target="_blank" rel="noopener">Share on X</a><a class="btn ghost" href="/terminal/report-cards/">All report cards</a></div>
<div class="card"><dl class="kv"><dt>Grade</dt><dd><b class="mono">{E(b["grade"])}</b> (score {b["score"]})</dd><dt>On label (±10%)</dt><dd class="mono">{b["on_label"]} of {b["scored_count"]} scored COAs</dd><dt>Under / over</dt><dd class="mono">{b["under_label"]} under · {b["over_label"]} over</dd><dt>Average deviation</dt><dd class="mono">{sg(b["mean_signed_dev"])}% (avg size {b["mean_abs_dev"]}%)</dd><dt>COAs read</dt><dd class="mono">{b["coa_count"]} · labs: {E(", ".join(b.get("labs") or []))}</dd><dt>Latest test</dt><dd class="mono">{E(b.get("latest_test") or "—")}</dd></dl>
<div class="lbl">Sources: every COA we read (brand-published)</div><div class="scroll-x"><table class="rctable"><thead><tr><th>Product · lab</th><th>Tested</th><th>Label claim</th><th>Lab result</th><th>Deviation</th><th>Verdict</th><th>Source</th></tr></thead><tbody>{tr}</tbody></table></div></div>{METHOD}</main>'''
        w(f'report-cards/{b["slug"]}',head(f'{b["name"]} report card: {b["grade"]} | Cannabis Agent Terminal',f'{b["name"]}: {b["on_label"]} of {b["scored_count"]} scored COAs within ±10% of label. Grade {b["grade"]}, from the brand\'s own published COAs.',url,img,kind="article")+header("rc")+body+foot())
    n=sum(b["scored_count"] for b in graded)
    idx=f'''<main class="wrap fpage" style="max-width:1000px"><h1>Brand Report Cards</h1><p class="lede">{len(graded)} hemp brands graded on one question: does the label claim match the brand's own published lab result (COA)? {n} scored COAs. Grades describe label-vs-lab numbers only, not safety or quality.</p><p class="ainote">{aitag(AI_BRAND,"AI-scored")} {E(AI_BRAND)}</p>
<div class="factions"><a class="btn xbtn" href="{E(xint(f"📋 {len(graded)} hemp brands graded on label claim vs their own posted lab results (COAs).",SITE+"/terminal/report-cards/"))}" target="_blank" rel="noopener">Share on X</a></div>
<div class="rcgrid">{tiles}</div>{METHOD}</main>'''
    w("report-cards",head("Brand Report Cards: hemp label claims vs. the brand's own COAs | Cannabis Agent Terminal",f"{len(graded)} hemp brands graded on label claim vs their own published lab results (COAs).",SITE+"/terminal/report-cards/",SITE+"/terminal/share/reports/report_cards.png")+header("rc")+idx+foot())
    return graded
def sitemap():
    import time; today=time.strftime("%Y-%m-%d"); urls=[]
    for root,dirs,files in os.walk(PUB):
        rel=os.path.relpath(root,PUB).replace(os.sep,"/"); rel="" if rel=="." else rel+"/"
        # report-cards: Brand Auditor was removed from the site; its pages are still built but unlinked and left out of the sitemap
        if rel.split("/")[0] in ("unsubscribe","account","assets","data","share","report-cards"): continue
        for f in files:
            if f=="index.html": urls.append(f"{SITE}/terminal/{rel}")
            elif f.endswith(".html") and rel.startswith("findings"): urls.append(f"{SITE}/terminal/{rel}{f}")
    # keep each URL's previous <lastmod> so an unchanged site does not produce a new sitemap (and a redeploy) every day;
    # only URLs that are new get today's date
    import re as _re; sm=os.path.join(PUB,"..","sitemap.xml")
    try: prev=dict(_re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>",open(sm).read()))
    except Exception: prev={}
    urls=sorted(set(urls)); open(sm,"w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f"<url><loc>{u}</loc><lastmod>{prev.get(u,today)}</lastmod></url>\n" for u in urls)+"</urlset>\n"); return len(urls)
def build():
    my(); unsub(); legal(); g=report_cards(); n=sitemap(); return dict(report_cards=len(g),sitemap=n)
if __name__=="__main__":
    print(build())
