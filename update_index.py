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
    def lst_si(ms): return ", ".join(f"{si(c['name'])} (රු. {money(a)} → {money(b)})" for _, c, a, b in ms)
    def lst_en(ms): return ", ".join(f"{c['name']} (Rs. {money(a)} → {money(b)})" for _, c, a, b in ms)

    p_si = (f"{fdate(d, 'si')} ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව අනුව භාණ්ඩ {len(rows)}ක සිල්ලර මිල පහත දැක්වේ. "
            + (f"පෙර වාර්තාවට වඩා වැඩිම ඉහළ යාම: {lst_si(up)}. " if up else "")
            + (f"වැඩිම පහළ යාම: {lst_si(dn)}." if dn else ""))
    p_en = (f"Sri Lanka vegetable prices today ({fdate(d, 'en')}): retail prices for {len(rows)} items from the "
            f"Central Bank of Sri Lanka daily price report. "
            + (f"Biggest rises since the previous report: {lst_en(up)}. " if up else "")
            + (f"Biggest falls: {lst_en(dn)}." if dn else ""))

    trs = ""
    for c, price, wp, chg in rows:
        mk = c.get("primaryMarket", "")
        ch = "—" if chg is None else (("▲ +" if chg >= 0.5 else ("▼ " if chg <= -0.5 else "■ ")) + f"{chg:.1f}%")
        trs += (f'<tr style="border-top:1px solid var(--line)"><td style="padding:5px 4px"><a href="price/{slug(c["name"])}.html">{si(c["name"])}</a>'
                f'<br><small style="color:var(--muted)">{c["name"]} · {mkt_si(mk)} ({mk})</small></td>'
                f'<td style="text-align:right;padding:5px 4px">{money(wp) if wp is not None else "—"}</td>'
                f'<td style="text-align:right;padding:5px 4px"><b>{money(price)}</b></td>'
                f'<td style="text-align:right;padding:5px 4px;white-space:nowrap">{ch}</td></tr>')

    return f"""{START}
<section id="today-prices" style="max-width:1100px;margin:28px auto 0;padding:0 16px">
  <h2 style="font-size:20px;margin:0 0 8px">අද මිල සාරාංශය · Sri Lanka vegetable prices today — {fdate(d, 'en')}</h2>
  <p style="font-size:14px;line-height:1.6;margin:0 0 6px">{p_si}</p>
  <p style="font-size:14px;line-height:1.6;margin:0 0 8px" lang="en">{p_en}</p>
  <details style="background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px">
    <summary style="cursor:pointer;font-weight:700">📋 සියලු මිල ලැයිස්තුව (පෙළ) / Full price list as text</summary>
    <div style="overflow-x:auto;margin-top:10px">
    <table style="width:100%;border-collapse:collapse;font-size:13.5px">
      <thead><tr style="font-size:12px;color:var(--muted)"><th style="text-align:left">භාණ්ඩය · වෙළඳපොළ<br>Item · Market</th>
      <th style="text-align:right">තොග<br>Wholesale</th><th style="text-align:right">සිල්ලර<br>Retail</th>
      <th style="text-align:right">වෙනස<br>Change</th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>
    <p style="font-size:12px;color:var(--muted);margin:8px 0 0">රු. / කි.ග්‍රෑ. (පොල් ගෙඩියකට, බිත්තර එකකට). දත්ත: ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව, {fdate(d, 'si')}. වෙනස = පෙර වාර්තාවට සාපේක්ෂව.
    Source: Central Bank of Sri Lanka daily price report. Change = vs the previous report. Prices are indicative only.</p>
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
