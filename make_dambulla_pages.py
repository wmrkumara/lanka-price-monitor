"""
make_dambulla_pages.py  -  TopGoviya.lk: one page per Dambulla DEC item
------------------------------------------------------------------------
Builds, from dambulla_dec.json (+ dambulla_early.json when newer) and dambulla_items.json:
  dambulla/<item>.html        e.g. dambulla/ginger.html  ("ඉඟුරු මිල අද")
  dambulla/index.html         list of all items by category
  share/items/<item>.jpg      link-preview picture per item (made once, kept)
and adds the pages to sitemap.xml.  Run after the Dambulla robot (in the preview-image robot).
"""
import html, json, os, re
from datetime import date

SITE = "https://topgoviya.lk"
OUT = "dambulla"
IMG = "share/items"
GA = "G-ZBN8Z32S4J"
UNIT_SI = {"kg": "කි.ග්‍රෑ.", "nut": "ගෙඩිය", "bundle": "මිටිය"}
UNIT_EN = {"kg": "kg", "nut": "nut", "bundle": "bundle"}
CAT = {"v": ("🥬", "එළවළු", "Vegetables"), "l": ("🌿", "පලා වර්ග", "Leafy vegetables"),
       "r": ("🥔", "අල වර්ග", "Roots & tubers"), "f": ("🍍", "පලතුරු", "Fruits"), "g": ("🌾", "ධාන්‍ය", "Grains")}
MONTHS = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි", "අගෝස්තු",
          "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]
e = lambda s: html.escape(str(s), quote=True)
money = lambda n: f"{round(n):,}"


def si_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.year} {MONTHS[d.month - 1]} {d.day}"


def dot_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.year}.{d.month:02d}.{d.day:02d}"


def slug(en):
    return re.sub(r"[^a-z0-9]+", "-", en.lower()).strip("-")


def load():
    db = json.load(open("dambulla_dec.json", encoding="utf-8"))
    days = dict(db.get("days", {}))
    try:
        ear = json.load(open("dambulla_early.json", encoding="utf-8"))
        if ear.get("date") and ear.get("prices") and ear["date"] not in days and (not days or ear["date"] > max(days)):
            days[ear["date"]] = ear["prices"]
    except Exception:
        pass
    names = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    return days, names


def pct(a, b):
    return None if not b else (a - b) / b * 100


def chg_html(p):
    if p is None:
        return '<span class="fl">—</span>'
    cls = "up" if p >= 0.5 else "dn" if p <= -0.5 else "fl"
    arrow = "▲" if cls == "up" else "▼" if cls == "dn" else "■"
    return f'<span class="{cls}">{arrow} {p:+.1f}%</span>'


def svg_chart(pts):
    """pts = [(iso, lo, hi)] oldest -> newest; min-max band + average line."""
    if len(pts) < 2:
        return ""
    W, H, L, R, T, B = 680, 230, 46, 14, 14, 30
    lo = min(p[1] for p in pts); hi = max(p[2] for p in pts); pad = (hi - lo) * .12 or 10
    lo, hi = lo - pad, hi + pad
    X = lambda k: L + k * (W - L - R) / (len(pts) - 1)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    band = " ".join(f"{X(k):.1f},{Y(p[2]):.1f}" for k, p in enumerate(pts)) + " " + \
           " ".join(f"{X(k):.1f},{Y(p[1]):.1f}" for k, p in reversed(list(enumerate(pts))))
    line = " ".join(f"{X(k):.1f},{Y((p[1] + p[2]) / 2):.1f}" for k, p in enumerate(pts))
    grid = "".join(f'<line x1="{L}" x2="{W - R}" y1="{Y(lo + (hi - lo) * i / 3):.1f}" y2="{Y(lo + (hi - lo) * i / 3):.1f}" stroke="#e3d9c4"/>'
                   f'<text x="{L - 6}" y="{Y(lo + (hi - lo) * i / 3) + 4:.1f}" text-anchor="end" font-size="11" fill="#6f675a">{money(lo + (hi - lo) * i / 3)}</text>'
                   for i in range(4))
    lx, ly = X(len(pts) - 1), Y((pts[-1][1] + pts[-1][2]) / 2)
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="price chart" style="width:100%;height:auto;display:block">{grid}'
            f'<polygon points="{band}" fill="rgba(14,79,74,.15)"/><polyline points="{line}" fill="none" stroke="#0e4f4a" stroke-width="3" stroke-linejoin="round"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="6" fill="#a9802a"/>'
            f'<text x="{L}" y="{H - 8}" font-size="11" fill="#6f675a">{e(pts[0][0])}</text>'
            f'<text x="{W - R}" y="{H - 8}" font-size="11" fill="#6f675a" text-anchor="end">{e(pts[-1][0])}</text></svg>')


CSS = """
body{margin:0;background:#f4efe4;color:#191d1a;font-family:'Noto Sans Sinhala','Hanken Grotesk',system-ui,sans-serif;line-height:1.55}
.top{background:#0e4f4a;padding:12px 18px;border-bottom:3px solid #a9802a}.top a{color:#fff;text-decoration:none;font-weight:700;margin-right:14px;font-size:15px}
.w{max-width:860px;margin:0 auto;padding:16px}
.crumb{font-size:13px;color:#6f675a;margin:4px 0 8px}.crumb a{color:#0e4f4a}
h1{color:#0e4f4a;font-size:30px;margin:6px 0 2px;line-height:1.25}.alt{color:#6f675a;margin:0 0 12px;font-size:14px}
.card{background:#fffdf7;border:1px solid #e3d9c4;border-radius:16px;padding:16px;margin:0 0 14px}
.hero{display:flex;gap:16px;align-items:center}.emo{font-size:58px;line-height:1;background:#efe8d8;border-radius:16px;padding:10px 12px}
.price{font-family:'JetBrains Mono',monospace;font-size:34px;font-weight:800;color:#0e4f4a}.price small{font-size:14px;color:#6f675a;font-weight:500}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.st{background:#f4efe4;border:1px solid #e3d9c4;border-radius:12px;padding:8px 10px}
.st b{display:block;font-family:'JetBrains Mono',monospace;font-size:18px}.st span{font-size:12px;color:#6f675a}
@media(max-width:560px){.stats{grid-template-columns:repeat(2,1fr)}h1{font-size:25px}.price{font-size:28px}}
.up{color:#b23a2e}.dn{color:#2c7a52}.fl{color:#8a8170}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:8px;border-bottom:1px solid #eee5d3;text-align:left}th{font-size:12px;color:#6f675a}
.n{text-align:right;font-family:'JetBrains Mono',monospace;white-space:nowrap}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 0}.btn{display:inline-flex;gap:6px;align-items:center;padding:10px 14px;border-radius:10px;font-weight:700;text-decoration:none;font-size:14px;border:1px solid #e3d9c4;color:#0e4f4a;background:#fff}
.btn.wa{background:#1f8a4c;color:#fff;border-color:#1f8a4c}.btn.main{background:#0e4f4a;color:#fff;border-color:#0e4f4a}
.rel{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px}.rel a{display:block;background:#fff;border:1px solid #e3d9c4;border-radius:10px;padding:8px 10px;text-decoration:none;color:#191d1a;font-size:14px}
.rel small{display:block;color:#6f675a;font-family:'JetBrains Mono',monospace}
h2{font-size:18px;color:#0e4f4a;margin:0 0 8px}.note{font-size:13px;color:#6f675a}a{color:#0e4f4a}
footer{background:#0a3a36;color:#e7d3a3;padding:16px;font-size:13px;margin-top:20px}footer a{color:#fff}
"""


def head(title, desc, url, img, extra=""):
    return f"""<!DOCTYPE html>
<html lang="si"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../icon-192x192.png"><meta name="theme-color" content="#0e4f4a">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700;800&family=JetBrains+Mono:wght@500;800&family=Hanken+Grotesk:wght@600;800&display=swap" rel="stylesheet">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<style>{CSS}</style>{extra}</head><body>
<div class="top"><a href="../">🥬 TopGoviya.lk</a><a href="./">සියලු භාණ්ඩ</a><a href="../retail.html">📊 CBSL</a></div>
"""


FOOT = """<footer><b>🌐 topgoviya.lk</b> · මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය (Dambulla DEC) · <a href="../data-sources.html">මිල ලබාගන්නා ආකාරය</a><br>
මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ. · © TopGoviya.lk</footer></body></html>
"""


def item_page(pid, m, days, order, names, latest_by_pid):
    s = slug(m["en"]); url = f"{SITE}/{OUT}/{s}.html"; img = f"{SITE}/{IMG}/{s}.jpg"
    have = [d for d in order if days[d].get(pid)]
    last = have[-1]; lo, hi = days[last][pid]; mid = (lo + hi) / 2
    prev = have[-2] if len(have) > 1 else None
    pmid = sum(days[prev][pid]) / 2 if prev else None
    wk = [d for d in have if (date.fromisoformat(last) - date.fromisoformat(d)).days >= 7]
    wmid = sum(days[wk[-1]][pid]) / 2 if wk else None
    pts = [(d[5:], *days[d][pid]) for d in have[-30:]]
    lo30 = min(p[1] for p in pts); hi30 = max(p[2] for p in pts)
    u_si, u_en = UNIT_SI.get(m["unit"], "කි.ග්‍රෑ."), UNIT_EN.get(m["unit"], "kg")
    p1, p7 = pct(mid, pmid), pct(mid, wmid)
    ce, csi, cen = CAT.get(m.get("cat"), ("🌿", "භාණ්ඩ", "Items"))
    title = f"{m['si']} මිල අද {dot_date(last)} | දඹුල්ල {m['si']} තොග මිල | {m['en']} Price Today Dambulla – TopGoviya"
    desc = (f"{m['si']} මිල අද ({si_date(last)}) — දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ තොග මිල රු. {money(lo)}–{money(hi)} / {u_si}"
            + (f", පෙර වාර්තාවට {p1:+.1f}%" if p1 is not None else "") + f". {m['en']} wholesale price today at Dambulla, Sri Lanka.")
    share = (f"{m.get('e', '🌿')} {m['si']} — අද දඹුල්ල තොග මිල ({si_date(last)}): රු. {money(lo)}–{money(hi)} / {u_si}"
             + (f" ({p1:+.1f}%)" if p1 is not None else "") + f"\n👉 {url}")
    import urllib.parse
    wa = "https://wa.me/?text=" + urllib.parse.quote(share)
    rows = "".join(f'<tr><td>{e(si_date(d))}</td><td class="n">{money(days[d][pid][0])} – {money(days[d][pid][1])}</td>'
                   f'<td class="n">{money(sum(days[d][pid]) / 2)}</td></tr>' for d in reversed(have[-10:]))
    rel = [(k, x) for k, x in sorted(names.items(), key=lambda kv: kv[1]["pop"]) if x.get("cat") == m.get("cat") and k != pid and k in latest_by_pid][:8]
    rel_html = "".join(f'<a href="{slug(x["en"])}.html">{x.get("e", "🌿")} {e(x["si"])}<small>{money(latest_by_pid[k][1])}–{money(latest_by_pid[k][2])}</small></a>' for k, x in rel)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TopGoviya.lk", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "දඹුල්ල මිල", "item": f"{SITE}/{OUT}/"},
            {"@type": "ListItem", "position": 3, "name": f"{m['si']} මිල", "item": url}]},
        {"@type": "WebPage", "url": url, "name": title, "inLanguage": "si",
         "about": {"@type": "Place", "name": "Dambulla Dedicated Economic Centre"}, "dateModified": last}]}
    stale = ""
    if last != order[-1]:
        stale = f'<p class="note">⏳ {e(si_date(order[-1]))} වාර්තාවේ {e(m["si"])} මිලක් නැත. පෙන්වන්නේ අවසන් මිලයි ({e(si_date(last))}).</p>'
    body = f"""<main class="w">
<p class="crumb"><a href="../">TopGoviya.lk</a> › <a href="./">දඹුල්ල මිල</a> › {e(m['si'])}</p>
<h1>{e(m['si'])} මිල අද</h1>
<p class="alt">දඹුල්ල {e(m['si'])} තොග මිල · {e(m['en'])} price today Dambulla · {e(m.get('ta', ''))} விலை இன்று</p>
<div class="card"><div class="hero"><div class="emo">{m.get('e', '🌿')}</div><div>
<div class="price">රු. {money(lo)} – {money(hi)} <small>/ {u_si}</small></div>
<div class="note">📅 {e(si_date(last))} · {ce} {e(csi)} · දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය, තොග මිල</div></div></div>
{stale}
<div class="stats"><div class="st"><span>සාමාන්‍ය මිල</span><b>{money(mid)}</b></div>
<div class="st"><span>පෙර වාර්තාවට</span><b>{chg_html(p1)}</b></div>
<div class="st"><span>සතියට</span><b>{chg_html(p7)}</b></div>
<div class="st"><span>වාර්තා {len(pts)} අවම / උපරිම</span><b>{money(lo30)} / {money(hi30)}</b></div></div>
<div class="btns"><a class="btn wa" href="{e(wa)}" target="_blank" rel="noopener">🟢 WhatsApp එකට යවන්න</a>
<a class="btn main" href="../">🥬 සියලු භාණ්ඩ 90+ ක අද මිල →</a></div></div>
<div class="card"><h2>📈 පසුගිය වාර්තා {len(pts)} — මිල ප්‍රවණතාව</h2>{svg_chart(pts)}
<p class="note">අඳුරු තීරුව = අවම–උපරිම පරාසය · රේඛාව = සාමාන්‍ය මිල · රු. / {u_si}</p></div>
<div class="card"><h2>🗓️ පසුගිය මිල</h2><div style="overflow-x:auto"><table><thead><tr><th>දිනය</th><th class="n">අවම – උපරිම</th><th class="n">සාමාන්‍ය</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">🧮 ගොවි / වෙළෙන්දා ලාභ ගණකය හා දින දර්ශනය: <a href="../">TopGoviya.lk මුල් පිටුව</a></p></div>
{f'<div class="card"><h2>{ce} තවත් {e(csi)} මිල</h2><div class="rel">{rel_html}</div></div>' if rel_html else ''}
<div class="card"><h2>{e(m['si'])} මිල ගැන</h2>
<p><b>දඹුල්ල {e(m['si'])} මිල අද කීයද?</b> {e(si_date(last))} දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ {e(m['si'])} තොග මිල රු. {money(lo)} – {money(hi)} ({u_si}යට). සාමාන්‍ය මිල රු. {money(mid)}.</p>
<p><b>මේවා සිල්ලර මිලද?</b> නැත — තොග මිල. කඩවල සිල්ලර මිල ප්‍රවාහන හා වෙනත් වියදම් නිසා වැඩි විය හැක.</p>
<p lang="en">{e(m['en'])} wholesale price at the Dambulla Dedicated Economic Centre on {e(dot_date(last))}: Rs. {money(lo)} – {money(hi)} per {u_en}.</p></div>
</main>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
"""
    return s, head(title, desc, url, img) + body + FOOT


def hub_page(names, latest_by_pid, latest):
    url = f"{SITE}/{OUT}/"
    title = f"දඹුල්ල එලවලු මිල අද {dot_date(latest)} — සියලු භාණ්ඩ | Dambulla Price List – TopGoviya"
    desc = f"දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ {si_date(latest)} තොග මිල — එළවළු, පලා, අල, පලතුරු, ධාන්‍ය භාණ්ඩ {len(latest_by_pid)}ක්. Dambulla wholesale price list today."
    parts = []
    for c, (ce, csi, cen) in CAT.items():
        its = [(k, x) for k, x in sorted(names.items(), key=lambda kv: kv[1]["pop"]) if x.get("cat") == c and k in latest_by_pid]
        if not its:
            continue
        parts.append(f'<div class="card"><h2>{ce} {e(csi)} <span class="note">{e(cen)}</span></h2><div class="rel">' +
                     "".join(f'<a href="{slug(x["en"])}.html">{x.get("e", "🌿")} {e(x["si"])}<small>{money(latest_by_pid[k][1])}–{money(latest_by_pid[k][2])}</small></a>' for k, x in its) +
                     "</div></div>")
    body = (f'<main class="w"><p class="crumb"><a href="../">TopGoviya.lk</a> › දඹුල්ල මිල</p><h1>දඹුල්ල එලවලු මිල අද</h1>'
            f'<p class="alt">{e(si_date(latest))} · තොග මිල (රු.) · භාණ්ඩයක් තෝරන්න · Dambulla price list today</p>'
            + "".join(parts) + '<p><a class="btn main" href="../">🥬 සියලු මිල, බාස්කට් එක හා ලාභ ගණකය →</a></p></main>')
    return head(title, desc, url, f"{SITE}/share/dambulla-wide.png?v={latest}") + body + FOOT


def make_images(todo):
    """Link-preview picture per item (1200x630). Only for items that don't have one yet."""
    if not todo:
        return
    from playwright.sync_api import sync_playwright
    os.makedirs(IMG, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
        for s, m in todo:
            pg.set_content(f"""<html><body style="margin:0;width:1200px;height:630px;font-family:'Noto Sans Sinhala',sans-serif;background:#f4efe4;display:flex">
<div style="width:430px;background:#0e4f4a;display:flex;align-items:center;justify-content:center;font-size:230px;font-family:'Noto Color Emoji',sans-serif">{m.get('e', '🌿')}</div>
<div style="flex:1;padding:60px 56px;display:flex;flex-direction:column;justify-content:center">
<div style="font-size:32px;color:#a9802a;font-weight:700">දඹුල්ල තොග මිල</div>
<div style="font-size:92px;font-weight:800;color:#0e4f4a;line-height:1.15">{e(m['si'])}</div>
<div style="font-size:40px;color:#6f675a;margin-top:6px">{e(m['en'])} price today</div>
<div style="margin-top:34px;display:inline-block;background:#a9802a;color:#fff;font-size:38px;font-weight:800;padding:14px 28px;border-radius:18px;align-self:flex-start">අද මිල බලන්න →</div>
<div style="margin-top:26px;font-size:34px;color:#0e4f4a;font-weight:800;font-family:sans-serif">topgoviya.lk</div></div></body></html>""")
            pg.wait_for_timeout(120)
            pg.screenshot(path=f"{IMG}/{s}.jpg", type="jpeg", quality=82)
        b.close()
    print(f"Made {len(todo)} link-preview pictures")


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
        print("No data."); return
    latest = order[-1]
    latest_by_pid = {}
    for d in order:
        for pid, v in days[d].items():
            if v:
                latest_by_pid[pid] = (d, v[0], v[1])
    os.makedirs(OUT, exist_ok=True)
    slugs, todo = [], []
    for pid, m in names.items():
        if pid not in latest_by_pid:
            continue
        s, page = item_page(pid, m, days, order, names, latest_by_pid)
        open(f"{OUT}/{s}.html", "w", encoding="utf-8").write(page)
        slugs.append(s)
        if not os.path.exists(f"{IMG}/{s}.jpg"):
            todo.append((s, m))
    open(f"{OUT}/index.html", "w", encoding="utf-8").write(hub_page(names, latest_by_pid, latest))
    update_sitemap(sorted(slugs), latest)
    try:
        make_images(todo)
    except Exception as ex:
        print("Preview pictures skipped:", ex)
    print(f"Built {len(slugs)} item pages + hub for {latest}")


if __name__ == "__main__":
    main()
