"""Shared NCBI E-utilities fetcher used by every PubMed-reading agent.
NCBI rules (https://www.ncbi.nlm.nih.gov/books/NBK25497/): at most 3 requests/second without an API key, and every
request should carry `tool` and `email`. This module enforces a process-wide minimum gap between requests, adds
tool/email (and api_key if NCBI_API_KEY is set, which allows 10 req/s), and backs off on HTTP 429/5xx (and retries a transient 400 twice).
Env (all optional, none are secrets except NCBI_API_KEY): NCBI_TOOL, NCBI_EMAIL, NCBI_API_KEY."""
import os,time,urllib.request,urllib.error
TOOL=os.environ.get("NCBI_TOOL") or "tutchgrass-terminal"
EMAIL=os.environ.get("NCBI_EMAIL") or "tutchgrass@mail.grokbot.com"
KEY=os.environ.get("NCBI_API_KEY") or ""
GAP=0.12 if KEY else 0.36          # seconds between requests: < 10/s with a key, < 3/s without
UA={"User-Agent":"tutchgrass-terminal/1 (public research hub; https://tutchgrass-terminal.onrender.com/terminal/)"}
_last=[0.0]
def _sign(u):
    if "eutils.ncbi.nlm.nih.gov" not in u or "tool=" in u: return u
    from urllib.parse import quote
    u+=("&" if "?" in u else "?")+f"tool={quote(TOOL)}&email={quote(EMAIL)}"
    return u+(f"&api_key={quote(KEY)}" if KEY else "")
def fetch(u,timeout=40,tries=5):
    u=_sign(u); err=None
    for i in range(tries):
        wait=_last[0]+GAP-time.time()
        if wait>0: time.sleep(wait)
        _last[0]=time.time()
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=timeout).read()
        except urllib.error.HTTPError as e:
            err=e
            # NCBI also answers a transient 400 under load (seen in testing); retry it twice, other 4xx are final
            if e.code not in (429,500,502,503,504) and not (e.code==400 and i<2): break
            ra=e.headers.get("Retry-After") if e.headers else None
            time.sleep(float(ra) if ra and ra.isdigit() else 2*(2**i))
        except Exception as e: err=e; time.sleep(2*(i+1))
    raise RuntimeError(f"NCBI request failed: {u.split('?')[0]}: {err}")
