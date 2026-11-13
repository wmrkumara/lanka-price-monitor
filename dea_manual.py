#!/usr/bin/env python3
"""
DEA manual week — TopGoviya.lk

The DEA website blocks the robot, so each week Rathna copies the DEA
"Producers' Prices (Farm Gate)" page text into dea_manual_week.txt and commits it.
This script reads that text, checks it carefully, and ADDS the week to
dea_data.json. It never deletes or replaces any other week.

Safe to run many times:
  - empty / example text      -> does nothing
  - week already in the file  -> does nothing
  - anything looks wrong      -> stops with a clear message, changes nothing
"""

import json, re, sys
from datetime import datetime, timezone

TXT = "dea_manual_week.txt"
DATA = "dea_data.json"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Section title lines on the DEA page, in page order -> key in dea_data.json
SECTIONS = [
    ("pepper",   lambda s: s == "PEPPER"),
    ("clove",    lambda s: s == "CLOVE"),
    ("coffee",   lambda s: s == "COFFEE"),
    ("cocoa",    lambda s: s == "COCOA"),
    ("cardamom", lambda s: s == "CARDAMOM"),
    ("nutmeg",   lambda s: s.replace(" ", "") == "NUTMEG/MACE"),
    ("cinnamon", lambda s: s == "CINNAMON"),
    ("betel",    lambda s: s == "BETEL"),
    ("arecanut", lambda s: s == "ARECANUT"),
    ("other",    lambda s: s.startswith("GORAKA, GINGER")),
    ("oil",      lambda s: s.startswith("CINNAMON BARK OIL, CINNAMON LEAF OIL")),
]

NUM = re.compile(r"^-?[\d,]+(\.\d+)?$")


def stop(msg):
    print("❌ " + msg)
    print("Nothing was changed. Check the copied DEA text and commit it again.")
    sys.exit(1)


def val(s):
    s = s.strip()
    if s in ("-", "–", "—", ""):
        return None
    if not NUM.match(s):
        raise ValueError(s)
    return float(s.replace(",", ""))


def main():
    try:
        raw = open(TXT, encoding="utf-8").read()
    except FileNotFoundError:
        print("No dea_manual_week.txt — nothing to do.")
        return

    m = re.search(r"Date of collection\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})", raw)
    if not m:
        print("No 'Date of collection' found in dea_manual_week.txt — nothing to do.")
        return
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        day = datetime(y, mo, d)
    except ValueError:
        stop(f"The date {m.group(0)} is not a real date.")
    iso = day.strftime("%Y-%m-%d")
    label = f"{d:02d}-{MONTHS[mo - 1]}-{y}"
    print(f"DEA text is for the week of {label} ({iso})")

    data = json.load(open(DATA, encoding="utf-8"))
    weeks = data.get("weeks", [])
    have = {w["date"] for w in weeks}
    if iso in have:
        print(f"✅ {label} is already in dea_data.json — nothing to do.")
        return
    if not weeks:
        stop("dea_data.json has no weeks to compare with.")
    newest = max(have)
    if iso < "2016-01-01" or (datetime.strptime(iso, "%Y-%m-%d") - datetime.strptime(newest, "%Y-%m-%d")).days > 60:
        stop(f"The date {label} looks wrong (newest week in the file is {newest}).")

    # Use the newest week as the pattern for columns and districts
    tmpl = sorted(weeks, key=lambda w: w["date"])[-1]["commodities"]

    found, cur = {}, None
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        up = s.upper()
        hit = next((k for k, test in SECTIONS if test(up)), None)
        if hit:
            if hit in found:
                stop(f"The section '{s}' appears twice in the copied text.")
            cur = hit
            found[cur] = {}
            continue
        if cur is None:
            continue
        parts = [p for p in re.split(r"\t+", s)]
        if len(parts) < 2:
            parts = s.split()
        if len(parts) < 2 or parts[0].upper() == "DISTRICT":
            continue
        try:
            nums = [val(p) for p in parts[1:]]
        except ValueError:
            continue  # a heading line, not a price row
        found[cur][parts[0].strip()] = nums

    missing = [k for k, _ in SECTIONS if k not in found]
    if missing:
        stop("These sections were not found in the copied text: " + ", ".join(missing)
             + ". Copy the whole DEA page (Ctrl+A, Ctrl+C).")

    com = {}
    for key, _ in SECTIONS:
        cols = tmpl[key]["columns"]
        rows = found[key]
        if "National" not in rows:
            stop(f"{key}: the 'National' row is missing.")
        districts = {}
        for dist, nums in rows.items():
            if len(nums) != len(cols):
                stop(f"{key} / {dist}: {len(nums)} numbers, expected {len(cols)}. "
                     "DEA may have changed this table.")
            districts[dist] = dict(zip(cols, nums))
        old = list(tmpl[key]["districts"])
        if list(districts) != old:
            print(f"   note: {key} districts differ from last week "
                  f"(now {len(districts)}, last week {len(old)})")
        com[key] = {"columns": cols, "districts": districts}
        print(f"   ✓ {key}: {len(districts)} rows")

    weeks.append({"date": iso, "date_label": label, "commodities": com})
    weeks.sort(key=lambda w: w["date"])
    data["weeks"] = weeks
    data["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    pep = com["pepper"]["districts"]["National"].get("GR-1 (Average Price)")
    print(f"✅ Added {label}. Pepper GR-1 national average: {pep}")
    print(f"Total weeks in dea_data.json: {len(weeks)}")


if __name__ == "__main__":
    main()
