#!/usr/bin/env python3
"""
Backfill historical data for the Sri Lanka Food Price Monitor.

It walks back through the CBSL listing pages, downloads every report PDF
within the date range you ask for, then rebuilds data.json so your charts
launch with real history instead of starting from zero.

Usage:
    python backfill.py                      # default: the last 365 days
    python backfill.py 2025-06-01 2026-05-29   # a specific start and end date

After it finishes, commit the updated data.json (and the pdfs/ folder).
The daily update.py then carries on from there automatically.
"""

import os, re, sys, datetime
import requests
import update   # reuse parsing + build() from update.py

BASE = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report"
LINK_RE = re.compile(r"https://[^\s\"']+price_report_\d{8}_e[^\s\"']*\.pdf")


def date_of(url):
    d = re.search(r"(\d{8})", url).group(1)
    return datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))


def links_on_page(page):
    url = BASE if page == 0 else f"{BASE}?page={page}"
    try:
        html = requests.get(url, headers=update.HEADERS, timeout=30).text
    except Exception as e:
        print(f"  WARN: could not read listing page {page}: {e}")
        return set()
    return set(LINK_RE.findall(html))


def backfill(start, end, max_pages=400):
    start = datetime.date.fromisoformat(start)
    end = datetime.date.fromisoformat(end)
    os.makedirs(update.PDF_DIR, exist_ok=True)
    print(f"Backfilling {start} to {end} ...")

    got = 0
    for page in range(max_pages):
        links = links_on_page(page)
        if not links:
            break
        page_dates = [date_of(u) for u in links]
        for u in links:
            d = date_of(u)
            if start <= d <= end:
                path = os.path.join(update.PDF_DIR, u.split("/")[-1])
                if os.path.exists(path):
                    continue
                try:
                    r = requests.get(u, headers=update.HEADERS, timeout=60)
                    r.raise_for_status()
                    with open(path, "wb") as f:
                        f.write(r.content)
                    got += 1
                    print("  downloaded", u.split("/")[-1])
                except Exception as e:
                    print("  WARN: failed", u.split("/")[-1], e)
        # once a page's oldest report predates our start date, we're done
        if min(page_dates) < start:
            break

    print(f"Downloaded {got} new report(s). Rebuilding data.json ...")
    update.build()


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        start, end = sys.argv[1], sys.argv[2]
    else:
        today = datetime.date.today()
        start = (today - datetime.timedelta(days=365)).isoformat()
        end = today.isoformat()
    backfill(start, end)
