import json,os,time,subprocess,re,html
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def curl(url,timeout=25,ua=UA):
    r=subprocess.run(["curl","-sL","-m",str(timeout),"-A",ua,url],capture_output=True)
    if r.returncode!=0: raise RuntimeError(f"curl {r.returncode}")
    return r.stdout.decode("utf-8","replace")
def text(h):
    h=re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S); return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',h))).strip()
def save(name,obj):
    obj.setdefault("generated",time.strftime("%Y-%m-%d %H:%M %Z")); json.dump(obj,open(os.path.join(ROOT,"data",name),"w"),indent=1); return obj
def load(name,default=None):
    try: return json.load(open(os.path.join(ROOT,"data",name)))
    except Exception: return default
