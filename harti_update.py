#!/usr/bin/env python3
"""
Daily updater for HARTI Wholesale Price data.
Only downloads last 3 years (2023-2026) to keep it fast!
https://www.harti.gov.lk/daily-price.php
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
HEADERS     = {"User-Agent": "Mozilla/5.0 (Lanka Price Monitor; topgoviya.lk)"}

# ── 3 year limit ──
CUTOFF_YEAR = datetime.date.today().year - 3  # 2023

# ── 10 wholesale markets ──
MARKETS = [
    "Peliyagoda","Kandy","Dambulla","Meegoda",
    "Norochchole","Thambuththegama","Keppetipola",
    "Nuwaraeliya","Bandarawela","Veyangoda"
]

CATEGORIES = {
    "Up Country Vegetables": [
        "Beans","Carrot","Leeks","Beetroot","Beetroot (N.Eliya)",
        "Knolkhol","Raddish","Cabbage (N.Eliya)","Cabbage (Kandy)","Tomato"
    ],
    "Low Country Vegetables": [
        "Ladies Fingers","Brinjals","Capsicum","Pumpkin","Cucumber",
        "Bitter Gourd","Snake Gourd","Drumstick","Luffa","Long Beans",
        "Ash Plantains","Green Chillies","Lime","Sweet Potato","Manioc","Eggplant"
    ],
    "Potatoes & Onions": [
        "Potato (Imported)","Potato (Welimada)","Potato (N.Eliya)","Big Onion (Imported)"
    ],
    "Fruits & Banana": [
        "Banana Ambul","Banana Kolikuttu","Banana Seeni","Papaya","Pineapple (Large)","Avocado"
    ]
}

RICE_CAT = {
    "Samba 1":"Rice","Samba 2":"Rice","Keeri Samba":"Rice",
    "Nadu 1":"Rice","Nadu 2":"Rice","Raw Red":"Rice","Raw White":"Rice",
    "Green Gram":"Pulses & Essentials","Cowpea":"Pulses & Essentials",
    "Red Dhal":"Pulses & Essentials","Dried Chillies (Imp)":"Pulses & Essentials",
    "Sugar (White)":"Pulses & Essentials","Wheat Flour":"Pulses & Essentials",
    "Eggs (Brown)":"Eggs","Eggs (White)":"Eggs",
}

# ── Name mapping PDF text → standard ──
VEG_NAMES = {
    "Beans":"Beans","Carrot":"Carrot","Leeks":"Leeks",
    "Beet root":"Beetroot","Beet root (N Eliya)":"Beetroot (N.Eliya)",
    "Beet root (N.Eliya)":"Beetroot (N.Eliya)",
    "Knolkhol":"Knolkhol","Raddish":"Raddish",
    "Cabbage (N'Eliya)":"Cabbage (N.Eliya)","Cabbage (Kandy)":"Cabbage (Kandy)",
    "Tomato":"Tomato","Ladies Fingers":"Ladies Fingers",
    "Brinjals":"Brinjals","Capsicum":"Capsicum","Pumpkin":"Pumpkin",
    "Cucumber":"Cucumber","Bitter Gourd":"Bitter Gourd",
    "Snake Gourd":"Snake Gourd","Drumstick":"Drumstick",
    "Luffa":"Luffa","Long Beans":"Long Beans",
    "Ash Plantains":"Ash Plantains","Green Chillies":"Green Chillies",
    "Lime":"Lime","Sweet Potatoe":"Sweet Potato","Sweet Potato":"Sweet Potato",
    "Manioc":"Manioc","Eggplant":"Eggplant",
    "Potato(Imported)":"Potato (Imported)","Potato (Imported)":"Potato (Imported)",
    "Potato (Welimada)":"Potato (Welimada)",
    "Potato (Nuwaraeliya)":"Potato (N.Eliya)",
    "B'Onion Imported":"Big Onion (Imported)",
    "Ambul(Rs/Kg)":"Banana Ambul","Kolikuttu":"Banana Kolikuttu",
    "Seeni":"Banana Seeni","Papaya (Rs/Kg)":"Papaya",
    "Pineapple - Large":"Pineapple (Large)","Avocado":"Avocado",
}


def parse_range(text):
    if not text: return None
    text = str(text).strip()
    if text in ("-","","-"): return None
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
    if m:
        lo,hi = int(m.group(1)),int(m.group(2))
        if lo == 0 or hi == 0: return None  # skip bad 0-250 ranges
        return {"min":lo,"max":hi,"mid":round((lo+hi)/2)}
    nums = re.findall(r'\d+',text)
    if nums:
        v = int(nums[0])
        if v == 0: return None
        return {"min":v,"max":v,"mid":v}
    return None

def mid(r): return r["mid"] if r else None

def date_from_filename(path):
    fname = os.path.basename(path)
    # (2026.06.16) format
    m = re.search(r"[\(\s_]?(20\d{2})\.(\d{2})\.(\d{2})[\)\s_]?",fname)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # daily_15-01-2026 format
    m = re.search(r"daily[_\s](\d{2})-(\d{2})-(\d{4})",fname)
    if m: return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    # 2026_06_16 or 2026-06-16
    m = re.search(r"(20\d{2})[_-](\d{2})[_-](\d{2})",fname)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None

def is_within_3_years(url):
    """Check if URL contains a year >= CUTOFF_YEAR"""
    years = re.findall(r'20(\d{2})', url)
    for y in years:
        if int("20"+y) >= CUTOFF_YEAR:
            return True
    return False


def discover_and_download():
    os.makedirs(PDF_DIR, exist_ok=True)
    print(f"Fetching PDF list from HARTI website...")
    print(f"Only downloading from year {CUTOFF_YEAR} onwards (3 year limit)")

    try:
        resp = requests.get(LISTING_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"WARN: Could not fetch HARTI page: {e}")
        return

    # Extract PDF links
    pdf_links = re.findall(
        r'href=["\']([^"\']*assets/pdf/food_price/daily/eng/[^"\']*\.pdf)["\']',
        html, re.IGNORECASE
    )
    pdf_links += re.findall(
        r'https://www\.harti\.gov\.lk/assets/pdf/food_price/daily/eng/[^\s"\'<>]+\.pdf',
        html, re.IGNORECASE
    )

    full_urls = set()
    for link in pdf_links:
        url = link if link.startswith("http") else urljoin(BASE_URL, link)
        # ── 3 YEAR FILTER ──
        if is_within_3_years(url):
            full_urls.add(url)

    print(f"Found {len(full_urls)} PDFs within 3 year range.")

    downloaded = skipped = failed = 0
    for url in sorted(full_urls):
        decoded  = unquote(url.split("/")[-1])
        safe     = re.sub(r'[^\w\s\-\.]','_',decoded).strip()
        safe     = re.sub(r'\s+','_',safe)
        if not safe.endswith('.pdf'): safe += '.pdf'
        path = os.path.join(PDF_DIR, safe)

        if os.path.exists(path):
            skipped += 1
            continue

        try:
            enc_url = quote(url, safe=':/?=&%#')
            r = requests.get(enc_url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            if len(r.content) < 1000 or not r.content.startswith(b'%PDF'):
                failed += 1
                continue
            with open(path,"wb") as f: f.write(r.content)
            downloaded += 1
            if downloaded % 10 == 0:
                print(f"  Downloaded {downloaded} new PDFs so far...")
        except Exception as e:
            failed += 1

    print(f"✅ Download done: {downloaded} new, {skipped} skipped, {failed} failed")


def parse_veg_table(pdf_page):
    """
    Parse vegetable page using pdfplumber table extraction.
    Returns {name: [range×10]}
    """
    results = {}
    try:
        tables = pdf_page.extract_tables()
        for table in tables:
            if not table or len(table) < 5: continue
            for row in table:
                if not row or not row[0]: continue
                raw_name = str(row[0]).strip()
                # Match commodity name
                std = None
                for pdf_n, std_n in sorted(VEG_NAMES.items(), key=lambda x: len(x[0]), reverse=True):
                    if raw_name.startswith(pdf_n):
                        std = std_n
                        break
                if not std: continue

                # Extract 10 market prices from columns
                market_prices = []
                data_cols = [c for c in row[1:] if c is not None]
                for col in data_cols[:10]:
                    market_prices.append(parse_range(str(col).strip()))
                while len(market_prices) < 10:
                    market_prices.append(None)
                market_prices = market_prices[:10]

                if any(p is not None for p in market_prices):
                    results[std] = market_prices
    except Exception as e:
        pass

    # Fallback: text parsing if table extraction failed
    if not results:
        results = parse_veg_text(pdf_page.extract_text() or "")
    return results


def parse_veg_text(text):
    """Fallback text parser for vegetable page."""
    results = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        if any(h in line for h in ["Up Country","Low Country","Banana","Other Fruits",
            "Variety","Market","Hector","Data Management","Note","Usually","Wholesale",
            "Peliyagoda","Kandy","Dambulla","Meegoda","Keppetipola","Nuwaraeliya"]):
            continue
        std = None
        rest = line
        for pdf_n in sorted(VEG_NAMES.keys(), key=len, reverse=True):
            if line.startswith(pdf_n):
                std = VEG_NAMES[pdf_n]
                rest = line[len(pdf_n):].strip()
                break
        if not std: continue

        # Split by 2+ spaces
        parts = re.split(r'\s{2,}', rest)
        mkt_prices = []
        for p in parts:
            p = p.strip()
            mkt_prices.append(None if (not p or p=="-") else parse_range(p))

        while len(mkt_prices) < 10: mkt_prices.append(None)
        mkt_prices = mkt_prices[:10]
        if any(p is not None for p in mkt_prices):
            results[std] = mkt_prices
    return results


def parse_rice_table(pdf_page):
    """Parse rice/essentials page using table extraction."""
    results = {}
    RICE_NAMES = {
        "Samba 1":"Samba 1","Samba 2":"Samba 2","Keeri Samba":"Keeri Samba",
        "Nadu 1":"Nadu 1","Nadu 2":"Nadu 2",
        "Raw red":"Raw Red","Raw White":"Raw White",
        "Green Gram":"Green Gram","Cowpea":"Cowpea","Red Dhal":"Red Dhal",
        "Sugar(White)":"Sugar (White)","Wheat Flour":"Wheat Flour",
        "Brown":"Eggs (Brown)","White":"Eggs (White)",
    }
    try:
        tables = pdf_page.extract_tables()
        in_dried = in_eggs = False
        for table in tables:
            if not table: continue
            for row in table:
                if not row or not row[0]: continue
                raw = str(row[0]).strip()
                if "Dried Chillies" in raw: in_dried = True; continue
                if "Eggs" in raw and "Rs" not in raw: in_eggs = True; continue
                if any(h in raw for h in ["Rice","Subsidiary","Onion","Potatoes","Pulses","Consumption"]):
                    in_dried = False
                    if "Eggs" not in raw: in_eggs = False

                std = None
                for pdf_n, std_n in RICE_NAMES.items():
                    if raw.startswith(pdf_n):
                        std = std_n
                        break
                if not std and in_dried and raw.startswith("Imported"):
                    std = "Dried Chillies (Imp)"
                if not std and in_eggs:
                    for pdf_n, std_n in [("Brown","Eggs (Brown)"),("White","Eggs (White)")]:
                        if raw.startswith(pdf_n): std = std_n; break
                if not std: continue

                # Get range and average from columns
                nums = []
                for col in row[1:]:
                    if col:
                        n = re.findall(r'\d+\.?\d*', str(col))
                        nums.extend(n)

                if len(nums) >= 2:
                    try:
                        lo,hi = float(nums[0]),float(nums[1])
                        if lo > 0 and hi > 0:
                            r = {"min":int(lo),"max":int(hi),"mid":round((lo+hi)/2)}
                            avg = float(nums[2]) if len(nums) > 2 else mid(r)
                            results[std] = {"pettah_range":r,"pettah_avg":avg}
                    except: pass
    except Exception as e:
        pass
    return results


def parse_pdf(path):
    date_str = date_from_filename(path)
    if not date_str: return None,{},{}

    # Skip if outside 3 year range
    try:
        y = int(date_str[:4])
        if y < CUTOFF_YEAR:
            return None,{},{}
    except: pass

    veg_data = rice_data = {}
    try:
        with pdfplumber.open(path) as pdf:
            n = len(pdf.pages)
            if n >= 1:
                rice_data = parse_rice_table(pdf.pages[0])
            if n >= 2:
                veg_data = parse_veg_table(pdf.pages[1])
            if not veg_data and n >= 1:
                veg_data = parse_veg_table(pdf.pages[0])
    except Exception as e:
        return date_str,{},{}

    print(f"  {date_str}: {len(veg_data)} veg, {len(rice_data)} essentials")
    return date_str, veg_data, rice_data


def build():
    files = sorted(glob.glob(os.path.join(PDF_DIR,"*.pdf")))
    if not files:
        print(f"No PDFs in {PDF_DIR}/"); return

    print(f"\nParsing {len(files)} PDFs (3 year range only)...")
    all_days = []
    seen = set()
    for f in files:
        d,v,r = parse_pdf(f)
        if d and d not in seen:
            all_days.append((d,v,r))
            seen.add(d)

    if not all_days:
        print("No valid data!"); return

    all_days.sort(key=lambda x: x[0])
    dates  = [d for d,_,_ in all_days]
    labels = []
    for d in dates:
        try: labels.append(datetime.date.fromisoformat(d).strftime("%-d %b"))
        except: labels.append(d)

    # Collect names
    all_veg   = []
    all_rice  = []
    for _,v,r in all_days:
        for n in v:
            if n not in all_veg: all_veg.append(n)
        for n in r:
            if n not in all_rice: all_rice.append(n)

    commodities = []
    idx = 0

    # Vegetable commodities
    for name in all_veg:
        cat = "Unknown"
        for c,items in CATEGORIES.items():
            if name in items: cat=c; break

        series_all = []
        for _,v,_ in all_days:
            series_all.append(v.get(name,[None]*10))

        valid = sum(1 for s in series_all if any(p is not None for p in s))
        if valid < 1: continue

        latest = series_all[-1]
        mkt_prices = {}
        for i,m in enumerate(MARKETS):
            mkt_prices[m] = latest[i] if i < len(latest) else None

        primary = next((m for m in MARKETS if mkt_prices.get(m) is not None), "Peliyagoda")

        # Series = midpoints over time for primary market
        primary_idx = MARKETS.index(primary)
        price_series = []
        for s in series_all:
            p = s[primary_idx] if primary_idx < len(s) else None
            price_series.append(mid(p))

        commodities.append({
            "id":idx,"name":name,"category":cat,"unit":"Rs./kg",
            "primaryMarket":primary,"markets":mkt_prices,"series":price_series,
        })
        idx += 1

    # Rice/Essentials
    for name in all_rice:
        cat  = RICE_CAT.get(name,"Rice")
        unit = "Rs./Egg" if "Egg" in name else "Rs./kg"

        price_series = []
        latest_data  = None
        for _,_,r in all_days:
            if name in r:
                rr = r[name].get("pettah_range")
                price_series.append(mid(rr))
                latest_data = r[name]
            else:
                price_series.append(None)

        if sum(1 for s in price_series if s is not None) < 1: continue

        pr = latest_data.get("pettah_range") if latest_data else None
        pa = latest_data.get("pettah_avg")   if latest_data else None

        commodities.append({
            "id":idx,"name":name,"category":cat,"unit":unit,
            "primaryMarket":"Pettah","markets":{"Pettah":mid(pr)},
            "series":price_series,"pettahRange":pr,"pettahAvg":pa,
        })
        idx += 1

    data = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": "Hector Kobbekaduwa Agrarian Research and Training Institute — Daily Wholesale Price Report",
        "sourceUrl": "https://www.harti.gov.lk/daily-price.php",
        "dates": dates,"dateLabels": labels,"markets": MARKETS,
        "commodities": commodities
    }

    with open(OUT_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=1,ensure_ascii=False)

    print(f"\n✅ {OUT_FILE} written!")
    print(f"   📦 {len(commodities)} commodities")
    print(f"   📅 {len(dates)} dates ({dates[0]} → {dates[-1]})")
    print(f"   🏪 {len(MARKETS)} markets")


if __name__ == "__main__":
    if "--no-download" not in sys.argv:
        discover_and_download()
    build()
