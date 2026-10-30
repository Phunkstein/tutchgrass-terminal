# Tutchgrass Terminal hub (branch `expand-hub`, preview only)

Tabs: **Hub** (`/terminal/`) · **Label vs Lab** (`/terminal/lab/` + leaderboards/explore/flags/game/submit) · **Terps** (`/terminal/terps/`, 9 goal pages) · **Science** (`/terminal/science/`) · **News** (`/terminal/news/`, Dec 11 countdown) · **Dispensary** · **Terp Quiz** · **Lab Duel** · **Report Cards**.

## Daily refresh
```
python3 hub/refresh_hub.py            # harvest_terps -> harvest_science -> harvest_news -> build.py -> hub_share.py
python3 hub/refresh_hub.py --no-terps # skip a step (also --no-science, --no-news)
```
No cron is installed. Requires python3, Playwright + Chrome at /usr/bin/google-chrome (cards only). Output: `site/` (copy to `public/` in the repo).

## Data sources (all free)
- PubMed E-utilities (esearch/efetch), window = last 18 months → `data/hub/terps.json`, `science.json`
- Curated, hand-read paper lists → `data/hub/terps_curated.json`, `data/hub/takeaways.json` (re-review when refreshing)
- RSS: Marijuana Moment, MJBizDaily, New Cannabis Ventures, Business of Cannabis, StratCann, Cannabis Health News, Google News (3 queries) → `news.json` (21-day window; kept unchanged if <5 items)
- Dec 11 facts: CRS IF13136 / IN12620, 7 USC §1639o (P.L. 119-37, P.L. 119-103)
- Lab data: existing scored COAs (`data/`)

Note: these scripts run from the local build workspace (next to build.py and data/); output site/ is copied into public/.
