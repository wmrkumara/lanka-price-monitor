#!/usr/bin/env python3
"""
Daily updater for the Sri Lanka Food Price Monitor.
Extracts both retail AND wholesale prices from CBSL Daily Price Report PDFs.
"""

import os, re, json, glob, datetime, sys
import requests
import pdfplumber

LISTING_URL = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report"
PDF_DIR = "pdfs"
HEADERS = {"User-Agent": "Mozilla/5.0 (price-monitor data updater)"}

SECTIONS = {"V E G E T A B L E S": "Vegetables", "O T H E R": "Other",
            "R I C E": "Rice", "F I S H": "Fish", "F R U I T S": "Fruits"}

# Primary retail market per category
PRIMARY = {"Vegetables": "Dambulla", "Other": "Dambulla", "Fruits": "Dambulla",
           "Rice": "Dambulla", "Fish": "Negombo"}

# Primary wholesale market per category
WHOLESALE_PRIMARY = {"Vegetables": "Dambulla", "Other": "Dambulla", "Fruits": "Dambulla",
                     "Rice": "Dambulla", "Fish": "Negombo"}


# ---------- 1 & 2: discover and download PDFs ----------
def discover_and_download():
    os.makedirs(PDF_DIR, exist_ok=True)
    try:
        html = requests.get(LISTING_URL, headers=HEADERS, timeout=30).text
    except Exception as e:
        print("WARN: could not reach listing page:", e)
        return
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
    """Parse a string of values including n.a. entries."""
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


# Fish items that appear under the "Other" category in the PDF
FISH_IN_OTHER = {"Katta (Imp)", "Katta", "Sprat (Imp)", "Sprat"}

def extract_prices(cat, v, name=""):
    """Extract wholesale and retail prices from the values list.

    PDF page 2 column layout:
    Vegetables / Other / Fruits (10 values):
      v[0]=W-Pettah-Yday   v[1]=W-Pettah-Today
      v[2]=W-Dambulla-Yday  v[3]=W-Dambulla-Today
      v[4]=R-Pettah-Yday   v[5]=R-Pettah-Today
      v[6]=R-Dambulla-Yday  v[7]=R-Dambulla-Today
      v[8]=R-Narahenpita-Yday  v[9]=R-Narahenpita-Today
    Produce items with no wholesale (6 values - Oil, Sugar, Dhal, Egg):
      v[0]=R-Pettah-Yday   v[1]=R-Pettah-Today
      v[2]=R-Dambulla-Yday  v[3]=R-Dambulla-Today
      v[4]=R-Narahenpita-Yday  v[5]=R-Narahenpita-Today
    Fish-in-Other items (Katta, Sprat - 6 values):
      v[0]=W-Pettah-Yday   v[1]=W-Pettah-Today
      v[2]=R-Pettah-Yday   v[3]=R-Pettah-Today
      v[4]=R-Narahenpita-Yday  v[5]=R-Narahenpita-Today
    Fruits with single market (Apple, Orange - 2 values):
      v[0]=R-Narahenpita-Yday  v[1]=R-Narahenpita-Today
    Rice (8-10 values):
      v[0..3] wholesale, v[4..9] retail Pettah+Dambulla(+Narahenpita)
    Fish (8 values):
      v[0]=W-Peliyagoda-Yday  v[1]=W-Peliyagoda-Today
      v[2]=W-Negombo-Yday     v[3]=W-Negombo-Today
      v[4]=R-Negombo-Yday     v[5]=R-Negombo-Today
      v[6]=R-Marandagahamula-Yday  v[7]=R-Marandagahamula-Today
    """
    out = {"retail": {}, "wholesale": {}}
    try:
        if cat in ("Vegetables", "Other", "Fruits"):
            if len(v) >= 10:
                out["wholesale"] = {"Pettah": v[1], "Dambulla": v[3]}
                out["retail"]    = {"Pettah": v[5], "Dambulla": v[7], "Narahenpita": v[9]}
            elif len(v) >= 6:
                if name in FISH_IN_OTHER:
                    # Fish items under Other: W-Pettah, R-Pettah, R-Narahenpita
                    out["wholesale"] = {"Pettah": v[1]}
                    out["retail"]    = {"Pettah": v[3], "Narahenpita": v[5]}
                else:
                    # Produce items with no wholesale: R-Pettah, R-Dambulla, R-Narahenpita
                    out["retail"] = {"Pettah": v[1], "Dambulla": v[3], "Narahenpita": v[5]}
            elif len(v) >= 2:  # Apple, Orange etc - Narahenpita retail only
                out["retail"] = {"Narahenpita": v[1]}
        elif cat == "Rice":
            if len(v) >= 8:
                out["wholesale"] = {"Pettah": v[1], "Dambulla": v[3]}
                out["retail"]    = {"Pettah": v[5], "Dambulla": v[7]}
                if len(v) >= 10:
                    out["retail"]["Narahenpita"] = v[9]
            elif len(v) >= 2:
                out["retail"] = {"Pettah": v[1]}
        elif cat == "Fish":
            if len(v) >= 8:
                out["wholesale"] = {"Peliyagoda": v[1], "Negombo": v[3]}
                out["retail"]    = {"Negombo": v[5], "Marandagahamula": v[7]}
            elif len(v) >= 6:
                out["wholesale"] = {"Peliyagoda": v[1], "Negombo": v[3]}
                out["retail"]    = {"Negombo": v[5]}
            elif len(v) >= 2:
                out["retail"] = {"Negombo": v[1]}
    except IndexError:
        pass
    return out


def pick_primary(markets, preferred):
    """Return (market_name, value) for the best available market."""
    if markets.get(preferred) is not None:
        return preferred, markets[preferred]
    for m, val in markets.items():
        if val is not None:
            return m, val
    return preferred, None


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


# ---------- 4: build data.json ----------
def build(pdf_dir=PDF_DIR, out="data.json"):
    files = sorted(glob.glob(os.path.join(pdf_dir, "price_report_*_e*.pdf")))
    if not files:
        print("No PDFs to process.")
        return
    days = [(date_from(f), parse_page2(f)) for f in files]
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
        retail_series, wholesale_series = [], []
        latest_retail, latest_wholesale = {}, {}

        for _, rows in days:
            if n in rows:
                cat = rows[n]["category"]
                unit = rows[n]["unit"]
                p = extract_prices(cat, rows[n]["values"], n)

                _, rval = pick_primary(p["retail"],    PRIMARY.get(cat, "Dambulla"))
                _, wval = pick_primary(p["wholesale"], WHOLESALE_PRIMARY.get(cat, "Dambulla"))

                retail_series.append(rval)
                wholesale_series.append(wval)
                latest_retail    = p["retail"]
                latest_wholesale = p["wholesale"]
            else:
                retail_series.append(None)
                wholesale_series.append(None)

        if len([x for x in retail_series if x is not None]) < 5:
            continue

        primary_mkt, _ = pick_primary(latest_retail, PRIMARY.get(cat, "Dambulla"))

        out_rows.append({
            "name": n, "category": cat, "unit": unit,
            "primaryMarket": primary_mkt,
            "series": retail_series,
            "markets": latest_retail,
            "wholesaleSeries": wholesale_series,
            "wholesaleMarkets": latest_wholesale
        })

    # sanity guard: warn on >60% single-step jumps
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
