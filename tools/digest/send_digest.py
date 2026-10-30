"""Cannabis Agent Terminal: new-study alerts + weekly digest (Brevo transactional email API).

DRY RUN BY DEFAULT: builds the emails and writes previews to tools/digest/out/ and sends nothing.
Real sending needs BOTH env vars plus the --send flag:
  BREVO_API_KEY              Brevo v3 API key (account Arkitekt@myyahoo.com), sent as the 'api-key' header
  SUPABASE_SERVICE_ROLE_KEY  server-side key used to read opted-in users (never ship it to the browser)
Optional: SUPABASE_URL (default the project URL), DIGEST_FROM (default tutchgrass@mail.grokbot.com), DIGEST_FROM_NAME.

  python3 tools/digest/send_digest.py --demo            # preview with a sample user, no keys needed
  python3 tools/digest/send_digest.py                   # dry run against real opted-in users (needs service key)
  python3 tools/digest/send_digest.py --send            # real send (refuses unless both keys are set)
  python3 tools/digest/send_digest.py --mode digest     # weekly digest instead of new-study alerts
Who gets mail: only users with an email_prefs row where alerts (mode=alerts) or digest (mode=digest) is true,
and only for the conditions they picked. Every email carries a one-click unsubscribe link."""
import argparse,datetime as dt,html,json,os,sys,urllib.request,urllib.error
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,"..","terminal"))
import newstudies as NS
SB_URL=os.environ.get("SUPABASE_URL","https://ckauuurdpltrqjimjgbt.supabase.co")
SITE="https://tutchgrass-terminal.onrender.com"; STATE=os.path.join(HERE,"state.json"); OUT=os.path.join(HERE,"out")
BREVO="https://api.brevo.com/v3/smtp/email"
def _req(url,key,method="GET",body=None,extra=None):
    h={"apikey":key,"Authorization":f"Bearer {key}","Content-Type":"application/json"}; h.update(extra or {})
    r=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers=h,method=method)
    with urllib.request.urlopen(r,timeout=30) as f: t=f.read(); return json.loads(t) if t else None
def users(key,mode):
    """opted-in users -> [{id,email,token,conditions}] (service role bypasses RLS; server-side only)."""
    col="alerts" if mode=="alerts" else "digest"
    prefs=_req(f"{SB_URL}/rest/v1/email_prefs?select=user_id,unsubscribe_token&{col}=eq.true",key)
    conds={}
    for r in _req(f"{SB_URL}/rest/v1/user_conditions?select=user_id,condition_id",key) or []: conds.setdefault(r["user_id"],[]).append(r["condition_id"])
    emails={};page=1
    while True:
        d=_req(f"{SB_URL}/auth/v1/admin/users?page={page}&per_page=1000",key); us=d.get("users",[]) if isinstance(d,dict) else d
        for u in us: emails[u["id"]]=u.get("email")
        if len(us)<1000: break
        page+=1
    return [dict(id=p["user_id"],email=emails.get(p["user_id"]),token=p["unsubscribe_token"],conditions=sorted(conds.get(p["user_id"],[])))
            for p in prefs if emails.get(p["user_id"]) and conds.get(p["user_id"])]
def last_run(mode):
    try: return dt.date.fromisoformat(json.load(open(STATE))[mode])
    except Exception: return dt.date.today()-dt.timedelta(days=1 if mode=="alerts" else 7)
def save_run(mode):
    s={}
    try: s=json.load(open(STATE))
    except Exception: pass
    s[mode]=dt.date.today().isoformat(); json.dump(s,open(STATE,"w"),indent=1)
def build(u,by,papers,mode,since):
    E=html.escape; unsub=f"{SITE}/terminal/unsubscribe/?t={u['token']}"; secs=[];txt=[];n=0
    for c in u["conditions"]:
        ps=[papers[i] for i in by.get(c,[]) if i in papers][:5]
        if not ps: continue
        n+=len(ps); lab=NS.LABELS.get(c,c)
        secs.append(f'<h2 style="font:600 17px Inter,Arial;margin:22px 0 6px">{E(lab)}</h2>'+"".join(
          f'<div style="border:1px solid #e3e6e3;border-radius:8px;padding:12px 14px;margin:8px 0"><div style="font:600 11px monospace;color:#1d5c3a">{E(p["grade_label"])} · {E(p["date"])}</div>'
          f'<a href="{E(p["url"])}" style="font:600 15px Inter,Arial;color:#111;text-decoration:none">{E(p["title"])}</a>'
          f'<p style="margin:6px 0 2px;font:14px Inter,Arial;color:#333"><b>What they did:</b> {E(p["plain"]["did"])}</p>'
          f'<p style="margin:2px 0;font:14px Inter,Arial;color:#333"><b>What the authors concluded:</b> {E(p["plain"]["found"])}</p>'
          f'<p style="margin:2px 0;font:13px Inter,Arial;color:#8a5a00">{E(p["plain"]["caveat"])}</p></div>' for p in ps))
        txt.append(f"\n{lab}\n"+"\n".join(f"- [{p['grade_label']}] {p['title']} ({p['date']})\n  What they did: {p['plain']['did']}\n  Authors concluded: {p['plain']['found']}\n  Caveat: {p['plain']['caveat']}\n  {p['url']}" for p in ps))
    if not n: return None
    kind="New studies" if mode=="alerts" else "Your weekly research digest"
    subj=f"{kind}: {n} new {'study' if n==1 else 'studies'} for your conditions"
    foot=(f'<p style="font:12px Inter,Arial;color:#777;margin-top:24px">Research summary, not medical advice. Studies suggest; they do not prove. Talk to a doctor, especially if you take other medicines. '
          f'You get this because you picked these conditions on Cannabis Agent Terminal. <a href="{SITE}/terminal/account/">Email settings</a> · <a href="{unsub}">Unsubscribe in one click</a></p>')
    body=(f'<div style="max-width:620px;margin:auto;font:15px Inter,Arial;color:#111"><div style="font:700 18px Inter,Arial;color:#1d5c3a">Cannabis Agent Terminal</div>'
          f'<p>{kind} since {since}. Each paper links to PubMed and carries an honest grade.</p>{"".join(secs)}'
          f'<p><a href="{SITE}/terminal/my/" style="color:#1d5c3a">Open My Condition →</a></p>{foot}</div>')
    text=f"Cannabis Agent Terminal. {kind} since {since}.\n"+"".join(txt)+f"\n\nResearch summary, not medical advice.\nSettings: {SITE}/terminal/account/\nUnsubscribe: {unsub}\n"
    return dict(subject=subj,html=body,text=text,unsub=unsub,count=n)
def send(brevo_key,to,m):
    body={"sender":{"email":os.environ.get("DIGEST_FROM","tutchgrass@mail.grokbot.com"),"name":os.environ.get("DIGEST_FROM_NAME","Cannabis Agent Terminal")},
          "to":[{"email":to}],"subject":m["subject"],"htmlContent":m["html"],"textContent":m["text"],
          "headers":{"List-Unsubscribe":f"<{m['unsub']}>"},"tags":["tutchgrass-digest"]}
    r=urllib.request.Request(BREVO,data=json.dumps(body).encode(),method="POST",headers={"api-key":brevo_key,"accept":"application/json","content-type":"application/json"})
    with urllib.request.urlopen(r,timeout=30) as f: return f.status,f.read().decode()
def main():
    a=argparse.ArgumentParser(); a.add_argument("--mode",choices=["alerts","digest"],default="alerts")
    a.add_argument("--send",action="store_true"); a.add_argument("--demo",action="store_true"); a.add_argument("--since")
    o=a.parse_args(); bk=os.environ.get("BREVO_API_KEY"); sk=os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if o.send and not (bk and sk):
        print("REFUSING TO SEND: needs a key. Set BREVO_API_KEY and SUPABASE_SERVICE_ROLE_KEY.",
              f"(BREVO_API_KEY {'set' if bk else 'MISSING'}, SUPABASE_SERVICE_ROLE_KEY {'set' if sk else 'MISSING'})"); sys.exit(2)
    if not bk: print("NOTE: BREVO_API_KEY is not set, so this is a dry run only. Real sending needs a Brevo API key.")
    since=dt.date.fromisoformat(o.since) if o.since else last_run(o.mode)
    if o.demo: us=[dict(id="demo",email="demo@example.invalid",token="00000000-0000-0000-0000-000000000000",conditions=["sleep","pain","anxiety"])]
    elif not sk: print("Need SUPABASE_SERVICE_ROLE_KEY to read opted-in users (or use --demo)."); sys.exit(2)
    else: us=users(sk,o.mode)
    cids=sorted({c for u in us for c in u["conditions"]})
    by,papers,_=NS.fetch(set(cids),since) if cids else ({},{},{})
    os.makedirs(OUT,exist_ok=True); sent=0;built=0
    for u in us:
        m=build(u,by,papers,o.mode,since)
        if not m: continue
        built+=1; slug=u["id"][:8]
        open(os.path.join(OUT,f"{o.mode}_{slug}.html"),"w").write(m["html"]); open(os.path.join(OUT,f"{o.mode}_{slug}.txt"),"w").write(f"Subject: {m['subject']}\n\n"+m["text"])
        if o.send and not o.demo:
            try: st,_=send(bk,u["email"],m); sent+=1; print("sent",slug,st)
            except urllib.error.HTTPError as e: print("brevo error",slug,e.code,e.read()[:200])
    print(f"mode={o.mode} since={since} users={len(us)} emails_built={built} sent={sent} previews={OUT}")
    if o.send and not o.demo and sent: save_run(o.mode)
if __name__=="__main__": main()
