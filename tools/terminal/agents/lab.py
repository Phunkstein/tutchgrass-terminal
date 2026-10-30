"""LAB / HOLISTIC / GROWER agent: joins curated text with PubMed metadata; refuses any PMID not retrieved."""
import json, os, sys, time, datetime
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(ROOT,"agents"))
import lab_curated as L
def index():
    a={}
    for f in ("cache/lab.json","cache/pubmed.json"):
        d=json.load(open(os.path.join(ROOT,f)))
        for k,v in d.items():
            if k=="_meta": continue
            for r in v.get("records",[]): a[r["pmid"]]=r
    return a
def run():
    a=index(); dropped=[]
    def cites(lst):
        out=[]
        for p,t in lst:
            r=a.get(p)
            if not r: dropped.append(p); continue
            out.append(dict(pmid=p,type=t,title=r["title"],journal=r["journal"],year=r["year"],first_author=r["first_author"],doi=r.get("doi"),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{p}/",doi_url=(f"https://doi.org/{r['doi']}" if r.get("doi") else None)))
        return out
    factors={k:dict(id=k,name=v["name"],finding=v["finding"],citations=cites(v["cites"]),
                    anecdotal=not v["cites"],source=(dict(label=v["source"][0],url=v["source"][1]) if v.get("source") else None)) for k,v in L.FACTORS.items()}
    comps=[dict({k:v for k,v in c.items() if k not in("cites",)},citations=cites(c["cites"])) for c in L.COMPOUNDS]
    doy=datetime.date.today().timetuple().tm_yday; spot=comps[doy%len(comps)]
    hol={k:dict(pairs=v["pairs"],citations=cites(v["cites"])) for k,v in L.HOLISTIC.items()}
    inter=[dict(title=i["title"],text=i["text"],citations=cites(i["cites"])) for i in L.INTERACTIONS]
    grow={k:dict(v,factor_names=[factors[f]["name"] for f in v["factors"]]) for k,v in L.GROWER.items()}
    res=dict(agent="lab",generated=time.strftime("%Y-%m-%d %H:%M %Z"),spotlight_id=spot["id"],spotlight_rule="rotates daily (day-of-year mod 8)",
             compounds=comps,entourage=dict(text=L.ENTOURAGE["text"],citations=cites(L.ENTOURAGE["cites"])),
             factors=factors,holistic=hol,interactions=inter,grower=grow,dropped_unverified=sorted(set(dropped)))
    json.dump(res,open(os.path.join(ROOT,"data/lab.json"),"w"),indent=1); return res
if __name__=="__main__":
    r=run(); print("spotlight",r["spotlight_id"],"dropped",r["dropped_unverified"])
