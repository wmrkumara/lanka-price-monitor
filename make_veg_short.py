"""
TopGoviya.lk — weekly VEGETABLE price YouTube Short maker
Reads data.json (CBSL daily retail) -> week-over-week movers -> 1080x1920 MP4
Output: short/topgoviya-veg-YYYY-MM-DD.mp4 (+ youtube-veg-YYYY-MM-DD.txt)
"""
import json, base64, os, subprocess, sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

DATA = sys.argv[1] if len(sys.argv) > 1 else "data.json"
LOGO = sys.argv[2] if len(sys.argv) > 2 else "icon-512x512.png"
OUT = "short"; SLIDE_SEC = 4.0; FADE = 0.5
os.makedirs(OUT, exist_ok=True)

SI_MONTHS = ['ජන','පෙබ','මාර්','අප්‍ර','මැයි','ජූනි','ජූලි','අගෝ','සැප්','ඔක්','නොව','දෙස්']
NAMES = {"Beans":"බෝංචි","Carrot":"කැරට්","Cabbage":"ගෝවා","Tomato":"තක්කාලි","Brinjal":"වම්බටු","Pumpkin":"වට්ටක්කා",
 "Snake gourd":"පතෝල","Green Chilli":"අමු මිරිස්","Lime":"දෙහි","Red Onion (Local)":"රතු ළූණු (දේශීය)",
 "Red Onion (lmp)":"රතු ළූණු (ආනයනික)","Big Onion (Local)":"ලොකු ළූණු (දේශීය)","Big Onion (Imp)":"ලොකු ළූණු (ආනයනික)",
 "Potato (Local)":"අර්තාපල් (දේශීය)","Potato (Imp)":"අර්තාපල් (ආනයනික)","Coconut (Avg.)":"පොල්","Egg (White)":"බිත්තර"}
MARKETS = {"Pettah":"පිටකොටුව","Dambulla":"දඹුල්ල","Narahenpita":"නාරාහේන්පිට","Negombo":"මීගමුව","Marandagahamula":"මාරන්දගහමුල"}
UNITS = {"Rs./kg":"/කි.ග්‍රෑ.","Rs./Nut":"/ගෙඩිය","Rs./Each":"/එකක්"}
STAPLES = ["Beans","Carrot","Tomato","Big Onion (Imp)","Potato (Local)","Coconut (Avg.)"]

d = json.load(open(DATA, encoding="utf-8"))
dates = [date.fromisoformat(x) for x in d["dates"]]
L = len(dates) - 1
target = dates[L] - timedelta(days=7)
P = max(i for i, x in enumerate(dates) if x <= target)  # report about one week earlier
def si_date(x): return f"{x.day} {SI_MONTHS[x.month-1]}"
DATE_NOW, DATE_PREV = si_date(dates[L]), si_date(dates[P])
YEAR = dates[L].year

def val(series, i):
    for j in range(i, max(-1, i - 3), -1):  # tolerate a missing day
        if series[j] is not None: return series[j]
    return None
def rs(v): return "—" if v is None else f"{v:,.0f}"
def u(r): return "" if r["unit"] == "/කි.ග්‍රෑ." else r["unit"]

items = {}
for c in d["commodities"]:
    if c["name"] not in NAMES: continue
    a, p = val(c["series"], L), val(c["series"], P)
    if a is None or p is None or p == 0: continue
    items[c["name"]] = dict(si=NAMES[c["name"]], now=a, prev=p, pct=(a - p) / p * 100,
                            unit=UNITS.get(c["unit"], ""), markets=c.get("markets", {}), mkt=c["primaryMarket"])
movers = sorted(items.values(), key=lambda r: r["pct"])
falls = [r for r in movers if r["pct"] <= -0.5][:3]
rises = [r for r in reversed(movers) if r["pct"] >= 0.5][:3]
from collections import Counter
MAIN_MKT = MARKETS.get(Counter(r["mkt"] for r in items.values()).most_common(1)[0][0], "")
star = max(items.values(), key=lambda r: abs(r["pct"]))  # biggest mover -> market comparison

logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode()
CSS = """
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#f4efe4;font-family:'Noto Sans Sinhala',sans-serif;color:#191d1a;display:flex;flex-direction:column;overflow:hidden}
.top{background:#0e4f4a;color:#fff;padding:70px 70px 60px;display:flex;align-items:center;gap:34px}
.top img{width:150px;height:150px;border-radius:50%;border:5px solid #a9802a}
.top .b{font-size:52px;font-weight:800}.top .s{font-size:34px;color:#e7d3a3;margin-top:6px}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 70px}
.foot{background:#0b0b0b;color:#e7d3a3;text-align:center;padding:40px;font-size:34px;font-weight:600}
.mono{font-family:'JetBrains Mono',monospace}
.big{font-size:120px;font-weight:800;line-height:1.15;color:#0e4f4a}
.date{display:inline-block;margin-top:50px;font-size:46px;font-weight:700;background:#0e4f4a;color:#fff;border-radius:999px;padding:18px 44px}
.note{font-size:40px;color:#7a7264;margin-top:50px;line-height:1.6}
.lbl{font-size:62px;font-weight:800;margin-bottom:40px}
.row{display:flex;align-items:center;gap:26px;background:#fffdf7;border:4px solid #e3d9c4;border-radius:30px;padding:40px 46px;margin-bottom:28px}
.row .nm{flex:1;font-size:58px;font-weight:800;line-height:1.2}
.row .pr{font-size:44px;color:#3a403a;margin-top:6px}
.tag{display:inline-block;font-size:34px;font-weight:700;color:#0e4f4a;background:#e6efec;border-radius:12px;padding:4px 16px;margin-right:14px}
.cell .t{font-size:30px;font-weight:700;color:#0e4f4a;margin-top:4px}
.chip{font-weight:800;padding:12px 26px;border-radius:20px;font-size:50px;white-space:nowrap}
.up{background:#f7e6e2;color:#b23a2e}.down{background:#e3efe6;color:#2c7a52}.flat{background:#efeada;color:#8a8170}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.cell{background:#fffdf7;border:4px solid #e3d9c4;border-radius:28px;padding:36px 34px}
.cell .n{font-size:46px;font-weight:800;color:#0e4f4a;line-height:1.2;min-height:112px}
.cell .p{font-size:62px;font-weight:800;margin:10px 0}
.cell .c{font-size:38px;font-weight:800}
.mk{display:flex;justify-content:space-between;align-items:center;background:#fffdf7;border:4px solid #e3d9c4;border-radius:30px;padding:46px 54px;margin-bottom:28px;font-size:62px;font-weight:800}
.mk.best{border-color:#2c7a52;background:#eef6f0}
.url{font-size:88px;font-weight:800;color:#0e4f4a;margin-top:30px}
"""
def page(inner):
    return f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="top"><img src="{logo}"><div><div class="b">TopGoviya.lk</div><div class="s">සතිපතා එළවළු මිල · CBSL</div></div></div>
<div class="main">{inner}</div>
<div class="foot">මූලාශ්‍රය: ශ්‍රී ලංකා මහ බැංකුව · සිල්ලර මිල · {DATE_NOW} {YEAR}</div></body></html>"""
def chip(p):
    c = "flat" if abs(p) < 0.5 else ("up" if p > 0 else "down")
    return f'<span class="chip mono {c}">{ {"up":"▲","down":"▼","flat":"■"}[c]} {p:+.0f}%</span>'
def rows(lst):
    return "".join(f'<div class="row"><div style="flex:1"><div class="nm">{r["si"]}</div>'
                   f'<div style="margin-top:8px"><span class="tag">📍 {MARKETS.get(r["mkt"], r["mkt"])} · සිල්ලර</span></div><div class="pr mono">{rs(r["prev"])} → <b>{rs(r["now"])}</b></div></div>{chip(r["pct"])}</div>' for r in lst)

slides = [page(f"""<div class="big" style="font-size:112px">මේ සතියේ<br>එළවළු<br><span style="color:#a9802a">සිල්ලර</span> මිල</div>
<div><span class="date mono">{DATE_PREV} → {DATE_NOW} {YEAR}</span></div>
<div class="note">Retail prices · CBSL දෛනික මිල වාර්තාව<br>ප්‍රධාන වෙළඳපොළ: <b>{MAIN_MKT}</b> · සතියකට පෙර සහ අද<br>රු./කි.ග්‍රෑ.</div>""")]
if rises: slides.append(page(f'<div class="lbl" style="color:#b23a2e">📈 මිල ඉහළ ගිය</div>{rows(rises)}<div class="note">සිල්ලර මිල · සතියකට පෙර → අද · රු./කි.ග්‍රෑ.</div>'))
if falls: slides.append(page(f'<div class="lbl" style="color:#2c7a52">📉 මිල පහළ ගිය</div>{rows(falls)}<div class="note">සිල්ලර මිල · සතියකට පෙර → අද · රු./කි.ග්‍රෑ.</div>'))
cells = "".join(f'<div class="cell"><div class="n">{items[k]["si"]}</div><div class="t">📍 {MARKETS.get(items[k]["mkt"], items[k]["mkt"])} · සිල්ලර</div><div class="p mono">රු. {rs(items[k]["now"])}<span style="font-size:30px;color:#7a7264">{u(items[k])}</span></div>'
                f'<div class="c mono {"up" if items[k]["pct"]>=0.5 else "down" if items[k]["pct"]<=-0.5 else "flat"}" style="background:none;padding:0">'
                f'{"▲" if items[k]["pct"]>=0.5 else "▼" if items[k]["pct"]<=-0.5 else "■"} {items[k]["pct"]:+.0f}%</div></div>'
                for k in STAPLES if k in items)
slides.append(page(f'<div class="lbl" style="color:#0e4f4a">🛒 ප්‍රධාන භාණ්ඩ</div><div class="grid">{cells}</div><div class="note">සිල්ලර මිල · සතිපතා වෙනස · රු.</div>'))
mk = {k: v for k, v in star["markets"].items() if v and k in MARKETS}
if len(mk) >= 2:
    cheap = min(mk, key=mk.get)
    mrows = "".join(f'<div class="mk{" best" if k==cheap else ""}"><span>{MARKETS[k]}{" ✅" if k==cheap else ""}</span><span class="mono">රු. {rs(v)}</span></div>'
                    for k, v in sorted(mk.items(), key=lambda x: x[1]))
    slides.append(page(f'<div class="lbl" style="color:#0e4f4a">📍 {star["si"]} — වෙළඳපොළ අනුව</div>{mrows}<div class="note">එකම භාණ්ඩය, වෙනස් වෙළඳපොළ · සිල්ලර මිල · {star["unit"]} · {DATE_NOW}</div>'))
slides.append(page(f"""<div class="big" style="font-size:96px">එළවළු 40+<br>අද මිල</div>
<div class="url">👉 topgoviya.lk</div>
<div class="note">නොමිලේ · සිංහල · தமிழ் · English<br>මිල ගණන් මඟපෙන්වීමක් පමණි.<br>ඔබේ තීරණ ඔබේ වගකීම වේ.</div>"""))

pngs = []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for i, html in enumerate(slides):
        pg.set_content(html); pg.wait_for_timeout(300)
        f = f"{OUT}/veg{i:02d}.png"; pg.screenshot(path=f); pngs.append(f)
    b.close()
n = len(pngs); inputs = []
for f in pngs: inputs += ["-loop", "1", "-t", str(SLIDE_SEC), "-i", f]
chain, last_lbl, off = [], "[0:v]", 0.0
for i in range(1, n):
    off += SLIDE_SEC - FADE
    chain.append(f"{last_lbl}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[v{i}]"); last_lbl = f"[v{i}]"
chain.append(f"{last_lbl}format=yuv420p,fps=30[outv]")
tag = dates[L].isoformat()
mp4 = f"{OUT}/topgoviya-veg-{tag}.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                "-map", "[outv]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", mp4], check=True)

title = f"එළවළු මිල අද {YEAR} | මේ සතියේ එළවළු සිල්ලර මිල {DATE_NOW} | {MAIN_MKT} | CBSL #shorts"
def mk_si(r): return MARKETS.get(r["mkt"], r["mkt"])
lines_up = [f"📈 {r['si']} ({mk_si(r)}): රු. {rs(r['prev'])} → {rs(r['now'])} ({r['pct']:+.0f}%)" for r in rises]
lines_dn = [f"📉 {r['si']} ({mk_si(r)}): රු. {rs(r['prev'])} → {rs(r['now'])} ({r['pct']:+.0f}%)" for r in falls]
lines_st = [f"🛒 {items[k]['si']} ({mk_si(items[k])}): රු. {rs(items[k]['now'])}{u(items[k])} ({items[k]['pct']:+.0f}%)" for k in STAPLES if k in items]
mk_line = ""
if len(mk) >= 2:
    mk_line = (f"\n📍 {star['si']} — වෙළඳපොළ අනුව සිල්ලර මිල ({DATE_NOW}):\n" +
               "\n".join(f"   {MARKETS[k]}: රු. {rs(v)}{'  ✅ අඩුම' if k == cheap else ''}" for k, v in sorted(mk.items(), key=lambda x: x[1])) + "\n")
desc = (f"🥕 මේ සතියේ එළවළු සිල්ලර මිල — {DATE_PREV} → {DATE_NOW} {YEAR}\n"
        f"📍 ප්‍රධාන වෙළඳපොළ: {MAIN_MKT} · සිල්ලර මිල (Retail) · රු./කි.ග්‍රෑ.\n"
        + ("\nමිල ඉහළ ගිය:\n" + "\n".join(lines_up) + "\n" if lines_up else "")
        + ("\nමිල පහළ ගිය:\n" + "\n".join(lines_dn) + "\n" if lines_dn else "")
        + "\nප්‍රධාන භාණ්ඩ:\n" + "\n".join(lines_st) + "\n"
        + mk_line +
        "\n👉 එළවළු 40+ අද මිල, වෙළඳපොළ 3ක: https://topgoviya.lk\n"
        "📊 මූලාශ්‍රය: ශ්‍රී ලංකා මහ බැංකුව (CBSL) දෛනික මිල වාර්තාව\n"
        "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
        "#එළවළුමිල #සිල්ලරමිල #VegetablePrices #TopGoviyaLK #SriLanka #shorts")
open(f"{OUT}/youtube-veg-{tag}.txt", "w", encoding="utf-8").write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n")
for f in pngs: os.remove(f)
print("Video:", mp4, f"({n} slides, ~{n*SLIDE_SEC-(n-1)*FADE:.0f}s)")
