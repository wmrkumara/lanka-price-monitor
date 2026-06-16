#!/usr/bin/env python3
"""
Daily updater for HARTI Wholesale Price data.
Fetches PDFs from Hector Kobbekaduwa Agrarian Research and Training Institute
https://www.harti.gov.lk/daily-price.php
Builds harti_data.json for wholesale.html
"""

import os, re, json, glob, datetime, sys
from urllib.parse import urljoin, unquote, quote
import requests
import pdfplumber

# ── Config ──
LISTING_URL = "https://www.harti.gov.lk/daily-price.php"
BASE_URL    = "https://www.harti.gov.lk/"
PDF_DIR     = "harti_pdfs"
OUT_FILE    = "harti_data.json"
HEADERS     = {
    "User-Agent": "Mozilla/5.0 (Lanka Price Monitor data updater; topgoviya.lk)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── 10 wholesale markets (column order in PDF page 2) ──
MARKETS = [
    "Peliyagoda", "Kandy", "Dambulla", "Meegoda",
    "Norochchole", "Thambuththegama", "Keppetipola",
    "Nuwaraeliya", "Bandarawela", "Veyangoda"
]

# ── Commodity categories ──
CATEGORIES = {
    "Up Country Vegetables": [
        "Beans", "Carrot", "Leeks", "Beetroot", "Beetroot (N.Eliya)",
        "Knolkhol", "Raddish", "Cabbage (N.Eliya)", "Cabbage (Kandy)", "Tomato"
    ],
    "Low Country Vegetables": [
        "Ladies Fingers", "Brinjals", "Capsicum", "Pumpkin", "Cucumber",
        "Bitter Gourd", "Snake Gourd", "Drumstick", "Luffa", "Long Beans",
        "Ash Plantains", "Green Chillies", "Lime", "Sweet Potato",
        "Manioc", "Eggplant"
    ],
    "Potatoes & Onions": [
        "Potato (Imported)", "Potato (Welimada)", "Potato (N.Eliya)",
        "Big Onion (Imported)"
    ],
    "Fruits & Banana": [
        "Banana Ambul", "Banana Kolikuttu", "Banana Seeni",
        "Papaya", "Pineapple (Large)", "Avocado"
    ]
}

RICE_CATEGORIES = {
    "Samba 1": "Rice", "Samba 2": "Rice", "Keeri Samba": "Rice",
    "Nadu 1": "Rice", "Nadu 2": "Rice", "Raw Red": "Rice", "Raw White": "Rice",
    "Green Gram": "Pulses & Essentials", "Cowpea": "Pulses & Essentials",
    "Red Dhal": "Pulses & Essentials", "Dried Chillies (Imp)": "Pulses & Essentials",
    "Sugar (White)": "Pulses & Essentials", "Wheat Flour": "Pulses & Essentials",
    "Eggs (Brown)": "Eggs", "Eggs (White)": "Eggs",
}

# ── Commodity name mapping (PDF text → standard name) ──
NAME_MAP = {
    "Beans": "Beans", "Carrot": "Carrot", "Leeks": "Leeks",
    "Beet root": "Beetroot", "Beet root (N Eliya)": "Beetroot (N.Eliya)",
    "Beet root (N.Eliya)": "Beetroot (N.Eliya)",
    "Knolkhol": "Knolkhol", "Raddish": "Raddish",
    "Cabbage (N'Eliya)": "Cabbage (N.Eliya)", "Cabbage (Kandy)": "Cabbage (Kandy)",
    "Tomato": "Tomato", "Ladies Fingers": "Ladies Fingers",
    "Brinjals": "Brinjals", "Capsicum": "Capsicum", "Pumpkin": "Pumpkin",
    "Cucumber": "Cucumber", "Bitter Gourd": "Bitter Gourd",
    "Snake Gourd": "Snake Gourd", "Drumstick": "Drumstick",
    "Luffa": "Luffa", "Long Beans": "Long Beans",
    "Ash Plantains": "Ash Plantains", "Green Chillies": "Green Chillies",
    "Lime": "Lime", "Sweet Potatoe": "Sweet Potato", "Sweet Potato": "Sweet Potato",
    "Manioc": "Manioc", "Eggplant": "Eggplant",
    "Potato(Imported)": "Potato (Imported)", "Potato (Imported)": "Potato (Imported)",
    "Potato (Welimada)": "Potato (Welimada)",
    "Potato (Nuwaraeliya)": "Potato (N.Eliya)",
    "B'Onion Imported": "Big Onion (Imported)",
    "Big-onion Local": None,  # skip
    "Ambul(Rs/Kg)": "Banana Ambul", "Kolikuttu": "Banana Kolikuttu",
    "Seeni": "Banana Seeni", "Papaya (Rs/Kg)": "Papaya",
    "Pineapple - Large": "Pineapple (Large)", "Avocado": "Avocado",
    # Rice/essentials
    "Samba 1": "Samba 1", "Samba 2": "Samba 2", "Keeri Samba": "Keeri Samba",
    "Nadu 1": "Nadu 1", "Nadu 2": "Nadu 2",
    "Raw red": "Raw Red", "Raw White": "Raw White",
    "Green Gram": "Green Gram", "Cowpea": "Cowpea", "Red Dhal": "Red Dhal",
    "Sugar(White)": "Sugar (White)", "Wheat Flour": "Wheat Flour",
    "Brown": "Eggs (Brown)", "White": "Eggs (White)",
}


# ════════════════════════════════════════════════
#  STEP 1: DISCOVER & DOWNLOAD PDFs
# ════════════════════════════════════════════════

def discover_and_download():
    """Scrape HARTI daily-price.php and download new PDFs."""
    os.makedirs(PDF_DIR, exist_ok=True)

    print(f"Fetching PDF list from {LISTING_URL} ...")
    try:
        resp = requests.get(LISTING_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"WARN: Could not fetch HARTI listing page: {e}")
        print("INFO: Will process existing PDFs in", PDF_DIR)
        return

    # Extract all PDF links from the page
    # Pattern: href="...assets/pdf/food_price/daily/eng/...pdf"
    pdf_links = re.findall(
        r'href=["\']([^"\']*assets/pdf/food_price/daily/eng/[^"\']*\.pdf)["\']',
        html, re.IGNORECASE
    )

    # Also catch full https links
    pdf_links += re.findall(
        r'https://www\.harti\.gov\.lk/assets/pdf/food_price/daily/eng/[^\s"\'<>]+\.pdf',
        html, re.IGNORECASE
    )

    # Build full URLs and deduplicate
    full_urls = set()
    for link in pdf_links:
        if link.startswith("http"):
            full_urls.add(link)
        else:
            full_urls.add(urljoin(BASE_URL, link))

    print(f"Found {len(full_urls)} PDF links on HARTI page.")

    if not full_urls:
        print("WARN: No PDF links found. Check if website structure changed.")
        return

    downloaded = 0
    skipped = 0
    for url in sorted(full_urls):
        # Create a safe local filename from the URL
        # Decode URL encoding for display, then make safe for filesystem
        decoded = unquote(url.split("/")[-1])
        # Make safe filename: remove special chars except dots, hyphens, spaces
        safe_name = re.sub(r'[^\w\s\-\.]', '_', decoded).strip()
        safe_name = re.sub(r'\s+', '_', safe_name)
        if not safe_name.endswith('.pdf'):
            safe_name += '.pdf'

        path = os.path.join(PDF_DIR, safe_name)
        if os.path.exists(path):
            skipped += 1
            continue

        try:
            # URL encode spaces and special chars in the URL
            encoded_url = quote(url, safe=':/?=&%#')
            r = requests.get(encoded_url, headers=HEADERS, timeout=60)
            r.raise_for_status()

            # Verify it's actually a PDF
            if len(r.content) < 1000 or not r.content.startswith(b'%PDF'):
                print(f"  SKIP (not valid PDF): {safe_name}")
                continue

            with open(path, "wb") as f:
                f.write(r.content)
            print(f"  Downloaded: {safe_name}")
            downloaded += 1

        except Exception as e:
            print(f"  WARN: Failed to download {safe_name}: {e}")

    print(f"Download complete: {downloaded} new, {skipped} already existed.")


# ════════════════════════════════════════════════
#  STEP 2: PARSE PDFs
# ════════════════════════════════════════════════

def parse_range(text):
    """Parse '550 - 600' or '550-600' → {'min':550, 'max':600, 'mid':575}"""
    if not text:
        return None
    text = str(text).strip()
    if text in ("-", "", "n.a.", "-"):
        return None
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return {"min": lo, "max": hi, "mid": round((lo + hi) / 2)}
    # Single number
    nums = re.findall(r'\d+', text)
    if nums:
        v = int(nums[0])
        return {"min": v, "max": v, "mid": v}
    return None


def midpoint(r):
    return r["mid"] if r else None


def date_from_filename(path):
    """Extract ISO date from any HARTI filename format."""
    fname = os.path.basename(path)

    # Format: daily_15-01-2026 or daily_15-01-2026.pdf
    m = re.search(r"daily[_\s](\d{2})-(\d{2})-(\d{4})", fname)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    # Format: (2026.06.16) or 2026.06.16
    m = re.search(r"[\(\s_]?(20\d{2})\.(\d{2})\.(\d{2})[\)\s_]?", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Format: 2026_06_16 or 2026-06-16
    m = re.search(r"(20\d{2})[_-](\d{2})[_-](\d{2})", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Format: 20260616
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    return None


def parse_vegetable_page(text):
    """
    Parse the vegetable wholesale price page.
    Returns {commodity_name: [range_or_None × 10_markets]}
    """
    results = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for line in lines:
        # Skip section headers and notes
        if any(h in line for h in [
            "Up Country", "Low Country", "Banana", "Other Fruits",
            "Variety", "Market", "Hector", "Data", "Note", "Usually",
            "Wholesale", "Peliyagoda", "Kandy", "Dambulla"
        ]):
            continue

        matched_std = None
        rest = line

        # Try to match commodity name at start of line
        # Sort by length descending to match longer names first
        for pdf_name in sorted(NAME_MAP.keys(), key=len, reverse=True):
            if line.startswith(pdf_name):
                matched_std = NAME_MAP[pdf_name]
                rest = line[len(pdf_name):].strip()
                break

        if not matched_std:
            continue

        # Extract price ranges from the rest of the line
        # Split by 2+ spaces to separate market columns
        parts = re.split(r'\s{2,}', rest)
        market_prices = []

        for part in parts:
            part = part.strip()
            if not part or part == "-":
                market_prices.append(None)
            else:
                r = parse_range(part)
                market_prices.append(r)

        # Pad to 10 markets
        while len(market_prices) < 10:
            market_prices.append(None)
        market_prices = market_prices[:10]

        # Only store if at least one price found
        if any(p is not None for p in market_prices):
            results[matched_std] = market_prices

    return results


def parse_rice_page(text):
    """
    Parse the rice & essentials page (Pettah + Marandagahamula).
    Returns {item_name: {'pettah_range': dict, 'pettah_avg': float, 'maranda_avg': float}}
    """
    results = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Section tracking
    in_dried_chilli = False
    in_eggs = False

    for line in lines:
        if "Dried Chillies" in line:
            in_dried_chilli = True
            continue
        if "Eggs" in line and "Rs" not in line:
            in_eggs = True
            continue
        if any(h in line for h in ["Rice", "Imported Rice", "Subsidiary", "Onion", "Potatoes", "Pulses", "Consumption"]):
            in_dried_chilli = False
            if "Eggs" not in line:
                in_eggs = False

        # Match known rice/essential items
        matched = None
        for pdf_name, std_name in NAME_MAP.items():
            if pdf_name in ["Brown", "White"] and in_eggs:
                if line.startswith(pdf_name):
                    matched = std_name
                    rest = line[len(pdf_name):].strip()
                    break
            elif line.startswith(pdf_name) and pdf_name in [
                "Samba 1", "Samba 2", "Keeri Samba", "Nadu 1", "Nadu 2",
                "Raw red", "Raw White", "Green Gram", "Cowpea", "Red Dhal",
                "Sugar(White)", "Wheat Flour"
            ]:
                matched = std_name
                rest = line[len(pdf_name):].strip()
                break
            elif in_dried_chilli and line.startswith("Imported"):
                matched = "Dried Chillies (Imp)"
                rest = line[len("Imported"):].strip()
                in_dried_chilli = False
                break

        if not matched:
            continue

        # Extract numbers from the rest
        nums = re.findall(r'\d+\.?\d*', rest)
        if not nums:
            continue

        # Try to get range and average
        r = parse_range(rest)
        avg = None
        if len(nums) >= 3:
            try:
                avg = float(nums[2])
            except ValueError:
                pass
        elif len(nums) >= 1:
            try:
                avg = float(nums[0])
            except ValueError:
                pass

        results[matched] = {
            "pettah_range": r,
            "pettah_avg": avg
        }

    return results


def parse_pdf(path):
    """Parse a single HARTI PDF. Returns (date_str, veg_data, rice_data)."""
    date_str = date_from_filename(path)
    if not date_str:
        print(f"  SKIP (no date in filename): {os.path.basename(path)}")
        return None, {}, {}

    veg_data  = {}
    rice_data = {}

    try:
        with pdfplumber.open(path) as pdf:
            n = len(pdf.pages)

            # Page 1 = Rice & Essentials (English)
            if n >= 1:
                txt1 = pdf.pages[0].extract_text() or ""
                rice_data = parse_rice_page(txt1)

            # Page 2 = Vegetables English table
            if n >= 2:
                txt2 = pdf.pages[1].extract_text() or ""
                veg_data = parse_vegetable_page(txt2)

            # Some older PDFs: English veg on page 1, Sinhala on page 2
            if not veg_data and n >= 1:
                txt1 = pdf.pages[0].extract_text() or ""
                veg_data = parse_vegetable_page(txt1)

    except Exception as e:
        print(f"  WARN: Parse failed for {os.path.basename(path)}: {e}")
        return date_str, {}, {}

    veg_count  = len(veg_data)
    rice_count = len(rice_data)
    print(f"  {date_str}: {veg_count} veg, {rice_count} essentials — {os.path.basename(path)}")
    return date_str, veg_data, rice_data


# ════════════════════════════════════════════════
#  STEP 3: BUILD harti_data.json
# ════════════════════════════════════════════════

def build(pdf_dir=PDF_DIR, out=OUT_FILE):
    """Build harti_data.json from all PDFs in pdf_dir."""
    files = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    if not files:
        print(f"No PDFs found in {pdf_dir}/")
        return

    print(f"\nParsing {len(files)} PDF(s)...")
    all_days = []
    seen_dates = set()

    for f in files:
        date_str, veg, rice = parse_pdf(f)
        if date_str and date_str not in seen_dates:
            all_days.append((date_str, veg, rice))
            seen_dates.add(date_str)

    if not all_days:
        print("No valid data parsed.")
        return

    # Sort by date
    all_days.sort(key=lambda x: x[0])
    dates  = [d for d, _, _ in all_days]
    labels = []
    for d in dates:
        try:
            labels.append(datetime.date.fromisoformat(d).strftime("%-d %b"))
        except Exception:
            labels.append(d)

    # ── Collect all commodity names ──
    all_veg_names = []
    for _, veg, _ in all_days:
        for n in veg:
            if n not in all_veg_names:
                all_veg_names.append(n)

    all_rice_names = []
    for _, _, rice in all_days:
        for n in rice:
            if n not in all_rice_names:
                all_rice_names.append(n)

    commodities = []
    idx = 0

    # ── Vegetable commodities ──
    for name in all_veg_names:
        cat = "Unknown"
        for c, items in CATEGORIES.items():
            if name in items:
                cat = c
                break

        series_by_date = []
        for _, veg, _ in all_days:
            if name in veg:
                series_by_date.append(veg[name])  # list of 10 ranges
            else:
                series_by_date.append([None] * 10)

        # Skip if no real data
        valid = sum(1 for s in series_by_date if any(p is not None for p in s))
        if valid < 1:
            continue

        # Latest market prices
        latest = series_by_date[-1]
        market_prices = {}
        for i, m in enumerate(MARKETS):
            market_prices[m] = latest[i] if i < len(latest) else None

        # Primary = first market with data in latest
        primary = "Peliyagoda"
        for m in MARKETS:
            if market_prices.get(m) is not None:
                primary = m
                break

        # Series = Peliyagoda midpoints over time
        price_series = []
        for s in series_by_date:
            p0 = s[0] if s else None
            price_series.append(midpoint(p0))

        commodities.append({
            "id": idx,
            "name": name,
            "category": cat,
            "unit": "Rs./kg",
            "primaryMarket": primary,
            "markets": market_prices,
            "series": price_series,
        })
        idx += 1

    # ── Rice & Essentials ──
    for name in all_rice_names:
        cat  = RICE_CATEGORIES.get(name, "Rice")
        unit = "Rs./Egg" if "Egg" in name else "Rs./kg"

        price_series = []
        latest_data  = None

        for _, _, rice in all_days:
            if name in rice:
                r = rice[name].get("pettah_range")
                price_series.append(midpoint(r))
                latest_data = rice[name]
            else:
                price_series.append(None)

        valid = sum(1 for s in price_series if s is not None)
        if valid < 1:
            continue

        pettah_range = latest_data.get("pettah_range") if latest_data else None
        pettah_avg   = latest_data.get("pettah_avg")   if latest_data else None

        commodities.append({
            "id": idx,
            "name": name,
            "category": cat,
            "unit": unit,
            "primaryMarket": "Pettah",
            "markets": {"Pettah": midpoint(pettah_range)},
            "series": price_series,
            "pettahRange": pettah_range,
            "pettahAvg": pettah_avg,
        })
        idx += 1

    # ── Write JSON ──
    data = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": "Hector Kobbekaduwa Agrarian Research and Training Institute — Daily Wholesale Price Report",
        "sourceUrl": "https://www.harti.gov.lk/daily-price.php",
        "dates": dates,
        "dateLabels": labels,
        "markets": MARKETS,
        "commodities": commodities
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)

    print(f"\n✅ {out} written successfully!")
    print(f"   📦 {len(commodities)} commodities")
    print(f"   📅 {len(dates)} dates ({dates[0]} → {dates[-1]})")
    print(f"   🏪 {len(MARKETS)} markets")


# ════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════

if __name__ == "__main__":
    if "--no-download" not in sys.argv:
        discover_and_download()
    build()
