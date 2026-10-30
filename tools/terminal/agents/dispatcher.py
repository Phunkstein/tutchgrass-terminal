#!/usr/bin/env python3
"""Agent Dispatcher: keeps every agent workflow on its schedule even when GitHub drops or delays
scheduled (cron) runs, which it often does for new repos and for frequent schedules.

Run by .github/workflows/agents-dispatcher.yml. It reads the `cron:` lines of every other workflow in
.github/workflows, and once a minute checks whether each workflow's most recent cron slot (UTC) has a
run. If GitHub's own scheduler has not started one within GRACE minutes of the slot, it starts one with
workflow_dispatch (the GITHUB_TOKEN may do this; it needs `actions: write`). Missed slots are caught up
once (not once per missed slot). It then exits after RUN_MINUTES so the workflow can re-dispatch itself.

API use is small: one runs-list call per workflow per new slot (~20/hour) plus the dispatches.
No secrets beyond GITHUB_TOKEN, nothing posted anywhere.
"""
import datetime as dt, glob, json, os, re, sys, time, urllib.request, urllib.error

REPO = os.environ.get("GITHUB_REPOSITORY", "Phunkstein/tutchgrass-terminal")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
REF = os.environ.get("DISPATCH_REF", "main")
GRACE = int(os.environ.get("GRACE_MINUTES", "3"))       # give GitHub's own scheduler this long first
RUN_MINUTES = float(os.environ.get("RUN_MINUTES", "340"))
DRY = os.environ.get("DRY_RUN") == "1"            # log what would be dispatched, dispatch nothing
SELF = os.environ.get("DISPATCHER_FILE", "agents-dispatcher.yml")
UTC = dt.timezone.utc


def log(*a):
    print(dt.datetime.now(UTC).strftime("%H:%M:%SZ"), *a, flush=True)


def api(method, path, body=None):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={**({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}), "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "tutchgrass-dispatcher"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


# ---- cron ------------------------------------------------------------------------------------------
def field(spec, lo, hi):
    out = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/"); step = int(s)
        if part in ("*", ""):
            a, b = lo, hi
        elif "-" in part:
            a, b = map(int, part.split("-"))
        else:
            a = int(part); b = hi if step > 1 else a
        out.update(range(a, b + 1, step))
    return out


class Cron:
    def __init__(self, expr):
        m, h, dom, mon, dow = expr.split()
        self.expr = expr
        self.m, self.h, self.mon = field(m, 0, 59), field(h, 0, 23), field(mon, 1, 12)
        self.dom, self.dow = field(dom, 1, 31), {d % 7 for d in field(dow, 0, 7)}
        self.dom_any, self.dow_any = dom == "*", dow == "*"

    def match(self, t):
        if t.minute not in self.m or t.hour not in self.h or t.month not in self.mon:
            return False
        d_ok, w_ok = t.day in self.dom, (t.weekday() + 1) % 7 in self.dow
        if self.dom_any or self.dow_any:
            return d_ok and w_ok
        return d_ok or w_ok

    def last_slot(self, before):
        """Latest matching minute <= before (looks back 8 days)."""
        t = before.replace(second=0, microsecond=0)
        for _ in range(8 * 24 * 60):
            if self.match(t):
                return t
            t -= dt.timedelta(minutes=1)
        return None


def workflows():
    out = {}
    for path in sorted(glob.glob(".github/workflows/*.yml")):
        name = os.path.basename(path)
        if name == SELF:
            continue
        text = open(path, encoding="utf-8").read()
        if "workflow_dispatch" not in text:
            continue
        crons = [Cron(c) for c in re.findall(r'^\s*-\s*cron:\s*["\']([^"\']+)["\']', text, re.M)]
        if crons:
            out[name] = crons
    return out


def parse_ts(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def main():
    if not TOKEN and not DRY:
        sys.exit("no GITHUB_TOKEN")
    wf = workflows()
    for k, v in wf.items():
        log("watching", k, [c.expr for c in v])
    handled = {}                       # workflow -> slot already covered
    deadline = time.time() + RUN_MINUTES * 60
    while True:
        now = dt.datetime.now(UTC)
        for name, crons in wf.items():
            slots = [s for s in (c.last_slot(now - dt.timedelta(minutes=GRACE)) for c in crons) if s]
            if not slots:
                continue
            slot = max(slots)
            if handled.get(name) == slot:
                continue
            try:
                runs = api("GET", f"/actions/workflows/{name}/runs?per_page=5&branch={REF}")["workflow_runs"]
                covered = [r for r in runs if parse_ts(r["created_at"]) >= slot - dt.timedelta(seconds=60)]
                if covered:
                    log(f"{name}: slot {slot:%H:%M}Z already has a run ({covered[-1]['event']} {covered[-1]['created_at']})")
                else:
                    if not DRY:
                        api("POST", f"/actions/workflows/{name}/dispatches", {"ref": REF})
                    log(f"{name}: slot {slot:%m-%d %H:%M}Z had no run -> {'WOULD dispatch' if DRY else 'dispatched'}")
                handled[name] = slot
            except urllib.error.HTTPError as e:
                log(f"{name}: API error {e.code} {e.read()[:200]!r}; retry next minute")
            except Exception as e:  # network hiccup: retry next minute
                log(f"{name}: error {e!r}; retry next minute")
        if time.time() > deadline:
            log("run window over; the workflow re-dispatches the next dispatcher run")
            return
        time.sleep(max(5, 60 - dt.datetime.now(UTC).second + 2))


if __name__ == "__main__":
    main()
