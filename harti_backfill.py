#!/usr/bin/env python3
"""
HARTI Wholesale Price Backfill Script
Downloads 2023-2026 PDFs using known URL pattern.
Run ONCE manually via GitHub Actions, then harti_update.py handles daily.

URL pattern:
  https://www.harti.gov.lk/assets/pdf/food_price/daily/eng/YYYY/MonthName/Vegetable Pricenew ex1(YYYY.MM.DD).pdf
  https://www.harti.gov.lk/assets/pdf/food_price/daily/eng/YYYY/MonthName/Vegetables Wholesale Prices (YYYY.MM.DD).pdf
"""

import os, datetime, time
from urllib.parse import quote
import requests

PDF_DIR   = "harti_pdfs"
BASE      = "https://www.harti.gov.lk/assets/pdf/food_price/daily/eng"
HEADERS   = {"User-Agent": "Mozilla/5.0 (Lanka Price Monitor; topgoviya.lk)"}

START     = datetime.date(2023, 1, 1)
END       = datetime.date.today()

# Two filename patterns HARTI uses
PATTERNS  = [
    "Vegetable Pricenew ex1({YYYY}.{MM}.{DD}).pdf",
    "Vegetables Wholesale Prices ({YYYY}.{MM}.{DD}).pdf",
    "Vegetable Price new ex1({YYYY}.{MM}.{DD}).pdf",
    "Vegetables  Wholesale Prices ({YYYY}.{MM}.{DD}).pdf",  # double space variant
]

MONTHS = {
    1:"January",2:"February",3:"March",4:"April",
    5:"May",6:"June",7:"July",8:"August",
    9:"September",10:"October",11:"November",12:"December"
}

def try_download(date):
    """Try all filename patterns for a given date. Return True if any succeeds."""
    yyyy = date.strftime("%Y")
    mm   = date.strftime("%m")
    dd   = date.strftime("%d")
    month_name = MONTHS[date.month]

    for pattern in PATTERNS:
        filename = pattern.replace("{YYYY}", yyyy).replace("{MM}", mm).replace("{DD}", dd)
        safe_filename = filename.replace(" ", "_").replace("(", "_").replace(")", "_")
        save_path = os.path.join(PDF_DIR, safe_filename)

        # Skip if already downloaded
        if os.path.exists(save_path):
            return True

        # Build URL
        url = f"{BASE}/{yyyy}/{month_name}/{filename}"
        encoded_url = quote(url, safe=":/?=&%#")

        try:
            r = requests.get(encoded_url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000 and r.content[:4] == b'%PDF':
                with open(save_path, "wb") as f:
                    f.write(r.content)
                print(f"  ✅ {date} → {filename}")
                return True
        except Exception:
            pass

    return False  # All patterns failed for this date

def main():
    os.makedirs(PDF_DIR, exist_ok=True)

    print("=" * 60)
    print("🌾 HARTI Wholesale Price Backfill")
    print(f"📅 Range: {START} → {END}")
    print("=" * 60)

    current = START
    downloaded = skipped = failed = 0
    total_days = (END - START).days + 1

    while current <= END:
        # Skip Sundays (HARTI usually no report)
        if current.weekday() == 6:
            current += datetime.timedelta(days=1)
            continue

        # Check if already have this date
        yyyy = current.strftime("%Y")
        mm   = current.strftime("%m")
        dd   = current.strftime("%d")

        # Check if any variant already saved
        already = any(
            os.path.exists(os.path.join(PDF_DIR,
                p.replace("{YYYY}",yyyy).replace("{MM}",mm).replace("{DD}",dd)
                 .replace(" ","_").replace("(","_").replace(")","_")))
            for p in PATTERNS
        )

        if already:
            skipped += 1
            current += datetime.timedelta(days=1)
            continue

        # Try downloading
        success = try_download(current)
        if success:
            downloaded += 1
            time.sleep(0.3)  # Be polite to HARTI server
        else:
            failed += 1
            # Only print failures for recent dates (old dates may not exist)
            if current >= datetime.date(2024, 1, 1):
                print(f"  ⚠️  {current} — no PDF found")

        current += datetime.timedelta(days=1)

    print("\n" + "=" * 60)
    print(f"✅ Backfill complete!")
    print(f"   📥 {downloaded} new PDFs downloaded")
    print(f"   ⏭️  {skipped} already existed")
    print(f"   ❌ {failed} dates with no PDF")
    print("=" * 60)
    print("\n🔨 Now run: python harti_update.py --no-download")
    print("   This will build harti_data.json with full history!")

if __name__ == "__main__":
    main()
