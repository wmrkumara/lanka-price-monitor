"""
build_spice_pages.py  -  TopGoviya.lk spice landing pages (DEA weekly farm-gate prices)
---------------------------------------------------------------------------------------
Reads dea_data.json and writes:
  spice/<name>.html   "ගම්මිරිස් මිල අද", "කුරුඳු මිල අද"... - one farm-gate price page per spice
  sitemap.xml         keeps every other page, adds/refreshes /spice/ entries

Prices are the Department of Export Agriculture (DEA) weekly producers' (farm gate)
prices. Weekly change = latest DEA week vs the week before (single weeks, not averages).
Runs daily from GitHub Actions; the page only changes when DEA publishes a new week.
Uses build_pages.py (same folder) for the shared look.
"""
import json, os, re
from datetime import datetime, timedelta

from build_pages import CSS, GA_ID, SITE, COPYRIGHT, e, money, fdate

OUT_DIR = "spice"
DEA_URL = "https://exagri.info/mkt/index.html"

DISTRICT_SI = {"Kandy": "මහනුවර", "Matale": "මාතලේ", "Nuwara_eliya": "නුවරඑළිය", "Kegalle": "කෑගල්ල",
               "Ratnapura": "රත්නපුර", "Badulla": "බදුල්ල", "Kurunegala": "කුරුණෑගල", "Colombo": "කොළඹ",
               "Gampaha": "ගම්පහ", "Kalutara": "කළුතර", "Galle": "ගාල්ල", "Matara": "මාතර",
               "Hambantota": "හම්බන්තොට", "Monaragala": "මොනරාගල"}
DISTRICT_EN = {"Nuwara_eliya": "Nuwara Eliya"}


# slug, DEA commodity, Sinhala, English, Tamil, Singlish, emoji,
# grades: (column prefix, Sinhala label, English label, unit), first grade = headline
SPICES = [
 {"slug": "pepper", "c": "pepper", "si": "ගම්මිරිස්", "en": "Black pepper", "ta": "மிளகு", "sl": "gammiris", "emo": "⚫",
  "alt_si": "කළු ගම්මිරිස් කිලෝවක මිල",
  "grades": [("GR-1", "GR-1 (කළු ගම්මිරිස්)", "GR-1 black pepper", "kg"), ("GR-2", "GR-2", "GR-2 black pepper", "kg"),
             ("WHITE", "සුදු ගම්මිරිස්", "White pepper", "kg")],
  "faq_grades": ("GR-1, GR-2 හා සුදු ගම්මිරිස් අතර වෙනස?", "What is the difference between GR-1, GR-2 and white pepper?",
                 "GR-1 යනු ඉහළම ශ්‍රේණියේ කළු ගම්මිරිස් (ඝනත්වය වැඩි, පිරිසිදු); GR-2 ඊට පහළ ශ්‍රේණියයි. සුදු ගම්මිරිස් පොත්ත ඉවත් කළ ඒවා බැවින් මිල වැඩිය.",
                 "GR-1 is the top grade of black pepper (denser, cleaner); GR-2 is the next grade. White pepper has the outer skin removed and sells higher.")},
 {"slug": "cinnamon", "c": "cinnamon", "si": "කුරුඳු", "en": "Cinnamon", "ta": "கறுவா", "sl": "kurundu", "emo": "🪵",
  "alt_si": "කුරුඳු කිලෝවක මිල · කුරුඳු පොතු මිල",
  "grades": [("C-5", "C-5", "C-5 (Continental)", "kg"), ("Alba", "ඇල්බා (Alba)", "Alba", "kg"), ("H-1", "H-1", "H-1 (Hamburg)", "kg")],
  "faq_grades": ("කුරුඳු ශ්‍රේණි (Alba, C, M, H) අතර වෙනස?", "What do the cinnamon grades (Alba, C, M, H) mean?",
                 "කුරුඳු ශ්‍රේණි බට (quill) වල ඝනකම අනුව වේ: Alba සිහින්ම හා මිල වැඩිම; ඉන්පසු C (Continental), M (Mexican), H (Hamburg) ශ්‍රේණි ඝනකම වැඩි වන විට මිල අඩු වේ.",
                 "Cinnamon grades follow quill thickness: Alba is the thinnest and highest priced, then C (Continental), M (Mexican) and H (Hamburg) grades are thicker and cheaper.")},
 {"slug": "clove", "c": "clove", "si": "කරාබු නැටි", "en": "Clove", "ta": "கராம்பு", "sl": "karabu", "emo": "🌰",
  "alt_si": "කරාබු මිල · කරාබු කිලෝවක මිල",
  "grades": [("CLOVE", "කරාබු නැටි", "Clove", "kg"), ("STEM", "කරාබු දඬු (Stem)", "Clove stem", "kg")],
  "faq_grades": ("කරාබු හා කරාබු දඬු අතර වෙනස?", "What is the difference between clove and clove stem prices?",
                 "කරාබු යනු වියළි මල් පොහොට්ටුය; දඬු (stem) අතුරු නිෂ්පාදනයක් බැවින් මිල බොහෝ අඩුය.",
                 "Clove is the dried flower bud; stems are a by-product and sell far lower.")},
 {"slug": "cardamom", "c": "cardamom", "si": "එනසාල්", "en": "Cardamom", "ta": "ஏலக்காய்", "sl": "enasal", "emo": "🟢",
  "alt_si": "එනසාල් කිලෝවක මිල",
  "grades": [("LG", "LG", "LG grade", "kg"), ("LLG1", "LLG1", "LLG1 grade", "kg"), ("LB", "LB", "LB grade", "kg")],
  "faq_grades": ("එනසාල් ශ්‍රේණි (LG, LLG1, LB) යනු?", "What are the cardamom grades (LG, LLG1, LB)?",
                 "DEA එනසාල් ශ්‍රේණි කිහිපයක් වාර්තා කරයි; LG ඉහළම ශ්‍රේණියයි, LLG1, LLG2, LB ක්‍රමයෙන් පහළ ශ්‍රේණි වන අතර මිල ද අඩු වේ.",
                 "DEA reports several cardamom grades; LG is the top grade, with LLG1, LLG2 and LB as lower grades at lower prices.")},
 {"slug": "nutmeg", "c": "nutmeg", "si": "සාදික්කා", "en": "Nutmeg & mace", "ta": "சாதிக்காய்", "sl": "sadikka", "emo": "🟤",
  "alt_si": "සාදික්කා මිල · වසාවාසි මිල",
  "grades": [("NUTMEG No.1", "සාදික්කා No.1", "Nutmeg No.1", "kg"), ("NUTMEG No.2", "සාදික්කා No.2", "Nutmeg No.2", "kg"),
             ("MACE No.1", "වසාවාසි No.1", "Mace No.1", "kg")],
  "faq_grades": ("සාදික්කා හා වසාවාසි අතර වෙනස?", "What is the difference between nutmeg and mace?",
                 "සාදික්කා යනු ඇටයයි; වසාවාසි (mace) යනු ඇටය වටා ඇති රතු ආවරණයයි. වසාවාසි කිලෝවක මිල සාදික්කාට වඩා බොහෝ වැඩිය.",
                 "Nutmeg is the seed; mace is the red covering around it. Mace sells for much more per kg.")},
 {"slug": "coffee", "c": "coffee", "si": "කෝපි", "en": "Coffee", "ta": "கோப்பி", "sl": "kopi", "emo": "☕",
  "alt_si": "කෝපි කිලෝවක මිල",
  "grades": [("GR 1", "GR 1", "GR 1", "kg"), ("GR 2", "GR 2", "GR 2", "kg"), ("PARCHMENT", "පාච්මන්ට් (Parchment)", "Parchment", "kg")],
  "faq_grades": ("කෝපි GR 1, GR 2 හා Parchment යනු?", "What are coffee GR 1, GR 2 and parchment?",
                 "GR 1 හා GR 2 යනු පිරිසිදු කළ කෝපි ඇට ශ්‍රේණියි. Parchment යනු පිටත පොත්ත සහිත ඇට වන අතර DEA එය වෙනම වාර්තා කරයි.",
                 "GR 1 and GR 2 are grades of cleaned coffee beans. Parchment coffee still has its inner husk and is reported separately by DEA.")},
 {"slug": "cocoa", "c": "cocoa", "si": "කොකෝවා", "en": "Cocoa", "ta": "கொக்கோ", "sl": "kokowa", "emo": "🍫",
  "alt_si": "කොකෝවා ඇට කිලෝවක මිල",
  "grades": [("GR 1", "GR 1", "GR 1", "kg"), ("GR 2", "GR 2", "GR 2", "kg")],
  "faq_grades": ("කොකෝවා GR 1 හා GR 2 අතර වෙනස?", "What is the difference between cocoa GR 1 and GR 2?",
                 "GR 1 ඉහළ ශ්‍රේණියේ වියළි කොකෝවා ඇටය; GR 2 ඊට පහළ ශ්‍රේණියයි.",
                 "GR 1 is the higher grade of dried cocoa beans; GR 2 is the next grade.")},
 {"slug": "arecanut", "c": "arecanut", "si": "පුවක්", "en": "Areca nut", "ta": "பாக்கு", "sl": "puwak", "emo": "🥥",
  "alt_si": "වියළි පුවක් (කරුංකා) මිල · අමු පුවක් ගෙඩි 100ක මිල",
  "grades": [("Dried-(Karunka)-(Rs./k.g.)", "වියළි පුවක් (කරුංකා)", "Dried areca nut (karunka)", "kg"),
             ("Fresh-(100 nuts)", "අමු පුවක් (ගෙඩි 100)", "Fresh areca nut (per 100 nuts)", "100 nuts")],
  "faq_grades": ("වියළි හා අමු පුවක් මිල වෙනස් ඇයි?", "Why are dried and fresh areca nut priced differently?",
                 "වියළි පුවක් (කරුංකා) කිලෝවකට මිල කරන අතර අමු පුවක් ගෙඩි 100කට මිල කරයි — ඒකක දෙකක් බැවින් සෘජුව සසඳන්න එපා.",
                 "Dried areca nut (karunka) is priced per kg, fresh nuts per 100 nuts — different units, so don't compare them directly.")},
 {"slug": "ginger", "c": "other", "si": "ඉඟුරු", "en": "Ginger", "ta": "இஞ்சி", "sl": "inguru", "emo": "🫚",
  "alt_si": "ඉඟුරු කිලෝවක මිල", "grades": [("Ginger", "ඉඟුරු", "Ginger", "kg")], "faq_grades": None},
 {"slug": "turmeric", "c": "other", "si": "කහ", "en": "Turmeric", "ta": "மஞ்சள்", "sl": "kaha", "emo": "🟡",
  "alt_si": "කහ කිලෝවක මිල", "grades": [("Turmeric", "කහ", "Turmeric", "kg")], "faq_grades": None},
 {"slug": "goraka", "c": "other", "si": "ගොරකා", "en": "Goraka", "ta": "கொறுக்காய்", "sl": "goraka", "emo": "🍂",
  "alt_si": "ගොරකා කිලෝවක මිල", "grades": [("Goraka", "ගොරකා", "Goraka", "kg")], "faq_grades": None},
]
UNIT_SI = {"kg": "කි.ග්‍රෑ.", "100 nuts": "ගෙඩි 100"}
UNIT_EN = {"kg": "kg", "100 nuts": "100 nuts"}


def d_(s): return datetime.strptime(s, "%Y-%m-%d").date()
def den(x): return DISTRICT_EN.get(x, x)


def nat(week, grade, kind="Average", c="pepper"):
    v = (((week.get("commodities") or {}).get(c) or {}).get("districts") or {}).get("National") or {}
    return v.get(f"{grade} ({kind} Price)")


def chg(now, old):
    if not now or not old:
        return "", "flat", ""
    pct = (now - old) / old * 100
    cls = "flat" if abs(pct) < 0.5 else ("up" if pct > 0 else "down")
    arrow = {"up": "▲", "down": "▼", "flat": "■"}[cls]
    return f'{arrow} {"+" if pct > 0 else ""}{pct:.1f}%', cls, pct


def svg_line(points, w=640, h=170, lang="si"):
    """Simple inline SVG line for (date, value) points."""
    pts = [(d, v) for d, v in points if v]
    if len(pts) < 2:
        return ""
    lo, hi = min(v for _, v in pts), max(v for _, v in pts)
    pad = (hi - lo) * 0.12 or 50
    lo, hi = lo - pad, hi + pad
    t0, t1 = pts[0][0].toordinal(), pts[-1][0].toordinal()
    X = lambda d: 40 + (d.toordinal() - t0) / ((t1 - t0) or 1) * (w - 52)
    Y = lambda v: 12 + (1 - (v - lo) / (hi - lo)) * (h - 36)
    path = " ".join(("M" if i == 0 else "L") + f"{X(d):.1f} {Y(v):.1f}" for i, (d, v) in enumerate(pts))
    grid = ""
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        grid += (f'<line x1="40" x2="{w-12}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#e3d9c4"/>'
                 f'<text x="34" y="{Y(v)+3:.1f}" text-anchor="end" font-size="10" fill="#7a7264">{money(v)}</text>')
    lab = ""
    for d in sorted({pts[0][0], pts[len(pts) // 2][0], pts[-1][0]}):
        lab += f'<text x="{X(d):.1f}" y="{h-6}" text-anchor="middle" font-size="10" fill="#7a7264">{d.strftime("%b %Y")}</text>'
    d_, v_ = pts[-1]
    # points for the hover / touch price box: [x, y, date, price]
    data = json.dumps([[round(X(d), 1), round(Y(v), 1), fdate(d, lang), money(v)] for d, v in pts], ensure_ascii=False)
    cur = "Rs." if lang == "en" else "රු."
    return (f'<div class="tgc" data-w="{w}" data-cur="{cur}" data-p=\'{e(data)}\'>'
            f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;display:block;touch-action:pan-y" role="img" '
            f'aria-label="National average price trend">{grid}{lab}'
            f'<path d="{path}" fill="none" stroke="#0e4f4a" stroke-width="2.2"/>'
            f'<circle cx="{X(d_):.1f}" cy="{Y(v_):.1f}" r="3.5" fill="#a9802a"/>'
            f'<line class="tgx" x1="0" x2="0" y1="12" y2="{h-24}" stroke="#a9802a" stroke-dasharray="3 3" opacity="0"/>'
            f'<circle class="tgd" cx="0" cy="0" r="5" fill="#fffdf7" stroke="#0e4f4a" stroke-width="2.4" opacity="0"/></svg>'
            f'<div class="tgt"></div></div>')


def shell(title, desc, canonical, body, jsonld, image="", lang="si", alternates=None):
    alt = "".join(f'\n<link rel="alternate" hreflang="{hl}" href="{u}">' for hl, u in (alternates or []))
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">{alt}
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="TopGoviya.lk">{f"""
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{image}">""" if image else ""}
<meta name="theme-color" content="#0e4f4a">
<link rel="icon" type="image/png" sizes="192x192" href="../icon-192x192.png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Noto+Sans+Sinhala:wght@400;600&family=Noto+Sans+Tamil:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}
.rng{{font-size:12.5px;color:var(--muted);font-weight:500}}
.chart{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px 12px;margin:10px 0}}
.tgc{{position:relative}}
.tgt{{position:absolute;pointer-events:none;background:#191d1a;color:#f4efe4;font-family:'JetBrains Mono',monospace;font-size:12px;
     font-weight:600;padding:5px 9px;border-radius:8px;white-space:nowrap;transform:translate(-50%,-135%);opacity:0;transition:opacity .12s;z-index:3}}
.tgt b{{color:#ffd98a}}
</style>
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="../index.html">TopGoviya.lk</a><span><a href="../spices.html">කුළුබඩු මිල / Spice prices</a><a class="tgc-top" href="../contact.html"><svg width="14" height="14" viewBox="0 0 24 24" fill="#25D366" aria-hidden="true" style="flex-shrink:0;vertical-align:-2px"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg> අමතන්න</a></span></header>
{body}
<p class="note">මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.<br>
Prices are indicative only. Decisions are your responsibility. Source: Department of Export Agriculture (DEA) weekly
producers' (farm gate) prices — <a href="{DEA_URL}" rel="noopener">exagri.info</a>. Not an official publication.
<a href="../data-sources.html">How we collect the data →</a> · මිලක් වැරදි යැයි සිතේද? <a href="../contact.html?t=price">අපට දන්වන්න</a><br>
விலைகள் வழிகாட்டல் மட்டுமே. உங்கள் முடிவுகளுக்கு நீங்களே பொறுப்பு.</p>
<script>
/* chart: hover (mouse) or touch-and-slide (phone) shows that week's date and price */
document.querySelectorAll(".tgc").forEach(function (box) {{
  var P = JSON.parse(box.getAttribute("data-p")), W = +box.getAttribute("data-w");
  var svg = box.querySelector("svg"), x = box.querySelector(".tgx"), dot = box.querySelector(".tgd"), tip = box.querySelector(".tgt");
  function show(cx) {{
    var r = svg.getBoundingClientRect(), u = (cx - r.left) / r.width * W, best = P[0];
    P.forEach(function (p) {{ if (Math.abs(p[0] - u) < Math.abs(best[0] - u)) best = p; }});
    x.setAttribute("x1", best[0]); x.setAttribute("x2", best[0]); x.setAttribute("opacity", "1");
    dot.setAttribute("cx", best[0]); dot.setAttribute("cy", best[1]); dot.setAttribute("opacity", "1");
    var px = best[0] / W * r.width, py = best[1] / W * r.width;
    tip.innerHTML = best[2] + " &nbsp;<b>" + (box.getAttribute("data-cur") || "රු.") + " " + best[3] + "</b>";
    tip.style.left = Math.min(Math.max(px, 70), r.width - 70) + "px"; tip.style.top = py + "px"; tip.style.opacity = 1;
  }}
  function hide() {{ tip.style.opacity = 0; x.setAttribute("opacity", "0"); dot.setAttribute("opacity", "0"); }}
  svg.addEventListener("mousemove", function (ev) {{ show(ev.clientX); }});
  svg.addEventListener("mouseleave", hide);
  svg.addEventListener("touchstart", function (ev) {{ show(ev.touches[0].clientX); }}, {{passive: true}});
  svg.addEventListener("touchmove", function (ev) {{ show(ev.touches[0].clientX); }}, {{passive: true}});
}});
</script>
<footer>{COPYRIGHT}<br>Design &amp; development by <a href="https://ebooklanka.com" target="_blank" rel="noopener">ebooklanka.com</a> · Built in Gampola, Sri Lanka</footer>
</div>
<script defer src="/events.js?v=1"></script>
</body>
</html>
"""


def spice_page(dea, sp):
    c, G = sp["c"], sp["grades"]
    main, main_si, main_en, main_unit = G[0]
    N = lambda w, g, k="Average": nat(w, g, k, c)
    weeks = [w for w in dea["weeks"] if N(w, main)]
    if len(weeks) < 2:
        return None, None
    cur, prev = weeks[-1], weeks[-2]
    d, dp = d_(cur["date"]), d_(prev["date"])
    url = f"{SITE}/{OUT_DIR}/{sp['slug']}.html"
    si, en, ta, sl = sp["si"], sp["en"], sp["ta"], sp["sl"]
    U_si, U_en = UNIT_SI[main_unit], UNIT_EN[main_unit]

    g1, g1p, g1h = N(cur, main), N(prev, main), N(cur, main, "Highest")
    ch_txt, ch_cls, ch_pct = chg(g1, g1p)
    cards = ""
    for i, (key, gsi, gen, unit) in enumerate(G):
        a_, ap = N(cur, key), N(prev, key)
        if not a_:
            continue
        t, cls, _ = chg(a_, ap)
        cards += (f'<div class="{"r" if i == 0 else "w"}"><b>රු. {money(a_)}</b>'
                  f'<span>{e(gsi)} · සාමාන්‍ය / avg per {UNIT_EN[unit]}'
                  + (f' · <span class="chg {cls}" style="font-size:11px;padding:1px 6px">{t}</span>' if t else "")
                  + '</span></div>')

    ya = None
    target = d - timedelta(days=364)
    for w in weeks:
        if abs((d_(w["date"]) - target).days) <= 4:
            ya = w
    hist = [(d_(w["date"]), N(w, main)) for w in weeks]
    hi_d, hi_v = max(hist, key=lambda t: t[1])
    lo_d, lo_v = min(hist, key=lambda t: t[1])
    yr = [t for t in hist if t[0] >= d - timedelta(days=365)]

    hi_txt_si = f" (ඉහළම රු. {money(g1h)})" if g1h else ""
    hi_txt_en = f" (highest Rs. {money(g1h)})" if g1h else ""
    s_si = (f"{fdate(d,'si')} සතියේ DEA වාර්තාව අනුව {main_si} {U_si} එකක ජාතික සාමාන්‍ය ගොවිපළ මිල රු. {money(g1)}{hi_txt_si}.")
    s_en = (f"In the DEA report for the week of {fdate(d,'en')}, the national average farm gate price of {main_en} "
            f"was Rs. {money(g1)} per {U_en}{hi_txt_en}.")
    s_ta = f"{fdate(d,'ta')} வார DEA அறிக்கையின்படி {ta} ({main_en}) தேசிய சராசரி பண்ணை விலை ரூ. {money(g1)} / {U_en}."
    if g1p:
        word_si = "ඉහළ ගොස් ඇත" if ch_cls == "up" else ("පහළ ගොස් ඇත" if ch_cls == "down" else "වෙනස් වී නැත")
        s_si += f" පෙර DEA වාර්තාවට ({fdate(dp,'si')} සතිය) සාපේක්ෂව රු. {money(g1p)} සිට {word_si}" + (f" ({ch_txt})." if ch_cls != "flat" else ".")
        s_en += (f" That is {'up' if ch_cls=='up' else 'down' if ch_cls=='down' else 'unchanged'} from Rs. {money(g1p)} "
                 f"in the previous DEA report (week of {fdate(dp,'en')})" + (f" ({ch_txt})." if ch_cls != "flat" else "."))
    if ya and N(ya, main):
        yv = N(ya, main)
        s_si += f" වසරකට පෙර ({fdate(d_(ya['date']),'si')}) මිල රු. {money(yv)} විය."
        s_en += f" A year earlier ({fdate(d_(ya['date']),'en')}) it was Rs. {money(yv)}."

    # district table: up to 3 grades
    dist = (((cur.get("commodities") or {}).get(c) or {}).get("districts") or {})
    cols = G[:3]
    rows = []
    for k, v in dist.items():
        if k == "National" or not v:
            continue
        vals = [v.get(f"{g[0]} (Average Price)") for g in cols]
        hi_ = v.get(f"{main} (Highest Price)")
        if any(vals):
            rows.append((k, vals, hi_))
    rows.sort(key=lambda r: -(r[1][0] or 0))
    head = "".join(f'<th class="n">{e(g[1])}<br>සාමාන්‍ය / Avg</th>' for g in cols)
    trs = "".join(
        f'<tr><td>{e(DISTRICT_SI.get(k, k))} <span style="color:var(--muted)">/ {e(den(k))}</span></td>'
        + "".join(f'<td class="n">{"<b>" if i == 0 else ""}{money(x) if x else "—"}{"</b>" if i == 0 else ""}</td>' for i, x in enumerate(vals))
        + '</tr>' for k, vals, hi_ in rows)
    best = rows[0] if rows and rows[0][1][0] else None
    dist_html = ""
    if rows:
        dist_html = (f'<h2>දිස්ත්‍රික්ක අනුව මිල<span>By district — week of {fdate(d,"en")}</span></h2>'
                     f'<div class="scroll"><table><thead><tr><th>දිස්ත්‍රික්කය / District</th>{head}</tr></thead><tbody>{trs}</tbody></table></div>'
                     f'<p class="asof" style="margin-top:8px">රු. / {", ".join(sorted({UNIT_SI[g[3]] for g in cols}))} · ගොවියාට ලැබෙන මිල (ගොවිපළ දොරටු) — අපනයන (FOB) හෝ සිල්ලර මිල නොවේ.</p>')

    last12 = weeks[-12:]
    g2 = G[1] if len(G) > 1 else None
    wk_rows = ""
    for w in reversed(last12):
        a_ = N(w, main); idx = weeks.index(w)
        pa = N(weeks[idx - 1], main) if idx > 0 else None
        t, cls, _ = chg(a_, pa)
        wk_rows += (f'<tr><td>{fdate(d_(w["date"]),"si")}</td><td class="n"><b>{money(a_)}</b></td>'
                    + (f'<td class="n">{money(N(w, g2[0])) if N(w, g2[0]) else "—"}</td>' if g2 else "")
                    + f'<td class="n">{f"""<span class="chg {cls}" style="font-size:11.5px;padding:2px 7px">{t}</span>""" if t else "—"}</td></tr>')

    faq = [(f"{si} මිල අද කීයද?", f"What is the {en.lower()} price today in Sri Lanka?",
            f"{fdate(d,'si')} සතියේ {main_si} {U_si} එකක ජාතික සාමාන්‍ය ගොවිපළ මිල රු. {money(g1)}{hi_txt_si}.",
            f"For the week of {fdate(d,'en')}, {main_en} averaged Rs. {money(g1)} per {U_en} at the farm gate nationally{hi_txt_en}, per DEA.")]
    if g1p:
        faq.append((f"{si} මිල ඉහළ ගියාද?", f"Did the {en.lower()} price go up or down?",
                    f"පෙර DEA වාර්තාවේ ({fdate(dp,'si')}) රු. {money(g1p)} සිට රු. {money(g1)}" + (f" ({ch_txt})." if ch_cls != "flat" else " — වෙනසක් නැත."),
                    f"From Rs. {money(g1p)} (week of {fdate(dp,'en')}) to Rs. {money(g1)}" + (f" ({ch_txt})." if ch_cls != "flat" else " — unchanged.")))
    if best and len(rows) > 1:
        faq.append((f"වැඩිම {si} මිල ලැබුණු දිස්ත්‍රික්කය?", f"Which district had the highest {en.lower()} price?",
                    f"{DISTRICT_SI.get(best[0], best[0])} — {main_si} සාමාන්‍ය රු. {money(best[1][0])}. ප්‍රවාහන වියදම හා ගුණාත්මකභාවය අනුව සැබෑ මිල වෙනස් වේ.",
                    f"{den(best[0])} — {main_en} average Rs. {money(best[1][0])}. Actual prices depend on quality and transport."))
    faq.append(("2023 සිට ඉහළම හා අඩුම මිල?", f"Highest and lowest {en.lower()} price since 2023?",
                f"{main_si} ජාතික සාමාන්‍ය: ඉහළම රු. {money(hi_v)} ({fdate(hi_d,'si')}), අඩුම රු. {money(lo_v)} ({fdate(lo_d,'si')}).",
                f"{main_en} national average: highest Rs. {money(hi_v)} ({fdate(hi_d,'en')}), lowest Rs. {money(lo_v)} ({fdate(lo_d,'en')})."))
    if sp.get("faq_grades"):
        faq.append(sp["faq_grades"])
    faq.append(("මෙම මිල ගණන් කොහෙන්ද?", "Where do these prices come from?",
                "අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුවේ (DEA) සතිපතා ගොවිපළ දොරටු මිල වාර්තාවෙන්. මේවා ගොවියාට ලැබෙන මිලයි — අපනයන (FOB) හෝ සිල්ලර මිල නොවේ.",
                "From the Department of Export Agriculture (DEA) weekly farm gate price report. These are prices paid to growers — not export (FOB) or retail prices."))
    faq_html = ('<h2>නිතර අසන ප්‍රශ්න<span>Frequently asked questions</span></h2><div class="story" style="font-size:14.5px">'
                + "".join(f'<h3 style="font-size:15.5px;margin:12px 0 4px">{e(qs)} <span style="color:var(--muted);font-weight:500">/ {e(qe)}</span></h3>'
                          f'<p style="margin:0">{e(a_)}</p><p lang="en" style="margin:2px 0 0;color:var(--soft)">{e(b_)}</p>'
                          for qs, qe, a_, b_ in faq) + '</div>')

    others = "".join(f'<a href="{o["slug"]}.html">{o["emo"]} {e(o["si"])} / {e(o["en"])}</a>' for o in SPICES if o["slug"] != sp["slug"])
    body = f"""
<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / <a href="../spices.html">කුළුබඩු මිල</a> / {e(si)}</p>
<h1>{sp['emo']} {e(si)} මිල අද</h1>
<p class="alt">{e(en)} price today in Sri Lanka · {e(sl)} mila ada · {e(si)} මිල today · {e(sp['alt_si'])}<br>{e(ta)} விலை இன்று</p>
<p class="asof" style="margin-top:14px"><b>🌾 ගොවිපළ දොරටු මිල / Farm gate price</b> · DEA සතිපතා වාර්තාව · {fdate(d,'si')} සතිය · රු./{U_si}</p>
<div class="duo">{cards}</div>
<div class="story">
  <p>{e(s_si)}</p>
  <p lang="en">{e(s_en)}</p>
  <p lang="ta">{e(s_ta)}</p>
</div>
{dist_html}
<h2>මිල ප්‍රවණතාව<span>{e(main_en)} national average since {hist[0][0].year} · weekly</span></h2>
<div class="chart">{svg_line(hist)}</div>
<p class="asof">2023 සිට ඉහළම රු. {money(hi_v)} ({fdate(hi_d,'si')}) · අඩුම රු. {money(lo_v)} ({fdate(lo_d,'si')})
 · පසුගිය වසර: රු. {money(min(v for _, v in yr))} – {money(max(v for _, v in yr))}</p>
<h2>පසුගිය DEA වාර්තා 12<span>Last 12 DEA reports · national average</span></h2>
<div class="scroll"><table><thead><tr><th>සතිය / Week</th><th class="n">{e(main_si)}</th>{f'<th class="n">{e(g2[1])}</th>' if g2 else ''}
<th class="n">වෙනස<br>vs prev. report</th></tr></thead><tbody>{wk_rows}</tbody></table></div>
<p class="asof" style="margin-top:8px">වෙනස = එක් DEA වාර්තාවක් ඊට පෙර වාර්තාවට සාපේක්ෂව (සාමාන්‍යයක් නොවේ). DEA සමහර සතිවල වාර්තා නිකුත් නොකරයි.</p>
{faq_html}
<p class="asof" style="margin-top:14px">📑 <a href="{DEA_URL}" rel="noopener">DEA නිල වාර්තාව / Official DEA report</a> ·
<a href="../spice-price-guide.html">ගොවිපළ, FOB හා සිල්ලර මිල පැහැදිලි කිරීම →</a></p>
<a class="cta" href="../spice-report.html?spice={sp['slug']}">📊 සම්පූර්ණ වාර්තාව — ශ්‍රේණි, වසරින් වසර සැසඳීම, දිස්ත්‍රික්ක / Full report →</a>
<p class="asof" style="margin-top:8px"><a href="../spices.html">සියලු කුළුබඩු මිල / All spice prices →</a></p>
<h2>අනෙක් කුළුබඩු<span>Other spice prices</span></h2>
<div class="rel">{others}</div>
"""
    title = f"{si} මිල අද ({sl.title()} Mila) | {en} Price Sri Lanka Today – TopGoviya"
    desc = (f"{si} මිල අද: {main_si} {U_si} එකක ගොවිපළ මිල රු. {money(g1)} ({fdate(d,'si')} සතිය, DEA). "
            f"{en} price in Sri Lanka today — farm gate Rs. {money(g1)}/{U_en}, by district, weekly trend since 2023. "
            f"{sl} mila today, {en.lower()} price sri lanka.")
    first = hist[0][0]
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Spice prices", "item": SITE + "/spices.html"},
            {"@type": "ListItem", "position": 3, "name": f"{en} price", "item": url}]},
        {"@type": "Dataset", "name": f"{en} farm gate price in Sri Lanka – weekly, by district",
         "description": (f"Weekly farm gate (producers') prices of {en.lower()} in Sri Lanka by grade and district, "
                         f"from the Department of Export Agriculture, {fdate(first,'en')} to {fdate(d,'en')}. "
                         f"Latest {main_en} national average Rs. {money(g1)} per {U_en}."),
         "url": url, "inLanguage": ["si", "en", "ta"], "spatialCoverage": "Sri Lanka",
         "temporalCoverage": f"{first.isoformat()}/{d.isoformat()}", "dateModified": d.isoformat(),
         "variableMeasured": f"{en} farm gate price (Rs./{U_en})", "isBasedOn": DEA_URL,
         "creator": {"@type": "Organization", "name": "TopGoviya.lk", "url": SITE + "/"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": qe, "acceptedAnswer": {"@type": "Answer", "text": b_}} for qs, qe, a_, b_ in faq]}]}
    # link preview picture made weekly by make_daily_image.py (share/spice-<slug>.png)
    image = f"{SITE}/share/spice-{sp['slug']}.png?v={cur['date']}"
    alts = None
    if sp["slug"] in EN_PAGES:
        en_url = f"{SITE}/{OUT_DIR}/{EN_PAGES[sp['slug']]['file']}.html"
        alts = [("si", url), ("en", en_url)]
        en_cfg = EN_PAGES[sp["slug"]]
        en_link = ('<p class="asof" style="margin-top:8px">🌍 <a href="' + en_cfg["file"] + '.html">English: '
                   + en_cfg["h1"] + ' (LKR &amp; US$) →</a></p>\n')
        body = body.replace('<p class="asof" style="margin-top:14px"><b>🌾', en_link + '<p class="asof" style="margin-top:14px"><b>🌾', 1)
    return shell(title, desc, url, body, jsonld, image, alternates=alts), cur["date"]


# ---------------------------------------------------------------- English pages (foreign buyers)
# Same DEA data, written for buyers abroad: LKR + USD per kg, grades, farm gate vs FOB.
EN_PAGES = {
 "cinnamon": {
  "file": "ceylon-cinnamon-price", "name": "Ceylon cinnamon", "emo": "🪵",
  "h1": "Ceylon Cinnamon Price Today",
  "title": "Ceylon Cinnamon Price Today – Sri Lanka Farm Gate Price per kg (LKR & USD) | TopGoviya",
  "grades": [("Alba", "Alba", "the thinnest, finest quills — the top grade"),
             ("C-5 Sp", "C-5 Special", "fine Continental quills"),
             ("C-5", "C-5", "Continental — the most widely quoted grade"),
             ("C-4", "C-4", "Continental, slightly thicker than C-5"),
             ("M-5", "M-5", "Mexican grade — thicker quills"),
             ("M-4", "M-4", "Mexican grade"),
             ("H-1", "H-1", "Hamburg grade — thicker, coarser quills"),
             ("H-2", "H-2", "Hamburg grade"),
             ("H-Faq", "H-FAQ", "Hamburg, fair average quality"),
             ("Heen", "Heen", "small broken pieces (quillings)"),
             ("Gorosu", "Gorosu", "coarse, thick bark pieces")],
  "main": "C-5",
  "extra": """<h2>Ceylon cinnamon vs cassia</h2><div class="story" style="font-size:14.5px">
<p><b>Ceylon cinnamon</b> (<i>Cinnamomum verum</i>, "true cinnamon") is the cinnamon grown in Sri Lanka. Its quills are made of many thin,
paper-like layers rolled together, light tan in colour, with a mild, sweet aroma.</p>
<p><b>Cassia</b> (Chinese, Indonesian or Vietnamese cinnamon) is a different species. Its bark is a single thick, hard layer, darker and
stronger tasting, and it contains <b>much more coumarin</b> than Ceylon cinnamon. That is why many buyers specifically look for Ceylon cinnamon.</p>
<p>Ceylon cinnamon is graded mainly by <b>quill thickness</b>: Alba is the finest, followed by the Continental (C), Mexican (M) and
Hamburg (H) groups. The table above shows how the price falls as the quills get thicker.</p></div>""",
 },
 "pepper": {
  "file": "sri-lanka-black-pepper-price", "name": "Sri Lankan black pepper", "emo": "⚫",
  "h1": "Sri Lanka Black Pepper Price Today",
  "title": "Sri Lanka Black Pepper Price Today – GR-1 & White Pepper Farm Gate Price per kg (LKR & USD) | TopGoviya",
  "grades": [("GR-1", "GR-1 black pepper", "the top black pepper grade — dense, clean berries"),
             ("GR-2", "GR-2 black pepper", "the second black pepper grade"),
             ("WHITE", "White pepper", "pepper with the outer skin removed")],
  "main": "GR-1",
  "extra": """<h2>About Sri Lankan pepper grades</h2><div class="story" style="font-size:14.5px">
<p>DEA reports Sri Lankan black pepper in two grades. <b>GR-1</b> is the higher grade (heavier, denser, cleaner berries);
<b>GR-2</b> is the next grade. <b>White pepper</b> is made by removing the outer skin, so it sells for more per kg.</p>
<p>Export buyers often also specify <b>bulk density</b> (for example 550 g/L) and moisture. Our
<a href="../spice-price-guide.html">spice price guide</a> explains these terms.</p></div>""",
 },
}


def usd_rate_for(dei, day):
    """CBSL indicative USD/LKR spot rate for the DEA week (nearest earlier day), with its date."""
    recs = [r for r in (dei or {}).get("records", []) if r.get("usd_lkr_spot") or r.get("usd_lkr")]
    if not recs:
        return None, None
    before = [r for r in recs if r["date"] <= day.isoformat()]
    r = before[-1] if before else recs[0]
    rate = r.get("usd_lkr_spot") or ((r.get("usd_lkr", 0) + r.get("usd_lkr_sell", r.get("usd_lkr", 0))) / 2)
    return rate, d_(r["date"])


def usd(v, rate):
    return f"US$ {v / rate:,.2f}" if (v and rate) else "—"


def spice_page_en(dea, sp, cfg, dei):
    c = sp["c"]
    N = lambda w, g, k="Average": nat(w, g, k, c)
    main = cfg["main"]
    weeks = [w for w in dea["weeks"] if N(w, main)]
    if len(weeks) < 2:
        return None, None
    cur, prev = weeks[-1], weeks[-2]
    d, dp = d_(cur["date"]), d_(prev["date"])
    url = f"{SITE}/{OUT_DIR}/{cfg['file']}.html"
    rate, rate_d = usd_rate_for(dei, d)
    g1, g1p, g1h = N(cur, main), N(prev, main), N(cur, main, "Highest")
    t_main, cls_main, _ = chg(g1, g1p)

    # grade table
    trs = ""
    for key, name, note in cfg["grades"]:
        a, ap, hi = N(cur, key), N(prev, key), N(cur, key, "Highest")
        if not a:
            continue
        t, cls, _ = chg(a, ap)
        trs += (f'<tr><td><b>{e(name)}</b><br><small style="color:var(--muted)">{e(note)}</small></td>'
                f'<td class="n"><b>Rs. {money(a)}</b></td><td class="n">{usd(a, rate)}</td>'
                f'<td class="n rng">{money(hi) if hi else "—"}</td>'
                f'<td class="n">{f"""<span class="chg {cls}" style="font-size:11.5px;padding:2px 7px">{t}</span>""" if t else "—"}</td></tr>')

    hist = [(d_(w["date"]), N(w, main)) for w in weeks]
    hi_d, hi_v = max(hist, key=lambda t: t[1])
    lo_d, lo_v = min(hist, key=lambda t: t[1])
    ya = next((w for w in weeks if abs((d_(w["date"]) - (d - timedelta(days=364))).days) <= 4), None)
    yv = N(ya, main) if ya else None
    main_name = next(n for k, n, _ in cfg["grades"] if k == main)

    # districts (main grade)
    dist = (((cur.get("commodities") or {}).get(c) or {}).get("districts") or {})
    drows = sorted([(k, v.get(f"{main} (Average Price)")) for k, v in dist.items() if k != "National" and v and v.get(f"{main} (Average Price)")],
                   key=lambda r: -r[1])
    dtrs = "".join(f'<tr><td>{e(den(k))}</td><td class="n"><b>Rs. {money(v)}</b></td><td class="n">{usd(v, rate)}</td></tr>' for k, v in drows)

    rate_txt = (f"US$ prices use the Central Bank of Sri Lanka indicative USD/LKR spot rate of Rs. {rate:,.2f} "
                f"({fdate(rate_d, 'en')}), for reference only." if rate else "")
    story = (f"In the Department of Export Agriculture (DEA) report for the week of {fdate(d,'en')}, {cfg['name']} "
             f"({main_name}) averaged <b>Rs. {money(g1)} per kg</b> at the farm gate across Sri Lanka "
             f"(≈ <b>{usd(g1, rate)}</b>/kg)" + (f", highest Rs. {money(g1h)}" if g1h else "") + ". "
             + (f"That is {'up' if cls_main == 'up' else 'down' if cls_main == 'down' else 'unchanged'} from Rs. {money(g1p)} "
                f"in the previous DEA report (week of {fdate(dp,'en')})" + (f" ({t_main})" if cls_main != "flat" else "") + ". " if g1p else "")
             + (f"A year earlier ({fdate(d_(ya['date']),'en')}) it was Rs. {money(yv)}." if yv else ""))

    faq = [(f"What is the {cfg['name']} price today?",
            f"For the week of {fdate(d,'en')}, {main_name} averaged Rs. {money(g1)} per kg at the farm gate in Sri Lanka "
            f"(about {usd(g1, rate)} per kg), according to the Department of Export Agriculture."),
           ("Is this the export (FOB) price?",
            "No. These are farm gate prices — what growers receive. Export (FOB) prices are higher because they include "
            "processing, grading, cleaning, fumigation, packing, transport and the exporter's margin."),
           (f"What were the highest and lowest prices since {hist[0][0].year}?",
            f"{main_name} national average: highest Rs. {money(hi_v)} ({fdate(hi_d,'en')}), lowest Rs. {money(lo_v)} ({fdate(lo_d,'en')})."),
           ("How are the US$ prices calculated?",
            rate_txt or "US$ prices are not available this week."),
           ("Where does the data come from, and how often is it updated?",
            "From the Department of Export Agriculture (DEA), Sri Lanka, weekly producers' (farm gate) price report. "
            "This page updates automatically when DEA publishes a new week. TopGoviya.lk is independent and does not buy or sell spices.")]
    faq_html = ('<h2>Frequently asked questions</h2><div class="story" style="font-size:14.5px">'
                + "".join(f'<h3 style="font-size:15.5px;margin:12px 0 4px">{e(q)}</h3><p style="margin:0">{e(a)}</p>' for q, a in faq) + '</div>')

    si_url = f"{SITE}/{OUT_DIR}/{sp['slug']}.html"
    body = f"""
<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / <a href="../spices.html">Spice prices</a> / {e(cfg['name'])}</p>
<h1>{cfg['emo']} {e(cfg['h1'])}</h1>
<p class="alt">Weekly farm gate price in Sri Lanka · LKR and US$ per kg · <a href="{sp['slug']}.html">සිංහල: {e(sp['si'])} මිල අද →</a></p>
<p class="asof" style="margin-top:14px"><b>🌾 Farm gate price</b> · DEA weekly report · week of {fdate(d,'en')} · per kg</p>
<div class="duo"><div class="r"><b>Rs. {money(g1)}</b><span>{e(main_name)} · national average
{f' · <span class="chg {cls_main}" style="font-size:11px;padding:1px 6px">{t_main}</span>' if t_main else ''}</span></div>
<div class="w"><b>{usd(g1, rate)}</b><span>per kg · at CBSL rate {f"Rs. {rate:,.2f}" if rate else ""}</span></div></div>
<div class="story"><p lang="en">{story}</p></div>
<h2>Prices by grade<span>Week of {fdate(d,'en')} · national average, per kg</span></h2>
<div class="scroll"><table><thead><tr><th>Grade</th><th class="n">LKR / kg</th><th class="n">≈ US$ / kg</th>
<th class="n">Highest<br>LKR</th><th class="n">vs prev.<br>report</th></tr></thead><tbody>{trs}</tbody></table></div>
<p class="asof" style="margin-top:8px">{e(rate_txt)} Farm gate prices — not export (FOB) or retail prices.</p>
<h2>Price trend<span>{e(main_name)} · national average since {hist[0][0].year} · LKR per kg</span></h2>
<div class="chart">{svg_line(hist, lang="en")}</div>
<p class="asof">Highest since {hist[0][0].year}: Rs. {money(hi_v)} ({fdate(hi_d,'en')}) · lowest Rs. {money(lo_v)} ({fdate(lo_d,'en')})
{f" · a year ago: Rs. {money(yv)}" if yv else ""}</p>
<h2>By growing district<span>{e(main_name)} · week of {fdate(d,'en')}</span></h2>
<div class="scroll"><table><thead><tr><th>District</th><th class="n">LKR / kg</th><th class="n">≈ US$ / kg</th></tr></thead><tbody>{dtrs}</tbody></table></div>
{cfg['extra']}
{faq_html}
<p class="asof" style="margin-top:14px">📑 <a href="{DEA_URL}" rel="noopener">Official DEA report</a> ·
<a href="../spice-report.html?spice={sp['slug']}">📊 Full report: all grades, year-on-year</a> · <a href="{sp['slug']}.html">සිංහල පිටුව</a></p>
<a class="cta" href="../spices.html">All Sri Lanka spice prices →</a>
"""
    desc = (f"{cfg['h1']}: {main_name} Rs. {money(g1)}/kg (≈ {usd(g1, rate)}) farm gate, week of {fdate(d,'en')} (DEA). "
            f"All grades, districts and weekly trend since {hist[0][0].year}.")
    first = hist[0][0]
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Spice prices", "item": SITE + "/spices.html"},
            {"@type": "ListItem", "position": 3, "name": cfg["h1"], "item": url}]},
        {"@type": "Dataset", "name": f"{cfg['name'].capitalize()} farm gate price in Sri Lanka – weekly, by grade and district",
         "description": (f"Weekly farm gate prices of {cfg['name']} in Sri Lanka by grade and district from the Department of Export "
                         f"Agriculture, {fdate(first,'en')} to {fdate(d,'en')}, with US$ reference prices. Latest {main_name} Rs. {money(g1)} per kg."),
         "url": url, "inLanguage": "en", "spatialCoverage": "Sri Lanka",
         "temporalCoverage": f"{first.isoformat()}/{d.isoformat()}", "dateModified": d.isoformat(),
         "variableMeasured": f"{cfg['name']} farm gate price (LKR per kg)", "isBasedOn": DEA_URL,
         "creator": {"@type": "Organization", "name": "TopGoviya.lk", "url": SITE + "/"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}]}
    image = f"{SITE}/share/spice-{sp['slug']}.png?v={cur['date']}"
    page = shell(cfg["title"], desc, url, body, jsonld, image, lang="en", alternates=[("en", url), ("si", si_url)])
    return page.replace("කුළුබඩු මිල / Spice prices</a>", "Spice prices</a>").replace("📞 අමතන්න</a>", "📞 Contact</a>"), cur["date"]


def update_sitemap(slugs, lastmod):
    path = "sitemap.xml"
    if not os.path.exists(path):
        return
    xml = open(path, encoding="utf-8").read()
    xml = re.sub(r"\s*<url>\s*<loc>[^<]*/" + OUT_DIR + r"/[^<]*</loc>.*?</url>", "", xml, flags=re.S)
    new = "".join(f"  <url>\n    <loc>{SITE}/{OUT_DIR}/{s}.html</loc>\n    <lastmod>{lastmod}</lastmod>\n"
                  f"    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n" for s in slugs)
    xml = xml.replace("</urlset>", new + "</urlset>")
    open(path, "w", encoding="utf-8").write(xml)


def main():
    dea = json.load(open("dea_data.json", encoding="utf-8"))
    os.makedirs(OUT_DIR, exist_ok=True)
    made, latest = [], ""
    for sp in SPICES:
        page, wk = spice_page(dea, sp)
        if not page:
            print(f"  {sp['slug']}: no data, skipped"); continue
        open(os.path.join(OUT_DIR, sp["slug"] + ".html"), "w", encoding="utf-8").write(page)
        made.append(sp["slug"]); latest = max(latest, wk)
        print(f"  {sp['slug']:10} DEA week {wk}")
    try:
        dei = json.load(open("dei_data.json", encoding="utf-8"))
    except Exception:
        dei = None
    for sp in SPICES:
        cfg = EN_PAGES.get(sp["slug"])
        if not cfg:
            continue
        page, wk = spice_page_en(dea, sp, cfg, dei)
        if page:
            open(os.path.join(OUT_DIR, cfg["file"] + ".html"), "w", encoding="utf-8").write(page)
            made.append(cfg["file"]); print(f"  {cfg['file']} (English)")
    if made:
        update_sitemap(made, latest)
    print(f"Built {len(made)} spice pages, sitemap updated.")


if __name__ == "__main__":
    main()
