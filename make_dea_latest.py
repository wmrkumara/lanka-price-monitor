# make_dea_latest.py
# Builds dea_ticker_data.json (a few KB) from dea_data.json (13 MB)
# so the homepage spice ticker loads fast.
# Reads dea_data.json only. Never changes it.
# Safe: if anything goes wrong it prints a message and exits without error.

import json
import sys

SRC = "dea_data.json"
OUT = "dea_ticker_data.json"

# (id, commodity group, column in DEA data, unit)
ITEMS = [
    ("pepper",    "pepper",   "GR-1 (Average Price)",                   "kg"),
    ("cinnamon",  "cinnamon", "C-5 (Average Price)",                    "kg"),
    ("clove",     "clove",    "CLOVE (Average Price)",                  "kg"),
    ("cardamom",  "cardamom", "LG (Average Price)",                     "kg"),
    ("nutmeg",    "nutmeg",   "NUTMEG No.1 (Average Price)",            "kg"),
    ("mace",      "nutmeg",   "MACE No.1 (Average Price)",              "kg"),
    ("coffee",    "coffee",   "GR 1 (Average Price)",                   "kg"),
    ("cocoa",     "cocoa",    "GR 1 (Average Price)",                   "kg"),
    ("arecanut",  "arecanut", "Dried-(Karunka)-(Rs./k.g.) (Average Price)", "kg"),
    ("goraka",    "other",    "Goraka (Average Price)",                 "kg"),
    ("ginger",    "other",    "Ginger (Average Price)",                 "kg"),
    ("turmeric",  "other",    "Turmeric (Average Price)",               "kg"),
]


def national(week, group, col):
    try:
        v = week["commodities"][group]["districts"]["National"][col]
        return round(float(v), 2) if v is not None else None
    except (KeyError, TypeError, ValueError):
        return None


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    weeks = data.get("weeks") or []
    if len(weeks) < 1:
        print("No weeks in dea_data.json - nothing to do")
        return
    latest = weeks[-1]
    prev = weeks[-2] if len(weeks) > 1 else None

    items = []
    for item_id, group, col, unit in ITEMS:
        price = national(latest, group, col)
        if price is None:
            continue  # DEA had no price this week - skip it
        grade = col.replace(" (Average Price)", "")
        if item_id == "arecanut":
            grade = "Dried"
        items.append({
            "id": item_id,
            "grade": grade,
            "price": price,
            "prev": national(prev, group, col) if prev else None,
            "unit": unit,
        })

    out = {
        "source": "Department of Export Agriculture (DEA), Sri Lanka",
        "type": "National average farm gate price (Rs.)",
        "date": latest.get("date"),
        "prev_date": prev.get("date") if prev else None,
        "items": items,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{OUT} written: {len(items)} items, week {out['date']} vs {out['prev_date']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never break the DEA robot
        print("make_dea_latest.py skipped:", e)
        sys.exit(0)
