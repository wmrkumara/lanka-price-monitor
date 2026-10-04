"""
TopGoviya.lk — weekly HARTI wholesale YouTube Short (10 markets, for farmers)
Usage: python3 make_harti_short.py harti_data.json icon-512x512.png
Output: short/topgoviya-harti-DATE.mp4 + short/youtube-harti-DATE.txt
"""
import json, base64, os, subprocess, sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

DATA = sys.argv[1] if len(sys.argv) > 1 else "harti_data.json"
LOGO = sys.argv[2] if len(sys.argv) > 2 else "icon-512x512.png"
OUT = "short"; SLIDE_SEC = 4.5; FADE = 0.5
os.makedirs(OUT, exist_ok=True)

SI_MONTHS = ['ජන','පෙබ','මාර්','අප්‍ර','මැයි','ජූනි','ජූලි','අගෝ','සැප්','ඔක්','නොව','දෙස්']
# Same names as the live wholesale.html (HARTI_MARKETS_SI / HARTI_NAMES_SI)
MK = {"Peliyagoda":"පෑලියගොඩ","Kandy":"මහනුවර","Dambulla":"දඹුල්ල","Meegoda":"මීගොඩ","Norochchole":"නොරොච්චෝලේ",
      "Thambuththegama":"තඹුත්තේගම","Keppetipola":"කෑප්පෙටිපොළ","Nuwaraeliya":"නුවරඑළිය","Bandarawela":"බණ්ඩාරවෙල","Veyangoda":"වේයන්ගොඩ"}
NM = {"Beans":"බෝංචි","Carrot":"කැරට්","Leeks":"ලීක්ස්","Beetroot":"බීට්රූට්","Knolkhol":"නෝල්කෝල්","Raddish":"රාබු",
      "Cabbage (Kandy)":"ගෝවා (නුවර)","Cabbage (N.Eliya)":"ගෝවා (නුවරඑළිය)","Tomato":"තක්කාලි","Ladies Fingers":"බණ්ඩක්කා",
      "Brinjals":"වම්බටු","Capsicum":"මාළු මිරිස්","Pumpkin":"වට්ටක්කා","Cucumber":"පිපිඤ්ඤා","Bitter Gourd":"කරවිල",
      "Snake Gourd":"පතෝල","Luffa":"වැටකොළු","Long Beans":"මෑකරල්","Ash Plantains":"අළු කෙසෙල්","Green Chillies":"අමු මිරිස්",
      "Lime":"දෙහි","Sweet Potato":"බතල","Manioc":"මඤ්ඤොක්කා","Drumstick":"මුරුංගා","Eggplant":"එළබටු",
      "Potato (N.Eliya)":"අර්තාපල් (නුවරඑළිය)","Potato (Welimada)":"අර්තාපල් (වැලිමඩ)","Potato (Imported)":"අර්තාපල් (ආනයනික)",
      "Big Onion (Imported)":"ලොකු ළූණු (ආනයනික)","Beetroot (N.Eliya)":"බීට්රූට් (නුවරඑළිය)"}
VEG_CATS = {"Up Country Vegetables", "Low Country Vegetables", "Potatoes & Onions"}
SELL_CROPS = ["Beans", "Carrot", "Tomato", "Potato (N.Eliya)", "Cabbage (N.Eliya)", "Green Chillies", "Pumpkin", "Brinjals"]

h = json.load(open(DATA, encoding="utf-8"))
dates = [date.fromisoformat(x) for x in h["dates"]]
L = len(dates) - 1
P = max(i for i, x in enumerate(dates) if x <= dates[L] - timedelta(days=7))
def si_date(x): return f"{x.day} {SI_MONTHS[x.month-1]}"
DATE_NOW, DATE_PREV, YEAR, TAG = si_date(dates[L]), si_date(dates[P]), dates[L].year, dates[L].isoformat()
def val(s, i):
    for j in range(i, max(-1, i - 3), -1):
        if s[j] is not None: return s[j]
    return None
def rs(v): return "—" if v is None else f"{v:,.0f}"

items = {}
for c in h["commodities"]:
    if c["category"] not in VEG_CATS or c["name"] not in NM: continue
    s = c.get("series") or []
    a, p = (val(s, L), val(s, P)) if len(s) > L else (None, None)
    mk = {k: v for k, v in (c.get("markets") or {}).items() if k in MK and v and v.get("mid")}
    items[c["name"]] = dict(si=NM[c["name"]], now=a, prev=p,
                            pct=((a - p) / p * 100) if (a and p) else None, pm=c.get("primaryMarket", "Peliyagoda"), mk=mk)
mov = [r for r in items.values() if r["pct"] is not None]
rises = sorted([r for r in mov if r["pct"] >= 0.5], key=lambda r: -r["pct"])[:3]
falls = sorted([r for r in mov if r["pct"] <= -0.5], key=lambda r: r["pct"])[:3]
# "where to sell": crops reported in 4+ markets, biggest price gap first
cands = [(k, r) for k, r in items.items() if k in SELL_CROPS and len(r["mk"]) >= 4]
def gap(r):
    mids = [v["mid"] for v in r["mk"].values()]; return (max(mids) - min(mids)) / min(mids)
sell = sorted(cands, key=lambda kr: -gap(kr[1]))[:3]

logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode()
CSS = """
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#f4efe4;font-family:'Noto Sans Sinhala',sans-serif;color:#191d1a;display:flex;flex-direction:column;overflow:hidden}
.top{background:#0e4f4a;color:#fff;padding:70px 70px 60px;display:flex;align-items:center;gap:34px}
.top img{width:150px;height:150px;border-radius:50%;border:5px solid #a9802a}
.top .b{font-size:52px;font-weight:800}.top .s{font-size:34px;color:#e7d3a3;margin-top:6px}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 64px}
.foot{background:#0b0b0b;color:#e7d3a3;text-align:center;padding:40px;font-size:32px;font-weight:600}
.mono{font-family:'JetBrains Mono',monospace}
.big{font-size:108px;font-weight:800;line-height:1.15;color:#0e4f4a}
.date{display:inline-block;margin-top:46px;font-size:46px;font-weight:700;background:#0e4f4a;color:#fff;border-radius:999px;padding:18px 44px}
.note{font-size:38px;color:#7a7264;margin-top:40px;line-height:1.6}
.lbl{font-size:60px;font-weight:800;margin-bottom:34px;line-height:1.25}
.row{display:flex;align-items:center;gap:24px;background:#fffdf7;border:4px solid #e3d9c4;border-radius:30px;padding:38px 44px;margin-bottom:26px}
.row .nm{font-size:56px;font-weight:800;line-height:1.2}
.row .pr{font-size:44px;color:#3a403a;margin-top:6px}
.tag{display:inline-block;font-size:32px;font-weight:700;color:#0e4f4a;background:#e6efec;border-radius:12px;padding:4px 16px}
.chip{font-weight:800;padding:12px 24px;border-radius:20px;font-size:48px;white-space:nowrap}
.up{background:#f7e6e2;color:#b23a2e}.down{background:#e3efe6;color:#2c7a52}
.m{display:flex;justify-content:space-between;align-items:center;background:#fffdf7;border:4px solid #e3d9c4;border-radius:26px;padding:30px 44px;margin-bottom:20px}
.m .n{font-size:52px;font-weight:800}.m .v{font-size:52px;font-weight:800}.m .r{font-size:30px;color:#7a7264;text-align:right}
.m.best{border-color:#2c7a52;background:#eef6f0}.m.low{border-color:#e3c9c2;background:#fbf1ee}
.gap{font-size:40px;font-weight:800;color:#a9802a;margin-top:18px}
.url{font-size:76px;font-weight:800;color:#0e4f4a;margin-top:30px}
"""
CALC_CSS = """
.ex{display:flex;justify-content:space-between;align-items:center;background:#fffdf7;border:4px solid #e3d9c4;border-radius:24px;padding:22px 38px;margin-bottom:14px}
.ex.low{border-color:#e3c9c2;background:#fbf1ee}
.ex .n{font-size:50px;font-weight:800}.ex .f{font-size:32px;color:#7a7264;margin-top:4px}
.ex .v{font-size:56px;font-weight:800;color:#0e4f4a;text-align:right}
.ex.best{border-color:#2c7a52;background:#eef6f0}
.sub{font-size:36px;font-weight:700;color:#3a403a;margin:-10px 0 22px}
.warn{background:#fff8ec;border-left:12px solid #a9802a;padding:22px 30px;font-size:36px;line-height:1.5;color:#3a403a;margin-top:10px}
.go{background:#0e4f4a;color:#fff;border-radius:24px;padding:24px 34px;font-size:40px;font-weight:800;margin-top:18px;line-height:1.4}
"""
def calc_example(crop_si, rows, unit_si, url_text, kg=500):
    """rows: list of (market_si, price). Shows harvest value = kg x price per market."""
    rows = sorted(rows, key=lambda r: -r[1])
    rows = rows[:3] + ([rows[-1]] if len(rows) > 3 else [])  # top 3 + lowest
    hi = rows[0][1]
    body = "".join(
        f'<div class="ex{" best" if p == hi else (" low" if (m, p) == rows[-1] and len(rows) > 1 else "")}"><div><div class="n">{m}{" ✅" if p == hi else ""}</div>'
        f'<div class="f mono">{kg} kg × රු.{p:,.0f}</div></div><div class="v mono">රු.{kg*p:,.0f}</div></div>' for m, p in rows)
    diff = (rows[0][1] - rows[-1][1]) * kg
    return f"""<div class="lbl" style="color:#0e4f4a;margin-bottom:24px">🧮 උදාහරණය: {crop_si} {kg} kg</div>
<div class="sub">අස්වැන්නේ වටිනාකම · {unit_si}</div>{body}
<div class="gap" style="font-size:40px;font-weight:800;color:#a9802a;margin:6px 0 10px">වෙනස: රු.{diff:,.0f} දක්වා</div>
<div class="warn">⚠️ ප්‍රවාහන වියදම අඩු කළ පසු සැබෑ ලාභය වෙනස් වේ</div>
<div class="go">🧮 ගොවියාගේ ලාභය | වෙළෙන්දාගේ ලාභය ගණනය කරගන්න<br><span style="color:#e7d3a3;font-size:36px">{url_text} · ඔබේ ප්‍රවාහන වියදම ඇතුළත් කරන්න</span></div>"""

CSS = CSS + CALC_CSS
def page(inner):
    return f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="top"><img src="{logo}"><div><div class="b">TopGoviya.lk</div><div class="s">තොග මිල · වෙළඳපොළ 10ක · HARTI</div></div></div>
<div class="main">{inner}</div>
<div class="foot">මූලාශ්‍රය: HARTI · තොග මිල මධ්‍යගතය · {DATE_NOW} {YEAR}</div></body></html>"""
def chip(p):
    c = "up" if p > 0 else "down"
    return f'<span class="chip mono {c}">{"▲" if p > 0 else "▼"} {p:+.0f}%</span>'
def rows(lst):
    return "".join(f'<div class="row"><div style="flex:1"><div class="nm">{r["si"]}</div>'
                   f'<div style="margin-top:8px"><span class="tag">📍 {MK.get(r["pm"], r["pm"])} · තොග</span></div>'
                   f'<div class="pr mono">{rs(r["prev"])} → <b>{rs(r["now"])}</b></div></div>{chip(r["pct"])}</div>' for r in lst)

slides = [page(f"""<div class="big">මේ සතියේ<br>එළවළු<br><span style="color:#a9802a">තොග</span> මිල</div>
<div style="font-size:64px;font-weight:800;color:#3a403a;margin-top:20px">ආර්ථික මධ්‍යස්ථාන 10ක</div>
<div><span class="date mono">{DATE_PREV} → {DATE_NOW} {YEAR}</span></div>
<div class="note">HARTI තොග මිල මධ්‍යගතය · රු./කි.ග්‍රෑ.<br>ගොවීන් සහ වෙළෙන්දන් සඳහා · කොහේ විකුණන්නද?</div>""")]
nw = f'<div class="note">තොග මිල මධ්‍යගතය · සතියකට පෙර → අද · රු./කි.ග්‍රෑ.</div>'
if rises: slides.append(page(f'<div class="lbl" style="color:#b23a2e">📈 තොග මිල ඉහළ ගිය</div>{rows(rises)}{nw}'))
if falls: slides.append(page(f'<div class="lbl" style="color:#2c7a52">📉 තොග මිල පහළ ගිය</div>{rows(falls)}{nw}'))
sell_txt = []
for k, r in sell:
    order = sorted(r["mk"].items(), key=lambda kv: -kv[1]["mid"])
    top, low = order[:4], order[-1]
    show = top + ([low] if low not in top else [])
    hi = order[0][1]["mid"]
    rws = "".join(f'<div class="m{" best" if kv[1]["mid"] == hi else (" low" if kv == low else "")}"><div class="n">{MK[kv[0]]}{" ✅" if kv[1]["mid"] == hi else ""}</div>'
                  f'<div><div class="v mono">රු. {rs(kv[1]["mid"])}</div><div class="r mono">{rs(kv[1]["min"])}–{rs(kv[1]["max"])}</div></div></div>'
                  for i, kv in enumerate(show))
    g = order[0][1]["mid"] - low[1]["mid"]
    slides.append(page(f'<div class="lbl" style="color:#0e4f4a">🚚 {r["si"]}<br>කොහේ විකුණන්නද?</div>{rws}'
                       f'<div class="gap">ඉහළම සහ අඩුම අතර: රු. {rs(g)}/කි.ග්‍රෑ.</div>'
                       f'<div class="note" style="margin-top:14px">✅ ඉහළම තොග මිල · ප්‍රවාහන වියදම සලකා බලන්න · {DATE_NOW}</div>'))
    tops = " / ".join(MK[k2] for k2, v2 in order if v2["mid"] == hi)
    sell_txt.append(f"🚚 {r['si']}: ඉහළම {tops} රු. {rs(hi)} · අඩුම {MK[low[0]]} රු. {rs(low[1]['mid'])}")
if sell:
    _k, _r = sell[0]
    slides.append(page(calc_example(_r["si"], [(MK[m], v["mid"]) for m, v in _r["mk"].items()],
                                    "HARTI තොග මිල මධ්‍යගතය · " + DATE_NOW, "topgoviya.lk/wholesale.html")))
slides.append(page("""<div class="big" style="font-size:90px">වෙළඳපොළ 10ක<br>තොග මිල අද</div>
<div class="url">👉 topgoviya.lk/<br>wholesale.html</div>
<div class="note">නොමිලේ · සිංහල · தமிழ் · English<br>මිල ගණන් මඟපෙන්වීමක් පමණි.<br>ඔබේ තීරණ ඔබේ වගකීම වේ.</div>"""))

pngs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for i, html in enumerate(slides):
        pg.set_content(html); pg.wait_for_timeout(300)
        f = f"{OUT}/harti{i:02d}.png"; pg.screenshot(path=f); pngs.append(f)
    b.close()
n = len(pngs); inputs = []
for f in pngs: inputs += ["-loop", "1", "-t", str(SLIDE_SEC), "-i", f]
chain, last_lbl, off = [], "[0:v]", 0.0
for i in range(1, n):
    off += SLIDE_SEC - FADE
    chain.append(f"{last_lbl}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[v{i}]"); last_lbl = f"[v{i}]"
chain.append(f"{last_lbl}format=yuv420p,fps=30[outv]")
mp4 = f"{OUT}/topgoviya-harti-{TAG}.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                "-map", "[outv]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", mp4], check=True)

title = f"එළවළු තොග මිල අද {YEAR} | වෙළඳපොළ 10ක | කොහේ විකුණන්නද? {DATE_NOW} | HARTI #shorts"
up = [f"📈 {r['si']} ({MK.get(r['pm'], r['pm'])}): රු. {rs(r['prev'])} → {rs(r['now'])} ({r['pct']:+.0f}%)" for r in rises]
dn = [f"📉 {r['si']} ({MK.get(r['pm'], r['pm'])}): රු. {rs(r['prev'])} → {rs(r['now'])} ({r['pct']:+.0f}%)" for r in falls]
desc = (f"🌾 මේ සතියේ එළවළු තොග මිල — ආර්ථික මධ්‍යස්ථාන 10ක — {DATE_PREV} → {DATE_NOW} {YEAR}\n"
        "📍 HARTI තොග මිල මධ්‍යගතය · රු./කි.ග්‍රෑ. · ගොවීන් සහ වෙළෙන්දන් සඳහා\n"
        + ("\nතොග මිල ඉහළ ගිය:\n" + "\n".join(up) + "\n" if up else "")
        + ("\nතොග මිල පහළ ගිය:\n" + "\n".join(dn) + "\n" if dn else "")
        + ("\nකොහේ විකුණන්නද? (" + DATE_NOW + "):\n" + "\n".join(sell_txt) + "\n" if sell_txt else "")
        + "\n👉 වෙළඳපොළ 10ක තොග මිල: https://topgoviya.lk/wholesale.html\n"
        "📊 මූලාශ්‍රය: හෙක්ටර් කොබ්බෑකඩුව ගොවිජන පර්යේෂණ හා පුහුණු ආයතනය (HARTI)\n"
        "🧮 ගොවියාගේ ලාභය | වෙළෙන්දාගේ ලාභය ගණනය කරගන්න: https://topgoviya.lk/wholesale.html\n"
        "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ප්‍රවාහන වියදම සලකා බලන්න. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
        "#එළවළුතොගමිල #තොගමිල #දඹුල්ල #පෑලියගොඩ #HARTI #TopGoviyaLK #SriLanka #shorts")
open(f"{OUT}/youtube-harti-{TAG}.txt", "w", encoding="utf-8").write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n")
for f in pngs: os.remove(f)
print("Video:", mp4, f"({n} slides, ~{n*SLIDE_SEC-(n-1)*FADE:.0f}s)")
