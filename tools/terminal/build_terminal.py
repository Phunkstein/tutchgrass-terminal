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
# ---- new studies explained + evidence scoreboard + My Condition data
import newstudies
if "--no-refresh" not in sys.argv or not os.path.exists(os.path.join(HERE,"data","new_studies.json")): safe(newstudies.run,"newstudies")
NS=J("data/new_studies.json")
if NS and R:
    wk=NS["week_start"]
    out["newstudies"]=dict(generated=NS["generated"],window=NS["window"],source=NS["source"],grades=NS["grades"],labels=NS["labels"],by_condition=NS["by_condition"],
        newest=NS["newest"],pubmed_counts=NS["pubmed_counts"],week_start=wk,papers=NS["papers"],
        week={k:sum(1 for i in v if (next((p for p in NS["papers"] if p["pmid"]==i),{}).get("date") or "")>=wk) for k,v in NS["by_condition"].items()})
    pmap={p["pmid"]:p for p in NS["papers"]}
    out["scoreboard"]=safe(lambda: newstudies.scoreboard(R,(S.get("scientist") or {}).get("conditions"),NS["by_condition"],pmap),"scoreboard")
    # compact per-condition data for /terminal/my/ (recent graded studies, holistic counts)
    out["conds"]={k:dict(label=newstudies.LABELS.get(k,v["label"]),emoji=v["emoji"],sci=(v.get("background") or [None])[0],matches=v["cann_matches"],
        recent=[dict(pmid=x["pmid"],title=x["title"],journal=x["journal"],date=x["date"],tag=x["tag"],first_author=x["first_author"],says=newstudies._clip(x.get("conclusion") or "",260)) for x in v["cannabinoid"][:5]],
        newest=NS["newest"].get(k),checked=NS["generated"]) for k,v in R["conditions"].items()}
    # Scientist "Last updated" badge: newest new-study date among hub conditions mapped to that background condition
    if S.get("scientist"):
        for c in S["scientist"]["conditions"]:
            ds=[NS["newest"].get(k) for k,v in R["conditions"].items() if c["id"] in v.get("background",[])]
            ds=[x for x in ds if x]; c["last_updated"]=max(ds) if ds else None; c["checked"]=NS["generated"]
# ---- Dec 11, 2026 federal hemp THC rule tracker (CRS IF13136 / IN12620)
out["dec11"]=dict(deadline="2026-12-11T00:00:00-05:00",synthetic="2026-11-12T00:00:00-05:00",
    headline="Max 0.4 mg total THC per container for final hemp products.",
    dates=[dict(date="2025-11-12",text="P.L. 119-37 (FY2026 Agriculture appropriations) rewrites the federal hemp definition, effective in 365 days."),
           dict(date="2026-09-02",text="Continuing resolution P.L. 119-103 delays most of it to Dec 11, 2026."),
           dict(date="2026-11-12",text="Cannabinoids not naturally produced by the plant (certain synthetics) stop counting as hemp."),
           dict(date="2026-12-11",text="Total THC (incl. THCA) must be 0.3% or less by dry weight; final products over 0.4 mg combined total THC per container are excluded.")],
    sources=[dict(label="CRS IF13136",url="https://www.congress.gov/crs-product/IF13136"),dict(label="CRS IN12620",url="https://www.congress.gov/crs-product/IN12620"),
             dict(label="7 U.S.C. 1639o",url="https://uscode.house.gov/us/usc/119-136/t7/s1639o/")],
    note="Not legal advice. Dates from the Congressional Research Service; state rules differ.")
import build_pages
safe(build_pages.build,'pages')
# social.json is read by refresh.py; make sure the newest copy (with refreshed X News) is used
so=J("data/social.json")
if so: out["social"]=so
os.makedirs(os.path.dirname(OUT),exist_ok=True); json.dump(out,open(OUT,"w"),separators=(",",":"))
print("wrote",os.path.normpath(OUT),os.path.getsize(OUT),"bytes")
