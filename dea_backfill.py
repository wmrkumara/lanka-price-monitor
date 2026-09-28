#!/usr/bin/env python3
"""
DEA Spice Price FULL BACKFILL — 2016 to 2026
TopGoviya.lk | ebooklanka.com

Fetches 533 weekly pages from exagri.info/mkt/
Builds complete dea_data.json with 10 years of history.

Run ONCE via GitHub Actions:
  Actions → DEA Spice Backfill → Run workflow

After backfill, dea_update.py handles weekly updates automatically.
"""

import json, re, time, sys, os, argparse
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    import urllib.request
    import urllib.error
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable,'-m','pip','install',
                          'beautifulsoup4','--break-system-packages','-q'])
    from bs4 import BeautifulSoup
    import urllib.request, urllib.error

# ── Config ────────────────────────────────────────────────────
DATA_FILE  = 'dea_data.json'
DELAY_SEC  = 2.5

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://exagri.info/mkt/index.html',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
}

TABLE_COMMODITY = {
    0:'pepper', 1:'clove', 2:'coffee', 3:'cocoa', 4:'cardamom',
    5:'nutmeg', 6:'cinnamon', 7:'betel', 8:'arecanut', 9:'other', 10:'oil',
}

# ── All 533 URLs — 2016 to September 2026 ────────────────────
ALL_DATES = [
    ('2026','15-September-2026'),('2026','08-September-2026'),('2026','01-September-2026'),
    ('2026','25-August-2026'),('2026','18-August-2026'),('2026','11-August-2026'),
    ('2026','04-August-2026'),('2026','28-July-2026'),('2026','21-July-2026'),
    ('2026','14-July-2026'),('2026','07-July-2026'),('2026','30-June-2026'),
    ('2026','23-June-2026'),('2026','16-June-2026'),('2026','09-June-2026'),
    ('2026','02-June-2026'),('2026','26-May-2026'),('2026','19-May-2026'),
    ('2026','12-May-2026'),('2026','05-May-2026'),('2026','28-April-2026'),
    ('2026','21-April-2026'),('2026','07-April-2026'),('2026','31-March-2026'),
    ('2026','24-March-2026'),('2026','17-March-2026'),('2026','10-March-2026'),
    ('2026','03-March-2026'),('2026','24-February-2026'),('2026','17-February-2026'),
    ('2026','10-February-2026'),('2026','03-February-2026'),('2026','27-January-2026'),
    ('2026','20-January-2026'),('2026','13-January-2026'),('2026','06-January-2026'),
    ('2025','30-December-2025'),('2025','23-December-2025'),('2025','16-December-2025'),
    ('2025','09-December-2025'),('2025','02-December-2025'),('2025','25-November-2025'),
    ('2025','18-November-2025'),('2025','11-November-2025'),('2025','04-November-2025'),
    ('2025','28-October-2025'),('2025','21-October-2025'),('2025','14-October-2025'),
    ('2025','07-October-2025'),('2025','30-September-2025'),('2025','23-September-2025'),
    ('2025','16-September-2025'),('2025','09-September-2025'),('2025','02-September-2025'),
    ('2025','26-August-2025'),('2025','19-August-2025'),('2025','12-August-2025'),
    ('2025','05-August-2025'),('2025','29-July-2025'),('2025','22-July-2025'),
    ('2025','15-July-2025'),('2025','08-July-2025'),('2025','01-July-2025'),
    ('2025','24-June-2025'),('2025','17-June-2025'),('2025','11-June-2025'),
    ('2025','03-June-2025'),('2025','27-May-2025'),('2025','20-May-2025'),
    ('2025','14-May-2025'),('2025','07-May-2025'),('2025','29-April-2025'),
    ('2025','22-April-2025'),('2025','08-April-2025'),('2025','01-April-2025'),
    ('2025','25-March-2025'),('2025','18-March-2025'),('2025','11-March-2025'),
    ('2025','04-March-2025'),('2025','25-February-2025'),('2025','18-February-2025'),
    ('2025','11-February-2025'),('2025','05-February-2025'),('2025','28-January-2025'),
    ('2025','21-January-2025'),('2025','15-January-2025'),('2025','07-January-2025'),
    ('2024','31-December-2024'),('2024','24-December-2024'),('2024','17-December-2024'),
    ('2024','10-December-2024'),('2024','03-December-2024'),('2024','26-November-2024'),
    ('2024','19-November-2024'),('2024','12-November-2024'),('2024','05-November-2024'),
    ('2024','29-October-2024'),('2024','22-October-2024'),('2024','15-October-2024'),
    ('2024','01-October-2024'),('2024','24-September-2024'),('2024','18-September-2024'),
    ('2024','10-September-2024'),('2024','03-September-2024'),('2024','27-August-2024'),
    ('2024','20-August-2024'),('2024','13-August-2024'),('2024','06-August-2024'),
    ('2024','30-July-2024'),('2024','23-July-2024'),('2024','16-July-2024'),
    ('2024','02-July-2024'),('2024','25-June-2024'),('2024','18-June-2024'),
    ('2024','11-June-2024'),('2024','04-June-2024'),('2024','28-May-2024'),
    ('2024','21-May-2024'),('2024','14-May-2024'),('2024','07-May-2024'),
    ('2024','30-April-2024'),('2024','24-April-2024'),('2024','16-April-2024'),
    ('2024','08-April-2024'),('2024','02-April-2024'),('2024','26-March-2024'),
    ('2024','19-March-2024'),('2024','12-March-2024'),('2024','05-March-2024'),
    ('2024','27-February-2024'),('2024','20-February-2024'),('2024','13-February-2024'),
    ('2024','06-February-2024'),('2024','30-January-2024'),('2024','23-January-2024'),
    ('2024','16-January-2024'),('2024','09-January-2024'),('2024','02-January-2024'),
    ('2023','27-December-2023'),('2023','19-December-2023'),('2023','12-December-2023'),
    ('2023','05-December-2023'),('2023','28-November-2023'),('2023','21-November-2023'),
    ('2023','14-November-2023'),('2023','07-November-2023'),('2023','31-October-2023'),
    ('2023','24-October-2023'),('2023','17-October-2023'),('2023','10-October-2023'),
    ('2023','03-October-2023'),('2023','26-September-2023'),('2023','19-September-2023'),
    ('2023','12-September-2023'),('2023','05-September-2023'),('2023','28-August-2023'),
    ('2023','22-August-2023'),('2023','15-August-2023'),('2023','08-August-2023'),
    ('2023','31-July-2023'),('2023','25-July-2023'),('2023','18-July-2023'),
    ('2023','11-July-2023'),('2023','04-July-2023'),('2023','27-June-2023'),
    ('2023','20-June-2023'),('2023','13-June-2023'),('2023','06-June-2023'),
    ('2023','30-May-2023'),('2023','23-May-2023'),('2023','16-May-2023'),
    ('2023','09-May-2023'),('2023','02-May-2023'),('2023','25-April-2023'),
    ('2023','18-April-2023'),('2023','10-April-2023'),('2023','03-April-2023'),
    ('2023','28-March-2023'),('2023','21-March-2023'),('2023','14-March-2023'),
    ('2023','07-March-2023'),('2023','28-February-2023'),('2023','21-February-2023'),
    ('2023','14-February-2023'),('2023','07-February-2023'),('2023','31-January-2023'),
    ('2023','24-January-2023'),('2023','17-January-2023'),('2023','10-January-2023'),
    ('2023','03-January-2023'),
    ('2022','27-December-2022'),('2022','20-December-2022'),('2022','13-December-2022'),
    ('2022','05-December-2022'),('2022','29-November-2022'),('2022','22-November-2022'),
    ('2022','15-November-2022'),('2022','08-November-2022'),('2022','01-November-2022'),
    ('2022','25-October-2022'),('2022','18-October-2022'),('2022','11-October-2022'),
    ('2022','04-October-2022'),('2022','27-September-2022'),('2022','20-September-2022'),
    ('2022','13-September-2022'),('2022','06-September-2022'),('2022','30-August-2022'),
    ('2022','23-August-2022'),('2022','16-August-2022'),('2022','09-August-2022'),
    ('2022','02-August-2022'),('2022','26-July-2022'),('2022','19-July-2022'),
    ('2022','12-July-2022'),('2022','05-July-2022'),('2022','28-June-2022'),
    ('2022','21-June-2022'),('2022','15-June-2022'),('2022','07-June-2022'),
    ('2022','31-May-2022'),('2022','24-May-2022'),('2022','17-May-2022'),
    ('2022','04-May-2022'),('2022','26-April-2022'),('2022','19-April-2022'),
    ('2022','05-April-2022'),('2022','29-March-2022'),('2022','22-March-2022'),
    ('2022','15-March-2022'),('2022','08-March-2022'),('2022','28-February-2022'),
    ('2022','22-February-2022'),('2022','14-February-2022'),('2022','08-February-2022'),
    ('2022','01-February-2022'),('2022','25-January-2022'),('2022','18-January-2022'),
    ('2022','11-January-2022'),('2022','04-January-2022'),
    ('2021','28-December-2021'),('2021','21-December-2021'),('2021','14-December-2021'),
    ('2021','07-December-2021'),('2021','30-November-2021'),('2021','23-November-2021'),
    ('2021','16-November-2021'),('2021','09-November-2021'),('2021','02-November-2021'),
    ('2021','26-October-2021'),('2021','18-October-2021'),('2021','12-October-2021'),
    ('2021','05-October-2021'),('2021','17-August-2021'),('2021','10-August-2021'),
    ('2021','03-August-2021'),('2021','27-July-2021'),('2021','19-July-2021'),
    ('2021','13-July-2021'),('2021','06-July-2021'),('2021','29-June-2021'),
    ('2021','22-June-2021'),('2021','18-May-2021'),('2021','11-May-2021'),
    ('2021','04-May-2021'),('2021','27-April-2021'),('2021','20-April-2021'),
    ('2021','06-April-2021'),('2021','30-March-2021'),('2021','23-March-2021'),
    ('2021','16-March-2021'),('2021','09-March-2021'),('2021','02-March-2021'),
    ('2021','23-February-2021'),('2021','16-February-2021'),('2021','09-February-2021'),
    ('2021','02-February-2021'),('2021','26-January-2021'),('2021','19-January-2021'),
    ('2021','12-January-2021'),('2021','05-January-2021'),
    ('2020','28-December-2020'),('2020','22-December-2020'),('2020','15-December-2020'),
    ('2020','08-December-2020'),('2020','01-December-2020'),('2020','24-November-2020'),
    ('2020','17-November-2020'),('2020','10-November-2020'),('2020','03-November-2020'),
    ('2020','27-October-2020'),('2020','20-October-2020'),('2020','13-October-2020'),
    ('2020','06-October-2020'),('2020','29-September-2020'),('2020','22-September-2020'),
    ('2020','15-September-2020'),('2020','08-September-2020'),('2020','31-August-2020'),
    ('2020','25-August-2020'),('2020','18-August-2020'),('2020','11-August-2020'),
    ('2020','04-August-2020'),('2020','28-July-2020'),('2020','21-July-2020'),
    ('2020','14-July-2020'),('2020','07-July-2020'),('2020','30-June-2020'),
    ('2020','23-June-2020'),('2020','16-June-2020'),('2020','09-June-2020'),
    ('2020','02-June-2020'),('2020','26-May-2020'),('2020','19-May-2020'),
    ('2020','12-May-2020'),('2020','05-May-2020'),('2020','28-April-2020'),
    ('2020','21-April-2020'),('2020','10-March-2020'),('2020','03-March-2020'),
    ('2020','25-February-2020'),('2020','18-February-2020'),('2020','11-February-2020'),
    ('2020','03-February-2020'),('2020','28-January-2020'),('2020','21-January-2020'),
    ('2020','13-January-2020'),('2020','07-January-2020'),
    ('2019','31-December-2019'),('2019','23-December-2019'),('2019','17-December-2019'),
    ('2019','09-December-2019'),('2019','03-December-2019'),('2019','26-November-2019'),
    ('2019','19-November-2019'),('2019','11-November-2019'),('2019','05-November-2019'),
    ('2019','29-October-2019'),('2019','22-October-2019'),('2019','15-October-2019'),
    ('2019','08-October-2019'),('2019','01-October-2019'),('2019','24-September-2019'),
    ('2019','17-September-2019'),('2019','10-September-2019'),('2019','03-September-2019'),
    ('2019','27-August-2019'),('2019','20-August-2019'),('2019','13-August-2019'),
    ('2019','06-August-2019'),('2019','30-July-2019'),('2019','23-July-2019'),
    ('2019','15-July-2019'),('2019','09-July-2019'),('2019','02-July-2019'),
    ('2019','25-June-2019'),('2019','18-June-2019'),('2019','11-June-2019'),
    ('2019','03-June-2019'),('2019','28-May-2019'),('2019','21-May-2019'),
    ('2019','14-May-2019'),('2019','07-May-2019'),('2019','29-April-2019'),
    ('2019','23-April-2019'),('2019','09-April-2019'),('2019','02-April-2019'),
    ('2019','26-March-2019'),('2019','18-March-2019'),('2019','12-March-2019'),
    ('2019','05-March-2019'),('2019','26-February-2019'),('2019','18-February-2019'),
    ('2019','12-February-2019'),('2019','05-February-2019'),('2019','29-January-2019'),
    ('2019','22-January-2019'),('2019','14-January-2019'),('2019','08-January-2019'),
    ('2018','31-December-2018'),('2018','24-December-2018'),('2018','18-December-2018'),
    ('2018','11-December-2018'),('2018','04-December-2018'),('2018','27-November-2018'),
    ('2018','19-November-2018'),('2018','13-November-2018'),('2018','05-November-2018'),
    ('2018','30-October-2018'),('2018','22-October-2018'),('2018','16-October-2018'),
    ('2018','09-October-2018'),('2018','02-October-2018'),('2018','25-September-2018'),
    ('2018','18-September-2018'),('2018','11-September-2018'),('2018','04-September-2018'),
    ('2018','28-August-2018'),('2018','20-August-2018'),('2018','14-August-2018'),
    ('2018','07-August-2018'),('2018','31-July-2018'),('2018','24-July-2018'),
    ('2018','17-July-2018'),('2018','10-July-2018'),('2018','03-July-2018'),
    ('2018','25-June-2018'),('2018','19-June-2018'),('2018','12-June-2018'),
    ('2018','05-June-2018'),('2018','28-May-2018'),('2018','22-May-2018'),
    ('2018','15-May-2018'),('2018','08-May-2018'),('2018','01-May-2018'),
    ('2018','24-April-2018'),('2018','17-April-2018'),('2018','09-April-2018'),
    ('2018','03-April-2018'),('2018','27-March-2018'),('2018','20-March-2018'),
    ('2018','13-March-2018'),('2018','06-March-2018'),('2018','27-February-2018'),
    ('2018','20-February-2018'),('2018','12-February-2018'),('2018','06-February-2018'),
    ('2018','29-January-2018'),('2018','23-January-2018'),('2018','16-January-2018'),
    ('2018','09-January-2018'),('2018','03-January-2018'),
    ('2017','26-December-2017'),('2017','19-December-2017'),('2017','12-December-2017'),
    ('2017','05-December-2017'),('2017','28-November-2017'),('2017','21-November-2017'),
    ('2017','14-November-2017'),('2017','07-November-2017'),('2017','31-October-2017'),
    ('2017','24-October-2017'),('2017','16-October-2017'),('2017','10-October-2017'),
    ('2017','03-October-2017'),('2017','26-September-2017'),('2017','19-September-2017'),
    ('2017','12-September-2017'),('2017','04-September-2017'),('2017','29-August-2017'),
    ('2017','22-August-2017'),('2017','15-August-2017'),('2017','08-August-2017'),
    ('2017','01-August-2017'),('2017','25-July-2017'),('2017','18-July-2017'),
    ('2017','11-July-2017'),('2017','04-July-2017'),('2017','27-June-2017'),
    ('2017','20-June-2017'),('2017','13-June-2017'),('2017','06-June-2017'),
    ('2017','30-May-2017'),('2017','23-May-2017'),('2017','16-May-2017'),
    ('2017','08-May-2017'),('2017','02-May-2017'),('2017','25-April-2017'),
    ('2017','18-April-2017'),('2017','04-April-2017'),('2017','28-March-2017'),
    ('2017','21-March-2017'),('2017','14-March-2017'),('2017','07-March-2017'),
    ('2017','28-February-2017'),('2017','21-February-2017'),('2017','14-February-2017'),
    ('2017','07-February-2017'),('2017','31-January-2017'),('2017','24-January-2017'),
    ('2017','17-January-2017'),('2017','10-January-2017'),('2017','03-January-2017'),
    ('2016','27-December-2016'),('2016','20-December-2016'),('2016','14-December-2016'),
    ('2016','06-December-2016'),('2016','29-November-2016'),('2016','22-November-2016'),
    ('2016','15-November-2016'),('2016','08-November-2016'),('2016','01-November-2016'),
    ('2016','25-October-2016'),('2016','18-October-2016'),('2016','11-October-2016'),
    ('2016','04-October-2016'),('2016','27-September-2016'),('2016','20-September-2016'),
    ('2016','30-August-2016'),('2016','23-August-2016'),('2016','15-August-2016'),
    ('2016','13-August-2016'),('2016','06-August-2016'),('2016','02-August-2016'),
    ('2016','26-July-2016'),('2016','18-July-2016'),('2016','12-July-2016'),
    ('2016','04-July-2016'),('2016','28-June-2016'),('2016','21-June-2016'),
    ('2016','14-June-2016'),('2016','07-June-2016'),('2016','31-May-2016'),
    ('2016','24-May-2016'),('2016','17-May-2016'),('2016','10-May-2016'),
    ('2016','03-May-2016'),('2016','26-April-2016'),('2016','19-April-2016'),
    ('2016','05-April-2016'),('2016','29-March-2016'),('2016','21-March-2016'),
    ('2016','15-March-2016'),('2016','08-March-2016'),('2016','01-March-2016'),
    ('2016','23-February-2016'),('2016','16-February-2016'),('2016','09-February-2016'),
    ('2016','02-February-2016'),('2016','26-January-2016'),('2016','19-January-2016'),
    ('2016','12-January-2016'),('2016','05-January-2016'),
]

MONTH_MAP = {
    'January':'01','February':'02','March':'03','April':'04',
    'May':'05','June':'06','July':'07','August':'08',
    'September':'09','October':'10','November':'11','December':'12'
}

def date_str_to_iso(date_str):
    """Convert '15-September-2026' → '2026-09-15'"""
    m = re.match(r'(\d{1,2})-([A-Za-z]+)-(\d{4})', date_str.strip())
    if not m: return None
    d, mon, y = m.groups()
    mo = MONTH_MAP.get(mon.capitalize())
    if not mo: return None
    return f"{y}-{mo}-{int(d):02d}"

def parse_val(s):
    s = str(s).strip().replace(',','').replace('\t','').replace('\n','').replace(' ','')
    if s in ['-','–','—','']: return None
    try: return float(s)
    except: return None

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def parse_dea_html(html_bytes, date_str):
    soup = BeautifulSoup(html_bytes, 'html.parser')
    iso_date = date_str_to_iso(date_str)
    if not iso_date: return None
    entry = {'date': iso_date, 'date_label': date_str, 'commodities': {}}
    for i, table in enumerate(soup.find_all('table')):
        key = TABLE_COMMODITY.get(i)
        if key is None: continue
        headers = [th.get_text(separator=' ', strip=True) for th in table.find_all('th')]
        col_names = headers[1:]
        districts = {}
        for tr in table.find_all('tr')[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            if not cells: continue
            district = cells[0].strip()
            values = {col: parse_val(cells[j+1]) if j+1 < len(cells) else None
                      for j, col in enumerate(col_names)}
            districts[district] = values
        entry['commodities'][key] = {'columns': col_names, 'districts': districts}
    return entry if len(entry['commodities']) >= 5 else None

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {
        'source': 'Department of Export Agriculture (DEA), Sri Lanka',
        'description': "Producers' Prices (Farm Gate) of Export Agricultural Commodities",
        'frequency': 'weekly',
        'generated': '',
        'weeks': []
    }

def save(data):
    data['generated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data['weeks'].sort(key=lambda x: x['date'])
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-year', type=int, default=2016)
    parser.add_argument('--test', action='store_true', help='Fetch first 5 only')
    args = parser.parse_args()

    existing = load_existing()
    existing_dates = {w['date'] for w in existing.get('weeks', [])}
    print(f"Already have: {len(existing_dates)} weeks")

    # Filter to-do list
    todo = [(yr, ds) for yr, ds in ALL_DATES
            if int(yr) >= args.from_year
            and date_str_to_iso(ds) not in existing_dates]

    if args.test:
        todo = todo[:5]
        print(f"TEST MODE — fetching {len(todo)} pages")
    else:
        print(f"To fetch: {len(todo)} pages ({args.from_year}→2026)")

    added = 0
    failed = 0
    failed_list = []

    for i, (year, date_str) in enumerate(todo):
        url = f"https://exagri.info/mkt/{year}/{date_str}.html"
        iso = date_str_to_iso(date_str)
        print(f"  [{i+1}/{len(todo)}] {date_str} ... ", end='', flush=True)
        try:
            html = fetch(url)
            parsed = parse_dea_html(html, date_str)
            if parsed:
                existing['weeks'].append(parsed)
                existing_dates.add(parsed['date'])
                added += 1
                print(f"✅ ({len(parsed['commodities'])} commodities)")
            else:
                print(f"⚠️  parse failed")
                failed += 1
                failed_list.append(date_str)
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP {e.code}")
            failed += 1
            failed_list.append(date_str)
        except Exception as e:
            print(f"❌ {e}")
            failed += 1
            failed_list.append(date_str)

        # Checkpoint every 20 pages
        if added > 0 and added % 20 == 0:
            save(existing)
            print(f"  💾 Checkpoint: {len(existing['weeks'])} total weeks saved")

        if i < len(todo) - 1:
            time.sleep(DELAY_SEC)

    save(existing)
    print(f"\n{'='*55}")
    print(f"✅ DONE — {added} added, {failed} failed")
    print(f"Total in dea_data.json: {len(existing['weeks'])} weeks")
    if existing['weeks']:
        print(f"Range: {existing['weeks'][0]['date']} → {existing['weeks'][-1]['date']}")
    if failed_list:
        print(f"\nFailed dates (retry manually):")
        for d in failed_list: print(f"  {d}")

if __name__ == '__main__':
    main()
