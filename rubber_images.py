# TopGoviya.lk - download Colombo rubber auction price images from RRISL
# Each auction has a number (nid). We count down from the newest one,
# read the auction date and save the image as rubber_imgs/YYYY-MM-DD.<ext>
# Images already saved are skipped. Stops when auctions are older than YEAR_FROM.
import os, re, ssl, time, urllib.request

BASE = "https://www.rrisl.gov.lk/"
OUT = "rubber_imgs"
YEAR_FROM = int(os.environ.get("YEAR_FROM") or "2026")
os.makedirs(OUT, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            return urllib.request.urlopen(req, timeout=60, context=ctx).read()
        except Exception as e:
            print("  retry", attempt + 1, url, e)
            time.sleep(5)
    return None

# 1) find the newest auction number from the first list page
start = 519
raw = get(BASE + "price_e.php?id=1")
if raw:
    html = raw.decode("utf-8", "ignore")
    nids = [int(n) for n in re.findall(r"nid=(\d+)", html)]
    if nids:
        start = max(nids)
    else:
        print("No auction numbers on list page - using", start)
        print("Page sample:", re.sub(r"\s+", " ", html)[:1500])
print("Newest auction number:", start)

# 2) count down, auction by auction
saved, skipped, failed, older, misses = 0, 0, [], 0, 0
for nid in range(start + 3, 0, -1):
    raw = get(f"{BASE}price_e.php?nid={nid}&id=1")
    if not raw:
        misses += 1
        if misses >= 15: break
        continue
    html = raw.decode("utf-8", "ignore")
    img = re.search(r"content/images/prices/([^\"'\s>]+)", html)
    date = None
    if img:
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", img.group(1))
        if m:
            date = "-".join(m.groups())
    if not date:
        txt = re.sub(r"<[^>]+>", " ", html)
        m = re.search(r"Date of Auction\s*:?\s*(\d{2})[-./](\d{2})[-./](\d{4})", txt)
        if m:
            date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    if not img or not date:
        misses += 1
        print(f"nid {nid}: no auction found")
        if misses == 1:
            print("Page sample:", re.sub(r"\s+", " ", html)[:800])
        if misses >= 15: break
        continue
    misses = 0
    if int(date[:4]) < YEAR_FROM:
        older += 1
        print(f"nid {nid}: {date} (older, skip)")
        if older >= 3: break
        continue
    older = 0
    if any(f.startswith(date) for f in os.listdir(OUT)):
        skipped += 1
        continue
    path = "content/images/prices/" + img.group(1)
    data = get(BASE + path)
    if data and len(data) > 2000:
        ext = os.path.splitext(path)[1].lower() or ".jpg"
        open(os.path.join(OUT, date + ext), "wb").write(data)
        print(f"nid {nid}: saved {date}{ext} ({len(data)} bytes)")
        saved += 1
    else:
        print(f"nid {nid}: {date} image download failed")
        failed.append(date)
    time.sleep(1)

print(f"\nDone. Saved {saved}, already had {skipped}, failed {len(failed)}")
if failed:
    print("Failed dates:", ", ".join(failed))
