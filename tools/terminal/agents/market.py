"""MARKET agent: cannabis equities daily move from Yahoo Finance public chart endpoint. Failure => 'unavailable'."""
import json,time
from common import curl,save
TICKERS=[("MSOS","AdvisorShares Pure US Cannabis ETF"),("TLRY","Tilray"),("CGC","Canopy Growth"),("CURLF","Curaleaf"),("GTBIF","Green Thumb"),("TRLV","Trulieve (NYSE; Yahoo lists old OTC TCNNF as delisted)"),("CRON","Cronos Group")]
def run():
    rows=[]
    for t,n in TICKERS:
        try:
            j=None
            for host in ("query1","query2"):
                try: j=json.loads(curl(f"https://{host}.finance.yahoo.com/v8/finance/chart/{t}?range=1mo&interval=1d",ua="Mozilla/5.0")); break
                except Exception: time.sleep(1)
            if j is None: raise RuntimeError("yahoo rate-limited/unreachable")
            r=j["chart"]["result"][0]; m=r["meta"]; q=r["indicators"]["quote"][0]["close"]; ts=r["timestamp"]
            pts=[(a,b) for a,b in zip(ts,q) if b is not None]
            price=m.get("regularMarketPrice"); prev=pts[-2][1] if len(pts)>=2 else m.get("chartPreviousClose")
            # if last bar is today's, compare to bar before it
            chg=(price/prev-1)*100 if price and prev else None
            m1=(price/pts[0][1]-1)*100 if pts else None
            rows.append(dict(ticker=t,name=n,price=round(price,4) if price else None,prev_close=round(prev,4) if prev else None,chg_pct=round(chg,2) if chg is not None else None,
                 chg_1mo_pct=round(m1,2) if m1 is not None else None,spark=[round(b,4) for _,b in pts],as_of=time.strftime("%Y-%m-%d %H:%M",time.localtime(m.get("regularMarketTime",0))),status="ok"))
        except Exception as e:
            rows.append(dict(ticker=t,name=n,status="unavailable",error=str(e)[:80]))
        time.sleep(0.5)
    ok=[r for r in rows if r["status"]=="ok"]
    return save("market.json",dict(agent="market",source="Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart)",rows=rows,ok=len(ok),failed=len(rows)-len(ok)))
if __name__=="__main__":
    r=run(); [print(x["ticker"],x.get("price"),x.get("chg_pct"),x["status"]) for x in r["rows"]]
