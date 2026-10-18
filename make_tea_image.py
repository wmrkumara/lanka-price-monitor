# TopGoviya.lk — monthly tea price images + Facebook caption
# Reads tea_price_data.json (Sri Lanka Tea Board, made tea auction price by sub-district).
# Makes: share/tea.png (4:5), share/tea-upcountry.png (4:5), share/tea-story.png (9:16), share/tea-caption.txt
#   python3 make_tea_image.py --check   -> prints need=yes / need=no
#   python3 make_tea_image.py           -> makes the files
#   python3 make_tea_image.py --force   -> makes the files even if this month was done
import json, os, sys, datetime
from PIL import Image, ImageDraw, ImageFont, features

DATA = "tea_price_data.json"
OUT = "share"
NOTE = os.path.join(OUT, ".tea_image_month")
LOGO = "icon-512x512.png"
FONT_DIR = os.path.expanduser("~/.fonts/")

MONTHS_SI = ["ජනවාරි", "පෙබරවාරි", "මාර්තු", "අප්‍රේල්", "මැයි", "ජූනි", "ජූලි",
             "අගෝස්තු", "සැප්තැම්බර්", "ඔක්තෝබර්", "නොවැම්බර්", "දෙසැම්බර්"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
# Low-grown areas; every other sub-district counts as up-country / hill country
LOW_GROWN = {"Deniyaya", "Matara", "Morawaka", "Galle", "Kalutara", "Ratnapura",
             "Kegalle", "Kelani Valley", "Balangoda", "Balangoda-Rakwana"}

PET = (14, 79, 74); PETD = (10, 58, 54); GOLD = (169, 128, 42); LIGHTGOLD = (255, 217, 138)
CREAM = (244, 239, 228); CARD = (255, 253, 247); ROW = (250, 246, 236)
INK = (25, 29, 26); MUT = (122, 114, 100); LINE = (227, 217, 196)
UP = (44, 122, 82); DN = (178, 58, 46); WHITE = (255, 255, 255)


def load():
    d = json.load(open(DATA, encoding="utf-8"))
    months = d["months"]
    keys = sorted(months)
    cur_k = d.get("latestMonth") or keys[-1]
    i = keys.index(cur_k)
    prev_k = keys[i - 1] if i > 0 else None
    y, m = map(int, cur_k.split("-"))
    ly_k = f"{y - 1}-{m:02d}"
    tbl = lambda k: {r["subDistrict"]: r["monthlyAvg"] for r in months.get(k, []) if r.get("monthlyAvg")}
    return cur_k, tbl(cur_k), tbl(prev_k) if prev_k else {}, tbl(ly_k)


def check():
    cur_k = json.load(open(DATA, encoding="utf-8")).get("latestMonth", "")
    done = open(NOTE).read().strip() if os.path.exists(NOTE) else ""
    print("need=" + ("no" if cur_k and cur_k == done else "yes"))


def font(name, size, style):
    f = ImageFont.truetype(FONT_DIR + name, size, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_name(style)
    except Exception:
        pass
    return f

si = lambda s, st="Bold": font("NotoSansSinhala.ttf", s, st)
mono = lambda s, st="Bold": font("JetBrainsMono.ttf", s, st)


def logo_badge(size):
    lg = Image.open(LOGO).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    lg.putalpha(mask)
    return lg


def pct(v, p):
    return None if not p else (v - p) / p * 100


def chg_text(c):
    if c is None:
        return "—", MUT
    if c >= 0.5:
        return f"▲ {c:+.1f}%", UP
    if c <= -0.5:
        return f"▼ {c:+.1f}%", DN
    return f"■ {c:+.1f}%", MUT


def fit(dr, text, fnt_fn, size, maxw, style="SemiBold"):
    f = fnt_fn(size, style)
    while dr.textlength(text, font=f) > maxw and size > 16:
        size -= 1
        f = fnt_fn(size, style)
    return f


def header(im, dr, W, title, sub, h=250):
    dr.rectangle((0, 0, W, h), fill=PET)
    b = logo_badge(170)
    im.paste(b, (50, (h - 170) // 2), b)
    dr.text((250, h // 2 - 74), title, font=fit(dr, title, si, 72, W - 290, "Bold"), fill=WHITE)
    dr.text((252, h // 2 + 26), sub, font=fit(dr, sub, si, 32, W - 290, "Medium"), fill=LIGHTGOLD)
    dr.rectangle((0, h, W, h + 8), fill=GOLD)


def note_lines(dr, x, y):
    dr.text((x, y), "සැකසූ තේ (Made tea) වෙන්දේසි මාසික සාමාන්‍යය  ·  රු./කි.ග්‍රෑ.",
            font=si(28, "SemiBold"), fill=INK)
    dr.text((x, y + 44), "මෙය දළු (කොළ) මිල නොවේ", font=si(26, "Medium"), fill=DN)


def footer(dr, W, y):
    dr.text((W // 2, y), "දත්ත: ශ්‍රී ලංකා තේ මණ්ඩලය (Sri Lanka Tea Board)",
            font=si(24, "SemiBold"), fill=INK, anchor="mm")
    dr.text((W // 2, y + 40), "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.",
            font=si(22, "Regular"), fill=MUT, anchor="mm")


def cta(dr, W, y, line1):
    dr.rounded_rectangle((50, y, W - 50, y + 100), radius=18, fill=PETD)
    dr.text((W // 2, y + 30), line1, font=si(28, "SemiBold"), fill=WHITE, anchor="mm")
    dr.text((W // 2, y + 72), "topgoviya.lk/tea.html", font=mono(30), fill=LIGHTGOLD, anchor="mm")


def table(dr, rows, prev, x0, y0, x1, rh, name_size=30, price_size=34):
    dr.rounded_rectangle((x0, y0, x1, y0 + 60 + rh * len(rows) + 10), radius=22, fill=CARD, outline=LINE, width=2)
    dr.text((x0 + 34, y0 + 30), "#", font=mono(24), fill=MUT, anchor="mm")
    dr.text((x0 + 80, y0 + 14), "උප දිස්ත්‍රික්කය", font=si(24, "SemiBold"), fill=MUT)
    dr.text((x1 - 200, y0 + 14), "මිල (රු.)", font=si(24, "SemiBold"), fill=MUT, anchor="ra")
    dr.text((x1 - 30, y0 + 14), "පෙර මාසයට", font=si(24, "SemiBold"), fill=MUT, anchor="ra")
    for i, (n, v) in enumerate(rows):
        y = y0 + 60 + i * rh
        if i % 2 == 0:
            dr.rectangle((x0 + 2, y, x1 - 2, y + rh), fill=ROW)
        dr.line((x0 + 20, y, x1 - 20, y), fill=LINE, width=1)
        cy = y + rh // 2
        dr.text((x0 + 34, cy), str(i + 1), font=mono(28), fill=GOLD if i < 3 else MUT, anchor="mm")
        nm = n.replace("-", " - ")
        f = fit(dr, nm, si, name_size, (x1 - 330) - (x0 + 80) - 20)
        dr.text((x0 + 80, cy), nm, font=f, fill=INK, anchor="lm")
        dr.text((x1 - 200, cy), f"{v:,.0f}", font=mono(price_size), fill=INK, anchor="rm")
        t, col = chg_text(pct(v, prev.get(n)))
        dr.text((x1 - 30, cy), t, font=mono(26), fill=col, anchor="rm")
    return y0 + 60 + rh * len(rows) + 10


def feed_image(path, rows, prev, title, sub, cta_line, rh):
    W, H = 1080, 1350
    im = Image.new("RGB", (W, H), CREAM); dr = ImageDraw.Draw(im)
    header(im, dr, W, title, sub)
    note_lines(dr, 60, 282)
    yb = table(dr, rows, prev, 50, 385, W - 50, rh)
    cta(dr, W, yb + 28, cta_line)
    footer(dr, W, yb + 170)
    im.save(path, optimize=True)


def story_image(path, feed_path, n):
    # 9:16 WhatsApp Status: the 4:5 image in the middle, big link below
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), PET); dr = ImageDraw.Draw(im)
    feed = Image.open(feed_path)
    im.paste(feed, (0, 230))
    dr.text((W // 2, 120), "තේ මිල — මේ මාසය", font=si(64, "Bold"), fill=WHITE, anchor="mm")
    dr.rectangle((0, 1580, W, 1588), fill=GOLD)
    dr.text((W // 2, 1680), f"උප දිස්ත්‍රික්ක {n} ම බලන්න", font=si(44, "SemiBold"), fill=WHITE, anchor="mm")
    dr.text((W // 2, 1770), "topgoviya.lk/tea.html", font=mono(52), fill=LIGHTGOLD, anchor="mm")
    im.save(path, optimize=True)


def caption(cur_k, cur, prev, ly, top):
    y, m = map(int, cur_k.split("-"))
    mon_si, mon_en = f"{y} {MONTHS_SI[m - 1]}", f"{MONTHS_EN[m - 1]} {y}"
    today = datetime.date.today().isoformat()
    link = f"https://topgoviya.lk/tea.html?d={today}"
    ch = [(n, pct(v, prev.get(n)), prev.get(n), v) for n, v in cur.items() if prev.get(n)]
    up = max(ch, key=lambda x: x[1]) if ch else None
    dn = min(ch, key=lambda x: x[1]) if ch else None
    avg = sum(cur.values()) / len(cur)
    ly_common = [n for n in cur if n in ly]
    avg_ly = sum(ly[n] for n in ly_common) / len(ly_common) if ly_common else None
    avg_now_c = sum(cur[n] for n in ly_common) / len(ly_common) if ly_common else None
    tag = "#" + top[0][0].replace("-", "").replace(" ", "")

    L = [f"🍃 තේ වෙන්දේසි මිල — {mon_si}", "",
         f"උප දිස්ත්‍රික්ක {len(cur)} අතරින් ඉහළම මිල ලැබුණු ප්‍රදේශ 3:"]
    for i, (n, v) in enumerate(top[:3]):
        L.append(f"{['🥇', '🥈', '🥉'][i]} {n} — රු. {v:,.0f}")
    L.append("")
    if up and up[1] >= 0.5:
        L.append(f"📈 වැඩිම ඉහළ යාම: {up[0]} — රු. {up[2]:,.0f} → {up[3]:,.0f} ({up[1]:+.1f}%)")
    if dn and dn[1] <= -0.5:
        L.append(f"📉 වැඩිම පහළ යාම: {dn[0]} — රු. {dn[2]:,.0f} → {dn[3]:,.0f} ({dn[1]:+.1f}%)")
    if avg_ly:
        L.append(f"📊 උප දිස්ත්‍රික්ක {len(ly_common)} සාමාන්‍යය: පසුගිය වසරේ මේ මාසයේ රු. {avg_ly:,.0f}, "
                 f"මේ වසරේ රු. {avg_now_c:,.0f} ({pct(avg_now_c, avg_ly):+.1f}%)")
    L += ["",
          "ℹ️ මේ මිල සැකසූ තේ (Made tea) වෙන්දේසි මාසික සාමාන්‍යයයි (රු./කි.ග්‍රෑ.). මෙය දළු (කොළ) මිල නොවේ.",
          "",
          "👉 ඔබේ ප්‍රදේශයේ මිල සහ පසුගිය මාස වල මිල:",
          link,
          "",
          "දත්ත: ශ්‍රී ලංකා තේ මණ්ඩලය (Sri Lanka Tea Board)",
          "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.",
          "",
          "— English —",
          f"🍃 Sri Lanka tea auction prices, {mon_en} (made tea, monthly average, Rs./kg — not green leaf price).",
          "Top 3: " + ", ".join(f"{n} Rs. {v:,.0f}" for n, v in top[:3]) + ".",
          f"All {len(cur)} sub-districts: {link}",
          "Source: Sri Lanka Tea Board. Prices are indicative only.",
          "",
          f"#TopGoviyaLK #තේමිල #TeaPrice #CeylonTea #SriLankaTea #TeaAuction #තේවගාව "
          f"#SriLankaAgriculture #DataDrivenFarming {tag}"]
    return "\n".join(L) + "\n"


def make():
    if not features.check("raqm"):
        sys.exit("Sinhala text support (raqm) is missing — Sinhala would look broken. Stopping.")
    os.makedirs(OUT, exist_ok=True)
    cur_k, cur, prev, ly = load()
    y, m = map(int, cur_k.split("-"))
    mon = f"{y} {MONTHS_SI[m - 1]}"
    ranked = sorted(cur.items(), key=lambda x: -x[1])
    top10 = ranked[:10]
    hill = [r for r in ranked if r[0] not in LOW_GROWN][:12]

    feed_image(f"{OUT}/tea.png", top10, prev, "තේ වෙන්දේසි මිල",
               f"{mon}  ·  ඉහළම උප දිස්ත්‍රික්ක 10",
               f"ඔබේ ප්‍රදේශයේ මිල? උප දිස්ත්‍රික්ක {len(cur)} ම බලන්න", 66)
    feed_image(f"{OUT}/tea-upcountry.png", hill, prev, "කඳුකර තේ මිල",
               f"{mon}  ·  කඳුකර උප දිස්ත්‍රික්ක",
               f"ඔබේ ප්‍රදේශයේ මිල? උප දිස්ත්‍රික්ක {len(cur)} ම බලන්න", 55)
    story_image(f"{OUT}/tea-story.png", f"{OUT}/tea.png", len(cur))
    open(f"{OUT}/tea-caption.txt", "w", encoding="utf-8").write(caption(cur_k, cur, prev, ly, ranked))
    open(NOTE, "w").write(cur_k + "\n")
    print("Made tea images for", cur_k)


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        make()
