"""TopGoviya - Dambulla DEC daily price robot.

Source: Dambulla Dedicated Economic Centre (dambulladec.com) - official daily
wholesale price list. Saves only date, product id, name, category and min/max
price to dambulla_dec.json. Photos inside the source data are thrown away.

MODE=daily    : fill any missing day in the last 7 days, re-check the newest 3 days for DEC corrections
MODE=backfill : collect older history slowly, BACKFILL_DAYS requests per run,
                with a pause between requests so the DEC server is not loaded
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

FILE = "dambulla_dec.json"
API = "https://api.dambulladec.com/api/prices/by-date/{d}?page={p}&limit=100"
LAST_ERROR = {}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (TopGoviya.lk price page; contact: wmrkumara.info@gmail.com)",
    "Accept": "application/json",
    "Referer": "https://dambulladec.com/",
}
SL = timezone(timedelta(hours=5, minutes=30))
MODE = (os.environ.get("MODE") or "daily").strip().lower()
BACKFILL_DAYS = max(1, min(60, int(os.environ.get("BACKFILL_DAYS") or 30)))
FLOOR = os.environ.get("FLOOR_DATE") or "2025-01-01"
PAUSE = 5            # seconds between requests
RECENT = 7           # days that are re-checked every run
REFRESH = 3          # newest saved days fetched again every run, to pick up corrections by the DEC
STOP_AFTER_EMPTY = 45  # backfill stops after this many empty days in a row

NOW_SL = datetime.now(SL)
STAMP = NOW_SL.strftime("%Y-%m-%d %H:%M")


def load():
    if os.path.exists(FILE):
        with open(FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "source": "Dambulla Dedicated Economic Centre (Dambulla DEC)",
        "source_url": "https://dambulladec.com/home-dailyprice",
        "unit_note": "Wholesale price range (min, max) in Rs. as published by the DEC",
        "products": {}, "days": {}, "arrived": {}, "empty_days": {}, "runs": [],
    }


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f.is_integer() else round(f, 2)


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def fetch(day):
    """Returns a list of rows, [] when the day has no prices, None on failure."""
    rows, page = [], 1
    while page <= 5:
        url = API.format(d=day, p=page)
        js, err = None, ""
        for attempt in range(3):
            try:
                js = get_json(url)
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return rows
                body = ""
                try:
                    body = e.read()[:150].decode("utf-8", "ignore")
                except Exception:
                    pass
                err = f"HTTP {e.code} {body}".strip()
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
            print(f"  {day}: attempt {attempt + 1} failed ({err})")
            time.sleep(15 * (attempt + 1))
        if js is None:
            LAST_ERROR[day] = err[:200]
            return None
        rows += js.get("data") or []
        if not (js.get("pagination") or {}).get("hasNextPage"):
            break
        page += 1
        time.sleep(PAUSE)
    return rows


def store(db, day, rows, how):
    prices = {}
    for row in rows:
        p = row.get("product") or {}
        pid = p.get("id")
        mn, mx = num(row.get("min_price")), num(row.get("max_price"))
        if pid is None or (mn is None and mx is None):
            continue
        key = str(pid)
        name = (p.get("name") or "").strip()
        typ = (p.get("type") or "").strip().lower()
        info = db["products"].setdefault(key, {"name": name, "type": typ, "first_seen": day})
        if name:
            info["name"] = name
        if typ:
            info["type"] = typ
        if day < info.get("first_seen", day):
            info["first_seen"] = day
        prices[key] = [mn, mx]
    if prices:
        db["days"][day] = prices
        db["arrived"][day] = how
        db["empty_days"].pop(day, None)
    else:
        db["empty_days"][day] = STAMP
    return len(prices)


def main():
    db = load()
    today = NOW_SL.date()
    fetched, failed, new_days = [], [], 0

    if MODE == "backfill":
        start = today - timedelta(days=RECENT + 1)
        recent_limit = (today - timedelta(days=RECENT)).isoformat()
        day, asked, empty_run = start, 0, 0
        while day.isoformat() >= FLOOR and asked < BACKFILL_DAYS:
            d = day.isoformat()
            day -= timedelta(days=1)
            if d in db["days"]:
                empty_run = 0
                continue
            if d in db["empty_days"] and d < recent_limit:
                empty_run += 1
                if empty_run >= STOP_AFTER_EMPTY:
                    print(f"Reached the start of DEC history (no prices before about {d}).")
                    db["history_start_note"] = f"No DEC prices found before about {d}"
                    break
                continue
            rows = fetch(d)
            asked += 1
            if rows is None:
                failed.append(f"{d} ({LAST_ERROR.get(d, '')})")
            else:
                n = store(db, d, rows, "backfill")
                fetched.append(f"{d}:{n}")
                new_days += 1 if n else 0
                empty_run = 0 if n else empty_run + 1
                print(f"  {d}: {n} items")
                if empty_run >= STOP_AFTER_EMPTY:
                    print(f"Reached the start of DEC history (no prices before about {d}).")
                    db["history_start_note"] = f"No DEC prices found before about {d}"
                    break
            time.sleep(PAUSE)
    else:
        suspect = db.setdefault("suspect", {})
        for i in range(RECENT + 1):
            d = (today - timedelta(days=i)).isoformat()
            saved = db["days"].get(d)
            if saved and i >= REFRESH and d not in suspect:
                continue
            rows = fetch(d)
            if rows is None:
                failed.append(f"{d} ({LAST_ERROR.get(d, '')})")
            elif saved:
                # already saved: replace only if the DEC has changed (corrected) that day's prices
                old = dict(saved)
                n = store(db, d, rows, f"robot {STAMP}")
                if n and db["days"][d] != old:
                    fetched.append(f"{d}:{n}:corrected")
                    new_days += 1
                    print(f"  {d}: corrected by the DEC ({n} items)")
                else:
                    db["days"][d] = old            # nothing new (or empty now): keep what we had
                    db["arrived"][d] = db["arrived"].get(d) or f"robot {STAMP}"
                    db["empty_days"].pop(d, None)
            else:
                n = store(db, d, rows, f"robot {STAMP}")
                fetched.append(f"{d}:{n}")
                new_days += 1 if n else 0
                print(f"  {d}: {n} items")
            # a day that is an exact copy of the previous report is probably a DEC posting mistake:
            # keep checking it every run (for the whole week) until it changes
            if db["days"].get(d):
                prev = [k for k in sorted(db["days"]) if k < d]
                pdays = db["days"][prev[-1]] if prev else {}
                cur = db["days"][d]
                same = sum(1 for k, v in cur.items() if pdays.get(k) == v)
                if len(cur) >= 30 and same >= 0.95 * len(cur):
                    suspect[d] = STAMP
                    print(f"  {d}: looks like a copy of {prev[-1]} — will re-check")
                else:
                    suspect.pop(d, None)
            time.sleep(PAUSE)

    db["days"] = dict(sorted(db["days"].items()))
    db["arrived"] = dict(sorted(db["arrived"].items()))
    db["empty_days"] = dict(sorted(db["empty_days"].items()))
    db["products"] = dict(sorted(db["products"].items(), key=lambda kv: int(kv[0])))
    db["latest_date"] = max(db["days"]) if db["days"] else None
    db["oldest_date"] = min(db["days"]) if db["days"] else None
    db["updated_sl"] = STAMP
    db["runs"] = (db.get("runs") or [])[-29:] + [
        {"at_sl": STAMP, "mode": MODE, "new_days": new_days, "checked": fetched, "failed": failed}]

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Mode {MODE}: {new_days} new day(s) with prices. "
          f"Stored days: {len(db['days'])} ({db['oldest_date']} to {db['latest_date']}).")
    if failed:
        print("FAILED days (will retry next run): " + ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
