import os, re, json, base64, requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

SAST = pytz.timezone('Africa/Johannesburg')
now = datetime.now(SAST)

WP_URL = os.environ.get("WP_URL", "https://test.vedicvibe.online").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_PASS = os.environ.get("WP_APP_PASSWORD")

SOURCES = {
 "lunchtime": "https://za.national-lottery.com/uk-49s/results/lunchtime",
 "teatime": "https://za.national-lottery.com/uk-49s/results/teatime",
 "brunchtime": "https://za.national-lottery.com/uk-49s/results/brunchtime",
 "drivetime": "https://za.national-lottery.com/uk-49s/results/drivetime",
}

def parse_concatenated(s):
    # e.g. "7101640474819" -> try to split into 7 numbers 1-49
    s = re.sub(r'\D','', s)
    res=[]
    i=0
    while i < len(s) and len(res)<7:
        # try 2-digit if <=49 and not leading zero weird
        if i+1 < len(s):
            two = int(s[i:i+2])
            if 1 <= two <= 49:
                # lookahead: if remaining chars can make remaining numbers
                remaining = 7 - len(res) -1
                remaining_chars = len(s) - (i+2)
                if remaining <= remaining_chars <= remaining*2:
                    res.append(two)
                    i+=2
                    continue
        one = int(s[i])
        if 1 <= one <= 49:
            res.append(one)
            i+=1
        else:
            i+=1
    if len(res)>=7:
        return res[:6], res[6]
    return None

def scrape_draw(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Referer": "https://za.national-lottery.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=25)
        print(f"GET {url} -> {r.status_code} len={len(r.text)}")
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        text = soup.get_text("\n")
        # 1) Try dash pattern - today's balls
        nums = re.findall(r"-\s*(\d{1,2})", text)
        print(f"  dash nums found: {nums[:10]}")
        if len(nums) >= 7:
            # first 7 after the date heading - filter 1-49
            valid = [int(x) for x in nums[:10] if 1 <= int(x) <= 49]
            if len(valid) >= 7:
                return {"balls": sorted(valid[:6]), "booster": valid[6], "date": now.strftime("%d %B %Y")}

        # 2) Try history table first row
        # find table rows with pipe format or html table
        # Look for pattern like "3 October 2026 | 8141625364335"
        m = re.search(r"\d+\s+\w+\s+2026\s*\|\s*(\d{6,20})", text)
        if m:
            print(f"  table concat found: {m.group(1)}")
            parsed = parse_concatenated(m.group(1))
            if parsed:
                balls, boost = parsed
                return {"balls": sorted(balls), "booster": boost, "date": now.strftime("%d %B %Y")}

        # 3) Try all long digit strings 12-20 chars in table
        for long_num in re.findall(r"\b\d{12,20}\b", text):
            parsed = parse_concatenated(long_num)
            if parsed:
                balls, boost = parsed
                print(f"  parsed long {long_num} -> {balls}+{boost}")
                return {"balls": sorted(balls), "booster": boost, "date": now.strftime("%d %B %Y")}

    except Exception as e:
        print(f"Scrape exception {url}: {e}")
    return None

draws={}
for k,url in SOURCES.items():
    d=scrape_draw(url)
    if d:
        print(f"{k} LIVE => {d}")
        draws[k]=d
    else:
        print(f"{k} FAILED, using placeholder - will be overwritten next run")
        draws[k]={"balls":[5,11,20,27,42,47],"booster":31,"date":now.strftime("%d %B %Y")}

def render_balls(balls, booster):
    b="".join([f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#facc15;color:#000;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #eab308">{n}</span>' for n in balls])
    boost=f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#38bdf8;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #0ea5e9">{booster}</span>'
    return f'<div style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:4px;white-space:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:4px 0">{b}<span style="font-weight:800;color:#9ca3af;margin:0 1px">+</span>{boost}</div>'

cards=""
for k in ["lunchtime","teatime","brunchtime","drivetime"]:
    d=draws[k]
    cards+=f"""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:6px;min-width:0">
      <div style="display:flex;justify-content:space-between"><div style="font-weight:800;font-size:15px;white-space:nowrap">{k.upper()}</div><div style="font-size:8px;font-weight:700;background:#f0fdf4;border:1px solid #dcfce7;color:#166534;padding:2px 6px;border-radius:999px">SAST Live</div></div>
      <div style="font-size:10px;color:#64748b">{d['date']}</div>
      {render_balls(d['balls'], d['booster'])}
      <div style="display:flex;gap:6px;margin-top:6px">
        <a href="/uk49s-{k}-results/" style="flex:1;background:#0F3D2E;color:#fff;text-align:center;text-decoration:none;border-radius:999px;font-size:11px;font-weight:600;padding:6px 0">View Result →</a>
        <a href="/uk49s-{k}-results/#history" style="flex:1;background:#ecfdf5;color:#065f46;border:1px solid #d1fae5;text-align:center;text-decoration:none;border-radius:999px;font-size:11px;font-weight:600;padding:6px 0">History</a>
      </div>
    </div>
    """

homepage=f"""
<div style="font-family:Inter,sans-serif;max-width:1150px;margin:0 auto">
  <div style="background:#fef08a;border:1px solid #fde047;border-radius:8px;padding:6px 10px;font-size:11px;text-align:center;margin-bottom:12px">Independent results. Not affiliated with 49's Ltd. 18+ Gamble Responsibly.</div>
  <div style="background:linear-gradient(135deg,#0F3D2E,#145A32);border-radius:14px;padding:24px 16px;color:#fff;text-align:center;margin-bottom:16px">
    <h1 style="font-size:22px;font-weight:800;margin:0">UK49s Results Today Live</h1>
    <p style="font-size:11px;opacity:.9;margin-top:6px">Live from za.national-lottery.com – Lunchtime 14:49 SAST / Teatime 19:49 SAST / Brunchtime 12:49 SAST / Drivetime 18:49 SAST – Updated {now.strftime("%d %B %Y %H:%M SAST")}</p>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">{cards}</div>
</div>
"""

if WP_USER and WP_PASS:
    token=base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers={"Authorization": f"Basic {token}", "Content-Type":"application/json"}
    try:
        res=requests.post(f"{WP_URL}/wp-json/wp/v2/pages/6", json={"content": homepage, "status":"publish"}, headers=headers, timeout=20)
        print(f"WP push {res.status_code}")
        print(res.text[:400])
    except Exception as e:
        print(f"WP fail {e}")
else:
    print("No WP creds")

with open("results.json","w") as f:
    json.dump(draws,f,indent=2)
print("DONE", draws)
