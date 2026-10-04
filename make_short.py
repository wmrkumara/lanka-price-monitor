"""
TopGoviya.lk — weekly spice price YouTube Short maker
Reads dea_data.json -> builds 1080x1920 slides (HTML, rendered by Chromium so
Sinhala shapes correctly) -> joins them into an MP4 with ffmpeg.
Output: short/topgoviya-spices-YYYY-MM-DD.mp4 (+ title/description .txt)
"""
import json, base64, os, subprocess, sys
from datetime import date
from playwright.sync_api import sync_playwright

DATA = sys.argv[1] if len(sys.argv) > 1 else "dea_data.json"
LOGO = sys.argv[2] if len(sys.argv) > 2 else "icon-512x512.png"
OUT = "short"
SLIDE_SEC = 4.0
FADE = 0.5
os.makedirs(OUT, exist_ok=True)

SI_MONTHS = ['ජන','පෙබ','මාර්','අප්‍ර','මැයි','ජූනි','ජූලි','අගෝ','සැප්','ඔක්','නොව','දෙස්']
ITEMS = [  # spice key, grade, Sinhala name, grade label, emoji
    ("pepper",   "GR-1",  "කළු ගම්මිරිස්", "GR-1 · වියළි",  "🌶️"),
    ("pepper",   "WHITE", "සුදු ගම්මිරිස්", "WHITE",        "⚪"),
    ("cinnamon", "Alba",  "කුරුඳු",        "Alba ශ්‍රේණිය", "🪵"),
    ("clove",    "CLOVE", "කරාබු නැටි",     "CLOVE",        "🌿"),
    ("cardamom", "LG",    "එනසාල්",        "LG ශ්‍රේණිය",   "🫚"),
]
DIST_SI = {"Kandy":"මහනුවර","Matale":"මාතලේ","Nuwara_eliya":"නුවරඑළිය","Kegalle":"කෑගල්ල","Ratnapura":"රත්නපුර",
           "Badulla":"බදුල්ල","Kurunegala":"කුරුණෑගල","Colombo":"කොළඹ","Gampaha":"ගම්පහ","Kalutara":"කළුතර",
           "Galle":"ගාල්ල","Matara":"මාතර","Hambantota":"හම්බන්තොට","Monaragala":"මොණරාගල"}

d = json.load(open(DATA, encoding="utf-8"))
W = d["weeks"]; last, prev = W[-1], W[-2]
y, m, dd = map(int, last["date"].split("-"))
DATE_SI = f"{dd} {SI_MONTHS[m-1]} {y}"
DATE_EN = date(y, m, dd).strftime("%d %b %Y").lstrip("0")

def nat(w, sp, col):
    return w["commodities"].get(sp, {}).get("districts", {}).get("National", {}).get(col)
def rs(v): return "—" if v is None else f"{v:,.0f}"

rows = []
for sp, g, name, glabel, emo in ITEMS:
    a = nat(last, sp, f"{g} (Average Price)"); h = nat(last, sp, f"{g} (Highest Price)")
    p = nat(prev, sp, f"{g} (Average Price)")
    pct = (a - p) / p * 100 if (a and p) else None
    rows.append(dict(name=name, glabel=glabel, emo=emo, avg=a, hi=h, pct=pct))

pdist = {k: v.get("GR-1 (Average Price)") for k, v in last["commodities"]["pepper"]["districts"].items()
         if k != "National" and v.get("GR-1 (Average Price)")}
top3 = sorted(pdist.items(), key=lambda x: -x[1])[:3]

logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode()

CSS = """
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#f4efe4;font-family:'Noto Sans Sinhala',sans-serif;color:#191d1a;
 display:flex;flex-direction:column;overflow:hidden}
.top{background:#0e4f4a;color:#fff;padding:70px 70px 60px;display:flex;align-items:center;gap:34px}
.top img{width:150px;height:150px;border-radius:50%;border:5px solid #a9802a}
.top .b{font-size:52px;font-weight:800;letter-spacing:.5px}
.top .s{font-size:34px;color:#e7d3a3;margin-top:6px}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 80px}
.foot{background:#0b0b0b;color:#e7d3a3;text-align:center;padding:40px;font-size:34px;font-weight:600}
.mono{font-family:'JetBrains Mono',monospace}
.big{font-size:120px;font-weight:800;line-height:1.15;color:#0e4f4a}
.date{display:inline-block;margin-top:50px;font-size:48px;font-weight:700;background:#0e4f4a;color:#fff;
 border-radius:999px;padding:18px 44px}
.card{background:#fffdf7;border:4px solid #e3d9c4;border-left:18px solid #a9802a;border-radius:36px;padding:70px 70px 60px}
.emo{font-size:130px;line-height:1}
.nm{font-size:110px;font-weight:800;color:#0e4f4a;margin-top:30px;line-height:1.15}
.gr{font-size:46px;color:#a9802a;font-weight:700;margin-top:10px}
.price{font-size:150px;font-weight:800;margin-top:50px;letter-spacing:-3px}
.unit{font-size:46px;color:#7a7264;font-weight:600}
.meta{display:flex;justify-content:space-between;align-items:center;margin-top:40px;font-size:44px;color:#3a403a}
.chip{font-weight:800;padding:12px 30px;border-radius:20px;font-size:48px}
.up{background:#f7e6e2;color:#b23a2e}.down{background:#e3efe6;color:#2c7a52}.flat{background:#efeada;color:#8a8170}
.lbl{font-size:52px;font-weight:800;color:#0e4f4a;margin-bottom:40px}
.rank{display:flex;align-items:center;gap:36px;background:#fffdf7;border:4px solid #e3d9c4;border-radius:30px;padding:46px 54px;margin-bottom:30px}
.rank .n{font-size:80px;font-weight:800;color:#a9802a;width:80px}
.rank .d{flex:1;font-size:66px;font-weight:800}
.rank .v{font-size:64px;font-weight:800}
.url{font-size:88px;font-weight:800;color:#0e4f4a;margin-top:30px}
.note{font-size:40px;color:#7a7264;margin-top:60px;line-height:1.6}
"""
def page(inner):
    return f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="top"><img src="{logo}"><div><div class="b">TopGoviya.lk</div><div class="s">සතිපතා කුළුබඩු මිල · DEA</div></div></div>
<div class="main">{inner}</div>
<div class="foot">මූලාශ්‍රය: DEA · ගොවිපළ දොරටු මිල · {DATE_SI}</div></body></html>"""

def chip(p):
    if p is None: return '<span class="chip flat">—</span>'
    c = "flat" if abs(p) < 0.5 else ("up" if p > 0 else "down")
    a = {"up": "▲", "down": "▼", "flat": "■"}[c]
    return f'<span class="chip mono {c}">{a} {p:+.1f}%</span>'

slides = [page(f"""<div class="big">මේ සතියේ<br>කුළුබඩු මිල</div>
<div><span class="date mono">DEA · {DATE_SI}</span></div>
<div class="note">ගම්මිරිස් · කුරුඳු · කරාබු නැටි · එනසාල්<br>ජාතික සාමාන්‍ය මිල · රු./කි.ග්‍රෑ.</div>""")]
for r in rows:
    slides.append(page(f"""<div class="card"><div class="emo">{r['emo']}</div>
<div class="nm">{r['name']}</div><div class="gr">{r['glabel']}</div>
<div class="price mono">රු. {rs(r['avg'])}<span class="unit"> /කි.ග්‍රෑ.</span></div>
<div class="meta"><span>ඉහළම: <b class="mono">රු. {rs(r['hi'])}</b></span>{chip(r['pct'])}</div></div>"""))
ranks = "".join(f'<div class="rank"><div class="n mono">{i}</div><div class="d">{DIST_SI.get(k, k)}</div><div class="v mono">{rs(v)}</div></div>'
                for i, (k, v) in enumerate(top3, 1))
slides.append(page(f'<div class="lbl">🏆 ගම්මිරිස් GR-1 ඉහළම මිල දිස්ත්‍රික්ක</div>{ranks}<div class="note">රු./කි.ග්‍රෑ. · සාමාන්‍ය මිල</div>'))
slides.append(page(f"""<div class="big" style="font-size:96px">දිස්ත්‍රික්ක 14ක<br>සම්පූර්ණ මිල</div>
<div class="url">👉 topgoviya.lk</div>
<div class="note">නොමිලේ · සිංහල · தமிழ் · English<br>මිල ගණන් මඟපෙන්වීමක් පමණි.<br>ඔබේ තීරණ ඔබේ වගකීම වේ.</div>"""))

# ---- render slides ----
pngs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for i, html in enumerate(slides):
        pg.set_content(html); pg.wait_for_timeout(300)
        f = f"{OUT}/slide{i:02d}.png"; pg.screenshot(path=f); pngs.append(f)
    b.close()

# ---- join into MP4 with crossfades ----
n = len(pngs)
inputs = []
for f in pngs: inputs += ["-loop", "1", "-t", str(SLIDE_SEC), "-i", f]
chain, last_lbl, offset = [], "[0:v]", 0.0
for i in range(1, n):
    offset += SLIDE_SEC - FADE
    out = f"[v{i}]"
    chain.append(f"{last_lbl}[{i}:v]xfade=transition=fade:duration={FADE}:offset={offset:.2f}{out}")
    last_lbl = out
chain.append(f"{last_lbl}format=yuv420p,fps=30[outv]")
mp4 = f"{OUT}/topgoviya-spices-{last['date']}.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                "-map", "[outv]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", mp4], check=True)

# ---- ready-to-paste YouTube title + description ----
pep = rows[0]
title = f"ගම්මිරිස් මිල අද {y} | කුළුබඩු මිල {DATE_SI} | DEA #shorts"
desc = (f"මේ සතියේ කුළුබඩු ගොවිපළ දොරටු මිල — DEA වාර්තාව {DATE_SI}\n\n"
        + "\n".join(f"{r['emo']} {r['name']} ({r['glabel']}): රු. {rs(r['avg'])}/කි.ග්‍රෑ." for r in rows)
        + f"\n\n🏆 ගම්මිරිස් ඉහළම මිල: {DIST_SI.get(top3[0][0], top3[0][0])} — රු. {rs(top3[0][1])}\n\n"
        "👉 දිස්ත්‍රික්ක 14ක සම්පූර්ණ මිල: https://topgoviya.lk/spice-price-guide.html\n"
        "📊 මූලාශ්‍රය: අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුව (DEA)\n"
        "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි.\n\n#ගම්මිරිස්මිල #කුළුබඩුමිල #TopGoviyaLK #SriLanka #shorts")
open(f"{OUT}/youtube-{last['date']}.txt", "w", encoding="utf-8").write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n")
for f in pngs: os.remove(f)
print("Video:", mp4, f"({n} slides, ~{n*SLIDE_SEC-(n-1)*FADE:.0f}s)")
