"""
Keppetipola DEC daily price-list PDF  ->  keppetipola_dec.json   (TopGoviya.lk)

The robot (GitHub Actions) runs this whenever a PDF is uploaded to the folder keppetipola_pdfs/.
It reads every PDF in that folder, takes the date PRINTED INSIDE the PDF (not the file name),
matches each product name to the master list in keppetipola_dec.json, and writes one block per day.

Safety rules:
  * A product is entered only when its name is in the NAME_TO_NO table below. Unknown names are
    left out and listed in keppetipola_pdf_report.txt (never guessed).
  * "---" (no price) is skipped.  One price (e.g. 350) is stored as min = max.
  * If the PDF looks wrong (too few products, date missing, date in the future) the robot STOPS
    and does not change keppetipola_dec.json.

Run by hand:  python keppetipola_pdf_update.py
"""
import glob
import json
import os
import re
import sys
from datetime import date

PDF_DIR = "keppetipola_pdfs"
JSON_FILE = "keppetipola_dec.json"
REPORT_FILE = "keppetipola_pdf_report.txt"
MIN_PRODUCTS = 30  # a normal sheet has ~58 rows; fewer than this means the PDF was not read properly

# PDF product name  ->  item "no" in keppetipola_dec.json
NAME_TO_NO = {
    "beans": 1,
    "beetroot": 2,
    "beetroot cut": 4,
    "brinjal": 5,
    "cabbage": 6,
    "cauliflower": 7,
    "red cabbage": 8,
    "athugowa": 9,
    "capsicum": 10,
    "carrot": 11,
    "cucumber": 12,
    "green chili": 13,
    "nookal": 14,
    "leeks": 15,
    "lettuce": 16,
    "raddish": 17,
    "tomato": 18,
    "bell pepper red": 19,
    "bell pepper green": 20,
    "bell pepper yellow": 21,
    "gherkin": 22,
    "parsleys": 23,
    "celery": 24,
    "mint leaves": 25,
    "coriander leaves": 26,
    "iceberg": 27,
    "pumpkin sri lankan": 28,
    "pumpkin malaysian": 29,
    "butternut squash": 30,
    "cooking melon": 31,
    "ridge gourd": 32,
    "lady s fingers": 33,
    "snake gourd": 34,
    "bitter gourd": 35,
    "thumbakarawila": 36,
    "thibbatu": 37,
    "thai eggplant": 38,
    "bolabatu": 39,
    "winged bean": 40,
    "yard long beans": 41,
    "drumsticks": 42,
    "ash plantain": 43,
    "plantain flower": 44,
    "ambarella": 45,
    "chaw chaw": 46,
    "lime": 47,
    "genger": 48,
    "ginger": 48,
    "nai miris": 50,
    "turmeric": 51,
    "jackfruit": 52,
    "small onions lanka": 53,
    "small onions import": 54,
    "b onion lanka": 55,
    "b onion import": 56,
    "potatoes walimada": 58,
    "potatoes import": 59,
    "kohila": 60,
    "kiriala": 61,
    "manioc": 62,
    "sweet potato": 63,
    "wild baby potato": 64,
    "onion leaves": 65,
    "mukunuwenna": 66,
    "gotukola": 67,
    "curry leaves": 68,
    "spinach": 69,
    "water spinach": 70,
    "green gram": 71,
    "cowpea": 72,
    "gram": 73,
    "dry chilies": 74,
    "banana sini": 75,
    "banana abul": 76,
    "kolikuttu": 77,
    "anamalu": 78,
    "coconut": 49,
    "tamarind": 79,
    "avocado": 80,
    "woodapple": 81,
    "pineapple": 82,
    "watermelon": 83,
    "papaya": 84,
    "mango karathakolomban": 85,
    "mango": 86,
    "cooking mango": 87,  # = Malu amba in the master list (same item, price level matches)
}


def key(name):
    """Loose name key: lower case, only letters/digits, single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def read_pdf_text(path):
    from pypdf import PdfReader
    return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)


LINE = re.compile(
    r"^\s*(\d{1,3})\s+(.+?)\s+(---|\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)\s*$"
)


def parse(text):
    """Return (date_string, rows) where rows = [(pdf_no, name, lo, hi)] ; lo/hi None when '---'."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    day = m.group(0) if m else None
    rows = []
    for line in text.splitlines():
        m = LINE.match(line)
        if not m:
            continue
        no, name, price = int(m.group(1)), m.group(2).strip(), m.group(3)
        if price == "---":
            rows.append((no, name, None, None))
            continue
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", price)]
        lo, hi = nums[0], nums[-1]
        if lo > hi:
            lo, hi = hi, lo
        rows.append((no, name, lo, hi))
    return day, rows


def clean(v):
    return int(v) if float(v) == int(v) else v


def main():
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    if not pdfs:
        print("No PDF files found in", PDF_DIR)
        return 0

    db = json.load(open(JSON_FILE, encoding="utf-8"))
    valid_no = {int(it["no"]) for it in db["items"]}
    days = db.setdefault("days", {})
    report, failed = [], False

    for path in pdfs:
        fname = os.path.basename(path)
        try:
            day, rows = parse(read_pdf_text(path))
        except Exception as ex:  # unreadable file
            report.append(f"❌ {fname}: could not read the PDF ({ex.__class__.__name__}) — skipped")
            failed = True
            continue

        if not day:
            report.append(f"❌ {fname}: no date found inside the PDF — skipped")
            failed = True
            continue
        try:
            d = date.fromisoformat(day)
        except ValueError:
            report.append(f"❌ {fname}: date '{day}' is not valid — skipped")
            failed = True
            continue
        if d > date.today():
            report.append(f"❌ {fname}: date {day} is in the future — skipped")
            failed = True
            continue
        if len(rows) < MIN_PRODUCTS:
            report.append(f"❌ {fname}: only {len(rows)} product rows read (expected ~58) — skipped, check the PDF")
            failed = True
            continue

        block, unknown, no_price = {}, [], []
        for pdf_no, name, lo, hi in rows:
            no = NAME_TO_NO.get(key(name))
            if no is None or no not in valid_no:
                unknown.append(f"#{pdf_no} {name}")
                continue
            if lo is None:
                no_price.append(name)
                continue
            block[str(no)] = [clean(lo), clean(hi)]

        note = ""
        if day not in fname:
            note = f"   (file name has a different date — used the date printed inside the PDF)"
        report.append(f"✅ {fname}: date {day}, {len(block)} prices entered, {len(no_price)} with no price (---){note}")
        if day in days:
            report.append(f"   ℹ️ {day} already existed — replaced by this PDF")

        prev_days = [x for x in days if x < day]
        if prev_days:
            prev = days[max(prev_days)]
            same = sum(1 for k, v in block.items() if prev.get(k) == v)
            if block and same >= 0.9 * len(block):
                report.append(f"   ⚠️ Almost all prices are the same as {max(prev_days)} — old sheet? Please check")
        if unknown:
            report.append("   ⚠️ Left out (name not in master list): " + "; ".join(unknown))

        days[day] = dict(sorted(block.items(), key=lambda kv: int(kv[0])))

    db["days"] = dict(sorted(days.items()))
    json.dump(db, open(JSON_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(REPORT_FILE, "w", encoding="utf-8").write("\n".join(report) + "\n")
    print("\n".join(report))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
