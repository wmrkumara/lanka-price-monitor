# TopGoviya.lk — daily Dambulla price video (Phase 1: 12 vegetables, silent, ~2 minutes)
# Reads data.json (CBSL daily report, Dambulla wholesale + retail) and makes, in folder daily_video/:
#   topgoviya-daily-YYYY-MM-DD.mp4   1920x1080 silent video (add your voice in CapCut)
#   thumbnail-YYYY-MM-DD.png         1280x720 YouTube thumbnail
#   youtube-YYYY-MM-DD.txt           ready title + description
# Crop photos (optional): video-assets/crops/<name>.jpg, e.g. cabbage.jpg. Missing photo = name box.
import json, os, subprocess, sys
from datetime import date
from PIL import Image, ImageDraw, ImageFont, ImageOps, features
from build_pages import n_si, fdate, sl, MONTHS

OUT = "daily_video"
CROPS = "video-assets/crops"
LOGO = "icon-512x512.png"
FONT_DIR = os.path.expanduser("~/.fonts/")
ITEMS = [  # (data.json name, photo file name)
    ("Beans", "beans"), ("Carrot", "carrot"), ("Cabbage", "cabbage"), ("Tomato", "tomato"),
    ("Brinjal", "brinjal"), ("Pumpkin", "pumpkin"), ("Snake gourd", "snake-gourd"),
    ("Green Chilli", "green-chilli"), ("Lime", "lime"), ("Big Onion (Local)", "big-onion"),
    ("Red Onion (Local)", "red-onion"), ("Potato (Local)", "potato"),
]
SEC_TITLE, SEC_ITEM, SEC_SUM, SEC_END = 7, 8, 8, 10
DAYS_SI = ["සඳුදා", "අඟහරුවාදා", "බදාදා", "බ්‍රහස්පතින්දා", "සිකුරාදා", "සෙනසුරාදා", "ඉරිදා"]

PET = (14, 79, 74); PETD = (10, 58, 54); GOLD = (169, 128, 42); LG = (255, 217, 138)
CREAM = (244, 239, 228); CARD = (255, 253, 247); INK = (25, 29, 26); MUT = (122, 114, 100)
LINE = (227, 217, 196); UP = (178, 58, 46); UPBG = (247, 230, 226); DN = (44, 122, 82); DNBG = (227, 239, 230)
FLAT = (122, 114, 100); FLATBG = (236, 231, 218); W = (255, 255, 255); PH = (232, 224, 206)


def font(n, s, st="Bold"):
    f = ImageFont.truetype(FONT_DIR + n, s, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_name(st)
    except Exception:
        pass
    return f

si = lambda s, st="Bold": font("NotoSansSinhala.ttf", s, st)
mono = lambda s, st="Bold": font("JetBrainsMono.ttf", s, st)


def last_two(series):
    pts = [v for v in series if v is not None]
    return (pts[-1] if pts else None), (pts[-2] if len(pts) > 1 else None)


def load():
    d = json.load(open("data.json", encoding="utf-8"))
    by = {c["name"]: c for c in d["commodities"]}
    rep = date.fromisoformat(d["dates"][-1])
    rows = []
    for name, photo in ITEMS:
        c = by.get(name)
        if not c:
            continue
        r_now = c["series"][-1] if c["series"] else None          # latest report only (no old prices)
        ws = c.get("wholesaleSeries") or []
        w_now = ws[-1] if ws else None
        w_prev = last_two(ws)[1] if w_now is not None else None
        if w_now is None and r_now is None:
            continue
        r_prev = last_two(c["series"])[1] if r_now is not None else None
        base_now, base_prev, kind = (w_now, w_prev, "තොග") if w_now is not None else (r_now, r_prev, "සිල්ලර")
        pct = (base_now - base_prev) / base_prev * 100 if base_now is not None and base_prev else None
        rows.append(dict(name=name, si=n_si(name), photo=photo, w=w_now, r=r_now,
                         prev=base_prev, now=base_now, kind=kind, pct=pct))
    return rep, rows


def logo_badge(size):
    lg = Image.open(LOGO).convert("RGBA").resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    lg.putalpha(m)
    return lg


def segs(dr, x, y, parts, anchor_center=False):
    """Draw mixed-font text pieces on one line (Sinhala font has no arrows)."""
    tw = sum(dr.textlength(t, font=f) for t, f, c in parts)
    if anchor_center:
        x -= tw / 2
    for t, f, c in parts:
        dr.text((x, y), t, font=f, fill=c, anchor="lm")
        x += dr.textlength(t, font=f)


def change_style(p):
    if p is None:
        return "■", FLAT, FLATBG
    if p >= 0.5:
        return "▲", UP, UPBG
    if p <= -0.5:
        return "▼", DN, DNBG
    return "■", FLAT, FLATBG


def frame(rep):
    im = Image.new("RGB", (1920, 1080), CREAM); dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, 1920, 150), fill=PET)
    b = logo_badge(110); im.paste(b, (40, 20), b)
    dr.text((175, 22), "දඹුල්ල වෙළඳපොළ · අද එළවළු මිල", font=si(56), fill=W)
    dr.text((178, 96), "TopGoviya.lk", font=si(30, "SemiBold"), fill=LG)
    dr.rounded_rectangle((1440, 38, 1880, 112), radius=37, fill=GOLD)
    dr.text((1660, 75), fdate(rep, "si"), font=si(36), fill=W, anchor="mm")
    dr.rectangle((0, 150, 1920, 158), fill=GOLD)
    dr.rectangle((0, 1000, 1920, 1080), fill=PETD)
    dr.text((60, 1040), "දත්ත: ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව · මිල ගණන් මඟපෙන්වීමක් පමණි",
            font=si(28, "Medium"), fill=W, anchor="lm")
    dr.text((1860, 1040), "topgoviya.lk", font=mono(36), fill=LG, anchor="rm")
    return im, dr


def photo_box(im, dr, row, box):
    x0, y0, x1, y1 = box
    p = None
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        f = os.path.join(CROPS, row["photo"] + ext)
        if os.path.exists(f):
            p = f; break
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=30, fill=255)
    if p:
        try:
            ph = ImageOps.fit(Image.open(p).convert("RGB"), (x1 - x0, y1 - y0), Image.LANCZOS)
            im.paste(ph, (x0, y0), mask)
            return
        except Exception:
            pass
    dr.rounded_rectangle(box, radius=30, fill=PH)
    dr.text(((x0 + x1) // 2, (y0 + y1) // 2), row["si"], font=si(80), fill=MUT, anchor="mm")


def item_slide(rep, row, i, n):
    im, dr = frame(rep)
    photo_box(im, dr, row, (60, 200, 900, 960))
    dr.text((960, 190), f"{i} / {n}", font=mono(30), fill=MUT)
    f = si(130)
    while dr.textlength(row["si"], font=f) > 900 and f.size > 70:
        f = si(f.size - 6)
    dr.text((960, 225), row["si"], font=f, fill=PET)
    dr.text((965, 400), f"{row['name']} · රු. / කි.ග්‍රෑ.", font=si(34, "Medium"), fill=MUT)

    def box(x, label, val, col):
        dr.rounded_rectangle((x, 470, x + 420, 760), radius=26, fill=CARD, outline=LINE, width=3)
        dr.text((x + 210, 520), label, font=si(40, "SemiBold"), fill=MUT, anchor="mm")
        txt = f"{val:,.0f}" if val is not None else "—"
        fs = mono(120)
        while dr.textlength(txt, font=fs) > 380:
            fs = mono(fs.size - 6)
        dr.text((x + 210, 650), txt, font=fs, fill=col, anchor="mm")
    box(960, "තොග", row["w"], GOLD)
    box(1420, "සිල්ලර", row["r"], INK)

    ar, col, bg = change_style(row["pct"])
    dr.rounded_rectangle((960, 800, 1840, 890), radius=20, fill=bg)
    if row["pct"] is None:
        segs(dr, 1400, 845, [("පෙර වාර්තාවේ මිල නැත", si(34, "SemiBold"), col)], True)
    else:
        segs(dr, 1400, 845, [
            (ar + " ", mono(36), col),
            (f"{row['kind']} මිල පෙර වාර්තාවට ", si(34, "SemiBold"), col),
            (f"{row['pct']:+.0f}%  ", mono(36), col),
            (f"({row['prev']:,.0f} → {row['now']:,.0f})", mono(32, "Medium"), col)], True)
    return im


def title_slide(rep, n):
    im = Image.new("RGB", (1920, 1080), PET); dr = ImageDraw.Draw(im)
    b = logo_badge(200); im.paste(b, (860, 110), b)
    dr.text((960, 420), "අද එළවළු මිල", font=si(150), fill=W, anchor="mm")
    dr.text((960, 560), f"දඹුල්ල වෙළඳපොළ · තොග හා සිල්ලර · එළවළු {n}ක්", font=si(46, "SemiBold"), fill=LG, anchor="mm")
    dr.rounded_rectangle((560, 640, 1360, 740), radius=50, fill=GOLD)
    dr.text((960, 690), f"{fdate(rep, 'si')} · {DAYS_SI[rep.weekday()]}", font=si(48), fill=W, anchor="mm")
    dr.text((960, 930), "දත්ත: ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව", font=si(34, "Medium"), fill=W, anchor="mm")
    dr.text((960, 990), "topgoviya.lk", font=mono(40), fill=LG, anchor="mm")
    return im


def movers(rows):
    ch = [r for r in rows if r["pct"] is not None]
    up = max(ch, key=lambda r: r["pct"]) if ch else None
    dn = min(ch, key=lambda r: r["pct"]) if ch else None
    return (up if up and up["pct"] >= 0.5 else None), (dn if dn and dn["pct"] <= -0.5 else None)


def summary_slide(rep, rows):
    im, dr = frame(rep)
    dr.text((960, 250), "අද වැඩිම වෙනස්වීම්", font=si(80), fill=PET, anchor="mm")
    up, dn = movers(rows)
    for k, (r, label) in enumerate([(up, "වැඩියෙන්ම ඉහළ ගියේ"), (dn, "වැඩියෙන්ම පහළ ගියේ")]):
        y = 380 + k * 290
        ar, col, bg = change_style(r["pct"] if r else None)
        dr.rounded_rectangle((260, y, 1660, y + 240), radius=30, fill=bg if r else FLATBG)
        dr.text((320, y + 60), label, font=si(40, "SemiBold"), fill=MUT, anchor="lm")
        if r:
            pt = f"{ar} {r['pct']:+.0f}%"
            pw = dr.textlength(pt, font=mono(90))
            nf = si(80)
            while dr.textlength(r["si"], font=nf) > (1600 - pw - 60) - 320 and nf.size > 44:
                nf = si(nf.size - 4)
            dr.text((320, y + 150), r["si"], font=nf, fill=INK, anchor="lm")
            segs(dr, 1600 - pw, y + 150, [(pt, mono(90), col)])
            info = [(f"{r['kind']} · රු. ", si(34, "Medium"), col), (f"{r['prev']:,.0f} → {r['now']:,.0f}", mono(32, "Medium"), col)]
            iw = sum(dr.textlength(t, font=f) for t, f, c in info)
            segs(dr, 1600 - iw, y + 60, info)
        else:
            dr.text((320, y + 150), "විශාල වෙනසක් නැත", font=si(60), fill=MUT, anchor="lm")
    return im


def end_slide(rep):
    im = Image.new("RGB", (1920, 1080), PET); dr = ImageDraw.Draw(im)
    b = logo_badge(180); im.paste(b, (870, 90), b)
    dr.text((960, 380), "සියලු මිල ගණන් නොමිලේ", font=si(84), fill=W, anchor="mm")
    dr.text((960, 500), "වෙළඳපොළ 10ක තොග මිල · කුළුබඩු · තේ මිල", font=si(46, "SemiBold"), fill=LG, anchor="mm")
    dr.rounded_rectangle((560, 580, 1360, 700), radius=60, fill=GOLD)
    dr.text((960, 640), "topgoviya.lk", font=mono(70), fill=W, anchor="mm")
    dr.text((960, 800), "Subscribe කරන්න · හෙට නැවත හමුවෙමු", font=si(48, "SemiBold"), fill=W, anchor="mm")
    dr.text((960, 960), "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.", font=si(34, "Medium"), fill=LG, anchor="mm")
    return im


def thumbnail(rep, rows):
    im = Image.new("RGB", (1280, 720), PET); dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, 1280, 120), fill=GOLD)
    dr.text((640, 60), f"{fdate(rep, 'si')} · {DAYS_SI[rep.weekday()]}", font=si(64), fill=W, anchor="mm")
    dr.text((640, 250), "අද දඹුල්ල", font=si(120), fill=W, anchor="mm")
    dr.text((640, 400), "එළවළු මිල", font=si(120), fill=LG, anchor="mm")
    up, dn = movers(rows)
    r = up or dn
    if r:
        ar, col, bg = change_style(r["pct"])
        dr.rounded_rectangle((140, 500, 1140, 670), radius=30, fill=bg)
        dr.text((200, 585), r["si"], font=si(80), fill=INK, anchor="lm")
        segs(dr, 1080 - dr.textlength(f"{ar} {r['pct']:+.0f}%", font=mono(90)), 585, [(f"{ar} {r['pct']:+.0f}%", mono(90), col)])
    b = logo_badge(110); im.paste(b, (20, 140), b)
    return im


def text_file(rep, rows):
    up, dn = movers(rows)
    ds = rep.strftime("%Y.%m.%d")
    t = f"අද එළවළු මිල {ds} {DAYS_SI[rep.weekday()]} | Dambulla Vegetable Price Today | දඹුල්ල තොග හා සිල්ලර මිල"
    lines = [f"TITLE:\n{t[:100]}", "", "DESCRIPTION:",
             f"අද එළවළු මිල — {fdate(rep, 'si')} ({DAYS_SI[rep.weekday()]}), දඹුල්ල වෙළඳපොළ.",
             "ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාවේ තොග හා සිල්ලර මිල (රු. / කි.ග්‍රෑ.).", ""]
    for r in rows:
        w = f"{r['w']:,.0f}" if r["w"] is not None else "—"
        rr = f"{r['r']:,.0f}" if r["r"] is not None else "—"
        lines.append(f"• {r['si']} — තොග {w} · සිල්ලර {rr}")
    lines.append("")
    if up:
        lines.append(f"📈 වැඩියෙන්ම ඉහළ ගියේ: {up['si']} ({up['pct']:+.0f}%)")
    if dn:
        lines.append(f"📉 වැඩියෙන්ම පහළ ගියේ: {dn['si']} ({dn['pct']:+.0f}%)")
    lines += ["", "👉 සියලු මිල, වෙළඳපොළ 10ක තොග මිල: https://topgoviya.lk",
              "👉 දඹුල්ල මිල: https://topgoviya.lk/market/dambulla.html", "",
              "දත්ත: ශ්‍රී ලංකා මහ බැංකුවේ දෛනික මිල වාර්තාව (Central Bank of Sri Lanka daily price report).",
              "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.", "",
              "elawalu mila ada · elawalu mila today · dambulla elawalu mila · dambulla market price today · "
              + " · ".join(f"{sl(r['name'])} mila" for r in rows if sl(r["name"])), "",
              "#අදඑළවළුමිල #TopGoviyaLK #DambullaMarket #ElawaluMila #VegetablePrice #SriLanka"]
    return "\n".join(lines) + "\n"


def script_file(rep, rows):
    """Reading script for the voice: one block per slide, same order and timing as the video."""
    up, dn = movers(rows)
    day = f"{MONTHS['si'][rep.month - 1]} {rep.day} {DAYS_SI[rep.weekday()]}"
    money_ = lambda v: f"{v:,.0f}"
    L = ["TopGoviya — කියවීමේ පිටපත (Reading script)", f"වාර්තා දිනය: {fdate(rep, 'si')}", "",
         f"[මාතෘකා පිටුව · තත්පර {SEC_TITLE}]",
         f"ආයුබෝවන්! TopGoviya අද එළවළු මිල. {day}, මහ බැංකු වාර්තාව අනුව, දඹුල්ල වෙළඳපොළ.", ""]
    for i, r in enumerate(rows, 1):
        parts = []
        if r["w"] is not None:
            parts.append(f"තොග රුපියල් {money_(r['w'])}")
        if r["r"] is not None:
            parts.append(f"සිල්ලර රුපියල් {money_(r['r'])}")
        line = f"{r['si']}. " + ", ".join(parts) + "."
        if r["pct"] is not None and abs(r["pct"]) >= 10:
            line += f" කලින් වාර්තාවට වඩා {abs(r['pct']):.0f}%කින් {'ඉහළයි' if r['pct'] > 0 else 'අඩුයි'}."
        L += [f"[{i} / {len(rows)} · තත්පර {SEC_ITEM}]", line, ""]
    L.append(f"[වැඩිම වෙනස්වීම් · තත්පර {SEC_SUM}]")
    t = []
    if up:
        t.append(f"අද වැඩියෙන්ම ඉහළ ගියේ {up['si']}, {abs(up['pct']):.0f}%යි.")
    if dn:
        t.append(f"වැඩියෙන්ම අඩු වුණේ {dn['si']}, {abs(dn['pct']):.0f}%යි.")
    L += [" ".join(t) or "අද විශාල මිල වෙනසක් නැහැ.", "",
          f"[අවසාන පිටුව · තත්පර {SEC_END}]",
          "සියලු මිල ගණන්, වෙළඳපොළ 10ක තොග මිල, topgoviya.lk වෙබ් අඩවියෙන් නොමිලේ බලන්න. "
          "මිල ගණන් මඟපෙන්වීමක් පමණි. Subscribe කරන්න, හෙට නැවත හමුවෙමු!"]
    return "\n".join(L) + "\n"


def main():
    if not features.check("raqm"):
        sys.exit("Sinhala text support (raqm) is missing. Stopping.")
    rep, rows = load()
    if not rows:
        sys.exit("No prices found in data.json")
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "frames"); os.makedirs(tmp, exist_ok=True)
    slides = [(title_slide(rep, len(rows)), SEC_TITLE)]
    slides += [(item_slide(rep, r, i + 1, len(rows)), SEC_ITEM) for i, r in enumerate(rows)]
    slides += [(summary_slide(rep, rows), SEC_SUM), (end_slide(rep), SEC_END)]
    lst = []
    for k, (im, sec) in enumerate(slides):
        p = os.path.join(tmp, f"s{k:02d}.png"); im.save(p)
        lst.append(f"file '{os.path.abspath(p)}'\nduration {sec}")
    lst.append(f"file '{os.path.abspath(p)}'")  # ffmpeg needs the last file twice
    open(os.path.join(tmp, "list.txt"), "w").write("\n".join(lst) + "\n")
    iso = rep.isoformat()
    mp4 = os.path.join(OUT, f"topgoviya-daily-{iso}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", os.path.join(tmp, "list.txt"), "-vf", "fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-movflags", "+faststart", mp4], check=True)
    thumbnail(rep, rows).save(os.path.join(OUT, f"thumbnail-{iso}.png"))
    open(os.path.join(OUT, f"youtube-{iso}.txt"), "w", encoding="utf-8").write(text_file(rep, rows))
    open(os.path.join(OUT, f"script-{iso}.txt"), "w", encoding="utf-8").write(script_file(rep, rows))
    total = SEC_TITLE + SEC_ITEM * len(rows) + SEC_SUM + SEC_END
    print(f"Made {mp4} ({total} seconds, {len(rows)} vegetables) for report {iso}")


if __name__ == "__main__":
    main()
