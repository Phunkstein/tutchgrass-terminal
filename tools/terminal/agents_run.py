"""Runs one group of Live Agents for the GitHub Actions workflows. Stdlib only (Python 3.12).

  python3 tools/terminal/agents_run.py fast     # Market Watcher (stocks + price series), Trend Spotter (X, if X_BEARER_TOKEN is set)
  python3 tools/terminal/agents_run.py hourly   # Scientist, Terpene Lab, Grower Notes, Research Wire (refresh.py),
                                                #   Study Grader (newstudies.py, skips when PubMed is unchanged),
                                                #   recent-studies harvest (harvest_conditions.py, at most once a day)
  python3 tools/terminal/agents_run.py recalls  # Recall & Safety (agents/recalls.py): state regulator recalls + FDA, own workflow
Each step runs on its own: one failing source never stops the others and never writes placeholder data
(a failed step keeps the last good file, and the site shows that agent as stale/unavailable). Always exits 0;
publish.py then decides whether anything really changed. News Desk is NOT here: news-wire.yml owns news.json."""
import json,os,subprocess,sys,time
HERE=os.path.dirname(os.path.abspath(__file__)); PY=sys.executable
def run(label,args,timeout):
    t=time.time()
    try:
        r=subprocess.run([PY,*args],cwd=HERE,timeout=timeout,capture_output=True,text=True)
        tail=(r.stdout.strip().splitlines() or [""])[-1][:300]
        print(f"[{label}] exit {r.returncode} in {time.time()-t:.0f}s: {tail}")
        if r.returncode: print("   ",r.stderr.strip()[-600:].replace("\n","\n    "))
        return r.returncode
    except subprocess.TimeoutExpired: print(f"[{label}] timed out after {timeout}s (last good file kept)"); return -1
def conditions_due(hours=20):
    try: g=json.load(open(os.path.join(HERE,"data","conditions_recent.json")))["generated"]
    except Exception: return True
    if g[:10]!=time.strftime("%Y-%m-%d"): return True
    try: return time.time()-time.mktime(time.strptime(g[:16],"%Y-%m-%d %H:%M"))>hours*3600
    except Exception: return True
def main(group):
    if group=="fast":
        run("market + prices",["-c","import sys;sys.path[:0]=['.','agents'];import market,prices;market.run();prices.run()"],240)
        run("trend spotter (X)",["agents/social_x.py"],180)
    elif group=="hourly":
        run("scientist/lab/grower/wire",["refresh.py"],900)
        run("study grader",["newstudies.py"],600)
        if conditions_due(): run("recent studies harvest",["harvest_conditions.py"],900)
        else: print("[recent studies harvest] skipped: already ran today")
    elif group=="recalls":
        run("recall & safety",["agents/recalls.py"],600)
    else: sys.exit("usage: agents_run.py fast|hourly|recalls")
if __name__=="__main__": main(sys.argv[1] if len(sys.argv)>1 else "")
