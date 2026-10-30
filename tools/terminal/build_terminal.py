"""Tutchgrass Labs terminal build: runs the original Cannabis Market Terminal agents and writes
public/terminal/data/terminal.json for the static site. A failing source is written as 'unavailable'
(never filled with placeholder numbers). Usage: python3 tools/terminal/build_terminal.py [--no-refresh]"""
import json,os,subprocess,sys,time,traceback
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,"agents"))
OUT=os.path.join(HERE,"..","..","public","terminal","data","terminal.json")
def safe(fn,name):
    try: return fn()
    except Exception as e:
        open(os.path.join(HERE,"logs","build.log"),"a").write(traceback.format_exc()); print(name,"unavailable",e); return None
if "--no-refresh" not in sys.argv:
    subprocess.run([sys.executable,os.path.join(HERE,"refresh.py")],check=False)   # scientist (live PubMed counts), lab, wire (+news)
    import market,prices
    safe(market.run,"market"); safe(prices.run,"prices")
J=lambda p: safe(lambda: json.load(open(os.path.join(HERE,p))),p)
S=J("web/stats.json") or {}; M=J("data/market.json"); P=J("data/prices.json"); N=J("data/news.json"); R=J("data/conditions_recent.json")
# attach recent (2025-2026) PubMed studies to each Scientist condition via the hub's background mapping
recent={}
if R:
    for k,v in R["conditions"].items():
        for b in v.get("background",[]): recent[b]=dict(window=R["window"],generated=R["generated"],matches=v["cann_matches"],studies=v["cannabinoid"][:4])
if S.get("scientist"):
    for c in S["scientist"]["conditions"]: c["recent"]=recent.get(c["id"])
def news_block(N):
    if not N: return None
    cats={k:[dict(title=i["title"],link=i["link"],source=i["source"],date=i["date"],summary=i["summary"][:220]) for i in v[:6]] for k,v in N["by_category"].items()}
    return dict(generated=N["generated"],total=N["total"],sources=N["sources"],by_category=cats)
def mstat(M): return None if not M else M
out=dict(product="Tutchgrass Labs",built=time.strftime("%Y-%m-%d %H:%M:%S %Z"),built_ts=time.time(),
    disclaimer="Research summary, not medical advice. Studies suggest; they do not prove. Talk to a doctor.",
    agents=S.get("agents"),scientist=S.get("scientist"),lab=S.get("lab"),wire=S.get("wire"),social=S.get("social"),feed=(S.get("feed") or [])[:40],
    source_status=S.get("source_status"),market=M,prices=P,news=news_block(N))
import build_findings
out['findings']=safe(build_findings.build,'findings')
# social.json is read by refresh.py; make sure the newest copy (with refreshed X News) is used
so=J("data/social.json")
if so: out["social"]=so
os.makedirs(os.path.dirname(OUT),exist_ok=True); json.dump(out,open(OUT,"w"),separators=(",",":"))
print("wrote",os.path.normpath(OUT),os.path.getsize(OUT),"bytes")
