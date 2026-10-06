"""
build_market_pages.py  -  TopGoviya.lk market pages
---------------------------------------------------
Reads harti_data.json (+ data.json for CBSL Dambulla) and writes:
  market/<market>.html        one Google-friendly page per HARTI market (10)
  market/index.html           hub page listing all 10 markets
  harti_market_history.json   small per-market price history (kept 120 days)
  sitemap.xml                 keeps every other page, adds/refreshes /market/ pages

Runs daily from GitHub Actions after harti_update.py.
Uses build_pages.py (same folder) for the shared look, and only the
Python standard library.
"""
import json, os, re
from datetime import datetime, timedelta

from build_pages import CSS, GA_ID, SITE, e, money, fdate, slug, MONTHS, NAMES as CBSL_NAMES, EMOJIS

OUT_DIR = "market"
HIST_FILE = "harti_market_history.json"
KEEP_DAYS = 120
HARTI_URL = "https://www.harti.gov.lk/daily-price.php"
CBSL_URL = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report"

# ---------------------------------------------------------------- names (same as live wholesale.html)
MKT = {
    "Peliyagoda":      {"si": "පෑලියගොඩ",    "ta": "பேலியகோட",    "slug": "peliyagoda"},
    "Kandy":           {"si": "මහනුවර",      "ta": "கண்டி",        "slug": "kandy"},
    "Dambulla":        {"si": "දඹුල්ල",      "ta": "தம்புள்ள",     "slug": "dambulla"},
    "Meegoda":         {"si": "මීගොඩ",       "ta": "மீகொட",       "slug": "meegoda"},
    "Norochchole":     {"si": "නොරොච්චෝලේ", "ta": "நொரோச்சோலே",  "slug": "norochchole"},
    "Thambuththegama": {"si": "තඹුත්තේගම",   "ta": "தம்புத்தேகம",  "slug": "thambuththegama"},
    "Keppetipola":     {"si": "කෑප්පෙටිපොළ", "ta": "கெப்பெட்டிபொல", "slug": "keppetipola"},
    "Nuwaraeliya":     {"si": "නුවරඑළිය",    "ta": "நுவரெலியா",    "slug": "nuwara-eliya"},
    "Bandarawela":     {"si": "බණ්ඩාරවෙල",   "ta": "பண்டாரவெல",    "slug": "bandarawela"},
    "Veyangoda":       {"si": "වේයන්ගොඩ",    "ta": "வேயன்கொட",     "slug": "veyangoda"},
}
# English name people search for (Nuwaraeliya is written "Nuwara Eliya" in searches)
MKT_EN = {"Nuwaraeliya": "Nuwara Eliya"}

H_SI = {
 "Beans":"බෝංචි","Carrot":"කැරට්","Leeks":"ලීක්ස්","Beetroot":"බීට්රූට්",
 "Beetroot (N.Eliya)":"බීට්රූට් (නුවරඑළිය)","Knolkhol":"නෝල්කෝල්","Raddish":"රාබු",
 "Cabbage (N.Eliya)":"ගෝවා (නුවරඑළිය)","Cabbage (Kandy)":"ගෝවා (නුවර)","Tomato":"තක්කාලි",
 "Ladies Fingers":"බණ්ඩක්කා","Brinjals":"වම්බටු","Capsicum":"මාළු මිරිස්","Pumpkin":"වට්ටක්කා",
 "Cucumber":"පිපිඤ්ඤා","Bitter Gourd":"කරවිල","Snake Gourd":"පතෝල","Drumstick":"මුරුංගා",
 "Luffa":"වැටකොළු","Long Beans":"මෑකරල්","Ash Plantains":"අළු කෙසෙල්",
 "Green Chillies":"අමු මිරිස්","Lime":"දෙහි","Sweet Potato":"බතල","Manioc":"මඤ්ඤොක්කා",
 "Eggplant":"එළබටු","Potato (Imported)":"අර්තාපල් (ආනයනික)",
 "Potato (Welimada)":"අර්තාපල් (වැලිමඩ)","Potato (N.Eliya)":"අර්තාපල් (නුවරඑළිය)",
 "Big Onion (Imported)":"ලොකු ළූණු (ආනයනික)",
 "Banana Ambul":"ඇඹුල් කෙසෙල්","Banana Kolikuttu":"කොලිකුට්ටු","Banana Seeni":"සීනි කෙසෙල්",
 "Papaya":"පැපොල්","Pineapple (Large)":"අන්නාසි (ලොකු)","Avocado":"අලිගැටපේර",
 "Passion Fruit":"වැල් දොඩම්",
}
H_TA = {
 "Beans":"பீன்ஸ்","Carrot":"கேரட்","Leeks":"லீக்ஸ்","Beetroot":"பீட்ரூட்",
 "Beetroot (N.Eliya)":"பீட்ரூட் (நுவரெலியா)","Knolkhol":"நோல்கோல்","Raddish":"ராடிஷ்",
 "Cabbage (N.Eliya)":"முட்டைக்கோஸ் (நுவரெலியா)","Cabbage (Kandy)":"முட்டைக்கோஸ் (கண்டி)",
 "Tomato":"தக்காளி","Ladies Fingers":"வெண்டைக்காய்","Brinjals":"கத்தரிக்காய்",
 "Capsicum":"குடை மிளகாய்","Pumpkin":"பூசணி","Cucumber":"வெள்ளரிக்காய்",
 "Bitter Gourd":"பாகற்காய்","Snake Gourd":"புடலங்காய்","Drumstick":"முருங்கை",
 "Luffa":"பீர்க்கங்காய்","Long Beans":"தட்டைப்பயறு","Ash Plantains":"வாழைக்காய்",
 "Green Chillies":"பச்சை மிளகாய்","Lime":"எலுமிச்சை","Sweet Potato":"சர்க்கரைவள்ளி",
 "Manioc":"மரவள்ளி","Eggplant":"கத்திரிக்காய்",
 "Potato (Imported)":"உருளை (இறக்குமதி)","Potato (Welimada)":"உருளை (வெலிமட)",
 "Potato (N.Eliya)":"உருளை (நுவரெலியா)","Big Onion (Imported)":"பெரிய வெங்காயம் (இறக்குமதி)",
}
CAT_SI = {"Up Country Vegetables": "උඩරට එළවළු", "Low Country Vegetables": "පහතරට එළවළු",
          "Potatoes & Onions": "අර්තාපල් හා ළූණු", "Fruits & Banana": "පළතුරු හා කෙසෙල්"}
CAT_ORDER = ["Up Country Vegetables", "Low Country Vegetables", "Potatoes & Onions", "Fruits & Banana"]

# HARTI crop -> CBSL crop (to link to the /price/ page of the same crop)
TO_CBSL = {"Beans":"Beans","Carrot":"Carrot","Cabbage (Kandy)":"Cabbage","Cabbage (N.Eliya)":"Cabbage",
           "Tomato":"Tomato","Brinjals":"Brinjal","Pumpkin":"Pumpkin","Snake Gourd":"Snake gourd",
           "Green Chillies":"Green Chilli","Lime":"Lime","Potato (N.Eliya)":"Potato (Local)",
           "Potato (Welimada)":"Potato (Local)","Potato (Imported)":"Potato (Imp)",
           "Big Onion (Imported)":"Big Onion (Imp)","Beetroot":"Beetroot","Leeks":"Leeks",
           "Knolkhol":"Knol-khol","Drumstick":"Drumstick","Manioc":"Manioc","Ash Plantains":"Ash Plantain"}

def hsi(n): return H_SI.get(n, n)
def hta(n): return H_TA.get(n, n)
def men(m): return MKT_EN.get(m, m)
def d_(s): return datetime.strptime(s, "%Y-%m-%d").date()
def short(d): return f"{d.day} {MONTHS['en'][d.month-1][:3]}"

# ---------------------------------------------------------------- history
def update_history(harti):
    """Add today's per-market snapshot to harti_market_history.json; keep KEEP_DAYS."""
    hist = {"markets": {}}
    if os.path.exists(HIST_FILE):
        try:
            hist = json.load(open(HIST_FILE, encoding="utf-8"))
        except Exception:
            pass
    hm = hist.setdefault("markets", {})
    today = harti["dates"][-1]
    for c in harti["commodities"]:
        for m, v in (c.get("markets") or {}).items():
            if isinstance(v, dict) and v.get("mid") is not None:
                hm.setdefault(m, {}).setdefault(c["name"], {})[today] = [v.get("min"), v.get("max"), v["mid"]]
    cutoff = (d_(today) - timedelta(days=KEEP_DAYS)).isoformat()
    for m in hm:
        for n in list(hm[m]):
            hm[m][n] = {k: x for k, x in sorted(hm[m][n].items()) if k >= cutoff}
            if not hm[m][n]:
                del hm[m][n]
    hist["note"] = "Per-market HARTI wholesale history (min, max, mid) kept by build_market_pages.py"
    hist["updated"] = today
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return hm

def market_snapshot(hm, market):
    """Latest report date for this market and its items: {name: (min,max,mid)}."""
    items = hm.get(market, {})
    dates = sorted({d for x in items.values() for d in x})
    if not dates:
        return None, {}
    last = dates[-1]
    return last, {n: x[last] for n, x in items.items() if last in x}

def week_ago(series, last):
    """Mid price from the report about one week before `last` (5-9 days earlier, closest to 7)."""
    t = d_(last)
    best, gap = None, 99
    for k, v in series.items():
        days = (t - d_(k)).days
        if 5 <= days <= 9 and abs(days - 7) < gap:
            best, gap = (k, v), abs(days - 7)
    return best

# ---------------------------------------------------------------- CBSL Dambulla block
def cbsl_dambulla(cbsl):
    dates = cbsl["dates"]
    li = len(dates) - 1
    rows = []
    for c in cbsl["commodities"]:
        s = c.get("series") or []
        ws = c.get("wholesaleSeries") or []
        r = (c.get("markets") or {}).get("Dambulla")
        w = (c.get("wholesaleMarkets") or {}).get("Dambulla")
        r_ok = r is not None and len(s) > li and s[li] is not None
        w_ok = w is not None and len(ws) > li and ws[li] is not None
        if r_ok or w_ok:
            rows.append((c, w if w_ok else None, r if r_ok else None))
    return d_(dates[li]), rows

# ---------------------------------------------------------------- page shell
def shell(title, desc, canonical, body, jsonld):
    return f"""<!DOCTYPE html>
<html lang="si">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="TopGoviya.lk">
<meta name="theme-color" content="#0e4f4a">
<link rel="icon" type="image/png" sizes="192x192" href="../icon-192x192.png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Noto+Sans+Sinhala:wght@400;600&family=Noto+Sans+Tamil:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}
.rng{{font-size:12.5px;color:var(--muted);font-weight:500}}
td.mid{{font-family:'JetBrains Mono',monospace;font-weight:700;text-align:right;white-space:nowrap}}
.tip{{font-size:13.5px;color:var(--soft);background:var(--amberbg);border-radius:10px;padding:10px 13px;margin:10px 0 0}}
</style>
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="../index.html">TopGoviya.lk</a><a href="index.html">වෙළඳපොළ 10 / All markets</a></header>
{body}
<p class="note">මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.<br>
Prices are indicative only. Decisions are your responsibility. Wholesale prices: <a href="{HARTI_URL}" rel="noopener">HARTI daily wholesale price report</a>;
Dambulla retail and wholesale: <a href="{CBSL_URL}" rel="noopener">Central Bank of Sri Lanka daily price report</a>. Not an official publication.
<a href="../data-sources.html">How we collect the data →</a><br>
விலைகள் வழிகாட்டல் மட்டுமே. உங்கள் முடிவுகளுக்கு நீங்களே பொறுப்பு.</p>
<footer>Design &amp; development by <a href="https://ebooklanka.com" target="_blank" rel="noopener">ebooklanka.com</a> · Built in Gampola, Sri Lanka</footer>
</div>
</body>
</html>
"""

def crop_cell(name):
    cb = TO_CBSL.get(name)
    label = f'{EMOJIS.get(cb, "🌿") if cb else "🌿"} {e(hsi(name))}'
    if cb and os.path.exists(os.path.join("price", slug(cb) + ".html")):
        label = f'<a href="../price/{slug(cb)}.html">{label}</a>'
    return f'{label} <span style="color:var(--muted)">/ {e(name)}</span>'

def chg_badge(now, old):
    if old is None:
        return "—"
    dd = now - old
    pct = dd / old * 100 if old else 0
    cls = "flat" if abs(pct) < 0.5 else ("up" if dd > 0 else "down")
    arrow = {"up": "▲", "down": "▼", "flat": "■"}[cls]
    return f'<span class="chg {cls}" style="font-size:12px;padding:2px 7px">{arrow} {"+" if pct > 0 else ""}{pct:.0f}%</span>'

# ---------------------------------------------------------------- one market page
def market_page(market, hm, harti, cats, cbsl):
    info = MKT[market]
    si, ta, en = info["si"], info["ta"], men(market)
    last, snap = market_snapshot(hm, market)
    latest_all = harti["dates"][-1]
    url = f"{SITE}/{OUT_DIR}/{info['slug']}.html"

    # rows with weekly change
    rows = []
    for n, (mn, mx, mid) in snap.items():
        wk = week_ago(hm[market][n], last)
        rows.append({"name": n, "cat": cats.get(n, "Up Country Vegetables"), "min": mn, "max": mx, "mid": mid,
                     "wk": wk[1][2] if wk else None, "wkdate": wk[0] if wk else None})
    rows.sort(key=lambda r: (CAT_ORDER.index(r["cat"]) if r["cat"] in CAT_ORDER else 9, r["name"]))

    # where pays more today (same report date only, HARTI rule: highlight the highest to sell)
    better = []
    if last:
        for r in rows:
            best_m, best_v = None, r["mid"]
            for m2 in MKT:
                if m2 == market:
                    continue
                v = hm.get(m2, {}).get(r["name"], {}).get(last)
                if v and v[2] > best_v:
                    best_m, best_v = m2, v[2]
            if best_m and best_v >= r["mid"] * 1.10:
                better.append((r, best_m, best_v))
        better.sort(key=lambda x: (x[2] - x[0]["mid"]) / x[0]["mid"], reverse=True)

    movers = [r for r in rows if r["wk"]]
    up = sorted([r for r in movers if r["mid"] > r["wk"]], key=lambda r: (r["mid"] - r["wk"]) / r["wk"], reverse=True)
    dn = sorted([r for r in movers if r["mid"] < r["wk"]], key=lambda r: (r["mid"] - r["wk"]) / r["wk"])

    # ---- story in 3 languages
    if last:
        d = d_(last)
        s_si = f"{fdate(d,'si')} HARTI තොග මිල වාර්තාව අනුව {si} වෙළඳපොළේ භාණ්ඩ {len(rows)}ක තොග මිල පහත දැක්වේ (රු./කි.ග්‍රෑ.)."
        s_en = f"On {fdate(d,'en')}, the HARTI daily report listed wholesale prices for {len(rows)} items at {en} market (Rs. per kg)."
        s_ta = f"{fdate(d,'ta')} HARTI அறிக்கையின்படி {ta} சந்தையில் {len(rows)} பொருட்களின் மொத்த விலை (ரூ./கி.)."
        if up:
            r = up[0]
            s_si += f" සතියකට පෙර සිට වැඩිම ඉහළ යාම: {hsi(r['name'])} (රු. {money(r['wk'])} → රු. {money(r['mid'])})."
            s_en += f" Biggest weekly rise: {r['name']} (Rs. {money(r['wk'])} → Rs. {money(r['mid'])})."
            s_ta += f" வாராந்திர அதிக உயர்வு: {hta(r['name'])} (ரூ. {money(r['wk'])} → ரூ. {money(r['mid'])})."
        if dn:
            r = dn[0]
            s_si += f" වැඩිම පහළ යාම: {hsi(r['name'])} (රු. {money(r['wk'])} → රු. {money(r['mid'])})."
            s_en += f" Biggest weekly fall: {r['name']} (Rs. {money(r['wk'])} → Rs. {money(r['mid'])})."
            s_ta += f" அதிக வீழ்ச்சி: {hta(r['name'])} (ரூ. {money(r['wk'])} → ரூ. {money(r['mid'])})."
    else:
        s_si = f"{si} වෙළඳපොළ සඳහා මෑත HARTI මිල වාර්තා නොමැත."
        s_en = f"HARTI has not reported prices for {en} market recently."
        s_ta = f"{ta} சந்தைக்கு சமீபத்திய HARTI விலைகள் இல்லை."

    stale = ""
    if last and last < latest_all:
        stale = (f'<p class="stale">⚠ HARTI නවතම වාර්තාවේ ({fdate(d_(latest_all),"si")}) {si} මිල නොතිබුණි. '
                 f'පහත දැක්වෙන්නේ {fdate(d_(last),"si")} මිලයි. Not in the latest HARTI report; '
                 f'showing {fdate(d_(last),"en")}.</p>')

    # ---- HARTI table
    table = ""
    cur = None
    for r in rows:
        if r["cat"] != cur:
            if cur is not None:
                table += "</tbody></table></div>"
            cur = r["cat"]
            table += (f'<h2 class="cat">{e(CAT_SI.get(cur, cur))} <span>{e(cur)}</span></h2><div class="scroll"><table>'
                      f'<thead><tr><th>භාණ්ඩය / Item</th><th class="n">අවම–උපරිම<br>Min–Max</th>'
                      f'<th class="n">මධ්‍යගතය<br>Mid</th><th class="n">සතියකට පෙර<br>1 week ago</th></tr></thead><tbody>')
        wk = (f'{money(r["wk"])} {chg_badge(r["mid"], r["wk"])}' if r["wk"] else "—")
        table += (f'<tr><td>{crop_cell(r["name"])}</td>'
                  f'<td class="n rng">{money(r["min"])}–{money(r["max"])}</td>'
                  f'<td class="mid">{money(r["mid"])}</td><td class="n">{wk}</td></tr>')
    if cur is not None:
        table += "</tbody></table></div>"
    wk_dates = sorted({r["wkdate"] for r in rows if r["wkdate"]})
    table_note = ('<p class="asof" style="margin-top:10px">රුපියල් / කි.ග්‍රෑ. · Rs. per kg · HARTI තොග මිල මධ්‍යගතය = (අවම + උපරිම) ÷ 2'
                  + (f' · සතියකට පෙර = {fdate(d_(wk_dates[-1]),"si")} වාර්තාව' if wk_dates else "") + '</p>')

    # ---- where pays more
    better_html = ""
    if better:
        lis = "".join(
            f'<tr><td>{e(hsi(r["name"]))} <span style="color:var(--muted)">/ {e(r["name"])}</span></td>'
            f'<td class="n">රු. {money(r["mid"])}</td>'
            f'<td>📍 {e(MKT[m2]["si"])} <span style="color:var(--muted)">/ {e(men(m2))}</span></td>'
            f'<td class="n"><b>රු. {money(v)}</b></td></tr>'
            for r, m2, v in better[:8])
        better_html = (f'<h2>වැඩි මිලක් ලැබුණු වෙළඳපොළ<span>Where the same crop sold higher on {short(d_(last))}</span></h2>'
                       f'<div class="scroll"><table><thead><tr><th>භාණ්ඩය / Item</th><th class="n">{e(si)}</th>'
                       f'<th>ඉහළම වෙළඳපොළ / Highest market</th><th class="n">මිල / Price</th></tr></thead><tbody>{lis}</tbody></table></div>'
                       f'<p class="tip">🚚 ප්‍රවාහන වියදම වෙළඳපොළ අනුව වෙනස් වේ. සැබෑ ලාභය ගණනය කිරීමට ඔබේ වියදම '
                       f'<a href="../wholesale.html">තොග මිල පිටුවේ ගණකයට</a> ඇතුළත් කරන්න. '
                       f'Transport cost changes the real profit — enter your own cost in the calculator.</p>')

    # ---- CBSL block (Dambulla only)
    cbsl_html = ""
    cbsl_count = 0
    cbsl_first = False
    cd = None
    if market == "Dambulla" and cbsl:
        cd, crow = cbsl_dambulla(cbsl)
        # Show the CBSL table first when it is newer than the HARTI report
        cbsl_first = bool(crow) and (not last or cd > d_(last))
        cbsl_count = len(crow)
        if crow:
            trs = "".join(
                f'<tr><td><a href="../price/{slug(c["name"])}.html">{EMOJIS.get(c["name"], "🌿")} '
                f'{e((CBSL_NAMES.get(c["name"]) or {}).get("si", c["name"]))}</a> '
                f'<span style="color:var(--muted)">/ {e(c["name"])}</span></td>'
                f'<td class="n w">{money(w) if w is not None else "—"}</td>'
                f'<td class="n">{money(r) if r is not None else "—"}</td></tr>'
                for c, w, r in crow)
            newest = ""
            if cbsl_first:
                newest = (f'<p class="tip" style="margin:0 0 12px;background:var(--goodbg,#e3efe6)">🟢 <b>නවතම මිල — {fdate(cd,"si")}</b>. '
                          f'HARTI {fdate(cd,"si")} වාර්තාව තවම නිකුත් කර නැත; HARTI මිල ({fdate(d_(last),"si") if last else "—"}) පහළින් ඇත. '
                          f'<span lang="en">Newest prices: CBSL report, {fdate(cd,"en")}. The HARTI report for this day is not out yet; '
                          f'HARTI prices from {fdate(d_(last),"en") if last else "—"} are below.</span></p>')
            cbsl_html = (f'<h2 id="cbsl">CBSL දඹුල්ල තොග හා සිල්ලර මිල<span>Central Bank report, {fdate(cd,"en")}</span></h2>'
                         + newest +
                         f'<p class="asof" style="margin:0 0 10px">මහ බැංකුවේ දෛනික මිල වාර්තාවේ දඹුල්ල මිල (රු.) · '
                         f'Central Bank of Sri Lanka daily price report, Dambulla.</p>'
                         f'<div class="scroll"><table><thead><tr><th>භාණ්ඩය / Item</th><th class="n">තොග<br>Wholesale</th>'
                         f'<th class="n">සිල්ලර<br>Retail</th></tr></thead><tbody>{trs}</tbody></table></div>')

    # ---- summary cards
    duo = ""
    if last:
        duo = (f'<div class="duo">'
               f'<div class="r"><b>{len(rows)}</b><span>භාණ්ඩ / items · HARTI</span></div>'
               f'<div class="w"><b>▲ {len(up)} · ▼ {len(dn)}</b><span>සතියකට පෙරට වඩා / vs 1 week ago</span></div>'
               + (f'<div class="g"><b>{cbsl_count}</b><span>CBSL තොග හා සිල්ලර / retail items</span></div>' if cbsl_count else "")
               + '</div>')

    harti_h2 = (f'<h2>HARTI {e(si)} තොග මිල<span>HARTI wholesale report, {fdate(d_(last),"en") if last else "—"}</span></h2>')
    others = "".join(f'<a href="{MKT[m]["slug"]}.html">📍 {e(MKT[m]["si"])} / {e(men(m))}</a>' for m in MKT if m != market)

    body = f"""
<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / <a href="index.html">වෙළඳපොළ මිල</a> / {e(si)}</p>
<h1>🧺 {e(si)} එළවළු මිල අද</h1>
<p class="alt">{e(en)} market price today – vegetable wholesale prices<br>{e(ta)} சந்தை விலை இன்று</p>
{cbsl_html if cbsl_first else ''}
{harti_h2 if cbsl_first else ''}
<p class="asof" style="margin-top:14px"><b>📦 තොග මිල / Wholesale</b> · 📍 {e(si)} ({e(en)}) · {fdate(d_(last),'si') if last else '—'} · HARTI</p>
{duo}
{stale}
<div class="story">
  <p>{e(s_si)}</p>
  <p lang="en">{e(s_en)}</p>
  <p lang="ta">{e(s_ta)}</p>
</div>
{table}
{table_note if rows else ''}
{better_html}
{'' if cbsl_first else cbsl_html}
<a class="cta" href="../wholesale.html">වෙළඳපොළ 10ක ප්‍රස්ථාර හා ලාභ ගණකය බලන්න / Charts &amp; calculator →</a>
<h2>අනෙක් වෙළඳපොළ<span>Other markets</span></h2>
<div class="rel">{others}</div>
"""
    dtxt = fdate(d_(last), "en") if last else ""
    title = f"{si} එළවළු මිල අද | {en} Market Price Today Sri Lanka – TopGoviya"
    top3 = ", ".join(f"{r['name']} Rs. {money(r['mid'])}" for r in rows[:3])
    if cbsl_first:
        top3 = ", ".join(f"{c['name']} Rs. {money(r)} retail" for c, w, r in crow[:3] if r is not None)
    if cbsl_first:
        desc = (f"{en} market price today ({fdate(cd,'en')}): CBSL wholesale and retail prices for {cbsl_count} items, "
                f"plus HARTI wholesale prices for {len(rows)} vegetables ({dtxt})")
    else:
        desc = (f"{en} market price today ({dtxt}): wholesale prices for {len(rows)} vegetables from the HARTI report"
                + (", plus CBSL Dambulla retail and wholesale" if cbsl_count else ""))
    desc = (desc
            + f". {top3}. {si} එළවළු මිල අද · {en.lower()} elawalu mila.")
    jsonld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Market prices", "item": f"{SITE}/{OUT_DIR}/"},
        {"@type": "ListItem", "position": 3, "name": f"{en} market price", "item": url}]}
    return shell(title, desc, url, body, jsonld), last, len(rows)

# ---------------------------------------------------------------- hub page
def hub_page(summary, latest_all):
    rows = "".join(
        f'<tr><td><a href="{MKT[m]["slug"]}.html">📍 {e(MKT[m]["si"])}</a> <span style="color:var(--muted)">/ {e(men(m))}</span></td>'
        f'<td class="n">{n}</td><td class="n">{fdate(d_(last),"si") if last else "—"}'
        f'{" ⚠" if last and last < latest_all else ""}</td></tr>'
        for m, (last, n) in summary.items())
    body = (f'<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / වෙළඳපොළ මිල</p>'
            f'<h1>🧺 වෙළඳපොළ එළවළු මිල අද</h1>'
            f'<p class="alt">Today\'s vegetable market prices in Sri Lanka – 10 wholesale markets<br>இன்றைய சந்தை விலைகள் – 10 சந்தைகள்</p>'
            f'<p class="asof" style="margin-top:14px">HARTI නවතම වාර්තාව / Latest HARTI report: {fdate(d_(latest_all),"si")}</p>'
            f'<div class="story" style="font-size:14.5px"><p>දඹුල්ල, පෑලියගොඩ, කෑප්පෙටිපොළ ඇතුළු ආර්ථික මධ්‍යස්ථාන 10ක HARTI තොග මිල. '
            f'වෙළඳපොළක් තට්ටු කර එදින භාණ්ඩ මිල, සතියකට පෙර මිල හා වැඩි මිලක් ලැබුණු වෙළඳපොළ බලන්න.</p>'
            f'<p lang="en">HARTI wholesale prices for 10 markets including Dambulla, Peliyagoda and Keppetipola. '
            f'Tap a market for its price list, last week\'s prices and where the same crop sold higher.</p></div>'
            f'<div class="scroll"><table><thead><tr><th>වෙළඳපොළ / Market</th><th class="n">භාණ්ඩ<br>Items</th>'
            f'<th class="n">වාර්තා දිනය<br>Report date</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="asof" style="margin-top:10px">⚠ = HARTI නවතම වාර්තාවේ නොතිබුණි / not in the latest report (showing its last report)</p>'
            f'<a class="cta" href="../price/index.html">සිල්ලර මිල (CBSL) බලන්න / Retail prices →</a>')
    url = f"{SITE}/{OUT_DIR}/"
    title = "වෙළඳපොළ එළවළු මිල අද | Sri Lanka Market Prices Today – Dambulla, Peliyagoda | TopGoviya"
    desc = (f"Vegetable wholesale prices today at 10 Sri Lankan markets – Dambulla, Peliyagoda, Keppetipola, Meegoda and more "
            f"(HARTI, {fdate(d_(latest_all),'en')}). අද වෙළඳපොළ එළවළු මිල.")
    jsonld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": url}
    return shell(title, desc, url, body, jsonld)

# ---------------------------------------------------------------- sitemap
def update_sitemap(slugs, lastmod):
    path = "sitemap.xml"
    if os.path.exists(path):
        xml = open(path, encoding="utf-8").read()
    else:
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n</urlset>\n'
    xml = re.sub(r"\s*<url>\s*<loc>[^<]*/" + OUT_DIR + r"/[^<]*</loc>.*?</url>", "", xml, flags=re.S)
    new = f"  <url>\n    <loc>{SITE}/{OUT_DIR}/</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>\n"
    for s in slugs:
        new += f"  <url>\n    <loc>{SITE}/{OUT_DIR}/{s}.html</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.9</priority>\n  </url>\n"
    xml = xml.replace("</urlset>", new + "</urlset>")
    open(path, "w", encoding="utf-8").write(xml)

# ---------------------------------------------------------------- main
def main():
    harti = json.load(open("harti_data.json", encoding="utf-8"))
    cbsl = json.load(open("data.json", encoding="utf-8")) if os.path.exists("data.json") else None
    cats = {c["name"]: c.get("category", "") for c in harti["commodities"]}
    hm = update_history(harti)
    os.makedirs(OUT_DIR, exist_ok=True)
    summary, made = {}, []
    for m in MKT:
        page, last, n = market_page(m, hm, harti, cats, cbsl)
        open(os.path.join(OUT_DIR, MKT[m]["slug"] + ".html"), "w", encoding="utf-8").write(page)
        summary[m] = (last, n)
        made.append(MKT[m]["slug"])
    latest_all = harti["dates"][-1]
    open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8").write(hub_page(summary, latest_all))
    update_sitemap(made, latest_all)
    print(f"Built {len(made)} market pages + hub page, sitemap updated.")
    for m, (last, n) in summary.items():
        print(f"  {m:16} {n:3} items  {last}")

if __name__ == "__main__":
    main()
