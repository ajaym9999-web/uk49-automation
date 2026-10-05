import os, re, base64, requests
from datetime import datetime
import pytz

SAST = pytz.timezone('Africa/Johannesburg')
now = datetime.now(SAST)

WP_URL = os.environ.get("WP_URL", "https://test.vedicvibe.online").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_APP_PASSWORD")

# Fallback ab 4 Oct ka latest hai, 29 Sept nahi
FALLBACK = {
 "lunchtime": {"balls": [23,27,30,31,40,44], "booster": 29, "date": "Sunday 4 October 2026"},
 "teatime": {"balls": [2,4,19,23,35,46], "booster": 6, "date": "Sunday 4 October 2026"},
 "brunchtime": {"balls": [8,14,16,25,36,43], "booster": 35, "date": "Saturday 3 October 2026"},
 "drivetime": {"balls": [5,10,20,22,24,38], "booster": 43, "date": "Saturday 3 October 2026"},
}

def scrape(url):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        # Real site se date nikalna: "Sunday 4 October 2026"
        mdate = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}\s+\w+\s+\d{4}', r.text)
        nums = [int(x) for x in re.findall(r'-\s*(\d{1,2})', r.text) if 1 <= int(x) <= 49]
        if len(nums) >= 7 and mdate:
            return {"balls": sorted(nums[:6]), "booster": nums[6], "date": mdate.group(0)}
    except: pass
    return None

SOURCES = {
 "lunchtime": "https://za.national-lottery.com/uk-49s/results/lunchtime",
 "teatime": "https://za.national-lottery.com/uk-49s/results/teatime",
 "brunchtime": "https://za.national-lottery.com/uk-49s/results/brunchtime",
 "drivetime": "https://za.national-lottery.com/uk-49s/results/drivetime",
}

draws = {}
for k,u in SOURCES.items():
    d = scrape(u)
    draws[k] = d if d else FALLBACK[k]

#... baaki render same...
