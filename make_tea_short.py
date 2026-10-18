"""
make_tea_short.py  -  TopGoviya.lk monthly TEA price Short (Sri Lanka Tea Board, made tea auction prices)
--------------------------------------------------------------------------------------------------------
Reads tea_price_data.json (38 sub-districts, monthly average Rs./kg) and the Sinhala/Tamil sub-district
names from tea.html, then makes a 9:16 video with background music and a ready-to-post folder:

  short/01-tea-YYYY-MM/
     video-with-music.mp4   (post this)
     video-silent.mp4       (for trending sounds on TikTok / Reels)
     youtube.txt            title + description + hashtags
     tiktok.txt             short caption + hashtags
     facebook.txt           caption + clickable link + hashtags

  python3 make_tea_short.py [tea_price_data.json] [icon-512x512.png]
Needs: ffmpeg, Playwright (Chromium), Noto Sans Sinhala font. Music: music/music-4.wav.
These are MADE TEA auction prices, not green leaf prices - every slide and caption says so.
"""
import json, base64, os, re, subprocess, sys, shutil

DATA = sys.argv[1] if len(sys.argv) > 1 else "tea_price_data.json"
LOGO = sys.argv[2] if len(sys.argv) > 2 else "icon-512x512.png"
OUT = "short"; SLIDE_SEC = 4.5; FADE = 0.5
MUSIC = "music/music-4.wav"; MUSIC_VOL = 0.8
SITE = "https://topgoviya.lk/tea.html"
MONTHS_SI = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි",
             "අගෝස්තු", "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]
LOW_GROWN = {"Deniyaya", "Matara", "Morawaka", "Galle", "Kalutara", "Ratnapura",
             "Kegalle", "Kelani Valley", "Balangoda", "Balangoda-Rakwana"}
os.makedirs(OUT, exist_ok=True)


def si_names():
    """Sinhala names of the sub-districts, read from tea.html so they always match the website."""
    try:
        s = open("tea.html", encoding="utf-8").read()
        return {en: si for en, si in re.findall(r'"([^"]+)":\["([^"]+)","[^"]*"\]', s)}
    except Exception:
        return {}


d = json.load(open(DATA, encoding="utf-8"))
months = d["months"]; keys = sorted(months)
CUR = d.get("latestMonth") or keys[-1]
i = keys.index(CUR); PREV = keys[i - 1] if i > 0 else None
y, m = map(int, CUR.split("-")); LY = f"{y - 1}-{m:02d}"
tbl = lambda k: {r["subDistrict"]: r["monthlyAvg"] for r in months.get(k, []) if r.get("monthlyAvg")}
cur, prev, ly = tbl(CUR), tbl(PREV) if PREV else {}, tbl(LY)
SI = si_names()
nm = lambda en: SI.get(en, en)
MONTH_SI = f"{y} {MONTHS_SI[m - 1]}"
MONTH_PREV_SI = f"{MONTHS_SI[int(PREV[5:]) - 1]}" if PREV else ""
rs = lambda v: f"{v:,.0f}"
avg = lambda t, keep=lambda k: True: (sum(v for k, v in t.items() if keep(k)) / max(1, sum(1 for k in t if keep(k)))) if t else None

top = sorted(cur.items(), key=lambda kv: -kv[1])[:5]
moves = sorted([(k, prev[k], v, (v - prev[k]) / prev[k] * 100) for k, v in cur.items() if prev.get(k)], key=lambda r: r[3])
rises = [r for r in reversed(moves) if r[3] >= 0.5][:3]
falls = [r for r in moves if r[3] <= -0.5][:3]
up_now = avg(cur, lambda k: k not in LOW_GROWN); low_now = avg(cur, lambda k: k in LOW_GROWN)
all_now, all_ly = avg(cur), avg({k: v for k, v in ly.items() if k in cur})
ly_pct = (all_now - all_ly) / all_ly * 100 if all_ly else None

# optional picture for the first slide (e.g. a cup of tea); the slide works without it too
HERO = next((f for f in ("video-assets/tea-cup.png", "video-assets/tea-cup.jpg") if os.path.exists(f)), None)
hero = ("data:image/" + ("png" if HERO.endswith(".png") else "jpeg") + ";base64," +
        base64.b64encode(open(HERO, "rb").read()).decode()) if HERO else ""
logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode() if os.path.exists(LOGO) else ""
CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1920px;background:#0e4f4a;font-family:'Noto Sans Sinhala',sans-serif;color:#fff;overflow:hidden;position:relative}
.safe{position:absolute;top:200px;left:60px;right:60px;bottom:240px;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:18px}.brand img{width:80px;height:80px;border-radius:16px;background:#fff}
.brand b{font-size:40px}.brand span{display:block;font-size:22px;color:#e7d3a3;font-weight:400}
h1{font-size:92px;line-height:1.12;margin:40px 0 14px}h2{font-size:58px;line-height:1.2;margin:10px 0 22px}
.pill{align-self:flex-start;background:#a9802a;border-radius:999px;padding:10px 32px;font-size:38px;font-weight:700}
.sub{color:#e7d3a3;font-size:32px;margin-top:22px;line-height:1.5}
.card{background:#fffdf7;color:#191d1a;border-radius:26px;padding:10px 28px}
.row{display:flex;justify-content:space-between;align-items:center;padding:22px 0;border-top:1px solid #e3d9c4;font-size:42px;font-weight:700}
.row:first-child{border-top:0}.n{font-family:'JetBrains Mono',monospace}.rk{color:#a9802a;margin-right:14px}
.up{color:#2c7a52}.dn{color:#b23a2e}.small{font-size:28px;color:#7a7264;font-weight:400;display:block}
.note{margin-top:auto;font-size:28px;color:#e7d3a3;line-height:1.5}
.hero{flex:1;margin:30px -60px 0;background-size:cover;background-position:center 82%;
  -webkit-mask-image:linear-gradient(to bottom,transparent 0%,#000 22%,#000 78%,transparent 100%);
  mask-image:linear-gradient(to bottom,transparent 0%,#000 22%,#000 78%,transparent 100%)}
.cta{margin-top:56px;background:rgba(255,255,255,.08);border:2px solid rgba(231,211,163,.45);border-radius:26px;padding:14px 30px}
.ct{display:flex;align-items:center;gap:22px;padding:20px 0;font-size:40px;font-weight:700}
.ct+.ct{border-top:1px solid rgba(231,211,163,.3)}.ci{font-size:54px;width:70px;text-align:center}
.big{font-size:120px;font-weight:800;font-family:'JetBrains Mono',monospace;color:#ffd98a;margin:10px 0}"""


def page(inner):
    return (f'<!DOCTYPE html><html lang="si"><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="safe">'
            f'<div class="brand">{f"<img src={chr(34)}{logo}{chr(34)}>" if logo else ""}<div><b>TopGoviya.lk</b>'
            f'<span>දත්තය බලලා තීරණ ගන්න</span></div></div>{inner}</div></body></html>')


slides = []
slides.append(page(f'<h1>🍃 තේ වෙන්දේසි මිල</h1><div class="pill">{MONTH_SI}</div>'
                   f'<div class="big">රු. {rs(all_now)}</div><div class="sub" style="margin-top:0">උප දිස්ත්‍රික්ක {len(cur)} සාමාන්‍යය · කි.ග්‍රෑ. එකකට</div>'
                   f'<div class="sub">සැකසූ තේ (Made tea) වෙන්දේසි මිල · ශ්‍රී ලංකා තේ මණ්ඩලය</div>'
                   + (f'<div class="hero" style="background-image:url({hero})"></div>' if hero else '') +
                   f'<div class="note">⚠️ මෙය දළු (කොළ) මිල නොවේ — සැකසූ තේ වෙන්දේසි මාසික සාමාන්‍යය.</div>'))
slides.append(page('<h2>🥇 ඉහළම මිල ලැබුණු ප්‍රදේශ 5</h2><div class="card">' +
                   "".join(f'<div class="row"><span><span class="rk">{n}</span>{nm(k)}</span><span class="n">රු. {rs(v)}</span></div>'
                           for n, (k, v) in enumerate(top, 1)) + f'</div><div class="note">{MONTH_SI} · මාසික සාමාන්‍යය</div>'))
if rises or falls:
    rows = "".join(f'<div class="row"><span>📈 {nm(k)}<span class="small">රු. {rs(a)} → {rs(b)}</span></span><span class="n up">+{p:.0f}%</span></div>' for k, a, b, p in rises)
    rows += "".join(f'<div class="row"><span>📉 {nm(k)}<span class="small">රු. {rs(a)} → {rs(b)}</span></span><span class="n dn">{p:.0f}%</span></div>' for k, a, b, p in falls)
    slides.append(page(f'<h2>පෙර මාසයට සාපේක්ෂව<br><span style="font-size:36px;color:#e7d3a3">{MONTH_PREV_SI} → {MONTHS_SI[m - 1]}</span></h2>'
                       f'<div class="card">{rows}</div>'))
cmp_rows = ""
if up_now and low_now:
    cmp_rows += (f'<div class="row"><span>⛰️ උඩරට / මැදරට<span class="small">සාමාන්‍යය</span></span><span class="n">රු. {rs(up_now)}</span></div>'
                 f'<div class="row"><span>🌴 පහතරට<span class="small">සාමාන්‍යය</span></span><span class="n">රු. {rs(low_now)}</span></div>')
if ly_pct is not None:
    cmp_rows += (f'<div class="row"><span>📅 පසුගිය වසරේ මේ මාසය<span class="small">රු. {rs(all_ly)} → {rs(all_now)}</span></span>'
                 f'<span class="n {"up" if ly_pct >= 0 else "dn"}">{ly_pct:+.1f}%</span></div>')
if cmp_rows:
    slides.append(page(f'<h2>සාමාන්‍ය මිල — {MONTH_SI}</h2><div class="card">{cmp_rows}</div>'))
slides.append(page(f'<h2>👉 ඔබේ ප්‍රදේශයේ තේ මිල</h2><div class="big" style="font-size:72px">topgoviya.lk/tea</div>'
                   f'<div class="sub">උප දිස්ත්‍රික්ක {len(cur)} · 2023 සිට මාසික මිල · සිංහල · தமிழ் · English</div>'
                   '<div class="cta">'
                   '<div class="ct"><span class="ci">👍</span><span>ලයික් කරන්න</span></div>'
                   '<div class="ct"><span class="ci">💬</span><span>ඔබේ ප්‍රදේශයේ තේ මිල කමෙන්ට් කරන්න</span></div>'
                   '<div class="ct"><span class="ci">📤</span><span>තේ වවන ඔබේ මිතුරන්ට ෂෙයාර් කරන්න</span></div>'
                   '<div class="ct"><span class="ci">🔔</span><span>සෑම මසකම තේ මිල සඳහා ෆලෝ කරන්න</span></div>'
                   '</div>'
                   f'<div class="note">දත්ත: ශ්‍රී ලංකා තේ මණ්ඩලය · මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.</div>'))

# ---- slides -> video
from playwright.sync_api import sync_playwright
pngs = []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for n, html in enumerate(slides):
        pg.set_content(html, wait_until="load"); pg.wait_for_timeout(400)
        f = f"{OUT}/tea{n:02d}.png"; pg.screenshot(path=f); pngs.append(f)
    b.close()
n = len(pngs); inputs = []
for f in pngs: inputs += ["-loop", "1", "-t", str(SLIDE_SEC), "-i", f]
chain, last, off = [], "[0:v]", 0.0
for k in range(1, n):
    off += SLIDE_SEC - FADE
    chain.append(f"{last}[{k}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[v{k}]"); last = f"[v{k}]"
chain.append(f"{last}format=yuv420p,fps=30[outv]")
silent = f"{OUT}/tea-silent.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                "-map", "[outv]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", silent], check=True)
for f in pngs: os.remove(f)
seconds = n * SLIDE_SEC - (n - 1) * FADE

folder = f"{OUT}/01-tea-{CUR}"
os.makedirs(folder, exist_ok=True)
shutil.move(silent, f"{folder}/video-silent.mp4")
if os.path.exists(MUSIC):
    af = (f"[1:a]atrim=0:{seconds:.2f},asetpts=PTS-STARTPTS,volume={MUSIC_VOL},"
          f"afade=t=in:st=0:d=1,afade=t=out:st={max(seconds - 2, 0):.2f}:d=2[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{folder}/video-silent.mp4", "-stream_loop", "-1", "-i", MUSIC,
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", f"{folder}/video-with-music.mp4"], check=True)
else:
    print("No music file", MUSIC, "- only the silent video is made")
    shutil.copy(f"{folder}/video-silent.mp4", f"{folder}/video-with-music.mp4")

# ---- captions
link = f"{SITE}?d={CUR}"
tops = "\n".join(f"{'🥇🥈🥉'[k] if k < 3 else '▫️'} {nm(a)}: රු. {rs(v)}" for k, (a, v) in enumerate(top[:3]))
mv = ([f"📈 {nm(k)}: රු. {rs(a)} → {rs(b)} ({p:+.0f}%)" for k, a, b, p in rises[:1]] +
      [f"📉 {nm(k)}: රු. {rs(a)} → {rs(b)} ({p:+.0f}%)" for k, a, b, p in falls[:1]])
lyline = f"📊 සාමාන්‍යය: පසුගිය වසරේ මේ මාසයේ රු. {rs(all_ly)}, මේ වසරේ රු. {rs(all_now)} ({ly_pct:+.1f}%)" if ly_pct is not None else ""
tags = "#තේමිල #TeaPrices #CeylonTea #SriLanka #TopGoviyaLK"
note = "ℹ️ සැකසූ තේ (Made tea) වෙන්දේසි මාසික සාමාන්‍යය (රු./කි.ග්‍රෑ.) — දළු (කොළ) මිල නොවේ."
title = f"තේ මිල {MONTH_SI} | උප දිස්ත්‍රික්ක {len(cur)} | Sri Lanka Tea Auction Prices | Tea Board #shorts"
desc = (f"🍃 තේ වෙන්දේසි මිල — {MONTH_SI}\n\nඉහළම මිල ලැබුණු ප්‍රදේශ:\n{tops}\n\n" + "\n".join(mv) +
        (f"\n{lyline}" if lyline else "") + f"\n\n{note}\n\n👉 ඔබේ ප්‍රදේශයේ මිල: {link}\n"
        "📊 දත්ත: ශ්‍රී ලංකා තේ මණ්ඩලය (Sri Lanka Tea Board)\n⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n"
        f"{tags} #shorts")
open(f"{folder}/youtube.txt", "w", encoding="utf-8").write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n")
open(f"{folder}/tiktok.txt", "w", encoding="utf-8").write(
    f"🍃 තේ වෙන්දේසි මිල — {MONTH_SI}\n{tops}\n" + "\n".join(mv) +
    f"\nසියලු ප්‍රදේශ 👉 topgoviya.lk/tea · දත්ත: ශ්‍රී ලංකා තේ මණ්ඩලය\nසැකසූ තේ මිල — දළු මිල නොවේ.\n\n{tags} #තේ #fyp\n")
open(f"{folder}/facebook.txt", "w", encoding="utf-8").write(
    f"🍃 තේ වෙන්දේසි මිල — {MONTH_SI}\n\nඉහළම මිල ලැබුණු ප්‍රදේශ:\n{tops}\n\n" + "\n".join(mv) +
    (f"\n{lyline}" if lyline else "") + f"\n\n{note}\n\n👉 ඔබේ ප්‍රදේශයේ මිල සහ පසුගිය මාස: {link}\n"
    "📊 දත්ත: ශ්‍රී ලංකා තේ මණ්ඩලය\n⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.\n\n" + tags + " #තේගොවි\n")
print(f"Ready-to-post folder: {folder} ({n} slides, ~{seconds:.0f}s)")
