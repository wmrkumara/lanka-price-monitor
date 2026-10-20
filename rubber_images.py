# TopGoviya.lk - download Colombo rubber auction price images from RRISL
# Saves each auction image as rubber_imgs/YYYY-MM-DD.<ext>  (images already saved are skipped)
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

saved, skipped, failed = 0, 0, []
for page in range(1, 200):
    raw = get(f"{BASE}price_e.php?id={page}")
    if raw is None:
        print("Could not open list page", page); break
    html = raw.decode("utf-8", "ignore")
    links = re.findall(r'nid=(\d+)[^>]*>\s*(\d{2})-(\d{2})-(\d{4})', html)
    if not links:
        print("No auctions found on page", page); break
    print(f"Page {page}: " + ", ".join(f"{d}-{m}-{y}" for _, d, m, y in links))
    older = 0
    for nid, d, m, y in links:
        if int(y) < YEAR_FROM:
            older += 1
            continue
        date = f"{y}-{m}-{d}"
        if any(f.startswith(date) for f in os.listdir(OUT)):
            skipped += 1
            continue
        img = None
        detail = get(f"{BASE}price_e.php?nid={nid}&id=1")
        if detail:
            mm = re.search(r'content/images/prices/([^"\'\s>]+)', detail.decode("utf-8", "ignore"))
            if mm:
                img = "content/images/prices/" + mm.group(1)
        tries = [img] if img else []
        tries += [f"content/images/prices/{date}.JPG", f"content/images/prices/{date}.jpg"]
        ok = False
        for path in tries:
            data = get(BASE + path)
            if data and len(data) > 2000:
                ext = os.path.splitext(path)[1].lower() or ".jpg"
                open(os.path.join(OUT, date + ext), "wb").write(data)
                print("  saved", date + ext, len(data), "bytes")
                saved += 1
                ok = True
                break
        if not ok:
            failed.append(date)
        time.sleep(1)
    if older == len(links):
        break

print(f"\nDone. Saved {saved}, already had {skipped}, failed {len(failed)}")
if failed:
    print("Failed dates:", ", ".join(failed))
