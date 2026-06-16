#!/usr/bin/env python3
"""
Daily updater for HARTI Wholesale Price data.
Fetches PDFs from Hector Kobbekaduwa Agrarian Research and Training Institute
and builds harti_data.json for wholesale.html
"""

import os, re, json, glob, datetime, sys
import requests
import pdfplumber

# ── HARTI website URL ──
LISTING_URL = "https://www.harti.gov.lk/index.php/en/market-information/wholesale-prices"
PDF_DIR = "harti_pdfs"
HEADERS = {"User-Agent": "Mozilla/5.0 (price-monitor data updater; Lanka Price Monitor)"}

# ── 10 wholesale markets (column order in PDF) ──
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

# ── Rice/Essentials from Page 1 (Pettah only) ──
RICE_ITEMS = {
    "Samba 1": "Rice",
    "Samba 2": "Rice",
    "Keeri Samba": "Rice",
    "Nadu 1": "Rice",
    "Nadu 2": "Rice",
    "Raw Red": "Rice",
    "Raw White": "Rice",
    "Green Gram": "Pulses & Essentials",
    "Cowpea": "Pulses & Essentials",
    "Red Dhal": "Pulses & Essentials",
    "Dried Chillies (Imp)": "Pulses & Essentials",
    "Sugar (White)": "Pulses & Essentials",
    "Wheat Flour": "Pulses & Essentials",
    "Eggs (Brown)": "Eggs",
    "Eggs (White)": "Eggs",
}


def discover_and_download():
    """Find and download new HARTI PDFs."""
    os.makedirs(PDF_DIR, exist_ok=True)
    try:
        html = requests.get(LISTING_URL, headers=HEADERS, timeout=30).text
    except Exception as e:
        print("WARN: could not reach HARTI listing page:", e)
        print("INFO: Using existing PDFs in", PDF_DIR)
        return

    # Look for PDF links on the HARTI website
    links = set(re.findall(r'https?://[^\s\'"]+\.pdf', html, re.IGNORECASE))
    # Also look for relative links
    rel_links = re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, re.IGNORECASE)
    for rl in rel_links:
        if rl.startswith("/"):
            links.add("https://www.harti.gov.lk" + rl)

    print(f"Found {len(links)} PDF links on HARTI listing page.")

    for url in sorted(links):
        fname = url.split("/")[-1]
        # Only process vegetable/wholesale price PDFs
        if not any(k in fname.lower() for k in ["vegetable", "wholesale", "price"]):
            continue
        path = os.path.join(PDF_DIR, fname)
        if os.path.exists(path):
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            print("Downloaded:", fname)
        except Exception as e:
            print("WARN: failed to download", fname, e)


def parse_range(text):
    """Parse '550 - 600' → {'min': 550, 'max': 600, 'mid': 575}"""
    text = str(text).strip()
    if not text or text == "-":
        return None
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return {"min": lo, "max": hi, "mid": round((lo + hi) / 2)}
    # Single value
    try:
        v = float(re.sub(r"[^\d.]", "", text))
        return {"min": int(v), "max": int(v), "mid": int(v)}
    except ValueError:
        return None


def midpoint(r):
    """Get midpoint from a range dict."""
    return r["mid"] if r else None


def date_from_filename(path):
    """Extract date from filename like daily_15-01-2026.pdf or Vegetable_Price_2026_06_15.pdf"""
    fname = os.path.basename(path)

    # Format: daily_15-01-2026
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", fname)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    # Format: 2026_06_15 or 2026-06-15
    m = re.search(r"(20\d{2})[_-](\d{2})[_-](\d{2})", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Format: 20260615
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    return None


def parse_vegetable_page(page_text):
    """
    Parse vegetable wholesale price page.
    Returns dict: {commodity_name: [range_or_none × 10_markets]}
    """
    results = {}
    lines = page_text.split("\n")

    # Known commodity names to match against
    all_commodities = []
    for items in CATEGORIES.values():
        all_commodities.extend(items)

    # Map of PDF text variations → standard names
    NAME_MAP = {
        "Beans": "Beans",
        "Carrot": "Carrot",
        "Leeks": "Leeks",
        "Beet root": "Beetroot",
        "Beet root (N Eliya)": "Beetroot (N.Eliya)",
        "Beet root (N.Eliya)": "Beetroot (N.Eliya)",
        "Knolkhol": "Knolkhol",
        "Raddish": "Raddish",
        "Cabbage (N'Eliya)": "Cabbage (N.Eliya)",
        "Cabbage (Kandy)": "Cabbage (Kandy)",
        "Tomato": "Tomato",
        "Ladies Fingers": "Ladies Fingers",
        "Brinjals": "Brinjals",
        "Capsicum": "Capsicum",
        "Pumpkin": "Pumpkin",
        "Cucumber": "Cucumber",
        "Bitter Gourd": "Bitter Gourd",
        "Snake Gourd": "Snake Gourd",
        "Drumstick": "Drumstick",
        "Luffa": "Luffa",
        "Long Beans": "Long Beans",
        "Ash Plantains": "Ash Plantains",
        "Green Chillies": "Green Chillies",
        "Lime": "Lime",
        "Sweet Potatoe": "Sweet Potato",
        "Sweet Potato": "Sweet Potato",
        "Manioc": "Manioc",
        "Eggplant": "Eggplant",
        "Potato(Imported)": "Potato (Imported)",
        "Potato (Imported)": "Potato (Imported)",
        "Potato (Welimada)": "Potato (Welimada)",
        "Potato (Nuwaraeliya)": "Potato (N.Eliya)",
        "B'Onion Imported": "Big Onion (Imported)",
        "Ambul(Rs/Kg)": "Banana Ambul",
        "Kolikuttu": "Banana Kolikuttu",
        "Seeni": "Banana Seeni",
        "Papaya (Rs/Kg)": "Papaya",
        "Pineapple - Large": "Pineapple (Large)",
        "Avocado": "Avocado",
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try to match a known commodity name at start of line
        matched_name = None
        for pdf_name, std_name in NAME_MAP.items():
            if line.startswith(pdf_name):
                matched_name = std_name
                rest = line[len(pdf_name):].strip()
                break

        if not matched_name:
            continue

        # Extract all number ranges from the rest of the line
        # Pattern: digits - digits (with optional spaces)
        range_pattern = re.finditer(r"(\d+)\s*[-–]\s*(\d+)", rest)
        ranges_found = []
        for rm in range_pattern:
            lo, hi = int(rm.group(1)), int(rm.group(2))
            ranges_found.append({"min": lo, "max": hi, "mid": round((lo + hi) / 2)})

        # Also find standalone dashes (missing data)
        # We build a 10-element list
        # Simple approach: count tokens separated by spaces
        tokens = re.split(r"\s{2,}", rest)
        market_prices = []
        for tok in tokens:
            tok = tok.strip()
            if not tok or tok == "-":
                market_prices.append(None)
            else:
                r = parse_range(tok)
                market_prices.append(r)

        # Pad or trim to 10 markets
        while len(market_prices) < 10:
            market_prices.append(None)
        market_prices = market_prices[:10]

        # Only store if at least one market has data
        if any(p is not None for p in market_prices):
            results[matched_name] = market_prices

    return results


def parse_rice_page(page_text):
    """
    Parse rice/essentials page (Pettah + Marandagahamula).
    Returns dict: {item_name: {'pettah_avg': float, 'maranda_avg': float, 'pettah_range': dict}}
    """
    results = {}
    lines = page_text.split("\n")

    ITEM_MAP = {
        "Samba 1": "Samba 1",
        "Samba 2": "Samba 2",
        "Keeri Samba": "Keeri Samba",
        "Nadu 1": "Nadu 1",
        "Nadu 2": "Nadu 2",
        "Raw red": "Raw Red",
        "Raw White": "Raw White",
        "Green Gram": "Green Gram",
        "Cowpea": "Cowpea",
        "Red Dhal": "Red Dhal",
        "Imported": "Dried Chillies (Imp)",  # Under Dried Chillies section
        "Sugar(White)": "Sugar (White)",
        "Wheat Flour": "Wheat Flour",
        "Brown": "Eggs (Brown)",
        "White": "Eggs (White)",
    }

    current_section = None
    for line in lines:
        line = line.strip()
        if "Dried Chillies" in line:
            current_section = "dried_chillies"
            continue
        if "Onion" in line and "Big" not in line:
            current_section = "onion"
            continue
        if "Eggs" in line:
            current_section = "eggs"
            continue

        for pdf_name, std_name in ITEM_MAP.items():
            if line.startswith(pdf_name):
                rest = line[len(pdf_name):].strip()
                nums = re.findall(r"\d+\.?\d*", rest)
                if len(nums) >= 2:
                    r = parse_range(rest)
                    try:
                        avg = float(nums[2]) if len(nums) > 2 else float(nums[1])
                    except (IndexError, ValueError):
                        avg = None
                    results[std_name] = {
                        "pettah_range": r,
                        "pettah_avg": avg
                    }
                break

    return results


def parse_pdf(path):
    """Parse a single HARTI PDF. Returns (date_str, veg_data, rice_data)."""
    date_str = date_from_filename(path)
    if not date_str:
        print(f"WARN: could not parse date from {path}")
        return None, {}, {}

    veg_data = {}
    rice_data = {}

    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages

            # Page 1: Rice & Essentials
            if len(pages) >= 1:
                txt1 = pages[0].extract_text() or ""
                rice_data = parse_rice_page(txt1)

            # Page 2: Vegetables (English)
            if len(pages) >= 2:
                txt2 = pages[1].extract_text() or ""
                veg_data = parse_vegetable_page(txt2)

            # Some PDFs have English on page 1 and Sinhala on page 2
            # Try page 3 if page 2 gave no results
            if not veg_data and len(pages) >= 3:
                txt3 = pages[2].extract_text() or ""
                veg_data = parse_vegetable_page(txt3)

    except Exception as e:
        print(f"WARN: failed to parse {path}: {e}")

    print(f"  {date_str}: {len(veg_data)} veg items, {len(rice_data)} rice/essential items")
    return date_str, veg_data, rice_data


def build(pdf_dir=PDF_DIR, out="harti_data.json"):
    """Build harti_data.json from all PDFs in pdf_dir."""
    files = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    if not files:
        print("No HARTI PDFs found in", pdf_dir)
        print("Place HARTI wholesale PDF files in the", pdf_dir, "folder.")
        return

    print(f"Processing {len(files)} PDF(s)...")

    # Parse all PDFs
    all_days = []
    for f in files:
        date_str, veg_data, rice_data = parse_pdf(f)
        if date_str:
            all_days.append((date_str, veg_data, rice_data))

    if not all_days:
        print("No valid data parsed.")
        return

    # Sort by date
    all_days.sort(key=lambda x: x[0])

    dates = [d for d, _, _ in all_days]
    labels = [datetime.date.fromisoformat(d).strftime("%-d %b") for d in dates]

    # Collect all commodity names
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

    # Build commodity records
    commodities = []
    idx = 0

    # Vegetable commodities — full 10-market series
    for name in all_veg_names:
        cat = "Unknown"
        for c, items in CATEGORIES.items():
            if name in items:
                cat = c
                break

        # Build series: list of [10 market prices] per date
        series = []
        for _, veg, _ in all_days:
            if name in veg:
                series.append(veg[name])
            else:
                series.append([None] * 10)

        # Only include if enough data
        valid_days = sum(1 for s in series if any(p is not None for p in s))
        if valid_days < 1:
            continue

        # Latest prices per market
        latest = series[-1] if series else [None] * 10
        market_prices = {}
        for i, m in enumerate(MARKETS):
            p = latest[i] if i < len(latest) else None
            market_prices[m] = p

        # Primary market = first market with data
        primary = "Peliyagoda"
        for m in MARKETS:
            if market_prices.get(m) is not None:
                primary = m
                break

        commodities.append({
            "id": idx,
            "name": name,
            "category": cat,
            "unit": "Rs./kg",
            "primaryMarket": primary,
            "markets": market_prices,
            # Latest midpoints per market for the series
            "series": [midpoint(s[0]) if s and s[0] else None for s in series],
        })
        idx += 1

    # Rice/Essentials — Pettah only
    for name in all_rice_names:
        cat = RICE_ITEMS.get(name, "Rice")
        unit = "Rs./Egg" if "Egg" in name else "Rs./kg"

        series = []
        for _, _, rice in all_days:
            if name in rice:
                r = rice[name].get("pettah_range")
                series.append(midpoint(r))
            else:
                series.append(None)

        valid = sum(1 for s in series if s is not None)
        if valid < 1:
            continue

        # Latest pettah data
        latest_rice = None
        for _, _, rice in reversed(all_days):
            if name in rice:
                latest_rice = rice[name]
                break

        pettah_range = latest_rice.get("pettah_range") if latest_rice else None
        pettah_avg = latest_rice.get("pettah_avg") if latest_rice else None

        market_prices = {"Pettah": midpoint(pettah_range)}

        commodities.append({
            "id": idx,
            "name": name,
            "category": cat,
            "unit": unit,
            "primaryMarket": "Pettah",
            "markets": market_prices,
            "series": series,
            "pettahRange": pettah_range,
            "pettahAvg": pettah_avg,
        })
        idx += 1

    # Build final JSON
    data = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": "Hector Kobbekaduwa Agrarian Research and Training Institute - Daily Wholesale Price Report",
        "dates": dates,
        "dateLabels": labels,
        "markets": MARKETS,
        "commodities": commodities
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)

    print(f"\n✅ Wrote {out}")
    print(f"   {len(commodities)} commodities")
    print(f"   {len(dates)} dates ({dates[0]} to {dates[-1]})")


if __name__ == "__main__":
    if "--no-download" not in sys.argv:
        discover_and_download()
    build()
