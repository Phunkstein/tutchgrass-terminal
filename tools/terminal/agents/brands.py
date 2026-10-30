"""BRAND AUDITOR, daily automation (free sources only: the brands' own public web pages). Stdlib only (plus the curl binary, present on GitHub runners, for redirect-safe link checks).

What it does every day, without inventing anything:
 1. COA link check: every COA the report cards are built from (public/terminal/data/coas.json) is re-requested
    (HEAD, then a 1-byte ranged GET before anything is called "removed") to confirm the brand still publishes it. 404/410 = "removed";
    timeouts, 403/429 and 5xx = "unreachable" (not counted as removed, since bot walls and outages happen).
    Requests are spread over hosts, 1.5 s apart per host, ~210 requests a day in total.
 2. New-COA discovery: each brand lab-results page in data/brand_sources.json is read once (plain GET) and its PDF
    links are compared with the COAs already scored. Unscored COAs are QUEUED in data/brand_audit.json, never
    auto-scored: a label-claim vs lab-result score needs the PDF read and checked, which stays a reviewed step.
 3. Writes data/brand_audit.json and adds the daily check to public/terminal/data/meta.json (checked, links_ok,
    links_removed, links_unreachable, queued_coas, new_coas_today). Grades and scores are NOT changed.
A failed run keeps the last good files. Prints a one-line summary."""
import json,os,re,shutil,subprocess,sys,time,threading,urllib.request,urllib.error,urllib.parse,hashlib
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REPO=os.path.abspath(os.path.join(HERE,"..",".."))
PUBD=os.path.join(REPO,"public","terminal","data"); AUD=os.path.join(HERE,"data","brand_audit.json"); SRC=os.path.join(HERE,"data","brand_sources.json")
UA="Mozilla/5.0 (compatible; TutchgrassBrandAuditor/1.0; +https://tutchgrass-terminal.onrender.com/terminal/report-cards/)"
GAP=1.5
def req(url,method="HEAD",rng=False,timeout=25):
    h={"User-Agent":UA,"Accept":"*/*"}
    if rng: h["Range"]="bytes=0-0"
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=h,method=method),timeout=timeout); c=r.status; r.close(); return c
    except urllib.error.HTTPError as e: return e.code
    except Exception: return None
CURL=shutil.which("curl")
def creq(url,head):
    """curl follows redirect chains (Dropbox, S3, Shopify CDN) more faithfully than urllib, whose redirect handling
    breaks some signed download links and would report a live COA as removed."""
    a=[CURL,"-s","-o","/dev/null","-w","%{http_code}","-L","--max-redirs","8","--max-time","25","-A",UA]+(["-I"] if head else ["-r","0-0"])+[url]
    try: c=int(subprocess.run(a,capture_output=True,text=True,timeout=40).stdout.strip() or 0); return c or None
    except Exception: return None
def check(url):
    if CURL:
        c=creq(url,True)
        if c is None or c in (403,404,405,400,429,501) or c>=500: c2=creq(url,False); c=c2 if c2 is not None else c
        if c is not None and c<400: return "ok",c
        if c in (404,410): return "removed",c
        return "unreachable",c
    c=req(url,"HEAD")
    if c is None or c in (403,405,400,429,501) or c>=500: c2=req(url,"GET",rng=True); c=c2 if c2 is not None else c
    if c is not None and c<400: return "ok",c
    if c in (404,410): return "removed",c
    return "unreachable",c
def norm(u): return urllib.parse.unquote(u.split("#")[0].split("?")[0]).strip().lower()
def pdf_links(html):
    s=set(x.replace("\\/","/") for x in re.findall(r"https?:(?:\\?/){2}[^\"'\s<>()]+?\.pdf(?:\?[^\"'\s<>()]*)?",html,re.I))
    s|={"https:"+x for x in re.findall(r"(?<=[\"'])//[^\"'\s<>()]+?\.pdf(?:\?[^\"'\s<>()]*)?",html,re.I)}
    return {u for u in s if not re.search(r"privacy|terms|policy|warranty|catalog|menu|brochure",u,re.I)}
def run():
    C=json.load(open(os.path.join(PUBD,"coas.json"))); meta=json.load(open(os.path.join(PUBD,"meta.json")))
    try: prev=json.load(open(AUD))
    except Exception: prev={}
    try: pages=json.load(open(SRC)).get("pages",{})
    except Exception: pages={}
    # 1. COA link check, one worker per host, GAP seconds apart
    byhost={}
    for c in C:
        if c.get("coa_url"): byhost.setdefault(urllib.parse.urlparse(c["coa_url"]).netloc,[]).append(c)
    links={}; lock=threading.Lock(); pl=prev.get("links",{})
    def worker(items):
        for i,c in enumerate(items):
            if i: time.sleep(GAP)
            st,code=check(c["coa_url"]); old=pl.get(c["id"],{})
            with lock: links[c["id"]]=dict(status=st,code=code,since=old.get("since") if old.get("status")==st else time.strftime("%Y-%m-%d"))
    ts=[threading.Thread(target=worker,args=(v,)) for v in byhost.values()]
    for t in ts: t.start()
    for t in ts: t.join()
    n=lambda s:sum(1 for v in links.values() if v["status"]==s)
    # 2. new-COA discovery on the brands' own lab-results pages
    known={norm(c["coa_url"]) for c in C if c.get("coa_url")}; ps=prev.get("sources",{}); sources={}
    for slug,page in pages.items():
        try:
            html=urllib.request.urlopen(urllib.request.Request(page,headers={"User-Agent":UA}),timeout=30).read().decode("utf-8","replace")
            found=sorted(pdf_links(html)); unscored=[u for u in found if norm(u) not in known]
            before=set(ps.get(slug,{}).get("queue_ids",[])) if ps.get(slug,{}).get("status")=="ok" else None
            ids=sorted(hashlib.sha1(norm(u).encode()).hexdigest()[:10] for u in unscored)
            new=[u for u in unscored if before is not None and hashlib.sha1(norm(u).encode()).hexdigest()[:10] not in before]
            sources[slug]=dict(page=page,status="ok",pdfs_on_page=len(found),scored_here=len(found)-len(unscored),queued=len(unscored),queue_ids=ids,
                               new_today=new[:25],queue_sample=unscored[:10])
        except Exception as e:
            old=ps.get(slug) or {}
            sources[slug]=dict(old,page=page,status="unreachable",error=str(e)[:80],new_today=[])
        time.sleep(GAP)
    queued=sum(s.get("queued",0) for s in sources.values()); new_today=sum(len(s.get("new_today",[])) for s in sources.values())
    when=time.strftime("%Y-%m-%d %H:%M")
    removed=sorted(([k,links[k]["since"]] for k in links if links[k]["status"]=="removed"))
    aud=dict(agent="brands",generated=when+" "+time.strftime("%Z"),coas_checked=len(links),links_ok=n("ok"),links_removed=n("removed"),links_unreachable=n("unreachable"),
             removed=removed,queued_coas=queued,new_coas_today=new_today,pages_ok=sum(1 for s in sources.values() if s["status"]=="ok"),pages=len(sources),
             note="Queued COAs are listed, not scored: scoring needs the PDF read and checked against the label.",links=links,sources=sources)
    if not links: print("Brand Auditor: no COA links checked; files unchanged"); return None
    json.dump(aud,open(AUD,"w"),indent=1)
    meta.update(checked=when.replace(" ","T"),coas_checked=len(links),links_ok=aud["links_ok"],links_removed=aud["links_removed"],links_unreachable=aud["links_unreachable"],
                queued_coas=queued,new_coas_today=new_today,source_pages_ok=aud["pages_ok"],source_pages=aud["pages"])
    json.dump(meta,open(os.path.join(PUBD,"meta.json"),"w"),indent=1)
    print(f"Brand Auditor: {aud['links_ok']}/{len(links)} COA links up, {aud['links_removed']} removed, {aud['links_unreachable']} unreachable; "
          f"{aud['pages_ok']}/{aud['pages']} lab pages read, {queued} unscored COAs queued ({new_today} new today)"); return aud
if __name__=="__main__":
    try: run()
    except Exception as e: print("Brand Auditor: unavailable:",e); sys.exit(0)
