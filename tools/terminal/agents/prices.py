"""PRICES agent: publicly posted cannabis price series, each judged against its own publishing cadence.
  US      Cannabis Benchmarks U.S. Cannabis Spot Index, free weekly summary (RSS), wholesale flower $/lb.
  Canada  Statistics Canada CPI, Recreational cannabis (Dec 2018=100), monthly, table 18-10-0004-01 (WDS API).
  Canada  Cannabis Benchmarks Canada Cannabis Spot Index (CCSI), C$/g: the free monthly summary stopped after the
          Oct 31, 2025 report, so it is kept only as a historical series with its real last date.
Freshness is never faked: every series carries its real latest_date, its cadence, and max_age_days (how old the latest
point may be before a new one is overdue). The site recomputes the age from latest_date in the browser.
A series whose newest point is more than DISCONTINUED_AFTER cadences overdue is marked status="discontinued"; it is shown
as history and does not make the Market Watcher amber (a live replacement covers that region)."""
import re,json,time,email.utils,datetime as dt,xml.etree.ElementTree as ET,subprocess
from common import curl,save,text
DISCONTINUED_AFTER=4      # cadences overdue before a series counts as no longer published
CB=[("US","U.S. Cannabis Spot Index (wholesale flower, $/lb)","https://www.cannabisbenchmarks.com/reports/feed/","weekly",7,14,"$","/lb",0,
      r"Spot Index (increased|decreased|unchanged|was unchanged)\s*([\d.]+)?%?\s*(?:to|at)?\s*\$([\d,]+)\s*per pound"),
    ("Canada","Canada Cannabis Spot Index (wholesale, C$/g)","https://www.cannabisbenchmarks.com/canada-reports/feed/","monthly",31,45,"C$","/g",2,
      r"CCSI was assessed at C\$(\d+\.\d+) per gram this month, (down|up) from last month.s C\$(\d+\.\d+)")]
WDS="https://www150.statcan.gc.ca/t1/wds/rest/getDataFromCubePidCoordAndLatestNPeriods"
CPI=dict(region="Canada",label="Canada retail: CPI, recreational cannabis (index, Dec 2018=100)",pid=18100004,coord="2.367.0.0.0.0.0.0.0.0",
         url="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810000401",source="Statistics Canada, table 18-10-0004-01 (free, monthly)")
def _age(d): return (time.time()-time.mktime(time.strptime(d,"%Y-%m-%d")))/86400
def _status(pts,cadence_days,max_age):
    if not pts: return "no source yet",None
    age=_age(pts[-1]["date"])
    return ("discontinued" if age>max_age+DISCONTINUED_AFTER*cadence_days else "ok"),age
def cb_series(region,label,url,cadence,cadence_days,max_age,cur,unit,dec,pat):
    root=ET.fromstring(curl(url).encode()); pts=[]
    for it in root.iter("item"):
        d=text(it.findtext("description") or ""); m=re.search(pat,d)
        ts=email.utils.parsedate_to_datetime(it.findtext("pubDate")).timestamp()
        if not m: continue
        if region=="Canada":
            val,_,prev=m.groups(); pct=round((float(val)/float(prev)-1)*100,2)
        else:
            dirn,pct,val=m.groups(); pct=float(pct) if pct else 0.0
            if dirn=="decreased": pct=-pct
        g=re.search(r"In grams, the Spot price was \$(\d+\.\d+)",d); fw=re.search(r"(\w+ \d{4}) Implied Forward[^$]*\$([\d,]+)",d)
        pts.append(dict(date=time.strftime("%Y-%m-%d",time.localtime(ts)),value=float(val.replace(",","")),chg_pct=pct,per_gram=float(g.group(1)) if g else None,
            forward=(fw.group(1),float(fw.group(2).replace(",",""))) if fw else None,title=text(it.findtext("title")),link=it.findtext("link"),summary=d.split("[")[0].strip()[:300]))
    pts.sort(key=lambda p:p["date"]); status,age=_status(pts,cadence_days,max_age)
    s=dict(region=region,label=label,source="Cannabis Benchmarks (free public summaries)",url=url,status=status,cadence=cadence,cadence_days=cadence_days,
           max_age_days=max_age,latest_date=pts[-1]["date"] if pts else None,period="week" if cadence=="weekly" else "month",currency=cur,unit=unit,decimals=dec,
           stale=bool(age is not None and status=="ok" and age>max_age),age_days=round(age) if age is not None else None,points=pts)
    if status=="discontinued": s["note"]=f"No new free {cadence} summary since {s['latest_date']}; shown as history only."
    return s
def cpi_series():
    body=json.dumps([dict(productId=CPI["pid"],coordinate=CPI["coord"],latestN=13)])
    r=subprocess.run(["curl","-sL","-m","30","-X","POST","-H","Content-Type: application/json","-d",body,WDS],capture_output=True)
    if r.returncode: raise RuntimeError(f"curl {r.returncode}")
    o=json.loads(r.stdout)[0]
    if o.get("status")!="SUCCESS": raise RuntimeError(str(o.get("object"))[:80])
    raw=[p for p in o["object"]["vectorDataPoint"] if p.get("value") is not None]; pts=[]
    for i,p in enumerate(raw):
        ref=dt.date.fromisoformat(p["refPer"]); rel=(p.get("releaseTime") or "")[:10]
        prev=raw[i-1]["value"] if i else None
        pts.append(dict(date=rel or p["refPer"],ref_period=ref.strftime("%b %Y"),value=float(p["value"]),chg_pct=round((p["value"]/prev-1)*100,2) if prev else None,
                        per_gram=None,forward=None,title=f"CPI recreational cannabis, {ref:%B %Y} (released {rel})",link=CPI["url"],summary=""))
    # date = StatCan release date (when the number became public); monthly cadence, next release due ~31 days later
    status,age=_status(pts,31,45)
    return dict(region=CPI["region"],label=CPI["label"],source=CPI["source"],url=CPI["url"],vector=o["object"].get("vectorId"),status=status,cadence="monthly",
                cadence_days=31,max_age_days=45,latest_date=pts[-1]["date"] if pts else None,period="month",currency="",unit=" index",decimals=1,
                stale=bool(age is not None and status=="ok" and age>45),age_days=round(age) if age is not None else None,points=pts)
def run():
    series=[]
    for args in CB[:1]:
        try: series.append(cb_series(*args))
        except Exception as e: series.append(dict(region=args[0],label=args[1],url=args[2],status="unavailable",error=str(e)[:80],points=[]))
    try: series.append(cpi_series())
    except Exception as e: series.append(dict(region=CPI["region"],label=CPI["label"],url=CPI["url"],status="unavailable",error=str(e)[:80],points=[]))
    for args in CB[1:]:
        try: series.append(cb_series(*args))
        except Exception as e: series.append(dict(region=args[0],label=args[1],url=args[2],status="unavailable",error=str(e)[:80],points=[]))
    series.append(dict(region="Multi-state retail",label="State-by-state retail/wholesale price reports",status="no source yet",points=[],note="No machine-readable multi-state retail price feed wired yet."))
    return save("prices.json",dict(agent="prices",freshness_rule="each series is judged by its own publishing cadence (max_age_days); discontinued series are history only",series=series))
if __name__=="__main__":
    for s in run()["series"]: print(s["region"],s["status"],s.get("cadence"),s.get("latest_date"),s.get("age_days"),"stale" if s.get("stale") else "",[(p["date"],p["value"],p["chg_pct"]) for p in s["points"]][-3:])
