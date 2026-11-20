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
Design (Nov 2026): "price board first" - second 0 shows a huge date + the 14 most-wanted prices
with red/green/grey up-down dots (rows slide in one by one, dots pop); then the next 14 items, the day's biggest movers, and the end card.
Rows come in one at a time (ITEM_SEC each) so people can read them: about 35-40 seconds. Each day's video differs because the prices differ.
"""
import json, base64, os, subprocess, sys
from datetime import date
import short_kit

OUT = "short"; FADE = 0.3; FPS = 30
ITEM_SEC = 0.9      # time for each row: slide in + highlight, so people can read it (change to slow down/speed up)
HOLD_SEC = 2.0      # full board stays on screen after the last row
MOVER_SEC = 0.7     # each "biggest change" card
END_SEC = 3.5       # last card (topgoviya.lk)
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


def stamp(day, prices):
    """Day + short fingerprint of that day's prices, e.g. 2026-10-26_3fa2c1d0.
    If the prices are corrected later, the fingerprint changes and a new video is made."""
    import hashlib
    fp = hashlib.sha1(json.dumps(prices, sort_keys=True).encode()).hexdigest()[:8]
    return f"{day}_{fp}"


def done_before(st):
    return os.path.exists(STATE) and open(STATE).read().strip() == st


def si_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {SI_MONTHS[d.month - 1]} {d.year}"


def rs(v): return f"{v:,.0f}"



def pin_comment(rises, falls, last):
    """Comment to post and pin under the YouTube video: subscribe ask + site link + a question."""
    d = date.fromisoformat(last)
    q = ""
    if rises:
        q = f"\n💬 අද {rises[0]['si']} මිල ඉහළ ගියා. ඔබේ ප්‍රදේශයේ {rises[0]['si']} කීයද? කමෙන්ට් කරන්න 👇"
    elif falls:
        q = f"\n💬 අද {falls[0]['si']} මිල පහළ ගියා. ඔබේ ප්‍රදේශයේ කීයද? කමෙන්ට් කරන්න 👇"
    return ("📌 සෑම දිනකම දඹුල්ල එලවලු මිල සඳහා Subscribe කරන්න 🔔\n"
            "👉 භාණ්ඩ 90+ ක අද මිල, 🛒 බාස්කට් එක හා 🧮 ලාභ ගණකය: https://topgoviya.lk/?d=" + last + q +
            "\n📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · " + f"{d.year}.{d.month:02d}.{d.day:02d}")

def main():
    days, names = load()
    if not days:
        print("need=no" if "--check" in sys.argv else "No data."); return
    order = sorted(days)
    last = order[-1]
    prev = order[-2] if len(order) > 1 else None
    st = stamp(last, days[last])
    if "--check" in sys.argv:
        print("need=" + ("no" if done_before(st) else "yes")); return
    if done_before(st) and "--force" not in sys.argv:
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
                          kg=(m["unit"] == "kg"), unit=m["unit"], lo=v[0], hi=v[1], mid=mid, chg=chg))
    if len(items) < 10:
        print("Too few items for", last); return
    by = {i["pid"]: i for i in items}
    moved = [i for i in items if i["chg"] is not None]
    rises = sorted([i for i in moved if i["chg"] >= 0.5], key=lambda i: -i["chg"])[:3]
    falls = sorted([i for i in moved if i["chg"] <= -0.5], key=lambda i: i["chg"])[:3]
    up, dn = sum(i["chg"] >= 0.5 for i in moved), sum(i["chg"] <= -0.5 for i in moved)
    same = len(moved) - up - dn
    nonew = len(items) - len(moved)          # no previous price to compare
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
body{width:1080px;height:1920px;background:#063027;font-family:'Noto Sans Sinhala',sans-serif;color:#faf6ec;display:flex;flex-direction:column;overflow:hidden}
.mono{font-family:'JetBrains Mono',monospace}
.hd{background:#0b4a3c;padding:34px 60px 36px;text-align:center}
.hd .t{font-size:58px;font-weight:800;line-height:1.3}
.dbox{margin-top:20px;background:#ffd43b;color:#063027;border-radius:28px;padding:10px 20px 18px}
.dbox .d{font-size:118px;font-weight:800;line-height:1.1;letter-spacing:-2px}
.dbox .w{font-size:44px;font-weight:800}
.hd.sm .dbox .d{font-size:84px}.hd.sm .t{font-size:50px}
.rows{flex:1;display:flex;flex-direction:column}
.r{display:flex;align-items:center;padding:0 40px;height:86px;margin-bottom:4px}
.r:nth-child(odd){background:#0f5c4a}.r:nth-child(even){background:#0a4235}
.r .n{flex:1;font-size:52px;font-weight:800;white-space:nowrap;overflow:hidden}
.r .n small{font-size:30px;font-weight:600;color:#bed7c8;margin-left:10px}
.r .p{font-size:62px;font-weight:800;color:#fff;margin-right:26px;white-space:nowrap}
.dot{width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:34px;font-weight:800;flex:none}
.u{background:#e23d34}.dn{background:#22a05a}.f{background:#96968c}
.leg{display:flex;gap:44px;padding:16px 40px;font-size:36px;font-weight:600;align-items:center}
.leg i{display:inline-block;width:34px;height:34px;border-radius:50%;margin-right:12px;vertical-align:middle}
.ft{background:#0b4a3c;display:flex;align-items:center;gap:24px;padding:26px 60px}
.ft img{width:100px;height:100px;border-radius:18px}
.ft .s{font-size:66px;font-weight:800;color:#ffd43b;font-family:'JetBrains Mono',monospace}
.ft .x{margin-left:auto;font-size:34px;font-weight:700;text-align:right;line-height:1.35}
.mv{flex:1;padding:40px 50px;display:flex;flex-direction:column;justify-content:center}
.mv .lbl{font-size:62px;font-weight:800;margin:10px 0 22px}
.card{display:flex;align-items:center;border-radius:28px;padding:24px 34px;margin-bottom:20px;background:#0f5c4a}
.card .n{flex:1;font-size:54px;font-weight:800;line-height:1.25}
.card .p{font-size:40px;color:#e6efe9;margin-top:4px}
.card .c{font-size:56px;font-weight:800;padding:10px 24px;border-radius:20px;color:#fff;white-space:nowrap}
.end{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 60px;text-align:center}
.end .big{font-size:80px;font-weight:800;line-height:1.35}
.end .url{font-size:100px;font-weight:800;color:#ffd43b;margin:30px 0}
.end .note{font-size:38px;color:#d7e6dc;line-height:1.6}
.cta{margin-top:40px;background:#0f5c4a;border-radius:26px;padding:6px 30px;text-align:left}
.ct{display:flex;align-items:center;gap:22px;padding:16px 0;font-size:40px;font-weight:700}
.ct+.ct{border-top:2px solid #0a4235}.ci{font-size:48px;width:64px;text-align:center}
@keyframes slideIn{0%{transform:translateX(105%);opacity:0}70%{transform:translateX(-3%);opacity:1}100%{transform:none;opacity:1}}
@keyframes pop{0%{transform:scale(0)}70%{transform:scale(1.3)}100%{transform:scale(1)}}
@keyframes drop{0%{transform:translateY(-60px);opacity:0}100%{transform:none;opacity:1}}
@keyframes glow{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
@keyframes hl{0%,100%{background:inherit;transform:none}15%,85%{background:#1f8a6c;transform:scale(1.035);box-shadow:0 0 0 5px #ffd43b inset}}
.r,.card{animation:slideIn .4s ease-out both}
.r{position:relative}
.dot,.card .c{animation:pop .3s ease-out both}
.dbox{animation:glow 1.6s ease-in-out .6s infinite}
.mv .lbl,.end>*{animation:drop .35s ease-out both}
"""
    dotdate = f"{date.fromisoformat(last):%Y.%m.%d}"

    def head(small=False):
        return (f'<div class="hd{" sm" if small else ""}"><div class="t">අද දඹුල්ල එළවළු තොග මිල</div>'
                f'<div class="dbox"><div class="d mono">{dotdate}</div><div class="w">{DAYS_SI[wd]} • 1kg රු.</div></div></div>')

    img_tag = '<img src="' + logo + '">' if logo else ""
    foot = (f'<div class="ft">{img_tag}<div class="s">TopGoviya.lk</div>'
            '<div class="x">සම්පූර්ණ ලැයිස්තුව<br>🔔 Subscribe</div></div>')

    def page(inner, small=False, header=True):
        return (f'<html><head><meta charset="utf-8"><style>{css}</style></head><body>'
                f'{head(small) if header else ""}{inner}{foot}</body></html>')

    def unit(i): return "" if i["kg"] else {"nut": " /ගෙඩිය", "bundle": " /මිටිය"}.get(i["unit"], "")

    def name(i):
        n, _, o = i["si"].partition(" (")
        return f'{n}<small>({o}</small>' if o else n

    def dot(c):
        if c is None or abs(c) < 0.5: return '<span class="dot f">●</span>'
        return '<span class="dot u">▲</span>' if c > 0 else '<span class="dot dn">▼</span>'

    def price(i):
        return rs(i["lo"]) if i["lo"] == i["hi"] else f"{rs(i['lo'])}-{rs(i['hi'])}"

    def board(lst):
        return ('<div class="rows">' + "".join(
            f'<div class="r" style="animation:slideIn .4s ease-out {k * ITEM_SEC:.2f}s both,hl {ITEM_SEC:.2f}s ease-in-out {k * ITEM_SEC + 0.35:.2f}s"><div class="n">{name(i)}</div><div class="p mono">{price(i)}<span style="font-size:32px">{unit(i)}</span></div>'
            + dot(i["chg"]).replace('<span class="dot', f'<span style="animation-delay:{k * ITEM_SEC + 0.35:.2f}s" class="dot') + '</div>'
            for k, i in enumerate(lst)) + '</div>'
            '<div class="leg"><span><i class="u"></i>ඉහළ</span><span><i class="dn"></i>පහළ</span><span><i class="f"></i>වෙනසක් නැත</span></div>')

    def cards(lst, cls):
        return "".join(f'<div class="card" style="animation-delay:{0.4 + k * MOVER_SEC:.2f}s"><div style="flex:1"><div class="n">{i["e"]} {name(i)}</div>'
                       f'<div class="p mono">රු. {price(i)}{unit(i)}</div></div>'
                       f'<div class="c mono {cls}" style="animation-delay:{0.7 + k * MOVER_SEC:.2f}s">{"▲" if cls == "u" else "▼"} {abs(i["chg"]):.0f}%</div></div>'
                       for k, i in enumerate(lst))

    ranked = sorted(items, key=lambda i: i["pop"])
    bsec = lambda n: n * ITEM_SEC + HOLD_SEC
    b1 = ranked[:14]
    slides = [page(board(b1))]; durs = [bsec(len(b1))]       # second 0: the prices, nothing else
    if len(ranked) > 14:
        b2 = ranked[14:28]
        slides.append(page(board(b2), small=True)); durs.append(bsec(len(b2)))
    if rises or falls:
        mv_html = '<div class="mv">'
        if rises: mv_html += f'<div class="lbl" style="color:#ff8a80">📈 අද වැඩිම ඉහළ යාම</div>{cards(rises[:3], "u")}'
        if falls: mv_html += f'<div class="lbl" style="color:#7fe0a6">📉 අද වැඩිම පහළ යාම</div>{cards(falls[:3], "dn")}'
        slides.append(page(mv_html + '</div>', small=True))
        durs.append(0.4 + (len(rises[:3]) + len(falls[:3])) * MOVER_SEC + HOLD_SEC)
    slides.append(page('<div class="end"><div class="big">දඹුල්ල භාණ්ඩ 90+ ක<br>අද මිල</div>'
                       '<div class="url mono">topgoviya.lk</div>'
                       '<div class="note">සිංහල · தமிழ் · English · නොමිලේ<br>මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.</div>'
                       '<div class="cta">'
                       '<div class="ct"><span class="ci">💬</span><span>ඔබේ ප්‍රදේශයේ මිල කමෙන්ට් කරන්න</span></div>'
                       '<div class="ct"><span class="ci">📤</span><span>ගොවි මිතුරන්ට ෂෙයාර් කරන්න</span></div>'
                       '<div class="ct"><span class="ci">🔔</span><span>හැමදාම මිල සඳහා Subscribe කරන්න</span></div>'
                       '</div></div>', small=True))
    durs.append(END_SEC)
    from playwright.sync_api import sync_playwright   # only needed when a video is made
    os.makedirs(OUT, exist_ok=True)
    dirs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for n, html in enumerate(slides):
            pg.set_content(html); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            pg.evaluate("document.getAnimations().forEach(a => a.pause())")
            fd = f"{OUT}/frames{n:02d}"; os.makedirs(fd, exist_ok=True); dirs.append(fd)
            for f in range(int(durs[n] * FPS)):      # step the animation by hand: smooth 30 fps, same result every run
                pg.evaluate(f"document.getAnimations().forEach(a => a.currentTime = {f * 1000 / FPS:.1f})")
                pg.screenshot(path=f"{fd}/{f:04d}.jpg", type="jpeg", quality=92)
        b.close()
    n = len(dirs); inputs = []
    for fd in dirs: inputs += ["-framerate", str(FPS), "-i", f"{fd}/%04d.jpg"]
    chain, lbl, off = [], "[0:v]", 0.0
    for k in range(1, n):
        off += durs[k - 1] - FADE
        chain.append(f"{lbl}[{k}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[v{k}]"); lbl = f"[v{k}]"
    chain.append(f"{lbl}format=yuv420p,fps={FPS}[outv]")
    silent = f"{OUT}/dambulla-{TAG}-silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                    "-map", "[outv]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", silent], check=True)
    seconds = sum(durs) - (n - 1) * FADE

    mv = lambda i, a: f"{a} {i['si']}: රු. {rs(i['lo'])}–{rs(i['hi'])} ({'+' if i['chg']>0 else '−'}{abs(i['chg']):.0f}%)"
    title = f"අද {dotdate} {DAYS_SI[wd]} දඹුල්ල එලවලු මිල | Dambulla vegetable price today #shorts"
    if len(title) > 100:   # YouTube limit
        title = title.replace(" today", "")
    desc = (f"🥬 අද දඹුල්ල එළවළු තොග මිල (දඹුල්ල එලවලු මිල අද) — {D} ({DAYS_SI[wd]})\nදඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ නිල තොග මිල.\n{mood.split(' ',1)[1]}: භාණ්ඩ {up}ක් ඉහළ, {dn}ක් පහළ, {same}ක් වෙනසක් නැත" + (f", {nonew}ක පෙර මිල නැත" if nonew else "") + " (පෙර වාර්තාවට සාපේක්ෂව).\n"
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
    tags = ["දඹුල්ල එලවලු මිල අද", "දඹුල්ල ආර්ථික මධ්‍යස්ථානයේ එළවළු මිල", "දඹුල්ලේ එලවලු මිල", "එලවලු මිල අද",
            "දඹුල්ල එළවළු මිල", "අද දඹුල්ල එළවළු මිල", "දබුල්ල එලවලු මිල", "dambulla market price today",
            "dambulla vegetable price", "dambulla price today", "එළවළු මිල", "අද එළවළු මිල", "තොග මිල",
            "elawalu mila", "elawalu mila ada", "vegetable price sri lanka", f"එළවළු මිල {date.fromisoformat(last).year}", "TopGoviya"]
    track = short_kit.pick_track("music-5.wav", "music-2.wav", "music-1.wav")
    short_kit.package(f"{OUT}/03-dambulla-{TAG}", silent, track, seconds, title, desc, tiktok, facebook,
                      tags, "🥬 අද දඹුල්ල එළවළු මිල | Dambulla Market Price Daily")
    pin = pin_comment(rises, falls, last)
    folder = f"{OUT}/03-dambulla-{TAG}"
    open(f"{folder}/pin-comment.txt", "w", encoding="utf-8").write(pin + "\n")
    with open(f"{folder}/youtube.txt", "a", encoding="utf-8") as f:
        f.write("\nPINNED COMMENT (post it, then ⋮ → Pin):\n" + pin + "\n")
    import shutil
    for fd in dirs:
        shutil.rmtree(fd, ignore_errors=True)
    if os.path.exists(silent): os.remove(silent)
    open(STATE, "w").write(st)
    print(f"Video for {last}: {n} slides, ~{seconds:.0f}s")


if __name__ == "__main__":
    main()
