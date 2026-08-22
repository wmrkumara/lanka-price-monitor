#!/usr/bin/env python3
"""
Daily updater for CBSL Daily Economic Indicators (DEI).
Fetches PDFs from the CBSL listing page — same approach as update.py.
Extracts: Exchange Rates, Stock Market (ASPI, S&P SL20), Money Market, Currency/Reserve Money.
Output: dei_data.json
"""

import os, re, json, glob, datetime, sys
import requests
import pdfplumber

LISTING_URL = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/daily-indicators"
PDF_DIR     = "dei_pdfs"
OUT_FILE    = "dei_data.json"
HEADERS     = {"User-Agent": "Mozilla/5.0 (price-monitor data updater)"}

# ── Discover & Download ──────────────────────────────────────────────────────

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
    # Also try relative links
    rel = re.findall(r'href=["\']([^"\']+daily_economic_indicators_\d{8}_e[^"\']*\.pdf)["\']', html)
    for r in rel:
        if r.startswith("http"):
            links.add(r)
        else:
            links.add("https://www.cbsl.gov.lk" + r)

    print(f"Found {len(links)} DEI report links on the listing page.")
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

# ── Parse PDF ────────────────────────────────────────────────────────────────

def extract_number(text, pattern, group=1):
    """Extract first float matching pattern from text."""
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(group).replace(",", ""))
    except Exception:
        return None

def parse_dei_pdf(path):
    """
    Parse a DEI PDF and return a dict of extracted values.
    DEI PDF contains (from text extraction):
      - Exchange Rates: Rs. Per USD (and others)
      - Stock Market: ASPI, S&P SL20
      - Money Market: AWCMR, AWRR, Overnight Liquidity
      - Currency: Currency in Circulation, Reserve Money
    """
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

    # ── Exchange Rate: USD/LKR ──────────────────────────────────────────────
    # Pattern: "Rs. Per USD  315.21" or "315.21  Rs. Per USD"
    usd = extract_number(text, r'Rs\.\s*Per\s*USD\s*([\d,]+\.?\d*)')
    if usd is None:
        usd = extract_number(text, r'([\d,]+\.?\d*)\s*Rs\.\s*Per\s*USD')
    result["usd_lkr"] = usd

    # ── Stock Market ─────────────────────────────────────────────────────────
    # ASPI appears before S&P SL20 in the text
    # Pattern: large numbers like 17000-25000 range for ASPI
    aspi = extract_number(text, r'ASPI[^\d]*([\d,]+\.?\d*)')
    result["aspi"] = aspi

    sp20 = extract_number(text, r'S&P\s*SL\s*20[^\d]*([\d,]+\.?\d*)')
    if sp20 is None:
        sp20 = extract_number(text, r'SL20[^\d]*([\d,]+\.?\d*)')
    result["sp_sl20"] = sp20

    # ── Money Market ─────────────────────────────────────────────────────────
    # AWCMR (Avg Weighted Call Money Rate)
    awcmr = extract_number(text, r'AWCMR[^\d]*([\d,]+\.?\d*)')
    result["awcmr"] = awcmr

    # AWRR (Avg Weighted Repo Rate)
    awrr = extract_number(text, r'AWRR[^\d]*([\d,]+\.?\d*)')
    result["awrr"] = awrr

    # Overnight Liquidity (Rs. bn)
    liq = extract_number(text, r'Overnight\s*Liquidity[^\d]*([\d,]+\.?\d*)')
    result["overnight_liquidity_bn"] = liq

    # ── Currency & Reserve Money (Rs. mn) ─────────────────────────────────
    # "Currency in Circulation  Reserve Money  1,896,252.00  1,889,828.80  1,652,639.88  1,655,040.41"
    # Latest (current day) values are the 2nd pair typically
    cur_match = re.findall(r'Currency\s*in\s*Circulation[^\d]*([\d,]+\.?\d*)', text)
    result["currency_circulation_mn"] = float(cur_match[0].replace(",","")) if cur_match else None

    res_match = re.findall(r'Reserve\s*Money[^\d]*([\d,]+\.?\d*)', text)
    result["reserve_money_mn"] = float(res_match[0].replace(",","")) if res_match else None

    return result

def date_from_fname(fname):
    m = re.search(r'(\d{8})', fname)
    if not m:
        return None
    s = m.group(1)
    try:
        return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8])).isoformat()
    except Exception:
        return None

# ── Build JSON ───────────────────────────────────────────────────────────────

def build():
    # Load existing data
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE) as f:
            db = json.load(f)
    else:
        db = {"generated": "", "source": "Central Bank of Sri Lanka – Daily Economic Indicators", "records": []}

    existing_dates = {r["date"] for r in db.get("records", [])}
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "daily_economic_indicators_*_e.pdf")))
    new_count = 0

    for path in pdfs:
        fname = os.path.basename(path)
        date  = date_from_fname(fname)
        if not date or date in existing_dates:
            continue
        parsed = parse_dei_pdf(path)
        if not any(v is not None for v in parsed.values()):
            print(f"SKIP (no data extracted): {fname}")
            continue
        record = {"date": date, **parsed}
        db["records"].append(record)
        existing_dates.add(date)
        print(f"Parsed {date}: USD={parsed.get('usd_lkr')}, ASPI={parsed.get('aspi')}, AWCMR={parsed.get('awcmr')}")
        new_count += 1

    if new_count == 0:
        print("No new DEI records to add.")
        return

    db["records"].sort(key=lambda r: r["date"])
    db["generated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    with open(OUT_FILE, "w") as f:
        json.dump(db, f, separators=(",", ":"))
    print(f"Written {OUT_FILE} — {len(db['records'])} records total, {new_count} new.")

# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--build-only" not in sys.argv:
        discover_and_download()
    build()
