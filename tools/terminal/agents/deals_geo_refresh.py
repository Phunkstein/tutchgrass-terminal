"""Re-attach store coordinates to the current deals.json without re-scraping (e.g. after editing deals_stores.json).
python3 tools/terminal/agents/deals_geo_refresh.py"""
import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from deals_geo import attach
from deals import PUB
from common import save
o=json.load(open(PUB)); o["locations"],o["geo"]=attach(o["deals"]); o["schema"]="deals/3"
o.setdefault("geo_note","Store addresses come from each chain's own site and were geocoded with the US Census Bureau geocoder (OpenStreetMap Nominatim as a fallback). 'city' locations are the city centre where the exact store address isn't known. Distances are worked out in your browser; your location stays on your device.")
save("deals.json",o); json.dump(o,open(PUB,"w"),indent=1); print("deals geo:",o["geo"])
