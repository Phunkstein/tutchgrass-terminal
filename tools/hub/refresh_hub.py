"""Daily hub refresh: re-pull PubMed + news feeds, rebuild static site, re-render share cards.
Usage (from repo root):  python3 hub/refresh_hub.py   [--no-terps] [--no-science] [--no-news]
No cron is installed; schedule it yourself if wanted. Network: NCBI E-utilities + public RSS (free)."""
import subprocess,sys,os,time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
steps=[('terps','hub/harvest_terps.py'),('science','hub/harvest_science.py'),('news','hub/harvest_news.py'),('build','build.py'),('cards','hub/hub_share.py')]
ok=True
for k,s in steps:
    if f'--no-{k}' in sys.argv: print('skip',k); continue
    t=time.time(); r=subprocess.run([sys.executable,s])
    print(f'[{k}] exit {r.returncode} in {time.time()-t:.0f}s')
    if r.returncode and k in('build','cards'): sys.exit(r.returncode)
    ok&= r.returncode==0
print('DONE' if ok else 'DONE with harvest warnings (previous JSON kept)')
