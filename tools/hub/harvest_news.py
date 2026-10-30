"""News harvester: public RSS feeds -> data/hub/news.json. Headlines + links only (no article text republished)."""
import json, os, re, sys, time, html, email.utils, subprocess, xml.etree.ElementTree as ET
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GN="https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="
FEEDS=[("Marijuana Moment","https://www.marijuanamoment.net/feed/"),("MJBizDaily","https://mjbizdaily.com/feed/"),
 ("New Cannabis Ventures","https://www.newcannabisventures.com/feed/"),("Business of Cannabis","https://businessofcannabis.com/feed/"),
 ("StratCann","https://stratcann.com/feed/"),("Cannabis Health News","https://www.cannabishealthnews.co.uk/feed/"),
 ("Google News","%s%s"%(GN,"hemp+THC+(ban+OR+rule+OR+%22December+11%22+OR+Congress+OR+FDA)+when:14d")),
 ("Google News","%s%s"%(GN,"hemp+(THCA+OR+delta-8+OR+intoxicating)+when:14d")),
 ("Google News","%s%s"%(GN,"cannabis+(rescheduling+OR+DEA+OR+legalization)+when:7d"))]
HEMP=re.compile(r"\b(hemp|THCA|THC-A|delta-8|delta 8|Δ8|intoxicating|0\.4 ?mg|farm bill|CBD|THC (drink|beverage|seltzer)s?|THC drinks?|December 11|Dec\. 11|Nov\. 12|November 12)\b",re.I)
FED=re.compile(r"\b(federal|Congress|Senate|House|DEA|FDA|reschedul\w*|Schedule (I|III)|SAFE Banking|Trump|White House|Justice Department|DOJ|HHS|USDA|IRS|280E|Supreme Court|appropriations|continuing resolution)\b",re.I)
SKIP=re.compile(r"\b(stock|shares|earnings|IPO|discount|coupon|deal of|sale|crypto|bitcoin|price target|prices?|revenue|financial results|sales top|sponsored|webinar|podcast)\b",re.I)
def fetch(url):
    return subprocess.run(["curl","-sL","--max-time","25","-A","Mozilla/5.0 (TutchgrassHub news bot)",url],capture_output=True,text=True).stdout
def clean(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()
def run(max_age_days=21):
    items=[]; status=[]; now=time.time()
    for name,url in FEEDS:
        try:
            root=ET.fromstring(fetch(url).encode()); n=0
            for it in root.iter("item"):
                title=clean(it.findtext("title")); link=(it.findtext("link") or "").strip(); pub=name
                if name=="Google News":
                    src=it.find("source"); pub=(src.text if src is not None else "")+" via Google News"
                    title=re.sub(r"\s+-\s+[^-]+$","",title)
                try: ts=email.utils.parsedate_to_datetime(it.findtext("pubDate")).timestamp()
                except Exception: continue
                if now-ts>max_age_days*86400 or SKIP.search(title) or not title or not link: continue
                desc="" if name=="Google News" else clean(it.findtext("description"))[:240]
                blob=title+" "+desc
                cat="Hemp rules" if HEMP.search(title) else ("Federal" if FED.search(blob) else "States & world")
                items.append(dict(source=pub,title=title,link=link,ts=int(ts),date=time.strftime("%Y-%m-%d",time.localtime(ts)),category=cat)); n+=1
            status.append(dict(source=name,url=url,status="ok",items=n))
        except Exception as e: status.append(dict(source=name,url=url,status="error",error=str(e)[:100]))
    seen=set(); u=[]
    for i in sorted(items,key=lambda x:-x["ts"]):
        k=re.sub(r"\W","",i["title"].lower())[:55]
        if k in seen: continue
        seen.add(k); u.append(i)
    out=dict(generated=time.strftime("%Y-%m-%d %H:%M %Z"),max_age_days=max_age_days,sources=status,total=len(u),
             hemp=[i for i in u if i["category"]=="Hemp rules"][:20],federal=[i for i in u if i["category"]=="Federal"][:12],
             other=[i for i in u if i["category"]=="States & world"][:20])
    if len(u)<5: print("news: too few items, keeping previous news.json",file=sys.stderr); sys.exit(2)
    os.makedirs(ROOT+"/data/hub",exist_ok=True); json.dump(out,open(ROOT+"/data/hub/news.json","w"),indent=1)
    print("news:",[(s["source"][:14],s.get("items",s.get("error"))) for s in status],"total",len(u),file=sys.stderr); return out
if __name__=="__main__":
    o=run()
    for k in("hemp","federal","other"):
        print("==",k,len(o[k])); [print("  ",i["date"],i["source"][:28],"|",i["title"][:110]) for i in o[k]]
