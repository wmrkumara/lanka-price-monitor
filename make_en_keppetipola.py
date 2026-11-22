#!/usr/bin/env python3
"""
English Keppetipola page — TopGoviya.lk (Nov 2026)
--------------------------------------------------
Writes en/keppetipola-market-price-today.html from keppetipola_dec.json
(the daily Keppetipola DEC price list he enters by hand).

It borrows the English Dambulla page design from make_dec_image.py, so any
improvement made to the Dambulla English page shows up here too. Only the
words, links and data are swapped to Keppetipola.

Run by the "Apply manual DEC prices" robot after the Keppetipola pages are built.
If anything goes wrong it prints a message and leaves the old page alone.
"""
import json, os, re

import make_dec_image as D
from build_keppetipola_page import build_master
from make_dambulla_pages import slug

FILE = "en/keppetipola-market-price-today.html"
URL = "https://topgoviya.lk/" + FILE
SI_URL = "https://topgoviya.lk/market/keppetipola.html"
HREFLANG = ('<link rel="alternate" hreflang="si" href="' + SI_URL + '">\n'
            '<link rel="alternate" hreflang="en" href="' + URL + '">\n'
            '<link rel="alternate" hreflang="x-default" href="' + SI_URL + '">')


def names_for(kep):
    """Keppetipola items in the shape the Dambulla English page expects."""
    try:
        dmaster = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    except Exception:
        dmaster = {}
    M = build_master(kep["items"], dmaster)
    return {k: {"en": m["en"], "si": m["si"], "cat": m["c"], "e": m["e"], "unit": m["u"],
                "pop": m["p"], "pop_cat": m["pc"]} for k, m in M.items()}


def make_page(kep):
    db = {"days": {d: {str(k): v for k, v in p.items()} for d, p in kep["days"].items() if p}}
    if not db["days"]:
        return None, None
    last = max(db["days"])
    names = names_for(kep)

    # item links go to the Keppetipola item pages (keppetipola/<item>.html)
    orig_listdir, orig_isdir, orig_slug = D.os.listdir, D.os.path.isdir, D.en_slug
    D.os.listdir = lambda p: orig_listdir("keppetipola") if p == "dambulla" else orig_listdir(p)
    D.os.path.isdir = lambda p: orig_isdir("keppetipola") if p == "dambulla" else orig_isdir(p)
    D.en_slug = slug
    try:
        h = D.en_page_html(db, names, last)
    finally:
        D.os.listdir, D.os.path.isdir, D.en_slug = orig_listdir, orig_isdir, orig_slug

    # ---- swap Dambulla -> Keppetipola (links first, then words) ----
    h = h.replace(D.HREFLANG, HREFLANG).replace(D.EN_URL, URL)
    h = h.replace('href="../dambulla/', 'href="../keppetipola/')
    h = h.replace('<a href="../market/keppetipola.html">Keppetipola</a>',
                  '<a href="dambulla-market-price-today.html">Dambulla</a>')
    h = re.sub(r"<p>Other markets:.*?</p>",
               '<p>Other markets: <a href="dambulla-market-price-today.html">Dambulla market price today</a> · '
               '<a href="../market/peliyagoda.html">Peliyagoda</a> · <a href="../market/nuwara-eliya.html">Nuwara Eliya</a> · '
               '<a href="../wholesale.html">HARTI wholesale prices</a></p>', h, flags=re.S)
    h = h.replace("one of Sri Lanka's main wholesale vegetable markets", "Sri Lanka's main up-country vegetable wholesale market")
    h = h.replace("Every day, including weekends.", "On most working days.")
    h = h.replace(" (coconut per nut)", "").replace("; coconut per nut", "")
    h = h.replace('href="../">📈 Charts', 'href="../market/keppetipola.html">📈 Charts')
    h = h.replace('<a class="cta g" href="../">', '<a class="cta g" href="../market/keppetipola.html">')
    h = h.replace('<a href="../">සිංහල</a>', '<a href="../market/keppetipola.html">සිංහල</a>')
    h = h.replace("share/dambulla-wide.png", "icon-512x512.png")
    h = h.replace('"en_dambulla"', '"en_keppetipola"')
    h = h.replace("Dambulla", "Keppetipola").replace("dambulla-market-price-today.html\">Keppetipola",
                                                       "dambulla-market-price-today.html\">Dambulla")
    # the two Dambulla links above were renamed too — put them back
    h = h.replace('href="dambulla-market-price-today.html">Keppetipola market price today',
                  'href="dambulla-market-price-today.html">Dambulla market price today')
    return h, last


def main():
    try:
        kep = json.load(open("keppetipola_dec.json", encoding="utf-8"))
        h, last = make_page(kep)
    except Exception as ex:
        print("English Keppetipola page skipped:", ex)
        return
    if not h:
        print("English Keppetipola page: no prices yet.")
        return
    os.makedirs("en", exist_ok=True)
    open(FILE, "w", encoding="utf-8").write(h)
    print("Wrote", FILE, "for", last)
    if os.path.exists("sitemap.xml"):
        sm = open("sitemap.xml", encoding="utf-8").read()
        if URL in sm:
            sm = re.sub(r"(<loc>" + re.escape(URL) + r"</loc>\s*<lastmod>)[^<]*", r"\g<1>" + last, sm)
        else:
            sm = sm.replace("</urlset>", f"  <url><loc>{URL}</loc><lastmod>{last}</lastmod>"
                                         f"<changefreq>daily</changefreq><priority>0.9</priority></url>\n</urlset>")
        open("sitemap.xml", "w", encoding="utf-8").write(sm)


if __name__ == "__main__":
    main()
