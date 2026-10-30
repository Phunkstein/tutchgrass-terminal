"""Tutchgrass Labs refresh: runs agents, builds web/stats.json. No posting, no drafts."""
import json,os,sys,time,traceback
ROOT=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,ROOT); sys.path.insert(0,os.path.join(ROOT,"agents"))
LOG=os.path.join(ROOT,"logs/refresh.log"); os.makedirs(os.path.dirname(LOG),exist_ok=True)
feed=[]
def ev(agent,kind,what,reason): feed.append(dict(ts=time.strftime("%Y-%m-%d %H:%M:%S"),agent=agent,kind=kind,what=what,reason=reason))
def step(name,fn):
    t=time.time()
    try: r=fn(); return r,"ok",round(time.time()-t,1)
    except Exception as e:
        open(LOG,"a").write(traceback.format_exc()); ev(name,"ERROR",name+" failed",str(e)[:160]); return None,"unavailable",round(time.time()-t,1)
import lab, scientist, wire
L,ls,lt=step("lab",lab.run)
S,ss,st=step("scientist",lambda: scientist.run(live=True))
W,ws,wt=step("wire",wire.run)
try: SO=json.load(open(os.path.join(ROOT,"data/social.json"))); sos="ok"
except Exception: SO=None; sos="unavailable"
now=time.time(); A={}
if S:
    for c in S["conditions"]:
        ev("scientist","PICK",c["name"],f"{c['evidence']} evidence; top pick: {c['top_pick']} ({len(c['citations'])} citations, {c.get('new_papers_30d','n/a')} new PubMed papers in 30 d)")
    A["scientist"]=dict(name="Scientist",job="12 conditions → chemotype",badge="LIVE",rule="cite only retrieved PubMed records",
        status=f"{len(S['conditions'])} conditions · {sum(len(c['citations']) for c in S['conditions'])} citations · {len(S['dropped_unverified'])} unverified dropped",ts=now,secs=st)
else: A["scientist"]=dict(name="Scientist",job="12 conditions → chemotype",badge="DOWN",rule="",status="unavailable",ts=None)
if L:
    sp=next(c for c in L["compounds"] if c["id"]==L["spotlight_id"])
    ev("lab","SPOTLIGHT",sp["name"],f"daily rotation (day-of-year mod 8); evidence: {sp['evidence']}; {len(sp['citations'])} citations")
    A["lab"]=dict(name="Terpene & Cannabinoid Lab",job="daily compound spotlight",badge="UPDATE",rule="health angle + grow/preserve angle",status=f"today: {sp['name']} · {len(L['compounds'])} compounds in rotation",ts=now,secs=lt)
    A["holistic"]=dict(name="Holistic Pairings",job="lifestyle complements + cautions",badge="UPDATE",rule="guidelines, SRs, RCTs only",
        status=f"{len(L['holistic'])} conditions · {len(L['interactions'])} interaction/caution notes",ts=now,secs=lt)
    A["grower"]=dict(name="Grower Notes",job="genetics + cultivation factors",badge="UPDATE",rule="studies cited; anecdotal flagged",
        status=f"{len(L['factors'])-1} studied factors · 1 anecdotal practice flagged",ts=now,secs=lt)
    for i in L["interactions"]: ev("holistic","CAUTION",i["title"],i["text"][:170])
    for k,f in L["factors"].items(): ev("grower","ANECDOTAL" if f["anecdotal"] else "FACTOR",f["name"],("grower practice, no study retrieved" if f["anecdotal"] else f"{len(f['citations'])} horticulture citations")+": "+f["finding"][:120])
else:
    for k,n in (("lab","Terpene & Cannabinoid Lab"),("holistic","Holistic Pairings"),("grower","Grower Notes")): A[k]=dict(name=n,job="",badge="DOWN",rule="",status="unavailable",ts=None)
if W:
    ok=sum(s["status"]=="ok" for s in W["sources"])
    A["wire"]=dict(name="Research Wire",job="new papers + health/policy news",badge="LIVE",rule="US + international; health filter",
        status=f"{len(W['papers_medical'])} medical + {len(W['papers_cultivation'])} cultivation papers (14 d) · {len(W['news_us'])+len(W['news_intl'])} news · {ok}/{len(W['sources'])} sources ok",ts=now,secs=wt)
    for p in (W["papers_medical"][:3]+W["papers_cultivation"][:3]): ev("wire","PAPER",p["title"][:110],f"newest PubMed ({p['track']}); {p['journal']}"+("; animal/cell study" if p["preclinical"] else ""))
    for s in W["sources"]:
        if s["status"]!="ok": ev("wire","SKIP",s["source"],"source unavailable: "+s.get("error",""))
else: A["wire"]=dict(name="Research Wire",job="",badge="DOWN",rule="",status="unavailable",ts=None)
if SO:
    A["social"]=dict(name="Social",job="what people ask on X",badge="READ",rule="read-only; nothing posted",
        status=f"{len(SO['posts'])} posts · {len(SO['news'])} X News stories · cached {SO['generated']}",ts=now)
    ev("social","READ","X search (cached)",f"{SO['source']}; topics: "+", ".join(f"{k} {v}" for k,v in sorted(SO['topic_counts'].items(),key=lambda x:-x[1])))
else: A["social"]=dict(name="Social",job="",badge="DOWN",rule="",status="unavailable",ts=None)
order=["scientist","lab","holistic","wire","social","grower"]
stats=dict(product="Tutchgrass Labs",generated=time.strftime("%Y-%m-%d %H:%M:%S %Z"),generated_ts=now,disclaimer=scientist.DISCLAIMER,
    agents={k:A[k] for k in order},scientist=S,lab=L,wire=W,social=SO,feed=feed,
    source_status=dict(pubmed=ss,lab=ls,wire=ws,social=sos,wire_sources=(W or {}).get("sources",[])))
json.dump(stats,open(os.path.join(ROOT,"web/stats.json"),"w"),indent=1)
print("ok",{k:a["status"] for k,a in stats["agents"].items()})
