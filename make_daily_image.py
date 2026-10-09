"""
make_daily_image.py  -  TopGoviya.lk daily price image for WhatsApp / Facebook
-------------------------------------------------------------------------------
Makes ONE branded image after each new CBSL report:
  share/today.png    1080 x 1350, "අද එළවළු මිල" - Dambulla wholesale + retail,
                     change vs the previous report, date, source, QR code
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
STATE = os.path.join(OUT_DIR, "today.json")
STYLE_VERSION = "2"            # change to force a redraw after a design change
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


def wanted(db):
    """True when there is a new report (or a new design) since the last image."""
    try:
        st = json.load(open(STATE, encoding="utf-8"))
        return not (st.get("date") == db["dates"][-1] and st.get("style") == STYLE_VERSION and os.path.exists(PNG))
    except Exception:
        return True


def main():
    db = json.load(open("data.json", encoding="utf-8"))
    if "--check" in sys.argv:
        print("need=" + ("yes" if wanted(db) else "no"))
        return
    if not wanted(db):
        print("Image already up to date for report", db["dates"][-1]); return
    rows, d = rows_for(db)
    if len(rows) < 5:
        print("Not enough Dambulla prices in the latest report - no image made."); return

    import base64
    from playwright.sync_api import sync_playwright
    logo = ""
    if os.path.exists("icon-512x512.png"):
        logo = "data:image/png;base64," + base64.b64encode(open("icon-512x512.png", "rb").read()).decode()
    os.makedirs(OUT_DIR, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.set_content(page_html(rows, d, logo), wait_until="load")
        pg.wait_for_timeout(500)
        pg.screenshot(path=PNG)
        b.close()
    try:                                   # smaller file, looks the same
        from PIL import Image
        Image.open(PNG).convert("RGB").quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(PNG, optimize=True)
    except Exception as e:
        print("note: PNG not compressed:", e)
    json.dump({"date": db["dates"][-1], "style": STYLE_VERSION, "items": len(rows)},
              open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Made {PNG} for report {db['dates'][-1]} ({len(rows)} items, {os.path.getsize(PNG)//1024} KB)")


if __name__ == "__main__":
    main()
