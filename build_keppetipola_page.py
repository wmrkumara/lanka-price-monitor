#!/usr/bin/env python3
"""
Keppetipola page in the same style as the Dambulla home page — TopGoviya.lk

Takes the home page (index.html, the Dambulla page) as the design, swaps in the
Keppetipola DEC prices (keppetipola_dec.json, entered daily from the official price
list) and writes market/keppetipola.html. Because it copies the home page each time,
every new feature added to the Dambulla page appears on Keppetipola too.

Called by build_market_pages.py. If anything does not match (for example the home
page changed a lot), it returns None and the normal Keppetipola page is kept,
so the site never breaks.
"""

import json, re, html as _h
from datetime import datetime

SITE = "https://topgoviya.lk"
URL = SITE + "/market/keppetipola.html"
TEMPLATE = "index.html"
DATA = "keppetipola_dec.json"

CAT = {"එළවළු (උඩරට)": "v", "පහතරට එළවළු": "v", "අල වර්ග": "r",
       "පලා වර්ග": "l", "ධාන්\u200dය": "g", "ධාන්ය": "g", "පලතුරු": "f"}
TYPE = {"v": "vegetable", "l": "leaf vegetable", "r": "potatoes", "g": "rice", "f": "fruit"}

# Items not on the Dambulla list: Tamil name, emoji, Singlish search words
EXTRA = {
    "Beetroot (leafy)": ("பீட்ரூட் (இலையுடன்)", "🥬", "kola beet, beetroot"),
    "Beetroot cut (N'Eliya/Welimada)": ("பீட்ரூட் வெட்டு (நுவரெலியா/வெலிமடை)", "🥬", "cut beet, beetroot cut"),
    "Beetroot cut (other)": ("பீட்ரூட் வெட்டு (ஏனையவை)", "🥬", "cut beet, beetroot cut"),
    "Carrot": ("கேரட்", "🥕", "carrot, keret"),
    "Bell pepper (red)": ("குடைமிளகாய் (சிவப்பு)", "🫑", "bell pepper, capsicum red"),
    "Bell pepper (green)": ("குடைமிளகாய் (பச்சை)", "🫑", "bell pepper, capsicum green"),
    "Bell pepper (yellow)": ("குடைமிளகாய் (மஞ்சள்)", "🫑", "bell pepper, capsicum yellow"),
    "Gherkin": ("கெர்கின் வெள்ளரி", "🥒", "gherkin"),
    "Parsley": ("பார்ஸ்லி", "🌿", "parsley"),
    "Celery": ("செலரி", "🌿", "celery, saldari"),
    "Mint leaves": ("புதினா", "🌿", "mint, pudina"),
    "Coriander leaves": ("கொத்தமல்லி இலை", "🌿", "kottamalli kola, coriander"),
    "Iceberg lettuce": ("ஐஸ்பர்க் லெட்டூஸ்", "🥬", "iceberg, salada, lettuce"),
    "Pumpkin (local)": ("பூசணிக்காய் (உள்ளூர்)", "🎃", "wattakka, poosanikai"),
    "Thumba karawila": ("பழுபாகற்காய்", "🥬", "thumba karawila"),
    "Nai miris (tunnel)": ("நாய் மிளகாய் (பசுமைக்குடில்)", "🌶️", "nai miris"),
    "Onion leaves": ("வெங்காயத் தாள்", "🧅", "lunu kola, vengaya thaal"),
    "Kankun": ("கங்குன் கீரை", "🌿", "kankun, kangkung"),
    "Banana (anamalu)": ("ஆனமாலு வாழைப்பழம்", "🍌", "anamalu kesel"),
}

MONTHS_SI = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි", "අගෝස්තු",
             "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]


class Miss(Exception):
    pass


def sub1(pattern, repl, s, flags=0):
    """Replace exactly one regex match, or stop."""
    n = len(re.findall(pattern, s, flags))
    if n != 1:
        raise Miss(f"pattern found {n} times: {pattern[:60]}")
    return re.sub(pattern, lambda m: repl, s, count=1, flags=flags)


def rep1(old, new, s):
    if s.count(old) != 1:
        raise Miss(f"text found {s.count(old)} times: {old[:60]}")
    return s.replace(old, new)


def build_master(items, dmaster):
    by_si = {v["si"]: v for v in dmaster.values()}
    by_en = {v["en"].lower(): v for v in dmaster.values()}
    M = {}
    for it in items:
        no, en, si = str(it["no"]), it["en"], it["si"].strip()
        c = CAT.get(it.get("cat", ""), "v")
        d = by_si.get(si) or by_en.get(en.lower())
        if d:
            m = {"si": si, "en": en, "ta": d.get("ta", en), "s": d.get("s", ""), "c": c,
                 "u": it.get("unit", "kg"), "e": d.get("e", "🥬"), "img": d.get("img", ""),
                 "p": d.get("p", 60), "pc": d.get("pc", 30)}
        else:
            ta, e, s = EXTRA.get(en, (en, {"v": "🥬", "l": "🌿", "r": "🥔", "g": "🌾", "f": "🍎"}[c], ""))
            m = {"si": si, "en": en, "ta": ta, "s": s, "c": c, "u": it.get("unit", "kg"),
                 "e": e, "img": "", "p": 70 + it["no"], "pc": 40 + it["no"]}
        M[no] = m
    return M


def to_db(kep):
    prods = {}
    for it in kep["items"]:
        c = CAT.get(it.get("cat", ""), "v")
        prods[str(it["no"])] = {"name": it["en"], "type": TYPE[c]}
    days = {d: {str(k): v for k, v in p.items()} for d, p in kep["days"].items()}
    dates = sorted(days)
    return {"source": "Keppetipola Dedicated Economic Centre (Keppetipola DEC)",
            "unit_note": "Wholesale price range (min, max) in Rs. from the official daily price list",
            "products": prods, "days": days,
            "latest_date": dates[-1] if dates else None, "oldest_date": dates[0] if dates else None}


def money(n):
    return f"{int(round(n)):,}"


def build():
    tpl = open(TEMPLATE, encoding="utf-8").read()
    kep = json.load(open(DATA, encoding="utf-8"))
    if not kep.get("days"):
        raise Miss("no Keppetipola days")
    db = to_db(kep)
    last = db["latest_date"]
    dt = datetime.strptime(last, "%Y-%m-%d")
    dot = dt.strftime("%Y.%m.%d")
    d_si = f"{dt.year} {MONTHS_SI[dt.month - 1]} {dt.day}"
    d_en = f"{dt.day} {MONTHS_EN[dt.month - 1]} {dt.year}"

    m = re.search(r"const MASTER=(\{.*?\});\n", tpl)
    if not m:
        raise Miss("MASTER not found")
    dmaster = json.loads(m.group(1))
    M = build_master(kep["items"], dmaster)
    today = db["days"][last]
    n_today = sum(1 for k in today if k in M)

    # ---------- head ----------
    title = f"කැප්පෙටිපොල එලවලු මිල අද {dot} | Keppetipola Vegetable Market Price List Today Sri Lanka"
    top = sorted((k for k in today if k in M), key=lambda k: M[k]["p"])[:3]
    top3 = ", ".join(f"{M[k]['en']} Rs. {money(today[k][0])}–{money(today[k][1])}" for k in top)
    desc = (f"Keppetipola economic centre vegetable market price list today ({d_en}): wholesale prices for "
            f"{n_today} items from the official Keppetipola Dedicated Economic Centre daily price list. {top3}. "
            f"Charts, profit calculator and price list PDF. කෑප්පෙටිපොළ එලවලු මිල අද · keppetipola elawalu mila.")
    e = lambda x: _h.escape(x, quote=True)
    out = tpl
    out = sub1(r"<title>.*?</title>", f"<title>{e(title)}</title>", out, re.S)
    out = sub1(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(desc)}">', out)
    out = sub1(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(title)}">', out)
    out = sub1(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{e(desc)}">', out)
    out = sub1(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{URL}">', out)
    out = sub1(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{URL}">', out)
    out = re.sub(r'<meta (property="og:image(?::width|:height|:alt)?"|name="twitter:image")[^>]*>\n', "", out)
    out = rep1('<meta name="twitter:card" content="summary_large_image">', '<meta name="twitter:card" content="summary">', out)
    out = rep1('<meta charset="UTF-8">', '<meta charset="UTF-8">\n<base href="/">', out)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": URL + "#webpage", "url": URL,
         "name": "කෑප්පෙටිපොළ එළවළු මිල අද — Keppetipola vegetable price today", "inLanguage": "si",
         "isPartOf": {"@id": SITE + "/#website"},
         "about": {"@type": "Place", "name": "Keppetipola Dedicated Economic Centre (කෑප්පෙටිපොළ විශේෂිත ආර්ථික මධ්‍යස්ථානය)",
                   "address": {"@type": "PostalAddress", "addressLocality": "Keppetipola",
                               "addressRegion": "Uva Province", "addressCountry": "LK"}}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Market prices", "item": SITE + "/market/"},
            {"@type": "ListItem", "position": 3, "name": "Keppetipola market price", "item": URL}]},
        {"@type": "Dataset", "name": "Keppetipola daily wholesale vegetable prices (කෑප්පෙටිපොළ දෛනික තොග මිල)",
         "description": "Daily minimum and maximum wholesale prices for up-country and low-country vegetables, roots, "
                        "leafy vegetables, grains and fruits at the Keppetipola Dedicated Economic Centre, Sri Lanka, "
                        "from the centre's official daily price list.",
         "url": URL, "isAccessibleForFree": True, "temporalCoverage": f"{db['oldest_date']}/..",
         "spatialCoverage": {"@type": "Place", "name": "Keppetipola, Sri Lanka"},
         "keywords": ["කැප්පෙටිපොල එලවලු මිල", "කෑප්පෙටිපොළ තොග මිල", "Keppetipola vegetable price",
                      "Keppetipola market price list today"]}]}
    out = sub1(r'<script type="application/ld\+json">.*?</script>',
               '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>", out, re.S)

    # ---------- menu: Keppetipola button next to Dambulla ----------
    out = out.replace(' aria-current="page"', "")
    if 'href="market/keppetipola.html" class="navlink' in out:
        out = re.sub(r'(<a href="market/keppetipola\.html" class="navlink[^"]*")', r'\1 aria-current="page"', out, count=1)
    else:
        dm = re.search(r'<a href="index\.html" class="navlink dec">[^<]*</a>', out)
        if not dm:
            raise Miss("Dambulla menu button not found")
        out = out.replace(dm.group(0), dm.group(0).replace('href="index.html"', 'href="/"')
                          + '\n    <a href="market/keppetipola.html" class="navlink kep" aria-current="page">🥕 කැප්පෙටිපොළ</a>', 1)
    if ".navlink.kep{" not in out:
        out = rep1(".navlink.dec{", ".navlink.kep{background:#5f7f24;color:#fff}\n.navlink.dec{", out)

    # ---------- heading ----------
    out = sub1(r'<h1 id="tH1">[^<]*</h1>', '<h1 id="tH1">කෑප්පෙටිපොළ එළවළු මිල අද</h1>', out)
    out = sub1(r'<div class="h1en">[^<]*</div>', '<div class="h1en">Keppetipola market price today</div>', out)

    # ---------- SEO text (baked daily) ----------
    lst = sorted((k for k in today if k in M), key=lambda k: M[k]["p"])[:30]
    lines = " · ".join(f"{e(M[k]['si'])} රු. {money(today[k][0])}" + (f"–{money(today[k][1])}" if today[k][1] != today[k][0] else "")
                       + " / කි.ග්‍රෑ." for k in lst)
    social = re.search(r'<div class="social">.*?</div>', out, re.S)
    pages = re.search(r'<ul class="pages">.*?</ul>', out, re.S)
    if not social or not pages:
        raise Miss("social/pages block not found")
    seo = f'''<section class="seo" aria-label="කෑප්පෙටිපොළ එලවලු මිල — තොරතුරු">
  <h2>අද කෑප්පෙටිපොළ එලවලු මිල ලැයිස්තුව</h2>
  <p><b>කැප්පෙටිපොල එලවලු මිල අද — {d_si}</b> (කෑප්පෙටිපොළ විශේෂිත ආර්ථික මධ්‍යස්ථානය, තොග මිල, අවම–උපරිම): {lines} — භාණ්ඩ {n_today} ක සම්පූර්ණ ලැයිස්තුව ඉහත.</p>
  <h2>කෑප්පෙටිපොළ එලවලු මිල අද — TopGoviya.lk</h2>
  <p>කෑප්පෙටිපොළ විශේෂිත ආර්ථික මධ්‍යස්ථානය (Keppetipola Dedicated Economic Centre) උඩරට එළවළු සඳහා ශ්‍රී ලංකාවේ ප්‍රධාන තොග වෙළඳපොළකි — බෝංචි, කැරට්, ගෝවා, ලීක්ස්, අර්තාපල්, බීට්, තක්කාලි හා තවත් බොහෝ භාණ්ඩ. TopGoviya.lk හි නිල දෛනික මිල ලැයිස්තුවෙන් අද තොග මිල (අවම – උපරිම), පෙර වාර්තාවට වෙනස, මිල ප්‍රස්ථාර, ගොවි හා වෙළෙන්දා ලාභ ගණකය සහ මිල ලැයිස්තුව PDF / පින්තූරය ලෙස නොමිලේ බලන්න.</p>
  <p lang="en">Keppetipola market price today: daily wholesale prices from the official price list of the Keppetipola Dedicated Economic Centre, Sri Lanka's main up-country vegetable market — beans, carrot, cabbage, leeks, potato, beetroot, tomato and more, with day-to-day change, price charts, profit calculators and a downloadable price list (PDF / image). Free, in Sinhala, Tamil and English. keppetipola elawalu mila ada · keppetipola economic centre price list today.</p>
  <p lang="ta">கெப்பெட்டிபொல காய்கறி விலை இன்று — கெப்பெட்டிபொல விசேட பொருளாதார மையத்தின் தினசரி மொத்த விலைகள், மாற்றங்கள் மற்றும் வரைபடங்களுடன்.</p>
  <h2>වෙනත් වෙළඳපොළ මිල</h2>
  <ul class="mk">
    <li><a href="/">🥬 දඹුල්ල</a></li>
    <li><a href="market/peliyagoda.html">පෑලියගොඩ</a></li>
    <li><a href="market/nuwara-eliya.html">නුවරඑළිය</a></li>
    <li><a href="market/thambuththegama.html">තඹුත්තේගම</a></li>
    <li><a href="market/bandarawela.html">බණ්ඩාරවෙල</a></li>
    <li><a href="market/kandy.html">මහනුවර</a></li>
    <li><a href="market/meegoda.html">මීගොඩ</a></li>
    <li><a href="market/veyangoda.html">වේයන්ගොඩ</a></li>
    <li><a href="market/norochchole.html">නොරොච්චෝල</a></li>
    <li><a href="wholesale.html">HARTI තොග මිල</a></li>
    <li><a href="retail.html">සිල්ලර මිල (CBSL)</a></li>
  </ul>
  <h2>📲 දිනපතා මිල අනුගමනය කරන්න</h2>
  {social.group(0)}
  <h2>TopGoviya පිටු</h2>
  {pages.group(0)}
</section>'''
    out = sub1(r'<section class="seo".*?</section>', seo, out, re.S)

    # ---------- data ----------
    out = sub1(r"const MASTER=\{.*?\};\n", "const MASTER=" + json.dumps(M, ensure_ascii=False, separators=(",", ":")) + ";\n", out, re.S)
    out = sub1(r"const EMBEDDED=\{.*?\};\n", "const EMBEDDED=" + json.dumps(db, ensure_ascii=False, separators=(",", ":")) + ";\n", out, re.S)

    # ---------- page script: Dambulla -> Keppetipola wording ----------
    i = out.find("const MASTER=")
    j = out.find("const EMBEDDED=")
    k = out.find(";\n", j) + 2          # leave the data alone, change the code after it
    head, data, code = out[:i], out[i:k], out[k:]
    for a, b in [("දඹුල්ල", "කෑප්පෙටිපොළ"), ("தம்புள்ள", "கெப்பெட்டிபொல"),
                 ("Dambulla", "Keppetipola"), ("dambulla", "keppetipola")]:
        code = code.replace(a, b)
    code = rep1('"https://topgoviya.lk/keppetipola/"+sl+".html"', '"https://topgoviya.lk/market/keppetipola.html"', code)
    code = sub1(r"const LIVE=\[[^\]]*\];",
                'const LIVE=["https://raw.githubusercontent.com/wmrkumara/lanka-price-monitor/main/keppetipola_dec.json","keppetipola_dec.json"];', code)
    code = sub1(r"const EARLY=\[[^\]]*\];", "const EARLY=[];", code)
    code = rep1("if(j&&j.days&&Object.keys(j.days).length)DB=j;",
                "if(j&&j.days&&Object.keys(j.days).length)DB=j.items?kepToDB(j):j;", code)
    code = rep1('const SITE=', '''function kepToDB(j){const T2={v:"vegetable",l:"leaf vegetable",r:"potatoes",g:"rice",f:"fruit"},P={};
  (j.items||[]).forEach(it=>{const m=MASTER[String(it.no)];P[String(it.no)]={name:it.en,type:T2[m?m.c:"v"]};});
  const D={};Object.keys(j.days||{}).forEach(d=>{D[d]={};Object.keys(j.days[d]).forEach(k=>D[d][String(k)]=j.days[d][k]);});
  return {source:EMBEDDED.source,unit_note:EMBEDDED.unit_note,products:P,days:D};}
const SITE=''', code)
    code = code.replace('"https://topgoviya.lk/"', '"https://topgoviya.lk/market/keppetipola.html"')
    # starter basket: same crops as Dambulla's, by Keppetipola item number
    sm = re.search(r"const STARTER=(\[.*?\]);", code)
    if sm:
        want = {"Tomato", "Big onion (imported)", "Green chilli", "Brinjal", "Beans", "Carrot", "Potato (Nuwara Eliya)", "Cabbage"}
        st = []
        for no, mm in M.items():
            base = mm["en"].split(" (")[0]
            if mm["en"] in want or base in {w.split(" (")[0] for w in want}:
                if base not in [M[x[0]]["en"].split(" (")[0] for x in st]:
                    st.append([no, 1 if base in ("Tomato", "Big onion", "Potato") else 0.5])
        code = code.replace(sm.group(0), "const STARTER=" + json.dumps(st) + ";")
    out = head + data + code
    return out, last, n_today


def page():
    """Returns (html, last_date, items) or None if anything did not match."""
    try:
        return build()
    except Exception as ex:
        print(f"WARN: Keppetipola Dambulla-style page skipped ({ex}); keeping the normal page.")
        return None


if __name__ == "__main__":
    r = page()
    if r:
        import os
        os.makedirs("market", exist_ok=True)
        open("market/keppetipola.html", "w", encoding="utf-8").write(r[0])
        print(f"Built market/keppetipola.html — {r[2]} items, {r[1]}")
