"""TREND SPOTTER (optional automation): reads recent public X posts about cannabis health and growing via the X API v2
recent-search endpoint (GET https://api.x.com/2/tweets/search/recent). Read-only: it never posts, likes or replies.

Needs ONE secret, set as a GitHub Actions repository secret and passed as an env var:
    X_BEARER_TOKEN   an X API app Bearer token whose plan includes v2 recent search
If X_BEARER_TOKEN is not set, this script prints "skipped" and changes nothing, so Trend Spotter keeps its last
hand-curated data (and honestly turns amber once that is older than 26 h).

Cost control: each query uses since_id, so a run only reads posts newer than the last run; the candidate pool lives in
data/social_pool.json (7-day window). data/social.json keeps the same shape the site already renders (posts, topic_counts,
queries, source, generated); the existing X News block (news, news_generated) is left as it was, with its real date."""
import json,os,re,sys,time,datetime as dt,urllib.request,urllib.parse,urllib.error
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOC=os.path.join(ROOT,"data","social.json"); POOL=os.path.join(ROOT,"data","social_pool.json")
API="https://api.x.com/2/tweets/search/recent"
Q={"health":'(cannabis OR CBD OR THC OR weed OR marijuana) (sleep OR insomnia OR pain OR anxiety OR PTSD OR migraine OR arthritis OR nausea OR seizures OR appetite) -is:retweet -is:reply -is:quote lang:en',
   "grow":'(terpenes OR trichomes OR curing OR "dry and cure" OR "jar humidity" OR "harvest window") (cannabis OR weed OR grow OR growers OR harvest) -is:retweet -is:reply lang:en'}
HEALTH=[("PTSD / nightmares",r"\bptsd\b|nightmare|trauma"),("sleep",r"sleep|insomnia"),("pain",r"\bpain|chronic pain|neuropath"),("anxiety",r"anxi|panic|stress"),
        ("migraine",r"migraine|headache"),("arthritis",r"arthrit|joint"),("nausea",r"nausea|vomit|chemo"),("epilepsy",r"seizure|epilep"),("appetite",r"appetite")]
GROW=[("dry & cure",r"dry and cure|dry & cure|drying"),("cure length",r"\bcur(e|ing)\b"),("jar humidity",r"humidity|boveda|\brh\b"),("harvest timing",r"harvest|chop"),
      ("trichomes",r"trichome"),("terpenes",r"terpene")]
SPAM=re.compile(r"\b(dm (me|for)|order now|discount|promo|coupon|% off|giveaway|shop now|buy now|link in bio|free shipping|telegram|whatsapp|onlyfans|plug)\b",re.I)
def _get(url,token,tries=4):
    for i in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"User-Agent":"tutchgrass-terminal/1"}),timeout=30).read())
        except urllib.error.HTTPError as e:
            if e.code==429 or e.code>=500:
                reset=e.headers.get("x-rate-limit-reset") if e.headers else None
                wait=max(1,min(60,int(reset)-int(time.time()))) if reset and reset.isdigit() else 5*(i+1)
                time.sleep(wait); continue
            raise RuntimeError(f"X API HTTP {e.code}: {e.read()[:200]!r}")
    raise RuntimeError("X API rate-limited; try next run")
def search(q,token,since_id=None,n=50):
    p=dict(query=q,max_results=n,**{"tweet.fields":"created_at,public_metrics,lang,author_id","expansions":"author_id","user.fields":"username"})
    if since_id: p["since_id"]=since_id
    else: p["start_time"]=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r=_get(API+"?"+urllib.parse.urlencode(p),token); users={u["id"]:u["username"] for u in (r.get("includes") or {}).get("users",[])}
    return r.get("data") or [],users,(r.get("meta") or {}).get("newest_id")
def topic(text,table):
    hits=[name for name,rx in table if re.search(rx,text,re.I)]; return " / ".join(hits[:2]) if hits else None
def run():
    token=os.environ.get("X_BEARER_TOKEN","").strip()
    if not token: print("Trend Spotter: skipped (X_BEARER_TOKEN not set); social.json unchanged"); return None
    try: pool=json.load(open(POOL))
    except Exception: pool={"since_id":{},"posts":{}}
    now=dt.datetime.now(dt.timezone.utc); read=0
    for aud,q in Q.items():
        rows,users,newest=search(q,token,pool["since_id"].get(aud))
        if newest: pool["since_id"][aud]=newest
        for t in rows:
            read+=1; txt=" ".join((t.get("text") or "").split())
            if SPAM.search(txt) or len(txt)<40: continue
            tp=topic(txt,HEALTH if aud=="health" else GROW)
            if not tp: continue
            m=t.get("public_metrics") or {}; h=users.get(t.get("author_id"),"")
            pool["posts"][t["id"]]=dict(audience=aud,topic=tp,handle=h,created=t.get("created_at"),likes=m.get("like_count",0),views=m.get("impression_count",0),
                                        text=re.sub(r"https://t\.co/\S+","",txt).strip(),url=f"https://x.com/{h or 'i/web'}/status/{t['id']}")
    cutoff=(now-dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pool["posts"]={k:v for k,v in pool["posts"].items() if (v.get("created") or "")>=cutoff}
    pool["updated"]=now.strftime("%Y-%m-%dT%H:%M:%SZ"); json.dump(pool,open(POOL,"w"),indent=1)
    rank=lambda v:-(v["likes"]*3+v["views"]/100)
    health=sorted([v for v in pool["posts"].values() if v["audience"]=="health"],key=rank)[:11]
    grow=sorted([v for v in pool["posts"].values() if v["audience"]=="grow"],key=rank)[:5]
    if len(health)+len(grow)<4: print(f"Trend Spotter: only {len(health)+len(grow)} usable posts in 7 days; social.json unchanged"); return None
    try: old=json.load(open(SOC))
    except Exception: old={}
    loc=lambda iso: time.strftime("%b %d %I:%M %p",time.localtime(dt.datetime.strptime(iso,"%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=dt.timezone.utc).timestamp())) if iso and "." in iso else (iso or "")
    posts=[dict(audience=v["audience"],topic=v["topic"],handle=v["handle"],date=loc(v["created"]),likes=v["likes"],views=v["views"],text=v["text"],url=v["url"]) for v in health+grow]
    tc={}
    for v in health:
        for k in v["topic"].split(" / "): tc[k]=tc.get(k,0)+1
    gen=time.strftime("%Y-%m-%d %H:%M %Z")
    out=dict(agent="social",generated=gen,source=f"X API v2 recent search (read {gen[:10]}, 7-day window, {read} new posts this run)"+(f"; X News read {old.get('news_generated')}" if old.get("news") else ""),
             queries=list(Q.values())+([q for q in old.get("queries",[]) if str(q).startswith("search_news")][:1]),topic_counts=tc,posts=posts,
             news=old.get("news",[]),news_generated=old.get("news_generated"))
    json.dump(out,open(SOC,"w"),indent=1); print(f"Trend Spotter: {len(posts)} posts ({len(health)} health, {len(grow)} grow); read {read} new"); return out
if __name__=="__main__":
    try: run()
    except Exception as e: print("Trend Spotter: unavailable:",e); sys.exit(0)   # keep last good social.json
