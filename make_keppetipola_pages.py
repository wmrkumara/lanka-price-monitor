"""
make_keppetipola_pages.py  -  TopGoviya.lk: one page per Keppetipola DEC item
------------------------------------------------------------------------------
Same idea as make_dambulla_pages.py, for Keppetipola. Builds, from keppetipola_dec.json:
  keppetipola/<item>.html     e.g. keppetipola/carrot.html  ("කැරට් මිල අද කැප්පෙටිපොල")
  keppetipola/index.html      list of all items by category
and adds the pages to sitemap.xml.  Run after keppetipola_dec.json changes
(in the "Apply manual DEC prices" robot).
Uses the design and helpers of make_dambulla_pages.py, so both markets look the same.
"""
import json, os, re, urllib.parse
from datetime import date

from make_dambulla_pages import (CSS, GA, SITE, si_date, dot_date, slug, pct, chg_html,
                                 svg_chart, money, e)
from build_keppetipola_page import CAT as KCAT, EXTRA

OUT = "keppetipola"
MARKET_SI = "කැප්පෙටිපොල"
MARKET_FULL_SI = "කෑප්පෙටිපොළ විශේෂිත ආර්ථික මධ්‍යස්ථානය"
MARKET_EN = "Keppetipola"
MARKET_PAGE = "../market/keppetipola.html"
IMG = f"{SITE}/icon-512x512.png"
CATS = {"v": ("🥬", "එළවළු", "Vegetables"), "l": ("🌿", "පලා වර්ග", "Leafy vegetables"),
        "r": ("🥔", "අල වර්ග", "Roots & tubers"), "f": ("🍍", "පලතුරු", "Fruits"), "g": ("🌾", "ධාන්‍ය", "Grains")}
DEF_EMOJI = {"v": "🥬", "l": "🌿", "r": "🥔", "g": "🌾", "f": "🍎"}


def load():
    kep = json.load(open("keppetipola_dec.json", encoding="utf-8"))
    days = {d: {str(k): v for k, v in p.items()} for d, p in kep.get("days", {}).items()}
    try:
        dam = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    except Exception:
        dam = {}
    by_si = {v["si"].strip(): v for v in dam.values()}
    by_en = {v["en"].lower(): v for v in dam.values()}
    names = {}
    for it in kep["items"]:
        c = KCAT.get(it.get("cat", ""), "v")
        si, en = it["si"].strip(), it["en"]
        d = by_si.get(si) or by_en.get(en.lower())
        if d:
            ta, emo, pop = d.get("ta", en), d.get("e", DEF_EMOJI[c]), d.get("pop", 50)
            dlink = slug(d["en"]) if os.path.exists(f"dambulla/{slug(d['en'])}.html") else None
        else:
            ta, emo, _ = EXTRA.get(en, (en, DEF_EMOJI[c], ""))
            pop, dlink = 100 + it["no"], None
        names[str(it["no"])] = {"si": si, "en": en, "ta": ta, "e": emo, "cat": c, "pop": pop,
                                "unit": it.get("unit", "kg"), "dam": dlink}
    return days, names


def head(title, desc, url):
    return f"""<!DOCTYPE html>
<html lang="si"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{IMG}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="../icon-192x192.png"><meta name="theme-color" content="#0e4f4a">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700;800&family=JetBrains+Mono:wght@500;800&family=Hanken+Grotesk:wght@600;800&display=swap" rel="stylesheet">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<style>{CSS}</style></head><body>
<div class="top"><a href="../">🥬 TopGoviya.lk</a><a href="./">සියලු භාණ්ඩ</a><a href="{MARKET_PAGE}">🧺 {MARKET_SI} වෙළඳපොළ</a></div>
"""


FOOT = f"""<footer><b>🌐 topgoviya.lk</b> · මූලාශ්‍රය: {MARKET_FULL_SI} (Keppetipola DEC) · <a href="../data-sources.html">මිල ලබාගන්නා ආකාරය</a><br>
මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ. · © TopGoviya.lk</footer></body></html>
"""


def item_page(pid, m, days, order, names, latest_by_pid):
    s = slug(m["en"]); url = f"{SITE}/{OUT}/{s}.html"
    have = [d for d in order if days[d].get(pid)]
    last = have[-1]; lo, hi = days[last][pid]; mid = (lo + hi) / 2
    prev = have[-2] if len(have) > 1 else None
    pmid = sum(days[prev][pid]) / 2 if prev else None
    wk = [d for d in have if (date.fromisoformat(last) - date.fromisoformat(d)).days >= 7]
    wmid = sum(days[wk[-1]][pid]) / 2 if wk else None
    pts = [(d[5:], *days[d][pid]) for d in have[-30:]]
    lo30 = min(p[1] for p in pts); hi30 = max(p[2] for p in pts)
    u_si = "කි.ග්‍රෑ."
    p1, p7 = pct(mid, pmid), pct(mid, wmid)
    ce, csi, cen = CATS.get(m["cat"], ("🌿", "භාණ්ඩ", "Items"))
    title = f"{m['si']} මිල අද {dot_date(last)} | {MARKET_SI} {m['si']} තොග මිල | {m['en']} Price Today Keppetipola – TopGoviya"
    desc = (f"{m['si']} මිල අද ({si_date(last)}) — {MARKET_FULL_SI}යේ තොග මිල රු. {money(lo)}–{money(hi)} / {u_si}"
            + (f", පෙර වාර්තාවට {p1:+.1f}%" if p1 is not None else "") + f". {m['en']} wholesale price today at Keppetipola, Sri Lanka.")
    share = (f"{m['e']} {m['si']} — අද {MARKET_SI} තොග මිල ({si_date(last)}): රු. {money(lo)}–{money(hi)} / {u_si}"
             + (f" ({p1:+.1f}%)" if p1 is not None else "") + f"\n👉 {url}")
    wa = "https://wa.me/?text=" + urllib.parse.quote(share)
    rows = "".join(f'<tr><td>{e(si_date(d))}</td><td class="n">{money(days[d][pid][0])} – {money(days[d][pid][1])}</td>'
                   f'<td class="n">{money(sum(days[d][pid]) / 2)}</td></tr>' for d in reversed(have[-10:]))
    rel = [(k, x) for k, x in sorted(names.items(), key=lambda kv: kv[1]["pop"])
           if x["cat"] == m["cat"] and k != pid and k in latest_by_pid][:8]
    rel_html = "".join(f'<a href="{slug(x["en"])}.html">{x["e"]} {e(x["si"])}<small>{money(latest_by_pid[k][1])}–{money(latest_by_pid[k][2])}</small></a>' for k, x in rel)
    dam = (f'<a class="btn" href="../dambulla/{m["dam"]}.html">🧺 දඹුල්ල {e(m["si"])} මිල සසඳන්න →</a>' if m.get("dam") else "")
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"{MARKET_SI} මිල", "item": f"{SITE}/{OUT}/"},
            {"@type": "ListItem", "position": 3, "name": f"{m['si']} මිල", "item": url}]},
        {"@type": "WebPage", "url": url, "name": title, "inLanguage": "si",
         "about": {"@type": "Place", "name": "Keppetipola Dedicated Economic Centre"}, "dateModified": last}]}
    stale = ""
    if last != order[-1]:
        stale = f'<p class="note">⏳ {e(si_date(order[-1]))} වාර්තාවේ {e(m["si"])} මිලක් නැත. පෙන්වන්නේ අවසන් මිලයි ({e(si_date(last))}).</p>'
    body = f"""<main class="w">
<p class="crumb"><a href="../">TopGoviya.lk</a> › <a href="./">{MARKET_SI} මිල</a> › {e(m['si'])}</p>
<h1>{e(m['si'])} මිල අද — {MARKET_SI}</h1>
<p class="alt">{MARKET_SI} {e(m['si'])} තොග මිල · {e(m['en'])} price today Keppetipola · {e(m['ta'])} விலை இன்று</p>
<div class="card"><div class="hero"><div class="emo">{m['e']}</div><div>
<div class="price">රු. {money(lo)} – {money(hi)} <small>/ {u_si}</small></div>
<div class="note">📅 {e(si_date(last))} · {ce} {e(csi)} · {MARKET_FULL_SI}, තොග මිල</div></div></div>
{stale}
<div class="stats"><div class="st"><span>සාමාන්‍ය මිල</span><b>{money(mid)}</b></div>
<div class="st"><span>පෙර වාර්තාවට</span><b>{chg_html(p1)}</b></div>
<div class="st"><span>සතියට</span><b>{chg_html(p7)}</b></div>
<div class="st"><span>වාර්තා {len(pts)} අවම / උපරිම</span><b>{money(lo30)} / {money(hi30)}</b></div></div>
<div class="btns"><a class="btn wa" href="{e(wa)}" target="_blank" rel="noopener">🟢 WhatsApp එකට යවන්න</a>
<a class="btn main" href="{MARKET_PAGE}">🥬 {MARKET_SI} සියලු මිල →</a>{dam}</div></div>
<div class="card"><h2>📈 පසුගිය වාර්තා {len(pts)} — මිල ප්‍රවණතාව</h2>{svg_chart(pts)}
<p class="note">අඳුරු තීරුව = අවම–උපරිම පරාසය · රේඛාව = සාමාන්‍ය මිල · රු. / {u_si}</p></div>
<div class="card"><h2>🗓️ පසුගිය මිල</h2><div style="overflow-x:auto"><table><thead><tr><th>දිනය</th><th class="n">අවම – උපරිම</th><th class="n">සාමාන්‍ය</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">🧮 ගොවි / වෙළෙන්දා ලාභ ගණකය: <a href="../">TopGoviya.lk මුල් පිටුව</a></p></div>
{f'<div class="card"><h2>{ce} තවත් {e(csi)} මිල — {MARKET_SI}</h2><div class="rel">{rel_html}</div></div>' if rel_html else ''}
<div class="card"><h2>{e(m['si'])} මිල ගැන</h2>
<p><b>{MARKET_SI} {e(m['si'])} මිල අද කීයද?</b> {e(si_date(last))} {MARKET_FULL_SI}යේ {e(m['si'])} තොග මිල රු. {money(lo)} – {money(hi)} ({u_si}යට). සාමාන්‍ය මිල රු. {money(mid)}.</p>
<p><b>මේවා සිල්ලර මිලද?</b> නැත — තොග මිල. කඩවල සිල්ලර මිල ප්‍රවාහන හා වෙනත් වියදම් නිසා වැඩි විය හැක.</p>
<p lang="en">{e(m['en'])} wholesale price at the Keppetipola Dedicated Economic Centre on {e(dot_date(last))}: Rs. {money(lo)} – {money(hi)} per kg.</p></div>
</main>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
"""
    return s, head(title, desc, url) + body + FOOT


def hub_page(names, latest_by_pid, latest):
    url = f"{SITE}/{OUT}/"
    title = f"{MARKET_SI} එලවලු මිල අද {dot_date(latest)} — සියලු භාණ්ඩ | Keppetipola Price List – TopGoviya"
    desc = f"{MARKET_FULL_SI}යේ {si_date(latest)} තොග මිල — එළවළු, පලා, අල, පලතුරු, ධාන්‍ය භාණ්ඩ {len(latest_by_pid)}ක්. Keppetipola wholesale price list today."
    parts = []
    for c, (ce, csi, cen) in CATS.items():
        its = [(k, x) for k, x in sorted(names.items(), key=lambda kv: kv[1]["pop"]) if x["cat"] == c and k in latest_by_pid]
        if not its:
            continue
        parts.append(f'<div class="card"><h2>{ce} {e(csi)} <span class="note">{e(cen)}</span></h2><div class="rel">' +
                     "".join(f'<a href="{slug(x["en"])}.html">{x["e"]} {e(x["si"])}<small>{money(latest_by_pid[k][1])}–{money(latest_by_pid[k][2])}</small></a>' for k, x in its) +
                     "</div></div>")
    body = (f'<main class="w"><p class="crumb"><a href="../">TopGoviya.lk</a> › {MARKET_SI} මිල</p><h1>{MARKET_SI} එලවලු මිල අද</h1>'
            f'<p class="alt">{e(si_date(latest))} · තොග මිල (රු.) · භාණ්ඩයක් තෝරන්න · Keppetipola price list today</p>'
            + "".join(parts) + f'<p><a class="btn main" href="{MARKET_PAGE}">🥬 {MARKET_SI} සම්පූර්ණ මිල ලැයිස්තුව →</a> '
            f'<a class="btn" href="../dambulla/">🧺 දඹුල්ල මිල →</a></p></main>')
    return head(title, desc, url) + body + FOOT


def update_sitemap(slugs, latest):
    if not os.path.exists("sitemap.xml"):
        return
    sm = open("sitemap.xml", encoding="utf-8").read()
    for s in [""] + slugs:
        loc = f"{SITE}/{OUT}/" + (f"{s}.html" if s else "")
        if f"<loc>{loc}</loc>" in sm:
            sm = re.sub(r"(<loc>" + re.escape(loc) + r"</loc>\s*<lastmod>)[^<]*", r"\g<1>" + latest, sm)
        else:
            sm = sm.replace("</urlset>", f"  <url><loc>{loc}</loc><lastmod>{latest}</lastmod><changefreq>daily</changefreq><priority>0.7</priority></url>\n</urlset>")
    open("sitemap.xml", "w", encoding="utf-8").write(sm)


def main():
    days, names = load()
    order = sorted(days)
    if not order:
        print("No Keppetipola data."); return
    latest = order[-1]
    latest_by_pid = {}
    for d in order:
        for pid, v in days[d].items():
            if v:
                latest_by_pid[pid] = (d, v[0], v[1])
    os.makedirs(OUT, exist_ok=True)
    slugs = []
    for pid, m in names.items():
        if pid not in latest_by_pid:
            continue
        s, page = item_page(pid, m, days, order, names, latest_by_pid)
        open(f"{OUT}/{s}.html", "w", encoding="utf-8").write(page)
        slugs.append(s)
    open(f"{OUT}/index.html", "w", encoding="utf-8").write(hub_page(names, latest_by_pid, latest))
    update_sitemap(sorted(slugs), latest)
    print(f"Built {len(slugs)} Keppetipola item pages + hub for {latest}")


if __name__ == "__main__":
    main()
