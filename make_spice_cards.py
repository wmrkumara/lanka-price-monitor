"""
TopGoviya.lk — one YouTube/TikTok/Facebook Short per spice (14 videos) from dea_data.json
Usage: python3 make_spice_cards.py dea_data.json icon-512x512.png
Output: short/spices/NN-key-DATE.mp4 + NN-key-DATE.txt  (title + description)
"""
import json, base64, os, subprocess, sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

DATA = sys.argv[1] if len(sys.argv) > 1 else "dea_data.json"
LOGO = sys.argv[2] if len(sys.argv) > 2 else "icon-512x512.png"
OUT = "short/spices"; SLIDE_SEC = 4.5; FADE = 0.5
os.makedirs(OUT, exist_ok=True)
SI_MONTHS = ['ජන','පෙබ','මාර්','අප්‍ර','මැයි','ජූනි','ජූලි','අගෝ','සැප්','ඔක්','නොව','දෙස්']
DIST = {"Kandy":"මහනුවර","Matale":"මාතලේ","Nuwara_eliya":"නුවරඑළිය","Kegalle":"කෑගල්ල","Ratnapura":"රත්නපුර","Badulla":"බදුල්ල",
        "Kurunegala":"කුරුණෑගල","Colombo":"කොළඹ","Gampaha":"ගම්පහ","Kalutara":"කළුතර","Galle":"ගාල්ල","Matara":"මාතර",
        "Hambantota":"හම්බන්තොට","Monaragala":"මොණරාගල"}
KG = "රු./කි.ග්‍රෑ."
# key, card, icon, Sinhala name, main grade column, grade columns to list, unit, example qty, example unit word
VIDEOS = [
 ("pepper","pepper","🌶️","ගම්මිරිස්","GR-1",["GR-1","GR-2","WHITE"],KG,100,"kg"),
 ("cinnamon","cinnamon","🪵","කුරුඳු","C-5",["Alba","C-5 Sp","C-5","C-4","M-5","M-4"],KG,100,"kg"),
 ("cardamom","cardamom","🫚","එනසාල්","LLG1",["LG","LLG1","LLG2","LB","LNS"],KG,10,"kg"),
 ("clove","clove","🌿","කරාබු නැටි","CLOVE",["CLOVE","STEM"],KG,100,"kg"),
 ("nutmeg","nutmeg","🥜","සාදික්කා සහ වසාවාසි","NUTMEG No.1",["NUTMEG No.1","NUTMEG No.2","NUTMEG BWP","MACE No.1","MACE No.2"],KG,100,"kg"),
 ("coffee","coffee","☕","කෝපි","GR 1",["GR 1","GR 2","PARCHMENT"],KG,100,"kg"),
 ("cocoa","cocoa","🍫","කොකෝ","GR 1",["GR 1","GR 2","GR 3","BLACK"],KG,100,"kg"),
 ("arecanut","arecanut","🌴","පුවක්","Dried-(Karunka)-(Rs./k.g.)",["Dried-(Karunka)-(Rs./k.g.)"],KG,100,"kg"),
 ("betel","betel","🍃","බුලත්","Local-Peedunu-",["Local-Peedunu-","Local-Keti-","Local-korikan-"],"රු./කොළ 1000",10,"LEAVES"),
 ("goraka","other","🌾","ගොරකා","Goraka",["Goraka"],KG,100,"kg"),
 ("ginger","other","🫚","ඉඟුරු","Ginger",["Ginger"],KG,100,"kg"),
 ("turmeric","other","🟡","කහ","Turmeric",["Turmeric"],KG,100,"kg"),
 ("kithul","other","🍯","කිතුල් හකුරු","Kithul Jaggery",["Kithul Jaggery"],KG,50,"kg"),
 ("leafoil","oil","💧","කුරුඳු කොළ තෙල්","Cinnamon Leaf Oil",["Cinnamon Leaf Oil"],KG,10,"kg"),
]
GRADE_LBL = {"Dried-(Karunka)-(Rs./k.g.)":"වියළි (කරුංකා)","Local-Peedunu-":"පීදුණු","Local-Keti-":"කෙටි","Local-korikan-":"කොරිකන්",
             "NUTMEG No.1":"සාදික්කා No.1","NUTMEG No.2":"සාදික්කා No.2","NUTMEG BWP":"සාදික්කා BWP","MACE No.1":"වසාවාසි No.1",
             "MACE No.2":"වසාවාසි No.2","Goraka":"ගොරකා","Ginger":"ඉඟුරු","Turmeric":"කහ","Kithul Jaggery":"කිතුල් හකුරු",
             "Cinnamon Leaf Oil":"කුරුඳු කොළ තෙල්"}
def col(g, kind="Average"):
    return f"{g}(Average Price)" if g.endswith("-") else f"{g} ({kind} Price)"
def hcol(g):
    return f"{g}(Highest Price)" if g.endswith("-") else f"{g} (Highest Price)"

d = json.load(open(DATA, encoding="utf-8")); W = d["weeks"]
dates = [date.fromisoformat(w["date"]) for w in W]; L = len(W) - 1
def si_date(x, year=True): return f"{x.day} {SI_MONTHS[x.month-1]}" + (f" {x.year}" if year else "")
NOW = dates[L]; DATE_SI = si_date(NOW); TAG = NOW.isoformat()
def nat(i, card, c):
    v = W[i]["commodities"].get(card, {}).get("districts", {}).get("National", {}).get(c)
    return v if isinstance(v, (int, float)) and v > 0 else None
def rs(v): return "—" if v is None else f"{v:,.0f}"
logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode()

CSS = """
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#f4efe4;font-family:'Noto Sans Sinhala',sans-serif;color:#191d1a;display:flex;flex-direction:column;overflow:hidden}
.top{background:#0e4f4a;color:#fff;padding:70px 70px 60px;display:flex;align-items:center;gap:34px}
.top img{width:150px;height:150px;border-radius:50%;border:5px solid #a9802a}
.top .b{font-size:52px;font-weight:800}.top .s{font-size:34px;color:#e7d3a3;margin-top:6px}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 66px}
.foot{background:#0b0b0b;color:#e7d3a3;text-align:center;padding:34px 40px;font-size:31px;font-weight:600;line-height:1.5}
.mono{font-family:'JetBrains Mono',monospace}
.emo{font-size:140px;line-height:1}
.h1{font-size:104px;font-weight:800;color:#0e4f4a;line-height:1.15;margin-top:20px}
.gr{font-size:46px;color:#a9802a;font-weight:700;margin-top:8px}
.price{font-size:150px;font-weight:800;margin-top:40px;letter-spacing:-3px}
.unit{font-size:44px;color:#7a7264;font-weight:600}
.chip{display:inline-block;font-weight:800;padding:14px 32px;border-radius:22px;font-size:54px;margin-top:30px}
.up{background:#f7e6e2;color:#b23a2e}.down{background:#e3efe6;color:#2c7a52}.flat{background:#efeada;color:#8a8170}
.date{display:inline-block;margin-top:34px;font-size:40px;font-weight:700;background:#0e4f4a;color:#fff;border-radius:999px;padding:14px 38px}
.lbl{font-size:60px;font-weight:800;color:#0e4f4a;margin-bottom:34px;line-height:1.25}
.row{display:flex;justify-content:space-between;align-items:center;background:#fffdf7;border:4px solid #e3d9c4;border-radius:26px;padding:30px 44px;margin-bottom:18px}
.row .n{font-size:50px;font-weight:800}.row .v{font-size:54px;font-weight:800}.row .s{font-size:30px;color:#7a7264;text-align:right}
.row.best{border-color:#2c7a52;background:#eef6f0}.row.low{border-color:#e3c9c2;background:#fbf1ee}.row.pick{border-color:#a9802a;background:#fff8ec}
.cmp{display:flex;gap:22px;margin-top:10px}
.box{flex:1;background:#fffdf7;border:4px solid #e3d9c4;border-radius:28px;padding:40px 30px;text-align:center}
.box .y{font-size:46px;font-weight:800;color:#7a7264}.box .p{font-size:74px;font-weight:800;margin-top:14px}
.box.now{border-color:#0e4f4a;background:#eef6f0}.box.now .y{color:#0e4f4a}
.big{font-size:88px;font-weight:800;text-align:center;margin-top:40px}
.bar{position:relative;height:40px;background:linear-gradient(90deg,#e3efe6,#f7e6e2);border-radius:20px;margin:110px 0 30px}
.dot{position:absolute;top:-14px;width:68px;height:68px;border-radius:50%;background:#0e4f4a;border:8px solid #fff;transform:translateX(-50%)}
.tag{position:absolute;top:-104px;transform:translateX(-50%);font-size:44px;font-weight:800;color:#0e4f4a;white-space:nowrap}
.ends{display:flex;justify-content:space-between;font-size:40px;font-weight:700}
.ends .s{font-size:30px;color:#7a7264;font-weight:600}
.ex{display:flex;justify-content:space-between;align-items:center;background:#fffdf7;border:4px solid #e3d9c4;border-radius:24px;padding:26px 40px;margin-bottom:16px}
.ex.best{border-color:#2c7a52;background:#eef6f0}
.ex .n{font-size:48px;font-weight:800}.ex .f{font-size:32px;color:#7a7264}.ex .v{font-size:56px;font-weight:800;color:#0e4f4a}
.warn{background:#fff8ec;border-left:12px solid #a9802a;padding:22px 30px;font-size:36px;line-height:1.5;color:#3a403a;margin-top:12px}
.ins{background:#0e4f4a;color:#fff;border-radius:34px;padding:60px 56px;font-size:66px;font-weight:800;line-height:1.35}
.ins .s{font-size:40px;color:#e7d3a3;font-weight:600;margin-top:24px;line-height:1.5}
.url{font-size:62px;font-weight:800;color:#0e4f4a;margin-top:30px;line-height:1.3}
.note{font-size:38px;color:#7a7264;margin-top:36px;line-height:1.6}
"""
def page(inner):
    return f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="top"><img src="{logo}"><div><div class="b">TopGoviya.lk</div><div class="s">සතිපතා කුළුබඩු මිල · DEA</div></div></div>
<div class="main">{inner}</div>
<div class="foot">දත්ත අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුවෙන් (DEA) · ගොවිපළ දොරටු මිල · {DATE_SI}</div></body></html>"""
def chip(p):
    if p is None: return ""
    c = "flat" if abs(p) < 0.5 else ("up" if p > 0 else "down")
    return f'<span class="chip mono {c}">{ {"up":"▲","down":"▼","flat":"■"}[c]} {p:+.1f}%</span>'

def build(v):
    key, card, icon, name, g, grades, unit, qty, qword = v
    c = col(g); now = nat(L, card, c)
    if now is None: print("skip", key, "(no price this week)"); return None
    prev_i = next((i for i in range(L - 1, -1, -1) if nat(i, card, c)), None)
    prev = nat(prev_i, card, c) if prev_i is not None else None
    pct = (now - prev) / prev * 100 if prev else None
    glbl = GRADE_LBL.get(g, g)
    slides = []
    # 1 hook
    slides.append(page(f"""<div class="emo">{icon}</div><div class="h1">{name} මිල අද</div><div class="gr">{glbl} · {unit}</div>
<div class="price mono">රු. {rs(now)}</div><div>{chip(pct)}<span class="note" style="margin-left:24px">පෙර වාර්තාවට සාපේක්ෂව</span></div>
<div><span class="date mono">DEA වාර්තාව · {DATE_SI}</span></div>
<div class="note" style="margin-top:20px">දත්ත අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුවෙන් (DEA)</div>"""))
    # 2 grades (or average vs highest for single-product cards)
    rows = []
    for gg in grades:
        a = nat(L, card, col(gg))
        if a: rows.append((GRADE_LBL.get(gg, gg), a, gg == g))
    if len(rows) >= 2:
        body = "".join(f'<div class="row{" pick" if m else ""}"><div class="n mono">{n}</div><div class="v mono">රු. {rs(a)}</div></div>' for n, a, m in rows)
        slides.append(page(f'<div class="lbl">🏷️ ශ්‍රේණි අනුව මිල</div>{body}<div class="note">ජාතික සාමාන්‍ය · {unit}</div>'))
    else:
        hi = nat(L, card, hcol(g))
        body = (f'<div class="row pick"><div class="n">සාමාන්‍ය මිල</div><div class="v mono">රු. {rs(now)}</div></div>'
                + (f'<div class="row"><div class="n">ඉහළම මිල</div><div class="v mono">රු. {rs(hi)}</div></div>' if hi else ""))
        slides.append(page(f'<div class="lbl">🏷️ {name} — ජාතික මිල</div>{body}<div class="note">{unit} · {DATE_SI}</div>'))
    # 3 districts
    dd = {k: x.get(c) for k, x in W[L]["commodities"][card]["districts"].items() if k != "National" and isinstance(x.get(c), (int, float)) and x.get(c) > 0}
    best_d = None
    if len(dd) >= 2:
        order = sorted(dd.items(), key=lambda kv: -kv[1]); best_d = order[0]
        show = order[:3] + ([order[-1]] if len(order) > 3 else [])
        body = "".join(f'<div class="row{" best" if i == 0 else (" low" if kv == order[-1] else "")}"><div class="n">{DIST.get(kv[0], kv[0])}{" ✅" if i == 0 else ""}</div><div class="v mono">රු. {rs(kv[1])}</div></div>' for i, kv in enumerate(show))
        slides.append(page(f'<div class="lbl">📍 දිස්ත්‍රික්ක අනුව — ඉහළම සහ අඩුම</div>{body}<div class="note">{glbl} · සාමාන්‍ය මිල · {unit}</div>'))
    # 4 vs same week last year
    tgt = NOW - timedelta(days=364)
    ly = min(range(L), key=lambda i: abs((dates[i] - tgt).days))
    lyv = nat(ly, card, c) if abs((dates[ly] - tgt).days) <= 10 else None
    if lyv:
        yp = (now - lyv) / lyv * 100
        slides.append(page(f"""<div class="lbl">📅 ගිය අවුරුද්දේ මේ කාලයට සාපේක්ෂව</div>
<div class="cmp"><div class="box"><div class="y mono">{dates[ly].year}</div><div class="p mono">{rs(lyv)}</div><div class="note" style="margin-top:10px">{si_date(dates[ly], False)}</div></div>
<div class="box now"><div class="y mono">{NOW.year}</div><div class="p mono">{rs(now)}</div><div class="note" style="margin-top:10px">{si_date(NOW, False)}</div></div></div>
<div class="big mono" style="color:{'#b23a2e' if yp > 0 else '#2c7a52'}">{'▲' if yp > 0 else '▼'} {yp:+.0f}%</div>
<div class="note" style="text-align:center">{glbl} · ජාතික සාමාන්‍ය · {unit}</div>"""))
    # 5 range since 2023
    hist = [(dates[i], nat(i, card, c)) for i in range(L + 1) if nat(i, card, c)]
    lo, hi = min(hist, key=lambda x: x[1]), max(hist, key=lambda x: x[1])
    pos = 50 if hi[1] == lo[1] else max(4, min(96, (now - lo[1]) / (hi[1] - lo[1]) * 100))
    slides.append(page(f"""<div class="lbl">📊 {hist[0][0].year} සිට මිල පරාසය</div>
<div class="bar"><div class="tag mono" style="left:{pos:.0f}%">අද {rs(now)}</div><div class="dot" style="left:{pos:.0f}%"></div></div>
<div class="ends"><div>අඩුම<br><span class="mono">රු. {rs(lo[1])}</span><br><span class="s">{si_date(lo[0])}</span></div>
<div style="text-align:right">ඉහළම<br><span class="mono">රු. {rs(hi[1])}</span><br><span class="s">{si_date(hi[0])}</span></div></div>
<div class="note">{glbl} · ජාතික සාමාන්‍ය · {unit}</div>"""))
    # 6 worked example (best district vs national)
    ex_title = f"{name} කොළ {qty*1000:,}" if qword == "LEAVES" else f"{name} {qty} {qword}"
    ex_f = (lambda p: f"{qty} × රු.{rs(p)} (කොළ 1000)") if qword == "LEAVES" else (lambda p: f"{qty} {qword} × රු.{rs(p)}")
    ex_rows = ([(f"{DIST.get(best_d[0], best_d[0])} ✅", best_d[1], True)] if best_d else []) + [("ජාතික සාමාන්‍යය", now, False)]
    body = "".join(f'<div class="ex{" best" if b else ""}"><div><div class="n">{n}</div><div class="f mono">{ex_f(p)}</div></div><div class="v mono">රු.{qty*p:,.0f}</div></div>' for n, p, b in ex_rows)
    slides.append(page(f"""<div class="lbl">🧮 උදාහරණය: {ex_title}</div>{body}
<div class="warn">⚠️ ප්‍රවාහන වියදම, තෙතමනය සහ ගුණාත්මකභාවය අනුව සැබෑ මිල වෙනස් වේ</div>
<div class="note">{glbl} · DEA ගොවිපළ දොරටු මිල · {DATE_SI}</div>"""))
    # 7 automatic insight
    rng = hi[1] - lo[1]
    last12 = [x for _, x in hist[-13:]]
    rec4 = [nat(i, card, c) for i in range(max(0, L - 4), L + 1)]
    rec4 = [x for x in rec4 if x]
    if rng and now >= hi[1] - 0.05 * rng:
        ins, sub = f"{hist[0][0].year} සිට ඉහළම මට්ටමට ආසන්නයි 📈", f"ඉහළම රු. {rs(hi[1])} ({si_date(hi[0])})"
    elif rng and now <= lo[1] + 0.05 * rng:
        ins, sub = f"{hist[0][0].year} සිට අඩුම මට්ටමට ආසන්නයි 📉", f"අඩුම රු. {rs(lo[1])} ({si_date(lo[0])})"
    elif now >= max(last12):
        ins, sub = "මාස 3ක ඉහළම මිල 📈", f"පසුගිය සති 12 තුළ ඉහළම: රු. {rs(now)}"
    elif now <= min(last12):
        ins, sub = "මාස 3ක අඩුම මිල 📉", f"පසුගිය සති 12 තුළ අඩුම: රු. {rs(now)}"
    elif len(rec4) >= 4 and all(b > a for a, b in zip(rec4, rec4[1:])):
        ins, sub = "සති කිහිපයක් පුරා ඉහළ යමින් 📈", f"{' → '.join(rs(x) for x in rec4)}"
    elif len(rec4) >= 4 and all(b < a for a, b in zip(rec4, rec4[1:])):
        ins, sub = "සති කිහිපයක් පුරා පහළ යමින් 📉", f"{' → '.join(rs(x) for x in rec4)}"
    else:
        p4 = (now - rec4[0]) / rec4[0] * 100 if rec4 and rec4[0] else 0
        ins, sub = ("මිල ස්ථාවරයි ⚖️" if abs(p4) < 3 else ("මාසයක් තුළ ඉහළ ගොස් ඇත 📈" if p4 > 0 else "මාසයක් තුළ පහළ ගොස් ඇත 📉")), f"සති 4කට පෙර සිට: {p4:+.1f}%"
    slides.append(page(f'<div class="lbl">💡 මේ සතියේ නිරීක්ෂණය</div><div class="ins">{ins}<div class="s">{sub}<br>{glbl} · {unit}</div></div>'))
    # 8 CTA
    slides.append(page(f"""<div class="emo">{icon}</div><div class="h1" style="font-size:86px">{name} — දිස්ත්‍රික්ක 14ක<br>සම්පූර්ණ මිල</div>
<div class="url">👉 topgoviya.lk/<br>spice-price-guide.html</div>
<div class="note">නොමිලේ · සිංහල · தமிழ் · English<br>මිල ගණන් මඟපෙන්වීමක් පමණි.<br>ඔබේ තීරණ ඔබේ වගකීම වේ.</div>"""))

    # render
    pngs = []
    for i, html in enumerate(slides):
        PG.set_content(html); PG.wait_for_timeout(150)
        f = f"{OUT}/_{key}{i:02d}.png"; PG.screenshot(path=f); pngs.append(f)
    n = len(pngs); inputs = []
    for f in pngs: inputs += ["-loop", "1", "-t", str(SLIDE_SEC), "-i", f]
    chain, last_lbl, off = [], "[0:v]", 0.0
    for i in range(1, n):
        off += SLIDE_SEC - FADE
        chain.append(f"{last_lbl}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[v{i}]"); last_lbl = f"[v{i}]"
    chain.append(f"{last_lbl}format=yuv420p,fps=30[outv]")
    num = f"{[x[0] for x in VIDEOS].index(key)+1:02d}"
    mp4 = f"{OUT}/{num}-{key}-{TAG}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                    "-map", "[outv]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", mp4], check=True)
    for f in pngs: os.remove(f)
    # text
    title = f"{name} මිල අද {NOW.year} | {glbl} රු. {rs(now)} | DEA {si_date(NOW, False)} #shorts"
    lines = [f"{icon} {name} ({glbl}): රු. {rs(now)} {unit}" + (f" ({pct:+.1f}% පෙර වාර්තාවට)" if pct is not None else "")]
    if len(rows) >= 2: lines += [f"   {n}: රු. {rs(a)}" for n, a, _ in rows if not _]
    if best_d: lines.append(f"📍 ඉහළම දිස්ත්‍රික්කය: {DIST.get(best_d[0], best_d[0])} — රු. {rs(best_d[1])}")
    if lyv: lines.append(f"📅 ගිය අවුරුද්දේ මේ කාලයේ: රු. {rs(lyv)} ({(now-lyv)/lyv*100:+.0f}%)")
    lines.append(f"📊 {hist[0][0].year} සිට: අඩුම රු. {rs(lo[1])} · ඉහළම රු. {rs(hi[1])}")
    lines.append(f"💡 {ins}")
    desc = (f"{name} ගොවිපළ දොරටු මිල — DEA වාර්තාව {DATE_SI}\n\n" + "\n".join(lines) +
            "\n\n👉 දිස්ත්‍රික්ක 14ක සම්පූර්ණ මිල: https://topgoviya.lk/spice-price-guide.html\n"
            "📊 මූලාශ්‍රය: අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුව (DEA)\n"
            "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
            f"#{name.replace(' ', '')}මිල #කුළුබඩුමිල #TopGoviyaLK #SriLanka #shorts")
    open(f"{OUT}/{num}-{key}-{TAG}.txt", "w", encoding="utf-8").write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n")
    print("Video:", mp4, f"({n} slides, ~{n*SLIDE_SEC-(n-1)*FADE:.0f}s)")
    return mp4

only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
with sync_playwright() as _pw:
    _b = _pw.chromium.launch(); PG = _b.new_page(viewport={"width": 1080, "height": 1920})
    for v in VIDEOS:
        if only is None or v[0] in only:
            try:
                build(v)
            except Exception as e:  # one bad spice must not stop the others
                print("ERROR", v[0], e)
    _b.close()
