#!/usr/bin/env python3
"""
Daily updater for the Sri Lanka Food Price Monitor.

What it does, every time you run it:
  1. Reads the CBSL "Daily Price Report" listing page.
  2. Finds every report PDF and downloads any it doesn't already have (into ./pdfs/).
  3. Parses page 2 of all downloaded PDFs.
  4. Writes data.json (which the website reads).

Run locally:   python update.py
Run on a server / GitHub Actions: same command, on a schedule.
"""

import os, re, json, glob, datetime, sys
import requests
import pdfplumber

LISTING_URL = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report"
PDF_DIR = "pdfs"
HEADERS = {"User-Agent": "Mozilla/5.0 (price-monitor data updater)"}

SECTIONS = {"V E G E T A B L E S": "Vegetables", "O T H E R": "Other",
            "R I C E": "Rice", "F I S H": "Fish", "F R U I T S": "Fruits"}
PRIMARY = {"Vegetables": "Dambulla", "Other": "Dambulla", "Fruits": "Dambulla",
           "Rice": "Dambulla", "Fish": "Negombo"}


# ---------- 1 & 2: discover and download PDFs ----------
def discover_and_download():
    os.makedirs(PDF_DIR, exist_ok=True)
    try:
        html = requests.get(LISTING_URL, headers=HEADERS, timeout=30).text
    except Exception as e:
        print("WARN: could not reach listing page:", e)
        return
    # English reports look like: .../pricerpt/price_report_YYYYMMDD_e[...].pdf
    links = set(re.findall(r"https://[^\s\"']+price_report_\d{8}_e[^\s\"']*\.pdf", html))
    print(f"Found {len(links)} report links on the listing page.")
    for url in sorted(links):
        fname = url.split("/")[-1]
        path = os.path.join(PDF_DIR, fname)
        if os.path.exists(path):
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            print("Downloaded", fname)
        except Exception as e:
            print("WARN: failed to download", fname, e)


# ---------- 3: parse one PDF's page 2 ----------
def parse_values(s):
    """Source quirk: the leading digit is split off by a space ('6 00.00' -> 600.00)."""
    vals, buf = [], ""
    for t in s.split():
        if t in ("n.a.", "n.a"):
            vals.append(None); buf = ""; continue
        buf += t
        if "." in t:
            try: vals.append(float(buf.replace(",", "")))
            except ValueError: pass
            buf = ""
    return vals

def parse_page2(path):
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) < 2:
            return {}
        txt = pdf.pages[1].extract_text() or ""
    rows, cur = {}, None
    for line in txt.split("\n"):
        line = line.strip()
        if line in SECTIONS:
            cur = SECTIONS[line]; continue
        if cur is None:
            continue
        m = re.match(r"^(.+?)\s+(Rs\./(?:kg|Nut|Ltr|Each))\s+(.*)$", line)
        if not m:
            continue
        rows[m.group(1).strip()] = {"category": cur, "unit": m.group(2),
                                    "values": parse_values(m.group(3))}
    return rows

def date_from(path):
    d = re.search(r"(\d{8})", os.path.basename(path)).group(1)
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"

def retail_today(cat, v):
    try:
        if cat in ("Vegetables", "Other", "Fruits") and len(v) >= 10:
            return {"Pettah": v[5], "Dambulla": v[7], "Narahenpita": v[9]}
        if cat == "Fish" and len(v) >= 8:
            return {"Negombo": v[5], "Marandagahamula": v[7]}
        if cat == "Rice" and len(v) >= 8:
            return {"Pettah": v[5], "Dambulla": v[7]}
    except IndexError:
        pass
    return {}


# ---------- 4: build data.json ----------
def build(pdf_dir=PDF_DIR, out="data.json"):
    files = sorted(glob.glob(os.path.join(pdf_dir, "price_report_*_e*.pdf")))
    if not files:
        print("No PDFs to process.")
        return
    days = [(date_from(f), parse_page2(f)) for f in files]
    # de-duplicate by date (keep the last file seen for a date), then sort
    by_date = {}
    for d, rows in days:
        by_date[d] = rows
    days = sorted(by_date.items())

    dates = [d for d, _ in days]
    labels = [datetime.date.fromisoformat(d).strftime("%-d %b") for d in dates]

    names = []
    for _, rows in days:
        for n in rows:
            if n not in names:
                names.append(n)

    out_rows = []
    for n in names:
        cat = unit = None
        series, latest_markets = [], {}
        for _, rows in days:
            if n in rows:
                cat, unit = rows[n]["category"], rows[n]["unit"]
                tr = retail_today(cat, rows[n]["values"])
                series.append(tr.get(PRIMARY.get(cat, "Dambulla")))
                latest_markets = tr
            else:
                series.append(None)
        if len([x for x in series if x is not None]) < 5:
            continue
        out_rows.append({"name": n, "category": cat, "unit": unit,
                         "primaryMarket": PRIMARY.get(cat, "Dambulla"),
                         "series": series, "markets": latest_markets})

    # simple sanity guard: warn on >60% single-step jumps (possible bad parse)
    for r in out_rows:
        vals = [x for x in r["series"] if x is not None]
        for a, b in zip(vals, vals[1:]):
            if a and abs(b - a) / a > 0.6:
                print(f"  CHECK: {r['name']} jumped {a:.0f} -> {b:.0f}")

    data = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "source": "Central Bank of Sri Lanka - Daily Price Report",
            "dates": dates, "dateLabels": labels, "commodities": out_rows}
    json.dump(data, open(out, "w"), indent=1)
    print(f"Wrote {out}: {len(out_rows)} commodities over {len(dates)} dates "
          f"({dates[0]} to {dates[-1]}).")


if __name__ == "__main__":
    if "--no-download" not in sys.argv:
        discover_and_download()
    build()
