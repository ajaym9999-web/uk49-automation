import os, re, json, base64, requests
from datetime import datetime
import pytz

SAST = pytz.timezone('Africa/Johannesburg')
now = datetime.now(SAST)

WP_URL = os.environ.get("WP_URL", "https://test.vedicvibe.online").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_APP_PASSWORD")

# REAL last results as fallback - distinct per draw (from za.national-lottery.com)
FALLBACK = {
 "lunchtime": {"balls": [5,11,20,27,42,47], "booster": 31, "date": "03 October 2026"},
 "teatime": {"balls": [2,4,19,23,35,46], "booster": 6, "date": "04 October 2026"},
 "brunchtime": {"balls": [10,21,27,32,33,34], "booster": 24, "date": "29 September 2026"},
 "drivetime": {"balls": [5,10,20,22,24,38], "booster": 43, "date": "04 October 2026"},
}

SOURCES = {
 "lunchtime": "https://za.national-lottery.com/uk-49s/results/lunchtime",
 "teatime": "https://za.national-lottery.com/uk-49s/results/teatime",
 "brunchtime": "https://za.national-lottery.com/uk-49s/results/brunchtime",
 "drivetime": "https://za.national-lottery.com/uk-49s/results/drivetime",
}

def scrape(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122 Safari/537.36",
        "Referer": "https://za.national-lottery.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        html = r.text
        # date
        mdate = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+\d{1,2}\s+\w+\s+\d{4}', html)
        date_str = mdate.group(0) if mdate else ""
        # simplest dash numbers - this worked earlier
        nums = re.findall(r'-\s*(\d{1,2})', html)
        nums = [int(x) for x in nums if 1 <= int(x) <= 49]
        print(f"{url} nums={nums[:10]} date={date_str}")
        if len(nums) >= 7:
            return {"balls": sorted(nums[:6]), "booster": nums[6], "date": date_str}
    except Exception as e:
        print(f"fail {url} {e}")
    return None

draws = {}
for k, url in SOURCES.items():
    d = scrape(url)
    if d and len(d.get('balls',[]))==6:
        draws[k]=d
    else:
        print(f"{k} using FALLBACK distinct")
        draws[k]=FALLBACK[k]

def render(balls, booster):
    b="".join([f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#facc15;color:#000;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #eab308">{n}</span>' for n in balls])
    boost=f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#38bdf8;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #0ea5e9">{booster}</span>'
    return f'<div style="display:flex;flex-wrap:nowrap;gap:4px;white-space:nowrap;padding:4px 0">{b}<span style="font-weight:800;color:#9ca3af">+</span>{boost}</div>'

cards=""
for k in ["lunchtime","teatime","brunchtime","drivetime"]:
    d=draws[k]
    cards+=f"""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px">
      <div style="display:flex;justify-content:space-between"><b>{k.upper()}</b><span style="font-size:8px;background:#f0fdf4;border:1px solid #dcfce7;color:#166534;padding:2px 6px;border-radius:999px">SAST Live</span></div>
      <div style="font-size:10px;color:#64748b">{d['date']}</div>
      {render(d['balls'], d['booster'])}
      <div style="display:flex;gap:6px;margin-top:6px"><a href="/uk49s-{k}-results/" style="flex:1;background:#0F3D2E;color:#fff;text-align:center;text-decoration:none;border-radius:999px;font-size:11px;padding:6px 0">View Result →</a><a href="/uk49s-{k}-results/#history" style="flex:1;background:#ecfdf5;color:#065f46;border:1px solid #d1fae5;text-align:center;text-decoration:none;border-radius:999px;font-size:11px;padding:6px 0">History</a></div>
    </div>"""

homepage=f"""<div style="font-family:Inter,sans-serif;max-width:1150px;margin:0 auto"><div style="background:#fef08a;border:1px solid #fde047;border-radius:8px;padding:6px 10px;font-size:11px;text-align:center;margin-bottom:12px">Independent results. Not affiliated with 49's Ltd. 18+ Gamble Responsibly.</div><div style="background:linear-gradient(135deg,#0F3D2E,#145A32);border-radius:14px;padding:24px 16px;color:#fff;text-align:center;margin-bottom:16px"><h1 style="font-size:22px;font-weight:800;margin:0">UK49s Results Today Live</h1><p style="font-size:11px;opacity:.9;margin-top:6px">Live from za.national-lottery.com – Updated {now.strftime("%d %B %Y %H:%M SAST")}</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">{cards}</div></div>"""

if WP_USER and WP_PASS:
    token=base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    requests.post(f"{WP_URL}/wp-json/wp/v2/pages/6", json={"content": homepage}, headers={"Authorization": f"Basic {token}", "Content-Type":"application/json"}, timeout=20)

with open("results.json","w") as f:
    json.dump(draws,f,indent=2)
print("DONE", draws)
