"""
TopGoviya.lk — DAILY Dambulla DEC price YouTube Short
------------------------------------------------------
Usage: python3 make_dambulla_short.py [--check] [--force]
  --check   prints need=yes / need=no (is there a new day without a video yet?)
  --force   make the video even if this day was already done

Data: dambulla_dec.json (robot, from the DEC website) + dambulla_early.json (early entry
from the official price list photo) - the newest day is used. Names: dambulla_items.json.
Output: short/03-dambulla-DATE/ with video-with-music.mp4, video-silent.mp4,
        youtube.txt, tiktok.txt, facebook.txt   (same style as the other Shorts robots)
Each day's video is different: real movers of the day + a category spotlight that
changes with the weekday (so YouTube does not see look-alike videos).
"""
import json, base64, os, subprocess, sys
from datetime import date
from playwright.sync_api import sync_playwright
import short_kit

OUT = "short"; SLIDE_SEC = 4.0; FADE = 0.5
STATE = ".dambulla_short_last"
LOGO = "icon-512x512.png"
SI_MONTHS = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි", "අගෝස්තු",
             "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]
DAYS_SI = ["සඳුදා", "අඟහරුවාදා", "බදාදා", "බ්‍රහස්පතින්දා", "සිකුරාදා", "සෙනසුරාදා", "ඉරිදා"]
# weekday spotlight (Mon..Sun): category key, title
SPOT = [("l", "🌿 අද පලා වර්ග මිල"), ("r", "🥔 අද අල වර්ග මිල"), ("f", "🍌 අද පලතුරු මිල"),
        ("g", "🌾 අද ධාන්‍ය මිල"), ("v2", "🥒 තවත් එළවළු මිල"), ("f", "🍍 සති අන්ත පලතුරු මිල"),
        ("l", "🌿 පලා වර්ග සහ කොළ")]
STAPLES = ["11", "70", "67", "26", "4", "6"]          # tomato, big onion (imp), green chilli, brinjal, beans, carrot


def load():
    db = json.load(open("dambulla_dec.json", encoding="utf-8"))
    days = db.get("days", {})
    if os.path.exists("dambulla_early.json"):
        try:
            e = json.load(open("dambulla_early.json", encoding="utf-8"))
            if e.get("date") and e.get("prices") and e["date"] not in days and (not days or e["date"] > max(days)):
                days[e["date"]] = e["prices"]
        except Exception as ex:
            print("Early file ignored:", ex)
    names = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    return days, names


def done_before(day):
    return os.path.exists(STATE) and open(STATE).read().strip() == day


def si_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {SI_MONTHS[d.month - 1]} {d.year}"


def rs(v): return f"{v:,.0f}"


def main():
    days, names = load()
    if not days:
        print("need=no" if "--check" in sys.argv else "No data."); return
    order = sorted(days)
    last = order[-1]
    prev = order[-2] if len(order) > 1 else None
    if "--check" in sys.argv:
        print("need=" + ("no" if done_before(last) else "yes")); return
    if done_before(last) and "--force" not in sys.argv:
        print("Video for", last, "already made."); return

    items = []
    for pid, v in days[last].items():
        m = names.get(pid)
        if not m or not v:
            continue
        mid = (v[0] + v[1]) / 2
        chg = None
        if prev and days[prev].get(pid):
            p = days[prev][pid]; pm = (p[0] + p[1]) / 2
            chg = (mid - pm) / pm * 100 if pm else None
        items.append(dict(pid=pid, si=m["si"], e=m["e"], cat=m["cat"], pop=m["pop"], pop_cat=m["pop_cat"],
                          kg=(m["unit"] == "kg"), lo=v[0], hi=v[1], mid=mid, chg=chg))
    if len(items) < 10:
        print("Too few items for", last); return
    by = {i["pid"]: i for i in items}
    moved = [i for i in items if i["chg"] is not None]
    rises = sorted([i for i in moved if i["chg"] >= 0.5], key=lambda i: -i["chg"])[:3]
    falls = sorted([i for i in moved if i["chg"] <= -0.5], key=lambda i: i["chg"])[:3]
    up, dn = sum(i["chg"] >= 0.5 for i in moved), sum(i["chg"] <= -0.5 for i in moved)
    same = len(moved) - up - dn
    avg = sum(max(-100, min(100, i["chg"])) for i in moved) / len(moved) if moved else 0
    mood = "🔴 අද මිල වැඩි දිනයක්" if avg >= 3 else "🟢 අද මිල අඩු දිනයක්" if avg <= -3 else "🟡 අද සාමාන්‍ය දිනයක්"
    wd = date.fromisoformat(last).weekday()
    spot_cat, spot_title = SPOT[wd]
    if spot_cat == "v2":   # vegetables ranked 7-12 by popularity
        spot = sorted([i for i in items if i["cat"] == "v" and i["pid"] not in STAPLES], key=lambda i: i["pop"])[:6]
    else:
        spot = sorted([i for i in items if i["cat"] == spot_cat], key=lambda i: i["pop_cat"])[:6]
    staples = [by[p] for p in STAPLES if p in by]
    D = si_date(last); TAG = last
    logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode() if os.path.exists(LOGO) else ""

    css = """
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#f4efe4;font-family:'Noto Sans Sinhala',sans-serif;color:#191d1a;display:flex;flex-direction:column;overflow:hidden}
.top{background:#0e4f4a;color:#fff;padding:70px 70px 60px;display:flex;align-items:center;gap:34px}
.top img{width:150px;height:150px;border-radius:50%;border:5px solid #a9802a;background:#f4efe4}
.top .b{font-size:52px;font-weight:800}.top .s{font-size:34px;color:#e7d3a3;margin-top:6px}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 64px}
.foot{background:#0b0b0b;color:#e7d3a3;text-align:center;padding:40px;font-size:32px;font-weight:600}
.mono{font-family:'JetBrains Mono',monospace}
.big{font-size:118px;font-weight:800;line-height:1.12;color:#0e4f4a}
.date{display:inline-block;margin-top:44px;font-size:48px;font-weight:700;background:#0e4f4a;color:#fff;border-radius:999px;padding:18px 44px}
.note{font-size:38px;color:#7a7264;margin-top:44px;line-height:1.6}
.lbl{font-size:66px;font-weight:800;margin-bottom:38px}
.mood{font-size:62px;font-weight:800;margin-top:60px}
.bar{display:flex;height:44px;border-radius:22px;overflow:hidden;margin-top:28px}
.bar span{display:block;height:100%}
.leg{display:flex;gap:34px;font-size:38px;color:#3a403a;margin-top:18px}
.row{display:flex;align-items:center;gap:24px;background:#fffdf7;border:4px solid #e3d9c4;border-radius:30px;padding:34px 40px;margin-bottom:26px}
.row .nm{font-size:58px;font-weight:800;line-height:1.2}
.row .pr{font-size:42px;color:#3a403a;margin-top:8px}
.chip{font-weight:800;padding:12px 24px;border-radius:20px;font-size:48px;white-space:nowrap}
.up{background:#f7e6e2;color:#b23a2e}.down{background:#e3efe6;color:#2c7a52}.flat{background:#efeada;color:#8a8170}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.cell{background:#fffdf7;border:4px solid #e3d9c4;border-radius:28px;padding:30px 30px}
.cell .n{font-size:46px;font-weight:800;color:#0e4f4a;line-height:1.2;min-height:112px}
.cell .p{font-size:52px;font-weight:800;margin:8px 0}
.cell .c{font-size:36px;font-weight:800}
.cu{color:#b23a2e}.cd{color:#2c7a52}.cf{color:#8a8170}
.url{font-size:92px;font-weight:800;color:#0e4f4a;margin-top:30px}
""" + short_kit.CTA_CSS

    def page(inner):
        return f"""<html><head><meta charset="utf-8"><style>{css}</style></head><body>
<div class="top">{f'<img src="{logo}">' if logo else ''}<div><div class="b">TopGoviya.lk</div><div class="s">අද දඹුල්ල තොග මිල · {DAYS_SI[wd]}</div></div></div>
<div class="main">{inner}</div>
<div class="foot">මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · තොග මිල · {D}</div></body></html>"""

    def chip(c):
        if c is None: return ""
        k = "flat" if abs(c) < 0.5 else ("up" if c > 0 else "down")
        return f'<span class="chip mono {k}">{ {"up":"▲","down":"▼","flat":"■"}[k]} {abs(c):.0f}%</span>'

    def unit(i): return "" if i["kg"] else "*"

    def rows(lst):
        out = ""
        for i in lst:
            out += (f'<div class="row"><div style="flex:1"><div class="nm">{i["e"]} {i["si"]}</div>'
                    f'<div class="pr mono">රු. {rs(i["lo"])} – {rs(i["hi"])}{unit(i)}</div></div>{chip(i["chg"])}</div>')
        return out

    def cells(lst):
        out = ""
        for i in lst:
            c = i["chg"]; k = "cf" if c is None or abs(c) < 0.5 else ("cu" if c > 0 else "cd")
            a = "■" if k == "cf" else ("▲" if k == "cu" else "▼")
            out += (f'<div class="cell"><div class="n">{i["e"]} {i["si"]}</div><div class="p mono">{rs(i["lo"])}–{rs(i["hi"])}{unit(i)}</div>'
                    f'<div class="c mono {k}">{a} {"" if c is None else f"{abs(c):.0f}%"}</div></div>')
        return out

    tot = max(len(moved), 1)
    bar = (f'<div class="bar"><span style="width:{up/tot*100:.1f}%;background:#b23a2e"></span>'
           f'<span style="width:{same/tot*100:.1f}%;background:#cdbf9f"></span><span style="width:{dn/tot*100:.1f}%;background:#2c7a52"></span></div>'
           f'<div class="leg"><span>🔴 ඉහළ {up}</span><span>⚪ වෙනසක් නැත {same}</span><span>🟢 පහළ {dn}</span></div>')
    note = '<div class="note">රු. / කි.ග්‍රෑ. · අවම – උපරිම · ▲▼ පෙර දිනට සාපේක්ෂව</div>'
    slides = [page(f'<div class="big">අද දඹුල්ල<br>එළවළු<br><span style="color:#a9802a">තොග</span> මිල</div>'
                   f'<div><span class="date">{D}</span></div><div class="mood">{mood}</div>{bar}')]
    if rises: slides.append(page(f'<div class="lbl" style="color:#b23a2e">📈 අද වැඩිම ඉහළ යාම</div>{rows(rises)}{note}'))
    if falls: slides.append(page(f'<div class="lbl" style="color:#2c7a52">📉 අද වැඩිම පහළ යාම</div>{rows(falls)}{note}'))
    slides.append(page(f'<div class="lbl" style="color:#0e4f4a">🛒 ජනප්‍රිය එළවළු</div><div class="grid">{cells(staples)}</div>{note}'))
    if len(spot) >= 4:
        slides.append(page(f'<div class="lbl" style="color:#0e4f4a">{spot_title}</div><div class="grid">{cells(spot)}</div>{note}'))
    slides.append(page('<div class="big" style="font-size:94px">දඹුල්ල මිල<br>භාණ්ඩ 90+</div>'
                       '<div class="url">👉 topgoviya.lk</div>'
                       '<div class="note">🛒 බාස්කට් එක · 🧮 ලාභ ගණකය · ⭐ මගේ භාණ්ඩ<br>සිංහල · தமிழ் · English · නොමිලේ<br>'
                       'මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.</div>'
                       + short_kit.cta("ඔබේ ප්‍රදේශයේ මිල කමෙන්ට් කරන්න", "ගොවි හා වෙළෙන්දා මිතුරන්ට ෂෙයාර් කරන්න",
                                       "සෑම දිනකම දඹුල්ල මිල සඳහා ෆලෝ කරන්න")))

    os.makedirs(OUT, exist_ok=True)
    pngs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for n, html in enumerate(slides):
            pg.set_content(html); pg.wait_for_timeout(300)
            f = f"{OUT}/dambulla{n:02d}.png"; pg.screenshot(path=f); pngs.append(f)
        b.close()
    n = len(pngs); inputs = []
    for f in pngs: inputs += ["-loop", "1", "-t", str(SLIDE_SEC), "-i", f]
    chain, lbl, off = [], "[0:v]", 0.0
    for k in range(1, n):
        off += SLIDE_SEC - FADE
        chain.append(f"{lbl}[{k}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[v{k}]"); lbl = f"[v{k}]"
    chain.append(f"{lbl}format=yuv420p,fps=30[outv]")
    silent = f"{OUT}/dambulla-{TAG}-silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                    "-map", "[outv]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", silent], check=True)
    seconds = n * SLIDE_SEC - (n - 1) * FADE

    mv = lambda i, a: f"{a} {i['si']}: රු. {rs(i['lo'])}–{rs(i['hi'])} ({'+' if i['chg']>0 else '−'}{abs(i['chg']):.0f}%)"
    title = f"අද දඹුල්ල එළවළු මිල {D} | Dambulla Market Price Today | තොග මිල #shorts"
    desc = (f"🥬 අද දඹුල්ල එළවළු තොග මිල — {D} ({DAYS_SI[wd]})\n{mood.split(' ',1)[1]}: භාණ්ඩ {up}ක් ඉහළ, {dn}ක් පහළ, {same}ක් වෙනසක් නැත.\n"
            + ("\nමිල ඉහළ ගිය:\n" + "\n".join(mv(i, "📈") for i in rises) + "\n" if rises else "")
            + ("\nමිල පහළ ගිය:\n" + "\n".join(mv(i, "📉") for i in falls) + "\n" if falls else "")
            + "\nජනප්‍රිය එළවළු (රු./කි.ග්‍රෑ., අවම – උපරිම):\n"
            + "\n".join(f"{i['e']} {i['si']}: රු. {rs(i['lo'])}–{rs(i['hi'])}" for i in staples) +
            "\n\n👉 දඹුල්ල භාණ්ඩ 90+ ක අද මිල, බාස්කට් එක හා ලාභ ගණකය: https://topgoviya.lk\n"
            "📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය\n"
            "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
            "#දඹුල්ල #එළවළුමිල #තොගමිල #DambullaPrice #TopGoviyaLK #SriLanka #shorts")
    moves = [mv(i, "📈") for i in rises[:2]] + [mv(i, "📉") for i in falls[:2]]
    tiktok = (f"අද දඹුල්ල එළවළු තොග මිල 🥬 {D}\n" + "\n".join(moves) +
              "\nසියලු මිල 👉 topgoviya.lk · දත්ත: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය\nමිල ගණන් මඟපෙන්වීමක් පමණි.\n\n"
              "#දඹුල්ල #එළවළුමිල #DambullaPrice #TopGoviyaLK #fyp")
    facebook = (f"🥬 අද දඹුල්ල එළවළු තොග මිල — {D}\n{mood}\n\n" + "\n".join(moves) +
                "\n\n👉 භාණ්ඩ 90+ ක මිල, 🛒 බාස්කට් එක, 🧮 ලාභ ගණකය: https://topgoviya.lk\n"
                "📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය\n⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
                "#දඹුල්ල #එළවළුමිල #TopGoviyaLK")
    tags = ["දඹුල්ල එළවළු මිල", "අද දඹුල්ල එළවළු මිල", "දබුල්ල එලවලු මිල", "dambulla market price today",
            "dambulla vegetable price", "dambulla price today", "එළවළු මිල", "අද එළවළු මිල", "තොග මිල",
            "elawalu mila", "elawalu mila ada", "vegetable price sri lanka", f"එළවළු මිල {date.fromisoformat(last).year}", "TopGoviya"]
    track = short_kit.pick_track("music-5.wav", "music-2.wav", "music-1.wav")
    short_kit.package(f"{OUT}/03-dambulla-{TAG}", silent, track, seconds, title, desc, tiktok, facebook,
                      tags, "🥬 අද දඹුල්ල එළවළු මිල | Dambulla Market Price Daily")
    for f in pngs + [silent]:
        if os.path.exists(f): os.remove(f)
    open(STATE, "w").write(last)
    print(f"Video for {last}: {n} slides, ~{seconds:.0f}s")


if __name__ == "__main__":
    main()
