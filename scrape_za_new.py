import os, re, json, base64, requests, time
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

def extract_real(html):
    # method: split lines and collect "- number" pattern
    lines = re.split(r'[\r\n]+', html)
    nums = []
    date_found = ""
    for line in lines:
        # date
        mdate = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+\d{1,2}\s+\w+\s+\d{4}', line)
        if mdate and not date_found:
            date_found = mdate.group(0)
        # dash number like "- 5" or ">5<" inside tag
        # clean tags
        clean = re.sub(r'<[^>]+>', ' ', line)
        mdash = re.search(r'-\s*(\d{1,2})\s*$', clean.strip())
        if mdash:
            v = int(mdash.group(1))
            if 1 <= v <= 49:
                nums.append(v)
        if len(nums) >= 7:
            break
    if len(nums) >= 7:
        return {"balls": sorted(nums[:6]), "booster": nums[6], "date": date_found or now.strftime("%d %B %Y")}

    # fallback: try to find long concatenated number in table
    text = re.sub(r'<[^>]+>', ' ', html)
    for long_num in re.findall(r'\b\d{8,20}\b', text):
        # try split into 7 numbers 1-49
        s = long_num
        res=[]
        i=0
        while i < len(s) and len(res)<7:
            if i+1 < len(s):
                two = int(s[i:i+2])
                if 1 <= two <= 49 and len(s)-(i+2) >= (7-len(res)-1):
                    res.append(two)
                    i+=2
                    continue
            res.append(int(s[i]))
            i+=1
        if len(res)>=7 and all(1<=x<=49 for x in res[:7]):
            return {"balls": sorted(res[:6]), "booster": res[6], "date": date_found or now.strftime("%d %B %Y")}
    return None

def scrape(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
        "Accept": "text/html",
        "Referer": "https://za.national-lottery.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=25)
        print(f"GET {url} -> {r.status_code} {len(r.text)}")
        if r.status_code==200:
            data = extract_real(r.text)
            print(f"  -> extracted {data}")
            return data
    except Exception as e:
        print(f"ERR {url} {e}")
    return None

draws = {}
for k, url in SOURCES.items():
    d = scrape(url)
    time.sleep(2)
    if not d:
        # if fails, keep None, don't duplicate other draw
        d = {"balls": [], "booster": None, "date": "Awaiting draw", "empty": True}
    draws[k]=d

print("FINAL DRAWS", draws)

def render_balls(balls, booster, empty=False):
    if empty or not balls:
        return '<div style="font-size:11px;color:#991b1b;background:#fef2f2;border:1px solid #fecaca;padding:4px 8px;border-radius:6px">⏳ Awaiting draw – result not published yet</div>'
    b="".join([f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#facc15;color:#000;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #eab308">{n}</span>' for n in balls])
    boost=f'<span style="flex:0 0 auto;width:25px;height:25px;min-width:25px;border-radius:50%;background:#38bdf8;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:11px;border:1px solid #0ea5e9">{booster}</span>'
    return f'<div style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:4px;white-space:nowrap;padding:4px 0">{b}<span style="font-weight:800;color:#9ca3af">+</span>{boost}</div>'

cards=""
for k in ["lunchtime","teatime","brunchtime","drivetime"]:
    d=draws[k]
    empty = d.get("empty", False) or len(d.get("balls",[]))<6
    date_str = d.get("date","")
    cards+=f"""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:6px">
      <div style="display:flex;justify-content:space-between"><div style="font-weight:800;font-size:15px">{k.upper()}</div><div style="font-size:8px;background:#f0fdf4;border:1px solid #dcfce7;color:#166534;padding:2px 6px;border-radius:999px">SAST Live</div></div>
      <div style="font-size:10px;color:#64748b">{date_str}</div>
      {render_balls(d.get("balls",[]), d.get("booster"), empty)}
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
        res=requests.post(f"{WP_URL}/wp-json/wp/v2/pages/6", json={"content": homepage}, headers=headers, timeout=20)
        print(f"WP push {res.status_code}")
    except Exception as e:
        print(f"WP fail {e}")

with open("results.json","w") as f:
    json.dump(draws,f,indent=2)
