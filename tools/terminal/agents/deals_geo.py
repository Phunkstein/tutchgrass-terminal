"""Deals agent geocoding (TEST): gives every deal the coordinates of the store(s) it applies to, so the Deals tab can
sort by distance from a ZIP/city the visitor types (or their browser location, which never leaves their device).

Sources, all free and public:
  - tools/terminal/data/deals_stores.json: store street addresses read from each chain's own public pages.
  - US Census Bureau geocoder (batch endpoint, no key) turns an address into lat/lon. If Census has no match, one
    OpenStreetMap Nominatim lookup (max 1 request/second, identifying User-Agent, per its usage policy) is tried;
    if that fails too, the ZIP's Census ZCTA centroid is used and the store is marked approximate.
  - public/terminal/data/geo/place.csv (Census 2023 Gazetteer places, public domain) gives a city centre for a deal
    whose city is known but whose street address is not (marked approximate, 'city').
Every result is cached in tools/terminal/data/deals_geo.json (committed), so the 3x-daily job only geocodes
addresses it has never seen; a normal run makes no geocoding requests at all.

How a deal gets locations (attach()):
  1. a store-specific deal (e.g. 'House of Dank Woodward') uses the chain address whose street matches that name;
  2. otherwise each city the deal lists uses the chain's stores in that city, or that city's centre if none known;
  3. a statewide/chain-wide deal (no city) uses every known store of that chain in the state;
  4. if no store and no city is known it is marked statewide (no coordinates; shown as 'statewide' on the tab).
"""
import csv,io,json,os,re,subprocess,time,urllib.parse
HERE=os.path.dirname(os.path.abspath(__file__))
DATA=os.path.join(os.path.dirname(HERE),"data")
GEO=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),"public","terminal","data","geo")
STORES=os.path.join(DATA,"deals_stores.json"); CACHE=os.path.join(DATA,"deals_geo.json")
UA_GEO="CannabisAgentTerminal-Deals/1.0 (store geocoding, about 1 request per new store; contact tutchgrass@mail.grokbot.com)"
# names on dispensary pages that are not Census place names
ALIAS={("New York (Manhattan)","NY"):"New York",("Manhattan","NY"):"New York",("Brooklyn","NY"):"New York",
       ("Koreatown","CA"):"Los Angeles",("Washington","DC"):"Washington",("Mt Pleasant","MI"):"Mount Pleasant",
       ("St. Louis","MO"):"St. Louis",("St Charles","MO"):"St. Charles",("St Clair","MO"):"St. Clair"}

def _load(p,d):
    try: return json.load(open(p))
    except Exception: return d
def oneline(a): return f'{a["street"]}, {a["city"]}, {a["state"]} {a["zip"]}'
_PL=None
def places():
    global _PL
    if _PL is None:
        _PL={}
        for ln in open(os.path.join(GEO,"place.csv"),encoding="utf-8"):
            n,st,la,lo=ln.rstrip("\n").split("|"); _PL[(n.lower(),st)]=(int(la)/100,int(lo)/100)
    return _PL
def city_ll(city,st):
    c=ALIAS.get((city,st),city); P=places()
    for k in (c,c.replace("St. ","Saint "),c.replace("Saint ","St. "),c.replace("Mt ","Mount ")):
        if (k.lower(),st) in P: return P[(k.lower(),st)]
    return None
_ZIP=None
def zip_ll(z):
    global _ZIP
    if _ZIP is None:
        _ZIP={}
        for ln in open(os.path.join(GEO,"zip.csv")):
            k,la,lo=ln.rstrip("\n").split(","); _ZIP[k]=(int(la)/100,int(lo)/100)
    return _ZIP.get(z)

def census_batch(rows):
    """rows: [(id, street, city, state, zip)] -> {id: (lat, lon, matched_address)}; up to 10,000 per request."""
    buf=io.StringIO(); csv.writer(buf).writerows(rows)
    tmp=os.path.join("/tmp","deals_geo_batch.csv"); open(tmp,"w").write(buf.getvalue())
    r=subprocess.run(["curl","-s","-m","300","-A",UA_GEO,"-F",f"addressFile=@{tmp}","-F","benchmark=Public_AR_Current",
                      "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"],capture_output=True)
    if r.returncode: raise RuntimeError(f"census batch: curl {r.returncode}")
    out={}
    for row in csv.reader(io.StringIO(r.stdout.decode("utf-8","replace"))):
        if len(row)>=6 and row[2]=="Match" and row[5]:
            lon,lat=map(float,row[5].split(",")); out[row[0]]=(round(lat,5),round(lon,5),row[4])
    return out
def nominatim(a):
    q=urllib.parse.urlencode({"street":a["street"],"city":a["city"],"state":a["state"],"postalcode":a["zip"],
                              "country":"us","format":"jsonv2","limit":1})
    time.sleep(1.1)
    r=subprocess.run(["curl","-s","-m","30","-A",UA_GEO,"https://nominatim.openstreetmap.org/search?"+q],capture_output=True)
    try: j=json.loads(r.stdout or b"[]")
    except Exception: j=[]
    return (round(float(j[0]["lat"]),5),round(float(j[0]["lon"]),5),j[0].get("display_name","")) if j else None

def geocode_all(offline=False):
    """Geocode every store address not yet cached. Returns the stores dict with lat/lon/precision filled in."""
    S=_load(STORES,{"stores":{}})["stores"]; C=_load(CACHE,{"about":"","addresses":{}})
    A=C.setdefault("addresses",{}); new=[]
    for grp in S.values():
        for a in grp:
            k=oneline(a)
            if k not in A: new.append(a)
    if new and not offline:
        try: got=census_batch([(str(i),a["street"],a["city"],a["state"],a["zip"]) for i,a in enumerate(new)])
        except Exception as e: print("deals_geo: census batch failed:",e); got={}
        for i,a in enumerate(new):
            k=oneline(a)
            if str(i) in got: la,lo,m=got[str(i)]; A[k]={"lat":la,"lon":lo,"precision":"address","source":"US Census geocoder","matched":m}; continue
            n=nominatim(a)
            if n: A[k]={"lat":n[0],"lon":n[1],"precision":"address","source":"OpenStreetMap Nominatim","matched":n[2][:120]}; continue
            z=zip_ll(a["zip"])
            if z: A[k]={"lat":z[0],"lon":z[1],"precision":"zip","source":"Census ZCTA centroid (address not matched)"}
        C["about"]=("Geocoding cache for the Deals tab: store address -> lat/lon. US Census geocoder first, OpenStreetMap "
                    "Nominatim second, ZIP (Census ZCTA) centroid last. Cached results are never re-requested.")
        json.dump(C,open(CACHE,"w"),indent=1)
    for grp in S.values():
        for a in grp:
            g=A.get(oneline(a))
            if g: a.update(lat=g["lat"],lon=g["lon"],precision=g["precision"])
    return S

# deal "cities" that are really regions: kept statewide (no store list) but only shown to people inside the box
REGION={("Upper Peninsula","MI"):[45.08,-90.42,47.5,-83.35]}   # lat_min, lon_min, lat_max, lon_max
def _norm(s): return re.sub(r'[^a-z0-9 ]','',re.sub(r'\b(street|st|road|rd|avenue|ave)\b','',s.lower())).split()
def attach(deals,offline=False):
    """Adds d['loc'] (indices into the returned store list) and d['geo'] ('store' | 'city' | 'statewide') to every
    deal. Returns (locations, stats). A location is {chain,name,addr,city,state,lat,lon,precision}."""
    S=geocode_all(offline); locs=[]; idx={}
    def add(chain,name,addr,city,st,la,lo,prec):
        k=(chain,addr or "",city,st)
        if k not in idx: idx[k]=len(locs); locs.append({"chain":chain,"name":name,"addr":addr,"city":city,"state":st,"lat":la,"lon":lo,"precision":prec})
        return idx[k]
    for d in deals:
        grp=[a for a in S.get(f'{d["state"]}|{d["chain"]}',[]) if "lat" in a]
        L=[]
        # 1. a store-specific deal: words left after removing the chain and the city name (e.g. '8 Mile', 'Woodward')
        rest=d["store"]
        for w in [d["chain"]]+d["cities"]+[d["city"]]: rest=rest.replace(w,"") if w else rest
        rest=re.sub(r'\(.*?\)|[–-]','',rest).strip()
        if rest and not re.search(r'stores|locations|all\b|listed',rest,re.I):
            key=_norm(rest)
            hit=[a for a in grp if key and all(t in _norm(a["street"]) for t in key)]
            if len(hit)==1: a=hit[0]; L=[add(d["chain"],d["store"],a["street"],a["city"],a["state"],a["lat"],a["lon"],a["precision"])]
        # 2. cities the deal lists
        if not L:
            for c in d["cities"]:
                here=[a for a in grp if a["city"].lower()==c.lower() or city_ll(a["city"],a["state"])==city_ll(c,d["state"])!=None]
                if here:
                    for a in here: L.append(add(d["chain"],f'{d["chain"]} {a["city"]}',a["street"],a["city"],a["state"],a["lat"],a["lon"],a["precision"]))
                else:
                    ll=city_ll(c,d["state"])
                    if ll: L.append(add(d["chain"],d["store"] if len(d["cities"])==1 else f'{d["chain"]} {c}',"",c,d["state"],ll[0],ll[1],"city"))
        # 3. statewide / chain-wide: every known store of the chain in the state
        if not L and not d["cities"]:
            for a in grp: L.append(add(d["chain"],f'{d["chain"]} {a["city"]}',a["street"],a["city"],a["state"],a["lat"],a["lon"],a["precision"]))
        d.pop("region",None)
        if not L:
            for c in [d["city"]]+d["cities"]:
                if (c,d["state"]) in REGION: d["region"]={"name":c,"bbox":REGION[(c,d["state"])]}; break
        d["loc"]=sorted(set(L))
        d["geo"]="statewide" if not L else ("store" if any(locs[i]["precision"]!="city" for i in L) else "city")
    st={"locations":len(locs),"store_points":sum(1 for l in locs if l["precision"]!="city"),
        "city_points":sum(1 for l in locs if l["precision"]=="city"),
        "deals_store":sum(1 for d in deals if d["geo"]=="store"),"deals_city":sum(1 for d in deals if d["geo"]=="city"),
        "deals_statewide":sum(1 for d in deals if d["geo"]=="statewide")}
    return locs,st

if __name__=="__main__":
    S=geocode_all()
    n=sum(len(v) for v in S.values()); ok=sum(1 for v in S.values() for a in v if "lat" in a)
    from collections import Counter
    print(f"deals_geo: {ok}/{n} store addresses have coordinates",Counter(a.get("precision","none") for v in S.values() for a in v))
