"""Tiny NCBI PubMed E-utilities client (esearch + efetch). No API key needed; stays under 3 req/s."""
import json,time,urllib.request,urllib.parse,xml.etree.ElementTree as ET,re,datetime as dt
EU="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
UA={"User-Agent":"tutchgrass-terminal/1 (public research hub; contact via x.com/Tutchgrass)"}
MON={m:i+1 for i,m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}
def _get(u):
    for i in range(4):
        try:
            time.sleep(0.38); return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read()
        except Exception as e: err=e; time.sleep(2+2*i)
    raise RuntimeError(f"{u}: {err}")
def window(months=18,today=None):
    t=today or dt.date.today(); y,m=t.year,t.month-months
    while m<=0: m+=12;y-=1
    import calendar
    return dt.date(y,m,min(t.day,calendar.monthrange(y,m)[1])),t
def dp(months=18):
    a,b=window(months); return f"{a:%Y/%m/%d}:{b:%Y/%m/%d}[dp]"
def esearch(term,n=100,sort="relevance"):
    q=urllib.parse.urlencode({"db":"pubmed","term":term,"retmode":"json","retmax":n,"sort":sort})
    r=json.loads(_get(EU+"esearch.fcgi?"+q))["esearchresult"]; return int(r["count"]),r["idlist"]
def _date(a):
    ad=a.find(".//Article/ArticleDate")
    if ad is not None and ad.findtext("Year"):
        return f'{ad.findtext("Year")}-{int(ad.findtext("Month") or 1):02d}-{int(ad.findtext("Day") or 1):02d}'
    pd=a.find(".//JournalIssue/PubDate")
    if pd is not None:
        y=pd.findtext("Year") or (pd.findtext("MedlineDate") or "")[:4]
        m=pd.findtext("Month") or "Jan"; m=MON.get(m[:3],int(m) if m.isdigit() else 1)
        d=int(pd.findtext("Day") or 1) if (pd.findtext("Day") or "1").isdigit() else 1
        if y: return f"{y}-{m:02d}-{d:02d}"
    return ""
def efetch(ids):
    out=[]
    for i in range(0,len(ids),150):
        x=ET.fromstring(_get(EU+"efetch.fcgi?db=pubmed&retmode=xml&id="+",".join(ids[i:i+150])))
        for a in x.findall(".//PubmedArticle"):
            art=a.find(".//Article"); pmid=a.findtext(".//MedlineCitation/PMID")
            t=art.find("ArticleTitle"); title=" ".join("".join(t.itertext()).split()) if t is not None else ""
            secs=[(s.get("Label") or s.get("NlmCategory") or "", " ".join("".join(s.itertext()).split())) for s in art.findall(".//Abstract/AbstractText")]
            doi=next((i.text for i in a.findall("./PubmedData/ArticleIdList/ArticleId") if i.get("IdType")=="doi"),None)
            au=art.findall(".//AuthorList/Author"); first=(au[0].findtext("LastName") or au[0].findtext("CollectiveName") or "") if au else ""
            mesh=[m.findtext("DescriptorName") for m in a.findall(".//MeshHeading")]
            ed=next((h for h in a.findall("./PubmedData/History/PubMedPubDate") if h.get("PubStatus") in("pubmed","entrez")),None)
            edat=f'{ed.findtext("Year")}-{int(ed.findtext("Month") or 1):02d}-{int(ed.findtext("Day") or 1):02d}' if ed is not None and ed.findtext("Year") else ""
            out.append(dict(edat=edat,pmid=pmid,title=title,abstract_sections=secs,abstract=" ".join(((l+": ") if l else "")+s for l,s in secs),date=_date(a),
              journal=a.findtext(".//Journal/ISOAbbreviation") or a.findtext(".//Journal/Title"),doi=doi,
              pubtypes=[p.text for p in art.findall(".//PublicationTypeList/PublicationType")],mesh=mesh,
              first_author=first+(" et al." if len(au)>1 else "")))
    return out
ANIMAL=re.compile(r"\b(mice|mouse|murine|rats?|rodents?|zebrafish|in vitro|cell lines?|cultured|drosophila|elegans|larvae|piglets?|broilers?|chickens?|hamsters?|rabbits?|in silico|molecular docking|xenograft|macrophages|RAW ?264\.7|ex vivo)\b",re.I)
HUMAN=re.compile(r"\b(participants|volunteers|patients|healthy adults|adults aged|women|men|children|subjects|respondents|people)\b",re.I)
RAND=re.compile(r"\b(randomi[sz]ed|placebo|double-blind|crossover|clinical trial)\b",re.I)
def evidence(r):
    pt=set(r["pubtypes"]); txt=r["title"]+" "+r["abstract"]
    if pt & {"Randomized Controlled Trial","Clinical Trial","Clinical Trial, Phase I","Clinical Trial, Phase II","Clinical Trial, Phase III","Controlled Clinical Trial","Pragmatic Clinical Trial"}: return "human_trial"
    if pt & {"Systematic Review","Meta-Analysis","Review","Scoping Review"} or re.search(r"\b(systematic review|meta-analys[ie]s|scoping review|narrative review|a review)\b",txt,re.I) or re.search(r"\breview\b",r["title"],re.I): return "review"
    if RAND.search(txt) and HUMAN.search(txt) and not ANIMAL.search(txt): return "human_trial"
    if ANIMAL.search(txt): return "preclinical"
    if HUMAN.search(txt): return "human_study"
    return "other"
