"""
build_spice_pages.py  -  TopGoviya.lk spice landing pages (DEA weekly farm-gate prices)
---------------------------------------------------------------------------------------
Reads dea_data.json and writes:
  spice/pepper.html   "ගම්මිරිස් මිල අද" - black pepper farm-gate price page
  sitemap.xml         keeps every other page, adds/refreshes /spice/ entries

Prices are the Department of Export Agriculture (DEA) weekly producers' (farm gate)
prices. Weekly change = latest DEA week vs the week before (single weeks, not averages).
Runs daily from GitHub Actions; the page only changes when DEA publishes a new week.
Uses build_pages.py (same folder) for the shared look.
"""
import json, os, re
from datetime import datetime, timedelta

from build_pages import CSS, GA_ID, SITE, e, money, fdate

OUT_DIR = "spice"
DEA_URL = "https://exagri.info/mkt/index.html"

DISTRICT_SI = {"Kandy": "මහනුවර", "Matale": "මාතලේ", "Nuwara_eliya": "නුවරඑළිය", "Kegalle": "කෑගල්ල",
               "Ratnapura": "රත්නපුර", "Badulla": "බදුල්ල", "Kurunegala": "කුරුණෑගල", "Colombo": "කොළඹ",
               "Gampaha": "ගම්පහ", "Kalutara": "කළුතර", "Galle": "ගාල්ල", "Matara": "මාතර",
               "Hambantota": "හම්බන්තොට", "Monaragala": "මොනරාගල"}
DISTRICT_EN = {"Nuwara_eliya": "Nuwara Eliya"}

# key, Sinhala, English, column prefix in dea_data.json
GRADES = [("GR-1", "GR-1 (කළු ගම්මිරිස්)", "GR-1 black pepper"),
          ("GR-2", "GR-2", "GR-2 black pepper"),
          ("WHITE", "සුදු ගම්මිරිස්", "White pepper")]


def d_(s): return datetime.strptime(s, "%Y-%m-%d").date()
def den(x): return DISTRICT_EN.get(x, x)


def nat(week, grade, kind="Average"):
    v = (((week.get("commodities") or {}).get("pepper") or {}).get("districts") or {}).get("National") or {}
    return v.get(f"{grade} ({kind} Price)")


def chg(now, old):
    if not now or not old:
        return "", "flat", ""
    pct = (now - old) / old * 100
    cls = "flat" if abs(pct) < 0.5 else ("up" if pct > 0 else "down")
    arrow = {"up": "▲", "down": "▼", "flat": "■"}[cls]
    return f'{arrow} {"+" if pct > 0 else ""}{pct:.1f}%', cls, pct


def svg_line(points, w=640, h=170):
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
    return (f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;display:block" role="img" '
            f'aria-label="Black pepper GR-1 national average price trend">{grid}{lab}'
            f'<path d="{path}" fill="none" stroke="#0e4f4a" stroke-width="2.2"/>'
            f'<circle cx="{X(d_):.1f}" cy="{Y(v_):.1f}" r="3.5" fill="#a9802a"/></svg>')


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
.chart{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px 12px;margin:10px 0}}
</style>
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="../index.html">TopGoviya.lk</a><a href="../spices.html">කුළුබඩු මිල / Spice prices</a></header>
{body}
<p class="note">මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.<br>
Prices are indicative only. Decisions are your responsibility. Source: Department of Export Agriculture (DEA) weekly
producers' (farm gate) prices — <a href="{DEA_URL}" rel="noopener">exagri.info</a>. Not an official publication.
<a href="../data-sources.html">How we collect the data →</a> · මිලක් වැරදි යැයි සිතේද? <a href="../data-sources.html">අපට දන්වන්න</a><br>
விலைகள் வழிகாட்டல் மட்டுமே. உங்கள் முடிவுகளுக்கு நீங்களே பொறுப்பு.</p>
<footer>Design &amp; development by <a href="https://ebooklanka.com" target="_blank" rel="noopener">ebooklanka.com</a> · Built in Gampola, Sri Lanka</footer>
</div>
</body>
</html>
"""


def pepper_page(dea):
    weeks = [w for w in dea["weeks"] if nat(w, "GR-1")]
    if len(weeks) < 2:
        return None, None
    cur, prev = weeks[-1], weeks[-2]
    d, dp = d_(cur["date"]), d_(prev["date"])
    url = f"{SITE}/{OUT_DIR}/pepper.html"

    # ---- headline cards
    g1, g1p = nat(cur, "GR-1"), nat(prev, "GR-1")
    g1h = nat(cur, "GR-1", "Highest")
    ch_txt, ch_cls, ch_pct = chg(g1, g1p)
    cards = ""
    for key, si, en in GRADES:
        a, ap = nat(cur, key), nat(prev, key)
        if not a:
            continue
        t, cls, _ = chg(a, ap)
        cards += (f'<div class="{"r" if key == "GR-1" else "w"}"><b>රු. {money(a)}</b>'
                  f'<span>{e(si)} · සාමාන්‍ය / avg per kg'
                  + (f' · <span class="chg {cls}" style="font-size:11px;padding:1px 6px">{t}</span>' if t else "")
                  + '</span></div>')

    # ---- year ago, range since 2023
    ya = None
    target = d - timedelta(days=364)
    for w in weeks:
        if abs((d_(w["date"]) - target).days) <= 4:
            ya = w
    hist = [(d_(w["date"]), nat(w, "GR-1")) for w in weeks]
    hi_d, hi_v = max(hist, key=lambda t: t[1])
    lo_d, lo_v = min(hist, key=lambda t: t[1])
    yr = [t for t in hist if t[0] >= d - timedelta(days=365)]

    # ---- story (3 languages)
    s_si = (f"{fdate(d,'si')} සතියේ DEA වාර්තාව අනුව GR-1 කළු ගම්මිරිස් කිලෝවක ජාතික සාමාන්‍ය ගොවිපළ මිල රු. {money(g1)} "
            f"(ඉහළම රු. {money(g1h)}).")
    s_en = (f"In the DEA report for the week of {fdate(d,'en')}, the national average farm gate price of GR-1 black pepper "
            f"was Rs. {money(g1)} per kg (highest Rs. {money(g1h)}).")
    s_ta = f"{fdate(d,'ta')} வார DEA அறிக்கையின்படி GR-1 கருப்பு மிளகு தேசிய சராசரி பண்ணை விலை ஒரு கிலோ ரூ. {money(g1)}."
    if g1p:
        word_si = "ඉහළ ගොස් ඇත" if ch_cls == "up" else ("පහළ ගොස් ඇත" if ch_cls == "down" else "වෙනස් වී නැත")
        s_si += f" පෙර DEA වාර්තාවට ({fdate(dp,'si')} සතිය) සාපේක්ෂව රු. {money(g1p)} සිට {word_si}" + (f" ({ch_txt})." if ch_cls != "flat" else ".")
        s_en += (f" That is {'up' if ch_cls=='up' else 'down' if ch_cls=='down' else 'unchanged'} from Rs. {money(g1p)} "
                 f"in the previous DEA report (week of {fdate(dp,'en')})" + (f" ({ch_txt})." if ch_cls != "flat" else "."))
    if ya and nat(ya, "GR-1"):
        yv = nat(ya, "GR-1")
        s_si += f" වසරකට පෙර ({fdate(d_(ya['date']),'si')}) මිල රු. {money(yv)} විය."
        s_en += f" A year earlier ({fdate(d_(ya['date']),'en')}) it was Rs. {money(yv)}."

    # ---- district table (latest week)
    dist = (((cur.get("commodities") or {}).get("pepper") or {}).get("districts") or {})
    rows = []
    for k, v in dist.items():
        if k == "National" or not v:
            continue
        a, h_, wa = v.get("GR-1 (Average Price)"), v.get("GR-1 (Highest Price)"), v.get("WHITE (Average Price)")
        if a or wa:
            rows.append((k, a, h_, wa))
    rows.sort(key=lambda r: -(r[1] or 0))
    trs = "".join(
        f'<tr><td>{e(DISTRICT_SI.get(k, k))} <span style="color:var(--muted)">/ {e(den(k))}</span></td>'
        f'<td class="n"><b>{money(a) if a else "—"}</b></td><td class="n rng">{money(h_) if h_ else "—"}</td>'
        f'<td class="n">{money(wa) if wa else "—"}</td></tr>' for k, a, h_, wa in rows)
    best = rows[0] if rows and rows[0][1] else None

    # ---- last 12 weeks table
    last12 = weeks[-12:]
    wk_rows = ""
    for i, w in enumerate(reversed(last12)):
        a = nat(w, "GR-1"); idx = weeks.index(w)
        pa = nat(weeks[idx - 1], "GR-1") if idx > 0 else None
        t, cls, _ = chg(a, pa)
        wk_rows += (f'<tr><td>{fdate(d_(w["date"]),"si")}</td><td class="n"><b>{money(a)}</b></td>'
                    f'<td class="n">{money(nat(w, "WHITE")) if nat(w, "WHITE") else "—"}</td>'
                    f'<td class="n">{f"""<span class="chg {cls}" style="font-size:11.5px;padding:2px 7px">{t}</span>""" if t else "—"}</td></tr>')

    # ---- FAQ
    faq = [("ගම්මිරිස් මිල අද කීයද?", "What is the black pepper price today in Sri Lanka?",
            f"{fdate(d,'si')} සතියේ GR-1 කළු ගම්මිරිස් කිලෝවක ජාතික සාමාන්‍ය ගොවිපළ මිල රු. {money(g1)} (ඉහළම රු. {money(g1h)}).",
            f"For the week of {fdate(d,'en')}, GR-1 black pepper averaged Rs. {money(g1)} per kg at the farm gate nationally (highest Rs. {money(g1h)}), per DEA.")]
    if g1p:
        faq.append(("ගම්මිරිස් මිල ඉහළ ගියාද?", "Did the pepper price go up or down?",
                    f"පෙර DEA වාර්තාවේ ({fdate(dp,'si')}) රු. {money(g1p)} සිට රු. {money(g1)}" + (f" ({ch_txt})." if ch_cls != "flat" else " — වෙනසක් නැත."),
                    f"From Rs. {money(g1p)} (week of {fdate(dp,'en')}) to Rs. {money(g1)}" + (f" ({ch_txt})." if ch_cls != "flat" else " — unchanged.")))
    if best:
        faq.append(("වැඩිම ගම්මිරිස් මිල ලැබුණු දිස්ත්‍රික්කය?", "Which district had the highest pepper price?",
                    f"{DISTRICT_SI.get(best[0], best[0])} — GR-1 සාමාන්‍ය රු. {money(best[1])}. ප්‍රවාහන වියදම හා ගුණාත්මකභාවය අනුව සැබෑ මිල වෙනස් වේ.",
                    f"{den(best[0])} — GR-1 average Rs. {money(best[1])}. Actual prices depend on quality and transport."))
    faq.append(("2023 සිට ඉහළම හා අඩුම මිල?", "Highest and lowest pepper price since 2023?",
                f"GR-1 ජාතික සාමාන්‍ය: ඉහළම රු. {money(hi_v)} ({fdate(hi_d,'si')}), අඩුම රු. {money(lo_v)} ({fdate(lo_d,'si')}).",
                f"GR-1 national average: highest Rs. {money(hi_v)} ({fdate(hi_d,'en')}), lowest Rs. {money(lo_v)} ({fdate(lo_d,'en')})."))
    faq.append(("GR-1, GR-2 හා සුදු ගම්මිරිස් අතර වෙනස?", "What is the difference between GR-1, GR-2 and white pepper?",
                "GR-1 යනු ඉහළම ශ්‍රේණියේ කළු ගම්මිරිස් (ඝනත්වය වැඩි, පිරිසිදු); GR-2 ඊට පහළ ශ්‍රේණියයි. සුදු ගම්මිරිස් පොත්ත ඉවත් කළ ඒවා බැවින් මිල වැඩිය.",
                "GR-1 is the top grade of black pepper (denser, cleaner); GR-2 is the next grade. White pepper has the outer skin removed and sells higher."))
    faq.append(("මෙම මිල ගණන් කොහෙන්ද?", "Where do these prices come from?",
                "අපනයන කෘෂිකර්ම දෙපාර්තමේන්තුවේ (DEA) සතිපතා ගොවිපළ දොරටු මිල වාර්තාවෙන්. මේවා ගොවියාට ලැබෙන මිලයි — අපනයන (FOB) හෝ සිල්ලර මිල නොවේ.",
                "From the Department of Export Agriculture (DEA) weekly farm gate price report. These are prices paid to growers — not export (FOB) or retail prices."))
    faq_html = ('<h2>නිතර අසන ප්‍රශ්න<span>Frequently asked questions</span></h2><div class="story" style="font-size:14.5px">'
                + "".join(f'<h3 style="font-size:15.5px;margin:12px 0 4px">{e(qs)} <span style="color:var(--muted);font-weight:500">/ {e(qe)}</span></h3>'
                          f'<p style="margin:0">{e(a_)}</p><p lang="en" style="margin:2px 0 0;color:var(--soft)">{e(b_)}</p>'
                          for qs, qe, a_, b_ in faq) + '</div>')

    body = f"""
<p class="crumb"><a href="../index.html">TopGoviya.lk</a> / <a href="../spices.html">කුළුබඩු මිල</a> / ගම්මිරිස්</p>
<h1>⚫ ගම්මිරිස් මිල අද</h1>
<p class="alt">Black pepper price today in Sri Lanka · gammiris mila ada · ගම්මිරිස් මිල today · කළු ගම්මිරිස් කිලෝවක මිල<br>மிளகு விலை இன்று</p>
<p class="asof" style="margin-top:14px"><b>🌾 ගොවිපළ දොරටු මිල / Farm gate price</b> · DEA සතිපතා වාර්තාව · {fdate(d,'si')} සතිය · රු./කි.ග්‍රෑ.</p>
<div class="duo">{cards}</div>
<div class="story">
  <p>{e(s_si)}</p>
  <p lang="en">{e(s_en)}</p>
  <p lang="ta">{e(s_ta)}</p>
</div>
<h2>දිස්ත්‍රික්ක අනුව මිල<span>By district — week of {fdate(d,'en')}</span></h2>
<div class="scroll"><table><thead><tr><th>දිස්ත්‍රික්කය / District</th><th class="n">GR-1<br>සාමාන්‍ය / Avg</th>
<th class="n">GR-1<br>ඉහළම / Highest</th><th class="n">සුදු<br>White avg</th></tr></thead><tbody>{trs}</tbody></table></div>
<p class="asof" style="margin-top:8px">රු. / කි.ග්‍රෑ. · ගොවියාට ලැබෙන මිල (ගොවිපළ දොරටු) — අපනයන (FOB) හෝ සිල්ලර මිල නොවේ.</p>
<h2>මිල ප්‍රවණතාව<span>GR-1 national average since {hist[0][0].year} · weekly</span></h2>
<div class="chart">{svg_line(hist)}</div>
<p class="asof">2023 සිට ඉහළම රු. {money(hi_v)} ({fdate(hi_d,'si')}) · අඩුම රු. {money(lo_v)} ({fdate(lo_d,'si')})
 · පසුගිය වසර: රු. {money(min(v for _, v in yr))} – {money(max(v for _, v in yr))}</p>
<h2>පසුගිය සති 12<span>Last 12 DEA weeks · national average</span></h2>
<div class="scroll"><table><thead><tr><th>සතිය / Week</th><th class="n">GR-1</th><th class="n">සුදු<br>White</th>
<th class="n">වෙනස<br>vs prev. report</th></tr></thead><tbody>{wk_rows}</tbody></table></div>
<p class="asof" style="margin-top:8px">වෙනස = එක් DEA වාර්තාවක් ඊට පෙර වාර්තාවට සාපේක්ෂව (සාමාන්‍යයක් නොවේ). DEA සමහර සතිවල වාර්තා නිකුත් නොකරයි.</p>
{faq_html}
<p class="asof" style="margin-top:14px">📑 <a href="{DEA_URL}" rel="noopener">DEA නිල වාර්තාව / Official DEA report</a> ·
<a href="../spice-price-guide.html">GR-1, 550 GL හා FOB පැහැදිලි කිරීම →</a></p>
<a class="cta" href="../spices.html">සියලු කුළුබඩු මිල — කුරුඳු, කරාබු, එනසාල්… / All spice prices →</a>
"""
    title = "ගම්මිරිස් මිල අද (Gammiris Mila) | Black Pepper Price Sri Lanka Today – TopGoviya"
    desc = (f"ගම්මිරිස් මිල අද: GR-1 කළු ගම්මිරිස් කිලෝවක ගොවිපළ මිල රු. {money(g1)} ({fdate(d,'si')} සතිය, DEA). "
            f"Black pepper price in Sri Lanka today — farm gate Rs. {money(g1)}/kg, by district, weekly trend since 2023. "
            f"gammiris mila today, pepper price sri lanka.")
    first = hist[0][0]
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Spice prices", "item": SITE + "/spices.html"},
            {"@type": "ListItem", "position": 3, "name": "Black pepper price", "item": url}]},
        {"@type": "Dataset", "name": "Black pepper farm gate price in Sri Lanka – weekly, by district",
         "description": (f"Weekly farm gate (producers') prices of black pepper GR-1, GR-2 and white pepper in Sri Lanka by district, "
                         f"from the Department of Export Agriculture, {fdate(first,'en')} to {fdate(d,'en')}. "
                         f"Latest GR-1 national average Rs. {money(g1)} per kg."),
         "url": url, "inLanguage": ["si", "en", "ta"], "spatialCoverage": "Sri Lanka",
         "temporalCoverage": f"{first.isoformat()}/{d.isoformat()}", "dateModified": d.isoformat(),
         "variableMeasured": "Black pepper farm gate price (Rs./kg)", "isBasedOn": DEA_URL,
         "creator": {"@type": "Organization", "name": "TopGoviya.lk", "url": SITE + "/"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": qe, "acceptedAnswer": {"@type": "Answer", "text": b_}} for qs, qe, a_, b_ in faq]}]}
    return shell(title, desc, url, body, jsonld), cur["date"]


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
    page, wk = pepper_page(dea)
    if not page:
        print("No pepper data - nothing built."); return
    open(os.path.join(OUT_DIR, "pepper.html"), "w", encoding="utf-8").write(page)
    update_sitemap(["pepper"], wk)
    print(f"Built spice/pepper.html (DEA week {wk}), sitemap updated.")


if __name__ == "__main__":
    main()
