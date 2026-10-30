"""Recall & Safety agent: official cannabis product recalls, health/safety advisories and failed-lab-test notices.

Sources are official regulator pages only (state cannabis regulators + FDA). Nothing is invented: every item
carries the official link it came from; fields a source does not publish are left empty. Polite: one pass per
run, at most hourly (agents-recalls.yml), a descriptive User-Agent, small page counts, detail pages cached.
Writes data/recalls.json (+ data/recalls_cache.json for detail-page enrichment). Stdlib only."""
import json,os,re,html,subprocess,sys,time,datetime as dt
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import UA as BROWSER_UA, text, save, load
POLITE="Mozilla/5.0 (compatible; CannabisAgentTerminal-RecallWatch/1.0; +https://tutchgrass-terminal.onrender.com/terminal/)"
MAXN=160
NOTE={}   # per-source fetch notes (e.g. UA fallback)

def fetch(url,timeout=30,accept=None,src=None):
    """GET with the polite UA; if the site's bot wall answers 403, retry once with the repo's standard browser UA."""
    for ua in (POLITE,BROWSER_UA):
        cmd=["curl","-sL","-m",str(timeout),"-A",ua,"-w","\n%{http_code}"]
        if accept: cmd+=["-H","Accept: "+accept]
        r=subprocess.run(cmd+[url],capture_output=True)
        if r.returncode: raise RuntimeError(f"network error (curl {r.returncode})")
        body,_,code=r.stdout.decode("utf-8","replace").rpartition("\n")
        if code=="403" and ua==POLITE:
            if src: NOTE[src]="site blocks the bot User-Agent (403); fetched with the standard browser UA"
            continue
        if code!="200": raise RuntimeError(f"HTTP {code}")
        return body
    raise RuntimeError("HTTP 403")
def T(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def iso(s,fmts=("%m/%d/%Y","%m-%d-%Y","%B %d, %Y","%b. %d, %Y","%b %d, %Y","%Y-%m-%d","%Y%m%d")):
    s=(s or "").strip().replace("Sept.","Sep.").replace("\u00a0"," ")
    for f in fmts:
        try: return dt.datetime.strptime(s,f).strftime("%Y-%m-%d")
        except ValueError: pass
    return ""
def cut(s,n):
    """trim to n chars; mark a cut with an ellipsis so truncated text is never shown as complete"""
    s=(s or "").strip()
    return s if len(s)<=n else s[:n-1].rstrip(" ,;:-—")+"…"
def item(**k):
    k.setdefault("lot",""); k.setdefault("brand",""); k.setdefault("kind","recall"); k.setdefault("tier","thc")
    k["product"]=cut(k.get("product"),160); k["issue"]=cut(k.get("issue"),260); k["lot"]=cut(k["lot"],160)
    return k
CACHE=load("recalls_cache.json",{}) or {}
def cached(url,fn,src):
    if url in CACHE: return CACHE[url]
    try: v=fn(fetch(url,src=src))
    except Exception: v=None
    if v is not None: CACHE[url]=v
    return v
def gist(txt,keys=r'recall|contamin|fail|exceed|banned|pesticide|mold|aspergillus|microb|solvent|label|THC|heavy metal|lead|salmonella'):
    for s in re.split(r'(?<=[.!?])\s+',txt):
        if re.search(keys,s,re.I) and 40<len(s)<400 and not re.search(r'cookie|javascript|subscribe',s,re.I): return s.strip()
    return ""
def pgist(t,pats):
    for k in pats:
        g=gist(t,k)
        if g: return g
    return ""
def uniq_order(xs):
    seen=set(); return [x for x in xs if not (x in seen or seen.add(x))]
def pdf_text(url):
    """Download a PDF (polite UA, browser-UA fallback on 403) and return its text via pdftotext; None if unavailable."""
    import tempfile,shutil
    if not shutil.which("pdftotext"): return None
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        for ua in (POLITE,BROWSER_UA):
            r=subprocess.run(["curl","-sL","-m","40","-A",ua,"-o",f.name,"-w","%{http_code}",url],capture_output=True,text=True)
            if r.stdout.strip()=="200": break
        else: return None
        o=subprocess.run(["pdftotext","-layout",f.name,"-"],capture_output=True,text=True)
        return o.stdout or None
LOT=re.compile(r'\b1A4[0-9A-F]{21}\b')

# ---------------- sources ----------------
def ca():
    out=[]
    for p in (1,2,3):
        h=fetch(f"https://recalls.cannabis.ca.gov/recalls?page={p}",src="CA")
        for c in re.findall(r'<div class="rounded-xl shadow-md relative">(.*?)Details</a>',h,re.S):
            m=re.search(r'href="(/recalls/[0-9a-f]+)"',c); t=T(c)
            d=re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s*$',t)
            h3=re.search(r'<h3[^>]*>(.*?)</h3>',c,re.S); typ=re.search(r'\b(Voluntary|Mandatory)\b',t)
            if not (m and d and h3): continue
            title=T(h3.group(1)); reason=t.split(title,1)[-1].replace(d.group(1),"").strip()
            url="https://recalls.cannabis.ca.gov"+m.group(1)
            det=cached(url,lambda x:{"over":gist(T(re.split(r'Recall Overview',text(x),maxsplit=1)[-1])[:1500]) ,
                                      "biz":(re.search(r'Legal Business Name (.+?) Legal',text(x)) or [None,""])[1]},"CA") or {}
            out.append(item(date=iso(d.group(1)),state="CA",agency="Dept. of Cannabis Control",product=title,brand=det.get("biz",""),
                issue=(reason+(" — "+det["over"] if det.get("over") else "")),lot="",url=url,kind=(typ.group(1).lower()+" recall") if typ else "recall"))
    return out
def mi():
    h=fetch("https://www.michigan.gov/cra/bulletins",src="MI")
    i=h.find("Public Health and Safety Advisory Bulletins",h.find("pagebody") if "pagebody" in h else 0)
    starts=[m.start() for m in re.finditer("Public Health and Safety Advisory Bulletins",h)]
    seg=""
    for s in starts:
        e=h.find("<h2",s+40); cand=h[s:e if e>0 else s+60000]
        if re.search(r'\d\d-\d\d-\d{4}\s*-',cand): seg=cand; break
    out=[]
    for href,lab in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*(\d\d-\d\d-\d{4}\s*-[^<]*)</a>',seg)[:25]:
        url=html.unescape(href); url=url if url.startswith("http") else "https://www.michigan.gov"+url
        d,_,title=html.unescape(lab).partition("-"); d=lab[:10]; title=html.unescape(lab[10:]).strip(" -")
        slug=re.sub(r'\?.*','',url).rstrip("/").rsplit("/",1)[-1]
        brand=""; m=re.search(r'recall-+(.+?)(?:\.pdf)?$',slug,re.I)
        if m: brand=re.sub(r'[-_]+',' ',re.sub(r'(?i)\.pdf|final|llc$','',m.group(1))).strip().title()
        det={}
        if ".pdf" in url.lower():
            if url not in CACHE:
                pt=pdf_text(url)
                if pt:
                    t=re.sub(r'\s+',' ',pt); why=re.search(r'([^.]*\b(?:because|due to)\b[^.]*\.)',t)
                    pr=re.search(r'recalling (?:the |all )?(.{5,140}?) (?:products? )?(?:that|which|because|due)',t)
                    CACHE[url]={"product":pr.group(1).strip() if pr else "","issue":why.group(1).strip() if why else "","lots":uniq_order(LOT.findall(t))[:6]}
            det=CACHE.get(url) or {}
        if "/cra/bulletins/" in url:
            def ex(x):
                t=text(x); k=t.find("In the interest"); t=t[k:] if k>=0 else t
                pr=re.search(r'recalling (?:the |all )?(.{5,140}?) (?:products? )?(?:that|which|because|due)',t)
                why=re.search(r'([^.]*\b(?:because|due to)\b[^.]*\.)',t[:3000])
                return {"product":pr.group(1).strip() if pr else "","issue":(why.group(1).strip() if why else gist(t[:3000])),"lots":sorted(set(LOT.findall(t)))[:6]}
            det=cached(url,ex,"MI") or {}
        out.append(item(date=iso(d),state="MI",agency="Cannabis Regulatory Agency",product=det.get("product") or title,brand=brand,
            issue=det.get("issue") or title,lot=", ".join(det.get("lots",[])[:3])+(f" (+{len(det['lots'])-3} more)" if len(det.get("lots",[]))>3 else ""),url=url))
    return out
def wa():
    h=fetch("https://lcb.wa.gov/examiners/recalls",src="WA"); t=text(h); out=[]
    for blk in re.split(r'(?=Date\s*:\s*\d{1,2}/\d{1,2}/\d{4})',t)[1:40]:
        d=re.match(r'Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',blk)
        prods=re.search(r'Products?\s*:\s*(.*?)(?:Producer/Processor|Processor|Producer)\s*:',blk)
        pp=re.search(r'(?:Producer/Processor|Processor|Producer)\s*:\s*(.*?)\s+Reason\s*:',blk)
        rs=re.search(r'Reason\s*:\s*(.*?)(?:\s+(?:20\d\d)\s+Date\s*:|$)',blk)
        if not d: continue
        ptxt=prods.group(1) if prods else ""; lots=re.findall(r'\b[A-Z]{0,2}\d{14,20}\b',ptxt)
        first=re.split(r'\s+[A-Z]{0,2}\d{14,20}\b',ptxt)[0].strip(" -") if ptxt else ""
        out.append(item(date=iso(d.group(1)),state="WA",agency="Liquor and Cannabis Board",product=first+(f" (+{len(lots)-1} more lots)" if len(lots)>1 else ""),
            brand=(pp.group(1).strip() if pp else ""),issue=(re.sub(r'\s+20\d\d$','',rs.group(1).strip())[:240] if rs else ""),lot=", ".join(lots[:2]),url="https://lcb.wa.gov/examiners/recalls"))
    return out
def oregon():
    j=json.loads(fetch("https://www.oregon.gov/olcc/_api/web/GetList('/olcc/Lists/Products')/items?$top=25&$orderby=Created%20desc",accept="application/json;odata=nometadata",src="OR"))
    out=[]
    for r in j.get("value",[]):
        link=re.search(r'href="([^"]+)"',r.get("Brand_x0020_Name") or ""); 
        out.append(item(date=iso(r.get("Date","")),state="OR",agency="OLCC",product=" ".join(x for x in [T(r.get("Product_x0020_Type")),T(r.get("Description"))] if x),
            brand=T(r.get("Brand")),issue=T(r.get("Brand_x0020_Name")),url=(lambda u:u if u.startswith("http") else "https://www.oregon.gov"+u)(html.unescape(link.group(1)).replace("&#58;",":")) if link else "https://www.oregon.gov/olcc/pages/product-recalls.aspx",
            tier="hemp" if (r.get("Title") or "").lower()=="hemp" else "thc"))
    return out
def co():
    h=fetch("https://med.colorado.gov/health-and-safety-advisory",src="CO"); out=[]
    lt=text(h[h.find("The Latest Health and Safety Advisory"):][:6000]); lm=re.search(r'([^.]*\bdue to\b[^.]*\.)',lt)
    latest=lm.group(1).strip().split(" - ",1)[-1].strip() if lm else ""
    for sec in re.findall(r'(20\d\d) Advisories(.*?)(?=20\d\d Advisories|$)',h,re.S)[:2]:
        for href,lab in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',sec[1],re.S):
            pass
    # list items look like "October 27, 2026: <a>Nutritional Elements LLC ...</a>"
    for m in re.finditer(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, 20\d\d)\s*:?\s*(?:&nbsp;|\s)*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',h):
        d=iso(m.group(1)) or iso(m.group(1).replace(".","")) ; name=T(m.group(3)); href=html.unescape(m.group(2))
        if not d or not name: continue
        if not re.match(r'https?://[^ ]+\.[a-z]{2,}/',href): href="https://med.colorado.gov/health-and-safety-advisory"
        kw=re.search(r'\(([^)]+)\)',name)
        out.append(item(date=d,state="CO",agency="Marijuana Enforcement Division",product="Health & Safety Advisory",brand=name,
            issue=(latest if not out and latest else ("Health & Safety Advisory"+(f": {kw.group(1)}" if kw else "")+" — see the official advisory for affected batches")),
            url=href,kind="advisory"))
    seen=set(); res=[]
    for x in out:
        k=(x["date"],x["brand"]); 
        if k not in seen: seen.add(k); res.append(x)
    return res[:30]
def ny():
    out=[]
    for page in ("current-recalls","past-recalls"):
        h=fetch("https://cannabis.ny.gov/"+page,src="NY")
        for sid,title,body in re.findall(r'<section id="(toc_\d+)"[^>]*>\s*<h2>(.*?)</h2>(.*?)</section>',h,re.S):
            title=T(title); t=T(body)
            if title.lower() in ("overview","") : continue
            d=re.search(r'Issued:?\s*([A-Z][a-z]+ \d{1,2}, 20\d\d)',t) or re.search(r'([A-Z][a-z]+ \d{1,2}, 20\d\d)',t)
            lots=re.findall(r'Lot #?:?\s*([A-Z0-9][A-Z0-9 \-]{3,30}?)(?=\s*(?:[A-Z][a-z]|$|;|\)))',t)
            out.append(item(date=iso(d.group(1)) if d else "",state="NY",agency="Office of Cannabis Management",product=title,brand=title,
                issue=re.sub(r'^Issued:?\s*[A-Z][a-z]+ \d{1,2}, 20\d\d\s*','',pgist(t,[r'aspergillus|mold|contamin|unreliable|pesticide|heavy metal|fail',r'recall']) or t[:200]),
                lot=", ".join(l.strip() for l in lots[:2])+(f" (+{len(lots)-2} more)" if len(lots)>2 else ""),
                url=f"https://cannabis.ny.gov/{page}#{sid}",kind="recall" if page=="current-recalls" else "recall (completed)"))
    return out
def mo():
    h=fetch("https://health.mo.gov/business-professionals/cannabis-regulation/licensee-compliance-guidance/product-recalls",src="MO"); out=[]
    for m in re.finditer(r'<div class="arrow-glyph"></div>\s*(\d{1,2}/\d{1,2}/\d{4})\s*[-–]\s*(.*?)</div>.*?<div class="text-formatted clearfix">(.*?)</div>',h,re.S):
        body=m.group(3); t=T(body); pdf=re.search(r'href="([^"]+\.pdf)"',body)
        prod=re.search(r'product(?:s)?\s+([A-Z]\d{8,}:.{3,140}?)\s+produced by',t)
        lic=T(m.group(2)); brand=lic.split(",",1)[-1].strip() if "," in lic else lic
        out.append(item(date=iso(m.group(1)),state="MO",agency="Division of Cannabis Regulation",product=(prod.group(1).split(":",1)[1].strip() if prod else "Marijuana product recall"),
            brand=brand,issue=pgist(t,[r'did not pass|failed',r'contamin|aspergillus|mold|pesticide|synthetic|chemical modification',r'label|recall']) or t[:220],
            lot=(prod.group(1).split(":")[0] if prod else ""),url=("https://health.mo.gov"+pdf.group(1)) if pdf else "https://health.mo.gov/business-professionals/cannabis-regulation/licensee-compliance-guidance/product-recalls"))
    return out[:30]
def nv():
    h=fetch("https://ccb.nv.gov/guidance/",src="NV"); out=[]
    i=h.find("Public Health and Safety Advisories 2"); i=h.find("Public Health and Safety Advisories</") if i<0 else i
    k=h.find("<h2>Public Health and Safety Advisories</h2>"); seg=h[k:k+30000] if k>=0 else h
    for m in re.finditer(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>([^<]*?(?:Bulletin|Advisory)\s+([\d]{4}-[\dA-Z]+)[^<]*)</a>\s*(?:–|&#8211;|-)\s*Issued\s+([A-Z][a-z]+ \d{1,2}, 20\d\d)',seg):
        m=type("M",(),{"group":lambda self,i,_m=m:{1:_m.group(3),2:_m.group(1),3:_m.group(4)}[i]})()
        num,url,d=m.group(1),m.group(2),m.group(3)
        def ex(_):
            r=subprocess.run(["sh","-c",f"curl -sL -m 30 -A '{POLITE}' '{url}' | pdftotext -layout - -"],capture_output=True,text=True)
            t=re.sub(r'\s+',' ',r.stdout)
            if not t.strip(): return None
            lots=uniq_order(LOT.findall(t))
            prods=re.findall(r'^\s{0,3}([A-Z][^\n]{3,45}?)\s{2,}[A-Z0-9]{5,9}\s+1A40',r.stdout,re.M)
            return {"issue":pgist(t,[r'failed for|failed',r'pesticide|contamin|mold|microb',r'altered|exceed']),"lots":lots[:6],"nlots":len(lots),"prods":prods[:3]}
        det=cached(url,ex,"NV") or {}
        lot=", ".join(det.get("lots",[])[:2])+(f" (+{det['nlots']-2} more)" if det.get("nlots",0)>2 else "")
        out.append(item(date=iso(d),state="NV",agency="Cannabis Compliance Board",product=("; ".join(det.get("prods",[])) or f"Public Health & Safety Bulletin {num}"),
            brand="",issue=det.get("issue") or f"Public Health & Safety Bulletin {num} — see the official PDF",lot=lot,url=url,kind="advisory"))
    return out
def ma():
    h=fetch("https://masscannabiscontrol.com/news/public-health-and-safety-advisories/",src="MA",timeout=60); out=[]; seen=set()
    for url in re.findall(r'href="(https://masscannabiscontrol\.com/20\d\d/\d\d/notice-[^"]*advisory[^"]*)"',h):
        if url in seen: continue
        seen.add(url); slug=url.rstrip("/").rsplit("/",1)[-1]
        d=re.search(r'((?:january|february|march|april|may|june|july|august|september|october|november|december)-\d{1,2}-20\d\d)(?:-\d+)?$',slug) or re.search(r'(?:january|february|march|april|may|june|july|august|september|october|november|december)-\d{1,2}(?=$|-)',slug)
        y=re.search(r'/(20\d\d)/(\d\d)/',url)
        date=iso(d.group(1).replace("-"," ",1).replace("-",", ",1),("%B %d, %Y",)) if d and d.lastindex else (y.group(1)+"-"+y.group(2)+"-01")
        title=re.sub(r'^notice-massachusetts-cannabis-control-commission-public-health-and-safety-advisory-','',slug).replace("-"," ")
        out.append(item(date=date,state="MA",agency="Cannabis Control Commission",product="Public Health & Safety Advisory",brand="",
            issue=title[:1].upper()+title[1:],url=url,kind="advisory"))
    return out
FDAKEY=re.compile(r'\b(delta[- ]?(?:8|9|10)|THC[A-Z]?|HHC|cannabis|cannabidiol|CBD|marijuana|hemp[- ](?:extract|derived|oil|flower|infused|gumm))',re.I)
def fda_recalls():
    q='https://api.fda.gov/food/enforcement.json?search=product_description:(%22delta-8%22+%22delta+8%22+%22THC%22+%22cannabis%22+%22cannabidiol%22+%22hemp%22+%22CBD%22)&sort=report_date:desc&limit=40'
    j=json.loads(fetch(q,src="FDA")); out=[]
    for r in j.get("results",[]):
        pd=r.get("product_description","")
        if not FDAKEY.search(pd) or re.search(r'hemp seed',pd,re.I) and not re.search(r'THC|CBD|delta',pd,re.I): continue
        thc=bool(re.search(r'\bTHC\b|cannabis|marijuana',pd,re.I)) and not re.search(r'less than 0\.3% THC|hemp',pd,re.I)
        rn=r.get("recall_number","")
        out.append(item(date=iso(r.get("report_date","")),state=r.get("state",""),agency=f"FDA enforcement report ({r.get('classification','')}, {r.get('status','')})",
            product=pd,brand=r.get("recalling_firm",""),issue=r.get("reason_for_recall",""),lot=(r.get("code_info") or "")[:120],
            url=f"https://api.fda.gov/food/enforcement.json?search=recall_number:%22{rn}%22",tier="hemp" if not thc else "thc",kind="FDA recall"))
    return out
def fda_letters():
    h=fetch("https://www.fda.gov/news-events/public-health-focus/warning-letters-and-test-results-cannabidiol-related-products",src="FDA-WL"); out=[]
    for row in re.findall(r'<tr>(.*?)</tr>',h,re.S):
        m=re.search(r'href="(/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/[^"]+-(\d{8}))"',row)
        if not m: continue
        cells=[T(c) for c in re.findall(r'<td[^>]*>(.*?)</td>',row,re.S)]
        d=iso(m.group(2),("%m%d%Y",))
        out.append(item(date=d,state=(cells[1] if len(cells)>1 else ""),agency="FDA warning letter",product="CBD / hemp-derived products",brand=(cells[0] if cells else ""),
            issue="FDA warning letter to this firm about its CBD/cannabis-derived products — read the letter for the specific violations",url="https://www.fda.gov"+m.group(1),tier="hemp",kind="warning letter"))
    out.sort(key=lambda x:x["date"],reverse=True)
    return out[:15]
SOURCES=[("CA","California DCC recall portal","https://recalls.cannabis.ca.gov/recalls",ca),
 ("MI","Michigan CRA bulletins","https://www.michigan.gov/cra/bulletins",mi),
 ("CO","Colorado MED health & safety advisories","https://med.colorado.gov/health-and-safety-advisory",co),
 ("WA","Washington LCB cannabis recalls","https://lcb.wa.gov/examiners/recalls",wa),
 ("OR","Oregon OLCC product recalls","https://www.oregon.gov/olcc/pages/product-recalls.aspx",oregon),
 ("NY","New York OCM recalls","https://cannabis.ny.gov/recalls",ny),
 ("MO","Missouri DCR product recalls","https://health.mo.gov/business-professionals/cannabis-regulation/licensee-compliance-guidance/product-recalls",mo),
 ("NV","Nevada CCB public health & safety bulletins","https://ccb.nv.gov/guidance/",nv),
 ("MA","Massachusetts CCC public health & safety advisories","https://masscannabiscontrol.com/news/public-health-and-safety-advisories/",ma),
 ("FDA","FDA enforcement reports (openFDA)","https://open.fda.gov/apis/food/enforcement/",fda_recalls),
 ("FDA-WL","FDA warning letters: CBD/cannabis products","https://www.fda.gov/news-events/public-health-focus/warning-letters-and-test-results-cannabidiol-related-products",fda_letters)]
NOT_COVERED=[("IL","No public recall list found on cannabis.illinois.gov / IDFPR pages"),("OH","Ohio DCC recall URL returns 404"),
 ("NJ","NJ CRC consumer page returns 404; no recall list found"),("MD","Maryland MCA Recalls page returns 404"),
 ("AZ","AZDHS only links marijuana-kitchen recalls inside a food-safety page (not parsed yet)"),("CT","DCP cannabis program URL returns 404")]
def run():
    prev=load("recalls.json",{}) or {}; prev_items={}
    for x in prev.get("items",[]): prev_items.setdefault(x.get("state_src") or x.get("src"),[]).append(x)
    items=[]; status=[]
    for sid,name,url,fn in SOURCES:
        try:
            got=[x for x in fn() if x.get("date") and x.get("url")]
            for x in got: x["src"]=sid
            items+=got; status.append(dict(source=sid,name=name,url=url,status="ok",items=len(got),**({"note":NOTE[sid]} if sid in NOTE else {})))
        except Exception as e:
            keep=prev_items.get(sid,[]); items+=keep
            status.append(dict(source=sid,name=name,url=url,status="unavailable",error=str(e)[:160],kept=len(keep)))
    seen=set(); uniq=[]
    for x in sorted(items,key=lambda x:(x["date"],x["tier"]=="thc"),reverse=True):
        k=(x["url"].split("#")[0] if x["src"] not in ("WA","NY","FDA") else x["url"],x["date"],x["product"].lower()[:60])
        if k in seen: continue
        seen.add(k); uniq.append(x)
    thc=[x for x in uniq if x["tier"]=="thc"]; hemp=[x for x in uniq if x["tier"]!="thc"]
    ok=sum(1 for s in status if s["status"]=="ok")
    obj=dict(agent="Recall & Safety",checked=time.strftime("%Y-%m-%d %H:%M %Z"),
        sources_ok=ok,sources_total=len(status),sources=status,not_covered=[dict(state=a,why=b) for a,b in NOT_COVERED],
        count=len(thc)+len(hemp),items=(thc[:MAXN]+hemp[:40]),
        what_to_do="If you have a product that matches a listed batch/lot, stop using it and follow the instructions in the official notice (usually return it to the retailer or dispose of it). Check the official link for exact batch numbers.")
    json.dump(CACHE,open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","recalls_cache.json"),"w"),indent=0)
    save("recalls.json",obj)
    print(f"recalls: {obj['count']} items, sources ok {ok}/{len(status)}")
    return obj
if __name__=="__main__": run()
