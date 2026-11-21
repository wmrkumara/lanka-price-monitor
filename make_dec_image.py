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
STYLE_VERSION = "14"                # change to force a redraw after a design change
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
    # English line (Nov 2026): for English searches like "dambulla market price today" / "dambulla market price list today"
    unit_en = {"kg": "kg", "nut": "nut", "bundle": "bundle"}
    en_parts = []
    for _, k in rows[:20]:
        lo, hi = day[k]
        en_parts.append(f"{names[k]['en']} Rs. {money(lo)}–{money(hi)} / {unit_en.get(names[k]['unit'], 'kg')}")
    d = date.fromisoformat(last)
    en_date = f"{d.day} {d.strftime('%B')} {d.year}"
    en = ('<p lang="en"><b>Dambulla market price today — ' + en_date + "</b> (Dambulla Dedicated Economic Centre wholesale price list, "
          "min–max, today's vegetable prices in Sri Lanka): " + " · ".join(en_parts)
          + " — full Dambulla market price list of " + str(len(day)) + " items above (tap EN at the top for English)."
          + ' <a href="en/dambulla-market-price-today.html">Dambulla market price today in English →</a></p>')
    return ("<p><b>දඹුල්ල එලවලු මිල අද — " + si_date(last) + "</b> (දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය, තොග මිල, අවම–උපරිම): "
            + " · ".join(parts) + " — භාණ්ඩ " + str(len(day)) + " ක සම්පූර්ණ ලැයිස්තුව ඉහත.</p>" + en
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
        if p == "index.html" and 'hreflang="en"' not in s2:
            s2 = s2.replace('<link rel="canonical" href="https://topgoviya.lk/">',
                            '<link rel="canonical" href="https://topgoviya.lk/">\n' + HREFLANG, 1)
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
     "words": "දඹුල්ල පලතුරු මිල today · දඹුල්ලේ පලතුරු තොග මිල ගණන් · අන්නාසි, පැපොල්, කෙසෙල්, අඹ, දොඩම් මිල"},
]
UNIT_SI = {"kg": "කි.ග්‍රෑ.", "nut": "ගෙඩිය", "bundle": "මිටිය"}
# DEC item (English name) -> existing CBSL retail/wholesale page with a longer history
PRICE_PAGES = {"Coconut": "price/coconut-avg.html", "Papaya": "price/papaw.html", "Pineapple": "price/pineapple.html",
               "Banana (Ambul)": "price/banana-sour.html"}


def cat_page_html(cfg, db, names, last):
    order = sorted(db["days"])
    prev = order[order.index(last) - 1] if order.index(last) > 0 else None
    day, pday = db["days"][last], (db["days"][prev] if prev else {})
    rows, movers = [], []
    for k, m in sorted(names.items(), key=lambda kv: kv[1]["pop"]):
        if m.get("cat") != cfg["cat"] or not day.get(k):
            continue
        lo, hi = day[k]
        mid = (lo + hi) / 2
        ch, pc = "", None
        if pday.get(k):
            pm = sum(pday[k]) / 2
            if pm:
                pc = (mid - pm) / pm * 100
                cls = "up" if pc >= 0.5 else "dn" if pc <= -0.5 else "fl"
                ch = f'<span class="{cls}">{"▲" if cls == "up" else "▼" if cls == "dn" else "■"} {pc:+.0f}%</span>'
        u = "" if m["unit"] == "kg" else f' <small>/ {UNIT_SI.get(m["unit"], "")}</small>'
        nm = f'{m["si"]} <small>{m["en"]}</small>'
        if m["en"] in PRICE_PAGES:
            nm = f'<a href="{PRICE_PAGES[m["en"]]}">{m["si"]}</a> <small>{m["en"]}</small>'
        movers.append((pc if pday.get(k) and sum(pday[k]) else None, m, lo, hi, pday.get(k)))
        rows.append(f'<tr><td>{nm}</td><td class="n">{money(lo)} – {money(hi)}{u}</td>'
                    f'<td class="n">{money(mid)}</td><td class="n">{ch or "—"}</td></tr>')
    mv = [x for x in movers if x[0] is not None]
    up = max(mv, key=lambda x: x[0]) if mv else None
    dn = min(mv, key=lambda x: x[0]) if mv else None
    same = sum(1 for x in mv if abs(x[0]) < 0.5)
    def mvtxt(x, word):
        pc, m, lo, hi, p = x
        return (f'{word}: <b>{m["si"]}</b> රු. {money(p[0])}–{money(p[1])} → <b>රු. {money(lo)}–{money(hi)}</b> '
                f'({pc:+.0f}%)')
    summ = []
    if up and up[0] >= 0.5: summ.append("📈 " + mvtxt(up, "වැඩිම ඉහළ යාම"))
    if dn and dn[0] <= -0.5: summ.append("📉 " + mvtxt(dn, "වැඩිම පහළ යාම"))
    summ.append(f"■ වෙනසක් නැති පලතුරු: {same}")
    summary_html = '<div class="sum">' + "<br>".join(summ) + "</div>"
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
.sum{{background:#fffdf7;border:1px solid #e3d9c4;border-radius:12px;padding:12px 14px;margin:0 0 14px;font-size:15px;line-height:1.8}}.src{{font-size:13px;color:#6f675a;margin:0 0 8px}}h2{{color:#0e4f4a;font-size:19px;margin:22px 0 6px}}
@media(max-width:520px){{th:nth-child(3),td:nth-child(3){{display:none}}th,td{{padding:9px 8px;font-size:14px}}h1{{font-size:26px}}}}
</style></head><body>
<div class="top"><a href="./">🥬 TopGoviya.lk</a><a href="./">දඹුල්ල මිල</a><a href="retail.html">📊 CBSL</a></div>
<main class="w">
<h1>{cfg["emoji"]} {cfg["h1"]}</h1>
<p class="sub">Dambulla {cfg["en"].lower()} price today · {cfg["words"]}</p>
<span class="pill">නවතම මිල: <b>{si_date(last)}</b></span><span class="pill">{len(rows)} භාණ්ඩ</span>
<p>දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ {si_date(last)} දින {cfg["si"]} තොග මිල (රු. / කි.ග්‍රෑ.; පොල් හා තැඹිලි ගෙඩියට). සාමාන්‍ය = (අවම + උපරිම) ÷ 2. වෙනස පෙර වාර්තාවට ({si_date(prev) if prev else "—"}) සාපේක්ෂව.</p>
{summary_html}
<p class="src">මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · වාර්තා දිනය: {si_date(last)} · ඒකකය: රු. / කි.ග්‍රෑ. (පොල්, තැඹිලි: ගෙඩියට) · තොග මිල; ප්‍රභේදය, ශ්‍රේණිය හා ප්‍රමාණය අනුව සැබෑ මිල වෙනස් විය හැක.</p>
<div style="overflow-x:auto"><table><thead><tr><th>භාණ්ඩය</th><th class="n">අවම – උපරිම</th><th class="n">සාමාන්‍ය</th><th class="n">පෙර වාර්තාවට<br><small>({si_date(prev) if prev else "—"})</small></th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<a class="cta" href="./">🥬 සියලු භාණ්ඩ 90+ ක අද මිල, ප්‍රස්ථාර හා ලාභ ගණකය →</a>
<h2>නිතර අසන ප්‍රශ්න</h2>
<p><b>මේවා සිල්ලර මිලද?</b> නැත — දඹුල්ල වෙළඳපොළේ තොග මිල (අවම – උපරිම). කඩවල සිල්ලර මිල ප්‍රවාහන හා වෙනත් වියදම් නිසා වැඩි විය හැක. සිල්ලර මිල සඳහා <a href="retail.html">CBSL සිල්ලර මිල</a> බලන්න.</p>
<p><b>පොල් හා තැඹිලි මිල කිලෝවටද?</b> නැත — ගෙඩියකට.</p>
<p><b>මෙම මිල යාවත්කාලීන වන්නේ කවදාද?</b> සති අන්ත ඇතුළුව දිනපතා. ඉහත දැක්වෙන්නේ නවතම වාර්තාවේ දිනයයි.</p>
<h2 lang="en">Dambulla fruit prices today</h2>
<p lang="en">Official wholesale minimum and maximum fruit prices from the Dambulla Dedicated Economic Centre, Sri Lanka, in rupees per kilogram (coconut and king coconut per nut), with the change since the previous report. Prices are indicative and differ from shop retail prices.</p>
<p lang="ta">தம்புள்ள பழ விலை இன்று — தம்புள்ள விசேட பொருளாதார மையத்தின் மொத்த விலைகள் (குறைந்த – அதிக), ரூ./கி.கி; தேங்காய், செவ்விளநீர் காய்க்கு.</p>
<p>🥬 <a href="./">දඹුල්ල එලවලු මිල අද</a> · 📊 <a href="retail.html">CBSL සිල්ලර මිල</a> · 🧺 <a href="market/peliyagoda.html">පෑලියගොඩ මිල</a></p>
<p class="note">මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය (Dambulla DEC) · <a href="data-sources.html">මිල ලබාගන්නා ආකාරය</a><br>
මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ. · © TopGoviya.lk</p>
</main></body></html>
"""


# ---------------------------------------------------------------- English Dambulla page (Nov 2026 pilot)
EN_FILE = "en/dambulla-market-price-today.html"
EN_URL = "https://topgoviya.lk/" + EN_FILE
HREFLANG = ('<link rel="alternate" hreflang="si" href="https://topgoviya.lk/">\n'
            '<link rel="alternate" hreflang="en" href="' + EN_URL + '">\n'
            '<link rel="alternate" hreflang="x-default" href="https://topgoviya.lk/">')
EN_CATS = [("v", "🥬 Vegetables"), ("l", "🌿 Leafy vegetables"), ("r", "🥔 Potatoes & roots"),
           ("g", "🌾 Grains & pulses"), ("f", "🍍 Fruits")]
EN_UNIT = {"kg": "kg", "nut": "nut", "bundle": "bundle"}


def en_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B')} {d.year}"


def en_slug(en):
    return re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")


def en_page_html(db, names, last):
    order = sorted(db["days"])
    i = order.index(last)
    prev = order[i - 1] if i > 0 else None
    day, pday = db["days"][last], (db["days"][prev] if prev else {})
    known = set(os.listdir("dambulla")) if os.path.isdir("dambulla") else set()
    tables, moves, total = [], [], 0
    for c, label in EN_CATS:
        rows = []
        for k, m in sorted(names.items(), key=lambda kv: kv[1].get("pop_cat", 999)):
            if m.get("cat") != c or not day.get(k):
                continue
            lo, hi = day[k]
            mid = (lo + hi) / 2
            ch, pc = "—", None
            if pday.get(k) and sum(pday[k]):
                pc = (mid - sum(pday[k]) / 2) / (sum(pday[k]) / 2) * 100
                cls = "up" if pc >= 0.5 else "dn" if pc <= -0.5 else "fl"
                ch = f'<span class="{cls}">{"▲" if cls == "up" else "▼" if cls == "dn" else "■"} {pc:+.0f}%</span>'
                moves.append((pc, m, lo, hi))
            nm = m["en"]
            sl = en_slug(m["en"]) + ".html"
            if sl in known:
                nm = f'<a href="../dambulla/{sl}">{m["en"]}</a>'
            u = EN_UNIT.get(m.get("unit"), "kg")
            rows.append(f'<tr><td>{m.get("e", "")} {nm} <small>{m["si"]}</small></td><td class="n">{money(lo)} – {money(hi)}'
                        f'<small> /{u}</small></td><td class="n">{money(mid)}</td><td class="n">{ch}</td></tr>')
        if rows:
            total += len(rows)
            tables.append(f'<h2>{label} <small>({len(rows)})</small></h2><div class="tw"><table><thead><tr><th>Item</th>'
                          f'<th class="n">Min – Max (Rs.)</th><th class="n">Average</th><th class="n">vs previous</th></tr></thead>'
                          f'<tbody>{"".join(rows)}</tbody></table></div>')
    up = sum(1 for x in moves if x[0] >= 0.5)
    dn = sum(1 for x in moves if x[0] <= -0.5)
    same = len(moves) - up - dn
    hi_m = max(moves, key=lambda x: x[0]) if moves else None
    lo_m = min(moves, key=lambda x: x[0]) if moves else None
    # market mood bar (same idea as the home page): average change of all items
    avg = sum(max(-100, min(100, x[0])) for x in moves) / len(moves) if moves else 0
    mood_t = "🔴 A higher-price day" if avg >= 3 else "🟢 A lower-price day" if avg <= -3 else "🟡 A normal day"
    nn = len(moves) or 1
    w = lambda n: f"{n / nn * 100:.1f}%"
    new_items = total - len(moves)
    mood_html = (f'<div class="mood"><p class="mt">{mood_t}</p><div class="gbar">'
                 f'<span style="width:{w(up)};background:#b23a2e"></span><span style="width:{w(same)};background:#cdbf9f"></span>'
                 f'<span style="width:{w(dn)};background:#2c7a52"></span></div><div class="glab">'
                 f'<span><i style="background:#b23a2e"></i>Up {up}</span><span><i style="background:#cdbf9f"></i>Unchanged {same}</span>'
                 f'<span><i style="background:#2c7a52"></i>Down {dn}</span>'
                 + (f'<span><i style="background:transparent;border:1px dashed #cdbf9f"></i>No previous price {new_items}</span>' if new_items > 0 else "")
                 + '</div></div>')
    summ = [f"Compared with the previous report ({en_date(prev) if prev else '—'}): <b>{up}</b> items up, <b>{dn}</b> down, <b>{same}</b> unchanged."]
    if hi_m and hi_m[0] >= 0.5:
        summ.append(f"📈 Biggest rise: <b>{hi_m[1]['en']}</b> Rs. {money(hi_m[2])}–{money(hi_m[3])} ({hi_m[0]:+.0f}%)")
    if lo_m and lo_m[0] <= -0.5:
        summ.append(f"📉 Biggest fall: <b>{lo_m[1]['en']}</b> Rs. {money(lo_m[2])}–{money(lo_m[3])} ({lo_m[0]:+.0f}%)")
    top = sorted((v["pop"], k) for k, v in names.items() if day.get(k))[:6]
    top_txt = ", ".join(f"{names[k]['en']} Rs. {money(day[k][0])}–{money(day[k][1])}" for _, k in top)
    d = date.fromisoformat(last)
    ds = f"{d.day} {d.strftime('%b')} {d.year}"
    title = f"Dambulla Market Price Today – {ds} | Vegetable Price List Sri Lanka | TopGoviya"
    desc = (f"Dambulla market price today ({en_date(last)}): wholesale prices of {total} vegetables, fruits, roots and grains at the "
            f"Dambulla Dedicated Economic Centre, Sri Lanka — min–max, average and change since the previous report.")
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": f"Dambulla market price today — {en_date(last)}",
                     "url": EN_URL, "inLanguage": "en", "dateModified": last,
                     "isPartOf": {"@type": "WebSite", "name": "TopGoviya.lk", "url": "https://topgoviya.lk/"},
                     "about": {"@type": "Place", "name": "Dambulla Dedicated Economic Centre",
                               "address": {"@type": "PostalAddress", "addressLocality": "Dambulla", "addressCountry": "LK"}}},
                    ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{EN_URL}">
{HREFLANG}
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{EN_URL}"><meta property="og:type" content="website"><meta property="og:locale" content="en_GB">
<meta property="og:image" content="https://topgoviya.lk/share/dambulla-wide.png?v={last}">
<link rel="icon" href="../icon-192x192.png"><meta name="theme-color" content="#0e4f4a">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ZBN8Z32S4J"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-ZBN8Z32S4J');</script>
<script type="application/ld+json">{ld}</script>
<style>
body{{margin:0;background:#f4efe4;color:#191d1a;font-family:'Hanken Grotesk','Noto Sans Sinhala',system-ui,sans-serif;line-height:1.55}}
.top{{background:#0a3a36;border-bottom:2px solid #a9802a;padding:10px 14px;display:flex;flex-wrap:wrap;gap:6px}}
.top a{{color:#fff;text-decoration:none;font-weight:700;font-size:14px;padding:6px 10px;border-radius:8px;background:rgba(255,255,255,.1)}}
.top a.b{{background:#a9802a}}
.w{{max-width:860px;margin:0 auto;padding:16px}}h1{{color:#0e4f4a;font-size:30px;line-height:1.2;margin:8px 0 4px}}
.sub{{color:#6f675a;margin:0 0 12px}}.pill{{display:inline-block;background:#fffdf7;border:1px solid #e3d9c4;border-radius:999px;padding:5px 12px;margin:0 6px 6px 0;font-size:14px}}
.ans{{background:#fffdf7;border:1px solid #e3d9c4;border-left:4px solid #0e4f4a;border-radius:10px;padding:10px 12px;margin:8px 0 12px}}
.mood{{background:#fffdf7;border:1px solid #cdbf9f;border-radius:14px;padding:12px 14px;margin:0 0 10px}}.mood .mt{{font-size:19px;font-weight:700;margin:0 0 8px}}
.gbar{{display:flex;height:12px;border-radius:7px;overflow:hidden;background:#ece4d2}}.gbar span{{display:block;height:100%}}
.glab{{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:#6f675a;margin-top:6px}}.glab i{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}}
.sum{{background:#fffdf7;border:1px solid #e3d9c4;border-radius:12px;padding:12px 14px;margin:0 0 6px;line-height:1.8}}
.tw{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:#fffdf7;border:1px solid #e3d9c4}}
th,td{{padding:9px 10px;border-bottom:1px solid #eee5d3;text-align:left;font-size:15px}}th{{background:#efe8d8;font-size:13px}}
td small{{color:#6f675a;font-size:12px}}.n{{text-align:right;font-family:'JetBrains Mono',monospace;white-space:nowrap}}
.up{{color:#b23a2e}}.dn{{color:#2c7a52}}.fl{{color:#8a8170}}
h2{{color:#0e4f4a;font-size:20px;margin:22px 0 8px}}h2 small{{color:#6f675a;font-size:14px;font-weight:500}}
.cta{{display:inline-block;margin:16px 8px 0 0;background:#0e4f4a;color:#fff;padding:11px 16px;border-radius:10px;text-decoration:none;font-weight:700}}
.cta.g{{background:#a9802a}}.note{{font-size:13px;color:#6f675a}}a{{color:#0e4f4a}}
@media(max-width:520px){{th:nth-child(3),td:nth-child(3){{display:none}}th,td{{padding:8px 6px;font-size:14px}}h1{{font-size:25px}}}}
</style></head><body>
<nav class="top"><a class="b" href="../">🥬 TopGoviya.lk</a><a href="../market/keppetipola.html">Keppetipola</a><a href="../spices.html">Spices</a><a href="../tea.html">Tea</a><a href="../">සිංහල</a></nav>
<main class="w">
<h1>Dambulla Market Price Today</h1>
<p class="sub">Dambulla vegetable price list · Sri Lanka wholesale prices · {en_date(last)}</p>
<span class="pill">Latest report: <b>{en_date(last)}</b></span><span class="pill">{total} items</span><span class="pill">Rs. per kg (coconut per nut)</span>
<p class="ans">📌 On <b>{en_date(last)}</b>, wholesale prices at the Dambulla Dedicated Economic Centre included {top_txt} (Rs. per kg; coconut per nut).</p>
{mood_html}
<div class="sum">{"<br>".join(summ)}</div>
{"".join(tables)}
<a class="cta" href="../">📈 Charts, price history and profit calculator →</a><a class="cta g" href="../">සිංහලෙන් බලන්න →</a>
<h2>About these prices</h2>
<p><b>What is the Dambulla market price?</b> It is the daily wholesale price range (minimum – maximum) published by the Dambulla Dedicated Economic Centre, one of Sri Lanka's main wholesale vegetable markets. Average = (min + max) ÷ 2.</p>
<p><b>Are these retail prices?</b> No. Shop (retail) prices are higher because of transport and other costs. For retail prices see <a href="../retail.html">CBSL retail prices</a>.</p>
<p><b>How often is it updated?</b> Every day, including weekends. The date above is the date of the latest report.</p>
<p>Other markets: <a href="../market/keppetipola.html">Keppetipola market price today</a> · <a href="../market/peliyagoda.html">Peliyagoda</a> · <a href="../dambulla-fruit-price.html">Dambulla fruit price today</a> · <a href="../wholesale.html">HARTI wholesale prices</a></p>
<p class="note">Source: Dambulla Dedicated Economic Centre (Dambulla DEC) · <a href="../data-sources.html">How we get prices</a><br>
Prices are indicative only. Decisions are your responsibility. · © TopGoviya.lk</p>
</main><script defer src="/events.js?v=1"></script></body></html>
"""


def write_en_page(db, last):
    try:
        names = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    except Exception as ex:
        print("English page skipped:", ex)
        return
    os.makedirs("en", exist_ok=True)
    with open(EN_FILE, "w", encoding="utf-8") as f:
        f.write(en_page_html(db, names, last))
    print("Wrote", EN_FILE)
    if os.path.exists("sitemap.xml"):
        sm = open("sitemap.xml", encoding="utf-8").read()
        if EN_URL in sm:
            sm = re.sub(r"(<loc>" + re.escape(EN_URL) + r"</loc>\s*<lastmod>)[^<]*", r"\g<1>" + last, sm)
        else:
            sm = sm.replace("</urlset>", f"  <url><loc>{EN_URL}</loc><lastmod>{last}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n</urlset>")
        open("sitemap.xml", "w", encoding="utf-8").write(sm)


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
        # the home page and dambulla.html also show today's Dambulla prices: tell Google they changed today
        # (20 Nov 2026: the home page date was stuck at 2026-09-29 although it changes every day)
        for loc in ("https://topgoviya.lk/", "https://topgoviya.lk/dambulla.html"):
            if "<loc>" + loc + "</loc>" in sm:
                sm = re.sub(r"(<loc>" + re.escape(loc) + r"</loc>\s*<lastmod>)[^<]*", r"\g<1>" + last, sm)
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
    write_en_page(db, last)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state_now(db), f)
    print(f"Made {WIDE} for {last} ({len(rows)} items).")


if __name__ == "__main__":
    main()
