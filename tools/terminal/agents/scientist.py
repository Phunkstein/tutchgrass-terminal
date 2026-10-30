"""SCIENTIST agent: joins curated syntheses with PubMed metadata actually retrieved; never cites a PMID not fetched."""
import json, os, sys, time, urllib.parse
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,ROOT); sys.path.insert(0,os.path.join(ROOT,"agents"))
from harvest_pubmed import efetch, esearch, get, E
from scientist_curated import C, NASEM, STRAIN_NOTE
DISCLAIMER="Research summary, not medical advice. Talk to a doctor."
LIVEQ={"chronic_neuropathic_pain":"(cannabis OR cannabinoid*) AND (chronic pain OR neuropathic pain)","fibromyalgia":"(cannabis OR cannabinoid*) AND fibromyalgia",
"ms_spasticity":"(cannabis OR cannabinoid* OR nabiximols) AND multiple sclerosis","epilepsy":"cannabidiol AND (epilepsy OR seizure*)",
"insomnia":"(cannabis OR cannabinoid* OR cannabinol) AND (insomnia OR sleep)","anxiety":"(cannabis OR cannabidiol) AND anxiety","ptsd":"(cannabis OR cannabinoid*) AND (PTSD OR posttraumatic)",
"ibd_crohns":"(cannabis OR cannabinoid*) AND (Crohn* OR colitis OR inflammatory bowel)","migraine":"(cannabis OR cannabinoid*) AND (migraine OR headache)",
"arthritis":"(cannabis OR cannabinoid*) AND arthritis","cinv":"(cannabis OR cannabinoid*) AND (nausea OR vomiting) AND chemotherapy","appetite_cachexia":"(cannabis OR cannabinoid* OR dronabinol) AND (appetite OR cachexia)"}
def count(term,reldate=30):
    q=urllib.parse.urlencode({"db":"pubmed","term":term,"retmode":"json","retmax":0,"reldate":reldate,"datetype":"edat"})
    time.sleep(0.4); return int(json.loads(get(E+"esearch.fcgi?"+q))["esearchresult"]["count"])
def run(live=True):
    cp=os.path.join(ROOT,"cache/pubmed.json"); d=json.load(open(cp))
    a={r['pmid']:r for k,v in d.items() if k!='_meta' for r in v['records']}
    need=[p for c in C for p,_ in c['cites'] if p not in a]
    if need:
        got=efetch(sorted(set(need))); d.setdefault("_direct",{"records":[]})["records"]+=got
        for r in got: a[r['pmid']]=r
        json.dump(d,open(cp,"w"),indent=1)
    out=[]; dropped=[]
    for c in C:
        cites=[]
        for p,t in c['cites']:
            r=a.get(p)
            if not r: dropped.append(p); continue
            cites.append(dict(pmid=p,type=t,title=r['title'],journal=r['journal'],year=r['year'],first_author=r['first_author'],doi=r['doi'],
              url=f"https://pubmed.ncbi.nlm.nih.gov/{p}/",doi_url=(f"https://doi.org/{r['doi']}" if r['doi'] else None)))
        e={k:v for k,v in c.items() if k not in("cites","nasem")}; e['citations']=cites
        if c.get('nasem'): e['citations'].append(dict(pmid=None,type="REPORT",title=NASEM['title'],url=NASEM['url'],doi=NASEM['doi'],doi_url="https://doi.org/"+NASEM['doi'],year="2017",journal="National Academies Press",first_author="NASEM"))
        if live:
            try: e['new_papers_30d']=count(LIVEQ[c['id']])
            except Exception: e['new_papers_30d']=None
        out.append(e)
    res=dict(agent="scientist",generated=time.strftime("%Y-%m-%d %H:%M %Z"),disclaimer=DISCLAIMER,strain_note=STRAIN_NOTE,
             method="PubMed E-utilities esearch+efetch (queries in cache/pubmed.json) plus National Academies 2017 report; syntheses written from retrieved abstracts only.",
             pubmed_records_cached=len(a),dropped_unverified=dropped,conditions=out)
    json.dump(res,open(os.path.join(ROOT,"data/scientist.json"),"w"),indent=1)
    lab=json.load(open(os.path.join(ROOT,"data/lab.json"))) if os.path.exists(os.path.join(ROOT,"data/lab.json")) else None
    L=[f"# Tutchgrass Labs: Scientist report","",f"Generated {res['generated']}. {DISCLAIMER}","",f"_{STRAIN_NOTE}_","",
       "Evidence tags: SR = systematic review/meta-analysis, RCT = human randomized trial, HUMAN-OBS = human observational, PRECLINICAL = animal/cell only, GUIDELINE, REPORT, COMMENTARY, REVIEW, CASE, HORT = horticultural study, ANECDOTAL = grower practice (not a study).",""]
    for e in out:
        L+=[f"## {e['name']}",f"- **Evidence strength:** {e['evidence']} — {e['evidence_note']}",f"- **Most promising chemotype:** {e['chemotype']}",
            f"- **Minor cannabinoids:** {', '.join(e['minors']) or '—'}",f"- **Terpenes:** {', '.join(e['terpenes']) or '—'}",
            f"- **Why (plain words):** {e['mechanism']}",f"- **Strains that typically express this profile:** {', '.join(e['strains'])} (typically; check the COA)",
            "- **Cautions:** "+" ".join(e['cautions']),f"- **New PubMed papers, last 30 days:** {e.get('new_papers_30d','n/a')}","- **Citations:**"]
        for ci in e['citations']:
            L.append(f"  - [{ci['type']}] {ci['first_author']} ({ci['year']}). {ci['title']} *{ci['journal']}*. "+(f"PMID [{ci['pmid']}]({ci['url']}). " if ci['pmid'] else f"[{ci['url']}]({ci['url']}). ")+(f"DOI [{ci['doi']}]({ci['doi_url']})" if ci['doi'] else ""))
        if lab:
            g=lab["grower"][e["id"]]; L.append(f"- **For growers:** target {g['target']}. Genetics: {g['genetics']} (cultivar examples are typical, not guaranteed; strain names track chemistry poorly, so test).")
            for f in g["factors"]:
                F=lab["factors"][f]; L.append(f"  - *{F['name']}:* {F['finding']} "+" ".join(f"[PMID {c['pmid']}]({c['url']}) ({c['type']})" for c in F["citations"]))
            F=lab["factors"]["anecdotal_cure"]; L.append(f"  - *{F['name']}:* {F['finding']} ([source]({F['source']['url']}))")
            h=lab["holistic"][e["id"]]; L.append("- **Holistic pairings:** "+" ".join(h["pairs"])+" "+" ".join(f"[PMID {c['pmid']}]({c['url']}) ({c['type']})" for c in h["citations"]))
        L.append("")
    if lab:
        L+=["## Drug interactions & cautions (all conditions)"]
        for i in lab["interactions"]: L.append(f"- **{i['title']}:** {i['text']} "+" ".join(f"[PMID {c['pmid']}]({c['url']}) ({c['type']})" for c in i["citations"]))
        L.append("")
    L.append(DISCLAIMER)
    open(os.path.join(ROOT,"report.md"),"w").write("\n".join(L))
    return res
if __name__=="__main__":
    r=run(live="--nolive" not in sys.argv); print("conditions",len(r['conditions']),"dropped",r['dropped_unverified'])
