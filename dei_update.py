#!/usr/bin/env python3
"""
Daily updater for CBSL Daily Economic Indicators (DEI).
Same pattern as update.py — fetches from CBSL listing page.
Output: dei_data.json
"""

import os, re, json, glob, datetime, sys
import requests
import pdfplumber

LISTING_URL = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/daily-indicators"
PDF_DIR     = "dei_pdfs"
OUT_FILE    = "dei_data.json"
HEADERS     = {"User-Agent": "Mozilla/5.0 (price-monitor data updater)"}

# ── Discover & Download ───────────────────────────────────────────────────────

def discover_and_download():
    os.makedirs(PDF_DIR, exist_ok=True)
    try:
        html = requests.get(LISTING_URL, headers=HEADERS, timeout=30).text
    except Exception as e:
        print("WARN: could not reach listing page:", e)
        return
    links = set(re.findall(
        r"https://[^\s\"']+daily_economic_indicators_\d{8}_e[^\s\"']*\.pdf", html
    ))
    rel = re.findall(r'href=["\']([^"\']+daily_economic_indicators_\d{8}_e[^"\']*\.pdf)["\']', html)
    for r in rel:
        links.add(r if r.startswith("http") else "https://www.cbsl.gov.lk" + r)
    print(f"Found {len(links)} DEI PDF links.")
    for url in sorted(links):
        fname = re.sub(r'[?#].*', '', url.split("/")[-1])
        path  = os.path.join(PDF_DIR, fname)
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

# ── Parse PDF ─────────────────────────────────────────────────────────────────

def parse_dei_pdf(path):
    result = {}
    try:
        with pdfplumber.open(path) as pdf:
            text = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += " " + t
    except Exception as e:
        print(f"WARN: could not parse {path}: {e}")
        return result

    def flt(s):
        try: return float(s.replace(",",""))
        except: return None

    # ── Exchange Rates ──
    usd = re.search(r'USD\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)', text)
    result["usd_lkr"]      = flt(usd.group(1)) if usd else None
    result["usd_lkr_sell"] = flt(usd.group(2)) if usd else None

    gbp = re.search(r'GBP\s+([\d,]+\.\d+)', text)
    result["gbp_lkr"] = flt(gbp.group(1)) if gbp else None

    eur = re.search(r'EUR\s+([\d,]+\.\d+)', text)
    result["eur_lkr"] = flt(eur.group(1)) if eur else None

    jpy = re.search(r'JPY\s+([\d,]+\.\d+)', text)
    result["jpy_lkr"] = flt(jpy.group(1)) if jpy else None

    # USD/LKR Spot rate (standalone 3-digit.2 near chart label)
    spot = re.search(r'\.sR\s*([\d,]+\.\d+)', text)
    result["usd_lkr_spot"] = flt(spot.group(1)) if spot else None

    # ── Money Market ──
    liq = re.search(r'Overnight Liquidity \(Rs\. bn\)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)', text)
    result["overnight_liquidity_bn"] = flt(liq.group(2)) if liq else None

    # AWCMR & AWRR appear BEFORE the label in extracted text
    awcmr_awrr = re.search(r'([\d.]+)\s+([\d.]+)\s+\(b\)\s+AWCMR\s+AWRR', text)
    if awcmr_awrr:
        result["awcmr"] = flt(awcmr_awrr.group(1))
        result["awrr"]  = flt(awcmr_awrr.group(2))
    else:
        result["awcmr"] = None
        result["awrr"]  = None

    # ── Stock Market ──
    # ASPI: large number like 21,405.62 (5 digits with comma)
    aspi_candidates = re.findall(r'(\d{2},\d{3}\.\d+)', text)
    result["aspi"] = flt(aspi_candidates[0]) if aspi_candidates else None

    # S&P SL20: 4-digit number like 6,019.25
    sp20_candidates = re.findall(r'(\d{1},\d{3}\.\d+)', text)
    result["sp_sl20"] = flt(sp20_candidates[-1]) if sp20_candidates else None

    # ── Currency & Reserve Money ──
    cic = re.search(r'Currency in Circulation\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)', text)
    result["currency_circulation_mn"] = flt(cic.group(2)) if cic else None

    rm = re.search(r'Reserve Money\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)', text)
    result["reserve_money_mn"] = flt(rm.group(2)) if rm else None

    # ── Energy ──
    petrol = re.search(r'Petrol \(92 octane\):\s*([\d\s.]+)', text)
    if petrol:
        try: result["petrol_lkr"] = float(petrol.group(1).replace(" ","").split()[0])
        except: result["petrol_lkr"] = None
    else:
        result["petrol_lkr"] = None

    diesel = re.search(r'Auto Diesel:\s*([\d\s.]+)', text)
    if diesel:
        try: result["auto_diesel_lkr"] = float(diesel.group(1).replace(" ","").split()[0])
        except: result["auto_diesel_lkr"] = None
    else:
        result["auto_diesel_lkr"] = None

    return result

def date_from_fname(fname):
    m = re.search(r'(\d{8})', fname)
    if not m: return None
    s = m.group(1)
    try: return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8])).isoformat()
    except: return None

# ── Build JSON ────────────────────────────────────────────────────────────────

def build():
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE) as f:
            db = json.load(f)
    else:
        db = {"generated":"","source":"Central Bank of Sri Lanka – Daily Economic Indicators","records":[]}

    existing_dates = {r["date"] for r in db.get("records",[])}
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "daily_economic_indicators_*_e.pdf")))
    new_count = 0

    for path in pdfs:
        date = date_from_fname(os.path.basename(path))
        if not date or date in existing_dates:
            continue
        parsed = parse_dei_pdf(path)
        if not any(v is not None for v in parsed.values()):
            print(f"SKIP (no data): {os.path.basename(path)}")
            continue
        db["records"].append({"date": date, **parsed})
        existing_dates.add(date)
        print(f"Parsed {date}: USD={parsed.get('usd_lkr')}, ASPI={parsed.get('aspi')}, AWCMR={parsed.get('awcmr')}")
        new_count += 1

    if new_count == 0:
        print("No new DEI records.")
        return

    db["records"].sort(key=lambda r: r["date"])
    db["generated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    with open(OUT_FILE, "w") as f:
        json.dump(db, f, separators=(",",":"))
    print(f"Written {OUT_FILE} — {len(db['records'])} total, {new_count} new.")

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--build-only" not in sys.argv:
        discover_and_download()
    build()
