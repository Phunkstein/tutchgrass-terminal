"""NEWS & LAW agent: public RSS feeds, classified US federal / US states / international. No regional priority."""
import re,time,email.utils,xml.etree.ElementTree as ET
from common import curl,save,text
FEEDS=[("Marijuana Moment","https://www.marijuanamoment.net/feed/"),("MJBizDaily","https://mjbizdaily.com/feed/"),("New Cannabis Ventures","https://www.newcannabisventures.com/feed/"),
 ("Business of Cannabis (intl)","https://businessofcannabis.com/feed/"),("StratCann (Canada)","https://stratcann.com/feed/"),
 ("Google News: intl cannabis","https://news.google.com/rss/search?q=cannabis+(Germany+OR+Canada+OR+Thailand+OR+Europe+OR+Australia+OR+UK)+when:7d&hl=en-US&gl=US&ceid=US:en")]
INTL_FEEDS={"Business of Cannabis (intl)","StratCann (Canada)","Google News: intl cannabis"}
STATES="Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota Ohio Oklahoma Oregon Pennsylvania Rhode Island|South Carolina|South Dakota Tennessee Texas Utah Vermont Virginia Washington West Virginia|Wisconsin Wyoming"
STATE_RE=re.compile(r"\b("+"|".join(x for chunk in STATES.split("|") for x in ([chunk] if " " in chunk and chunk.count(" ")==1 and chunk.split()[0] in("New","North","South","Rhode","West") else chunk.split()))+r")\b")
FED=re.compile(r"\b(federal|Congress|Senate|House (bill|committee|vote)|DEA|FDA|rescheduling|reschedul|Schedule (I|III)|SAFE Banking|SAFER|Trump|White House|Justice Department|DOJ|attorney general Bondi|HHS|hemp ban|farm bill|IRS|280E|Supreme Court|VA |veterans)\b",re.I)
INTL=re.compile(r"\b(Germany|German|Canada|Canadian|Thailand|Thai|UK|United Kingdom|Britain|Australia|Israel|Mexico|Colombia|Uruguay|Europe|EU|Switzerland|Swiss|Czech|Netherlands|Dutch|Malta|Luxembourg|Portugal|Spain|France|Italy|Poland|Ukraine|South Africa|Japan|Korea|Brazil|Health Canada|international|global)\b")
LAW=re.compile(r"\b(law|bill|legaliz|ballot|regulat|lawmakers|legislat|court|ruling|governor|vote|measure|policy|license|ban|reschedul|decriminal)\w*",re.I)
def classify(t):
    if FED.search(t): return "US federal"
    if INTL.search(t): return "International"
    if STATE_RE.search(t): return "US states"
    return "Industry"
def run():
    items=[];status=[]
    for name,url in FEEDS:
        try:
            root=ET.fromstring(curl(url).encode()); n=0
            for it in root.iter("item"):
                title=text(it.findtext("title") or ""); link=it.findtext("link"); desc=text(it.findtext("description") or "")[:260]
                if name.startswith("Google News"): desc=""
                n_lim=12 if name.startswith("Google") else 30
                if n>=n_lim: break
                try: ts=email.utils.parsedate_to_datetime(it.findtext("pubDate")).timestamp()
                except Exception: ts=0
                blob=title+" "+desc
                st=STATE_RE.findall(blob)
                items.append(dict(source=name,title=title,link=link,summary=desc,ts=ts,date=time.strftime("%Y-%m-%d %H:%M",time.localtime(ts)) if ts else "",
                    category=("International" if name in INTL_FEEDS and classify(blob) in ("Industry","International") else classify(blob)),is_law=bool(LAW.search(blob)),states=sorted(set(st))))
                n+=1
            status.append(dict(source=name,url=url,status="ok",items=n))
        except Exception as e: status.append(dict(source=name,url=url,status="unavailable",error=str(e)[:80]))
    seen=set();u=[]
    for i in sorted(items,key=lambda x:-x["ts"]):
        k=re.sub(r'\W','',i["title"].lower())[:60]
        if k in seen: continue
        seen.add(k);u.append(i)
    cats={c:[i for i in u if i["category"]==c][:8] for c in("US federal","US states","International","Industry")}
    return save("news.json",dict(agent="news",sources=status,total=len(u),by_category=cats,latest=u[:30]))
if __name__=="__main__":
    r=run(); print(r["sources"])
    for c,v in r["by_category"].items(): print("==",c,len(v)); [print("  ",i["date"],i["source"][:10],i["title"][:100]) for i in v[:5]]
