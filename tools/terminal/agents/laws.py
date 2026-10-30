"""Policy Watch: laws that just took effect or take effect soon.
Detection, run hourly (agents_run.py hourly):
 1. Curated, hand-verified items (laws_curated.py). Each has an official source and an effective date.
 2. Federal Register API (free, no key): final RULE documents whose effective date is within
    -30..+60 days and whose title or abstract mentions cannabis/marijuana/hemp/THC. These are added
    automatically with the official federalregister.gov link.
 3. Source link check (once a day): an item whose official link returns 404/410 is hidden until fixed.
 4. News leads: News Desk headlines (data/news.json) that say a law "takes effect" are saved as
    unverified leads. They are counted in the agent log, never shown as items.
Writes tools/terminal/data/laws.json. On a failed fetch, the last good data is kept.
Status (in effect / taking effect soon / alert) is computed from the date at every site build (status())."""
import datetime as dt,json,re,subprocess,sys,time,urllib.parse,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import curl,save,load,UA
import laws_curated
PAST,AHEAD,ALERT=30,60,7          # window: effective in the last 30 days or next 60; alert if it took effect in the last 7
CANN=re.compile(r"\b(cannabis|marijuana|marihuana|hemp|tetrahydrocannabinol|THC|cannabinoids?|cannabidiol)\b",re.I)
EFFECT=re.compile(r"\b(takes? effect|took effect|goes? into effect|went into effect|now in effect|in effect (?:on|today|as of)|effective (?:today|on|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|kicks? in|begins? (?:today|on))\b",re.I)
def today():
    try:
        from zoneinfo import ZoneInfo; return dt.datetime.now(ZoneInfo("America/New_York")).date()   # Actions runs in UTC; dates are US Eastern
    except Exception: return dt.date.today()
def fed_register(t=None):
    t=t or today(); lo=(t-dt.timedelta(days=PAST)).isoformat(); hi=(t+dt.timedelta(days=AHEAD)).isoformat()
    q=[("conditions[term]","cannabis | marijuana | marihuana | hemp | tetrahydrocannabinol"),("conditions[type][]","RULE"),
       ("conditions[effective_date][gte]",lo),("conditions[effective_date][lte]",hi),("per_page","100"),("order","newest")]
    q+=[("fields[]",f) for f in ("title","abstract","effective_on","html_url","document_number","agencies","citation","publication_date")]
    j=json.loads(curl("https://www.federalregister.gov/api/v1/documents.json?"+urllib.parse.urlencode(q),timeout=40))
    out=[]
    for d in j.get("results",[]):
        blob=(d.get("title") or "")+" "+(d.get("abstract") or "")
        if not CANN.search(blob) or not d.get("effective_on"): continue   # the term search hits full text; keep only real cannabis rules
        ag=", ".join(a.get("name","") for a in d.get("agencies") or [] if a.get("name"))
        ab=re.sub(r"\s+"," ",d.get("abstract") or "").strip()
        out.append(dict(id="fr-"+d["document_number"],where="Federal",code="US",effective=d["effective_on"],kind="Federal rule",
            title=d["title"],plain=(ab[:300]+("…" if len(ab)>300 else "")) or d["title"],cite=d.get("citation") or "FR Doc. "+d["document_number"],
            agency=ag,sources=[dict(label="Federal Register "+(d.get("citation") or d["document_number"]),url=d["html_url"])],
            auto="federalregister.gov",verified_on=t.isoformat()))
    return out
def http_status(url):
    r=subprocess.run(["curl","-s","-o","/dev/null","-L","-m","20","-A",UA,"-w","%{http_code}",url],capture_output=True,text=True)
    try: return int(r.stdout.strip() or 0)
    except ValueError: return 0
def link_check(items,prev):
    """Daily. 404/410 = broken (item hidden). 401/403/429/000 = the site blocks automated checks; treated as OK (checked by hand)."""
    if prev and prev.get("checked") and time.time()-prev.get("checked_ts",0)<20*3600: return prev
    res={}
    for it in items:
        for s in it["sources"]:
            if s["url"] in res: continue
            c=http_status(s["url"]); res[s["url"]]=dict(code=c,state="broken" if c in(404,410) else "ok" if 200<=c<400 else "blocked")
    return dict(checked=time.strftime("%Y-%m-%d %H:%M %Z"),checked_ts=time.time(),urls=res)
def news_leads(items):
    N=load("news.json") or {}; seen=set(); leads=[]
    try: from news import STATE_RE
    except Exception: STATE_RE=re.compile(r"$^")
    for cat in (N.get("by_category") or {}).values():
        for i in cat:
            t=i.get("title") or ""; blob=t+" "+(i.get("summary") or "")
            if i.get("link") in seen or not EFFECT.search(blob) or not CANN.search(blob): continue
            seen.add(i.get("link")); st=sorted(set(STATE_RE.findall(t)))
            covered=any(x["where"] in st for x in items) if st else False
            leads.append(dict(title=t,link=i.get("link"),source=i.get("source"),date=i.get("date"),states=st,covered=covered))
    return leads[:40]
def status(item,t=None):
    """'alert' (took effect 0..7 days ago), 'in_effect' (0..30 days ago), 'upcoming' (1..60 days ahead), or None."""
    t=t or today(); d=(dt.date.fromisoformat(item["effective"][:10])-t).days
    if -ALERT<=d<=0: return "alert"
    if -PAST<=d<0: return "in_effect"
    if 0<d<=AHEAD: return "upcoming"
    return None
def assemble(L=None,t=None):
    """Build the terminal.json 'laws' block. Works even before the agent has run (curated items only)."""
    t=t or today(); L=L if L is not None else (load("laws.json") or {})
    urls=((L.get("links") or {}).get("urls")) or {}
    items=[dict(x) for x in laws_curated.ITEMS]+[dict(x) for x in (L.get("federal_register") or []) if x["id"] not in {c["id"] for c in laws_curated.ITEMS}]
    shown=[];broken=[]
    for it in items:
        s=status(it,t)
        if not s: continue
        if it["sources"] and all((urls.get(x["url"]) or {}).get("state")=="broken" for x in it["sources"]): broken.append(it["id"]); continue
        d=(dt.date.fromisoformat(it["effective"][:10])-t).days
        it.update(status="in_effect" if s=="alert" else s,alert=(s=="alert"),days=d); shown.append(it)
    shown.sort(key=lambda x:(x["status"]!="in_effect",-x["days"] if x["status"]=="in_effect" else x["days"],x["where"]))
    now=[x for x in shown if x["status"]=="in_effect"]; soon=[x for x in shown if x["status"]=="upcoming"]
    leads=L.get("leads") or []
    return dict(as_of=t.isoformat(),window=dict(past_days=PAST,ahead_days=AHEAD,alert_days=ALERT),
        in_effect=now,upcoming=soon,
        alerts=[dict(id=x["id"],where=x["where"],title=x["title"],effective=x["effective"],url=x["sources"][0]["url"]) for x in now if x["alert"]],
        counts=dict(in_effect=len(now),upcoming=len(soon),alerts=sum(1 for x in now if x["alert"]),federal_register=len(L.get("federal_register") or []),
                    leads=len(leads),leads_unmatched=sum(1 for x in leads if not x["covered"]),hidden_broken=len(broken)),
        checked=L.get("generated"),fr_status=L.get("fr_status"),
        method="Hand-verified official sources plus the Federal Register API, checked hourly. Status is computed from each effective date.",
        note="Not legal advice. Each item links to the official statute, rule, regulator or legislature page.")
def run():
    prev=load("laws.json") or {}; out=dict(prev); out.pop("generated",None)
    try: out["federal_register"]=fed_register(); out["fr_status"]="ok"
    except Exception as e: out["fr_status"]=f"unavailable ({e}); kept last good"; out.setdefault("federal_register",[])
    allitems=laws_curated.ITEMS+out["federal_register"]
    try: out["links"]=link_check([x for x in allitems if status(x) or dt.date.fromisoformat(x["effective"][:10])>today()],prev.get("links"))
    except Exception as e: out.setdefault("links",prev.get("links") or {})
    try: out["leads"]=news_leads(allitems)
    except Exception: out.setdefault("leads",[])
    out["curated"]=len(laws_curated.ITEMS)
    save("laws.json",out); a=assemble(out)
    print("laws:",a["counts"])
if __name__=="__main__": run()
