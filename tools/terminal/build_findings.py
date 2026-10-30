"""Static permalink pages for 'Latest findings' (public/terminal/findings/<slug>.html) with OG/Twitter cards."""
import json,os,html,urllib.parse
HERE=os.path.dirname(os.path.abspath(__file__)); PUB=os.path.join(HERE,"..","..","public","terminal")
SITE="https://tutchgrass.com"; E=lambda s: html.escape(str(s),quote=True)
LOGO='<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="#14532d"/><g color="#fff" transform="translate(6 5) scale(.82)"><path d="M32 8c3 7 4 14 2 22 5-6 11-9 18-10-4 7-9 12-16 14 6 0 11 2 15 5-7 2-13 1-17-2 1 4 1 8-2 13-3-5-3-9-2-13-4 3-10 4-17 2 4-3 9-5 15-5-7-2-12-7-16-14 7 1 13 4 18 10-2-8-1-15 2-22z" fill="currentColor"/><path d="M32 40v16" stroke="currentColor" stroke-width="2.5"/></g></svg>'
def load(): return json.load(open(os.path.join(HERE,"data","findings.json")))["findings"]
def enrich(f):
    f=dict(f); f["url"]=f"{SITE}/terminal/findings/{f['slug']}.html"; f["path"]=f"/terminal/findings/{f['slug']}.html"
    f["img"]=f"/terminal/findings/img/{f['slug']}.png"
    f["x_intent"]="https://x.com/intent/post?"+urllib.parse.urlencode({"text":f["share"],"url":f["url"]},quote_via=urllib.parse.quote)
    return f
HEAD='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t}</title><meta name="description" content="{d}"><link rel="canonical" href="{u}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Tutchgrass Labs"><meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:url" content="{u}">
<meta property="og:image" content="{img}"><meta property="og:image:width" content="1600"><meta property="og:image:height" content="900"><meta property="og:image:alt" content="{t}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{t}"><meta name="twitter:description" content="{d}"><meta name="twitter:image" content="{img}"><meta name="twitter:image:alt" content="{t}">
<meta name="theme-color" content="#ffffff"><link rel="icon" href="/terminal/assets/logo.svg"><link rel="stylesheet" href="/terminal/assets/terminal.css"></head><body>
<header class="top"><div class="wrap"><a class="brand" href="/terminal/">'''+LOGO+'''<span>Tutchgrass Labs<small>Cannabis research terminal</small></span></a>
<nav class="nav"><a href="/terminal/#scientist">Scientist</a><a href="/terminal/#findings">Latest findings</a><a href="/terminal/#news">News &amp; Law</a><a href="/terminal/#market">Market</a></nav>
<div class="auth"><a id="acct" class="btn ghost sm" href="/terminal/account/">Sign in</a><a class="btn sm" href="/terminal/account/#signup">Sign up free</a></div></div></header>
<div class="disc"><div class="wrap"><b>Research summary, not medical advice.</b> Studies suggest; they do not prove. Talk to a doctor. 21+.</div></div>'''
FOOT='''<footer class="foot"><div class="wrap"><b>Tutchgrass Labs</b> · Every study links to PubMed. Not medical advice. 21+. <a href="/terminal/">Back to the terminal</a> · <a href="/terminal/privacy/">Privacy</a> · <a href="/terminal/disclaimer/">Disclaimer</a></div></footer>
<script type="module" src="/terminal/assets/app.js"></script></body></html>'''
def studies_html(f):
    return "".join(f'<li><span class="tag t-{E(s["type"])}">{E(s["type"])}</span><a href="https://pubmed.ncbi.nlm.nih.gov/{E(s["pmid"])}/" target="_blank" rel="noopener">{E(s["cite"])}</a> <span class="mute mono small">PMID {E(s["pmid"])}</span> · <a class="small" href="https://doi.org/{E(s["doi"])}" target="_blank" rel="noopener">DOI</a><span class="cc dim small" style="display:block">{E(s["note"])}</span></li>' for s in f["studies"])
def page(f,allf):
    others="".join(f'<li><a href="{E(o["path"])}">{E(o["condition"])}: {E(o["headline"])}</a></li>' for o in allf if o["slug"]!=f["slug"])
    body=f'''<main class="wrap fpage"><p class="eyebrow"><a href="/terminal/#findings">Latest findings</a> · {E(f["condition"])} · <time>{E(f["date"])}</time></p>
<h1>{E(f["headline"])}</h1><p><span class="badge grade g-{E(f["grade_cls"])}">{E(f["grade"])}</span></p>
<img class="fimg" src="{E(f["img"])}" width="1600" height="900" alt="{E(f["headline"])}">
<div class="factions"><a class="btn xbtn" href="{E(f["x_intent"])}" target="_blank" rel="noopener">Share on X</a><a class="btn ghost" href="/terminal/#cond-{E(f["sci"])}">See {E(f["condition"])} in the Scientist</a></div>
<div class="card"><div class="lbl" style="margin-top:0">In plain words</div>{"".join(f"<p>{E(p)}</p>" for p in f["summary"])}
{f'<div class="lbl">Typical strains</div><p class="note">{E(f["strains"])}</p>' if f["strains"] else ''}
<div class="lbl">Studies (PubMed)</div><ul class="cites">{studies_html(f)}</ul>
<p class="small mute" style="margin-top:14px">Studies suggest; they do not prove. Animal results may not apply to people. Not medical advice; talk to a doctor.</p></div>
<div class="card" style="margin-top:16px"><div class="lbl" style="margin-top:0">More findings</div><ul class="small">{others}</ul><a class="btn sm" href="/terminal/account/#signup">Sign up free for new findings</a></div></main>'''
    d=f["share"]
    return HEAD.format(t=E(f["headline"])+" | Tutchgrass Labs",d=E(d),u=E(f["url"]),img=E(SITE+f["img"]))+body+FOOT
def build():
    allf=[enrich(f) for f in load()]
    os.makedirs(os.path.join(PUB,"findings"),exist_ok=True)
    for f in allf: open(os.path.join(PUB,"findings",f["slug"]+".html"),"w").write(page(f,allf))
    lst="".join(f'<a class="fcard" href="{E(f["path"])}"><img src="{E(f["img"])}" alt="" loading="lazy" width="1600" height="900"><div class="fb"><div class="fc">{E(f["condition"])}</div><b>{E(f["headline"])}</b><span class="badge grade g-{E(f["grade_cls"])}">{E(f["grade"])}</span></div></a>' for f in allf)
    idx=HEAD.format(t="Latest findings | Tutchgrass Labs",d="New cannabis studies in plain words, graded honestly, with PubMed links.",u=SITE+"/terminal/findings/",img=SITE+allf[0]["img"])+f'<main class="wrap fpage"><h1>Latest findings</h1><p class="lede">New studies in plain words, graded honestly. Every finding links to PubMed.</p><div class="fgrid" style="margin-top:18px">{lst}</div></main>'+FOOT
    open(os.path.join(PUB,"findings","index.html"),"w").write(idx)
    return allf
if __name__=="__main__": print(len(build()),"finding pages")
