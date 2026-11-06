#!/usr/bin/env python3
"""
DEA Weekly Spice Price Updater — TopGoviya.lk
Runs automatically via GitHub Actions (Tue / Wed / Fri, 5 PM Sri Lanka).

Reads exagri.info/mkt/index.html, finds ALL weekly report links,
and adds every week that is not already in dea_data.json
(catch-up mode: fills gaps when DEA publishes several weeks at once).
Safe to run many times — existing weeks are skipped.
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
MAX_CATCHUP = 12   # newest weeks to check each run

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
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def get_all_urls():
    """Return list of (iso_date, date_str, url) for every weekly report on the index, newest first."""
    html = fetch(INDEX_URL)
    soup = BeautifulSoup(html, 'html.parser')
    found = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not re.search(r'/mkt/\d{4}/\d{1,2}-\w+-\d{4}\.html', href):
            continue
        if not href.startswith('http'):
            href = 'https://exagri.info' + ('' if href.startswith('/') else '/') + href
        m = re.search(r'/(\d{1,2}-[A-Za-z]+-\d{4})\.html', href)
        if not m: continue
        date_str = m.group(1)
        iso = date_str_to_iso(date_str)
        if iso and iso not in found:
            found[iso] = (iso, date_str, href)
    return sorted(found.values(), key=lambda x: x[0], reverse=True)

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
    last_have = max(existing_dates) if existing_dates else 'none'
    print(f"Latest week already in file: {last_have}")

    print("Checking DEA index for all weekly reports...")
    try:
        urls = get_all_urls()
    except Exception as e:
        print(f"❌ Could not fetch index: {e}")
        sys.exit(0)

    if not urls:
        print("❌ No report links found on index")
        sys.exit(0)

    print(f"Index lists {len(urls)} reports; newest = {urls[0][1]}")

    missing = [u for u in urls[:MAX_CATCHUP] if u[0] not in existing_dates]
    if not missing:
        print("✅ All recent weeks already in dea_data.json — nothing to update")
        sys.exit(0)

    print(f"Missing weeks to add: {', '.join(m[1] for m in missing)}")

    added, failed = [], []
    for iso, date_str, url in sorted(missing, key=lambda x: x[0]):
        print(f"Fetching {url} ...")
        try:
            html = fetch(url)
            parsed = parse_dea_html(html, date_str)
        except Exception as e:
            print(f"   ❌ Fetch failed: {e}")
            failed.append(date_str); continue
        if not parsed:
            print("   ❌ Parse failed — page layout may have changed")
            failed.append(date_str); continue
        data['weeks'].append(parsed)
        added.append(date_str)
        print(f"   ✅ Added {date_str}")
        time.sleep(2)

    if added:
        data['weeks'].sort(key=lambda x: x['date'])
        data['generated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nSUMMARY: added {len(added)} week(s): {', '.join(added) or '-'}")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print(f"Total weeks in dea_data.json: {len(data['weeks'])}")

    if failed and not added:
        sys.exit(1)

if __name__ == '__main__':
    main()
