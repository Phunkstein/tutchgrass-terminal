"""PRICES agent: national wholesale price summaries that are publicly posted (Cannabis Benchmarks free weekly summaries)."""
import re,time,email.utils,xml.etree.ElementTree as ET
from common import curl,save,text
SRC=[("US","U.S. Cannabis Spot Index (wholesale flower, $/lb)","https://www.cannabisbenchmarks.com/reports/feed/",r"Spot Index (increased|decreased|unchanged|was unchanged)\s*([\d.]+)?%?\s*(?:to|at)?\s*\$([\d,]+)\s*per pound"),
     ("Canada","Canada Cannabis Spot Index (wholesale, C$/g)","https://www.cannabisbenchmarks.com/canada-reports/feed/",r"CCSI was assessed at C\$(\d+\.\d+) per gram this month, (down|up) from last month.s C\$(\d+\.\d+)")]
def run():
    series=[]
    for region,label,url,pat in SRC:
        try:
            root=ET.fromstring(curl(url).encode()); pts=[]
            for it in root.iter("item"):
                d=text(it.findtext("description") or ""); m=re.search(pat,d)
                ts=email.utils.parsedate_to_datetime(it.findtext("pubDate")).timestamp()
                if not m: continue
                if region=="Canada":
                    val,_,prev=m.groups(); pct=round((float(val)/float(prev)-1)*100,2); dirn=None
                else:
                    dirn,pct,val=m.groups(); pct=float(pct) if pct else 0.0
                    if dirn=="decreased": pct=-pct
                g=re.search(r"In grams, the Spot price was \$(\d+\.\d+)",d); fw=re.search(r"(\w+ \d{4}) Implied Forward[^$]*\$([\d,]+)",d)
                pts.append(dict(date=time.strftime("%Y-%m-%d",time.localtime(ts)),value=float(val.replace(",","")),chg_pct=pct,per_gram=float(g.group(1)) if g else None,
                    forward=(fw.group(1),float(fw.group(2).replace(",",""))) if fw else None,title=text(it.findtext("title")),link=it.findtext("link"),summary=d.split("[")[0].strip()[:300]))
            pts.sort(key=lambda p:p["date"]); age=(time.time()-time.mktime(time.strptime(pts[-1]["date"],"%Y-%m-%d")))/86400 if pts else None
            series.append(dict(region=region,label=label,source="Cannabis Benchmarks (free public weekly summaries)",url=url,status="ok" if pts else "no source yet",
                               stale=bool(age and age>45),age_days=round(age) if age else None,points=pts))
        except Exception as e:
            series.append(dict(region=region,label=label,url=url,status="unavailable",error=str(e)[:80],points=[]))
    series.append(dict(region="Multi-state retail",label="State-by-state retail/wholesale price reports",status="no source yet",points=[],note="No machine-readable multi-state retail price feed wired yet."))
    return save("prices.json",dict(agent="prices",series=series))
if __name__=="__main__":
    for s in run()["series"]: print(s["region"],s["status"],s.get("stale"),[(p["date"],p["value"],p["chg_pct"]) for p in s["points"]][-6:])
