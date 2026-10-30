"""Deals agent (TEST): current dispensary deals and specials across US legal cannabis markets (every state + DC with
licensed adult-use or medical dispensaries), licensed THC dispensaries only (no hemp shops).

Adding a state = adding sources: append a site(...) line to SOURCES below with its state, city and page URL.
The generic page reader (deals_page.py) keeps only lines that state a concrete deal, in the page's own words.

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

def _dom(u): return ".".join(urlparse(u).netloc.lower().split(".")[-2:])
def get(url,timeout=30):
    r=subprocess.run(["curl","-sL","-m",str(timeout),"-A",UA,"-w","\n%{http_code} %{url_effective}",url],capture_output=True)
    if r.returncode: raise RuntimeError(f"network error (curl {r.returncode})")
    body,_,tail=r.stdout.decode("utf-8","replace").rpartition("\n"); code,_,eff=tail.partition(" ")
    if code!="200": raise RuntimeError(f"HTTP {code}")
    if eff and _dom(eff)!=_dom(url) and not url.endswith("/robots.txt"):
        raise RuntimeError(f"page redirects to another site ({urlparse(eff).netloc}, e.g. a menu platform); not used")
    if re.search(r'cf-chl|Just a moment\.\.\.|Attention Required|px-captcha',body[:8000]): raise RuntimeError("bot-check page instead of content")
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
def D(chain,store,city,text,url,valid="",until=None,kind="limited",note="",state="MI",cities=None):
    return {"chain":chain,"store":store,"city":city,"cities":cities or [c.strip() for c in re.split(r'\s*[·,]\s*',city) if c.strip() and not re.search(r'statewide|multiple|locations|peninsula|stores',c,re.I)],"state":state,"deal":re.sub(r'\s+',' ',text).strip(),
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

from deals_page import lines as page_lines
DAYS=r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
def _blk(L,start,end):
    i=next((k for k,l in enumerate(L) if re.search(start,l,re.I)),None)
    if i is None: raise RuntimeError(f"section '{start}' not found (layout changed?)")
    j=next((k for k in range(i+1,len(L)) if re.search(end,L[k],re.I)),len(L))
    return L[i+1:j]
def _first_deal_sents(t):
    """keep sentences up to and including the first one that states the offer (drops the product blurb after it)"""
    out=[]
    for x in re.split(r'(?<=[.!])\s+',t):
        out.append(x)
        if re.search(r'\d+\s*%\s*off|BOGO|\$\d',x,re.I): break
    return " ".join(out)
def stay_lifted(url):
    L=_blk(page_lines(get(url)),r'^Daily Specials$',r'^About Us$'); out=[]; seen=set()
    for k,l in enumerate(L):
        if not re.search(r'\d+\s*%\s*off|BOGO',l,re.I) or re.search(r'loyalty|points',l,re.I): continue
        t=_first_deal_sents(l)
        if t in seen: continue
        seen.add(t)
        day=re.search(DAYS,t,re.I)
        head=L[k-1] if not day and k and len(L[k-1])<45 and re.search(DAYS,L[k-1],re.I) else ""   # only the heading right above it
        days=re.findall(DAYS,head or t,re.I)
        valid=("every "+" & ".join(dict.fromkeys(d.capitalize() for d in days))) if days else "ongoing (per page)"
        out.append(D("Stay Lifted","Stay Lifted Jackson","Jackson",(f"{head}: " if head else "")+t,url,valid,None,"everyday",
                     "From the store's “Daily Specials” section."))
    return out
def lettuce(url):
    L=_blk(page_lines(get(url)),r"^This Week.s Specials$",r'^Must be 21|^What are you Shopping'); out=[]
    for k,l in enumerate(L):
        m=re.match(r'^\$\d+(?:\.\d\d)?\s*(?:/\s*\w+|EACH)$',l,re.I)
        if not m: continue
        name=next((L[x] for x in range(k+1,min(k+3,len(L))) if not L[x].startswith("★")),"")
        mem=next((L[x] for x in range(k+1,min(k+5,len(L))) if L[x].startswith("Lettuce +:")),"")
        sup=" While supplies last." if any("while supplies last" in L[x].lower() for x in range(k+1,min(k+4,len(L)))) else ""
        out.append(D("Lettuce","Lettuce Jackson","Jackson",f"{name} — {l}"+(f" (Lettuce+ members: {mem.split(':',1)[1].strip()})" if mem else "")+sup,
                     url,"this week (per page)",None,"limited","“This Week's Specials” on the store's homepage; limited, while they last. Lettuce+ is a paid membership."))
    if not out: raise RuntimeError("no specials found in “This Week's Specials” (layout changed?)")
    return out
def dank420(url):
    L=_blk(page_lines(get(url)),r'^Daily Deals$',r'^Our mission'); out=[]; head=[]
    for l in L:
        if l=="Detroit": continue
        if re.match(r'^\d+\s*%',l):
            h=" ".join(head).strip(" ,"); day=re.search(DAYS,h,re.I)
            out.append(D("420 Dank","420 Dank Detroit","Detroit",f"{h}: {l}",url,"every "+day.group(1).capitalize() if day else "",None,"everyday",
                         "Listed under the page's “Detroit” heading (420 Dank Detroit, E 8 Mile Rd)."))
            head=[]
        else: head.append(l)
    return out
def natures_remedy(url):
    L=page_lines(get(url)); out=[]
    for l in _blk(L,r'^REC & MED - Daily Specials$',r'^REC & MED Flower Specials$'):
        l=l.lstrip("-").strip()
        if re.search(r'medical patients',l,re.I): continue          # medical-only
        if re.match(r'^\d+% off when you buys? \d+',l,re.I) and out: out[-1]["deal"]+=("; " if out[-1]["deal"].endswith(")") is False and ":" in out[-1]["deal"] else ": ")+l; continue
        day=re.search(DAYS+r's?\b',l,re.I)
        out.append(D("Nature's Remedy","Nature's Remedy Ferndale","Ferndale",l,url,("every "+day.group(1).capitalize()) if day else "recurring (per page)",None,"everyday",
                     "From the store's “Full List of Deals” page; exclusions may apply (per page)."))
    # (dated November promos on the same page start later; not listed until they start, like other not-yet-started deals)
    for l in _blk(L,r'^REC & MED Flower Specials$',r'^REC - 7 Grams'):
        out.append(D("Nature's Remedy","Nature's Remedy Ferndale","Ferndale",l,url,"current specials (per page)",None,"limited","Flower bundle; exclusions may apply (per page)."))
    return out
def planet_jane(url):
    L=page_lines(get(url)); out=[]
    for k,l in enumerate(L):
        if re.match(r'^Hippy Hour\s*=\s*\d+% Off$',l,re.I):
            out.append(D("Planet Jane","Planet Jane Ypsilanti","Ypsilanti",f"{l}, {L[k+1]}" if k+1<len(L) and re.search(r'\d\s*(?:-|–)\s*\d.*daily',L[k+1],re.I) else l,url,"daily (per page)",None,"everyday"))
        if re.match(r'^\d+% off$',l,re.I) and k+1<len(L) and re.match(r'^for loyalty members$',L[k+1],re.I):
            out.append(D("Planet Jane","Planet Jane Ypsilanti","Ypsilanti",f"{l} {L[k+1]}",url,"ongoing (per page)",None,"everyday","Loyalty (rewards) members only."))
    return out

from deals_page import extract as read_page
from deals_geo import attach as locate
def site(state,chain,store,city,url,note="",**cfg):
    """One dispensary's own deals page. city: shown text ('A · B' for several); every deal from it gets this state/city."""
    cfg.setdefault("chain_word",re.escape(re.sub(r'^The ','',chain)))
    def fn(u):
        out=[]
        for x in read_page(get(u),cfg):
            st,c,sto=(x["region"] or (state,city,store))
            out.append(D(chain,sto or store,c or city,x["deal"],u,x["valid"],dt.date.fromisoformat(x["until"]) if x["until"] else None,x["kind"],note,st or state))
        return out
    return (state,f"{chain}" + (f" – {store}" if store and store!=chain else ""),url,fn)

# Every US state + DC with licensed dispensaries (adult-use or medical). Counts are reported for all of them, zeros included.
ADULT_USE=["AK","AZ","CA","CO","CT","DE","DC","IL","ME","MD","MA","MI","MN","MO","MT","NV","NJ","NM","NY","OH","OR","RI","VT","VA","WA"]
MEDICAL=["AL","AR","FL","GA","HI","IA","KY","LA","MS","NH","ND","OK","PA","SD","TX","UT","WV"]
NAMES={"AK":"Alaska","AL":"Alabama","AR":"Arkansas","AZ":"Arizona","CA":"California","CO":"Colorado","CT":"Connecticut","DC":"District of Columbia","DE":"Delaware",
 "FL":"Florida","GA":"Georgia","HI":"Hawaii","IA":"Iowa","IL":"Illinois","KY":"Kentucky","LA":"Louisiana","MA":"Massachusetts","MD":"Maryland","ME":"Maine",
 "MI":"Michigan","MN":"Minnesota","MO":"Missouri","MS":"Mississippi","MT":"Montana","ND":"North Dakota","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico",
 "NV":"Nevada","NY":"New York","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SD":"South Dakota","TX":"Texas","UT":"Utah",
 "VA":"Virginia","VT":"Vermont","WA":"Washington","WV":"West Virginia"}
HOD={"gratiot":"Detroit","recreational-cannabis-8-mile":"Detroit","woodward":"Detroit","recreational-cannabis-fort-st":"Detroit","lansing":"Lansing",
     "grand-rapids":"Grand Rapids","kalamazoo-rec":"Kalamazoo","ann-arbor-rec":"Ann Arbor","ypsilanti":"Ypsilanti","centerline":"Center Line",
     "garden-city":"Garden City","saginaw":"Saginaw","traverse-city-rec":"Traverse City","lapeer":"Lapeer","monroe-laplaisance":"Monroe","new-buffalo":"New Buffalo"}
HOD_NAME={"recreational-cannabis-8-mile":"8 Mile","recreational-cannabis-fort-st":"Fort St","gratiot":"Gratiot","woodward":"Woodward"}
SOURCES=[
 # ---- Michigan (hand-written readers first, then generic pages)
 ("MI","The Fire Station (Upper Peninsula)","https://thefirestation.com/deals/",fire_station),
 ("MI","Bloom City Club","https://www.bloomcityclub.com/cannabis-deals-promotions/",bloom_city),
 *[("MI",f"King of Budz {c}",f"https://www.kingofbudz.com/michigan/{s}/deals",king_of_budz) for s,c in KOB_CITY.items()],
 ("MI","Cannabis Club New Buffalo","https://www.cannabisclubmi.com/deals/",cannabis_club),
 ("MI","Lume Cannabis Co.","https://www.lume.com/",lume),
 ("MI","LIV Cannabis","https://livcannabis.com/",liv),
 ("MI","Fluresh","https://fluresh.com/deals/",fluresh),
 ("MI","Exclusive Ann Arbor","https://exclusivemi.com/dispensaries/locations/ann-arbor/",exclusive),
 ("MI","Stay Lifted (Jackson)","https://staylifted420.com/",stay_lifted),
 ("MI","Lettuce (Jackson)","https://lettucedispo.com/",lettuce),
 ("MI","Planet Jane (Ypsilanti)","https://planet-jane.com/",planet_jane),
 ("MI","420 Dank (Detroit)","https://shop420dank.com/daily-deals-about-us/",dank420),
 ("MI","Nature's Remedy (Ferndale)","https://www.naturesremedycannabis.com/alldeals/",natures_remedy),
 *[site("MI","House of Dank",f"House of Dank {HOD_NAME.get(k,c)}",c,f"https://shophod.com/stores/house-of-dank-{k}",start=r'DELI HAPPY HOUR|HAPPY HOUR|% OFF',
      skip=r'(?:SECOND|THIRD|FOURTH|FIFTH|2ND|3RD|4TH|5TH) VISIT|^\W*\d0% OFF ONE (?:FULL PRICED |REGULAR PRICED )?ITEM\W*$') for k,c in HOD.items()],
 site("MI","Wayne Releaf","Wayne Releaf","Detroit","https://waynereleaf.com/specials/"),
 site("MI","Flavors Detroit","Flavors Detroit","Detroit","https://www.flavorsdetroit.com/post/halloween-at-flavors-detroit-new-flower-10-eighths-5-concentrates-85-ounces",
      "Store blog post; no end date stated."),
 # ---- other states (one line per dispensary page)
 site("AK","Catalyst Cannabis Co.","Catalyst Cannabis Co.","Anchorage","https://www.catalystcannabisco.com/dailydeals"),
 site("AR","Good Day Farm","Good Day Farm (Arkansas & Missouri stores)","Little Rock · Hensley · Monticello · Texarkana · Van Buren","https://gooddayfarmdispensary.com/specials/",
      "One page covers Good Day Farm's Arkansas and Missouri stores; check your store.",prefix_prev=True),
 site("AZ","Nirvana Cannabis","Nirvana West Phoenix","Phoenix","https://nirvanacannabis.com/deals/west-phoenix-az/"),
 site("AZ","Nirvana Cannabis","Nirvana North Phoenix","Phoenix","https://nirvanacannabis.com/deals/north-phoenix-az/"),
 site("AZ","The Superior Dispensary","The Superior Dispensary","Phoenix","https://thesuperiordispensary.com/shop-deals/"),
 site("AZ","Sticky Saguaro","Sticky Saguaro","Chandler","https://stickysaguaro.com/deals/"),
 site("AZ","YiLo","YiLo Superstore","Phoenix","https://yilo.com/specials"),
 site("CA","The Artist Tree","The Artist Tree (California stores)","El Sobrante · Fresno · Hawthorne · Beverly Hills · Koreatown · Laguna Woods · Oxnard · West Hollywood",
      "https://theartisttree.com/daily-deals","Page says daily deals run through the end of the calendar month unless noted; pick your store on their site.",prefix_prev=True),
 site("CA","From the Earth","From the Earth","Santa Ana · Port Hueneme","https://fromtheearth.com/deals"),
 site("CA","Gemme Verdi","Gemme Verdi","San Francisco","https://www.gemmeverdi.com/san-francisco-cannabis-deals/"),
 site("CA","Urbn Leaf","Urbn Leaf","San Diego","https://www.urbnleaf.com/deals",skip=r'^Urbn Leaf Deals'),
 site("CO","Lightshade","Lightshade","Denver · Aurora · Federal Heights","https://lightshade.com/",prefix_prev=True,start=r'WEEKLY DEALS',end=r'DISPENSARY LOCATIONS'),
 site("CO","Del Mundo","Del Mundo Cannabis","Denver","https://www.delmundocannabis.com/deals/"),
 site("CO","Simply Pure","Simply Pure","Denver","https://simplypure.com/discounts/"),
 site("CO","Colorado Harvest Company","Colorado Harvest Company","Denver · Aurora","https://coloradoharvestcompany.com/event/october-vendor-of-the-month-2026/",
      range=r'(?:Oct(?:ober)?\.?\s*\d{1,2}|\d{1,2}/\d{1,2})(?:/\d{2,4})?\s*(?:[-–—]|to|through)\s*(?:Oct(?:ober)?\.?\s*\d{1,2}|\d{1,2}/\d{1,2})(?:/\d{2,4})?'),
 site("CT","Fine Fettle","Fine Fettle (Connecticut stores)","","https://www.finefettle.com/ct-daily-deals/"),
 site("CT","Shangri-La","Shangri-La Waterbury","Waterbury","https://shangriladispensaries.com/stores/shangri-la-waterbury"),
 site("DC","Firehouse DC","Firehouse DC","Washington","https://www.firehousedc.com/daily-deals/"),
 site("DC","Cookies D.C.","Cookies D.C.","Washington","https://dc.cookies.co/specials/"),
 site("DE","First State Compassion","First State Compassion","Lewes · Wilmington","https://firststatecompassion.com/"),
 site("FL","Trulieve","Trulieve (Florida stores)","","https://www.trulieve.com/discover/promotions/florida","Statewide promotions page; check your store."),
 site("IL","Bud & Rita's","Bud & Rita's","Chicago · Niles · Wadsworth · Sycamore · Forsyth","https://budandritas.com/specials/"),
 site("IL","Planet 13","Planet 13 Illinois","Waukegan","https://planet13.com/stores/planet-13-illinois-llc/specials"),
 site("IL","Altius","Altius Round Lake Beach","Round Lake Beach","https://shop.altiusdispensary.com/locations/IL/round-lake-beach/menu/discounts"),
 site("MA","Caroline's Cannabis","Caroline's Cannabis","Uxbridge · Hopedale","https://carolinescannabis.com/specials"),
 site("MA","Temescal Wellness","Temescal Wellness (Massachusetts)","Framingham · Hudson · Pittsfield","https://temescalwellness.com/"),
 site("MA","Bask","Bask","Taunton · Fairhaven","https://cometobask.com/specials/"),
 site("MA","Fine Fettle","Fine Fettle (Massachusetts stores)","","https://www.finefettle.com/ma-daily-deals/"),
 site("MA","Pettals","Pettals Cannabis","Attleboro · Charlton","https://www.pettalscannabis.com/blog/pettals-halloweek-halloween-cannabis-deals-bundles-more/",dated_only=True),
 site("MA","Massachusetts Green Retail","Massachusetts Green Retail","Lynn","https://massgreenretail.com/recreational-cannabis-dispensary-lynn-ma/mgr-halloween-2026-costumes-cannabis-deals-vendors-good-energy-in-lynn/",
      range=r'(?:Friday,\s*)?October 30.{0,40}October 31'),
 site("MA","CommCan","CommCan","Millis · Mansfield · Rehoboth","https://commcan.com/weekly-deals-news/"),
 site("MA","NETA","NETA","Brookline · Northampton","https://www.netacare.org/specials"),
 site("MD","Jenny's","Jenny's Maryland","","https://jennysmaryland.com/specials"),
 site("MD","Haven","Haven Brandywine","Brandywine","https://www.findinghaven.com/specials/halloween-weekend-5-off-all-edibles-happy-halloween-d/","Halloween weekend offer; exact dates not stated."),
 site("MD","Trulieve","Trulieve (Maryland stores)","","https://www.trulieve.com/discover/promotions/maryland","Statewide promotions page; check your store."),
 site("ME","Green Truck Farm","Green Truck Farm","North Berwick · Sanford · Kittery","https://greentruckfarm.com/specials/",prefix_prev=True),
 site("ME","Beach Boys Cannabis","Beach Boys Cannabis Co.","South Portland · Old Orchard Beach","https://www.beachboyscannabis.com/surfreport/stoner-october-2026-deals"),
 site("MO","Greenlight","Greenlight (Missouri stores)","","https://greenlightdispensary.com/greenlight-marijuana-specials/",
      regions=[(r'^MO WEST\b',"MO","Western Missouri stores",""),(r'^MO COLUMBIA',"MO","Columbia · St. Louis","")]),
 site("MO","Codes","Codes (Missouri stores)","Kansas City","https://codesdispensary.com/specials/",prefix_prev=True),
 site("MO","Proper Cannabis","Proper Cannabis (all locations)","","https://propercannabis.com/specials"),
 site("MS","Star Buds","Star Buds Oxford","Oxford","https://www.starbuds.us/oxford"),
 site("MT","The Hi-Line Co.","The Hi-Line Co. (Montana stores)","","https://www.hi-line.co/daily-deals/",prefix_prev=True),
 site("MT","Lone Peak Cannabis","Lone Peak Cannabis Co. (all MT stores)","Bozeman","https://lonepeakcannabiscompany.com/"),
 site("MT","Mission Mountain Organics","Mission Mountain Organics","Whitefish · Helena","https://www.missionmountainorganics.com/deals"),
 site("MT","Spark1","Spark1","Missoula","https://www.spark1mt.com/deals"),
 site("MT","Top Shelf Botanicals","Top Shelf Botanicals","Bozeman · Great Falls · Helena","https://topshelfbotanicals.com/daily-deals/"),
 site("NJ","Earth & Ivy","Earth & Ivy","New Brunswick · Lakehurst","https://earthandivy.co/discounts/"),
 site("NJ","Valley Wellness","Valley Wellness","Raritan","https://valleywellnessnj.com/"),
 site("NM","1UP Dispensary","1UP Dispensary","Albuquerque","https://1upabq.com/deals-/-specials"),
 site("NV","Planet 13","Planet 13 Las Vegas","Las Vegas","https://planet13.com/deals"),
 site("NV","Inyo","Inyo Fine Cannabis","Las Vegas","https://inyolasvegas.com/deals"),
 site("NY","Green Genius","Green Genius","New York (Manhattan)","https://greengeniusnyc.com/deals/",prefix_prev=True),
 site("NY","Housing Works Cannabis Co.","Housing Works Cannabis Co. (Broadway)","New York (Manhattan)","https://hwcannabis.co/deals/broadway/",prefix_prev=True),
 site("NY","Buzzy","Buzzy","Brooklyn","https://getbuzzy.com/event/flower-friday-10-off-tks-sensei-lead-farmer-oct-30/",range=r'Oct(?:ober)?\.?\s*30\b(?:,?\s*2026)?'),
 site("NY","The Daily Green","The Daily Green","New York","https://thedailygreennyc.com/specials/halloween-b2g1-mix-n-match-edibles/"),
 site("OH","Greenlight","Greenlight (Ohio stores)","","https://ohio.greenlightdispensary.com/greenlight-marijuana-specials/"),
 site("OH","Pure Ohio Wellness","Pure Ohio Wellness","Dayton · London · Tallmadge","https://pureohiowellness.com/"),
 site("OR","Bridge City Collective","Bridge City Collective","Portland","https://bridgecitycollective.com/deals"),
 site("OR","Chalice","Chalice (Oregon stores)","","https://www.chalicecannabis.com/deals"),
 site("PA","Vytal Options","Vytal Options","Harrisburg · Kennett Square · State College · Lancaster · Lansdale · Fogelsville","https://vytaloptions.com/weekly-deals/",
      range=r'Monday,?\s*October\s*\d{1,2}\s*[-–]\s*\w+,?\s*(?:October|November)\s*\d{1,2}',range_required=False),
 site("RI","Slater Center","Slater Center","Providence","https://slatercenter.com/"),
 site("SD","Good Company Cannabis","Good Company Cannabis","Sioux Falls","https://shop.cannacaresf.com/stores/cannacare-sioux-falls"),
 site("VA","Zen Leaf","Zen Leaf Norfolk","Norfolk","https://zenleafdispensaries.com/locations/norfolk/menu/medical/menu",prefix_prev=True),
 site("WA","Craft Cannabis","Craft Cannabis Andresen","Vancouver","https://www.craftcannabis.com/deals"),
 site("WA","Kaleafa","Kaleafa (Washington stores)","Aberdeen · Des Moines · Oak Harbor","https://kaleafa.com/deals",
      regions=[(r'^Aberdeen Deals',"WA","Aberdeen","Kaleafa Aberdeen"),(r'^Des Moines Deals',"WA","Des Moines","Kaleafa Des Moines"),(r'^Oak Harbor Deals',"WA","Oak Harbor","Kaleafa Oak Harbor")]),
 site("WA","Mary Mart","Mary Mart","Tacoma","https://marymart.com/deals"),
 site("WA","Clear Choice","Clear Choice Tacoma","Tacoma","https://findclearchoice.com/tacoma-deals/"),
 site("WV","Zen Leaf","Zen Leaf Morgantown","Morgantown","https://zenleafdispensaries.com/locations/morgantown/medical-menu/menu/discounts",prefix_prev=True),
]
# Checked by hand while building the test and NOT used (reason kept so the gap is visible on the tab):
NOT_USED=[
 ("Nirvana Center (Michigan)","https://nirvanacenter.com/specials/","Every Michigan deal on it is dated 2025 (expired)."),
 ("JARS (MI, incl. Jackson)","https://jarscannabis.com/mi-weekly-ads-2","Weekly ad is public text and robots.txt allows it, but JARS's terms forbid bots/scrapers “for any purpose whatsoever” and reproducing content without written consent; not used."),
 ("Mood, Fuel 420, Boogiez Arcanna (Jackson); Herbal Solutions, Flower Bowl W. Warren, Gramz Hazel Park, Information Entropy (MI)","","Deals are only in a Dutchie (or Treez) menu embed loaded from the platform; Dutchie's terms bar scraping/data mining. Not used."),
 ("20 Past 4, Pegasus (Jackson)","","Deals are a Treez storefront behind a browser-only age gate (per-product markdowns, or empty); promo banners are images or browser-rendered only. Not used."),
 ("Choice Labs (Jackson)","","No deals text on its site; the menu redirects off-site to a menu platform (dispenseapp.com)."),
 ("The Big Top Cannabis Co. (Hanover, near Jackson)","","No deals page; its menu (Carrot) renders nothing without a browser and deals go out by app/newsletter only."),
 ("420 Dank Leoni (Jackson)","https://shop420dank.com/daily-deals-about-us/","The chain's daily-deals page lists Detroit only; nothing stated for the Jackson/Leoni store."),
 ("Cloud Cannabis, A New Standard (MI)","","Deal text is public, but the site terms forbid scraping / data-mining tools; not used."),
 ("North Coast Provisions (Arborside), Herbana, The Jungle House, Supergood (MI)","","No deal text found on the store's own pages (checked homepage and common deals paths)."),
 ("Zen Leaf MI, High Profile, Ascend, Gage, Common Citizen, Dunegrass, Pure Options, Joyology (MI); Curaleaf, RISE, Zen Leaf PA (multi-state)","","Deals load in the browser from a menu platform, or the site blocked our fetch; not scraped."),
 ("Greenhouse, Pinnacle, Stash, Pleasantrees, Herbana, Skymint (MI)","","Site timed out or returned an error to our fetch."),
 ("Puff, Breeze, Quality Roots (MI)","","Site returned a bot-check page instead of content."),
 ("Airfield Supply (CA), STIIIZY, Sweet Flower, MediThrive","","Deals page redirects to a menu platform (stiiizy.dispensary.shop / flowercompany.com) or is a pop-up only."),
 ("The Source, NuLeaf (NV); Wholesome, Dragonfly (UT); Apothecarium (NJ); Frostbite (MN)","","Product menu (prices per item from a menu platform), not a deals page."),
 ("Cultivate (NV)","https://cultivatelv.com/deals","Posts mix several days' deals in one block, so current vs expired can't be told apart reliably."),
 ("Thrive (DE/IL/MD/MA/OH), RISE (PA), Star Buds IL, Ritual (OK)","","Site returned 403 / no response to our fetch."),
 ("Rebud, SPARC, Moe Greens, LAX Cannabis Club (CA); Green Legacy, Don Fuego (DC); Waabigwan (MN); No Worries (SD); ANC (AZ)","","No deal text in the page's server HTML (loads in the browser) or only rewards text."),
 ("Aggregators: Weedmaps, Leafly, Dutchie, Jane, Calm Effect, PuffPrice, Leefii, Leafbuyer, findweedny, terptaxi","","Not used: partner/API only, terms bar scraping, or not the dispensary's own page."),
 ("Scarlet Reserve Room (NJ)","https://scarletreserveroom.com/35-off-cannabis-nj-fall-sale/","A sale blog post with no stated end date, so it can't be confirmed as current."),
 ("Planet 13 Illinois","","Old deals page now redirects to a separate site (planet13illinois.com); not checked yet."),
 ("Deals inbox","","Newsletters received so far had no usable deal text (sign-up confirmations)."),
]

def run():
    deals=[]; sources=[]
    for state,name,url,fn in SOURCES:
        s={"state":state,"name":name,"url":url,"robots":"","status":"","deals":0}
        try:
            if not robots_ok(url): s.update(robots="disallowed",status="skipped: robots.txt disallows this page"); sources.append(s); continue
            s["robots"]="allowed"; got=fn(url); kept=[]; per={}
            for d in got:                                  # cap per store so one big menu can't flood the tab
                per[d["store"]]=per.get(d["store"],0)+1
                if per[d["store"]]<=PER_STORE: kept.append(d)
            if len(kept)<len(got): s["more"]=len(got)-len(kept)
            got=kept
            s["deals"]=len(got); s["status"]="ok" if got else "ok, but no current deals parsed (none stated, or layout changed)"
            deals+=got
        except Exception as e: s["status"]=f"error: {e}"
        sources.append(s); time.sleep(0.7)
    by_chain={}; by_city={}; by_state={k:0 for k in sorted(ADULT_USE+MEDICAL)}
    for d in deals:
        by_chain[d["chain"]]=by_chain.get(d["chain"],0)+1
        by_state[d["state"]]=by_state.get(d["state"],0)+1
        for c in (d["cities"] or [""]):
            if c: by_city[f'{c}, {d["state"]}']=by_city.get(f'{c}, {d["state"]}',0)+1
    try: locations,geo=locate(deals)                    # store coordinates for the distance search (cached; see deals_geo.py)
    except Exception as e: locations,geo=[],{"error":str(e)}; [d.update(loc=[],geo="statewide") for d in deals]
    states=[{"code":k,"name":NAMES.get(k,k),"market":"adult-use + medical" if k in ADULT_USE else "medical only","deals":by_state.get(k,0),
             "sources":sum(1 for s in sources if s["state"]==k)} for k in sorted(by_state,key=lambda k:NAMES.get(k,k))]
    obj={"schema":"deals/3","test":True,"region":"United States (all legal markets)","checked":time.strftime("%Y-%m-%d %H:%M %Z"),
         "count":len(deals),"chains":len(by_chain),"states_with_deals":sum(1 for v in by_state.values() if v),
         "by_state":by_state,"by_chain":by_chain,"by_city":by_city,"states":states,"sources":sources,
         "not_used":[{"name":n,"url":u,"why":w} for n,u,w in NOT_USED],"deals":deals,
         "locations":locations,"geo":geo,
         "geo_note":"Store addresses come from each chain's own site and were geocoded with the US Census Bureau geocoder (OpenStreetMap Nominatim as a fallback). 'city' locations are the city centre where the exact store address isn't known. Distances are worked out in your browser; your location stays on your device.",
         "state_note":"Nebraska has a medical law but no operating dispensaries yet, so it is not listed. Georgia (low-THC oil) and Texas (TCUP) are limited medical programs.",
         "sponsored":{"example":True,"label":"EXAMPLE LAYOUT","items":[],
                      "note":"Paid placement slot (not live). Sponsored deals will always be labeled and kept separate from, never ranked above, the free list."},
         "disclaimer":"21+ only. For adults 21 and older (or registered medical patients). Deals change often and can differ by store: always confirm with the store before you go. Listed from each dispensary's own public page; not an endorsement."}
    save("deals.json",obj)
    os.makedirs(os.path.dirname(PUB),exist_ok=True); json.dump(obj,open(PUB,"w"),indent=1)
    print(f"deals: {len(deals)} deals in {obj['states_with_deals']} states from {sum(1 for s in sources if s['deals'])}/{len(sources)} sources")
    return obj
if __name__=="__main__": run()
