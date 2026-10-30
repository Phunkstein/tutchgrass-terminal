"""Generic reader for a dispensary's own public deals page (used by deals.py). Stdlib only.

It turns the server-rendered HTML into text lines and keeps only lines that state a concrete deal
(percent off, BOGO, N for $X, $X off, happy hour, ...). It never invents or rewrites a deal: the text kept
is the page's own wording (a weekday/date heading from the page may be put in front of it).
Date rules: a page/section/line whose stated end date has passed is dropped, one that starts later is dropped,
and a page whose only date range is in the past is not used at all. Missing years are read as the current year.
"""
import re,html,datetime as dt
TODAY=dt.date.today()
MON={m:i+1 for i,m in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"])}
MONTHS="january|february|march|april|may|june|july|august|september|october|november|december"
DEAL=re.compile(r'\d{1,2}\s?%\s?(?:off|back)|\bBOGO\b|\bB[1-9]G[1-9]\b|\bbuy (?:one|1|two|2|three|3|four|4|any (?:\w+ )?\w+),? (?:\w+ )?get|\$\s?\d+(?:\.\d\d)? off|\b\d+\s?(?:for|/)\s?\$\s?\d+|happy hour|\bfree\b.{0,40}\b(?:with|when)\b|\$\d+(?:\.\d\d)?\s*(?:eighths|8ths|ounces?|oz\b|1/8|3\.5g|prerolls?|pre-rolls?|half)|\bpenny\b|\$0?\.01',re.I)
SKIP=re.compile(r'^home\s*/|\bround (?:up|down)\b|\b\d+\s*points\b|\brewards? (?:include|members|program)|redeem|refer a friend|searching for|looking for|\?\s*$|you save|points? ?=|earn \d+ points?|\bearn \d|reward points|loyalty points|sign up|subscribe|newsletter|text club|join (?:our|the)|copyright|©|\bterms\b.*\bapply\b$|unsubscribe|cookie|javascript',re.I)
BLOCK=re.compile(r'</?(?:p|li|h[1-6]|br|div|tr|td|th|section|article|ul|ol|table|header|footer|button|figcaption|dt|dd)\b[^>]*>',re.I)
WEEKDAY=re.compile(r'\b(?:mon|tues?|wed(?:nes)?|thu(?:rs?)?|fri|sat(?:ur)?|sun)(?:day)?s?\b',re.I)
DAYHEAD=re.compile(r'^(?:[^\w$]*)(?:(?:mon|tues?|wed(?:nes)?|thu(?:rs?)?|fri|sat(?:ur)?|sun)(?:day)?s?|every ?day|weekends?)\b',re.I)
EXP=re.compile(r'^(?:[^\w]*)(?:expires?|ends?|sale ends|bundle ends|deal ends|offer ends|valid (?:through|thru|until)|through|thru|good through|while supplies last through)\b',re.I)

def lines(h):
    h=re.sub(r'<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>|<!--.*?-->|<svg.*?</svg>|<template.*?</template>','',h,flags=re.S|re.I)
    h=BLOCK.sub('\n',h); t=html.unescape(re.sub(r'<[^>]+>',' ',h))
    out=[]
    for l in t.split('\n'):
        l=re.sub(r'[ \t\r\u00a0\u200b\ufeff]+',' ',l).strip()
        l=re.sub(r'\s+([.,!:;])',r'\1',l)
        if l: out.append(l)
    return out
def _d(mo,d,y):
    try: return dt.date(y,mo,d)
    except ValueError: return None
def dates(s):
    """Dates mentioned in s, in order: list of (pos, date). 'October 29-31' gives Oct 29 and Oct 31."""
    raw=[]
    for m in re.finditer(r'(?<![\d$.])(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?![\d%])',s):
        mo,d=int(m.group(1)),int(m.group(2))
        if not(1<=mo<=12 and 1<=d<=31): continue
        if re.match(r'\s*(?:g|mg|oz|for|\$)',s[m.end():m.end()+4],re.I) or s[max(0,m.start()-1):m.start()]=="$": continue  # 2/$45, 1/8 oz
        if mo==1 and d in(2,4,8): continue   # 1/2, 1/4, 1/8 (sizes)
        y=int(m.group(3)) if m.group(3) else None
        if y and y<100: y+=2000
        raw.append((m.start(),mo,d,y))
    for m in re.finditer(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*[-–—]\s*(\d{1,2})(?:st|nd|rd|th)?\b)?(?:,?\s+(20\d\d))?\b',s,re.I):
        mo=MON[m.group(1)[:3].lower()]; y=int(m.group(4)) if m.group(4) else None
        raw.append((m.start(),mo,int(m.group(2)),y))
        if m.group(3): raw.append((m.start(3),mo,int(m.group(3)),y))
    res=[]
    for pos,mo,d,y in sorted(raw):
        if y is None:
            x=_d(mo,d,TODAY.year)
            if x and (x-TODAY).days>200: x=_d(mo,d,TODAY.year-1)
            elif x and (TODAY-x).days>200: x=_d(mo,d,TODAY.year+1)
        else: x=_d(mo,d,y)
        if x: res.append((pos,x))
    return res
def span(s):
    """(start, end) stated in s, or None."""
    ds=dates(s)
    if not ds: return None
    a,b=ds[0][1],ds[-1][1]
    if b<a and (a-b).days>200: b=b.replace(year=b.year+1)
    return a,b
def status(s,single_is_day=False):
    """'past' / 'future' / 'ok' / None for the dates stated in s."""
    ds=dates(s)
    if not ds: return None,None
    if len(ds)>=2 or single_is_day:
        a,b=span(s)
        if b<TODAY: return "past",b
        if a>TODAY+dt.timedelta(days=0 if single_is_day else 1): return "future",b
        return "ok",b
    pos,x=ds[0]; pre=s[max(0,pos-30):pos]
    if re.search(r'expir|through|thru|until|till|ends?\b|valid|by\s*$',pre,re.I):
        return ("past" if x<TODAY else "ok"),x
    if re.search(r'\b(?:on|only)\s*$',pre,re.I) or re.search(r'\bonly\b',s[pos:pos+30],re.I):
        return ("past" if x<TODAY else "future" if x>TODAY else "ok"),x
    return None,None
def vague(l):
    if l.rstrip().endswith(':'): return True
    if not re.search(r'\d|bogo|b\dg\d|\bfree\b|penny',l,re.I): return True
    rest=WEEKDAY.sub(' ',DEAL.sub(' ',l)); rest=re.sub(r'\b(?:off|for|get|buy|select|all|any|save|up to|deal|deals|special|specials|sale|now|only|each|ea)\b',' ',rest,flags=re.I)
    return len(re.sub(r'[^A-Za-z]','',rest))<7

EVERGREEN=re.compile(r'\bevery\b|\beveryday\b|first[- ](?:time|visit|order)|\bveterans?\b|\bseniors?\b|\b55\+|birthday|\bstudents?\b|\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b|\b(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\s*[-–]\s*(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\b|\bdaily\b',re.I)
def _evergreen(t,head):
    """A standing offer (every Tuesday, veterans, first visit) sitting under a dated heading is not limited to that date."""
    m=EVERGREEN.search(t)
    if not m: return False
    hd=WEEKDAY.search(head or "")
    return not (hd and hd.group(0).lower()[:3] in t.lower())
def extract(h,cfg):
    """cfg keys (all optional): start/end (text markers), range (regex for the page's stated date range),
    range_required, heads (extra heading regex), regions [(regex,state,city,store)], prefix_prev, skip, maxlen, dated_only, month_guard."""
    L=lines(h); txt="\n".join(L)
    if cfg.get("start"):
        m=re.search(cfg["start"],txt)
        if not m: raise RuntimeError("deals section not found on the page (layout changed?)")
        txt=txt[m.start():]
    if cfg.get("end"):
        m=re.search(cfg["end"],txt[1:])
        if m: txt=txt[:m.start()+1]
    if cfg.get("month_guard",True):
        mg=re.search(rf'\b({MONTHS})\b(?:\s+20\d\d)?\s+(?:cannabis |weed |dispensary |daily |weekly )?(?:deals|specials|savings|promotions)\b',txt[:4000],re.I)
        if mg and MON[mg.group(1)[:3].lower()]!=TODAY.month: raise RuntimeError(f"page is headed “{mg.group(0)}”, not this month; not used")
    page_valid,page_until="",None
    if cfg.get("range"):
        m=re.search(cfg["range"],txt,re.I)
        sp=span(m.group(0)) if m else None
        if not sp:
            if cfg.get("range_required",True): raise RuntimeError("no current date stated on the page; not used")
        else:
            a,b=sp
            if b<TODAY: raise RuntimeError(f"page's stated dates (“{m.group(0).strip()[:60]}”) have passed; not used")
            if a>TODAY+dt.timedelta(days=1): raise RuntimeError(f"page's stated dates (“{m.group(0).strip()[:60]}”) start later; not used")
            lab=re.sub(r'\s+',' ',m.group(0)).strip()
            page_valid=lab+("" if re.search(r'20\d\d|\d/\d{1,2}/\d\d',lab) else " (year not stated)"); page_until=b
    out=[]; head=""; head_until=None; head_dead=False; prev=""; block=[]; region=None
    for l in txt.split("\n"):
        if len(l)<3: continue
        for rx,stt,city,store in cfg.get("regions",[]):
            if len(l)<=80 and re.search(rx,l,re.I): region=(stt,city,store); head=""; head_dead=False; head_until=None
        isdeal=bool(DEAL.search(l)) and len(l)<=cfg.get("maxlen",240)
        if not isdeal:
            if EXP.search(l) and len(l)<=80:           # an "Expires 10/5/25" line closes the deals just above it
                stt_,x=status(l if re.search(r'expir|through|thru|until|ends?|valid',l,re.I) else "through "+l)
                if stt_=="past":
                    for d in block[-3:]: d["_drop"]=True
                elif x:
                    for d in block[-3:]:
                        if not _evergreen(d["deal"],""): d["until"]=d["until"] or x.isoformat(); d["valid"]=d["valid"] or l.strip()
                block=[]
            elif len(l)<=60 and not re.match(r'^\s*\*',l) and not re.search(r'do not|exclude',l,re.I) and not re.search(r'\d{1,2}(?::\d\d)?\s*[ap]\.?m\b.{0,4}[-–]|%|\$|\boff\b|bogo',l,re.I) and not l.rstrip().endswith('.') and (
                    DAYHEAD.match(l) or (dates(l) and len(l)<=50) or (cfg.get("heads") and re.search(cfg["heads"],l,re.I))):
                ds=dates(l); block=[]
                if ds and not DAYHEAD.match(l) and (re.search(r'20\d\d',l) or re.match(r'^\W*(?:posted|published|updated|by)\b|^\s*/',l,re.I)) and len(ds)==1:
                    pass                                   # a post's publish date, not a deal day
                else:
                    head=l.strip(' :-–|')
                    if ds:
                        stt_,x=status(l,single_is_day=len(ds)==1)
                        soon=stt_=="future" and x and (x-TODAY).days<=2   # e.g. tomorrow's Halloween deal: kept, labeled with its day
                        head_dead=stt_=="past" or (stt_=="future" and not soon); head_until=x if stt_=="ok" or soon else None
                    else: head_dead=False; head_until=None
            elif len(l)<=60 and not re.match(r'^\s*\*',l) and re.search(r'\b(?:deals?|specials?|discounts?|savings|offers?|promotions?)\b',l,re.I) and not dates(l):
                head="" if not DAYHEAD.match(l) else l.strip(' :-–|'); head_dead=False; head_until=None   # a new section starts
            prev=l if (3<=len(l)<=40 and re.search(r'[A-Za-z]{3}',l) and not re.search(r'[.:!?$]\s*$|\$|\d{1,2}/\d|\b(?:skip|shop|menu|view|home|deals?|sale|promotions?|bundle|previously|check out|in stock|order|learn|more|location|hours|open)\b',l,re.I) and not DAYHEAD.match(l)) else ""
            continue
        if head_dead or SKIP.search(l) or (cfg.get("skip") and re.search(cfg["skip"],l,re.I)): continue
        stt_,x=status(l)
        if stt_ in("past","future"): continue
        hu=head_until
        if hu and not x and _evergreen(l,head): hu=None
        if cfg.get("dated_only") and not (x or hu): continue
        t=l; short=len(l)<45 or vague(l)
        if cfg.get("prefix_prev") and prev and short and prev.lower() not in l.lower(): t=f"{prev}: {l}"
        hv=""
        if head and not head_until and not hu and not WEEKDAY.search(l) and not re.search(r'every ?day|daily',l,re.I):
            if (short or vague(t)) and head.lower()[:8] not in t.lower(): t=f"{head}: {t}"
            else: hv=head[:70]
        t=re.sub(r'^\d\.\s+','',re.sub(r'\s+',' ',t).strip(" |·-–"))
        if cfg.get("chain_word"): t=re.sub(r'\s*[|–—-]\s*(?:The )?'+cfg["chain_word"]+r'\b.{0,50}$','',t,flags=re.I)
        if vague(t): continue
        dm=DEAL.search(t); sig=re.sub(r'\s','',dm.group(0).lower()) if dm else ""
        if out and sig and out[-1].get("_sig")==sig and len(t)>len(out[-1]["deal"])+20: continue   # long blurb repeating the deal just above
        k=re.sub(r'[^a-z0-9]','',t.lower())
        if any(k in o["_k"] or o["_k"] in k for o in out): continue
        st_=region[0] if region else None
        until=(x or hu or page_until)
        everyday=bool(DAYHEAD.match(head) and not hu) or bool(re.search(r'\bevery ?day\b|\bdaily\b|\bevery (?:mon|tues|wednes|thurs|fri|satur|sun)day\b',t,re.I))
        d={"_k":k,"_sig":sig,"deal":t,"valid":(head if hu else "") or hv or page_valid,
           "until":until.isoformat() if until else "","kind":"everyday" if everyday and not until else "limited","region":region}
        out.append(d); block.append(d); prev=""
    return [ {k:v for k,v in d.items() if k not in("_k","_sig")} for d in out if not d.get("_drop")]
