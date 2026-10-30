"""News Wire fast loop (GitHub Actions, every 5 min). Re-reads the public news RSS feeds, finds items never seen before,
and only then updates the site data, so Render only redeploys when there is genuinely new news.
Writes:
  tools/terminal/data/news.json            full News agent output
  tools/terminal/data/news_seen.json       every item key ever seen, with first_seen (pruned after 21 days)
  public/terminal/data/breaking.json       machine-readable list of items first seen in the last 48 h (for a later alert)
  public/terminal/data/terminal.json       only its "news" block is patched (other agents untouched)
Prints new=<n> and appends it to $GITHUB_OUTPUT. Exit code 0 even with no news; nothing is posted or emailed."""
import json,os,re,sys,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,"agents"))
PUB=os.path.join(HERE,"..","..","public","terminal","data")
SEEN=os.path.join(HERE,"data","news_seen.json"); BRK=os.path.join(PUB,"breaking.json"); TERM=os.path.join(PUB,"terminal.json")
KEEP_DAYS=21; WINDOW_H=48; GRACE_H=3   # an unseen item counts as breaking only if its feed pubDate is no older than the previous check minus 3 h
# (Google News rotates older stories in and out of its top results; those are recorded as seen, not breaking)
key=lambda t: re.sub(r"\W","",(t or "").lower())[:60]
iso=lambda ts: time.strftime("%Y-%m-%dT%H:%M:%S%z",time.localtime(ts))
def jload(p,d):
    try: return json.load(open(p))
    except Exception: return d
def news_block(N):  # same shape build_terminal.py writes
    cats={k:[dict(title=i["title"],link=i["link"],source=i["source"],date=i["date"],summary=(i.get("summary") or "")[:220]) for i in v[:6]] for k,v in N["by_category"].items()}
    return dict(generated=N["generated"],total=N["total"],sources=N["sources"],by_category=cats)
def out(n):
    print(f"new={n}")
    if os.environ.get("GITHUB_OUTPUT"): open(os.environ["GITHUB_OUTPUT"],"a").write(f"new={n}\n")
def main():
    import news
    seen=jload(SEEN,None); baseline=seen is None; seen=seen or {"items":{}}
    old_news=jload(os.path.join(HERE,"data","news.json"),None)
    N=news.run(); now=time.time()
    if not any(s["status"]=="ok" for s in N["sources"]):
        if old_news: json.dump(old_news,open(os.path.join(HERE,"data","news.json"),"w"),indent=1)  # keep last good copy
        print("all news sources unavailable; nothing changed"); return out(0)
    last=seen.get("last_run_ts") or now; new=[]
    for i in N.get("all",[]):
        k=key(i["title"])
        if not k or k in seen["items"]: continue
        rec=dict(id=k,title=i["title"],link=i["link"],source=i["source"],category=i["category"],is_law=i["is_law"],states=i["states"],
                 published=iso(i["ts"]) if i["ts"] else None,published_ts=i["ts"] or None,first_seen=iso(now),first_seen_ts=round(now),baseline=baseline or not i["ts"] or i["ts"]<last-GRACE_H*3600)
        seen["items"][k]=rec; new.append(rec)
    seen["items"]={k:v for k,v in seen["items"].items() if now-v["first_seen_ts"]<KEEP_DAYS*86400}
    seen["updated"]=iso(now); seen["last_run_ts"]=round(now)
    json.dump(seen,open(SEEN,"w"),indent=1)
    real=[r for r in new if not r["baseline"]]
    print(f"unseen items: {len(new)}, breaking: {len(real)}"+(" (baseline run: existing items recorded as seen)" if baseline else ""))
    recent=sorted([v for v in seen["items"].values() if not v.get("baseline") and now-v["first_seen_ts"]<WINDOW_H*3600],key=lambda v:-v["first_seen_ts"])[:100]
    json.dump(dict(agent="news-wire",about="Items the News Wire saw for the first time in the last 48 hours, newest first. first_seen = when our 5-minute check first saw it; published = the feed's own pubDate. Older stories that a feed re-surfaces are not listed.",
                   generated=iso(now),generated_ts=round(now),window_hours=WINDOW_H,check_every_minutes=5,
                   sources=[dict(source=s["source"],status=s["status"],items=s.get("items",0)) for s in N["sources"]],
                   new_this_run=len(real),items=[{k:v for k,v in r.items() if k!="baseline"} for r in recent]),open(BRK,"w"),indent=1)
    if real:
        T=jload(TERM,None)
        if T is not None: T["news"]=news_block(N); json.dump(T,open(TERM,"w"),separators=(",",":"))
    out(len(real))
if __name__=="__main__": main()
