"""New studies, explained: per condition, the newest PubMed cannabinoid papers (by Entrez date), each with an
honest evidence grade and a plain-words summary built only from the paper's own record (no invented results).
Also builds the evidence scoreboard. Shared by build_terminal.py and tools/digest/send_digest.py.
Usage: python3 tools/terminal/newstudies.py [days=30]  -> data/new_studies.json"""
import json,os,re,sys,time,datetime as dt
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from pubmed_lib import esearch,efetch,ANIMAL
from harvest_conditions import C,CANN,CANNT
OUT=os.path.join(HERE,"data","new_studies.json")
LABELS={c[0]:c[1] for c in C}
LABELS.update(arthritis="Arthritis / inflammation")  # picker label; 'inflammation' kept as its own id too
TRIAL={"Randomized Controlled Trial","Clinical Trial","Clinical Trial, Phase I","Clinical Trial, Phase II","Clinical Trial, Phase III","Clinical Trial, Phase IV","Controlled Clinical Trial","Pragmatic Clinical Trial","Equivalence Trial"}
OBS={"Observational Study","Comparative Study","Multicenter Study","Validation Study","Twin Study"}
CELLS=re.compile(r"\b(in vitro|cell lines?|cultured cells|in silico|molecular docking)\b",re.I)
PLACEBO=re.compile(r"\b(placebo|sham|vehicle[- ]controlled|double[- ]blind)\b",re.I)
OBSW=re.compile(r"\b(cohort|cross-sectional|survey|registry|case-control|longitudinal|retrospective|prospective|database|questionnaire|claims data|records)\b",re.I)
HUMANS=re.compile(r"\b(patients|participants|adults|people|individuals|veterans|women|men|children|adolescents|respondents|users|subjects)\b",re.I)
# grade id -> (label, short honest caveat)
GRADES={
 "meta":("Meta-analysis / systematic review","Pools earlier studies. Only as strong as the studies it includes."),
 "rct":("Human RCT (placebo)","Randomized against placebo: the strongest single-study design. Check the size and dose."),
 "noplacebo":("Human trial, no placebo","No placebo group, so expectation alone can explain part of the effect."),
 "obs":("Observational","Shows a link, not cause and effect. People who choose cannabis can differ in other ways."),
 "mice":("Mice / rats only","Animal results often do not carry over to people."),
 "cells":("Cells only (lab dish)","Lab-dish results are an early lead, not evidence of a health effect."),
 "review":("Narrative review","An expert overview, not a systematic search. No new data."),
 "case":("Case report","One or a few patients. Useful for safety signals, not for effect."),
}
def grade(r):
    pt=set(r["pubtypes"]); txt=r["title"]+" "+r["abstract"]
    if pt&{"Meta-Analysis","Systematic Review"} or re.search(r"\b(systematic review|meta-analys[ie]s)\b",r["title"],re.I): return "meta"
    if pt&{"Case Reports"}: return "case"
    if pt&{"Review","Scoping Review"} or re.search(r"\b(review|overview|perspectives?|rationale|update)\b",r["title"],re.I): return "review"
    trial=bool(pt&TRIAL) or (re.search(r"\b(trial|randomi[sz]ed)\b",r["title"],re.I) and not ANIMAL.search(r["title"]))
    if trial: return "rct" if (re.search(r"\brandomi[sz]ed\b",txt,re.I) and PLACEBO.search(txt)) else "noplacebo"
    if ANIMAL.search(txt) and not HUMANS.search(r["title"]): return "cells" if (CELLS.search(txt) and not re.search(r"\b(mice|mouse|rats?|murine|rodents?)\b",txt,re.I)) else "mice"
    if pt&OBS or (HUMANS.search(txt) and OBSW.search(txt)): return "obs"
    return None   # cannot grade honestly -> left out
NUM=r"(\d{1,3}(?:,\d{3})+|\d+)"
def _n(txt,words):
    m=re.search(r"(?<![\d.,%])"+NUM+r"\s+(?:[A-Za-z-]+\s+)?(?:"+words+r")\b",txt,re.I)
    return m.group(1) if m and int(m.group(1).replace(",",""))>=5 else None
def _concl(r):
    for lab,t in r["abstract_sections"]:
        if lab and re.search(r"conclu|interpretation|implication",lab,re.I): return t
    s=re.split(r"(?<=[.!?])\s+",r["abstract"].strip()); return " ".join(s[-2:]) if s and s[0] else ""
def _clip(s,n=300):
    s=re.sub(r"\s+"," ",s).strip()
    if len(s)<=n: return s
    cut=s[:n]; k=max(cut.rfind(". "),cut.rfind("; ")); return (cut[:k+1] if k>120 else cut.rsplit(" ",1)[0]+" …")
def plain(r,g):
    txt=r["abstract"]
    if g=="meta": did="Researchers searched for and pooled the results of earlier studies"
    elif g in("rct","noplacebo"):
        n=_n(txt,"participants|patients|adults|people|individuals|veterans|subjects|women|men|children|volunteers")
        who=f"{n} people" if n else "people"
        did=f"A randomized trial in {who} compared a cannabis product with placebo" if g=="rct" else f"A trial in {who} tested a cannabis product without a placebo comparison"
    elif g=="obs": n=_n(txt,"participants|patients|adults|people|individuals|veterans|respondents|users|women|men"); did=f"Researchers looked at data on {n} people (nobody was assigned a treatment)" if n else "Researchers looked at existing data on people (nobody was assigned a treatment)"
    elif g=="mice": did="Experiments in mice or rats; no people were studied"
    elif g=="cells": did="Lab-dish experiments; no people or animals were dosed"
    elif g=="review": did="An expert overview of existing research"
    else: did="A report on one or a few patients"
    c=_clip(_concl(r))
    return dict(did=did+".",found=c,caveat=GRADES[g][1])
def _edat(d): return f"{d:%Y/%m/%d}"
def fetch(cids,since,until=None,per=25):
    """newest papers (Entrez date in [since,until]) per condition id; returns {cid:[paper]} and pmid->paper."""
    until=until or dt.date.today(); rng=f'("{_edat(since)}"[edat] : "{_edat(until)}"[edat])'
    ids={};counts={}
    for cid,lab,em,q,rx,goal,bg in C:
        if cid not in cids: continue
        n,l=esearch(f"{CANN} AND {q} AND {rng} AND english[la] NOT (letter[pt] OR comment[pt] OR editorial[pt] OR erratum[pt])",per,"pub_date")
        ids[cid]=l; counts[cid]=n
    allids=sorted({i for l in ids.values() for i in l}); recs={r["pmid"]:r for r in (efetch(allids) if allids else [])}
    out={};papers={}
    for cid,lab,em,q,rx,goal,bg in C:
        if cid not in ids: continue
        out[cid]=[]
        for i in ids[cid]:
            r=recs.get(i)
            if not r or not r["abstract"]: continue
            con=_concl(r)
            if not CANNT.search(r["title"]+" "+con) or not re.search(rx,r["title"]+" "+con,re.I): continue
            g=grade(r)
            if not g: continue
            if i not in papers:
                papers[i]=dict(pmid=i,title=r["title"],journal=r["journal"],date=r.get("edat") or r["date"],pubdate=r["date"],first_author=r["first_author"],doi=r["doi"],
                    grade=g,grade_label=GRADES[g][0],plain=plain(r,g),url=f"https://pubmed.ncbi.nlm.nih.gov/{i}/",conditions=[])
            papers[i]["conditions"].append(cid); out[cid].append(i)
    return out,papers,counts
STRENGTH={"strong":3,"moderate":2,"limited":1}
def scoreboard(recent,sci,new_by_cond,papers):
    """recent=conditions_recent.json, sci=scientist conditions list. Rank by background grade, then recent high-grade papers."""
    bg={c["id"]:c for c in (sci or [])}; rows=[]
    for cid,v in recent["conditions"].items():
        b=[bg[x] for x in v.get("background",[]) if x in bg]; ev=b[0]["evidence"] if b else None
        tags=[p["tag"] for p in v["cannabinoid"]]
        hi=sorted([p for p in v["cannabinoid"] if p["tag"] in("META-ANALYSIS","SR","RCT","GUIDELINE")],key=lambda p:p["date"],reverse=True)
        new=[papers[i] for i in new_by_cond.get(cid,[])]
        score=STRENGTH.get(ev,0)*10+min(5,sum(t in("META-ANALYSIS","RCT","GUIDELINE") for t in tags))+min(3,sum(p["grade"] in("rct","meta") for p in new))
        latest=hi[0] if hi else None
        rows.append(dict(id=cid,label=LABELS.get(cid,v["label"]),emoji=v["emoji"],evidence=ev or "not graded",sci=(v.get("background") or [None])[0],
            score=score,recent_total=v["cann_matches"],recent_high=dict(meta=sum(t in("META-ANALYSIS","SR") for t in tags),rct=tags.count("RCT"),guideline=tags.count("GUIDELINE")),
            new_30d=len(new),new_rct_meta_30d=sum(p["grade"] in("rct","meta") for p in new),new_mice_30d=sum(p["grade"] in("mice","cells") for p in new),
            latest=dict(title=latest["title"],date=latest["date"],tag=latest["tag"],journal=latest["journal"],url=f"https://pubmed.ncbi.nlm.nih.gov/{latest['pmid']}/",says=_clip(latest["conclusion"],240)) if latest else None))
    rows.sort(key=lambda r:(-r["score"],-r["new_30d"]))
    for i,r in enumerate(rows,1): r["rank"]=i
    return rows
def run(days=30):
    today=dt.date.today(); since=today-dt.timedelta(days=days)
    by,papers,counts=fetch({c[0] for c in C},since,today)
    wk=(today-dt.timedelta(days=7)).isoformat()
    newest={cid:max([papers[i]["date"] for i in l if papers[i]["date"]] or [None],key=lambda x:x or "") for cid,l in by.items()}
    out=dict(generated=time.strftime("%Y-%m-%d %H:%M %Z"),window=dict(start=since.isoformat(),end=today.isoformat(),days=days),source="NCBI PubMed E-utilities (Entrez date)",
        grades={k:dict(label=v[0],caveat=v[1]) for k,v in GRADES.items()},labels=LABELS,by_condition=by,pubmed_counts=counts,newest=newest,
        papers=sorted(papers.values(),key=lambda p:p["date"] or "",reverse=True),week_start=wk)
    if not papers: print("no papers; keeping previous file",file=sys.stderr); return None
    json.dump(out,open(OUT,"w"),indent=1); print("new studies:",len(papers),"papers;",{k:len(v) for k,v in by.items()},file=sys.stderr); return out
if __name__=="__main__": run(int(sys.argv[1]) if len(sys.argv)>1 else 30)
