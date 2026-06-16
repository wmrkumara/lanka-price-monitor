#!/usr/bin/env python3
"""
ONE-TIME backfill script for HARTI Wholesale Price data.
Downloads last 3 years of PDFs from HARTI website.
Run manually once, then harti_update.py handles daily updates.
"""

import os, re, datetime, sys
from urllib.parse import urljoin, unquote, quote
import requests

LISTING_URL = "https://www.harti.gov.lk/daily-price.php"
BASE_URL    = "https://www.harti.gov.lk/"
PDF_DIR     = "harti_pdfs"
HEADERS     = {"User-Agent": "Mozilla/5.0 (Lanka Price Monitor; topgoviya.lk)"}

# 3 year limit
CUTOFF_YEAR = datetime.date.today().year - 3  # 2023

def discover_and_download():
    os.makedirs(PDF_DIR, exist_ok=True)
    print(f"🔍 Fetching PDF list from HARTI...")
    print(f"📅 Downloading from {CUTOFF_YEAR} onwards (3 years)")

    try:
        resp = requests.get(LISTING_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"❌ Could not fetch HARTI page: {e}")
        return

    # Extract all PDF links
    pdf_links = re.findall(
        r'href=["\']([^"\']*assets/pdf/food_price/daily/eng/[^"\']*\.pdf)["\']',
        html, re.IGNORECASE
    )
    pdf_links += re.findall(
        r'https://www\.harti\.gov\.lk/assets/pdf/food_price/daily/eng/[^\s"\'<>]+\.pdf',
        html, re.IGNORECASE
    )

    # Build full URLs
    full_urls = set()
    for link in pdf_links:
        url = link if link.startswith("http") else urljoin(BASE_URL, link)
        # Year filter
        years = re.findall(r'20(\d{2})', url)
        for y in years:
            if int("20"+y) >= CUTOFF_YEAR:
                full_urls.add(url)
                break

    total = len(full_urls)
    print(f"📦 Found {total} PDFs within 3 year range")

    downloaded = skipped = failed = 0
    for i, url in enumerate(sorted(full_urls), 1):
        decoded = unquote(url.split("/")[-1])
        safe    = re.sub(r'[^\w\s\-\.]','_',decoded).strip()
        safe    = re.sub(r'\s+','_',safe)
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
            print(f"  [{i}/{total}] ✅ {safe}")
        except Exception as e:
            failed += 1
            print(f"  [{i}/{total}] ❌ {safe}: {e}")

    print(f"\n✅ Backfill complete!")
    print(f"   📥 {downloaded} new PDFs downloaded")
    print(f"   ⏭️  {skipped} already existed")
    print(f"   ❌ {failed} failed")

if __name__ == "__main__":
    discover_and_download()
    # After download, run harti_update.py to build JSON
    print("\n🔨 Now run: python harti_update.py --no-download")
