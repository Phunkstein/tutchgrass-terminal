"""Shared light-style page shell (header with My Condition first, footer) for generated Tutchgrass Labs pages."""
import html
SITE="https://tutchgrass.com"; E=lambda s: html.escape(str(s),quote=True)
LOGO='<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="#14532d"/><g color="#fff" transform="translate(6 5) scale(.82)"><path d="M32 8c3 7 4 14 2 22 5-6 11-9 18-10-4 7-9 12-16 14 6 0 11 2 15 5-7 2-13 1-17-2 1 4 1 8-2 13-3-5-3-9-2-13-4 3-10 4-17 2 4-3 9-5 15-5-7-2-12-7-16-14 7 1 13 4 18 10-2-8-1-15 2-22z" fill="currentColor"/><path d="M32 40v16" stroke="currentColor" stroke-width="2.5"/></g></svg>'
NAV=[("home","/terminal/","Home"),("my","/terminal/my/","My Condition"),("scientist","/terminal/#scientist","Scientist"),("feed","/terminal/#newstudies","New studies"),("score","/terminal/#scoreboard","Scoreboard"),
     ("findings","/terminal/findings/","Findings"),("dec11","/terminal/#dec11","Dec 11"),("news","/terminal/#news","News &amp; Law"),("market","/terminal/#market","Market"),
     ("prices","/terminal/#prices","Prices"),("social","/terminal/#social","Social"),("wire","/terminal/#wire","Wire"),("rc","/terminal/report-cards/","Brand Report Cards")]
def nav(active=""):
    return '<nav class="nav" aria-label="Sections">'+"".join(f'<a href="{h}"{" class=mc" if k=="my" else (" class=lo" if k=="rc" else (" class=home" if k=="home" else ""))}{" aria-current=page" if k==active else ""}>{t}</a>' for k,h,t in NAV)+'</nav>'
def header(active=""):
    return f'''<header class="top"><div class="wrap"><a class="brand" href="/terminal/">{LOGO}<span>Tutchgrass Labs<small>Cannabis research terminal</small></span></a>
{nav(active)}<div class="auth"><a id="acct" class="btn ghost sm" href="/terminal/account/">Sign in</a><a class="btn sm" href="/terminal/account/#signup">Sign up free</a></div></div></header>'''
def head(title,desc,url,img=None,w=1200,h=675,kind="website"):
    im=(f'<meta property="og:image" content="{E(img)}"><meta property="og:image:width" content="{w}"><meta property="og:image:height" content="{h}"><meta property="og:image:alt" content="{E(title)}">'
        f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{E(img)}"><meta name="twitter:image:alt" content="{E(title)}">') if img else '<meta name="twitter:card" content="summary">'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{E(url)}">
<meta property="og:type" content="{kind}"><meta property="og:site_name" content="Tutchgrass Labs"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{E(url)}">
{im}<meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}">
<meta name="theme-color" content="#ffffff"><link rel="preload" href="/terminal/assets/fonts/Inter-var.woff2" as="font" type="font/woff2" crossorigin><link rel="icon" href="/terminal/assets/logo.svg"><link rel="stylesheet" href="/terminal/assets/terminal.css"></head><body>'''
DISC='<div class="disc"><div class="wrap"><b>Research summary, not medical advice.</b> Studies suggest; they do not prove. Talk to a doctor. 21+.</div></div>'
def foot(extra=""):
    return f'''<footer class="foot"><div class="wrap"><b>Tutchgrass Labs</b> · Every study links to PubMed. Not medical advice. 21+. Grades are AI-generated or scored automatically by AI tools from the published source. Always check the source. <a href="/terminal/">Terminal</a> · <a href="/terminal/my/">My Condition</a> · <a href="/terminal/report-cards/">Brand Report Cards</a> · <a href="/terminal/privacy/">Privacy</a> · <a href="/terminal/disclaimer/">Disclaimer</a> · <a href="/terminal/corrections/">Corrections</a></div></footer>
<script type="module" src="/terminal/assets/app.js"></script>{extra}</body></html>'''

AI_FIND="AI-graded: the grade and plain-words summary were written by AI from the cited studies; PubMed and DOI links were checked automatically. Not reviewed by a doctor. Always check the source."
AI_BRAND="Scored automatically by AI tools from the brand's own published lab reports (COAs): AI read each label claim and lab result, then a fixed formula sets the grade. Not reviewed by a person. Check the COA."
def aitag(tip,label="AI-graded"):
    return f'<span class="aitag" tabindex="0" role="note" title="{E(tip)}" data-tip="{E(tip)}">{E(label)} <i aria-hidden="true">ⓘ</i></span>'
