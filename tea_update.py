"""
TopGoviya.lk - Sri Lanka Tea Board robot
Source: https://srilankateaboard.lk/tea-statistics/  (Category: Sub District Price)
Data: MADE TEA auction price by sub-district, Rs./kg (monthly average + cumulative average)
NOT green leaf price.

First run (no tea_price_data.json): downloads history from January 2023
(same start as CBSL, HARTI and DEA data on TopGoviya.lk).
Colombo is skipped: the Tea Board figure is not a normal per-kg price.
Later runs: re-checks the last 3 months and adds any new month.
"""
import json, os, re, sys, time, html
from datetime import datetime, timezone
import urllib.request, urllib.parse, http.cookiejar

PAGE = "https://srilankateaboard.lk/tea-statistics/"
AJAX = "https://srilankateaboard.lk/wp-admin/admin-ajax.php"
CATEGORY = "1982"            # "Sub District Price"
OUT = "tea_price_data.json"
RECHECK_MONTHS = 3
START_MONTH = "2023-01"      # keep history from here
SKIP = {"colombo", "total"}  # Colombo: unusual values in source; Total: empty row

# One clean name per sub-district. Key = source name lower-case, letters only.
# The Tea Board changed spellings in Aug 2023 and has some typos.
CLEAN = {
    "nuwaraeliya": "Nuwara Eliya",
    "ramboda": "Ramboda",
    "pundaluoya": "Pundaluoya",
    "agarapatana": "Agarapatana",
    "nanuoyalindulatalawakele": "Nanuoya-Lindula-Talawakele",
    "patanakotagala": "Patana-Kotagala",
    "hattondickoya": "Hatton-Dickoya",
    "bogawantalawa": "Bogawantalawa",
    "upcotmaskeliya": "Upcot-Maskeliya",
    "upcotmaskeliyab": "Upcot-Maskeliya",
    "watawalaginigatnorton": "Watawala-Ginigathena-Norton",
    "watawalaginigatnotron": "Watawala-Ginigathena-Norton",
    "pussellawahewaheta": "Pussellawa-Hewaheta",
    "kothmale": "Kotmale",
    "kotmale": "Kotmale",
    "gampolanawalapitiyadolosbage": "Gampola-Nawalapitiya-Dolosbage",
    "nilambehantanegalaha": "Nilambe-Hantane-Galaha",
    "kadugannawa": "Kadugannawa",
    "madulkelleknuckles": "Madulkelle-Knuckles-Rangala",
    "madulkelleknucklesranga": "Madulkelle-Knuckles-Rangala",
    "hunasgiriyamatale": "Hunasgiriya-Matale-Yakdessa",
    "hunasgiriyamataleyakdessa": "Hunasgiriya-Matale-Yakdessa",
    "balangodarakwana": "Balangoda-Rakwana",
    "udapussellawahalgranoya": "Udapussellawa-Halgranoya",
    "maturata": "Maturata",
    "koslandahaldumulla": "Koslanda-Haldumulla",
    "haputale": "Haputale",
    "bandarawelapoonagalla": "Bandarawela-Poonagalla",
    "malwattewelimada": "Malwatte-Welimada",
    "demodarahaliellabadulla": "Demodara-Haliella-Badulla",
    "ellanamunukula": "Ella-Namunukula",
    "passaralunugalla": "Passara-Lunugalla",
    "madulsima": "Madulsima",
    "deniyaya": "Deniyaya",
    "galle": "Galle",
    "kalutara": "Kalutara",
    "kegalle": "Kegalle",
    "kellanivelli": "Kelani Valley",
    "kalanyvelly": "Kelani Valley",
    "kandymatalekurunegala": "Kandy-Matale-Kurunegala",
    "matara": "Matara",
    "morawaka": "Morawaka",
    "morawake": "Morawaka",
    "ratnapura": "Ratnapura",
    "balangoda": "Balangoda",
}
UNKNOWN = set()


def clean_name(raw, seen):
    key = re.sub(r"[^a-z]", "", raw.lower())
    if key in SKIP:
        return None
    # Jan-Jul 2023 lists "Balangoda" twice: the first is Balangoda-Rakwana (mid grown)
    if key == "balangoda" and "Balangoda" not in seen and "Balangoda-Rakwana" not in seen \
            and seen and len(seen) < 25:
        return "Balangoda-Rakwana"
    if key not in CLEAN:
        UNKNOWN.add(raw)
        return re.sub(r"\s+", " ", raw).title()
    return CLEAN[key]
MAX_NORMAL_PRICE = 5000      # Rs./kg; anything above is flagged, not shown as a price

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
HEAD = {"User-Agent": "Mozilla/5.0 (TopGoviya.lk price robot)", "Referer": PAGE}


def get(url, data=None):
    for attempt in range(4):
        try:
            body = urllib.parse.urlencode(data).encode() if data else None
            h = dict(HEAD)
            if data:
                h["X-Requested-With"] = "XMLHttpRequest"
            req = urllib.request.Request(url, data=body, headers=h)
            with opener.open(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"  retry {attempt+1}: {e}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Could not reach " + url)


def get_security_code():
    page = get(PAGE)
    m = re.search(r'name="wpsecurity"\s+value="([^"]+)"', page)
    if not m:
        raise RuntimeError("wpsecurity code not found - page layout may have changed")
    return m.group(1)


def ajax(code, **extra):
    data = {"action": "ajaxteaprice", "selected_category": CATEGORY, "wpsecurity": code}
    data.update(extra)
    txt = get(AJAX, data)
    try:
        return json.loads(txt).get("htmloptions", "") or ""
    except json.JSONDecodeError:
        raise RuntimeError("Tea Board reply was not JSON: " + txt[:200])


def num(s):
    s = s.replace(",", "").strip()
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def parse_month(table_html):
    rows = re.findall(r"<tr>(.*?)</tr>", table_html, re.S)
    out = []
    for r in rows:
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(cells) < 4 or not cells[1]:
            continue
        name = clean_name(cells[1], [o["subDistrict"] for o in out])
        if not name:
            continue
        avg, cum = num(cells[2]), num(cells[3])
        if avg is None and cum is None:
            continue
        item = {"subDistrict": name, "monthlyAvg": avg, "cumAvg": cum}
        # a value far too high is a typing error at the source: blank it, keep a note
        if avg and avg > MAX_NORMAL_PRICE:
            item["monthlyAvg"] = None
            item["note"] = f"source monthly value {avg} removed (unusual)"
        if cum and cum > MAX_NORMAL_PRICE:
            item["cumAvg"] = None
            item["note"] = f"source cumulative value {cum} removed (unusual)"
        out.append(item)
    return out


def main():
    db = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            db = json.load(f)
    months_data = {m: v for m, v in db.get("months", {}).items() if m >= START_MONTH}

    code = get_security_code()
    print("Security code found")
    opts = ajax(code, req_type="teaprice_category")
    available = sorted(set(m for m in re.findall(r'value="(\d{4}-\d{2})"', opts)
                           if m >= START_MONTH))
    if not available:
        raise RuntimeError("No months listed by Tea Board")
    print(f"Using {len(available)} months: {available[0]} to {available[-1]}")

    todo = [m for m in available if m not in months_data] + available[-RECHECK_MONTHS:]
    todo = sorted(set(todo))
    print(f"Fetching {len(todo)} month(s)")

    changed = 0
    for i, m in enumerate(todo, 1):
        rows = parse_month(ajax(code, req_type="teaprice_data", selected_year=m))
        if not rows:
            print(f"  {m}: no rows (skipped)")
            continue
        if months_data.get(m) != rows:
            months_data[m] = rows
            changed += 1
        if i % 20 == 0:
            print(f"  ...{i}/{len(todo)} (progress saved)")
            save(months_data)
        time.sleep(0.7)   # be polite to the Tea Board server

    if changed == 0 and os.path.exists(OUT):
        print(f"No new tea data (latest {max(months_data)}) - file not changed")
        return
    latest = save(months_data)
    print(f"Saved {OUT}: {len(months_data)} months, latest {latest}, {changed} changed")
    if UNKNOWN:
        print("NOTE - new sub-district names (add to CLEAN list):", sorted(UNKNOWN))


def save(months_data):
    latest = max(months_data)
    db = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Sri Lanka Tea Board - Tea Statistics (Sub District Price)",
        "sourceUrl": PAGE,
        "description": "Made tea auction price by sub-district, Rs./kg. Not green leaf price.",
        "unit": "Rs./kg",
        "latestMonth": latest,
        "monthCount": len(months_data),
        "months": dict(sorted(months_data.items())),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=1)
    return latest


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
