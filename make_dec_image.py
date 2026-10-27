"""
make_dec_image.py  -  TopGoviya.lk link preview image for the Dambulla DEC page
------------------------------------------------------------------------------
Makes share/dambulla-wide.png (1200 x 630): the picture WhatsApp / Facebook show
when someone shares the Dambulla page link. It shows today's DEC wholesale price
range for 8 popular items, with the change vs the previous report.

Also updates the og:image address inside dambulla.html (?v=date) so Facebook and
WhatsApp show the new picture instead of an old saved copy.

  python make_dec_image.py --check   prints need=yes / need=no (for the robot)
  python make_dec_image.py           makes the image

Drawn with Chrome (Playwright) like make_daily_image.py, so Sinhala letters join correctly.
"""
import json, os, re, sys
from datetime import date

DATA = "dambulla_dec.json"
OUT_DIR = "share"
WIDE = os.path.join(OUT_DIR, "dambulla-wide.png")
STATE = os.path.join(OUT_DIR, "dambulla-wide.json")
PAGES = ["index.html"]          # pages whose og:image is refreshed
STYLE_VERSION = "8"                # change to force a redraw after a design change
ROWS = 8

# DEC product id -> (Sinhala name, emoji), in popular order. Coconut is left out
# until its unit (per nut / per kg) is confirmed.
POPULAR = [
    ("11", "තක්කාලි", "🍅"), ("70", "ලොකු ළූණු (ආනයනික)", "🧅"), ("67", "අමු මිරිස්", "🌶️"),
    ("26", "වම්බටු", "🍆"), ("4", "බෝංචි", "🫛"), ("6", "කැරට්", "🥕"),
    ("69", "රතු ළූණු (දේශීය)", "🧅"), ("15", "අර්තාපල් (නුවරඑළිය)", "🥔"),
    ("20", "අර්තාපල් (ආනයනික)", "🥔"), ("1", "ගෝවා", "🥬"), ("22", "බණ්ඩක්කා", "🫑"),
    ("27", "දෙහි", "🍋"), ("47", "සුදු ළූණු", "🧄"), ("23", "පතෝල", "🥒"),
]
MONTHS = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි",
          "අගෝස්තු", "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]


def si_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.year} {MONTHS[d.month - 1]} {d.day}"


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def state_now(db):
    return {"date": db.get("latest_date"), "style": STYLE_VERSION}


def need(db):
    if not db.get("latest_date"):
        return False
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f) != state_now(db)
    except Exception:
        return True


def rows_for(db):
    days = sorted(db["days"])
    last = days[-1]
    prev = days[-2] if len(days) > 1 else None
    out = []
    for pid, name, emoji in POPULAR:
        v = db["days"][last].get(pid)
        if not v:
            continue
        mid = (v[0] + v[1]) / 2
        chg = None
        if prev and db["days"][prev].get(pid):
            p = db["days"][prev][pid]
            pm = (p[0] + p[1]) / 2
            chg = (mid - pm) / pm * 100 if pm else None
        out.append((emoji, name, v[0], v[1], chg))
        if len(out) == ROWS:
            break
    return out, last


def money(n):
    return f"{n:,.0f}"


def page_html(rows, last):
    trs = []
    for emoji, name, lo, hi, chg in rows:
        if chg is None or abs(chg) < 0.5:
            badge = '<span class="c flat">■</span>'
        elif chg > 0:
            badge = f'<span class="c up">▲ {chg:.0f}%</span>'
        else:
            badge = f'<span class="c down">▼ {abs(chg):.0f}%</span>'
        trs.append(f'<div class="r"><span class="n">{emoji} {name}</span>'
                   f'<span class="p">{money(lo)}–{money(hi)}</span>{badge}</div>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;display:flex;font-family:'Noto Sans Sinhala',sans-serif;background:#fffdf7;color:#191d1a}}
.l{{flex:0 0 420px;background:#0e4f4a;color:#fff;padding:44px 40px;display:flex;flex-direction:column}}
.brand{{color:#d4ad55;font:700 26px 'Noto Sans Sinhala',sans-serif;letter-spacing:.02em}}
h1{{font-size:62px;line-height:1.12;margin-top:34px;font-weight:800}}
.sub{{font-size:27px;opacity:.9;margin-top:10px}}
.d{{display:inline-block;margin-top:26px;background:#d4ad55;color:#0a3a36;font-weight:800;font-size:28px;padding:8px 18px;border-radius:12px}}
.url{{margin-top:auto;font:700 30px 'Noto Sans Sinhala',sans-serif}}
.rt{{flex:1;min-width:0;padding:30px 40px 24px;display:flex;flex-direction:column}}
.hd{{display:flex;justify-content:space-between;font-size:21px;color:#6f675a;border-bottom:3px solid #a9802a;padding-bottom:8px;margin-bottom:6px}}
.r{{display:flex;align-items:center;height:62px;border-bottom:1px solid #e3d9c4}}
.r:nth-child(even){{background:#f7f2e7}}
.n{{flex:1;min-width:0;font-size:28px;font-weight:600;padding-left:6px;white-space:nowrap;overflow:hidden}}
.p{{font:700 29px 'JetBrains Mono',monospace;flex:0 0 190px;text-align:right}}
.c{{font:700 22px 'JetBrains Mono',monospace;flex:0 0 105px;text-align:right;padding-right:6px}}
.up{{color:#b23a2e}}.down{{color:#2c7a52}}.flat{{color:#8a8170}}
.ft{{margin-top:auto;font-size:18px;color:#6f675a}}
</style></head><body>
<div class="l"><div class="brand">TopGoviya.lk</div><h1>දඹුල්ල<br>තොග මිල</h1>
<div class="sub">අද එළවළු මිල<br>රු. / කි.ග්‍රෑ.</div><div class="d">{si_date(last)}</div>
<div class="url">🌐 topgoviya.lk</div></div>
<div class="rt"><div class="hd"><span>භාණ්ඩය</span><span>අවම – උපරිම · පෙර දිනට</span></div>
{''.join(trs)}
<div class="ft">මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය</div></div>
</body></html>"""


def seo_today_html(db, last):
    """Plain-text list of today's popular prices for search engines (and readers) — between
    <!--SEO-TODAY--> markers in index.html."""
    try:
        names = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    except Exception:
        return None
    unit = {"kg": "කි.ග්‍රෑ.", "nut": "ගෙඩිය", "bundle": "මිටිය"}
    day = db["days"][last]
    rows = sorted((v["pop"], k) for k, v in names.items() if k in day and day[k])
    parts = []
    for _, k in rows[:30]:
        lo, hi = day[k]
        parts.append(f"{names[k]['si']} රු. {money(lo)}–{money(hi)} / {unit.get(names[k]['unit'], 'කි.ග්‍රෑ.')}")
    return ("<p><b>දඹුල්ල එලවලු මිල අද — " + si_date(last) + "</b> (දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය, තොග මිල, අවම–උපරිම): "
            + " · ".join(parts) + " — භාණ්ඩ " + str(len(day)) + " ක සම්පූර්ණ ලැයිස්තුව ඉහත.</p>"
            + '<p>🍍 <a href="dambulla-fruit-price.html">දඹුල්ල පලතුරු මිල අද</a> (Dambulla fruit price today)</p>')


def refresh_pages(last, db=None):
    for p in PAGES:
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        s2 = re.sub(r"(share/dambulla-wide\.png\?v=)[0-9-]+", r"\g<1>" + last, s)
        d = date.fromisoformat(last)
        new_title = f"දඹුල්ල එලවලු මිල අද {d.year}.{d.month:02d}.{d.day:02d} | Dambulla Market Price Today | TopGoviya"
        s2 = re.sub(r"<title>[^<]*</title>", "<title>" + new_title + "</title>", s2, count=1)
        if db is not None:
            seo = seo_today_html(db, last)
            if seo:
                s2 = re.sub(r"<!--SEO-TODAY-->.*?<!--/SEO-TODAY-->", lambda m: "<!--SEO-TODAY-->" + seo + "<!--/SEO-TODAY-->", s2, flags=re.S)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            print(f"Updated preview address in {p}")


# ---------------------------------------------------------------- category pages (plain HTML, for Google)
CAT_PAGES = [
    {"cat": "f", "file": "dambulla-fruit-price.html", "emoji": "🍍",
     "si": "පලතුරු", "en": "Fruit", "h1": "දඹුල්ල පලතුරු මිල අද",
     "words": "දඹුල්ල පලතුරු මිල today · අන්නාසි, පැපොල්, කෙසෙල්, අඹ, දොඩම් මිල"},
]
UNIT_SI = {"kg": "කි.ග්‍රෑ.", "nut": "ගෙඩිය", "bundle": "මිටිය"}


def cat_page_html(cfg, db, names, last):
    order = sorted(db["days"])
    prev = order[order.index(last) - 1] if order.index(last) > 0 else None
    day, pday = db["days"][last], (db["days"][prev] if prev else {})
    rows = []
    for k, m in sorted(names.items(), key=lambda kv: kv[1]["pop"]):
        if m.get("cat") != cfg["cat"] or not day.get(k):
            continue
        lo, hi = day[k]
        mid = (lo + hi) / 2
        ch = ""
        if pday.get(k):
            pm = sum(pday[k]) / 2
            if pm:
                pc = (mid - pm) / pm * 100
                cls = "up" if pc >= 0.5 else "dn" if pc <= -0.5 else "fl"
                ch = f'<span class="{cls}">{"▲" if cls == "up" else "▼" if cls == "dn" else "■"} {pc:+.0f}%</span>'
        u = "" if m["unit"] == "kg" else f' <small>/ {UNIT_SI.get(m["unit"], "")}</small>'
        rows.append(f'<tr><td>{m["si"]} <small>{m["en"]}</small></td><td class="n">{money(lo)} – {money(hi)}{u}</td>'
                    f'<td class="n">{money(mid)}</td><td class="n">{ch or "—"}</td></tr>')
    d = date.fromisoformat(last)
    ds = f"{d.year}.{d.month:02d}.{d.day:02d}"
    title = f'{cfg["h1"]} {ds} | Dambulla {cfg["en"]} Price Today | TopGoviya'
    desc = (f'{cfg["h1"]} — දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ {si_date(last)} {cfg["si"]} {len(rows)} ක තොග මිල (අවම–උපරිම) හා පෙර දිනට වෙනස. '
            f'Dambulla {cfg["en"].lower()} wholesale prices today, Sri Lanka.')
    url = "https://topgoviya.lk/" + cfg["file"]
    return f"""<!DOCTYPE html>
<html lang="si"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}"><meta property="og:type" content="website">
<meta property="og:image" content="https://topgoviya.lk/share/dambulla-wide.png?v={last}">
<link rel="icon" href="icon-192x192.png"><meta name="theme-color" content="#0e4f4a">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ZBN8Z32S4J"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-ZBN8Z32S4J');</script>
<style>
body{{margin:0;background:#f4efe4;color:#191d1a;font-family:'Noto Sans Sinhala','Hanken Grotesk',system-ui,sans-serif;line-height:1.55}}
.top{{background:#0e4f4a;padding:12px 18px}}.top a{{color:#fff;text-decoration:none;font-weight:700;margin-right:14px}}
.w{{max-width:860px;margin:0 auto;padding:18px}}h1{{color:#0e4f4a;font-size:30px;margin:10px 0 2px}}
.sub{{color:#6f675a;margin:0 0 14px}}.pill{{display:inline-block;background:#fffdf7;border:1px solid #e3d9c4;border-radius:999px;padding:5px 12px;margin:0 6px 6px 0;font-size:14px}}
table{{width:100%;border-collapse:collapse;background:#fffdf7;border:1px solid #e3d9c4;border-radius:12px;overflow:hidden}}
th,td{{padding:10px 12px;border-bottom:1px solid #eee5d3;text-align:left;font-size:15px}}th{{background:#efe8d8;font-size:13px}}
td small{{color:#6f675a}}.n{{text-align:right;font-family:'JetBrains Mono',monospace;white-space:nowrap}}
.up{{color:#b23a2e}}.dn{{color:#2c7a52}}.fl{{color:#8a8170}}
.cta{{display:inline-block;margin:16px 0;background:#0e4f4a;color:#fff;padding:11px 16px;border-radius:10px;text-decoration:none;font-weight:700}}
.note{{font-size:13px;color:#6f675a}}a{{color:#0e4f4a}}
@media(max-width:520px){{th:nth-child(3),td:nth-child(3){{display:none}}th,td{{padding:9px 8px;font-size:14px}}h1{{font-size:26px}}}}
</style></head><body>
<div class="top"><a href="./">🥬 TopGoviya.lk</a><a href="./">දඹුල්ල මිල</a><a href="retail.html">📊 CBSL</a></div>
<main class="w">
<h1>{cfg["emoji"]} {cfg["h1"]}</h1>
<p class="sub">Dambulla {cfg["en"].lower()} price today · {cfg["words"]}</p>
<span class="pill">නවතම මිල: <b>{si_date(last)}</b></span><span class="pill">{len(rows)} භාණ්ඩ</span>
<p>දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ {si_date(last)} දින {cfg["si"]} තොග මිල (රු. / කි.ග්‍රෑ.; පොල් හා තැඹිලි ගෙඩියට). සාමාන්‍ය = (අවම + උපරිම) ÷ 2. වෙනස පෙර වාර්තාවට ({si_date(prev) if prev else "—"}) සාපේක්ෂව.</p>
<div style="overflow-x:auto"><table><thead><tr><th>භාණ්ඩය</th><th class="n">අවම – උපරිම</th><th class="n">සාමාන්‍ය</th><th class="n">පෙර දිනට</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<a class="cta" href="./">🥬 සියලු භාණ්ඩ 90+ ක අද මිල, ප්‍රස්ථාර හා ලාභ ගණකය →</a>
<p class="note">මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය (Dambulla DEC) · <a href="data-sources.html">මිල ලබාගන්නා ආකාරය</a><br>
මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ. · © TopGoviya.lk</p>
</main></body></html>
"""


def write_cat_pages(db, last):
    try:
        names = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    except Exception as ex:
        print("Category pages skipped:", ex)
        return
    for cfg in CAT_PAGES:
        with open(cfg["file"], "w", encoding="utf-8") as f:
            f.write(cat_page_html(cfg, db, names, last))
        print("Wrote", cfg["file"])
    # make sure the pages are in the sitemap (other entries are left as they are)
    if os.path.exists("sitemap.xml"):
        sm = open("sitemap.xml", encoding="utf-8").read()
        for cfg in CAT_PAGES:
            loc = "https://topgoviya.lk/" + cfg["file"]
            if loc in sm:
                sm = re.sub(r"(<loc>" + re.escape(loc) + r"</loc>\s*<lastmod>)[^<]*", r"\g<1>" + last, sm)
            else:
                sm = sm.replace("</urlset>", f"  <url><loc>{loc}</loc><lastmod>{last}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>\n</urlset>")
        open("sitemap.xml", "w", encoding="utf-8").write(sm)


def main():
    db = load()
    if "--check" in sys.argv:
        print("need=" + ("yes" if need(db) else "no"))
        return
    rows, last = rows_for(db)
    if not rows:
        print("No prices to draw.")
        return
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT_DIR, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        pg.set_content(page_html(rows, last))
        pg.wait_for_timeout(400)
        pg.screenshot(path=WIDE)
        b.close()
    refresh_pages(last, db)
    write_cat_pages(db, last)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state_now(db), f)
    print(f"Made {WIDE} for {last} ({len(rows)} items).")


if __name__ == "__main__":
    main()
