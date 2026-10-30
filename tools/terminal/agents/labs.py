"""PRODUCT CHECKER agent (weekly): builds the licensed / accredited cannabis testing lab list and re-verifies the action
limits used by the in-browser COA checker (public/terminal/assets/product.js). Stdlib + curl (+ pdftotext for ORELAP).

Sources (official only; each one is fetched on its own, and a source that fails keeps its last good rows, marked stale):
  CA  Dept. of Cannabis Control public license search API (Testing Laboratory licenses)
  MA  Cannabis Control Commission open data (Independent Testing Laboratory licenses)
  CO  Marijuana Enforcement Division "Testing Facilities" certification sheet (per-panel certified-until dates)
  OR  OLCC marijuana license list (LABORATORY) + ORELAP cannabis laboratory accreditation list (PDF)
  WA  WSDA cannabis lab accreditation status table
  FL  Office of Medical Marijuana Use certified marijuana testing laboratories (CMTL) table
  ISO/IEC 17025: A2LA public directory (scopes that mention cannabis or hemp). ANAB and PJLA directories refuse
      automated reads, so they are linked for manual checks instead of scraped.
Writes tools/terminal/data/labs.json and public/terminal/data/labs.json. Never writes placeholder rows."""
import csv,io,json,os,re,subprocess,tempfile,time
from common import curl,save,load,text,ROOT,UA
from labs_limits import LIMITS
PUB=os.path.join(ROOT,"..","..","public","terminal","data","labs.json")
SUFFIX=r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|ltd|pbc|pllc|lp|the|dba)\b"
def norm(s): s=(s or "").lower().replace("&"," and "); s=re.sub(SUFFIX," ",s); return re.sub(r"[^a-z0-9]+"," ",s).strip()
def iso(s):
    s=(s or "").strip()
    for f in ("%Y-%m-%dT%H:%M:%S","%Y-%m-%d","%m/%d/%Y","%m-%d-%Y"):
        try: return time.strftime("%Y-%m-%d",time.strptime(s[:19] if "T" in s else s,f))
        except Exception: pass
    return None
def lab(name,state,source,license=None,status=None,dba=None,city=None,expires=None,panels=None,url=None,**kw):
    d=dict(name=re.sub(r"\s+"," ",name).strip(),dba=(re.sub(r"\s+"," ",dba).strip() or None) if dba else None,state=state,license=license,status=status,
           city=(city or "").strip().title() or None,expires=expires,panels=panels,source=source,url=url,**kw)
    d["keys"]=sorted({k for k in (norm(d["name"]),norm(d["dba"] or "")) if len(k)>=4})
    return d
# ---------- per-source fetchers: each returns a list of labs or raises ----------
def ca():
    u="https://as-dcc-pub-cann-w-p-002.azurewebsites.net/licenses/filteredSearch?licenseType=Commercial%20-%20%20Testing%20Laboratory&pageSize=100&pageNumber={}"
    out=[];p=1
    while True:
        j=json.loads(curl(u.format(p),40)); rows=j["data"]
        for r in rows:
            if (r.get("licenseStatus") or "").lower()!="active": continue
            out.append(lab(r["businessLegalName"],"CA","ca_dcc",license=r["licenseNumber"],status="Active",dba=r.get("businessDbaName") if r.get("businessDbaName") not in (None,"","Data Not Available") else None,
                city=r.get("premiseCity") if r.get("premiseCity")!="Data Not Available" else None,expires=iso(r.get("expirationDate")),url="https://search.cannabis.ca.gov/"))
        if not j["metadata"].get("hasNext"): break
        p+=1
    if not out: raise RuntimeError("no active CA labs returned")
    return out
def ma():
    rows=json.loads(curl("https://masscannabiscontrol.com/resource/l_licenses_all_details_public.json?$limit=50000",120).lstrip("\ufeff"))
    out=[lab(r["BUSINESS_NAME"],"MA","ma_ccc",license=r.get("LICENSE_NUMBER"),status=r.get("LICENSE_STATUS"),city=r.get("ESTABLISHMENT_CITY") or r.get("BUSINESS_CITY"),
             expires=iso(r.get("LIC_EXPIRATION_DATE")),url="https://masscannabiscontrol.com/licensing-tracker/")
         for r in rows if r.get("LICENSE_TYPE")=="Independent Testing Laboratory" and (r.get("LICENSE_STATUS") or "").lower()=="active"]
    if not out: raise RuntimeError("no MA testing labs")
    return out
CO_PANELS={"Elemental Impurities":"heavy_metals","Microbials":"microbials","Mycotoxins":"mycotoxins","Pesticides":"pesticides","Potency":"potency","Residual Solvents":"residual_solvents","Water Activity":"water_activity"}
def co():
    rows=list(csv.DictReader(io.StringIO(curl("https://docs.google.com/spreadsheets/d/1ZuxyHg-5Apy4pHrNQNndBZPP8ulzCfOz4fzlHvs1Xxc/export?format=csv",60).lstrip("\ufeff"))))
    out=[]
    for r in rows:
        if not (r.get("Licensee Name") or "").strip() or not (r.get("License Number") or "").strip(): continue
        pan={v:(iso(r.get(k)) or (r.get(k) or "").strip() or None) for k,v in CO_PANELS.items()}
        out.append(lab(r["Licensee Name"].title(),"CO","co_med",license=r["License Number"].strip(),status="Certified",dba=(r.get("DBA") or "").title(),city=r.get("City"),panels=pan,
                       url="https://med.colorado.gov/licensee-information-and-lookup-tool"))
    if not out: raise RuntimeError("no CO labs")
    return out
def orx():
    rows=list(csv.DictReader(io.StringIO(curl("https://data.oregon.gov/api/v3/views/q32u-cmam/export.csv?accessType=DOWNLOAD",120).lstrip("\ufeff"))))
    seen={};
    for r in rows:
        if (r.get("License Type") or "").upper()!="LABORATORY" or (r.get("License Status") or "").upper()!="ACTIVE": continue
        seen[r["License Number"]]=lab(r.get("Business Name") or r["Business Licensee"],"OR","or_olcc",license=r["License Number"],status="Active",dba=r.get("Business Licensee"),
            city=((r.get("County") or "").title()+" County") if r.get("County") else None,expires=iso(r.get("Expiration Date")),url="https://www.oregon.gov/olcc/marijuana/pages/default.aspx")
    out=list(seen.values())
    if not out: raise RuntimeError("no OR labs")
    return out
def orelap():
    url="https://www.oregon.gov/oha/PH/LABORATORYSERVICES/ENVIRONMENTALLABORATORYACCREDITATION/Documents/canna-list.pdf"
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        r=subprocess.run(["curl","-sL","-m","60","-A",UA,"-o",f.name,url]); 
        if r.returncode: raise RuntimeError("curl failed")
        t=subprocess.run(["pdftotext","-layout",f.name,"-"],capture_output=True,text=True).stdout
    upd=re.search(r"Updated:\s*([\d/]+)",t); out=[]
    for line in t.splitlines():
        m=re.match(r"^(\S.*?)\s{2,}((?:[PO]\s+){5,}[PO])\s*$",line.strip())
        if m: out.append(lab(m.group(1),"OR","or_orelap",status="ORELAP accredited",url=url,codes=m.group(2).split()))
    if not out: raise RuntimeError("ORELAP list not parsed")
    return out,(iso(upd.group(1)) if upd else None)
def wa():
    h=curl("https://agr.wa.gov/departments/cannabis",60); out=[]
    for tb in re.findall(r"<table.*?</table>",h,re.S):
        rows=[[text(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>",tr,re.S)] for tr in re.findall(r"<tr.*?</tr>",tb,re.S)]
        if not rows or "Accreditation Status" not in rows[0]: continue
        hd=rows[0]
        for r in rows[1:]:
            if len(r)!=len(hd) or not r[0]: continue
            d=dict(zip(hd,r)); pan={k.lower().replace(" ","_"):v for k,v in d.items() if k and k!="Accreditation Status"}
            out.append(lab(r[0],"WA","wa_wsda",status=d["Accreditation Status"],panels={("potency" if k=="cannabinoids" else k):v for k,v in pan.items()},url="https://agr.wa.gov/departments/cannabis"))
    upd=re.search(r"updated as of ([A-Z][a-z]+ \d+)(?:st|nd|rd|th)?, (\d{4})",h)
    if not out: raise RuntimeError("WSDA table not found")
    return out,(time.strftime("%Y-%m-%d",time.strptime(f"{upd.group(1)} {upd.group(2)}","%B %d %Y")) if upd else None)
def fl():
    h=curl("https://knowthefactsmmj.com/cmtl/",40); out=[]
    for tb in re.findall(r"<table.*?</table>",h,re.S):
        rows=[[text(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>",tr,re.S)] for tr in re.findall(r"<tr.*?</tr>",tb,re.S)]
        if not rows or "Date Certified" not in " ".join(rows[0]): continue
        hd=rows[0]
        for r in rows[1:]:
            if len(r)!=len(hd) or not r[0]: continue
            d=dict(zip(hd,r))
            out.append(lab(r[0],"FL","fl_ommu",status="Certified",address=d.get("Address") or None,certified=iso(d.get("Date Certified")),url="https://knowthefactsmmj.com/cmtl/"))
    if not out: raise RuntimeError("OMMU table not found")
    return out
def a2la():
    out={}
    for kw in ("cannabis","hemp"):
        r=subprocess.run(["curl","-sL","-m","90","-A",UA,"-H","Content-Type: application/json; charset=utf-8","-X","POST",
            "https://customer.a2la.org/index.cfm?event=directory.search","-d",json.dumps({"criteria":{"keyword":kw}})],capture_output=True)
        if r.returncode: raise RuntimeError("a2la curl failed")
        for x in json.loads(r.stdout.decode("utf-8","replace")):
            if "17025" not in (x.get("programFieldPath") or ""): continue
            k=x["labPID"]; e=out.get(k)
            if e: e["programs"]=sorted(set(e["programs"])|{x["programFieldPath"]}); continue
            out[k]=dict(name=x["labName"].strip(),location=x.get("location"),country=x.get("country"),cert=x.get("accreditationCode"),programs=[x["programFieldPath"]],
                        expires=iso(x.get("accreditationExpirationDate")),body="A2LA",keys=[k2 for k2 in [norm(x["labName"])] if len(k2)>=4],
                        url=f"https://customer.a2la.org/index.cfm?event=directory.detail&labPID={k}")
        time.sleep(1)
    if not out: raise RuntimeError("A2LA returned nothing")
    return sorted(out.values(),key=lambda d:(d["name"],d["cert"] or ""))
SOURCES=[("ca_dcc","California Department of Cannabis Control (license search)","https://search.cannabis.ca.gov/",ca),
 ("ma_ccc","Massachusetts Cannabis Control Commission (open data)","https://masscannabiscontrol.com/open-data/data-catalog/",ma),
 ("co_med","Colorado Marijuana Enforcement Division (testing facility certifications)","https://med.colorado.gov/licensee-information-and-lookup-tool",co),
 ("or_olcc","Oregon Liquor and Cannabis Commission (license list)","https://data.oregon.gov/d/q32u-cmam",orx),
 ("or_orelap","Oregon ORELAP cannabis laboratory accreditation list","https://www.oregon.gov/oha/PH/LABORATORYSERVICES/ENVIRONMENTALLABORATORYACCREDITATION/Pages/cannabis.aspx",orelap),
 ("fl_ommu","Florida Office of Medical Marijuana Use (certified testing labs)","https://knowthefactsmmj.com/cmtl/",fl),
 ("wa_wsda","Washington State Dept. of Agriculture (cannabis lab accreditation)","https://agr.wa.gov/departments/cannabis",wa)]
MANUAL=[dict(body="ANAB",url="https://search.anab.org/public/",note="ANAB directory blocks automated reads; check the certificate number by hand."),
        dict(body="PJLA",url="https://www.pjlabs.com/search-accredited-organizations",note="PJLA directory blocks automated reads; check the certificate number by hand.")]
def check_limits(prev):
    out=[];pv={l["id"]:l for l in (prev or {}).get("limits",[])}
    for L in LIMITS:
        d={k:v for k,v in L.items() if k!="must"}
        try:
            t=text(curl(L["url"],40)).replace("µ","?").replace("\u2009"," ")
            if len(t)<500: raise RuntimeError("source refused a scripted read")
            miss=[m for m in L["must"] if re.sub(r"\s+"," ",m.replace("µ","?")) not in t]
            d["status"]="verified" if not miss else "needs review"; d["missing"]=miss or None; d["verified"]=time.strftime("%Y-%m-%d")
        except Exception as e:
            p=pv.get(L["id"]) or {}; d["error"]=str(e)[:80]
            if L.get("hand_checked"): d["status"]="hand-checked"; d["verified"]=L["hand_checked"]
            else: d["status"]="unreachable" if p.get("status")!="verified" else "verified (last week)"; d["verified"]=p.get("verified")
        out.append(d)
    return out
def run():
    prev=load("labs.json") or {}; pl={s["id"]:s for s in prev.get("sources",[])}; labs=[];srcs=[]
    for sid,name,url,fn in SOURCES:
        s=dict(id=sid,name=name,url=url)
        try:
            r=fn(); upd=None
            if isinstance(r,tuple): r,upd=r
            labs+=r; s.update(status="ok",count=len(r),checked=time.strftime("%Y-%m-%d %H:%M %Z"),list_updated=upd)
        except Exception as e:
            old=[l for l in prev.get("labs",[]) if l["source"]==sid]; labs+=old
            p=pl.get(sid,{}); s.update(status="stale" if old else "unavailable",count=len(old),checked=p.get("checked"),list_updated=p.get("list_updated"),error=str(e)[:120])
        srcs.append(s); print(sid,s["status"],s["count"])
    acc=[]; a=dict(id="a2la",name="A2LA directory (ISO/IEC 17025 scopes mentioning cannabis or hemp)",url="https://customer.a2la.org/index.cfm?event=directory.index")
    try: acc=a2la(); a.update(status="ok",count=len(acc),checked=time.strftime("%Y-%m-%d %H:%M %Z"))
    except Exception as e:
        acc=prev.get("accredited",[]); p=pl.get("a2la",{}); a.update(status="stale" if acc else "unavailable",count=len(acc),checked=p.get("checked"),error=str(e)[:120])
    srcs.append(a); print("a2la",a["status"],a["count"])
    lim=check_limits(prev)
    obj=dict(agent="Product Checker",sources=srcs,manual=MANUAL,labs=sorted(labs,key=lambda l:(l["state"],l["name"])),accredited=acc,limits=lim,
             counts=dict(state_labs=len(labs),states=sorted({l["state"] for l in labs}),accredited=len(acc),limits_verified=sum(1 for l in lim if l["status"] in ("verified","hand-checked","verified (last week)")),limits=len(lim)),
             note="Lists come straight from the regulators and accreditation bodies named in sources. A lab missing here may be licensed in a state we do not read yet.")
    save("labs.json",obj); os.makedirs(os.path.dirname(PUB),exist_ok=True); json.dump(obj,open(PUB,"w"),separators=(",",":"))
    return obj
if __name__=="__main__":
    o=run(); print("labs",o["counts"])
