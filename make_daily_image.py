"""
make_daily_image.py  -  TopGoviya.lk daily price image for WhatsApp / Facebook
-------------------------------------------------------------------------------
Makes ONE branded image after each new CBSL report:
  share/today.png    1080 x 1350, "අද එළවළු මිල" - Dambulla wholesale + retail,
                     change vs the previous report, date, source, QR code
  share/today-wide.png  1200 x 630 preview shown when a topgoviya.lk link is shared
  share/today-story.png 1080 x 1920 for WhatsApp Status / Facebook & Instagram Stories
  share/spice-<name>.png  1200 x 630 preview for each spice page (redrawn when DEA publishes a new week)
  share/today.json   which report the image was made from (so it is only redrawn
                     when there is a new report)

The image is always at the same address: https://topgoviya.lk/share/today.png
(overwritten each time, so the repository grows only ~150 KB per report).

  python make_daily_image.py --check   prints need=yes / need=no (for the robot)
  python make_daily_image.py           makes the image

Drawn with Chrome (Playwright) like the video robots, so Sinhala letters join correctly.
Uses build_pages.py (same folder) for names, dates and number formats.
"""
import io, json, os, sys
from datetime import datetime

from build_pages import NAMES, EMOJIS, fdate, money

OUT_DIR = "share"
PNG = os.path.join(OUT_DIR, "today.png")
WIDE = os.path.join(OUT_DIR, "today-wide.png")   # 1200 x 630 link preview (WhatsApp / Facebook)
STORY = os.path.join(OUT_DIR, "today-story.png") # 1080 x 1920 WhatsApp Status / Facebook Story
STATE = os.path.join(OUT_DIR, "today.json")
STYLE_VERSION = "5"            # change to force a redraw after a design change
MARKET = "Dambulla"
MAX_ROWS = 13
# items shown first, in this order (others from the report follow if there is room)
ORDER = ["Beans", "Carrot", "Cabbage", "Tomato", "Brinjal", "Pumpkin", "Snake gourd", "Green Chilli",
         "Lime", "Big Onion (Local)", "Red Onion (Local)", "Potato (Local)", "Coconut (Avg.)"]


def si(n): return (NAMES.get(n) or {}).get("si", n)


def rows_for(db):
    """Dambulla items reported in the latest CBSL report: (name, wholesale, retail, change %)."""
    dates = db["dates"]
    li = len(dates) - 1
    out = []
    for c in db["commodities"]:
        if c.get("primaryMarket") != MARKET:
            continue
        s = c.get("series") or []
        if len(s) <= li or s[li] is None:
            continue
        retail = s[li]
        prev = next((s[i] for i in range(li - 1, -1, -1) if s[i] is not None), None)
        chg = (retail - prev) / prev * 100 if prev else None
        w = None
        if c.get("wholesaleMarket", MARKET) == MARKET:
            ws = c.get("wholesaleSeries") or []
            w = ws[li] if len(ws) > li else None
        if w is None:
            w = (c.get("wholesaleMarkets") or {}).get(MARKET)
        out.append((c["name"], w, retail, chg, c.get("unit", "Rs./kg")))
    rank = {n: i for i, n in enumerate(ORDER)}
    out.sort(key=lambda r: rank.get(r[0], 99))
    return out[:MAX_ROWS], datetime.strptime(dates[li], "%Y-%m-%d").date()


def qr_svg(url):
    try:
        import qrcode, qrcode.image.svg
        img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=1)
        buf = io.BytesIO(); img.save(buf)
        return buf.getvalue().decode().split("?>", 1)[-1]
    except Exception:
        return ""


def page_html(rows, d, logo):
    def chg_html(c):
        if c is None:
            return '<span class="chg flat">—</span>'
        cls = "flat" if abs(c) < 0.5 else ("up" if c > 0 else "down")
        arrow = {"up": "▲", "down": "▼", "flat": "■"}[cls]
        return f'<span class="chg {cls}">{arrow} {"+" if c > 0 else ""}{c:.0f}%</span>'

    movers = [r for r in rows if r[3] is not None]
    up = max(movers, key=lambda r: r[3], default=None)
    dn = min(movers, key=lambda r: r[3], default=None)
    strip = ""
    if up and up[3] >= 0.5:
        strip += f'<span class="up">▲ වැඩිම ඉහළ: {si(up[0])} +{up[3]:.0f}%</span>'
    if dn and dn[3] <= -0.5:
        strip += f'<span class="down">▼ වැඩිම පහළ: {si(dn[0])} {dn[3]:.0f}%</span>'

    trs = ""
    for name, w, r, c, unit in rows:
        u = "" if unit == "Rs./kg" else ' <small>(ගෙඩියකට)</small>' if "Nut" in unit else f" <small>({unit})</small>"
        trs += (f'<tr><td class="nm"><span class="em">{EMOJIS.get(name, "🌿")}</span>{si(name)}{u}</td>'
                f'<td class="n w">{money(w) if w is not None else "—"}</td>'
                f'<td class="n r">{money(r)}</td><td class="n">{chg_html(c)}</td></tr>')

    return f"""<!DOCTYPE html><html lang="si"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1350px;background:#f4efe4;font-family:'Noto Sans Sinhala',sans-serif;color:#191d1a;overflow:hidden}}
.mono,.n{{font-family:'JetBrains Mono',monospace}}
.top{{background:#0e4f4a;color:#fff;display:flex;align-items:center;gap:20px;padding:24px 44px}}
.top img{{width:76px;height:76px;border-radius:16px;background:#fff}}
.top .b{{font-size:38px;font-weight:700}} .top .s{{font-size:22px;color:#e7d3a3}}
.head{{padding:18px 44px 4px}}
.head h1{{font-size:60px;line-height:1.12;color:#0e4f4a;font-weight:700}}
.head .sub{{font-size:26px;color:#3a403a;margin-top:2px}}
.date{{display:inline-block;margin-top:10px;background:#a9802a;color:#fff;font-size:28px;font-weight:700;border-radius:999px;padding:8px 28px}}
.strip{{display:flex;gap:12px;flex-wrap:wrap;margin:12px 44px 0}}
.strip span{{font-size:22px;font-weight:700;border-radius:10px;padding:6px 14px}}
.strip .up{{background:#f7e6e2;color:#b23a2e}} .strip .down{{background:#e3efe6;color:#2c7a52}}
table{{width:calc(100% - 88px);margin:12px 44px 0;border-collapse:collapse;background:#fffdf7;border-radius:18px;overflow:hidden}}
th{{font-size:21px;color:#7a7264;font-weight:700;padding:10px 16px;background:#efe8d8;text-align:right}}
th:first-child{{text-align:left}}
td{{padding:6px 16px;border-top:1px solid #e3d9c4;font-size:29px;font-weight:700}}
td.nm{{font-size:29px}} td.nm small{{font-size:18px;color:#7a7264;font-weight:400}}
.em{{display:inline-block;width:42px}}
td.n{{text-align:right;white-space:nowrap}} td.w{{color:#a9802a}} td.r{{color:#191d1a}}
.chg{{font-size:21px;border-radius:8px;padding:3px 9px}}
.up .chg,.chg.up{{color:#b23a2e;background:#f7e6e2}} .chg.down{{color:#2c7a52;background:#e3efe6}} .chg.flat{{color:#8a8170;background:#efeada}}
.foot{{position:absolute;left:44px;right:44px;bottom:26px;display:flex;gap:22px;align-items:center;border-top:2px solid #cdbf9f;padding-top:18px}}
.foot svg{{width:130px;height:130px;flex:0 0 130px;background:#fff;border-radius:12px;padding:6px}}
.foot .u{{font-size:34px;font-weight:700;color:#0e4f4a}}
.foot .t{{font-size:20px;color:#3a403a;line-height:1.5}}
</style></head><body>
<div class="top">{f'<img src="{logo}">' if logo else ''}<div><div class="b">TopGoviya.lk</div><div class="s">දත්තය බලලා තීරණ ගන්න</div></div></div>
<div class="head"><h1>අද එළවළු මිල</h1>
<div class="sub">දඹුල්ල වෙළඳපොළ · තොග හා සිල්ලර · රු. / කි.ග්‍රෑ.</div>
<div class="date">{fdate(d, 'si')} · මහ බැංකු වාර්තාව</div></div>
<div class="strip">{strip}</div>
<table><thead><tr><th>භාණ්ඩය</th><th>තොග</th><th>සිල්ලර</th><th>වෙනස*</th></tr></thead><tbody>{trs}</tbody></table>
<div class="foot">{qr_svg("https://topgoviya.lk/")}<div>
<div class="u">topgoviya.lk</div>
<div class="t">සියලු මිල, වෙළඳපොළ 10ක තොග මිල, කුළුබඩු මිල හා ගණක — නොමිලේ.<br>
දත්ත: ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව · *වෙනස = පෙර වාර්තාවට සාපේක්ෂව (සිල්ලර).<br>
මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.</div></div></div>
</body></html>"""


def wide_html(rows, d, logo):
    """1200 x 630 preview shown when a topgoviya.lk link is shared."""
    def chg(c):
        if c is None: return ""
        cls = "flat" if abs(c) < 0.5 else ("up" if c > 0 else "down")
        return f'<span class="chg {cls}">{ {"up": "▲", "down": "▼", "flat": "■"}[cls] } {"+" if c > 0 else ""}{c:.0f}%</span>'
    trs = "".join(f'<tr><td class="nm"><span class="em">{EMOJIS.get(n, "🌿")}</span>{si(n)}</td>'
                  f'<td class="n">රු. {money(r)}</td><td class="n">{chg(c)}</td></tr>' for n, w, r, c, u in rows[:6])
    return f"""<!DOCTYPE html><html lang="si"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;display:flex;font-family:'Noto Sans Sinhala',sans-serif;background:#f4efe4;overflow:hidden}}
.l{{width:430px;background:#0e4f4a;color:#fff;padding:40px 36px;display:flex;flex-direction:column}}
.l img{{width:84px;height:84px;border-radius:18px;background:#fff}}
.l h1{{font-size:62px;line-height:1.15;margin:26px 0 14px;font-weight:700}}
.l .date{{display:inline-block;background:#a9802a;border-radius:999px;padding:8px 20px;font-size:25px;font-weight:700;align-self:flex-start}}
.l .sub{{font-size:22px;color:#e7d3a3;margin-top:14px}}
.l .u{{margin-top:auto;font-size:36px;font-weight:700}}
.r{{flex:1;padding:30px 36px}}
.r h2{{font-size:24px;color:#7a7264;font-weight:700;margin-bottom:8px}}
table{{width:100%;border-collapse:collapse;background:#fffdf7;border-radius:16px;overflow:hidden}}
td{{padding:12px 16px;border-top:1px solid #e3d9c4;font-size:34px;font-weight:700;color:#191d1a}}
tr:first-child td{{border-top:0}}
.em{{display:inline-block;width:52px}}
td.n{{text-align:right;white-space:nowrap;font-family:'JetBrains Mono',monospace}}
.chg{{font-size:24px;border-radius:8px;padding:3px 10px}}
.chg.up{{color:#b23a2e;background:#f7e6e2}} .chg.down{{color:#2c7a52;background:#e3efe6}} .chg.flat{{color:#8a8170;background:#efeada}}
.r .src{{font-size:19px;color:#7a7264;margin-top:10px}}
</style></head><body>
<div class="l">{f'<img src="{logo}">' if logo else ''}<h1>අද එළවළු මිල</h1>
<div class="date">{fdate(d, 'si')}</div><div class="sub">දඹුල්ල සිල්ලර මිල · රු./කි.ග්‍රෑ.</div>
<div class="u">topgoviya.lk</div></div>
<div class="r"><h2>දඹුල්ල වෙළඳපොළ · පෙර වාර්තාවට සාපේක්ෂව</h2><table>{trs}</table>
<div class="src">දත්ත: ශ්‍රී ලංකා මහ බැංකුව · සියලු මිල topgoviya.lk හි</div></div>
</body></html>"""


def story_html(rows, d, logo):
    """1080 x 1920 for WhatsApp Status / Stories. Content kept in the middle,
    away from the app's own name bar (top) and reply bar (bottom)."""
    def chg(c):
        if c is None: return '<span class="chg flat">—</span>'
        cls = "flat" if abs(c) < 0.5 else ("up" if c > 0 else "down")
        return f'<span class="chg {cls}">{ {"up": "▲", "down": "▼", "flat": "■"}[cls] } {"+" if c > 0 else ""}{c:.0f}%</span>'
    trs = "".join(f'<tr><td class="nm"><span class="em">{EMOJIS.get(n, "🌿")}</span>{si(n)}</td>'
                  f'<td class="n w">{money(w) if w is not None else "—"}</td><td class="n r">{money(r)}</td>'
                  f'<td class="n">{chg(c)}</td></tr>' for n, w, r, c, u in rows[:11])
    return f"""<!DOCTYPE html><html lang="si"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1920px;background:#0e4f4a;font-family:'Noto Sans Sinhala',sans-serif;overflow:hidden;position:relative}}
.safe{{position:absolute;top:200px;left:50px;right:50px;bottom:230px;display:flex;flex-direction:column}}
.brand{{display:flex;align-items:center;gap:18px;color:#fff}}
.brand img{{width:78px;height:78px;border-radius:16px;background:#fff}}
.brand b{{font-size:40px}} .brand span{{display:block;font-size:22px;color:#e7d3a3;font-weight:400}}
h1{{color:#fff;font-size:104px;line-height:1.1;margin:34px 0 12px;font-weight:700}}
.date{{align-self:flex-start;background:#a9802a;color:#fff;font-size:36px;font-weight:700;border-radius:999px;padding:10px 32px}}
.sub{{color:#e7d3a3;font-size:28px;margin:16px 0 22px}}
table{{width:100%;border-collapse:collapse;background:#fffdf7;border-radius:24px;overflow:hidden}}
th{{font-size:24px;color:#7a7264;padding:12px 18px;background:#efe8d8;text-align:right}} th:first-child{{text-align:left}}
td{{padding:12px 18px;border-top:1px solid #e3d9c4;font-size:38px;font-weight:700;color:#191d1a}}
.em{{display:inline-block;width:56px}}
td.n{{text-align:right;white-space:nowrap;font-family:'JetBrains Mono',monospace}} td.w{{color:#a9802a}}
.chg{{font-size:26px;border-radius:10px;padding:4px 10px}}
.chg.up{{color:#b23a2e;background:#f7e6e2}} .chg.down{{color:#2c7a52;background:#e3efe6}} .chg.flat{{color:#8a8170;background:#efeada}}
.foot{{margin-top:auto;display:flex;gap:22px;align-items:center;color:#fff}}
.foot svg{{width:150px;height:150px;flex:0 0 150px;background:#fff;border-radius:16px;padding:8px}}
.foot .u{{font-size:52px;font-weight:700}} .foot .t{{font-size:24px;color:#e7d3a3;line-height:1.5}}
</style></head><body><div class="safe">
<div class="brand">{f'<img src="{logo}">' if logo else ''}<div><b>TopGoviya.lk</b><span>දත්තය බලලා තීරණ ගන්න</span></div></div>
<h1>අද එළවළු මිල</h1>
<div class="date">{fdate(d, 'si')}</div>
<div class="sub">දඹුල්ල වෙළඳපොළ · තොග හා සිල්ලර · රු./කි.ග්‍රෑ.</div>
<table><thead><tr><th>භාණ්ඩය</th><th>තොග</th><th>සිල්ලර</th><th>වෙනස</th></tr></thead><tbody>{trs}</tbody></table>
<div class="foot">{qr_svg("https://topgoviya.lk/")}<div><div class="u">topgoviya.lk</div>
<div class="t">සියලු මිල නොමිලේ · දත්ත: මහ බැංකුව<br>මිල ගණන් මඟපෙන්වීමක් පමණි.</div></div></div>
</div></body></html>"""


SPICE_STATE = os.path.join(OUT_DIR, "spices.json")
SPICE_STYLE = "1"


def spice_preview_html(sp, dea, logo):
    """1200 x 630 link preview for one spice page (spice/<slug>.html)."""
    from build_spice_pages import nat, chg, d_, UNIT_EN
    from datetime import timedelta
    c, G = sp["c"], sp["grades"]
    N = lambda w, g: nat(w, g, "Average", c)
    weeks = [w for w in dea["weeks"] if N(w, G[0][0])]
    cur, prev = weeks[-1], weeks[-2]
    d = d_(cur["date"])
    rows = ""
    for key, gsi, gen, unit in G[:3]:
        a, ap = N(cur, key), N(prev, key)
        if not a:
            continue
        t, cls, _ = chg(a, ap)
        per = "" if unit == "kg" or "100" in gsi else f' <small>({"ගෙඩි 100" if unit == "100 nuts" else unit})</small>'
        rows += (f'<tr><td class="nm">{gsi}{per}</td><td class="n">රු. {money(a)}</td>'
                 f'<td class="n">{f"""<span class="chg {cls}">{t}</span>""" if t else ""}</td></tr>')
    ya = next((w for w in weeks if abs((d_(w["date"]) - (d - timedelta(days=364))).days) <= 4), None)
    yv = N(ya, G[0][0]) if ya else None
    year_line = f'වසරකට පෙර ({G[0][1]}): රු. {money(yv)}' if yv else ""
    return f"""<!DOCTYPE html><html lang="si"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;display:flex;font-family:'Noto Sans Sinhala',sans-serif;background:#f4efe4;overflow:hidden}}
.l{{width:450px;background:#0e4f4a;color:#fff;padding:38px 36px;display:flex;flex-direction:column}}
.l img{{width:80px;height:80px;border-radius:18px;background:#fff}}
.l .em{{font-size:64px;margin-top:18px;line-height:1}}
.l h1{{font-size:64px;line-height:1.15;margin:10px 0 14px;font-weight:700}}
.l .date{{display:inline-block;background:#a9802a;border-radius:999px;padding:8px 20px;font-size:24px;font-weight:700;align-self:flex-start}}
.l .sub{{font-size:22px;color:#e7d3a3;margin-top:12px}}
.l .u{{margin-top:auto;font-size:34px;font-weight:700}}
.r{{flex:1;padding:44px 36px;display:flex;flex-direction:column}}
.r h2{{font-size:24px;color:#7a7264;font-weight:700;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;background:#fffdf7;border-radius:16px;overflow:hidden}}
td{{padding:18px 18px;border-top:1px solid #e3d9c4;font-size:34px;font-weight:700;color:#191d1a}}
tr:first-child td{{border-top:0}} td small{{font-size:20px;color:#7a7264;font-weight:400}}
td.n{{text-align:right;white-space:nowrap;font-family:'JetBrains Mono',monospace}}
.chg{{font-size:24px;border-radius:8px;padding:3px 10px}}
.chg.up{{color:#b23a2e;background:#f7e6e2}} .chg.down{{color:#2c7a52;background:#e3efe6}} .chg.flat{{color:#8a8170;background:#efeada}}
.r .yr{{font-size:24px;color:#3a403a;margin-top:16px}}
.r .src{{font-size:19px;color:#7a7264;margin-top:auto}}
</style></head><body>
<div class="l">{f'<img src="{logo}">' if logo else ''}<div class="em">{sp["emo"]}</div><h1>{sp["si"]} මිල අද</h1>
<div class="date">{fdate(d, 'si')} සතිය</div><div class="sub">ගොවිපළ මිල · රු./{ "ගෙඩි 100" if G[0][3] == "100 nuts" else "කි.ග්‍රෑ." }</div>
<div class="u">topgoviya.lk</div></div>
<div class="r"><h2>{sp["en"]} · farm gate · national average</h2><table>{rows}</table>
<div class="yr">{year_line}</div>
<div class="src">දත්ත: අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුව (DEA) · පෙර වාර්තාවට සාපේක්ෂව</div></div>
</body></html>"""


def dea_week():
    try:
        return json.load(open("dea_data.json", encoding="utf-8"))["weeks"][-1]["date"]
    except Exception:
        return None


def spices_wanted():
    """True when DEA has a new week (or a new design) since the last spice previews."""
    wk = dea_week()
    if not wk:
        return False
    try:
        from build_spice_pages import SPICES
        st = json.load(open(SPICE_STATE, encoding="utf-8"))
        have = all(os.path.exists(os.path.join(OUT_DIR, f"spice-{s['slug']}.png")) for s in SPICES)
        return not (st.get("week") == wk and st.get("style") == SPICE_STYLE and have)
    except Exception:
        return True


def make_spice_previews(pg, logo):
    from build_spice_pages import SPICES
    dea = json.load(open("dea_data.json", encoding="utf-8"))
    made = []
    pg.set_viewport_size({"width": 1200, "height": 630})
    for sp in SPICES:
        try:
            html = spice_preview_html(sp, dea, logo)
        except Exception as e:
            print(f"  {sp['slug']}: skipped ({e})"); continue
        out = os.path.join(OUT_DIR, f"spice-{sp['slug']}.png")
        pg.set_content(html, wait_until="load"); pg.wait_for_timeout(300)
        pg.screenshot(path=out); made.append(out)
    json.dump({"week": dea_week(), "style": SPICE_STYLE, "pages": len(made)},
              open(SPICE_STATE, "w", encoding="utf-8"), ensure_ascii=False)
    return made


def wanted(db):
    """True when there is a new report (or a new design) since the last image."""
    try:
        st = json.load(open(STATE, encoding="utf-8"))
        return not (st.get("date") == db["dates"][-1] and st.get("style") == STYLE_VERSION
                    and os.path.exists(PNG) and os.path.exists(WIDE) and os.path.exists(STORY))
    except Exception:
        return True


def main():
    db = json.load(open("data.json", encoding="utf-8"))
    need_veg, need_spice = wanted(db), spices_wanted()
    if "--check" in sys.argv:
        print("need=" + ("yes" if (need_veg or need_spice) else "no"))
        return
    if not (need_veg or need_spice):
        print("Images already up to date for report", db["dates"][-1], "and DEA week", dea_week()); return
    rows, d = rows_for(db)
    if need_veg and len(rows) < 5:
        print("Not enough Dambulla prices in the latest report - no vegetable image made."); need_veg = False

    import base64
    from playwright.sync_api import sync_playwright
    logo = ""
    if os.path.exists("icon-512x512.png"):
        logo = "data:image/png;base64," + base64.b64encode(open("icon-512x512.png", "rb").read()).decode()
    os.makedirs(OUT_DIR, exist_ok=True)
    made = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        if need_veg:
            pg.set_content(page_html(rows, d, logo), wait_until="load")
            pg.wait_for_timeout(500)
            pg.screenshot(path=PNG)
            pg.set_viewport_size({"width": 1200, "height": 630})
            pg.set_content(wide_html(rows, d, logo), wait_until="load")
            pg.wait_for_timeout(500)
            pg.screenshot(path=WIDE)
            pg.set_viewport_size({"width": 1080, "height": 1920})
            pg.set_content(story_html(rows, d, logo), wait_until="load")
            pg.wait_for_timeout(500)
            pg.screenshot(path=STORY)
            made += [PNG, WIDE, STORY]
        if need_spice:
            made += make_spice_previews(pg, logo)
        b.close()
    try:                                   # smaller files, look the same
        from PIL import Image
        for f in made:
            Image.open(f).convert("RGB").quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(f, optimize=True)
    except Exception as e:
        print("note: PNG not compressed:", e)
    if need_veg:
        json.dump({"date": db["dates"][-1], "style": STYLE_VERSION, "items": len(rows)},
                  open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Made {len(made)} image(s): " + ", ".join(os.path.basename(f) for f in made))


if __name__ == "__main__":
    main()
