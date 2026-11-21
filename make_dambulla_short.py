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
with red/green/grey up-down dots (rows slide in one by one, dots pop); then the next 14 items, the day's biggest movers, the end card, and a 1.2 s thumbnail frame (also saved as thumbnail.png).
Rows come in one at a time (ITEM_SEC each) so people can read them: about 35-40 seconds. Each day's video differs because the prices differ.
Mobile safe area (20 Nov 2026): all text stays inside x 120-860, y 300-1440 so YouTube's top bar, side buttons,
caption and the side crop on tall phones never cover names or prices. Colours still fill the whole screen.
  --preview   save one picture per slide (short/preview-N.png) with the YouTube danger zones marked, no video
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
SHORT_TRACKS = ["short-1-the-new-me.mp3", "short-2-its-been-sold.mp3", "short-3-free-advice.mp3",
                "short-4-thats-the-way.mp3", "music-5.wav"]   # files in the music/ folder, used in turn (one per day)
STAPLES = ["11", "70", "67", "26", "4", "6"]          # tomato, big onion (imp), green chilli, brinjal, beans, carrot
# YouTube Shorts safe area (1080x1920 video). Text only inside it; background colour fills the rest.
SAFE_TOP, SAFE_BOTTOM = 300, 480    # top bar / channel name + caption
SAFE_LEFT, SAFE_RIGHT = 120, 220    # side crop on tall phones / like-comment-share buttons
ROWS_PER_BOARD = 7                  # 7 extra-big rows per screen (easy to read on cheap phones)
MAX_ITEMS = 21                      # 3 boards x 7 most popular items (full list is on topgoviya.lk)


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
.topband{height:SAFE_TOPpx;flex:none;background:#0b4a3c;display:flex;align-items:flex-end;justify-content:center;padding:0 SAFE_RIGHTpx 14px SAFE_LEFTpx;font-size:48px;font-weight:800;text-align:center}
.botband{height:SAFE_BOTTOMpx;flex:none;background:#0b4a3c;display:flex;align-items:flex-start;gap:24px;padding:40px SAFE_RIGHTpx 0 SAFE_LEFTpx;opacity:.55}
.botband img{width:90px;height:90px;border-radius:18px}
.botband .s{font-size:60px;font-weight:800;color:#ffd43b;font-family:'JetBrains Mono',monospace}
.mid{flex:1;display:flex;flex-direction:column;overflow:hidden}
.hd{background:#0b4a3c;padding:6px SAFE_RIGHTpx 14px SAFE_LEFTpx;text-align:center}
.hd .t{font-size:44px;font-weight:800;line-height:1.3}
.dbox{margin-top:8px;background:#ffd43b;color:#063027;border-radius:24px;padding:4px 16px 10px}
.dbox .d{font-size:112px;font-weight:800;line-height:1.1;letter-spacing:-2px}
.dbox .w{font-size:42px;font-weight:800}
.hd.sm .dbox .d{font-size:74px}.hd.sm .t{font-size:40px}.hd.sm .dbox .w{font-size:34px}
.rows{flex:1;display:flex;flex-direction:column;padding-top:10px}
.r{display:flex;align-items:center;padding:0 SAFE_RIGHTpx 0 SAFE_LEFTpx;height:110px;margin-bottom:5px}
.r:nth-child(odd){background:#0f5c4a}.r:nth-child(even){background:#0a4235}
.r .n{flex:1;min-width:0;font-size:58px;font-weight:800;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.r .n.lg{font-size:46px}
.r .n small{display:block;font-size:30px;font-weight:600;color:#bed7c8;line-height:1.1}
.r .p{font-size:66px;font-weight:800;color:#fff;margin:0 16px 0 12px;white-space:nowrap}
.dot{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:36px;font-weight:800;flex:none}
.u{background:#e23d34}.dn{background:#22a05a}.f{background:#96968c}
.leg{display:flex;gap:20px;padding:14px SAFE_RIGHTpx 14px SAFE_LEFTpx;font-size:32px;white-space:nowrap;font-weight:600;align-items:center;background:#0b4a3c}
.leg i{display:inline-block;width:28px;height:28px;border-radius:50%;margin-right:8px;vertical-align:middle}
.leg .s,.brand .s{margin-left:auto;font-size:36px;font-weight:800;color:#ffd43b;font-family:'JetBrains Mono',monospace}
.brand{display:flex;padding:12px SAFE_RIGHTpx 12px SAFE_LEFTpx;background:#0b4a3c;align-items:center;font-size:32px;font-weight:700}
.mv{flex:1;padding:8px SAFE_RIGHTpx 6px SAFE_LEFTpx;display:flex;flex-direction:column;justify-content:center}
.mv .lbl{font-size:48px;font-weight:800;margin:4px 0 8px}
.card{display:flex;align-items:center;border-radius:22px;padding:6px 20px;margin-bottom:8px;background:#0f5c4a}
.card .n{flex:1;font-size:46px;font-weight:800;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card .p{font-size:34px;color:#e6efe9;margin-top:0}
.card .c{font-size:48px;font-weight:800;padding:8px 18px;border-radius:18px;color:#fff;white-space:nowrap;margin-left:12px}
.end{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 SAFE_RIGHTpx 0 SAFE_LEFTpx;text-align:center}
.end .big{font-size:64px;font-weight:800;line-height:1.35}
.end .url{font-size:86px;font-weight:800;color:#ffd43b;margin:20px 0}
.end .note{font-size:32px;color:#d7e6dc;line-height:1.6}
.cta{margin-top:28px;background:#0f5c4a;border-radius:24px;padding:4px 24px;text-align:left}
.ct{display:flex;align-items:center;gap:18px;padding:12px 0;font-size:34px;font-weight:700}
.ct+.ct{border-top:2px solid #0a4235}.ci{font-size:42px;width:56px;text-align:center}
.th{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 SAFE_RIGHTpx 0 SAFE_LEFTpx;text-align:center}
.th .emo{font-size:100px;line-height:1.05}
.th .h{font-size:92px;font-weight:800;line-height:1.15;color:#fff}
.th .db{margin:14px 0 10px;background:#ffd43b;color:#063027;border-radius:26px;padding:4px 10px 10px}
.th .db .d{font-size:96px;font-weight:800;line-height:1.1;letter-spacing:-2px}
.th .db .w{font-size:36px;font-weight:800}
.th .o{display:flex;align-items:center;background:#0f5c4a;border-radius:18px;padding:4px 18px;margin-top:8px;font-size:46px;font-weight:800;text-align:left}
.th .o .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.th .o .v{margin:0 12px}
.th .o .dot{width:48px;height:48px;font-size:26px}
@keyframes slideIn{0%{transform:translateX(105%);opacity:0}70%{transform:translateX(-3%);opacity:1}100%{transform:none;opacity:1}}
@keyframes pop{0%{transform:scale(0)}70%{transform:scale(1.3)}100%{transform:scale(1)}}
@keyframes drop{0%{transform:translateY(-60px);opacity:0}100%{transform:none;opacity:1}}
@keyframes glow{0%,100%{transform:scale(1)}50%{transform:scale(1.02)}}
@keyframes hl{0%,100%{background:inherit;transform:none}15%,85%{background:#1f8a6c;transform:scale(1.02);box-shadow:0 0 0 5px #ffd43b inset}}
.r,.card{animation:slideIn .4s ease-out both}
.r{position:relative}
.dot,.card .c{animation:pop .3s ease-out both}
.dbox{animation:glow 1.6s ease-in-out .6s infinite}
.mv .lbl,.end>*{animation:drop .35s ease-out both}
""".replace("SAFE_TOP", str(SAFE_TOP)).replace("SAFE_BOTTOM", str(SAFE_BOTTOM)).replace("SAFE_LEFT", str(SAFE_LEFT)).replace("SAFE_RIGHT", str(SAFE_RIGHT))
    dotdate = f"{date.fromisoformat(last):%Y.%m.%d}"

    def head(small=False):
        return (f'<div class="hd{" sm" if small else ""}">'
                f'<div class="dbox"><div class="d mono">{dotdate}</div><div class="w">{DAYS_SI[wd]} • 1kg රු.</div></div></div>')

    img_tag = '<img src="' + logo + '">' if logo else ""
    # bottom band sits under YouTube's caption on phones (decoration only); the real brand line is inside the safe area
    foot = f'<div class="botband">{img_tag}<div class="s">TopGoviya.lk</div></div>'
    brand = '<div class="brand"><span>සම්පූර්ණ ලැයිස්තුව 👉</span><span class="s">TopGoviya.lk</span></div>'

    def page(inner, small=False, header=True):
        return (f'<html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="topband">අද දඹුල්ල එළවළු තොග මිල</div>'
                f'<div class="mid">{head(small) if header else ""}{inner}</div>{foot}</body></html>')

    def unit(i): return "" if i["kg"] else {"nut": " /ගෙඩිය", "bundle": " /මිටිය"}.get(i["unit"], "")

    def name(i):
        n, _, o = i["si"].partition(" (")
        return f'{n}<small>({o}</small>' if o else n   # row: label goes on its own small line under the name

    def dot(c):
        if c is None or abs(c) < 0.5: return '<span class="dot f">●</span>'
        return '<span class="dot u">▲</span>' if c > 0 else '<span class="dot dn">▼</span>'

    def price(i):
        return rs(i["lo"]) if i["lo"] == i["hi"] else f"{rs(i['lo'])}-{rs(i['hi'])}"

    def board(lst):
        return ('<div class="rows">' + "".join(
            f'<div class="r" style="animation:slideIn .4s ease-out {k * ITEM_SEC:.2f}s both,hl {ITEM_SEC:.2f}s ease-in-out {k * ITEM_SEC + 0.35:.2f}s"><div class="n{" lg" if len(i["si"].partition(" (")[0]) > 9 else ""}">{name(i)}</div><div class="p mono">{price(i)}<span style="font-size:32px">{unit(i)}</span></div>'
            + dot(i["chg"]).replace('<span class="dot', f'<span style="animation-delay:{k * ITEM_SEC + 0.35:.2f}s" class="dot') + '</div>'
            for k, i in enumerate(lst)) + '</div>'
            '<div class="leg"><span><i class="u"></i>ඉහළ</span><span><i class="dn"></i>පහළ</span><span><i class="f"></i>සමාන</span><span class="s">TopGoviya.lk</span></div>')

    def cards(lst, cls):
        return "".join(f'<div class="card" style="animation-delay:{0.4 + k * MOVER_SEC:.2f}s"><div style="flex:1"><div class="n">{i["e"]} {name(i)}</div>'
                       f'<div class="p mono">රු. {price(i)}{unit(i)}</div></div>'
                       f'<div class="c mono {cls}" style="animation-delay:{0.7 + k * MOVER_SEC:.2f}s">{"▲" if cls == "u" else "▼"} {abs(i["chg"]):.0f}%</div></div>'
                       for k, i in enumerate(lst))

    ranked = sorted(items, key=lambda i: i["pop"])
    bsec = lambda n: n * ITEM_SEC + HOLD_SEC
    slides, durs = [], []
    for k in range(0, min(len(ranked), MAX_ITEMS), ROWS_PER_BOARD):   # second 0: the prices, nothing else
        bl = ranked[k:k + ROWS_PER_BOARD]
        slides.append(page(board(bl), small=k > 0)); durs.append(bsec(len(bl)))
    if rises or falls:
        mv_html = '<div class="mv">'
        if rises: mv_html += f'<div class="lbl" style="color:#ff8a80">📈 අද වැඩිම ඉහළ යාම</div>{cards(rises[:3], "u")}'
        if falls: mv_html += f'<div class="lbl" style="color:#7fe0a6">📉 අද වැඩිම පහළ යාම</div>{cards(falls[:3], "dn")}'
        slides.append(page(mv_html + '</div>' + brand, small=True))
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
    # Thumbnail (Nov 2026): last 1.2 s of the video (pick this frame in YouTube's thumbnail picker) + thumbnail.png
    th_rows = "".join(f'<div class="o"><span class="nm">{i["e"]} {i["si"].partition(" (")[0]}</span><span class="v mono">{price(i)}</span>{dot(i["chg"])}</div>'
                      for i in staples[:5])
    thumb = page(f'<div class="th"><div class="emo">🥬🍅🧅</div><div class="h">දඹුල්ල එළවළු<br>මිල අද</div>'
                 f'<div class="db"><div class="d mono">{dotdate}</div><div class="w">{DAYS_SI[wd]} • 1kg රු.</div></div>{th_rows}</div>', header=False)
    thumb = thumb.replace('class="topband">අද දඹුල්ල එළවළු තොග මිල<', 'class="topband">TopGoviya.lk<')
    slides.append(thumb); durs.append(1.2)
    from playwright.sync_api import sync_playwright   # only needed when a video is made
    if "--preview" in sys.argv:      # one still per slide + red danger zones, to check the layout on a phone
        os.makedirs(OUT, exist_ok=True)
        zones = (f'<div style="position:fixed;inset:0;pointer-events:none">'
                 f'<div style="position:absolute;left:0;right:0;top:0;height:{SAFE_TOP}px;background:rgba(255,0,0,.35)"></div>'
                 f'<div style="position:absolute;left:0;right:0;bottom:0;height:{SAFE_BOTTOM}px;background:rgba(255,0,0,.35)"></div>'
                 f'<div style="position:absolute;left:0;top:{SAFE_TOP}px;bottom:{SAFE_BOTTOM}px;width:{SAFE_LEFT}px;background:rgba(255,0,0,.35)"></div>'
                 f'<div style="position:absolute;right:0;top:{SAFE_TOP}px;bottom:{SAFE_BOTTOM}px;width:{SAFE_RIGHT}px;background:rgba(255,0,0,.35)"></div></div>')
        with sync_playwright() as pw:
            b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
            for n, html in enumerate(slides):
                pg.set_content(html.replace("</body>", zones + "</body>")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
                pg.evaluate(f"document.getAnimations().forEach(a => {{a.pause(); a.currentTime = {durs[n] * 1000 - 50:.0f}}})")
                pg.screenshot(path=f"{OUT}/preview-{n}.png")
            b.close()
        print(f"Preview saved: {len(slides)} pictures in {OUT}/"); return
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
    # Facebook link carries utm_ tags, so Google Analytics shows how many visitors come from the Facebook posts
    facebook = (f"🥬 අද දඹුල්ල එළවළු තොග මිල — {D}\n{mood}\n\n" + "\n".join(moves) +
                "\n\n👉 භාණ්ඩ 90+ ක මිල, 🛒 බාස්කට් එක, 🧮 ලාභ ගණකය: https://topgoviya.lk/?d=" + last + "&utm_source=facebook&utm_medium=social&utm_campaign=dambulla_daily\n"
                "📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය\n⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
                "#දඹුල්ල #එළවළුමිල #TopGoviyaLK")
    tags = ["දඹුල්ල එලවලු මිල අද", "දඹුල්ල ආර්ථික මධ්‍යස්ථානයේ එළවළු මිල", "දඹුල්ලේ එලවලු මිල", "එලවලු මිල අද",
            "දඹුල්ල එළවළු මිල", "අද දඹුල්ල එළවළු මිල", "දබුල්ල එලවලු මිල", "dambulla market price today",
            "dambulla vegetable price", "dambulla price today", "එළවළු මිල", "අද එළවළු මිල", "තොග මිල",
            "elawalu mila", "elawalu mila ada", "vegetable price sri lanka", f"එළවළු මිල {date.fromisoformat(last).year}", "TopGoviya"]
    # music test (Nov 2026): a different track each day, so we can compare views per song
    found = [t for t in SHORT_TRACKS if os.path.exists(os.path.join("music", t))]
    track = os.path.join("music", found[date.fromisoformat(last).toordinal() % len(found)]) if found else \
        short_kit.pick_track("music-5.wav", "music-2.wav", "music-1.wav")
    short_kit.package(f"{OUT}/03-dambulla-{TAG}", silent, track, seconds, title, desc, tiktok, facebook,
                      tags, "🥬 අද දඹුල්ල එළවළු මිල | Dambulla Market Price Daily")
    pin = pin_comment(rises, falls, last)
    folder = f"{OUT}/03-dambulla-{TAG}"
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.set_content(thumb); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.evaluate("document.getAnimations().forEach(a => {a.pause(); a.currentTime = 5000})")
        pg.screenshot(path=f"{folder}/thumbnail.png"); b.close()
    open(f"{folder}/pin-comment.txt", "w", encoding="utf-8").write(pin + "\n")
    with open(f"{folder}/youtube.txt", "a", encoding="utf-8") as f:
        f.write("\nPINNED COMMENT (post it, then ⋮ → Pin):\n" + pin + "\n")
        f.write("\nTHUMBNAIL:\nthumbnail.png is also the LAST frame of the video. Phone app: thumbnail picker → slide to the very end. "
                "Computer (YouTube Studio): Thumbnail → Upload file → thumbnail.png (only if your channel has this option).\n")
        f.write("\nMUSIC USED (note the views after 2-3 days to see which song works best):\n" + (os.path.basename(track) if track else "none") + "\n")
    import shutil
    for fd in dirs:
        shutil.rmtree(fd, ignore_errors=True)
    if os.path.exists(silent): os.remove(silent)
    open(STATE, "w").write(st)
    print(f"Video for {last}: {n} slides, ~{seconds:.0f}s")


if __name__ == "__main__":
    main()
