#!/usr/bin/env python3
"""
apply_dec_prices.py  -  TopGoviya.lk
Adds the manual economic-centre (DEC) prices in dec_manual_prices.json to
harti_market_history.json, which the /market/ pages are built from.

Safe by design:
  * harti_data.json, the HARTI PDFs and the HARTI robot are never touched.
  * If HARTI already reported a market on a day, that whole day stays HARTI (DEC prices skipped).
  * Every DEC day is listed under "decSource", so the pages label it "DEC", not "HARTI".
  * Bad rows (unknown item, min > max, zero) are skipped and printed, not saved.
Run:  python apply_dec_prices.py   (then python build_market_pages.py)
"""
import json, os, sys
from datetime import date

SRC_FILE  = "dec_manual_prices.json"
HIST_FILE = "harti_market_history.json"
MARKETS   = ["Peliyagoda", "Kandy", "Dambulla", "Meegoda", "Norochchole",
             "Thambuththegama", "Keppetipola", "Nuwaraeliya", "Bandarawela", "Veyangoda"]
ITEMS = {
    "Beans", "Carrot", "Leeks", "Beetroot", "Beetroot (N.Eliya)", "Knolkhol", "Raddish",
    "Cabbage (N.Eliya)", "Cabbage (Kandy)", "Tomato", "Ladies Fingers", "Brinjals", "Capsicum",
    "Pumpkin", "Cucumber", "Bitter Gourd", "Snake Gourd", "Drumstick", "Luffa", "Long Beans",
    "Ash Plantains", "Green Chillies", "Lime", "Sweet Potato", "Manioc", "Eggplant",
    "Potato (Imported)", "Potato (Welimada)", "Potato (N.Eliya)", "Big Onion (Imported)",
    "Banana Ambul", "Banana Kolikuttu", "Banana Seeni", "Anamalu", "Papaya", "Passion Fruit",
    "Pineapple (Large)", "Pineapple (Medium)", "Pineapple (Small)", "Mango (Betti)",
    "Mango (Karathakolomban)", "Woodapple", "Avocado", "Orange",
}

def main():
    if not os.path.exists(SRC_FILE):
        print(f"No {SRC_FILE} - nothing to do."); return
    src = json.load(open(SRC_FILE, encoding="utf-8"))
    hist = json.load(open(HIST_FILE, encoding="utf-8")) if os.path.exists(HIST_FILE) else {"markets": {}}
    hm  = hist.setdefault("markets", {})
    dec = hist.setdefault("decSource", {})
    today = date.today().isoformat()
    added = kept = bad = 0
    for day, markets in sorted((src.get("days") or {}).items()):
        try:
            if date.fromisoformat(day).isoformat() != day or day > today: raise ValueError
        except ValueError:
            print(f"  ❌ skipped date '{day}' (must be YYYY-MM-DD, not in the future)"); bad += 1; continue
        for m, items in (markets or {}).items():
            if m not in MARKETS:
                print(f"  ❌ {day}: unknown market '{m}'"); bad += 1; continue
            if day not in dec.get(m, []) and any(day in ser for ser in hm.get(m, {}).values()):
                kept += len(items or {}); continue          # HARTI already reported this market on this day
            for name, rng in (items or {}).items():
                ok = (name in ITEMS and isinstance(rng, list) and len(rng) == 2
                      and all(isinstance(x, (int, float)) and x > 0 for x in rng) and rng[0] <= rng[1])
                if not ok:
                    print(f"  ❌ {day} {m}: bad row {name} = {rng}"); bad += 1; continue
                ser = hm.setdefault(m, {}).setdefault(name, {})
                lo, hi = int(rng[0]), int(rng[1])
                ser[day] = [lo, hi, round((lo + hi) / 2)]
                if day not in dec.setdefault(m, []):
                    dec[m].append(day)
                added += 1
    for m in dec:
        dec[m] = sorted(set(dec[m]))
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"✅ DEC prices applied: {added} prices saved, {kept} kept as HARTI, {bad} rows skipped.")
    for m, days in dec.items():
        if days: print(f"   {m}: DEC days {', '.join(days)}")
    if bad: sys.exit(0)   # never fail the robot because of one bad row

if __name__ == "__main__":
    main()
