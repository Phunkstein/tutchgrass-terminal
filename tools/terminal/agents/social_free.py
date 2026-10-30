"""TREND SPOTTER, free sources (no X key needed). Same job as social_x.py: what PEOPLE say about cannabis for health and
growing (claims and questions, not evidence and not news). Read-only; it never posts, likes or replies.

Sources (all free, no account, no key):
  Bluesky  public AppView search, GET https://api.bsky.app/xrpc/app.bsky.feed.searchPosts (sort=top, last 7 days, lang=en)
  Reddit   one best-effort RSS read of r/MedicalMarijuana+microgrowery+CBD top-of-day threads (Reddit often rate-limits
           datacenter IPs; a failure is simply skipped)
Politeness: ~12 small requests per run, 1 s apart; agents_run.py runs this at most once an hour.
News-bot accounts and promo/spam posts are dropped so this stays distinct from News Desk.
Writes data/social.json in the shape the site already renders (posts, topic_counts, queries, source, generated).
If fewer than 4 usable posts are found, social.json is left unchanged (last good data is kept, the site shows its real age).
The X News block (news, news_generated) is kept only while it is under 72 h old."""
import json,os,re,sys,time,datetime as dt,urllib.request,urllib.parse,xml.etree.ElementTree as ET
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOC=os.path.join(ROOT,"data","social.json")
UA="tutchgrass-terminal/1.0 (Trend Spotter, read-only; +https://tutchgrass-terminal.onrender.com/terminal/)"
BSKY="https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
REDDIT="https://www.reddit.com/r/MedicalMarijuana+microgrowery+CBD/top/.rss?t=day&limit=15"
QH=["cannabis sleep","cannabis insomnia","cannabis pain","cannabis anxiety","cannabis PTSD","cannabis migraine","CBD sleep","CBD anxiety"]
QG=["trichomes","cannabis curing","cannabis harvest","terpenes cannabis grow"]
CANNA=re.compile(r"cannabis|\bcbd\b|\bthc\b|marijuana|\bweed\b|\bmmj\b|edible|gumm(y|ies)|\bindica|\bsativa|\bstrain|\bbud\b|\bbuds\b|\bkush\b",re.I)
HEALTH=[("PTSD / nightmares",r"\bptsd\b|nightmare|trauma"),("sleep",r"sleep|insomnia"),("pain",r"\bpain|chronic pain|neuropath"),("anxiety",r"anxi|panic|stress"),
        ("migraine",r"migraine|headache"),("arthritis",r"arthrit|joint pain"),("nausea",r"nausea|vomit|chemo"),("epilepsy",r"seizure|epilep"),("appetite",r"appetite")]
GROW=[("dry & cure",r"dry and cure|dry & cure|drying"),("cure length",r"\bcur(e|ed|ing)\b"),("jar humidity",r"humidity|boveda|\brh\b"),("harvest timing",r"harvest|\bchop"),
      ("trichomes",r"trichome"),("terpenes",r"terpene")]
SPAM=re.compile(r"\b(dm (me|for)|order now|discount|promo|coupon|% off|giveaways?|shop now|buy now|link in bio|free shipping|telegram|whatsapp|onlyfans|plug|use code)\b",re.I)
GROWCTX=re.compile(CANNA.pattern+r"|\bpot\b|\bgrow(ing|er|n)?\b|\bcrop\b|#cannabis|harvest",re.I)
NEWSY=re.compile(r"news|press|daily|times|journal|magazine|report|wire|today|media|\bmjbiz|norml|leafly|hightimes",re.I)
def get(url,timeout=20):
    return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json, application/atom+xml, */*"}),timeout=timeout).read()
def topic(text,table):
    hits=[n for n,rx in table if re.search(rx,text,re.I)]; return " / ".join(hits[:2]) if hits else None
def bsky(q,since):
    r=json.loads(get(BSKY+"?"+urllib.parse.urlencode(dict(q=q,sort="top",limit=25,lang="en",since=since))))
    return r.get("posts") or []
def reddit():
    ns={"a":"http://www.w3.org/2005/Atom"}; root=ET.fromstring(get(REDDIT)); out=[]
    for e in root.findall("a:entry",ns):
        ln=e.find("a:link",ns); cat=e.find("a:category",ns)
        out.append(dict(title=" ".join((e.findtext("a:title",namespaces=ns) or "").split()),url=ln.get("href") if ln is not None else "",
                        sub=(cat.get("label") if cat is not None else ""),date=(e.findtext("a:published",namespaces=ns) or e.findtext("a:updated",namespaces=ns) or "")[:16].replace("T"," ")))
    return out
def loc(iso):
    try: return time.strftime("%b %d %I:%M %p",time.localtime(dt.datetime.fromisoformat(iso.replace("Z","+00:00")).timestamp()))
    except Exception: return (iso or "")[:16]
def run():
    now=dt.datetime.now(dt.timezone.utc); since=(now-dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pool={}; read=0; errs=[]; qs=[("health",q) for q in QH]+[("grow",q) for q in QG]
    for aud,q in qs:
        try: rows=bsky(q,since)
        except Exception as e: errs.append(f"bluesky '{q}': {str(e)[:60]}"); rows=[]
        for p in rows:
            read+=1; a=p.get("author") or {}; h=a.get("handle",""); nm=a.get("displayName") or ""
            rec=p.get("record") or {}; txt=" ".join((rec.get("text") or "").split())
            if len(txt)<40 or SPAM.search(txt) or NEWSY.search(h+" "+nm) or not (CANNA if aud=="health" else GROWCTX).search(txt): continue
            if txt.count("http")>0 and len(re.sub(r"https?://\S+","",txt))<80: continue          # mostly a link share
            tp=topic(txt,HEALTH if aud=="health" else GROW)
            if not tp: continue
            uri=p.get("uri",""); rk=uri.rsplit("/",1)[-1]
            prev=pool.get(uri)
            if prev and prev["audience"]=="health": continue
            pool[uri]=dict(audience=aud,topic=tp,handle=h,platform="Bluesky",created=rec.get("createdAt") or p.get("indexedAt"),likes=p.get("likeCount",0) or 0,
                           reposts=p.get("repostCount",0) or 0,replies=p.get("replyCount",0) or 0,views=0,text=txt,url=f"https://bsky.app/profile/{h}/post/{rk}")
        time.sleep(1)
    threads=[]
    try: threads=[t for t in reddit() if t["title"] and not SPAM.search(t["title"])][:6]
    except Exception as e: errs.append(f"reddit: {str(e)[:60]}")
    rank=lambda v:-(v["likes"]*3+v["reposts"]*4+v["replies"]*2)
    seen=set(); dedup=[]
    for v in sorted(pool.values(),key=rank):                       # one post per author, so one account cannot fill the list
        if v["handle"] in seen: continue
        seen.add(v["handle"]); dedup.append(v)
    health=[v for v in dedup if v["audience"]=="health"][:11]; grow=[v for v in dedup if v["audience"]=="grow"][:5]
    for e in errs: print("  source issue:",e)
    if len(health)+len(grow)<4: print(f"Trend Spotter (free): only {len(health)+len(grow)} usable posts; social.json unchanged"); return None
    try: old=json.load(open(SOC))
    except Exception: old={}
    xnews=old.get("news") or []; ng=old.get("news_generated")
    try: fresh=ng and time.time()-time.mktime(time.strptime(ng[:16],"%Y-%m-%d %H:%M"))<72*3600
    except Exception: fresh=False
    posts=[dict(audience=v["audience"],topic=v["topic"],handle=v["handle"],platform=v["platform"],date=loc(v["created"]),likes=v["likes"],views=v["views"],text=v["text"],url=v["url"]) for v in health+grow]
    tc={}
    for v in health:
        for k in v["topic"].split(" / "): tc[k]=tc.get(k,0)+1
    gen=time.strftime("%Y-%m-%d %H:%M %Z")
    out=dict(agent="social",mode="free",generated=gen,platforms=["Bluesky"]+(["Reddit"] if threads else []),
             source=f"Bluesky public search (top posts, 7-day window, {read} read this run)"+(" + Reddit top threads today" if threads else ""),
             queries=len(qs)+(1 if threads else 0),query_list=[q for _,q in qs],topic_counts=tc,posts=posts,threads=threads,
             news=xnews if fresh else [],news_generated=ng if fresh else None)
    json.dump(out,open(SOC,"w"),indent=1)
    print(f"Trend Spotter (free): {len(posts)} posts ({len(health)} health, {len(grow)} grow) from {read} read; {len(threads)} Reddit threads"); return out
if __name__=="__main__":
    try: run()
    except Exception as e: print("Trend Spotter (free): unavailable:",e); sys.exit(0)   # keep last good social.json
