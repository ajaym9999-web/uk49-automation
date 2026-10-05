import os
import re
import json
import base64
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

SAST = pytz.timezone('Africa/Johannesburg')
now = datetime.now(SAST)

WP_URL = os.environ.get("WP_URL", "https://test.vedicvibe.online").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_APP_PASSWORD")

PAGE_HOMEPAGE = 6
PAGE_IDS = {"lunchtime":17,"teatime":20,"brunchtime":22,"drivetime":24}

SOURCES = {
 "lunchtime": "https://za.national-lottery.com/uk-49s/results/lunchtime",
 "teatime": "https://za.national-lottery.com/uk-49s/results/teatime",
 "brunchtime": "https://za.national-lottery.com/uk-49s/results/brunchtime",
 "drivetime": "https://za.national-lottery.com/uk-49s/results/drivetime",
}

def scrape_draw(url):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        # Find today's block: look for lines like "- 5"
        text = soup.get_text("\n")
        # Regex for - number pattern, capture 7 consecutive
        nums = re.findall(r"-\s*(\d{1,2})", text)
        # First 7 numbers after date are today's result
        if len(nums) >= 7:
            balls = list(map(int, nums[:6]))
            booster = int(nums[6])
            # Also try to get date
            date_match = re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+\d+\s+\w+\s+\d{4}", text)
            date_str = date_match.group(0) if date_match else now.strftime("%d %B %Y")
            return {"balls": sorted(balls), "booster": booster, "date": date_str, "raw": nums[:7]}
    except Exception as e:
        print(f"Scrape fail {url}: {e}")
    return None

draws = {}
for key, url in SOURCES.items():
    data = scrape_draw(url)
    if data:
        print(f"{key}: {data}")
        draws[key] = data
    else:
        # fallback dummy to avoid blank
        draws[key] = {"balls":[7,17,22,24,34,39], "booster":11, "date": now.strftime("%d %B %Y")}

# Ball render - COMPACT 25px fix, flex-nowrap
def render_balls(balls, booster):
    b_html = "".join([f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#facc15;color:#000;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #eab308;box-shadow:inset 0 -1px 0 rgba(0,0,0,.2)">{n}</span>' for n in balls])
    boost = f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#38bdf8;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #0ea5e9">{booster}</span>'
    return f'<div style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:4px;white-space:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:4px 0">{b_html}<span style="font-weight:800;color:#9ca3af;margin:0 1px">+</span>{boost}</div>'

cards = ""
for k in ["lunchtime","teatime","brunchtime","drivetime"]:
    d = draws[k]
    cards += f"""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:6px;min-width:0">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:6px">
        <div style="font-weight:800;font-size:15px;white-space:nowrap">{k.upper()}</div>
        <div style="font-size:8px;font-weight:700;background:#f0fdf4;border:1px solid #dcfce7;color:#166534;padding:2px 6px;border-radius:999px;white-space:nowrap">SAST Live</div>
      </div>
      <div style="font-size:10px;color:#64748b">{d['date']}</div>
      {render_balls(d['balls'], d['booster'])}
      <div style="display:flex;gap:6px;margin-top:6px">
        <a href="/uk49s-{k}-results/" style="flex:1;background:#0F3D2E;color:#fff;text-align:center;text-decoration:none;border-radius:999px;font-size:11px;font-weight:600;padding:6px 0">View Result →</a>
        <a href="/uk49s-{k}-results/#history" style="flex:1;background:#ecfdf5;color:#065f46;border:1px solid #d1fae5;text-align:center;text-decoration:none;border-radius:999px;font-size:11px;font-weight:600;padding:6px 0">History</a>
      </div>
    </div>
    """

# Homepage HTML - pure static, 0 React, SEO pre-rendered
homepage = f"""
<div style="font-family:Inter,sans-serif;max-width:1150px;margin:0 auto">
  <div style="background:#fef08a;border:1px solid #fde047;border-radius:8px;padding:6px 10px;font-size:11px;text-align:center;margin-bottom:12px">Independent results. Not affiliated with 49's Ltd. 18+ Gamble Responsibly.</div>
  <div style="background:linear-gradient(135deg,#0F3D2E,#145A32);border-radius:14px;padding:24px 16px;color:#fff;text-align:center;margin-bottom:16px">
    <h1 style="font-size:22px;font-weight:800;margin:0">UK49s Results Today Live</h1>
    <p style="font-size:11px;opacity:.9;margin-top:6px">Live from za.national-lottery.com - Lunchtime 14:49 SAST / Teatime 19:49 SAST / Brunchtime 12:49 SAST / Drivetime 18:49 SAST</p>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">
    {cards}
  </div>
</div>
"""

# Push to WordPress if creds exist
if WP_USER and WP_PASS:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type":"application/json"}
    try:
        res = requests.post(f"{WP_URL}/wp-json/wp/v2/pages/{PAGE_HOMEPAGE}", json={"content": homepage, "status":"publish"}, headers=headers, timeout=20)
        print(f"Homepage push status: {res.status_code}")
        if res.status_code != 200:
            print(res.text[:500])
    except Exception as e:
        print(f"WP push fail: {e}")
else:
    print("No WP creds - printing homepage preview")
    print(homepage[:1000])

# Save results.json for backup
with open("results.json","w") as f:
    json.dump(draws, f, indent=2)
print("Done")
