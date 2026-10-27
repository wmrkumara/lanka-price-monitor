# TopGoviya.lk — DAILY Dambulla DEC price video (~2 minutes, 16:9) for YouTube
# Same style and tools as make_daily_video.py (CBSL), but from the Dambulla DEC data:
#   dambulla_dec.json (robot, DEC website) + dambulla_early.json (early entry) — newest day used.
# Makes, in folder dambulla_video/:
#   dambulla-daily-YYYY-MM-DD.mp4         1920x1080 silent video (for your voice)
#   dambulla-daily-YYYY-MM-DD-music.mp4   same video with background music
#   dambulla-thumbnail-YYYY-MM-DD.png     1280x720 YouTube thumbnail
#   dambulla-youtube-YYYY-MM-DD.txt       title + description + tags
#   dambulla-script-YYYY-MM-DD.txt        reading script for your voice, slide by slide
# Crop photos: video-assets/crops/<name>.png (same photos as the CBSL video). Missing photo = name box.
import json, os, subprocess, sys, hashlib
from datetime import date

OUT = "dambulla_video"
STATE = ".dambulla_video_last"


def _quick_check():
    """--check: runs BEFORE the robot installs Pillow, so it uses only built-in Python."""
    days = json.load(open("dambulla_dec.json", encoding="utf-8")).get("days", {})
    if os.path.exists("dambulla_early.json"):
        try:
            e = json.load(open("dambulla_early.json", encoding="utf-8"))
            if e.get("date") and e.get("prices") and e["date"] not in days and (not days or e["date"] > max(days)):
                days[e["date"]] = e["prices"]
        except Exception:
            pass
    if not days:
        print("need=no"); return
    last = max(days)
    st = f"{last}_" + hashlib.sha1(json.dumps(days[last], sort_keys=True).encode()).hexdigest()[:8]
    done = os.path.exists(STATE) and open(STATE).read().strip() == st
    print("need=" + ("no" if done else "yes"))


if __name__ == "__main__" and "--check" in sys.argv:
    _quick_check()
    sys.exit(0)

from PIL import Image, ImageDraw, features
from build_pages import fdate, MONTHS
import make_daily_video as V      # reuse fonts, colours, logo, photo box, music loop
import short_kit
ITEMS = [  # (DEC product id, crop photo name) — in the site's popular order
    ("11", "tomato"), ("70", "big-onion"), ("69", "red-onion"), ("67", "green-chilli"),
    ("15", "potato"), ("26", "brinjal"), ("1", "cabbage"), ("6", "carrot"),
    ("4", "beans"), ("25", "pumpkin"), ("27", "lime"), ("23", "snake-gourd"),
]
SEC_TITLE, SEC_MOOD, SEC_ITEM, SEC_MOVE, SEC_END = 7, 9, 8, 10, 10
si, mono = V.si, V.mono
PET, PETD, GOLD, LG, CREAM, CARD, INK, MUT, LINE, W = V.PET, V.PETD, V.GOLD, V.LG, V.CREAM, V.CARD, V.INK, V.MUT, V.LINE, V.W
UP, UPBG, DN, DNBG, FLAT, FLATBG = V.UP, V.UPBG, V.DN, V.DNBG, V.FLAT, V.FLATBG
DAYS_SI = V.DAYS_SI


def load():
    db = json.load(open("dambulla_dec.json", encoding="utf-8"))
    days = db.get("days", {})
    if os.path.exists("dambulla_early.json"):
        try:
            e = json.load(open("dambulla_early.json", encoding="utf-8"))
            if e.get("date") and e.get("prices") and e["date"] not in days and (not days or e["date"] > max(days)):
                days[e["date"]] = e["prices"]
        except Exception as ex:
            print("Early file ignored:", ex)
    names = json.load(open("dambulla_items.json", encoding="utf-8"))["items"]
    return days, names


def build_rows(days, names):
    order = sorted(days)
    last = order[-1]
    prev = order[-2] if len(order) > 1 else None
    def item(pid):
        v = days[last].get(pid); m = names.get(pid)
        if not v or not m:
            return None
        mid = (v[0] + v[1]) / 2
        pm = None
        if prev and days[prev].get(pid):
            p = days[prev][pid]; pm = (p[0] + p[1]) / 2
        pct = (mid - pm) / pm * 100 if pm else None
        return dict(pid=pid, si=m["si"], en=m["en"], unit=m["unit"], lo=v[0], hi=v[1], mid=mid, prev=pm, pct=pct)
    rows = []
    for pid, photo in ITEMS:
        r = item(pid)
        if r:
            r["photo"] = photo
            rows.append(r)
    allr = [r for r in (item(p) for p in days[last]) if r]
    return date.fromisoformat(last), rows, allr


def unit_si(r):
    return {"kg": "රු. / කි.ග්‍රෑ.", "nut": "රු. / ගෙඩිය", "bundle": "රු. / මිටිය"}.get(r["unit"], "රු.")


def frame(rep):
    im = Image.new("RGB", (1920, 1080), CREAM); dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, 1920, 150), fill=PET)
    b = V.logo_badge(110); im.paste(b, (40, 20), b)
    dr.text((175, 22), "දඹුල්ල තොග මිල · අද එළවළු මිල", font=si(56), fill=W)
    dr.text((178, 96), "TopGoviya.lk", font=si(30, "SemiBold"), fill=LG)
    dr.rounded_rectangle((1440, 38, 1880, 112), radius=37, fill=GOLD)
    dr.text((1660, 75), fdate(rep, "si"), font=si(36), fill=W, anchor="mm")
    dr.rectangle((0, 150, 1920, 158), fill=GOLD)
    dr.rectangle((0, 1000, 1920, 1080), fill=PETD)
    dr.text((60, 1040), "මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · මිල ගණන් මඟපෙන්වීමක් පමණි",
            font=si(28, "Medium"), fill=W, anchor="lm")
    dr.text((1860, 1040), "topgoviya.lk", font=mono(36), fill=LG, anchor="rm")
    return im, dr


def title_slide(rep):
    im = Image.new("RGB", (1920, 1080), PET); dr = ImageDraw.Draw(im)
    b = V.logo_badge(200); im.paste(b, (860, 100), b)
    dr.text((960, 410), "අද දඹුල්ල එළවළු මිල", font=si(130), fill=W, anchor="mm")
    dr.text((960, 550), "දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · තොග මිල පරාසය", font=si(46, "SemiBold"), fill=LG, anchor="mm")
    dr.rounded_rectangle((560, 630, 1360, 730), radius=50, fill=GOLD)
    dr.text((960, 680), f"{fdate(rep, 'si')} · {DAYS_SI[rep.weekday()]}", font=si(48), fill=W, anchor="mm")
    dr.text((960, 990), "topgoviya.lk", font=mono(40), fill=LG, anchor="mm")
    return im


def mood_of(allr):
    mv = [r for r in allr if r["pct"] is not None]
    up = sum(r["pct"] >= 0.5 for r in mv); dn = sum(r["pct"] <= -0.5 for r in mv); same = len(mv) - up - dn
    avg = sum(max(-100, min(100, r["pct"])) for r in mv) / len(mv) if mv else 0
    title = "🔴 අද මිල වැඩි දිනයක්" if avg >= 3 else "🟢 අද මිල අඩු දිනයක්" if avg <= -3 else "🟡 අද සාමාන්‍ය දිනයක්"
    return title, up, dn, same, len(allr)


def mood_slide(rep, allr):
    im, dr = frame(rep)
    title, up, dn, same, n = mood_of(allr)
    word = title.split(" ", 1)[1]
    col = UP if title.startswith("🔴") else DN if title.startswith("🟢") else GOLD
    dr.ellipse((300, 300, 380, 380), fill=col)
    dr.text((420, 340), word, font=si(90), fill=PET, anchor="lm")
    tot = max(up + dn + same, 1); x = 300
    for cnt, c in ((up, UP), (same, (205, 191, 159)), (dn, DN)):
        w = int(1320 * cnt / tot)
        if w: dr.rectangle((x, 450, x + w, 520), fill=c)
        x += w
    for k, (lbl, cnt, c) in enumerate((("▲ ඉහළ ගියා", up, UP), ("■ වෙනසක් නැත", same, MUT), ("▼ පහළ ගියා", dn, DN))):
        cx = 300 + k * 520
        dr.text((cx, 600), f"{cnt}", font=mono(110), fill=c, anchor="lm")
        V.segs(dr, cx, 700, [(lbl[0] + " ", mono(40), c), (lbl[2:], si(42, "SemiBold"), MUT)])
    dr.text((960, 860), f"භාණ්ඩ {n}ක දඹුල්ල තොග මිල · පෙර දිනට සාපේක්ෂව", font=si(40, "Medium"), fill=MUT, anchor="mm")
    return im


def item_slide(rep, r, i, n):
    im, dr = frame(rep)
    V.photo_box(im, dr, r, (60, 200, 900, 960))
    dr.text((960, 190), f"{i} / {n}", font=mono(30), fill=MUT)
    f = si(130)
    while dr.textlength(r["si"], font=f) > 900 and f.size > 64:
        f = si(f.size - 6)
    dr.text((960, 225), r["si"], font=f, fill=PET)
    dr.text((965, 400), f"{r['en']} · {unit_si(r)}", font=si(34, "Medium"), fill=MUT)

    def box(x, label, val, col):
        dr.rounded_rectangle((x, 470, x + 420, 760), radius=26, fill=CARD, outline=LINE, width=3)
        dr.text((x + 210, 520), label, font=si(40, "SemiBold"), fill=MUT, anchor="mm")
        txt = f"{val:,.0f}"
        fs = mono(120)
        while dr.textlength(txt, font=fs) > 380:
            fs = mono(fs.size - 6)
        dr.text((x + 210, 650), txt, font=fs, fill=col, anchor="mm")
    box(960, "අවම", r["lo"], INK)
    box(1420, "උපරිම", r["hi"], GOLD)
    ar, col, bg = V.change_style(r["pct"])
    dr.rounded_rectangle((960, 800, 1840, 890), radius=20, fill=bg)
    if r["pct"] is None:
        V.segs(dr, 1400, 845, [(f"සාමාන්‍ය මිල රු. {r['mid']:,.0f}", si(34, "SemiBold"), col)], True)
    else:
        V.segs(dr, 1400, 845, [
            (ar + " ", mono(36), col),
            ("සාමාන්‍ය මිල පෙර දිනට ", si(34, "SemiBold"), col),
            (f"{r['pct']:+.0f}%  ", mono(36), col),
            (f"({r['prev']:,.0f} → {r['mid']:,.0f})", mono(32, "Medium"), col)], True)
    return im


def movers(allr, k=3):
    mv = [r for r in allr if r["pct"] is not None]
    ups = sorted([r for r in mv if r["pct"] >= 0.5], key=lambda r: -r["pct"])[:k]
    dns = sorted([r for r in mv if r["pct"] <= -0.5], key=lambda r: r["pct"])[:k]
    return ups, dns


def movers_slide(rep, allr):
    im, dr = frame(rep)
    dr.text((960, 225), "අද වැඩිම වෙනස්වීම් · භාණ්ඩ 90+ අතරින්", font=si(64), fill=PET, anchor="mm")
    ups, dns = movers(allr)
    for col_i, (lst, head, col, bg) in enumerate(((ups, "📈 ඉහළ ගිය", UP, UPBG), (dns, "📉 පහළ ගිය", DN, DNBG))):
        x0 = 100 + col_i * 880
        dr.text((x0, 320), head.split(" ", 1)[1], font=si(50), fill=col, anchor="lm")
        for k, r in enumerate(lst):
            y = 380 + k * 190
            dr.rounded_rectangle((x0, y, x0 + 840, y + 165), radius=24, fill=bg)
            nf = si(56)
            while dr.textlength(r["si"], font=nf) > 520 and nf.size > 34:
                nf = si(nf.size - 3)
            dr.text((x0 + 30, y + 55), r["si"], font=nf, fill=INK, anchor="lm")
            dr.text((x0 + 30, y + 120), f"{r['lo']:,.0f} – {r['hi']:,.0f}", font=mono(36, "Medium"), fill=MUT, anchor="lm")
            pt = f"{'▲' if r['pct'] > 0 else '▼'} {abs(r['pct']):.0f}%"
            dr.text((x0 + 810, y + 82), pt, font=mono(64), fill=col, anchor="rm")
        if not lst:
            dr.text((x0 + 30, 460), "විශාල වෙනසක් නැත", font=si(48), fill=MUT, anchor="lm")
    return im


def end_slide(rep):
    im = Image.new("RGB", (1920, 1080), PET); dr = ImageDraw.Draw(im)
    b = V.logo_badge(180); im.paste(b, (870, 80), b)
    dr.text((960, 360), "දඹුල්ල භාණ්ඩ 90+ ක අද මිල", font=si(80), fill=W, anchor="mm")
    dr.text((960, 470), "🛒 බාස්කට් එක · 🧮 ලාභ ගණකය · ⭐ මගේ භාණ්ඩ · නොමිලේ".replace("🛒 ", "").replace("🧮 ", "").replace("⭐ ", ""),
            font=si(44, "SemiBold"), fill=LG, anchor="mm")
    dr.rounded_rectangle((560, 560, 1360, 680), radius=60, fill=GOLD)
    dr.text((960, 620), "topgoviya.lk", font=mono(70), fill=W, anchor="mm")
    dr.text((960, 790), "Subscribe කරන්න · හෙට නැවත හමුවෙමු", font=si(48, "SemiBold"), fill=W, anchor="mm")
    dr.text((960, 960), "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.", font=si(34, "Medium"), fill=LG, anchor="mm")
    return im


def thumbnail(rep, allr):
    im = Image.new("RGB", (1280, 720), PET); dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, 1280, 120), fill=GOLD)
    dr.text((640, 60), f"{fdate(rep, 'si')} · {DAYS_SI[rep.weekday()]}", font=si(64), fill=W, anchor="mm")
    dr.text((640, 230), "අද දඹුල්ල", font=si(110), fill=W, anchor="mm")
    dr.text((640, 365), "තොග මිල", font=si(110), fill=LG, anchor="mm")
    ups, dns = movers(allr, 1)
    picks = [r for r in (ups[:1] + dns[:1]) if r]
    if not picks:
        picks = []
    y0 = 470 if len(picks) == 2 else 520
    for k, r in enumerate(picks):
        ar, col, bg = V.change_style(r["pct"])
        y = y0 + k * 120
        dr.rounded_rectangle((120, y, 1160, y + 105), radius=26, fill=bg)
        nf = si(64)
        while dr.textlength(r["si"], font=nf) > 640 and nf.size > 36:
            nf = si(nf.size - 3)
        dr.text((160, y + 52), r["si"], font=nf, fill=INK, anchor="lm")
        tt = f"{ar} {abs(r['pct']):.0f}%"
        dr.text((1120, y + 52), tt, font=mono(72), fill=col, anchor="rm")
    b = V.logo_badge(110); im.paste(b, (20, 140), b)
    return im


def text_file(rep, rows, allr):
    ups, dns = movers(allr)
    title_m, up, dn, same, n = mood_of(allr)
    t = f"දඹුල්ල එලවලු මිල අද {rep.strftime('%Y.%m.%d')} {DAYS_SI[rep.weekday()]} | දඹුල්ල ආර්ථික මධ්‍යස්ථානයේ තොග මිල | Dambulla Market Price"
    L = [f"TITLE:\n{t[:100]}", "", "DESCRIPTION:",
         f"අද දඹුල්ල එළවළු තොග මිල — {fdate(rep, 'si')} ({DAYS_SI[rep.weekday()]}).",
         f"{title_m.split(' ', 1)[1]}: භාණ්ඩ {up}ක් ඉහළ, {dn}ක් පහළ, {same}ක් වෙනසක් නැත.",
         "දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ තොග මිල පරාසය (අවම – උපරිම), රු.", ""]
    for r in rows:
        L.append(f"• {r['si']} — රු. {r['lo']:,.0f} – {r['hi']:,.0f}" + ("" if r["unit"] == "kg" else " (" + {"nut": "ගෙඩිය", "bundle": "මිටිය"}.get(r["unit"], "") + ")"))
    L.append("")
    for r in ups:
        L.append(f"📈 {r['si']}: රු. {r['lo']:,.0f}–{r['hi']:,.0f} (+{r['pct']:.0f}%)")
    for r in dns:
        L.append(f"📉 {r['si']}: රු. {r['lo']:,.0f}–{r['hi']:,.0f} (−{abs(r['pct']):.0f}%)")
    L += ["", "👉 දඹුල්ල භාණ්ඩ 90+ ක අද මිල, ප්‍රස්ථාර, 🛒 බාස්කට් එක හා 🧮 ලාභ ගණකය: https://topgoviya.lk",
          "📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය",
          "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.", "",
          "#දඹුල්ල #එළවළුමිල #තොගමිල #DambullaPrice #TopGoviyaLK #SriLanka", "",
          "TAGS (paste into the Tags box):",
          "දඹුල්ල එලවලු මිල අද, දඹුල්ල ආර්ථික මධ්‍යස්ථානයේ එළවළු මිල, දඹුල්ලේ එලවලු මිල, එලවලු මිල අද, "
          "දඹුල්ල එළවළු මිල, අද දඹුල්ල එළවළු මිල, දබුල්ල එලවලු මිල, dambulla market price today, dambulla vegetable price, "
          "dambulla price today, එළවළු මිල, අද එළවළු මිල, තොග මිල, elawalu mila, elawalu mila ada, vegetable price sri lanka, TopGoviya",
          "", "PLAYLIST:", "🥬 අද දඹුල්ල එළවළු මිල | Dambulla Market Price Daily",
          "", "SETTINGS:", "Category: Education · Video language: Sinhala · Location: Sri Lanka · Not made for kids"]
    return "\n".join(L) + "\n"


def script_file(rep, rows, allr):
    ups, dns = movers(allr, 2)
    title_m, up, dn, same, n = mood_of(allr)
    day = f"{MONTHS['si'][rep.month - 1]} {rep.day} {DAYS_SI[rep.weekday()]}"
    L = ["TopGoviya — දඹුල්ල වීඩියෝව කියවීමේ පිටපත (Reading script)", f"වාර්තා දිනය: {fdate(rep, 'si')}", "",
         f"[මාතෘකා පිටුව · තත්පර {SEC_TITLE}]",
         f"ආයුබෝවන්! TopGoviya අද දඹුල්ල එළවළු මිල. {day}, දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ තොග මිල.", "",
         f"[අද තත්ත්වය · තත්පර {SEC_MOOD}]",
         f"{title_m.split(' ', 1)[1]}. භාණ්ඩ {up}ක මිල ඉහළ ගියා, {dn}ක පහළ ගියා, {same}ක වෙනසක් නැහැ.", ""]
    t = []
    if ups: t.append("අද වැඩියෙන්ම ඉහළ ගියේ " + " සහ ".join(f"{r['si']} {abs(r['pct']):.0f}%" for r in ups) + ".")
    if dns: t.append("වැඩියෙන්ම අඩු වුණේ " + " සහ ".join(f"{r['si']} {abs(r['pct']):.0f}%" for r in dns) + ".")
    L += [f"[වැඩිම වෙනස්වීම් · තත්පර {SEC_MOVE}]", " ".join(t) or "අද විශාල මිල වෙනසක් නැහැ.", "",
          "දැන් ජනප්‍රිය එළවළු මිල බලමු.", ""]
    for i, r in enumerate(rows, 1):
        line = f"{r['si']}. රුපියල් {r['lo']:,.0f} සිට {r['hi']:,.0f} දක්වා."
        if r["pct"] is not None and abs(r["pct"]) >= 10:
            line += f" ඊයේට වඩා {abs(r['pct']):.0f}%කින් {'ඉහළයි' if r['pct'] > 0 else 'අඩුයි'}."
        L += [f"[{i} / {len(rows)} · තත්පර {SEC_ITEM}]", line, ""]
    L += [
          f"[අවසාන පිටුව · තත්පර {SEC_END}]",
          "දඹුල්ල භාණ්ඩ අනූවකට වැඩි ගණනක අද මිල, බාස්කට් එක හා ලාභ ගණකය topgoviya.lk වෙබ් අඩවියෙන් නොමිලේ බලන්න. "
          "මිල ගණන් මඟපෙන්වීමක් පමණි. Subscribe කරන්න, හෙට නැවත හමුවෙමු!"]
    return "\n".join(L) + "\n"


def main():
    days, names = load()
    if not days:
        print("need=no" if "--check" in sys.argv else "No data."); return
    last = max(days)
    import hashlib
    st = f"{last}_" + hashlib.sha1(json.dumps(days[last], sort_keys=True).encode()).hexdigest()[:8]
    done = os.path.exists(STATE) and open(STATE).read().strip() == st   # changes if prices are corrected
    if "--check" in sys.argv:
        print("need=" + ("no" if done else "yes")); return
    if done and "--force" not in sys.argv:
        print("Video for", last, "already made."); return
    if not features.check("raqm"):
        sys.exit("Sinhala text support (raqm) is missing. Stopping.")
    rep, rows, allr = build_rows(days, names)
    if len(rows) < 6:
        sys.exit("Too few items for the video.")
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "frames"); os.makedirs(tmp, exist_ok=True)
    slides = [(title_slide(rep), SEC_TITLE), (mood_slide(rep, allr), SEC_MOOD), (movers_slide(rep, allr), SEC_MOVE)]
    slides += [(item_slide(rep, r, i + 1, len(rows)), SEC_ITEM) for i, r in enumerate(rows)]
    slides += [(end_slide(rep), SEC_END)]
    lst = []
    for k, (im, sec) in enumerate(slides):
        p = os.path.join(tmp, f"s{k:02d}.png"); im.save(p)
        lst.append(f"file '{os.path.abspath(p)}'\nduration {sec}")
    lst.append(f"file '{os.path.abspath(p)}'")
    open(os.path.join(tmp, "list.txt"), "w").write("\n".join(lst) + "\n")
    iso = rep.isoformat()
    mp4 = os.path.join(OUT, f"dambulla-daily-{iso}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", os.path.join(tmp, "list.txt"), "-vf", "fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-movflags", "+faststart", mp4], check=True)
    total = sum(s for _, s in slides)
    try:
        track = short_kit.pick_track("music-5.wav", "music-2.wav", "music-4.wav")
        if track:
            V.add_music_loop(mp4, os.path.join(OUT, f"dambulla-daily-{iso}-music.mp4"), track, total)
    except Exception as e:
        print("Music step skipped:", e)
    thumbnail(rep, allr).save(os.path.join(OUT, f"dambulla-thumbnail-{iso}.png"))
    open(os.path.join(OUT, f"dambulla-youtube-{iso}.txt"), "w", encoding="utf-8").write(text_file(rep, rows, allr))
    open(os.path.join(OUT, f"dambulla-script-{iso}.txt"), "w", encoding="utf-8").write(script_file(rep, rows, allr))
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    open(STATE, "w").write(st)
    print(f"Made {mp4} ({total} seconds, {len(rows)} items) for {iso}")


if __name__ == "__main__":
    main()
