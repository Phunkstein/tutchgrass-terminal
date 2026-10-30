"""Commit-and-push helper for the agent workflows (agents-fast.yml, agents-hourly.yml). Stdlib only.

  python3 tools/terminal/publish.py --name "Agents Fast" --heartbeat tools/terminal/data/market.json:6 \
      --owned tools/terminal/data/market.json tools/terminal/data/prices.json ...

1. Re-assembles the site from the data files on disk (build_terminal.py --no-refresh): terminal.json, findings and pages.
2. Decides whether anything REALLY changed versus HEAD: JSON files are compared with volatile run-time fields removed
   (generated, built, ts, secs, age_days, ...), so a run that only produced new timestamps does not commit.
   Exception (heartbeat): if the committed copy of the heartbeat file is older than N hours, it commits anyway so the
   site's "ran recently" status stays true (the timestamps are real run times, never invented).
3. Commits only the workflow's own files plus the re-assembled public/ output, then pushes to main.
   If the push is rejected (News Wire or the other agent workflow pushed first), it does NOT rebase with -X theirs:
   it saves its own files, hard-resets to the new origin/main, puts its own files back, re-assembles terminal.json from
   everyone's latest data (so nobody's block is clobbered), re-checks for changes, commits and retries (6 tries, backoff).
Prints changed=0/1 (and writes it to $GITHUB_OUTPUT)."""
import argparse,json,os,random,shutil,subprocess,sys,tempfile,time
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,"..",".."))
VOLATILE={"generated","generated_ts","built","built_ts","ts","secs","checked","age_days","updated","last_run_ts"}
DERIVED=["public/terminal/data/terminal.json","public/sitemap.xml","public/terminal/findings","public/terminal/my","public/terminal/unsubscribe",
         "public/terminal/privacy","public/terminal/disclaimer","public/terminal/corrections","public/terminal/report-cards"]
def git(*a,check=True,cap=True):
    r=subprocess.run(["git",*a],cwd=REPO,capture_output=cap,text=True)
    if check and r.returncode: raise RuntimeError(f"git {' '.join(a)}: {r.stderr.strip()[:300]}")
    return r
def strip(o):
    if isinstance(o,dict): return {k:strip(v) for k,v in o.items() if k not in VOLATILE}
    if isinstance(o,list): return [strip(v) for v in o]
    return o
def head_bytes(path):
    r=subprocess.run(["git","show","HEAD:"+path],cwd=REPO,capture_output=True)
    return r.stdout if r.returncode==0 else None
def really_changed(path):
    new=open(os.path.join(REPO,path),"rb").read() if os.path.exists(os.path.join(REPO,path)) else None
    old=head_bytes(path)
    if new==old: return False
    if new is None or old is None: return True
    if path.endswith(".json"):
        try: return strip(json.loads(new))!=strip(json.loads(old))
        except Exception: return True
    if path.endswith("report.md"):   # only its "Generated <time>." line is volatile
        dl=lambda b:[l for l in b.decode("utf-8","replace").splitlines() if not l.startswith("Generated ")]
        return dl(new)!=dl(old)
    return True
def changed_paths(paths):
    """paths (files or dirs) that differ from HEAD or are untracked, as repo-relative file paths"""
    r=git("status","--porcelain","--untracked-files=all","--",*paths)
    return sorted({l[3:].split(" -> ")[-1].strip('"') for l in r.stdout.splitlines() if l.strip()})
def heartbeat_due(spec):
    if not spec: return False
    path,hours=spec.rsplit(":",1); old=head_bytes(path)
    if old is None: return True
    sys.path.insert(0,HERE)
    try: g=json.loads(old).get("generated") or ""
    except Exception: return True
    try: t=time.mktime(time.strptime(g[:16],"%Y-%m-%d %H:%M"))
    except Exception: return True
    return time.time()-t>float(hours)*3600
def assemble():
    r=subprocess.run([sys.executable,os.path.join(HERE,"build_terminal.py"),"--no-refresh"],cwd=REPO,capture_output=True,text=True)
    if r.returncode: print(r.stdout[-800:],r.stderr[-800:]); raise RuntimeError("assemble failed")
def decide(owned,hb):
    cands=changed_paths(owned+DERIVED); real=[p for p in cands if really_changed(p)]
    return cands,real,(not real and heartbeat_due(hb))
def out(v):
    print(f"changed={v}")
    if os.environ.get("GITHUB_OUTPUT"): open(os.environ["GITHUB_OUTPUT"],"a").write(f"changed={v}\n")
def commit(name,cands,real,beat):
    git("add","-A","--",*cands)
    if git("diff","--cached","--quiet",check=False).returncode==0: return False
    msg=f"{name}: "+(", ".join(sorted({os.path.basename(p) for p in real}))[:180] if real else "heartbeat (data re-checked, no change)")
    git("commit","-q","-m",msg); return True
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--name",required=True); ap.add_argument("--owned",nargs="+",required=True)
    ap.add_argument("--heartbeat",default=None,help="path:hours"); ap.add_argument("--no-push",action="store_true"); ap.add_argument("--tries",type=int,default=6)
    a=ap.parse_args(); owned=[p for p in a.owned]
    assemble(); cands,real,beat=decide(owned,a.heartbeat)
    print("real changes:",real or "none","| heartbeat due" if beat else "")
    if not real and not beat: return out(0)
    if not commit(a.name,cands,real,beat): return out(0)
    if a.no_push: return out(1)
    for i in range(1,a.tries+1):
        if git("push","-q","origin","HEAD:main",check=False).returncode==0: print(f"pushed on try {i}"); return out(1)
        print(f"push rejected (try {i}); re-basing our own files on the new main")
        tmp=tempfile.mkdtemp(); keep=[]
        for p in changed_paths_since_main(owned):
            src=os.path.join(REPO,p)
            if os.path.isfile(src): os.makedirs(os.path.dirname(os.path.join(tmp,p)),exist_ok=True); shutil.copy2(src,os.path.join(tmp,p)); keep.append(p)
        time.sleep(3*i+random.random()*4)
        git("fetch","-q","origin","main"); git("reset","-q","--hard","origin/main")
        for p in keep: os.makedirs(os.path.dirname(os.path.join(REPO,p)),exist_ok=True); shutil.copy2(os.path.join(tmp,p),os.path.join(REPO,p))
        shutil.rmtree(tmp,ignore_errors=True)
        assemble(); cands,real,beat=decide(owned,a.heartbeat)
        if not real and not beat: print("nothing left to publish after re-basing"); return out(0)
        if not commit(a.name,cands,real,beat): return out(0)
    print("push failed after retries"); out(0); sys.exit(1)
def changed_paths_since_main(owned):
    """our own files as they are in our commit (HEAD), whether or not they changed in it"""
    files=[]
    for p in owned:
        full=os.path.join(REPO,p)
        if os.path.isdir(full):
            for root,_,fs in os.walk(full): files+= [os.path.relpath(os.path.join(root,f),REPO) for f in fs]
        elif os.path.exists(full): files.append(p)
    return files
if __name__=="__main__": main()
