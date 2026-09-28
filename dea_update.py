#!/usr/bin/env python3
"""
DEA Weekly Spice Price Updater — TopGoviya.lk
Runs automatically via GitHub Actions every Monday.

Checks exagri.info/mkt/index.html for the latest URL,
fetches it if not already in dea_data.json, updates the file.
"""

import json, re, time, os, sys
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    import urllib.request, urllib.error
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable,'-m','pip','install',
                          'beautifulsoup4','--break-system-packages','-q'])
    from bs4 import BeautifulSoup
    import urllib.request, urllib.error

INDEX_URL = 'https://exagri.info/mkt/index.html'
DATA_FILE = 'dea_data.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://exagri.info/mkt/index.html',
}

TABLE_COMMODITY = {
    0:'pepper',1:'clove',2:'coffee',3:'cocoa',4:'cardamom',
    5:'nutmeg',6:'cinnamon',7:'betel',8:'arecanut',9:'other',10:'oil',
}

MONTH_MAP = {
    'January':'01','February':'02','March':'03','April':'04',
    'May':'05','June':'06','July':'07','August':'08',
    'September':'09','October':'10','November':'11','December':'12'
}

def date_str_to_iso(date_str):
    m = re.match(r'(\d{1,2})-([A-Za-z]+)-(\d{4})', date_str.strip())
    if not m: return None
    d, mon, y = m.groups()
    mo = MONTH_MAP.get(mon.capitalize())
    if not mo: return None
    return f"{y}-{mo}-{int(d):02d}"

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def get_latest_url():
    """Fetch index and find the most recent data URL."""
    html = fetch(INDEX_URL)
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        if re.search(r'/mkt/\d{4}/\d{2}-\w+-\d{4}\.html', href):
            if not href.startswith('http'):
                href = 'https://exagri.info' + href
            return href
    return None

def parse_val(s):
    s = str(s).strip().replace(',','').replace('\t','').replace('\n','').replace(' ','')
    if s in ['-','–','—','']: return None
    try: return float(s)
    except: return None

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

def main():
    # Load existing data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'source': 'Department of Export Agriculture (DEA), Sri Lanka',
            'description': "Producers' Prices (Farm Gate) of Export Agricultural Commodities",
            'frequency': 'weekly', 'generated': '', 'weeks': []
        }

    existing_dates = {w['date'] for w in data.get('weeks', [])}

    # Get latest URL from index
    print("Checking DEA index for latest update...")
    try:
        latest_url = get_latest_url()
    except Exception as e:
        print(f"❌ Could not fetch index: {e}")
        sys.exit(0)

    if not latest_url:
        print("❌ No URL found in index")
        sys.exit(0)

    # Extract date string from URL
    m = re.search(r'/(\d{2}-[A-Za-z]+-\d{4})\.html', latest_url)
    if not m:
        print(f"❌ Could not parse date from {latest_url}")
        sys.exit(0)

    date_str = m.group(1)
    iso_date = date_str_to_iso(date_str)
    print(f"Latest available: {date_str} ({iso_date})")

    if iso_date in existing_dates:
        print(f"✅ Already have {date_str} — nothing to update")
        sys.exit(0)

    # Fetch and parse
    print(f"Fetching {latest_url} ...")
    try:
        html = fetch(latest_url)
        parsed = parse_dea_html(html, date_str)
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        sys.exit(1)

    if not parsed:
        print("❌ Parse failed — page may have changed structure")
        sys.exit(1)

    data['weeks'].append(parsed)
    data['weeks'].sort(key=lambda x: x['date'])
    data['generated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Added {date_str} — total {len(data['weeks'])} weeks in dea_data.json")

if __name__ == '__main__':
    main()
