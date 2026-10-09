"""
update_index.py  -  keeps index.html's built-in content current (TopGoviya.lk)
------------------------------------------------------------------------------
index.html loads fresh prices from data.json in the browser, but Google and AI
tools often read only the HTML itself. This script runs daily after update.py and:

  1. replaces the built-in EMBEDDED data with the last KEEP_DAYS reports only
     (it is just the offline fallback; a much smaller page loads faster),
  2. writes the latest report date into the "Latest report" line,
  3. writes a plain-text "today's prices" section (between TG-TODAY markers)
     that search engines and AI assistants can read without running JavaScript.

Only changes those three places; everything else in index.html stays as it is.
Uses build_pages.py (same folder) for names, dates and number formats.
"""
import json, re

from build_pages import NAMES, MARKETS, EMOJIS, slug, fdate, money
from datetime import datetime

KEEP_DAYS = 60
INDEX = "index.html"
START, END = "<!-- TG-TODAY-START -->", "<!-- TG-TODAY-END -->"


def si(n): return (NAMES.get(n) or {}).get("si", n)
def mkt_si(m): return (MARKETS.get(m) or {}).get("si", m)


def last_two(series):
    pts = [(i, v) for i, v in enumerate(series or []) if v is not None]
    return pts[-1] if pts else None, pts[-2] if len(pts) > 1 else None


def small_db(db):
    """Same structure as data.json, but only the last KEEP_DAYS reports."""
    k = KEEP_DAYS
    out = {key: db[key] for key in db if key not in ("dates", "dateLabels", "commodities")}
    out["dates"] = db["dates"][-k:]
    if "dateLabels" in db:
        out["dateLabels"] = db["dateLabels"][-k:]
    out["commodities"] = []
    for c in db["commodities"]:
        c2 = dict(c)
        for key in ("series", "wholesaleSeries"):
            if isinstance(c.get(key), list):
                c2[key] = c[key][-k:]
        out["commodities"].append(c2)
    return out


def ta(n): return (NAMES.get(n) or {}).get("ta", n)
def mkt_ta(m): return (MARKETS.get(m) or {}).get("ta", m)


def L(si_, en_, ta_, tag="span", style=""):
    """The same text in 3 languages; CSS shows the one matching the page language."""
    st = f' style="{style}"' if style else ""
    return (f'<{tag} class="tgl tgl-si"{st}>{si_}</{tag}><{tag} class="tgl tgl-en" lang="en"{st}>{en_}</{tag}>'
            f'<{tag} class="tgl tgl-ta" lang="ta"{st}>{ta_}</{tag}>')


def today_section(db):
    dates = db["dates"]
    li = len(dates) - 1
    d = datetime.strptime(dates[li], "%Y-%m-%d").date()
    rows, moves = [], []
    for c in db["commodities"]:
        cur, prev = last_two(c.get("series"))
        if not cur or cur[0] != li:          # only items reported in the latest report
            continue
        price = cur[1]
        chg = None
        if prev and prev[1]:
            chg = (price - prev[1]) / prev[1] * 100
            moves.append((chg, c, prev[1], price))
        w = (c.get("wholesaleSeries") or [None] * (li + 1))
        wp = w[li] if len(w) > li else None
        rows.append((c, price, wp, chg))

    up = sorted([m for m in moves if m[0] >= 0.5], key=lambda m: -m[0])[:3]
    dn = sorted([m for m in moves if m[0] <= -0.5], key=lambda m: m[0])[:3]
    def lst(ms, nm, rs): return ", ".join(f"{nm(c['name'])} ({rs} {money(a)} → {money(b)})" for _, c, a, b in ms)

    p_si = (f"{fdate(d, 'si')} ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව අනුව භාණ්ඩ {len(rows)}ක සිල්ලර මිල පහත දැක්වේ. "
            + (f"පෙර වාර්තාවට වඩා වැඩිම ඉහළ යාම: {lst(up, si, 'රු.')}. " if up else "")
            + (f"වැඩිම පහළ යාම: {lst(dn, si, 'රු.')}." if dn else ""))
    p_en = (f"Sri Lanka vegetable prices today ({fdate(d, 'en')}): retail prices for {len(rows)} items from the "
            f"Central Bank of Sri Lanka daily price report. "
            + (f"Biggest rises since the previous report: {lst(up, lambda n: n, 'Rs.')}. " if up else "")
            + (f"Biggest falls: {lst(dn, lambda n: n, 'Rs.')}." if dn else ""))
    p_ta = (f"{fdate(d, 'ta')} இலங்கை மத்திய வங்கியின் தினசரி விலை அறிக்கையின்படி {len(rows)} பொருட்களின் சில்லறை விலைகள். "
            + (f"முந்தைய அறிக்கையை விட அதிக உயர்வு: {lst(up, ta, 'ரூ.')}. " if up else "")
            + (f"அதிக வீழ்ச்சி: {lst(dn, ta, 'ரூ.')}." if dn else ""))

    trs = ""
    for c, price, wp, chg in rows:
        mk = c.get("primaryMarket", "")
        ch = "—" if chg is None else (("▲ +" if chg >= 0.5 else ("▼ " if chg <= -0.5 else "■ ")) + f"{chg:.1f}%")
        name = L(f'{si(c["name"])}<br><small style="color:var(--muted)">{c["name"]} · {mkt_si(mk)}</small>',
                 f'{c["name"]}<br><small style="color:var(--muted)">{mk}</small>',
                 f'{ta(c["name"])}<br><small style="color:var(--muted)">{c["name"]} · {mkt_ta(mk)}</small>')
        trs += (f'<tr style="border-top:1px solid var(--line)"><td style="padding:5px 4px"><a href="price/{slug(c["name"])}.html">{name}</a></td>'
                f'<td style="text-align:right;padding:5px 4px">{money(wp) if wp is not None else "—"}</td>'
                f'<td style="text-align:right;padding:5px 4px"><b>{money(price)}</b></td>'
                f'<td style="text-align:right;padding:5px 4px;white-space:nowrap">{ch}</td></tr>')

    chip = ('display:inline-flex;align-items:center;gap:4px;padding:5px 11px;border-radius:999px;border:1px solid var(--petrol);'
            'color:var(--petrol);background:var(--card);font-size:12.5px;font-weight:700;text-decoration:none')
    chips = "".join(f'<a href="{href}" style="{chip}">{L(a_, b_, c_)}</a>' for href, a_, b_, c_ in [
        ("market/", "🧺 වෙළඳපොළ මිල", "🧺 Market prices", "🧺 சந்தை விலைகள்"),
        ("price/", "🏷️ භාණ්ඩ අනුව මිල", "🏷️ Prices by item", "🏷️ பொருள் வாரியாக விலை"),
        ("spice/pepper.html", "⚫ ගම්මිරිස් මිල අද", "⚫ Pepper price today", "⚫ மிளகு விலை இன்று"),
        ("spice/cinnamon.html", "🪵 කුරුඳු මිල අද", "🪵 Cinnamon price today", "🪵 கறுவா விலை இன்று"),
        # ?v=<date> so phones always get the newest image (old ones stay cached under their own date)
        (f"share/today.png?v={dates[li]}", "📤 අද මිල පින්තූරය (WhatsApp)", "📤 Today's price image (WhatsApp)", "📤 இன்றைய விலைப் படம் (WhatsApp)")])
    th = 'style="text-align:right"'
    return f"""{START}
<style>.tgl{{display:none}}html[lang="si"] .tgl-si,html[lang="en"] .tgl-en,html[lang="ta"] .tgl-ta{{display:revert}}</style>
<section id="today-prices" style="max-width:1100px;margin:28px auto 0;padding:0 16px">
  <h2 style="font-size:20px;margin:0 0 8px">{L(f"අද මිල සාරාංශය — {fdate(d, 'si')}", f"Sri Lanka vegetable prices today — {fdate(d, 'en')}", f"இன்றைய விலைச் சுருக்கம் — {fdate(d, 'ta')}")}</h2>
  <p style="font-size:12.5px;color:var(--muted);margin:0 0 6px">{L("අද එලවලු මිල · දඹුල්ල (දබුල්ල) එලවලු මිල · elawalu mila ada", "Today vegetable prices Sri Lanka · Dambulla market price today", "இன்றைய காய்கறி விலை · தம்புள்ள சந்தை விலை இன்று")}</p>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin:0 0 10px">{chips}</div>
  {L(p_si, p_en, p_ta, "p", "font-size:14px;line-height:1.6;margin:0 0 8px")}
  <details style="background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px">
    <summary style="cursor:pointer;font-weight:700">📋 {L("සියලු මිල ලැයිස්තුව (පෙළ)", "Full price list as text", "முழு விலைப் பட்டியல் (உரை)")}</summary>
    <div style="overflow-x:auto;margin-top:10px">
    <table style="width:100%;border-collapse:collapse;font-size:13.5px">
      <thead><tr style="font-size:12px;color:var(--muted)"><th style="text-align:left">{L("භාණ්ඩය · වෙළඳපොළ", "Item · Market", "பொருள் · சந்தை")}</th>
      <th {th}>{L("තොග", "Wholesale", "மொத்த")}</th><th {th}>{L("සිල්ලර", "Retail", "சில்லறை")}</th>
      <th {th}>{L("වෙනස", "Change", "மாற்றம்")}</th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>
    {L(f"රු. / කි.ග්‍රෑ. (පොල් ගෙඩියකට, බිත්තර එකකට). දත්ත: ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව, {fdate(d, 'si')}. වෙනස = පෙර වාර්තාවට සාපේක්ෂව. මිල ගණන් මඟපෙන්වීමක් පමණි.",
       f"Rs. per kg (coconut per nut, egg each). Source: Central Bank of Sri Lanka daily price report, {fdate(d, 'en')}. Change = vs the previous report. Prices are indicative only.",
       f"ரூ. / கி.கி. (தேங்காய் ஒன்றுக்கு, முட்டை ஒன்றுக்கு). மூலம்: இலங்கை மத்திய வங்கியின் தினசரி விலை அறிக்கை, {fdate(d, 'ta')}. மாற்றம் = முந்தைய அறிக்கையுடன் ஒப்பிட. விலைகள் வழிகாட்டல் மட்டுமே.",
       "p", "font-size:12px;color:var(--muted);margin:8px 0 0")}
  </details>
</section>
{END}"""


def main():
    db = json.load(open("data.json", encoding="utf-8"))
    html = open(INDEX, encoding="utf-8").read()
    d = datetime.strptime(db["dates"][-1], "%Y-%m-%d").date()

    # 1) smaller built-in data (offline fallback only)
    a = html.index("const EMBEDDED = ") + len("const EMBEDDED = ")
    b = html.index(";\nlet DB=EMBEDDED", a)
    html = html[:a] + json.dumps(small_db(db), ensure_ascii=False, separators=(",", ":")) + html[b:]

    # 2) latest report date in the page itself
    html, n = re.subn(r'(<span class="stamp" id="stampDate">)[^<]*(</span>)',
                      lambda m: m.group(1) + fdate(d, "si") + m.group(2), html, count=1)
    if not n:
        print("WARN: stampDate not found")

    # 2b) homepage description for Google: today's date + the spelling most people type ("එලවලු")
    desc = (f"අද එලවලු මිල ({fdate(d, 'si')}) — දඹුල්ල (දබුල්ල), පිටකොටුව, නාරාහේන්පිට සිල්ලර සහ තොග මිල, දිනපතා. "
            f"Today's Dambulla vegetable prices in Sri Lanka from Central Bank daily reports. සිංහල · தமிழ் · English.")
    html = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + desc + m.group(2), html, count=1)
    html = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + desc + m.group(2), html, count=1)

    # 2c) link preview picture for WhatsApp / Facebook: today's prices (made by make_daily_image.py)
    img = f"https://topgoviya.lk/share/today-wide.png?v={db['dates'][-1]}"
    html = re.sub(r'\n?<meta (?:property="og:image[^"]*"|name="twitter:image")[^>]*>', "", html)
    tags = (f'\n<meta property="og:image" content="{img}">'
            f'\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">'
            f'\n<meta property="og:image:alt" content="අද එළවළු මිල — {fdate(d, "si")} · TopGoviya.lk">'
            f'\n<meta name="twitter:image" content="{img}">')
    html = re.sub(r'(<meta property="og:description" content="[^"]*">)', lambda m: m.group(1) + tags, html, count=1)
    html = html.replace('<meta name="twitter:card" content="summary">', '<meta name="twitter:card" content="summary_large_image">')

    # 3) plain-text 'today' section (replace the old one, or add it before the footer the first time)
    sec = today_section(db)
    if START in html and END in html:
        i, j = html.index(START), html.index(END) + len(END)
        html = html[:i] + sec + html[j:]
    else:
        k = html.index("<footer")
        html = html[:k] + sec + "\n\n  " + html[k:]

    open(INDEX, "w", encoding="utf-8").write(html)
    print(f"index.html updated: latest report {db['dates'][-1]}, built-in data {KEEP_DAYS} reports, "
          f"{len(html) // 1024} KB")


if __name__ == "__main__":
    main()
