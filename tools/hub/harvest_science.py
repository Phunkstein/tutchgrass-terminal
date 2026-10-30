"""Science feed: recent cannabis RCTs / systematic reviews / meta-analyses from PubMed.
Writes data/hub/science.json. Hand-written takeaways (data/hub/takeaways.json) are used when present;
otherwise the authors' own conclusion sentence is shown, labeled as such."""
import json, os, re, sys, time
from pubmed_lib import esearch, efetch, dp, window, evidence
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANN='(cannabis[ti] OR cannabinoid*[ti] OR cannabidiol[ti] OR THC[ti] OR tetrahydrocannabinol[ti] OR marijuana[ti] OR hemp[ti] OR dronabinol[ti] OR nabiximols[ti] OR cannabigerol[ti] OR nabilone[ti])'
TYPES='(randomized controlled trial[pt] OR systematic review[pt] OR meta-analysis[pt])'
def conclusion(r):
    for lab,txt in r.get("abstract_sections",[]):
        if lab and re.search(r'conclu|interpretation',lab,re.I): return txt
    secs=[t for l,t in r.get("abstract_sections",[]) if not (l and re.search(r"fund|regist|trial|keyword|copyright",l,re.I))]
    s=re.split(r"(?<=[.!?])\s+",(secs[-1] if secs else r["abstract"]).strip()); return " ".join(s[-2:]) if s else ""
def kind(r):
    p=r["pubtypes"]
    if "Meta-Analysis" in p: return "Meta-analysis"
    if "Systematic Review" in p: return "Systematic review"
    if "Randomized Controlled Trial" in p: return "Randomized trial"
    return "Study"
def run(n=80):
    a,b=window(18); q=f"{CANN} AND {TYPES} AND {dp(18)} AND english[la]"
    cnt,ids=esearch(q,n,"pub_date")
    TK=json.load(open(ROOT+"/data/hub/takeaways.json")) if os.path.exists(ROOT+"/data/hub/takeaways.json") else {}
    ids=ids+[k for k in TK if k not in ids]; recs=efetch(ids)
    recs=[r for r in recs if r["date"]>=a.isoformat()[:7] or r["pmid"] in TK]
    items=[]
    for r in recs:
        t=TK.get(r["pmid"])
        if t and t.get("skip"): continue
        items.append(dict(pmid=r["pmid"],title=r["title"],journal=r["journal"],date=r["date"],kind=kind(r),doi=r["doi"],
            first_author=r["first_author"],takeaway=(t or {}).get("takeaway"),topic=(t or {}).get("topic"),
            authors_conclusion=conclusion(r)[:400],curated=bool(t)))
    items.sort(key=lambda x:x["date"],reverse=True)
    sow=next((i for i in items if i["curated"] and TK[i["pmid"]].get("sow")),None) or next((i for i in items if i["curated"]),None)
    out=dict(window=dict(start=a.isoformat(),end=b.isoformat()),generated=time.strftime("%Y-%m-%d %H:%M %Z"),query=q,total_matches=cnt,
             source="NCBI PubMed E-utilities",items=items,study_of_week=sow)
    json.dump(out,open(ROOT+"/data/hub/science.json","w"),indent=1)
    json.dump({r["pmid"]:r for r in recs},open(ROOT+"/data/hub/science_records.json","w"))
    print(f"science: {cnt} matches, {len(items)} items, curated {sum(i['curated'] for i in items)}",file=sys.stderr); return out
if __name__=="__main__": run()
