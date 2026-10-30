"""Conditions harvest: for each condition, recent (last 18 months) PubMed cannabinoid trials/reviews and recent
holistic (exercise, diet, mind-body, CBT...) systematic reviews/guidelines. Writes tools/terminal/data/conditions_recent.json (was data/hub/conditions.json in the original box layout).
Background evidence (older, dated) comes from the Cannabis Market Terminal scientist/lab data copied to
data/hub/background.json (originally PubMed-verified, generated 2026-10-28)."""
import json,os,re,sys,time
from pubmed_lib import esearch,efetch,dp,window,evidence
ROOT=os.path.dirname(os.path.abspath(__file__))   # tools/terminal
SKIP=os.path.join(ROOT,'data','conditions_skip.json'); OUTF=os.path.join(ROOT,'data','conditions_recent.json')
CANN='(cannabis[tiab] OR cannabinoid*[tiab] OR cannabidiol[tiab] OR THC[tiab] OR tetrahydrocannabinol[tiab] OR marijuana[tiab] OR dronabinol[tiab] OR nabiximols[tiab] OR nabilone[tiab] OR cannabigerol[tiab])'
CANNT=re.compile(r'cannab|THC|tetrahydrocannab|marijuana|dronabinol|nabiximol|nabilone|CBD|CBG|hemp',re.I)
TYPES='(randomized controlled trial[pt] OR clinical trial[pt] OR systematic review[pt] OR meta-analysis[pt])'
HOL='(exercise[ti] OR "physical activity"[ti] OR yoga[ti] OR mindfulness[ti] OR meditation[ti] OR "cognitive behavioral"[ti] OR "cognitive behavioural"[ti] OR CBT*[ti] OR diet*[ti] OR nutrition*[ti] OR acupuncture[ti] OR "tai chi"[ti] OR massage[ti] OR "non-pharmacological"[ti] OR nonpharmacological[ti] OR lifestyle[ti] OR "sleep hygiene"[ti] OR ginger[ti] OR "physical therapy"[ti] OR physiotherapy[ti])'
HTYPES='(systematic review[pt] OR meta-analysis[pt] OR practice guideline[pt] OR guideline[pt])'
C=[# id,label,emoji,pubmed condition terms,title regex,terps goal,background ids
('sleep','Sleep','😴','(sleep[tiab] OR insomnia[tiab])',r'sleep|insomnia','sleep',['insomnia']),
('pain','Chronic pain','🩹','("chronic pain"[tiab] OR "neuropathic pain"[tiab] OR neuropath*[tiab] OR "pain"[ti])',r'pain|neuropath','pain',['chronic_neuropathic_pain']),
('anxiety','Anxiety','🫧','(anxiety[tiab] OR anxious[tiab])',r'anxi','anxiety',['anxiety']),
('mood','Mood & depression','🌤️','(depression[tiab] OR depressive[tiab] OR mood[ti])',r'depress|mood','mood',[]),
('ptsd','PTSD','🕊️','(PTSD[tiab] OR posttraumatic[tiab] OR "post-traumatic"[tiab])',r'PTSD|post-?traumatic','',['ptsd']),
('arthritis','Arthritis','🦴','(arthritis[tiab] OR osteoarthritis[tiab])',r'arthrit','inflammation',['arthritis']),
('inflammation','Inflammation','🔥','(inflammation[ti] OR inflammatory[ti] OR "C-reactive"[tiab] OR cytokine*[ti])',r'inflamm|cytokine|C-reactive','inflammation',[]),
('nausea','Nausea & vomiting','🌊','(nausea[tiab] OR vomiting[tiab] OR emesis[tiab] OR antiemetic[tiab])',r'nausea|vomit|emesis|emetic','nausea',['cinv']),
('appetite','Appetite & weight loss','🍽️','(appetite[tiab] OR cachexia[tiab] OR anorexia[tiab])',r'appetite|cachexi|anorexi|weight','appetite',['appetite_cachexia']),
('focus','Focus & memory','🎯','(cognition[ti] OR cognitive[ti] OR memory[ti] OR attention[ti] OR ADHD[ti])',r'cogni|memory|attention|ADHD','focus',[]),
('fibromyalgia','Fibromyalgia','🧶','(fibromyalgia[tiab])',r'fibromyalg','',['fibromyalgia']),
('ms','MS spasticity','🧠','("multiple sclerosis"[tiab] OR spasticity[tiab])',r'sclerosis|spastic','',['ms_spasticity']),
('epilepsy','Epilepsy','⚡','(epilep*[tiab] OR seizure*[tiab] OR Dravet[tiab] OR Lennox[tiab])',r'epilep|seizure|Dravet|Lennox','',['epilepsy']),
('migraine','Migraine','🌀','(migraine*[tiab] OR headache*[tiab])',r'migraine|headache','',['migraine']),
('ibd','Crohn\'s & IBD','🫄','(Crohn*[tiab] OR colitis[tiab] OR "inflammatory bowel"[tiab])',r'crohn|colitis|bowel','',['ibd_crohns']),
]
def conclusion(r):
    for lab,txt in r.get("abstract_sections",[]):
        if lab and re.search(r'conclu|interpretation',lab,re.I): return txt
    secs=[t for l,t in r.get("abstract_sections",[]) if not (l and re.search(r"fund|regist|trial|keyword|copyright",l,re.I))]
    s=re.split(r"(?<=[.!?])\s+",(secs[-1] if secs else r["abstract"]).strip()); return " ".join(s[-2:]) if s else ""
def tag(r):
    p=set(r["pubtypes"])
    if p&{"Practice Guideline","Guideline"}: return "GUIDELINE"
    if "Meta-Analysis" in p: return "META-ANALYSIS"
    if "Systematic Review" in p: return "SR"
    if p&{"Randomized Controlled Trial"}: return "RCT"
    ev=evidence(r)
    return {"human_trial":"TRIAL","review":"REVIEW","preclinical":"PRECLINICAL","human_study":"HUMAN-OBS"}.get(ev,"STUDY")
RANK={"GUIDELINE":0,"META-ANALYSIS":1,"SR":2,"RCT":3,"TRIAL":4,"REVIEW":5,"HUMAN-OBS":6,"STUDY":7,"PRECLINICAL":8}
def item(r): return dict(pmid=r["pmid"],title=r["title"],journal=r["journal"],date=r["date"],tag=tag(r),first_author=r["first_author"],doi=r["doi"],conclusion=conclusion(r)[:420])
def pick(recs,rx,a,need_cann,n,skip=()):
    out=[]
    for r in recs:
        if r['pmid'] in skip: continue
        if not r["date"] or r["date"]<a: continue
        if not re.search(rx,r["title"],re.I): continue
        if need_cann and not CANNT.search(r["title"]): continue
        if not need_cann and CANNT.search(r["title"]): continue
        t=tag(r)
        if t=="PRECLINICAL" or not r["abstract"]: continue
        out.append(item(r))
    out.sort(key=lambda x:x["date"],reverse=True); out.sort(key=lambda x:RANK[x["tag"]])
    return out[:n]
def run():
    a,b=window(18); A=a.isoformat(); W=dp(18); res={}
    SK=json.load(open(SKIP)) if os.path.exists(SKIP) else {}
    for cid,lab,em,q,rx,goal,bg in C:
        cq=f"{CANN} AND {q} AND {TYPES} AND {W} AND english[la] NOT (animals[mh] NOT humans[mh])"
        cn,ids=esearch(cq,40,"relevance")
        hq=f"{q} AND {HOL} AND {HTYPES} AND {W} AND english[la] NOT (cannabis[tiab] OR cannabinoid*[tiab])"
        hn,hids=esearch(hq,25,"relevance")
        recs=efetch(ids+hids) if ids or hids else []
        cr=[r for r in recs if r["pmid"] in ids]; hr=[r for r in recs if r["pmid"] in hids]
        cann=pick(cr,rx,A,True,5,SK.get(cid,[])); hol=pick(hr,rx,A,False,3,SK.get(cid,[]))
        res[cid]=dict(label=lab,emoji=em,goal=goal,background=bg,cann_matches=cn,hol_matches=hn,cannabinoid=cann,holistic=hol,cann_query=cq,hol_query=hq)
        print(f"{cid}: cann {cn}->{len(cann)}  holistic {hn}->{len(hol)}",file=sys.stderr)
    out=dict(window=dict(start=A,end=b.isoformat()),generated=time.strftime("%Y-%m-%d %H:%M %Z"),source="NCBI PubMed E-utilities",conditions=res)
    if sum(len(v["cannabinoid"]) for v in res.values())<10: print("too few results; keeping previous conditions_recent.json",file=sys.stderr); sys.exit(2)
    json.dump(out,open(OUTF,"w"),indent=1); return out
if __name__=="__main__": run()
