"""
TopGoviya.lk — WEEKLY spice price YouTube Short in the Dambulla "price board" style
-----------------------------------------------------------------------------------
Usage: python3 make_spice_board_short.py [--check] [--force] [--preview]
  --check   prints need=yes / need=no (is there a new DEA week without a video yet?)
  --force   make the video even if this week was already done
  --preview save one picture per slide (short/preview-N.png) with YouTube's danger zones marked, no video

Data: dea_data.json (DEA weekly farm gate prices, national average, Rs./kg).
Output: short/04-spice-board-DATE/ with video-with-music.mp4, video-silent.mp4,
        youtube.txt, tiktok.txt, facebook.txt, pin-comment.txt
Design (Nov 2026): same as the daily Dambulla Short - huge date box, 3 boards x 7 big rows
(spice + grade, average price, red/green/grey up-down dot vs the previous DEA week),
then the week's biggest movers, then the end card. All text inside the mobile safe area.
"""
import json, base64, os, subprocess, sys, hashlib, shutil
from datetime import date
import short_kit

DATA = "dea_data.json"
OUT = "short"; FADE = 0.3; FPS = 30
ITEM_SEC = 0.9; HOLD_SEC = 2.0; MOVER_SEC = 0.7; END_SEC = 3.5
STATE = ".spice_board_last"
LOGO = "icon-512x512.png"
SI_MONTHS = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි", "අගෝස්තු",
             "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]
SAFE_TOP, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT = 300, 480, 120, 220
ROWS_PER_BOARD = 7

# Most-wanted first (3 boards x 7). commodity key, DEA grade column (without " (Average Price)"), Sinhala name, grade label, emoji
# All per kg (betel and fresh arecanut are left out - different units).
ROWS = [
    ("pepper", "GR-1", "කළු ගම්මිරිස්", "GR-1", "🌶️"),
    ("pepper", "WHITE", "සුදු ගම්මිරිස්", "WHITE", "⚪"),
    ("cinnamon", "Alba", "කුරුඳු", "Alba", "🪵"),
    ("cinnamon", "C-5", "කුරුඳු", "C-5", "🪵"),
    ("clove", "CLOVE", "කරාබු නැටි", "", "🌿"),
    ("cardamom", "LG", "එනසාල්", "LG", "🫛"),
    ("nutmeg", "NUTMEG No.1", "සාදික්කා", "No.1", "🌰"),
    # board 2
    ("nutmeg", "MACE No.1", "වසාවාසි", "No.1", "🌺"),
    ("pepper", "GR-2", "කළු ගම්මිරිස්", "GR-2", "🌶️"),
    ("cinnamon", "H-1", "කුරුඳු", "H-1", "🪵"),
    ("cinnamon", "C-4", "කුරුඳු", "C-4", "🪵"),
    ("coffee", "GR 1", "කෝපි", "GR 1", "☕"),
    ("cocoa", "GR 1", "කොකෝවා", "GR 1", "🍫"),
    ("arecanut", "Dried-(Karunka)-(Rs./k.g.)", "පුවක්", "වියළි", "🌴"),
    # board 3
    ("other", "Ginger", "ඉඟුරු", "", "🫚"),
    ("other", "Turmeric", "කහ", "", "🟡"),
    ("other", "Goraka", "ගොරකා", "", "🟤"),
    ("other", "Kithul Jaggery", "කිතුල් හකුරු", "", "🍯"),
    ("clove", "STEM", "කරාබු", "කඳ", "🌿"),
    ("cardamom", "LLG1", "එනසාල්", "LLG1", "🫛"),
    ("cinnamon", "M-5", "කුරුඳු", "M-5", "🪵"),
]


def nat(week, key, grade):
    return week["commodities"].get(key, {}).get("districts", {}).get("National", {}).get(f"{grade} (Average Price)")


def si_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {SI_MONTHS[d.month - 1]} {d.year}"


def rs(v): return f"{v:,.0f}"


def main():
    W = json.load(open(DATA, encoding="utf-8"))["weeks"]
    last, prev = W[-1], (W[-2] if len(W) > 1 else None)
    items = []
    for k, (key, grade, si, glbl, emo) in enumerate(ROWS):
        now = nat(last, key, grade)
        if not now:
            continue
        p = nat(prev, key, grade) if prev else None
        chg = (now - p) / p * 100 if p else None
        items.append(dict(rank=k, si=si, g=glbl, e=emo, v=now, chg=chg))
    fp = hashlib.sha1(json.dumps([(i["si"], i["g"], i["v"]) for i in items]).encode()).hexdigest()[:8]
    st = f"{last['date']}_{fp}"
    done = os.path.exists(STATE) and open(STATE).read().strip() == st
    if "--check" in sys.argv:
        print("need=" + ("no" if done else "yes")); return
    if done and "--force" not in sys.argv and "--preview" not in sys.argv:
        print("Video for DEA week", last["date"], "already made."); return
    if len(items) < 10:
        print("Too few spice prices for", last["date"]); return

    moved = [i for i in items if i["chg"] is not None]
    rises = sorted([i for i in moved if i["chg"] >= 0.5], key=lambda i: -i["chg"])[:3]
    falls = sorted([i for i in moved if i["chg"] <= -0.5], key=lambda i: i["chg"])[:3]
    up, dn = sum(i["chg"] >= 0.5 for i in moved), sum(i["chg"] <= -0.5 for i in moved)
    same = len(moved) - up - dn
    D = si_date(last["date"]); TAG = last["date"]; y = date.fromisoformat(last["date"]).year
    dotdate = f"{date.fromisoformat(last['date']):%Y.%m.%d}"
    logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode() if os.path.exists(LOGO) else ""

    css = """
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#3a1f0d;font-family:'Noto Sans Sinhala',sans-serif;color:#fbf3e4;display:flex;flex-direction:column;overflow:hidden}
.mono{font-family:'JetBrains Mono',monospace}
.topband{height:SAFE_TOPpx;flex:none;background:#5a2f12;display:flex;align-items:flex-end;justify-content:center;padding:0 SAFE_RIGHTpx 14px SAFE_LEFTpx;font-size:48px;font-weight:800;text-align:center}
.botband{height:SAFE_BOTTOMpx;flex:none;background:#5a2f12;display:flex;align-items:flex-start;gap:24px;padding:40px SAFE_RIGHTpx 0 SAFE_LEFTpx;opacity:.55}
.botband img{width:90px;height:90px;border-radius:18px}
.botband .s{font-size:60px;font-weight:800;color:#ffd43b;font-family:'JetBrains Mono',monospace}
.mid{flex:1;display:flex;flex-direction:column;overflow:hidden}
.hd{background:#5a2f12;padding:6px SAFE_RIGHTpx 14px SAFE_LEFTpx;text-align:center}
.dbox{margin-top:8px;background:#ffd43b;color:#3a1f0d;border-radius:24px;padding:4px 16px 10px}
.dbox .d{font-size:112px;font-weight:800;line-height:1.1;letter-spacing:-2px}
.dbox .w{font-size:40px;font-weight:800}
.hd.sm .dbox .d{font-size:74px}.hd.sm .dbox .w{font-size:32px}
.rows{flex:1;display:flex;flex-direction:column;padding-top:10px}
.r{display:flex;align-items:center;padding:0 SAFE_RIGHTpx 0 SAFE_LEFTpx;height:110px;margin-bottom:5px;position:relative}
.r:nth-child(odd){background:#6b3815}.r:nth-child(even){background:#4f2a10}
.r .n{flex:1;min-width:0;font-size:54px;font-weight:800;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.r .n small{display:block;font-size:30px;font-weight:600;color:#f0cfa0;line-height:1.1}
.r .p{font-size:66px;font-weight:800;color:#fff;margin:0 16px 0 12px;white-space:nowrap}
.dot{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:36px;font-weight:800;flex:none}
.u{background:#e23d34}.dn{background:#22a05a}.f{background:#96968c}
.leg{display:flex;gap:20px;padding:14px SAFE_RIGHTpx 14px SAFE_LEFTpx;font-size:32px;white-space:nowrap;font-weight:600;align-items:center;background:#5a2f12}
.leg i{display:inline-block;width:28px;height:28px;border-radius:50%;margin-right:8px;vertical-align:middle}
.leg .s,.brand .s{margin-left:auto;font-size:36px;font-weight:800;color:#ffd43b;font-family:'JetBrains Mono',monospace}
.brand{display:flex;padding:12px SAFE_RIGHTpx 12px SAFE_LEFTpx;background:#5a2f12;align-items:center;font-size:32px;font-weight:700}
.mv{flex:1;padding:8px SAFE_RIGHTpx 6px SAFE_LEFTpx;display:flex;flex-direction:column;justify-content:center}
.mv .lbl{font-size:48px;font-weight:800;margin:4px 0 8px}
.card{display:flex;align-items:center;border-radius:22px;padding:6px 20px;margin-bottom:8px;background:#6b3815}
.card .n{flex:1;font-size:44px;font-weight:800;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card .p{font-size:34px;color:#f3e3cc}
.card .c{font-size:48px;font-weight:800;padding:8px 18px;border-radius:18px;color:#fff;white-space:nowrap;margin-left:12px}
.end{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 SAFE_RIGHTpx 0 SAFE_LEFTpx;text-align:center}
.end .big{font-size:62px;font-weight:800;line-height:1.35}
.end .url{font-size:86px;font-weight:800;color:#ffd43b;margin:20px 0}
.end .note{font-size:32px;color:#f0dcc0;line-height:1.6}
.cta{margin-top:28px;background:#6b3815;border-radius:24px;padding:4px 24px;text-align:left}
.ct{display:flex;align-items:center;gap:18px;padding:12px 0;font-size:34px;font-weight:700}
.ct+.ct{border-top:2px solid #4f2a10}.ci{font-size:42px;width:56px;text-align:center}
.th{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 SAFE_RIGHTpx 0 SAFE_LEFTpx;text-align:center}
.th .emo{font-size:110px;line-height:1.05}
.th .h{font-size:96px;font-weight:800;line-height:1.15;color:#fff}
.th .pr{margin:16px 0 8px;background:#ffd43b;color:#3a1f0d;border-radius:30px;padding:10px 10px 18px}
.th .pr .v{font-size:116px;font-weight:800;line-height:1.1;letter-spacing:-3px;white-space:nowrap}
.th .pr .v b{font-size:80px;vertical-align:middle}
.th .pr .l{font-size:38px;font-weight:800}
.th .dt{font-size:42px;font-weight:800;color:#ffd43b;margin-bottom:8px}
.th .o{display:flex;justify-content:space-between;background:#6b3815;border-radius:18px;padding:4px 22px;margin-top:8px;font-size:42px;font-weight:800}
@keyframes slideIn{0%{transform:translateX(105%);opacity:0}70%{transform:translateX(-3%);opacity:1}100%{transform:none;opacity:1}}
@keyframes pop{0%{transform:scale(0)}70%{transform:scale(1.3)}100%{transform:scale(1)}}
@keyframes drop{0%{transform:translateY(-60px);opacity:0}100%{transform:none;opacity:1}}
@keyframes glow{0%,100%{transform:scale(1)}50%{transform:scale(1.02)}}
@keyframes hl{0%,100%{background:inherit;transform:none}15%,85%{background:#a0561f;transform:scale(1.02);box-shadow:0 0 0 5px #ffd43b inset}}
.r,.card{animation:slideIn .4s ease-out both}
.dot,.card .c{animation:pop .3s ease-out both}
.dbox{animation:glow 1.6s ease-in-out .6s infinite}
.mv .lbl,.end>*{animation:drop .35s ease-out both}
""".replace("SAFE_TOP", str(SAFE_TOP)).replace("SAFE_BOTTOM", str(SAFE_BOTTOM)).replace("SAFE_LEFT", str(SAFE_LEFT)).replace("SAFE_RIGHT", str(SAFE_RIGHT))

    def head(small=False):
        return (f'<div class="hd{" sm" if small else ""}"><div class="dbox"><div class="d mono">{dotdate}</div>'
                f'<div class="w">සතිපතා ගොවිපළ මිල • 1kg රු.</div></div></div>')

    img_tag = f'<img src="{logo}">' if logo else ""
    foot = f'<div class="botband">{img_tag}<div class="s">TopGoviya.lk</div></div>'
    brand = '<div class="brand"><span>සම්පූර්ණ ලැයිස්තුව 👉</span><span class="s">TopGoviya.lk</span></div>'

    def page(inner, small=False, header=True):
        return (f'<html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="topband">මේ සතියේ කුළුබඩු මිල</div>'
                f'<div class="mid">{head(small) if header else ""}{inner}</div>{foot}</body></html>')

    def name(i):
        return f'{i["si"]}<small>{i["g"]}</small>' if i["g"] else i["si"]

    def dot(c):
        if c is None or abs(c) < 0.5: return '<span class="dot f">●</span>'
        return '<span class="dot u">▲</span>' if c > 0 else '<span class="dot dn">▼</span>'

    def board(lst):
        return ('<div class="rows">' + "".join(
            f'<div class="r" style="animation:slideIn .4s ease-out {k * ITEM_SEC:.2f}s both,hl {ITEM_SEC:.2f}s ease-in-out {k * ITEM_SEC + 0.35:.2f}s">'
            f'<div class="n">{name(i)}</div><div class="p mono">{rs(i["v"])}</div>'
            + dot(i["chg"]).replace('<span class="dot', f'<span style="animation-delay:{k * ITEM_SEC + 0.35:.2f}s" class="dot') + '</div>'
            for k, i in enumerate(lst)) + '</div>'
            '<div class="leg"><span><i class="u"></i>ඉහළ</span><span><i class="dn"></i>පහළ</span><span><i class="f"></i>සමාන</span><span class="s">TopGoviya.lk</span></div>')

    def label(i): return f'{i["si"]} {i["g"]}'.strip()

    def cards(lst, cls):
        return "".join(f'<div class="card" style="animation-delay:{0.4 + k * MOVER_SEC:.2f}s"><div style="flex:1"><div class="n">{i["e"]} {label(i)}</div>'
                       f'<div class="p mono">රු. {rs(i["v"])} /kg</div></div>'
                       f'<div class="c mono {cls}" style="animation-delay:{0.7 + k * MOVER_SEC:.2f}s">{"▲" if cls == "u" else "▼"} {abs(i["chg"]):.0f}%</div></div>'
                       for k, i in enumerate(lst))

    slides, durs = [], []
    for k in range(0, len(items), ROWS_PER_BOARD):
        bl = items[k:k + ROWS_PER_BOARD]
        slides.append(page(board(bl), small=k > 0)); durs.append(len(bl) * ITEM_SEC + HOLD_SEC)
    if rises or falls:
        mv_html = '<div class="mv">'
        if rises: mv_html += f'<div class="lbl" style="color:#ff8a80">📈 වැඩිම ඉහළ යාම</div>{cards(rises, "u")}'
        if falls: mv_html += f'<div class="lbl" style="color:#7fe0a6">📉 වැඩිම පහළ යාම</div>{cards(falls, "dn")}'
        slides.append(page(mv_html + '</div>' + brand, small=True))
        durs.append(0.4 + (len(rises) + len(falls)) * MOVER_SEC + HOLD_SEC)
    slides.append(page('<div class="end"><div class="big">කුළුබඩු 11ක මිල<br>දිස්ත්‍රික්ක 14ක් අනුව</div>'
                       '<div class="url mono">topgoviya.lk</div>'
                       '<div class="note">සිංහල · தமிழ் · English · නොමිලේ<br>මූලාශ්‍රය: අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුව<br>මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.</div>'
                       '<div class="cta">'
                       '<div class="ct"><span class="ci">💬</span><span>ඔබේ ප්‍රදේශයේ මිල කමෙන්ට් කරන්න</span></div>'
                       '<div class="ct"><span class="ci">📤</span><span>කුළුබඩු වවන මිතුරන්ට ෂෙයාර් කරන්න</span></div>'
                       '<div class="ct"><span class="ci">🔔</span><span>සෑම සතියකම මිල සඳහා Subscribe කරන්න</span></div>'
                       '</div></div>', small=True))
    durs.append(END_SEC)
    # Thumbnail: last 1.2 s of the video (choose this frame in YouTube's thumbnail picker) + thumbnail.png
    pep = items[0]
    pick = (("කුරුඳු", "Alba"), ("කරාබු නැටි", ""), ("එනසාල්", "LG"))
    others = "".join(f'<div class="o"><span>{i["e"]} {i["si"]}</span><span class="mono">{rs(i["v"])}</span></div>'
                     for i in items if (i["si"], i["g"]) in pick)
    arrow = "" if pep["chg"] is None or abs(pep["chg"]) < 0.5 else (' <b style="color:#c62828">▲</b>' if pep["chg"] > 0 else ' <b style="color:#1b7a43">▼</b>')
    thumb = page(f'<div class="th"><div class="emo">🌶️</div><div class="h">ගම්මිරිස් මිල<br>අද</div>'
                 f'<div class="pr"><div class="v mono">රු. {rs(pep["v"])}{arrow}</div><div class="l">කළු ගම්මිරිස් GR-1 • 1kg</div></div>'
                 f'<div class="dt mono">මේ සතිය • {dotdate}</div>{others}</div>', header=False)
    thumb = thumb.replace('class="topband">මේ සතියේ කුළුබඩු මිල<', 'class="topband">TopGoviya.lk<')
    # Thumbnail uses the full picture (no Shorts safe-area margins): bigger heading, price and rows.
    # The price line shrinks itself to fit the width, so 5-digit prices still fit on one line.
    big = ('<style>'
           '.topband{height:170px;padding:0 50px 18px;font-size:58px}'
           '.botband{height:230px;padding:40px 60px 0;opacity:.95;align-items:center}'
           '.botband img{width:130px;height:130px;border-radius:24px}.botband .s{font-size:86px}'
           '.th{padding:0 46px}.th .emo{font-size:130px}'
           '.th .h{font-size:132px;line-height:1.12}'
           '.th .pr{margin:30px 0 18px;border-radius:40px;padding:14px 16px 26px}'
           '.th .pr .v{font-size:200px;letter-spacing:-6px;display:inline-block}'
           '.th .pr .v b{font-size:120px}.th .pr .l{font-size:62px}'
           '.th .dt{font-size:62px;margin-bottom:10px}'
           '.th .o{font-size:62px;padding:8px 34px;margin-top:14px;border-radius:26px}'
           '</style>')
    fit = ('<script>document.fonts.ready.then(()=>{const v=document.querySelector(".th .pr .v");'
           'if(!v)return;let f=200;const max=v.parentElement.clientWidth-30;'
           'while(v.scrollWidth>max&&f>90){f-=4;v.style.fontSize=f+"px";}});</script>')
    thumb = thumb.replace("</head>", big + "</head>").replace("</body>", fit + "</body>")
    slides.append(thumb); durs.append(1.2)

    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
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

    dirs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for n, html in enumerate(slides):
            pg.set_content(html); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            pg.evaluate("document.getAnimations().forEach(a => a.pause())")
            fd = f"{OUT}/sframes{n:02d}"; os.makedirs(fd, exist_ok=True); dirs.append(fd)
            for f in range(int(durs[n] * FPS)):
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
    silent = f"{OUT}/spice-board-{TAG}-silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                    "-map", "[outv]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", silent], check=True)
    seconds = sum(durs) - (n - 1) * FADE

    mv = lambda i, a: f"{a} {label(i)}: රු. {rs(i['v'])} ({'+' if i['chg'] > 0 else '−'}{abs(i['chg']):.0f}%)"
    top = "\n".join(f"{i['e']} {label(i)}: රු. {rs(i['v'])}" for i in items[:7])
    moves = [mv(i, "📈") for i in rises[:2]] + [mv(i, "📉") for i in falls[:2]]
    pep = items[0]   # black pepper GR-1 - the most searched spice
    title = f"ගම්මිරිස් මිල අද {y} රු. {rs(pep['v'])} | මේ සතියේ කුළුබඩු මිල {dotdate[5:]} | කුරුඳු කරාබු එනසාල් #shorts"
    if len(title) > 100:   # YouTube limit
        title = title.replace(" | කුරුඳු කරාබු එනසාල්", "")
    desc = (f"🌶️ ගම්මිරිස් මිල අද — කළු ගම්මිරිස් GR-1 රු. {rs(pep['v'])}/kg · මේ සතියේ කුළුබඩු ගොවිපළ මිල — {D}\nඅපනයන කෘෂිකර්ම දෙපාර්තමේන්තුවේ (DEA) ජාතික සාමාන්‍ය මිල, රු./කි.ග්‍රෑ.\n"
            f"පෙර සතියට සාපේක්ෂව: {up}ක් ඉහළ, {dn}ක් පහළ, {same}ක් වෙනසක් නැත.\n"
            + ("\nමිල ඉහළ ගිය:\n" + "\n".join(mv(i, "📈") for i in rises) + "\n" if rises else "")
            + ("\nමිල පහළ ගිය:\n" + "\n".join(mv(i, "📉") for i in falls) + "\n" if falls else "")
            + "\nප්‍රධාන කුළුබඩු:\n" + top +
            "\n\n👉 කුළුබඩු 11ක මිල, දිස්ත්‍රික්ක 14ක් අනුව: https://topgoviya.lk/spice-price-guide.html\n"
            "📊 මූලාශ්‍රය: අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුව (DEA)\n"
            "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
            "#ගම්මිරිස්මිල #කුළුබඩුමිල #කුරුඳුමිල #gammirismila #SpicePrices #TopGoviyaLK #SriLanka #shorts")
    tiktok = (f"ගම්මිරිස් මිල අද රු. {rs(pep['v'])} 🌶️ මේ සතියේ කුළුබඩු මිල — {D}\n" + "\n".join(moves) +
              "\nකුළුබඩු 21ක මිල වීඩියෝවේ 👆 · සියලු දිස්ත්‍රික්ක 👉 topgoviya.lk · දත්ත: DEA\nමිල ගණන් මඟපෙන්වීමක් පමණි.\n\n"
              "#ගම්මිරිස්මිල #කුළුබඩුමිල #කුරුඳුමිල #gammirismila #SriLanka #TopGoviyaLK #fyp")
    facebook = (f"🌶️ මේ සතියේ කුළුබඩු ගොවිපළ මිල — {D}\nඔබ කුළුබඩු විකුණන්නේ කීයටද? 👇 කමෙන්ට් කරන්න\n\n{top}\n\n" + "\n".join(moves) +
                "\n\n👉 කුළුබඩු 11ක මිල, දිස්ත්‍රික්ක 14ක් අනුව: https://topgoviya.lk/spice-price-guide.html"
                "?utm_source=facebook&utm_medium=social&utm_campaign=spice_weekly\n"
                "📊 මූලාශ්‍රය: අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුව (DEA)\n⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
                "#ගම්මිරිස්මිල #කුළුබඩුමිල #කුරුඳුමිල #එනසාල්මිල #SriLanka #TopGoviyaLK")
    tags = ["ගම්මිරිස් මිල අද", "ගම්මිරිස් මිල", f"ගම්මිරිස් මිල අද {y}", "කුළුබඩු මිල", "කුලුබඩු මිල", "කුළුබඩු මිල අද",
            "කුරුඳු මිල", "කරාබු මිල", "එනසාල් මිල", "සාදික්කා මිල", "gammiris mila", "gammiris mila ada",
            "kurundu mila", "karabu mila", "pepper price today sri lanka", "spice prices sri lanka",
            "cinnamon price sri lanka", "TopGoviya"]
    track = short_kit.pick_track("music-4.wav", "music-5.wav")   # our own spice track: "Green hill garden"
    folder = f"{OUT}/04-spice-board-{TAG}"
    short_kit.package(folder, silent, track, seconds, title, desc, tiktok, facebook, tags,
                      "🌶️ කුළුබඩු මිල — සතිපතා | Sri Lanka Spice Prices")
    q = (f"\n💬 මේ සතියේ {label(rises[0])} මිල ඉහළ ගියා. ඔබේ ප්‍රදේශයේ කීයද? කමෙන්ට් කරන්න 👇" if rises else
         f"\n💬 මේ සතියේ {label(falls[0])} මිල පහළ ගියා. ඔබේ ප්‍රදේශයේ කීයද? කමෙන්ට් කරන්න 👇" if falls else "")
    pin = ("📌 සෑම සතියකම කුළුබඩු මිල සඳහා Subscribe කරන්න 🔔\n"
           "👉 කුළුබඩු 11ක මිල, දිස්ත්‍රික්ක 14ක් අනුව: https://topgoviya.lk/spice-price-guide.html" + q +
           f"\n📊 මූලාශ්‍රය: අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුව · {dotdate}")
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
        f.write("\nMUSIC USED:\n" + (os.path.basename(track) if track else "none") + "\n")
    for fd in dirs: shutil.rmtree(fd, ignore_errors=True)
    if os.path.exists(silent): os.remove(silent)
    open(STATE, "w").write(st)
    print(f"Spice board Short for DEA week {last['date']}: {len(items)} prices, {len(slides)} slides, ~{seconds:.0f}s")


if __name__ == "__main__":
    main()
