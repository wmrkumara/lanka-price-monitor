#!/usr/bin/env python3
"""
DAILY updater for HARTI Wholesale Price data.
Downloads TODAY's PDF only — fast! (30 seconds)
For historical data use harti_backfill.py
"""

import os, re, json, glob, datetime, sys
from urllib.parse import urljoin, unquote, quote
import requests
import pdfplumber

LISTING_URL = "https://www.harti.gov.lk/daily-price.php"
BASE_URL    = "https://www.harti.gov.lk/"
PDF_DIR     = "harti_pdfs"
OUT_FILE    = "harti_data.json"
HEADERS     = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.harti.gov.lk/",
}

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
        "Banana Ambul","Banana Kolikuttu","Banana Seeni","Anamalu","Papaya",
        "Passion Fruit","Pineapple (Large)","Pineapple (Medium)","Pineapple (Small)",
        "Mango (Betti)","Mango (Karathakolomban)","Woodapple","Avocado","Orange"
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
    "Seeni":"Banana Seeni","Anamalu (Rs/Fruits)":"Anamalu",
    "Papaya (Rs/Kg)":"Papaya","Passion Fruits(Rs/Fruit":"Passion Fruit",
    "Pineapple - Large":"Pineapple (Large)","Mango - Betti":"Mango (Betti)",
    "Woodapple":"Woodapple","Avocado":"Avocado","Orange":"Orange",
}

# Some fruit rows wrap onto continuation lines that repeat just a dash
# (e.g. "Pineapple - Large" is followed by "- Medium", "- Small").
# This maps a parent row's raw text to the ordered list of sub-item
# names that should be assigned to the following dash-only rows.
FRUIT_SUBITEMS = {
    "Pineapple - Large": ["Pineapple (Medium)", "Pineapple (Small)"],
    "Mango - Betti": ["Mango (Karathakolomban)"],
}

def clean_price_cell(s):
    """Strip stray letters/parentheses that sometimes visually overlap
    wrapped fruit labels during PDF text extraction (e.g. a wrapped
    'Karathakolomban' bleeding into the price column)."""
    return re.sub(r'[A-Za-z()]', '', s)

def parse_range(text):
    if not text: return None
    text = str(text).strip()
    if text in ("-",""): return None
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
    if m:
        lo,hi = int(m.group(1)),int(m.group(2))
        if lo==0 or hi==0: return None
        return {"min":lo,"max":hi,"mid":round((lo+hi)/2)}
    nums = re.findall(r'\d+',text)
    if nums:
        v = int(nums[0])
        if v==0: return None
        return {"min":v,"max":v,"mid":v}
    return None

def mid(r): return r["mid"] if r else None

def date_from_filename(path):
    fname = os.path.basename(path)
    m = re.search(r"[\(\s_]?(20\d{2})\.(\d{2})\.(\d{2})[\)\s_]?",fname)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"daily[_\s](\d{2})-(\d{2})-(\d{4})",fname)
    if m: return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.search(r"(20\d{2})[_-](\d{2})[_-](\d{2})",fname)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None

def download_today():
    """Download ONLY today's PDF — fast!"""
    os.makedirs(PDF_DIR, exist_ok=True)
    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"📥 Downloading today's PDF ({today})...")

    try:
        resp = requests.get(LISTING_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"WARN: {e}"); return

    pdf_links = re.findall(
        r'href=["\']([^"\']*assets/pdf/food_price/daily/eng/[^"\']*\.pdf)["\']',
        html, re.IGNORECASE
    )

    today_str = datetime.date.today().strftime("%Y.%m.%d")
    today_links = [l for l in pdf_links if today_str in l or
                   datetime.date.today().strftime("%Y-%m-%d") in l]

    if not today_links:
        # Try yesterday (weekend/holiday)
        yesterday = (datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y.%m.%d")
        today_links = [l for l in pdf_links if yesterday in l]
        if today_links:
            print(f"  Using yesterday's data ({yesterday})")

    if not today_links:
        print("  No new PDF found today — using existing data")
        return

    for link in today_links[:2]:  # max 2 files per day
        url  = link if link.startswith("http") else urljoin(BASE_URL, link)
        dec  = unquote(url.split("/")[-1])
        safe = re.sub(r'[^\w\s\-\.]','_',dec).strip()
        safe = re.sub(r'\s+','_',safe)
        if not safe.endswith('.pdf'): safe += '.pdf'
        path = os.path.join(PDF_DIR, safe)

        if os.path.exists(path):
            print(f"  Already downloaded: {safe}")
            continue
        try:
            r = requests.get(quote(url,safe=':/?=&%#'), headers=HEADERS, timeout=60)
            r.raise_for_status()
            if r.content.startswith(b'%PDF'):
                with open(path,"wb") as f: f.write(r.content)
                print(f"  ✅ Downloaded: {safe}")
        except Exception as e:
            print(f"  ❌ {e}")

def parse_veg_table(pdf_page):
    results = {}
    try:
        tables = pdf_page.extract_tables()
        for table in tables:
            if not table or len(table) < 5: continue
            pending_subitems = []
            for row in table:
                if not row or not row[0]: continue
                raw = str(row[0]).strip()
                std = None
                for pdf_n,std_n in sorted(VEG_NAMES.items(),key=lambda x:len(x[0]),reverse=True):
                    if raw.startswith(pdf_n): std=std_n; break
                if not std and raw.startswith("-") and pending_subitems:
                    std = pending_subitems.pop(0)
                if raw in FRUIT_SUBITEMS:
                    pending_subitems = list(FRUIT_SUBITEMS[raw])
                if not std: continue
                mkt = []
                for col in [c for c in row[1:] if c is not None][:10]:
                    mkt.append(parse_range(clean_price_cell(str(col).strip())))
                while len(mkt)<10: mkt.append(None)
                if any(p is not None for p in mkt):
                    results[std] = mkt[:10]
    except: pass
    if not results:
        txt = pdf_page.extract_text() or ""
        for line in [l.strip() for l in txt.split("\n") if l.strip()]:
            if any(h in line for h in ["Up Country","Low Country","Banana","Hector","Note","Market","Peliyagoda"]): continue
            std=None; rest=line
            for pdf_n in sorted(VEG_NAMES.keys(),key=len,reverse=True):
                if line.startswith(pdf_n): std=VEG_NAMES[pdf_n]; rest=line[len(pdf_n):].strip(); break
            if not std: continue
            parts=re.split(r'\s{2,}',rest)
            mkt=[None if(not p.strip() or p.strip()=="-")else parse_range(p) for p in parts]
            while len(mkt)<10: mkt.append(None)
            if any(p is not None for p in mkt): results[std]=mkt[:10]
    return results

def parse_rice_table(pdf_page):
    results={}
    RICE_N={"Samba 1":"Samba 1","Samba 2":"Samba 2","Keeri Samba":"Keeri Samba",
             "Nadu 1":"Nadu 1","Nadu 2":"Nadu 2","Raw red":"Raw Red","Raw White":"Raw White",
             "Green Gram":"Green Gram","Cowpea":"Cowpea","Red Dhal":"Red Dhal",
             "Sugar(White)":"Sugar (White)","Wheat Flour":"Wheat Flour",
             "Brown":"Eggs (Brown)","White":"Eggs (White)"}
    try:
        in_dried=in_eggs=False
        for table in (pdf_page.extract_tables() or []):
            for row in (table or []):
                if not row or not row[0]: continue
                raw=str(row[0]).strip()
                if "Dried Chillies" in raw: in_dried=True; continue
                if "Eggs" in raw and "Rs" not in raw: in_eggs=True; continue
                std=None
                for pdf_n,std_n in RICE_N.items():
                    if raw.startswith(pdf_n): std=std_n; break
                if not std and in_dried and raw.startswith("Imported"):
                    std="Dried Chillies (Imp)"; in_dried=False
                if not std and in_eggs:
                    for pdf_n,std_n in [("Brown","Eggs (Brown)"),("White","Eggs (White)")]:
                        if raw.startswith(pdf_n): std=std_n; break
                if not std: continue
                nums=[]
                for col in row[1:]:
                    if col: nums.extend(re.findall(r'\d+\.?\d*',str(col)))
                if len(nums)>=2:
                    try:
                        lo,hi=float(nums[0]),float(nums[1])
                        if lo>0 and hi>0:
                            r={"min":int(lo),"max":int(hi),"mid":round((lo+hi)/2)}
                            avg=float(nums[2]) if len(nums)>2 else mid(r)
                            results[std]={"pettah_range":r,"pettah_avg":avg}
                    except: pass
    except: pass
    return results

def parse_pdf(path):
    date_str=date_from_filename(path)
    if not date_str: return None,{},{}
    veg=rice={}
    try:
        with pdfplumber.open(path) as pdf:
            n=len(pdf.pages)
            if n>=1: rice=parse_rice_table(pdf.pages[0])
            if n>=2: veg=parse_veg_table(pdf.pages[1])
            if not veg and n>=1: veg=parse_veg_table(pdf.pages[0])
    except: return date_str,{},{}
    print(f"  {date_str}: {len(veg)} veg, {len(rice)} essentials")
    return date_str,veg,rice

def build():
    """Smart incremental build — only parse NEW PDFs, merge with existing data."""
    files = sorted(glob.glob(os.path.join(PDF_DIR,"*.pdf")))
    if not files: print(f"No PDFs in {PDF_DIR}/"); return

    # ── Load existing harti_data.json ──
    existing_dates = set()
    existing_data = None
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_dates = set(existing_data.get("dates", []))
            print(f"📂 Existing data: {len(existing_dates)} dates")
        except Exception as e:
            print(f"WARN: Could not load existing data: {e}")

    # ── Find only NEW PDFs not already in data ──
    new_files = []
    for f in files:
        d = date_from_filename(f)
        if d and d not in existing_dates:
            new_files.append(f)

    print(f"📥 New PDFs to parse: {len(new_files)}")

    if not new_files and existing_data:
        print("✅ No new data — harti_data.json is up to date!")
        return

    # ── Parse only new PDFs ──
    new_days = []; seen = set()
    for f in new_files:
        d,v,r = parse_pdf(f)
        if d and d not in seen:
            new_days.append((d,v,r)); seen.add(d)

    if not new_days and existing_data:
        print("✅ No new valid data parsed.")
        return

    # ── Merge new data with existing ──
    if existing_data:
        # Build dict of existing days from existing_data
        existing_days_map = {}
        ex_dates = existing_data.get("dates", [])
        ex_comms = existing_data.get("commodities", [])
        # Reconstruct day data from existing JSON using actual per-day series values
        for i, date_str in enumerate(ex_dates):
            veg = {}; rice = {}
            for comm in ex_comms:
                series = comm.get("series", [])
                if i < len(series) and series[i] is not None:
                    mid_val = series[i]  # actual per-day mid price
                    if comm.get("primaryMarket") == "Pettah":
                        rice[comm["name"]] = {
                            "pettah_range": {"min": mid_val, "max": mid_val, "mid": mid_val},
                            "pettah_avg": mid_val
                        }
                    else:
                        primary = comm.get("primaryMarket", MARKETS[0])
                        prices = [None] * len(MARKETS)
                        if primary in MARKETS:
                            prices[MARKETS.index(primary)] = {"min": mid_val, "max": mid_val, "mid": mid_val}
                        veg[comm["name"]] = prices
            existing_days_map[date_str] = (veg, rice)

        # Combine existing + new
        all_days_map = dict(existing_days_map)
        for d,v,r in new_days:
            all_days_map[d] = (v, r)

        all_days = sorted([(d,v,r) for d,(v,r) in all_days_map.items()], key=lambda x: x[0])
    else:
        # No existing data — parse ALL files
        print("⚠️ No existing data — parsing ALL PDFs (first run)...")
        all_days_new = []; seen2 = set()
        for f in files:
            d,v,r = parse_pdf(f)
            if d and d not in seen2:
                all_days_new.append((d,v,r)); seen2.add(d)
        all_days = sorted(all_days_new, key=lambda x: x[0])

    if not all_days: print("No valid data!"); return

    dates = [d for d,_,_ in all_days]
    labels = []
    for d in dates:
        try: labels.append(datetime.date.fromisoformat(d).strftime("%-d %b"))
        except: labels.append(d)

    # ── Collect commodity names ──
    all_veg=[]; all_rice=[]
    for _,v,r in all_days:
        for n in v:
            if n not in all_veg: all_veg.append(n)
        for n in r:
            if n not in all_rice: all_rice.append(n)

    commodities=[]; idx=0

    for name in all_veg:
        cat="Unknown"
        for c,items in CATEGORIES.items():
            if name in items: cat=c; break
        series_all=[v.get(name,[None]*10) for _,v,_ in all_days]
        if sum(1 for s in series_all if any(p is not None for p in s))<1: continue
        latest=series_all[-1]
        mkt_p={MARKETS[i]:latest[i] if i<len(latest) else None for i in range(len(MARKETS))}
        primary=next((m for m in MARKETS if mkt_p.get(m) is not None),"Peliyagoda")
        pi=MARKETS.index(primary)
        series=[mid(s[pi]) if pi<len(s) else None for s in series_all]
        commodities.append({"id":idx,"name":name,"category":cat,"unit":"Rs./kg",
            "primaryMarket":primary,"markets":mkt_p,"series":series})
        idx+=1

    for name in all_rice:
        cat=RICE_CAT.get(name,"Rice")
        unit="Rs./Egg" if "Egg" in name else "Rs./kg"
        series=[]; ld=None
        for _,_,r in all_days:
            if name in r: series.append(mid(r[name].get("pettah_range"))); ld=r[name]
            else: series.append(None)
        if sum(1 for s in series if s is not None)<1: continue
        pr=ld.get("pettah_range") if ld else None
        pa=ld.get("pettah_avg") if ld else None
        commodities.append({"id":idx,"name":name,"category":cat,"unit":unit,
            "primaryMarket":"Pettah","markets":{"Pettah":mid(pr)},
            "series":series,"pettahRange":pr,"pettahAvg":pa})
        idx+=1

    data={"generated":datetime.datetime.now().isoformat(timespec="seconds"),
          "source":"Hector Kobbekaduwa Agrarian Research and Training Institute — Daily Wholesale Price Report",
          "sourceUrl":"https://www.harti.gov.lk/daily-price.php",
          "dates":dates,"dateLabels":labels,"markets":MARKETS,"commodities":commodities}

    with open(OUT_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=1,ensure_ascii=False)
    print(f"\n✅ {OUT_FILE} written!")
    print(f"   📦 {len(commodities)} commodities")
    print(f"   📅 {len(dates)} dates ({dates[0]} → {dates[-1]})")
    print(f"   🆕 {len(new_days)} new dates added")

if __name__=="__main__":
    if "--no-download" not in sys.argv:
        download_today()
    build()
