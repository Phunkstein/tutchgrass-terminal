"""Terps tab: for each goal x terpene, count + classify PubMed papers from the last 18 months. Writes data/hub/terps.json"""
import json,sys,os,time,datetime as dt
sys.path.insert(0,os.path.dirname(__file__)); from pubmed_lib import esearch,efetch,evidence,dp,window
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOALS={ # id: (label, emoji, PubMed title/abstract terms)
 "sleep":("Sleep","😴",["sleep","insomnia","sedative","hypnotic"]),
 "pain":("Pain","🩹",["pain","analgesic","analgesia","antinociceptive","nociception","neuropathic"]),
 "anxiety":("Anxiety","🫨",["anxiety","anxiolytic","anxiety-like"]),
 "mood":("Mood","🌈",["depression","depressive","antidepressant","mood"]),
 "focus":("Focus & memory","🎯",["cognition","cognitive","memory","attention","alertness"]),
 "appetite":("Appetite","🍽️",["appetite","food intake","hunger","satiety"]),
 "inflammation":("Inflammation","🔥",["inflammation","anti-inflammatory","inflammatory"]),
 "nausea":("Nausea","🤢",["nausea","vomiting","antiemetic","emesis"]),
}
TERPS={ # id: (display name, PubMed terms, aroma, common in)
 "myrcene":("Myrcene",["myrcene","beta-myrcene"],"earthy, musky, herbal","hops, mango, lemongrass"),
 "limonene":("Limonene",["limonene","d-limonene"],"citrus","citrus peels"),
 "linalool":("Linalool",["linalool"],"floral, lavender","lavender, coriander"),
 "caryophyllene":("β-Caryophyllene",["caryophyllene","beta-caryophyllene"],"peppery, spicy, woody","black pepper, cloves"),
 "pinene":("Pinene",["pinene","alpha-pinene"],"pine, fresh","pine needles, rosemary"),
 "terpinolene":("Terpinolene",["terpinolene"],"fresh, piney, floral","tea tree, lilac"),
 "humulene":("Humulene",["humulene","alpha-humulene"],"woody, hoppy","hops, sage"),
 "ocimene":("Ocimene",["ocimene"],"sweet, herbal","basil, mint"),
 "nerolidol":("Nerolidol",["nerolidol"],"woody, floral","jasmine, tea tree"),
 "bisabolol":("Bisabolol",["bisabolol"],"soft floral, chamomile","chamomile"),
}
def tiab(ws): return "("+" OR ".join(f'"{w}"[tiab]' if " " in w or "-" in w else f"{w}[tiab]" for w in ws)+")"
RANK={"human_trial":0,"review":1,"human_study":2,"preclinical":3,"other":4}
def run():
    D=dp(18); a,b=window(18)
    OV=json.load(open(ROOT+"/data/hub/evidence_overrides.json")) if os.path.exists(ROOT+"/data/hub/evidence_overrides.json") else {}
    RP=ROOT+"/data/hub/terps_records.json"; cache=json.load(open(RP)) if os.path.exists(RP) else {}
    out={"window":{"from":a.isoformat(),"to":b.isoformat()},"generated":time.strftime("%Y-%m-%d %H:%M %Z"),
      "source":"NCBI PubMed E-utilities (esearch + efetch)","rule":"Counted = PubMed papers published in the window with the terpene in the TITLE and the goal in the title or abstract. Trial protocols (no results yet) are not counted.",
      "goals":{},"terpenes":{k:dict(name=v[0],aroma=v[2],common_in=v[3]) for k,v in TERPS.items()}}
    for g,(gl,em,gw) in GOALS.items():
        rows=[]
        for t,(tn,tw,ar,ci) in TERPS.items():
            q=f"{tiab(tw)} AND {tiab(gw)} AND {D}"
            n,ids=esearch(q,200,"pub_date")
            need=[i for i in ids if i not in cache]
            for r in efetch(need): cache[r["pmid"]]=r
            tl=[w.lower() for w in tw]; recs=[]
            for i in ids:
                if i not in cache: continue
                r=dict(cache[i]); r["evidence"]=evidence(r)
                if "Clinical Trial Protocol" in r["pubtypes"] or "protocol" in r["title"].lower(): r["evidence"]="protocol"
                o=OV.get(i,{})
                if o.get("evidence"): r["evidence"]=o["evidence"]
                if o.get("exclude"): continue
                if any(w in r["title"].lower() for w in tl) and r["evidence"]!="protocol": recs.append((r,o))
            cnt={k:sum(1 for r,o in recs if r["evidence"]==k) for k in RANK}
            top=sorted(recs,key=lambda x:(RANK[x[0]["evidence"]],-int(x[0]["date"].replace("-","") or 0)))[:3]
            rows.append(dict(terp=t,query=q,search_hits=n,count=len(recs),by_evidence=cnt,ids=[r["pmid"] for r,o in recs],
              papers=[dict(pmid=r["pmid"],title=r["title"],journal=r["journal"],date=r["date"],evidence=r["evidence"],first_author=r["first_author"],doi=r["doi"],takeaway=o.get("takeaway")) for r,o in top]))
            print(g,t,n,len(recs),cnt,file=sys.stderr)
        rows.sort(key=lambda r:(min([RANK[p["evidence"]] for p in r["papers"]] or [9]),-r["count"]))
        out["goals"][g]=dict(label=gl,emoji=em,terms=gw,terps=rows)
    json.dump(out,open(ROOT+"/data/hub/terps.json","w"),indent=1)
    json.dump(cache,open(RP,"w"))
    return out
if __name__=="__main__": run()
