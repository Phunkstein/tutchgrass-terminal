"""Harvest real PubMed records (esearch + efetch) for scientist agent. Caches to cache/pubmed.json."""
import json, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET, sys
E="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
def get(u):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"cannabis-terminal/1 (research)"}),timeout=30).read()
        except Exception as e: time.sleep(2)
    raise RuntimeError(u)
def esearch(term,n=6):
    q=urllib.parse.urlencode({"db":"pubmed","term":term,"retmode":"json","retmax":n,"sort":"relevance"})
    time.sleep(0.4); return json.loads(get(E+"esearch.fcgi?"+q))["esearchresult"]["idlist"]
def efetch(ids):
    if not ids: return []
    time.sleep(0.4); x=ET.fromstring(get(E+"efetch.fcgi?db=pubmed&retmode=xml&id="+",".join(ids)))
    out=[]
    for a in x.findall(".//PubmedArticle"):
        pmid=a.findtext(".//PMID"); art=a.find(".//Article")
        title="".join(art.find("ArticleTitle").itertext()) if art.find("ArticleTitle") is not None else ""
        abs_=" ".join(((t.get("Label")+": ") if t.get("Label") else "")+"".join(t.itertext()) for t in art.findall(".//AbstractText"))
        year=a.findtext(".//JournalIssue/PubDate/Year") or (a.findtext(".//JournalIssue/PubDate/MedlineDate") or "")[:4]
        doi=None
        for i in a.findall("./PubmedData/ArticleIdList/ArticleId"):
            if i.get("IdType")=="doi": doi=i.text
        pts=[p.text for p in art.findall(".//PublicationType")]
        au=art.findall(".//Author"); first=(au[0].findtext("LastName") or au[0].findtext("CollectiveName") or "") if au else ""
        out.append(dict(pmid=pmid,title=title,abstract=abs_,year=year,journal=a.findtext(".//Journal/ISOAbbreviation") or a.findtext(".//Journal/Title"),doi=doi,pubtypes=pts,first_author=first+(" et al." if len(au)>1 else "")))
    return out
SR='(systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt] OR review[pt])'
Q={
"chronic_neuropathic_pain":["(cannabis OR cannabinoids OR nabiximols OR tetrahydrocannabinol) AND neuropathic pain AND (systematic review[pt] OR meta-analysis[pt])","(cannabis OR tetrahydrocannabinol) AND neuropathic pain AND randomized controlled trial[pt] AND (vaporized OR smoked)","beta-caryophyllene AND (neuropathic pain OR CB2) AND pain"],
"fibromyalgia":["(cannabis OR cannabinoids OR nabilone OR cannabidiol) AND fibromyalgia AND "+SR,"cannabis AND fibromyalgia AND (Bedrocan OR Bediol OR Bedrolite)"],
"ms_spasticity":["(nabiximols OR Sativex) AND spasticity AND multiple sclerosis AND (randomized controlled trial[pt] OR meta-analysis[pt])","cannabinoids AND multiple sclerosis AND spasticity AND systematic review[pt]"],
"epilepsy":["cannabidiol AND (Dravet OR Lennox-Gastaut OR tuberous sclerosis) AND randomized controlled trial[pt]","cannabidiol AND epilepsy AND (systematic review[pt] OR meta-analysis[pt])","(CBD-enriched OR cannabis extract) AND epilepsy AND THC"],
"insomnia":["(cannabis OR cannabinoids OR cannabidiol OR cannabinol) AND (insomnia OR sleep) AND (systematic review[pt] OR meta-analysis[pt])","(cannabinol OR CBN) AND sleep AND randomized controlled trial[pt]","(THC OR cannabis) AND insomnia AND randomized controlled trial[pt]"],
"anxiety":["cannabidiol AND anxiety AND (randomized controlled trial[pt] OR systematic review[pt])","limonene AND (THC OR tetrahydrocannabinol) AND anxiety","(tetrahydrocannabinol OR THC) AND anxiety AND dose AND (biphasic OR anxiogenic)"],
"ptsd":["(cannabis OR cannabinoids OR nabilone) AND (PTSD OR posttraumatic stress) AND (randomized controlled trial[pt] OR systematic review[pt])"],
"ibd_crohns":["(cannabis OR cannabinoids OR cannabidiol) AND (Crohn OR ulcerative colitis OR inflammatory bowel disease) AND (randomized controlled trial[pt] OR systematic review[pt] OR meta-analysis[pt])"],
"migraine":["(cannabis OR cannabinoids) AND migraine AND (randomized controlled trial[pt] OR systematic review[pt] OR review[pt])","cannabis AND migraine AND (THC AND CBD) AND acute treatment"],
"arthritis":["(cannabis OR cannabinoids OR cannabidiol) AND (rheumatoid arthritis OR osteoarthritis) AND (randomized controlled trial[pt] OR systematic review[pt])","cannabidiol AND osteoarthritis AND randomized controlled trial[pt]"],
"cinv":["(cannabinoids OR dronabinol OR nabilone OR THC) AND chemotherapy-induced nausea AND (systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt])"],
"appetite_cachexia":["(cannabis OR cannabinoids OR dronabinol) AND (appetite OR cachexia OR anorexia) AND (cancer OR HIV) AND (randomized controlled trial[pt] OR systematic review[pt] OR meta-analysis[pt])"],
}
if __name__=="__main__":
    res={}
    for k,qs in Q.items():
        ids=[]
        for q in qs:
            for i in esearch(q,7):
                if i not in ids: ids.append(i)
        res[k]={"queries":qs,"records":efetch(ids)}
        print(k,len(res[k]["records"]),file=sys.stderr)
    res["_meta"]={"source":"NCBI PubMed E-utilities esearch+efetch","fetched":time.strftime("%Y-%m-%d %H:%M %Z")}
    json.dump(res,open("cache/pubmed.json","w"),indent=1)
