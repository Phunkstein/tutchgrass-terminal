"""RESEARCH WIRE: newest PubMed papers (medical + cultivation) + health/policy news from public RSS. US + international."""
import json,os,re,sys,time,urllib.parse
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT); sys.path.insert(0,os.path.join(ROOT,"agents"))
import news
from common import save
from harvest_pubmed import efetch, get, E
news.FEEDS.append(("Cannabis Health News (UK)","https://www.cannabishealthnews.co.uk/feed/")); news.INTL_FEEDS.add("Cannabis Health News (UK)")
HEALTH=re.compile(r"\b(health|medical|medicin|patient|doctor|study|studies|research|trial|clinical|pain|sleep|insomnia|anxiety|PTSD|epilep|seizure|cancer|chemo|nausea|arthritis|migraine|multiple sclerosis|Crohn|veteran|psychosis|heart|cardio|pregnan|hospital|emergency|CBD|cannabidiol|terpene|cannabinoid|overdose|mental|dementia|opioid|FDA|reschedul|Schedule III|cultivat|harvest|growers?\b)\w*",re.I)
PQ={"medical":"(cannabis[tiab] OR cannabinoid*[tiab] OR cannabidiol[tiab] OR marijuana[tiab]) AND (patient* OR trial OR clinical OR therap*)",
    "cultivation":"(Cannabis sativa[tiab] OR hemp[tiab]) AND (cultivation OR light OR harvest OR drying OR genotype OR terpene* OR yield OR trichome*)"}
def newest(q,n=10,days=14):
    p=urllib.parse.urlencode({"db":"pubmed","term":q,"retmode":"json","retmax":n,"reldate":days,"datetype":"edat","sort":"pub_date"})
    time.sleep(0.4); ids=json.loads(get(E+"esearch.fcgi?"+p))["esearchresult"]["idlist"]; return efetch(ids) if ids else []
def run():
    papers=[];pstat=[]
    for k,q in PQ.items():
        try:
            rs=newest(q)
            rs=[r for r in rs if re.search(r'cannab|hemp|marijuana|terpen|THC|CBD',r['title'],re.I) and not re.search(r'nanocellulose|biochar|composite|concrete|fibre board|hempcrete',r['title'],re.I)]
            for r in rs:
                papers.append(dict(track=k,pmid=r["pmid"],title=r["title"],journal=r["journal"],year=r["year"],first_author=r["first_author"],
                    pubtypes=r.get("pubtypes",[]),preclinical=bool(re.search(r"\b(mice|mouse|rat|rats|murine|in vitro|zebrafish|cell line)\b",(r["title"]+" "+r.get("abstract",""))[:2000],re.I)),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"))
            pstat.append(dict(source=f"PubMed newest ({k}, 14 d)",status="ok",items=len(rs)))
        except Exception as e: pstat.append(dict(source=f"PubMed newest ({k})",status="unavailable",error=str(e)[:80]))
    n=news.run(save_file=False)   # read the feeds, but leave data/news.json to the News Wire workflow
    hn=[i for i in n["latest"] if HEALTH.search(i["title"]+" "+i["summary"])]
    allitems=[]
    for c,v in n["by_category"].items(): allitems+=v
    pool={i["link"]:i for i in n["latest"]+allitems}
    health=[i for i in sorted(pool.values(),key=lambda x:-x["ts"]) if HEALTH.search(i["title"]+" "+i["summary"])]
    us=[i for i in health if i["category"]!="International"][:10]; intl=[i for i in health if i["category"]=="International"][:8]
    return save("wire.json",dict(agent="wire",sources=pstat+n["sources"],papers_medical=[p for p in papers if p["track"]=="medical"],
        papers_cultivation=[p for p in papers if p["track"]=="cultivation"],news_us=us,news_intl=intl,news_health_total=len(health)))
if __name__=="__main__":
    r=run()
    for s in r["sources"]: print(s)
    print(len(r["papers_medical"]),len(r["papers_cultivation"]),len(r["news_us"]),len(r["news_intl"]))
    for p in r["papers_cultivation"][:5]: print(" C",p["title"][:90])
    for p in r["news_intl"][:5]: print(" I",p["title"][:90])
