"""TopGoviya - Dambulla DEC data test (one request, one day).
Checks that GitHub can reach the Dambulla DEC price data and saves
the result to dec_api_test.json. Photos inside the data are thrown away;
only product id, name, category and min/max prices are kept."""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone

DAY = (os.environ.get("TEST_DATE") or "2026-10-23").strip()
URL = f"https://api.dambulladec.com/api/prices/by-date/{DAY}?page=1&limit=100"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (TopGoviya.lk price page; contact: wmrkumara.info@gmail.com)",
    "Accept": "application/json",
    "Referer": "https://dambulladec.com/",
}

result = {"tested_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
          "date": DAY, "url": URL}
try:
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        result["http_status"] = r.status
        result["size_kb"] = round(len(raw) / 1024)
    data = json.loads(raw)
    items = []
    for row in data.get("data", []):
        p = row.get("product") or {}
        items.append({
            "pid": p.get("id"),
            "name": (p.get("name") or "").strip(),
            "type": p.get("type"),
            "min": row.get("min_price"),
            "max": row.get("max_price"),
        })
    items.sort(key=lambda x: (x["type"] or "", x["name"]))
    result["pagination"] = data.get("pagination")
    result["count"] = len(items)
    result["ok"] = len(items) > 0
    result["items"] = items
except urllib.error.HTTPError as e:
    result.update(ok=False, http_status=e.code, error=str(e))
except Exception as e:
    result.update(ok=False, error=f"{type(e).__name__}: {e}")

with open("dec_api_test.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print(json.dumps({k: v for k, v in result.items() if k != "items"}, indent=1))
for it in result.get("items", [])[:10]:
    print(it)

sys.exit(0 if result.get("ok") else 1)
