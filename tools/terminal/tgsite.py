"""Shared light-style page shell (header with My Condition first, footer) for generated Cannabis Agent Terminal pages."""
import html
SITE="https://tutchgrass-terminal.onrender.com"; E=lambda s: html.escape(str(s),quote=True)
LOGO='<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="#14532d"/><g color="#fff" transform="translate(6 5) scale(.82)"><path d="M32 8c3 7 4 14 2 22 5-6 11-9 18-10-4 7-9 12-16 14 6 0 11 2 15 5-7 2-13 1-17-2 1 4 1 8-2 13-3-5-3-9-2-13-4 3-10 4-17 2 4-3 9-5 15-5-7-2-12-7-16-14 7 1 13 4 18 10-2-8-1-15 2-22z" fill="currentColor"/><path d="M32 40v16" stroke="currentColor" stroke-width="2.5"/></g></svg>'
# Agents bar. agents.js rebuilds it from the live data (status dots, "now doing", N agents are live); this static copy is the no-JS fallback.
AGENTS=[("scientist","🔬","Scientist","/terminal/#scientist"),("grader","🧪","Study Grader","/terminal/#newstudies"),("policy","⚖️","Policy Watch","/terminal/#dec11"),
     ("news","📰","News Desk","/terminal/#news"),("recalls","🚨","Recall &amp; Safety","/terminal/#recalls"),("market","📈","Market Watcher","/terminal/#market"),("lab","🌿","Terpene Lab","/terminal/#lab"),
     ("trends","💬","Trend Spotter","/terminal/#social"),("grower","🌱","Grower Notes","/terminal/#grower"),("brands","🏷️","Brand Auditor","/terminal/report-cards/")]
PAGE_AGENT={"home":"all","my":"scientist","findings":"scientist","rc":"brands"}
def _chip(k,ic,t,h,cur):
    return (f'<a class="ag{" all" if k=="all" else ""}" data-ag="{k}" href="{h}"{" aria-current=page" if k==cur else ""}><span class="av" aria-hidden="true">{ic}</span>'
            f'<span class="tx"><span class="nm">{t}{"" if k=="all" else "<i class=\"dot s-pend\"></i>"}</span><small class="doing">{f"{len(AGENTS)} on the team" if k=="all" else "checking…"}</small></span></a>')
def nav(active=""):
    cur=PAGE_AGENT.get(active,"")
    return ('<nav class="nav agnav" aria-label="Agents"><div class="ascroll">'
            +_chip("all","◎","All agents","/terminal/",cur)+"".join(_chip(k,ic,t,h,cur) for k,ic,t,h in AGENTS)+'</div></nav>')
def header(active=""):
    return f'''<header class="top"><div class="wrap"><a class="brand" href="/terminal/">{LOGO}<span>Cannabis Agent Terminal<small>by Tutchgrass</small></span></a>
{nav(active)}<div class="auth"><a id="acct" class="btn ghost sm" href="/terminal/account/">Sign in</a><a class="btn sm" href="/terminal/account/#signup">Sign up free</a></div></div></header>'''
def head(title,desc,url,img=None,w=1200,h=675,kind="website"):
    im=(f'<meta property="og:image" content="{E(img)}"><meta property="og:image:width" content="{w}"><meta property="og:image:height" content="{h}"><meta property="og:image:alt" content="{E(title)}">'
        f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{E(img)}"><meta name="twitter:image:alt" content="{E(title)}">') if img else '<meta name="twitter:card" content="summary">'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{E(url)}">
<meta property="og:type" content="{kind}"><meta property="og:site_name" content="Cannabis Agent Terminal"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{E(url)}">
{im}<meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}">
<meta name="theme-color" content="#ffffff"><link rel="preload" href="/terminal/assets/fonts/Inter-var.woff2" as="font" type="font/woff2" crossorigin><link rel="icon" href="/terminal/assets/logo.svg"><link rel="stylesheet" href="/terminal/assets/terminal.css"></head><body>'''
DISC='<div class="disc"><div class="wrap"><b>Research summary, not medical advice.</b> Studies suggest; they do not prove. Talk to a doctor. 21+.</div></div>'
def foot(extra=""):
    return f'''<footer class="foot"><div class="wrap"><b>Cannabis Agent Terminal</b> · Every study links to PubMed. Not medical advice. 21+. Grades are AI-generated or scored automatically by AI tools from the published source. Always check the source. <a href="/terminal/">Terminal</a> · <a class="mylink" href="/terminal/my/"><svg class="hx" viewBox="0 0 16 16" aria-hidden="true"><path d="M5.5 1h5v4.5H15v5h-4.5V15h-5v-4.5H1v-5h4.5z"/></svg>My Condition</a> · <a href="/terminal/report-cards/">Brand Report Cards</a> · <a href="/terminal/privacy/">Privacy</a> · <a href="/terminal/disclaimer/">Disclaimer</a> · <a href="/terminal/corrections/">Corrections</a></div></footer>
<script type="module" src="/terminal/assets/app.js"></script><script src="/terminal/assets/agents.js" defer></script>{extra}</body></html>'''

AI_FIND="AI-graded: the grade and plain-words summary were written by AI from the cited studies; PubMed and DOI links were checked automatically. Not reviewed by a doctor. Always check the source."
AI_BRAND="Scored automatically by AI tools from the brand's own published lab reports (COAs): AI read each label claim and lab result, then a fixed formula sets the grade. Not reviewed by a person. Check the COA."
def aitag(tip,label="AI-graded"):
    return f'<span class="aitag" tabindex="0" role="note" title="{E(tip)}" data-tip="{E(tip)}">{E(label)} <i aria-hidden="true">ⓘ</i></span>'
