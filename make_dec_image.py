"""
make_dec_image.py  -  TopGoviya.lk link preview image for the Dambulla DEC page
------------------------------------------------------------------------------
Makes share/dambulla-wide.png (1200 x 630): the picture WhatsApp / Facebook show
when someone shares the Dambulla page link. It shows today's DEC wholesale price
range for 8 popular items, with the change vs the previous report.

Also updates the og:image address inside dambulla.html (?v=date) so Facebook and
WhatsApp show the new picture instead of an old saved copy.

  python make_dec_image.py --check   prints need=yes / need=no (for the robot)
  python make_dec_image.py           makes the image

Drawn with Chrome (Playwright) like make_daily_image.py, so Sinhala letters join correctly.
"""
import json, os, re, sys
from datetime import date

DATA = "dambulla_dec.json"
OUT_DIR = "share"
WIDE = os.path.join(OUT_DIR, "dambulla-wide.png")
STATE = os.path.join(OUT_DIR, "dambulla-wide.json")
PAGES = ["dambulla.html"]          # pages whose og:image is refreshed
STYLE_VERSION = "4"                # change to force a redraw after a design change
ROWS = 8

# DEC product id -> (Sinhala name, emoji), in popular order. Coconut is left out
# until its unit (per nut / per kg) is confirmed.
POPULAR = [
    ("11", "තක්කාලි", "🍅"), ("70", "ලොකු ළූණු (ආනයනික)", "🧅"), ("67", "අමු මිරිස්", "🌶️"),
    ("26", "වම්බටු", "🍆"), ("4", "බෝංචි", "🫛"), ("6", "කැරට්", "🥕"),
    ("69", "රතු ළූණු (දේශීය)", "🧅"), ("15", "අර්තාපල් (නුවරඑළිය)", "🥔"),
    ("20", "අර්තාපල් (ආනයනික)", "🥔"), ("1", "ගෝවා", "🥬"), ("22", "බණ්ඩක්කා", "🫑"),
    ("27", "දෙහි", "🍋"), ("47", "සුදු ළූණු", "🧄"), ("23", "පතෝල", "🥒"),
]
MONTHS = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි",
          "අගෝස්තු", "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]


def si_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.year} {MONTHS[d.month - 1]} {d.day}"


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def state_now(db):
    return {"date": db.get("latest_date"), "style": STYLE_VERSION}


def need(db):
    if not db.get("latest_date"):
        return False
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f) != state_now(db)
    except Exception:
        return True


def rows_for(db):
    days = sorted(db["days"])
    last = days[-1]
    prev = days[-2] if len(days) > 1 else None
    out = []
    for pid, name, emoji in POPULAR:
        v = db["days"][last].get(pid)
        if not v:
            continue
        mid = (v[0] + v[1]) / 2
        chg = None
        if prev and db["days"][prev].get(pid):
            p = db["days"][prev][pid]
            pm = (p[0] + p[1]) / 2
            chg = (mid - pm) / pm * 100 if pm else None
        out.append((emoji, name, v[0], v[1], chg))
        if len(out) == ROWS:
            break
    return out, last


def money(n):
    return f"{n:,.0f}"


def page_html(rows, last):
    trs = []
    for emoji, name, lo, hi, chg in rows:
        if chg is None or abs(chg) < 0.5:
            badge = '<span class="c flat">■</span>'
        elif chg > 0:
            badge = f'<span class="c up">▲ {chg:.0f}%</span>'
        else:
            badge = f'<span class="c down">▼ {abs(chg):.0f}%</span>'
        trs.append(f'<div class="r"><span class="n">{emoji} {name}</span>'
                   f'<span class="p">{money(lo)}–{money(hi)}</span>{badge}</div>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;display:flex;font-family:'Noto Sans Sinhala',sans-serif;background:#fffdf7;color:#191d1a}}
.l{{flex:0 0 420px;background:#0e4f4a;color:#fff;padding:44px 40px;display:flex;flex-direction:column}}
.brand{{color:#d4ad55;font:700 26px 'Noto Sans Sinhala',sans-serif;letter-spacing:.02em}}
h1{{font-size:62px;line-height:1.12;margin-top:34px;font-weight:800}}
.sub{{font-size:27px;opacity:.9;margin-top:10px}}
.d{{display:inline-block;margin-top:26px;background:#d4ad55;color:#0a3a36;font-weight:800;font-size:28px;padding:8px 18px;border-radius:12px}}
.url{{margin-top:auto;font:700 30px 'Noto Sans Sinhala',sans-serif}}
.rt{{flex:1;min-width:0;padding:30px 40px 24px;display:flex;flex-direction:column}}
.hd{{display:flex;justify-content:space-between;font-size:21px;color:#6f675a;border-bottom:3px solid #a9802a;padding-bottom:8px;margin-bottom:6px}}
.r{{display:flex;align-items:center;height:62px;border-bottom:1px solid #e3d9c4}}
.r:nth-child(even){{background:#f7f2e7}}
.n{{flex:1;min-width:0;font-size:28px;font-weight:600;padding-left:6px;white-space:nowrap;overflow:hidden}}
.p{{font:700 29px 'JetBrains Mono',monospace;flex:0 0 190px;text-align:right}}
.c{{font:700 22px 'JetBrains Mono',monospace;flex:0 0 105px;text-align:right;padding-right:6px}}
.up{{color:#b23a2e}}.down{{color:#2c7a52}}.flat{{color:#8a8170}}
.ft{{margin-top:auto;font-size:18px;color:#6f675a}}
</style></head><body>
<div class="l"><div class="brand">TopGoviya.lk</div><h1>දඹුල්ල<br>තොග මිල</h1>
<div class="sub">අද එළවළු මිල<br>රු. / කි.ග්‍රෑ.</div><div class="d">{si_date(last)}</div>
<div class="url">🌐 topgoviya.lk</div></div>
<div class="rt"><div class="hd"><span>භාණ්ඩය</span><span>අවම – උපරිම · පෙර දිනට</span></div>
{''.join(trs)}
<div class="ft">මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය</div></div>
</body></html>"""


def refresh_pages(last):
    for p in PAGES:
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        s2 = re.sub(r"(share/dambulla-wide\.png\?v=)[0-9-]+", r"\g<1>" + last, s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            print(f"Updated preview address in {p}")


def main():
    db = load()
    if "--check" in sys.argv:
        print("need=" + ("yes" if need(db) else "no"))
        return
    rows, last = rows_for(db)
    if not rows:
        print("No prices to draw.")
        return
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT_DIR, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        pg.set_content(page_html(rows, last))
        pg.wait_for_timeout(400)
        pg.screenshot(path=WIDE)
        b.close()
    refresh_pages(last)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state_now(db), f)
    print(f"Made {WIDE} for {last} ({len(rows)} items).")


if __name__ == "__main__":
    main()
