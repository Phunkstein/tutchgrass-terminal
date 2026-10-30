"""Deals agent (TEST): current dispensary deals and specials, Michigan first, licensed THC dispensaries only (no hemp shops).

Free, public sources only: each dispensary's OWN deals page or homepage, read as server-rendered HTML with one GET.
Before fetching a page, the agent reads that site's robots.txt and skips the page if robots disallows it. Nothing
behind a login, no partner/menu APIs (Dutchie, Jane, Weedmaps and Leafly are partner-only or bar scraping, so they
are not used), and no keys. Nothing is invented: every deal is the dispensary's own wording, with the dispensary's
own link. Validity dates are kept only when the page states them, and a deal whose stated end date is in the past
is dropped. A source that fails, or whose layout changed so nothing parses, gives 0 deals and an honest status.
Writes public/terminal/data/deals.json (and a copy in tools/terminal/data/deals.json). Stdlib only (Python 3.12).

  python3 tools/terminal/agents/deals.py
"""
import json,os,re,html,subprocess,sys,time,datetime as dt
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import UA, save
HERE=os.path.dirname(os.path.abspath(__file__))
PUB=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),"public","terminal","data","deals.json")
TODAY=dt.date.today()
PER_STORE=10          # keep the tab readable; the rest stay on the store's own page ("more" link)
ROBOTS={}

def get(url,timeout=30):
    r=subprocess.run(["curl","-sL","-m",str(timeout),"-A",UA,"-w","\n%{http_code}",url],capture_output=True)
    if r.returncode: raise RuntimeError(f"network error (curl {r.returncode})")
    body,_,code=r.stdout.decode("utf-8","replace").rpartition("\n")
    if code!="200": raise RuntimeError(f"HTTP {code}")
    return body
def robots_ok(url):
    p=urlparse(url); base=f"{p.scheme}://{p.netloc}"
    if base not in ROBOTS:
        rp=RobotFileParser()
        try: rp.parse(get(base+"/robots.txt",20).splitlines())
        except Exception: rp.parse([])          # no robots.txt (or unreachable) = no restrictions stated
        ROBOTS[base]=rp
    return ROBOTS[base].can_fetch("*",url) and ROBOTS[base].can_fetch("CannabisAgentTerminal",url)
def T(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def strip(h): return re.sub(r'<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>','',h,flags=re.S)
def md(s,year=None):
    """'10/28/26' or '11/1' -> date; a missing year is the current year (pages state week ranges without one)."""
    m=re.match(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$',s.strip())
    if not m: return None
    y=int(m.group(3)) if m.group(3) else (year or TODAY.year)
    if y<100: y+=2000
    try: return dt.date(y,int(m.group(1)),int(m.group(2)))
    except ValueError: return None
def D(chain,store,city,text,url,valid="",until=None,kind="limited",note=""):
    return {"chain":chain,"store":store,"city":city,"state":"MI","deal":re.sub(r'\s+',' ',text).strip(),
            "valid":valid,"until":until.isoformat() if until else "","kind":kind,"note":note,
            "collected":TODAY.isoformat(),"url":url}

# ---------- one extractor per dispensary page (each returns a list of deals; raises on fetch/parse trouble) ----------
def fire_station(url):
    h=get(url); out=[]
    for m in re.finditer(r'<h3 class="elementor-post__title">\s*<a href="([^"]+)"[^>]*>(.*?)</a>.*?<div class="elementor-post__excerpt">(.*?)</div>',h,re.S):
        link,title,body=m.group(1),T(m.group(2)),T(m.group(3))
        v=re.search(r'valid from (\d{1,2}/\d{1,2}/\d{2,4}) to (\d{1,2}/\d{1,2}/\d{2,4})',body)
        s=re.search(r'valid starting (\d{1,2}/\d{1,2}/\d{2,4})',body); o=re.search(r'valid on (\d{1,2}/\d{1,2}/\d{2,4}) only',body)
        until=md(v.group(2)) if v else (md(o.group(1)) if o else None)
        start=md(v.group(1)) if v else (md(s.group(1)) if s else (md(o.group(1)) if o else None))
        if until and until<TODAY: continue                # stated end date has passed
        if start and start>TODAY: continue                # not started yet
        valid=(f"{v.group(1)} – {v.group(2)}" if v else f"from {s.group(1)}" if s else f"{o.group(1)} only" if o else "")
        if body.startswith("Discounts are as marked above"): continue   # terms for an image-only calendar, no deal text
        kind="everyday" if re.search(r'first purchase|deals of the day',title,re.I) else "limited"
        out.append(D("The Fire Station","All TFS locations","Upper Peninsula",f"{title} — {body}",link,valid,until,kind))
    return out
def bloom_city(url):
    h=strip(get(url)); out=[]
    w=re.search(r'VALID (\d{1,2}/\d{1,2})\s*[–-]\s*(\d{1,2}/\d{1,2})',h)
    if not w: raise RuntimeError("weekly-deals header not found (layout changed?)")
    start,until=md(w.group(1)),md(w.group(2))
    if start and until and until<start: until=until.replace(year=until.year+1)
    valid=f"{w.group(1)} – {w.group(2)} (year not stated)"
    if until and until<TODAY: raise RuntimeError(f"weekly deals stated as ending {w.group(2)}: expired, not used")
    blk=h[w.end():h.find('Weekly Recurring Deals',w.end())]
    for m in re.finditer(r'<div[^>]*>\s*([A-Z][A-Za-z .]+?)\s*</div>(.*?)(?=<a [^>]*href="([^"]+/specials)")',blk,re.S):
        city,inner,link=m.group(1).strip(),m.group(2),m.group(3)
        if city in("REC","MED"): continue
        tag=""
        for part in re.split(r'(<div[^>]*>\s*(?:REC|MED)\s*</div>)',inner):
            t=re.search(r'>\s*(REC|MED)\s*<',part)
            if t and '<li' not in part: tag=t.group(1); continue
            for li in re.findall(r'<li[^>]*>(.*?)</li>',part,re.S):
                out.append(D("Bloom City Club",f"Bloom City Club {city}",city,T(li)+(f" ({'medical' if tag=='MED' else 'adult-use'} menu)" if tag else ""),link,valid,until))
    rec=h[h.find('Weekly Recurring Deals'):]
    rec=rec[:rec.find('cannot be combined')+40]
    for m in re.finditer(r'<strong>(\w+day)</strong>(.*?)</div>',rec,re.S):
        out.append(D("Bloom City Club","All Bloom City Club locations","Ann Arbor · Ypsilanti · Kalamazoo · Sturgis · Paw Paw",
                     f"{m.group(1)}: {T(m.group(2))}",url,"every "+m.group(1),None,"everyday","Not stackable with other offers (per page)."))
    return out
KOB_CITY={"detroit":"Detroit","ferndale":"Ferndale","inkster":"Inkster","monroe":"Monroe","new-buffalo":"New Buffalo"}
def king_of_budz(url):
    slug=url.rstrip("/").split("/")[-2]; city=KOB_CITY[slug]
    h=strip(get(url)); out=[]; seen=set()
    for m in re.finditer(r'<a data-deal-card-link=""[^>]*href="([^"]+)"[^>]*>(.*?)</a></p><div[^>]*><span[^>]*>(.*?)</span><span[^>]*>(.*?)</span>',h,re.S):
        link,name,typ,left=m.group(1),T(m.group(2)),T(m.group(3)),T(m.group(4))
        if name in seen: continue
        seen.add(name)
        until=None; n=re.match(r'(\d+) Days? Left',left)
        if n: until=TODAY+dt.timedelta(days=int(n.group(1)))
        out.append(D("King of Budz",f"King of Budz {city}",city,f"{name} ({typ})" if typ.lower() not in name.lower() and typ!="DEAL" else name,
                     urljoin(url,link),f"page said “{left}” when checked",None,"limited"))
    return out
def cannabis_club(url):
    h=strip(get(url)); out=[]
    for m in re.finditer(r'<article[^>]*data-until="(\d{4}-\d\d-\d\d)"[^>]*>(.*?)</article>',h,re.S):
        until=dt.date.fromisoformat(m.group(1))
        if until<TODAY: continue
        lab=re.search(r'<p>(?:<svg.*?</svg>)?(.*?)</p>',m.group(2),re.S); valid=T(lab.group(1)) if lab else ""
        for li in re.findall(r'<li[^>]*>(.*?)</li>',m.group(2),re.S):
            parts=[T(x) for x in re.findall(r'<(?:span|strong)[^>]*>(.*?)</(?:span|strong)>',li,re.S)]
            out.append(D("Cannabis Club","Cannabis Club New Buffalo","New Buffalo"," — ".join(p for p in parts if p),url,valid,until,"limited",
                         "Limit 1 per customer; coupons cannot be combined (per page)."))
    for m in re.finditer(r'<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>',h,re.S):
        t,b=T(m.group(1)),T(m.group(2))
        if t in("Referral Bonus","Price Match Guarantee") or not b: continue
        out.append(D("Cannabis Club","Cannabis Club New Buffalo","New Buffalo",f"{t}: {b}",url,"recurring (per page)",None,"everyday"))
    hh=re.search(r'Happy Hour · every day.*?(\d+)\s*</?\w*[^>]*>\s*%.*?(\d{1,2}–\d{1,2} AM &amp; \d{1,2}–\d{1,2} PM)',h,re.S)
    if hh: out.append(D("Cannabis Club","Cannabis Club New Buffalo","New Buffalo",f"Happy Hour: {hh.group(1)}% off storewide, {html.unescape(hh.group(2))}, seven days a week",url,"daily",None,"everyday"))
    return out
def lume(url):
    h=strip(get(url)); out=[]
    i=h.find('Even Deeper Discounts'); blk=h[i:i+200000] if i>=0 else h
    for m in re.finditer(r'<li id="border_pod_\d+".*?<a [^>]*href="(/specials/[^"]+)"></a><div[^>]*><div[^>]*>(.*?)</div><h3[^>]*>(.*?)</h3>',blk,re.S):
        txt=f"{T(m.group(2))} {T(m.group(3))}".strip()
        if txt: out.append(D("Lume Cannabis Co.","Lume (Michigan stores)","Statewide (multiple stores)",txt,urljoin(url,m.group(1)),"",None,"limited",
                             "Homepage promo; Lume's site asks you to pick a store, so availability can vary by store."))
    return out
def liv(url):
    h=strip(get(url)); out=[]
    m=re.search(r'(Give a Can, Get a FREE Pre-Roll)\s*</[^>]+>.*?(Our fifth annual Can for a Gram[^<]+)',h,re.S)
    if m:
        body=T(m.group(2)); v=re.search(r'returns (\w+ \d{1,2}) through (\w+ \d{1,2})',body); until=None
        if v:
            try: until=dt.datetime.strptime(f"{v.group(2)} {TODAY.year}","%B %d %Y").date()
            except ValueError: pass
        if not until or until>=TODAY:
            out.append(D("LIV Cannabis","LIV (all MI stores listed)","Detroit · Ferndale · Grand Rapids · Lake Orion · Lansing · Pontiac · Westland",
                         f"{T(m.group(1))} — {body}",url,f"{v.group(1)} – {v.group(2)} (year not stated)" if v else "",until))
    if re.search(r'Bulk Flower by Common Citizen',h) and re.search(r'Common Citizen.{0,400}30% off',h,re.S):
        out.append(D("LIV Cannabis","LIV (all MI stores listed)","Detroit · Ferndale · Grand Rapids · Lake Orion · Lansing · Pontiac · Westland",
                     "Bulk Flower by Common Citizen — 30% off (as marked on the homepage)",url,"",None,"limited","Check availability at your store."))
    return out
def fluresh(url):
    h=strip(get(url)); out=[]
    m=re.search(r'(Fluresh partners with a local food pantry[^<]*?receive 10% off your order\.)',h)
    if m: out.append(D("Fluresh","Fluresh Grand Rapids","Grand Rapids",html.unescape(m.group(1)),url,"ongoing (per page)",None,"everyday"))
    return out
def exclusive(url):
    h=strip(get(url)); out=[]
    m=re.search(r'(Celebrating a birthday\? Get an extra 25% off[^<]*?)\s*(Plus, students and veterans enjoy 10% off their entire purchase every single day\.)',h)
    if m: out.append(D("Exclusive","Exclusive Ann Arbor","Ann Arbor",f"{html.unescape(m.group(1))} {m.group(2)}",url,"every day (per page)",None,"everyday"))
    m=re.search(r"(you(?:&#8217;|’|')ll earn \$25 in store credit when you refer a friend)",h)
    return out

SOURCES=[
 ("The Fire Station (Upper Peninsula)","https://thefirestation.com/deals/",fire_station),
 ("Bloom City Club","https://www.bloomcityclub.com/cannabis-deals-promotions/",bloom_city),
 *[(f"King of Budz {c}",f"https://www.kingofbudz.com/michigan/{s}/deals",king_of_budz) for s,c in KOB_CITY.items()],
 ("Cannabis Club New Buffalo","https://www.cannabisclubmi.com/deals/",cannabis_club),
 ("Lume Cannabis Co.","https://www.lume.com/",lume),
 ("LIV Cannabis","https://livcannabis.com/",liv),
 ("Fluresh","https://fluresh.com/deals/",fluresh),
 ("Exclusive Ann Arbor","https://exclusivemi.com/dispensaries/locations/ann-arbor/",exclusive),
]
# Checked by hand while building the test and NOT used (reason kept so the gap is visible on the tab):
NOT_USED=[
 ("Nirvana Center","https://nirvanacenter.com/specials/","Page is public, but every Michigan deal on it is dated 2025 (expired)."),
 ("JARS, Zen Leaf, High Profile, Ascend, Gage, Common Citizen, Dunegrass, Pure Options, Joyology","","Deals load in the browser from a menu platform (no server-side deal text); not scraped."),
 ("House of Dank, Cloud, Greenhouse, Pinnacle, Stash, Pleasantrees, Herbana, Skymint","","Site timed out or returned an error to our fetch."),
 ("Puff, Breeze, Nature's Remedy, Quality Roots","","Site returned a bot-check page instead of content."),
 ("Dutchie, Jane, Weedmaps, Leafly","","Not used: partner/API access only or their terms bar scraping."),
 ("Deals inbox","","Newsletters received so far had no Michigan deal text (out-of-state stores / a sign-up confirmation)."),
]

def run():
    deals=[]; sources=[]
    for name,url,fn in SOURCES:
        s={"name":name,"url":url,"robots":"","status":"","deals":0}
        try:
            if not robots_ok(url): s.update(robots="disallowed",status="skipped: robots.txt disallows this page"); sources.append(s); continue
            s["robots"]="allowed"; got=fn(url); kept=[]; per={}
            for d in got:                                  # cap per store so one big menu can't flood the tab
                per[d["store"]]=per.get(d["store"],0)+1
                if per[d["store"]]<=PER_STORE: kept.append(d)
            if len(kept)<len(got): s["more"]=len(got)-len(kept)
            got=kept
            s["deals"]=len(got); s["status"]="ok" if got else "ok, but no deals parsed (layout may have changed)"
            deals+=got
        except Exception as e: s["status"]=f"error: {e}"
        sources.append(s); time.sleep(1)
    by_chain={}; by_city={}
    for d in deals:
        by_chain[d["chain"]]=by_chain.get(d["chain"],0)+1; by_city[d["city"]]=by_city.get(d["city"],0)+1
    obj={"schema":"deals/1","test":True,"region":"Michigan","checked":time.strftime("%Y-%m-%d %H:%M %Z"),
         "count":len(deals),"by_chain":by_chain,"by_city":by_city,"sources":sources,
         "not_used":[{"name":n,"url":u,"why":w} for n,u,w in NOT_USED],"deals":deals,
         "sponsored":{"example":True,"label":"EXAMPLE LAYOUT","items":[],
                      "note":"Paid placement slot (not live). Sponsored deals will always be labeled and kept separate from, never ranked above, the free list."},
         "disclaimer":"21+ only. For adults 21 and older (or registered medical patients). Deals change often and can differ by store: always confirm with the store before you go. Listed from each dispensary's own public page; not an endorsement."}
    save("deals.json",obj)
    os.makedirs(os.path.dirname(PUB),exist_ok=True); json.dump(obj,open(PUB,"w"),indent=1)
    print(f"deals: {len(deals)} deals from {sum(1 for s in sources if s['deals'])}/{len(sources)} sources; "+", ".join(f"{k} {v}" for k,v in by_chain.items()))
    return obj
if __name__=="__main__": run()
