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

PRIMARY = {"Vegetables": "Dambulla", "Other": "Dambulla", "Fruits": "Dambulla",
           "Rice": "Dambulla", "Fish": "Negombo"}

WHOLESALE_PRIMARY = {"Vegetables": "Dambulla", "Other": "Dambulla", "Fruits": "Dambulla",
                     "Rice": "Dambulla", "Fish": "Negombo"}

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

def parse_values(s):
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

FISH_IN_OTHER = {"Katta (Imp)", "Katta", "Sprat (Imp)", "Sprat"}
NO_WHOLESALE = {"Coconut oil", "Red Dhal", "Sugar (White)", "Egg (White)"}

def extract_prices(cat, v, name=""):
    out = {"retail": {}, "wholesale": {}}
    try:
        if cat in ("Vegetables", "Other", "Fruits"):
            if name in NO_WHOLESALE:
                if len(v) >= 6:
                    out["retail"] = {"Pettah": v[1], "Dambulla": v[3], "Narahenpita": v[5]}
                elif len(v) >= 4:
                    out["retail"] = {"Pettah": v[1], "Dambulla": v[3]}
                elif len(v) >= 2:
                    out["retail"] = {"Pettah": v[1]}
            elif name in FISH_IN_OTHER:
                if len(v) >= 6:
                    out["wholesale"] = {"Pettah": v[1]}
                    out["retail"]    = {"Pettah": v[3], "Narahenpita": v[5]}
            elif len(v) >= 10:
                out["wholesale"] = {"Pettah": v[1], "Dambulla": v[3]}
                out["retail"]    = {"Pettah": v[5], "Dambulla": v[7], "Narahenpita": v[9]}
            elif len(v) >= 2:
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
    if markets.get(preferred) is not None:
        return preferred, markets[preferred]
    for m, val in markets.items():
        if val is not None:
            return m, val
    return preferred, None

SERIES_WINDOW = 90   # reports used to choose each item's market

def series_market(day_maps, preferred):
    """Market used for this item's price history: the usual (preferred) market,
    unless it reported the item much less often (under 80%) than another market
    in the last SERIES_WINDOW reports - then the market that reported it most."""
    counts = {}
    for dm in [x for x in day_maps if x][-SERIES_WINDOW:]:
        for m, v in dm.items():
            if v is not None:
                counts[m] = counts.get(m, 0) + 1
    if not counts:
        return preferred
    best = max(counts.values())
    if counts.get(preferred, 0) >= 0.8 * best:     # usual market reports often enough: keep it
        return preferred
    return max(counts, key=lambda m: counts[m])

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
        day_retail, day_wholesale = [], []      # per day: {market: price} or None
        latest_retail, latest_wholesale = {}, {}

        for _, rows in days:
            if n in rows:
                cat = rows[n]["category"]
                unit = rows[n]["unit"]
                p = extract_prices(cat, rows[n]["values"], n)
                day_retail.append(p["retail"])
                day_wholesale.append(p["wholesale"])
                latest_retail    = p["retail"]
                latest_wholesale = p["wholesale"]
            else:
                day_retail.append(None)
                day_wholesale.append(None)

        # One market per item for the whole history, so a change always compares
        # the same market (before: a missing Dambulla price was silently filled
        # with another market's price, which made fake rises and falls).
        r_mkt = series_market(day_retail, PRIMARY.get(cat, "Dambulla"))
        w_mkt = series_market(day_wholesale, WHOLESALE_PRIMARY.get(cat, "Dambulla"))
        retail_series    = [(dm or {}).get(r_mkt) for dm in day_retail]
        wholesale_series = [(dm or {}).get(w_mkt) for dm in day_wholesale]

        if len([x for x in retail_series if x is not None]) < 5:
            continue

        out_rows.append({
            "name": n, "category": cat, "unit": unit,
            "primaryMarket": r_mkt,
            "series": retail_series,
            "markets": latest_retail,
            "wholesaleMarket": w_mkt,
            "wholesaleSeries": wholesale_series,
            "wholesaleMarkets": latest_wholesale
        })

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
