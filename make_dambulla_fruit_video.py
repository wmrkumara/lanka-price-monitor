# TopGoviya.lk — Dambulla FRUIT price video (~2.5 minutes, 16:9) for YouTube — TEST: Monday / Wednesday / Friday
# Same data and look as make_dambulla_video.py (Dambulla DEC prices), but fruits only, with 2 animations:
#   pop-in  — the fruit photo grows in with a small bounce
#   count-up — the lowest / highest price counts up from 0
# Only fruits that have a photo in video-assets/crops/ get their own slide (all fruits still count in the summary).
# Makes, in folder dambulla_fruit_video/:
#   fruit-daily-YYYY-MM-DD.mp4 / -music.mp4   video (silent / with music)
#   fruit-thumbnail-YYYY-MM-DD.png            1280x720 YouTube thumbnail
#   fruit-youtube-YYYY-MM-DD.txt              title + description + tags + pinned comment
#   fruit-whatsapp-YYYY-MM-DD.txt             ready WhatsApp message
import json, os, subprocess, sys, hashlib
from datetime import date

OUT = "dambulla_fruit_video"
STATE = ".dambulla_fruit_last"
DAYS_ON = (0, 2, 4)          # report date Monday, Wednesday, Friday (manual "force" works any day)
SKIP_PIDS = {"75"}           # "Mango (other)" mixes many kinds; its price jumps are not a real change


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
    if date.fromisoformat(last).weekday() not in DAYS_ON:
        print("need=no"); return
    st = f"{last}_" + hashlib.sha1(json.dumps(days[last], sort_keys=True).encode()).hexdigest()[:8]
    done = os.path.exists(STATE) and open(STATE).read().strip() == st
    print("need=" + ("no" if done else "yes"))


if __name__ == "__main__" and "--check" in sys.argv:
    _quick_check()
    sys.exit(0)

from PIL import Image, ImageDraw, ImageOps, features
from build_pages import fdate
import make_daily_video as V
import make_dambulla_video as D
import short_kit

FRUITS = [  # (DEC product id, photo name) — popular order
    ("46", "coconut"), ("41", "banana-seeni"), ("44", "banana-ambul"), ("36", "papaya"),
    ("79", "king-coconut"), ("35", "watermelon"), ("38", "pineapple"), ("34", "guava"),
    ("71", "banana-kolikuttu"), ("40", "banana-ambun"), ("73", "mango-malu"), ("42", "mango-karthakolomban"),
    ("33", "avocado"), ("74", "mango-tjc"), ("72", "banana-rathambala"), ("43", "passion-fruit"),
    ("39", "wood-apple"), ("37", "soursop"), ("78", "bael"), ("77", "gooseberry-nelli"),
]
FPS = 30
SEC_TITLE, SEC_MOOD, SEC_ITEM, SEC_MOVE, SEC_END = 7, 9, 7, 10, 10
POP_SEC, COUNT_SEC = 0.6, 1.2          # animation lengths
si, mono = V.si, V.mono
PET, PETD, GOLD, LG, CREAM, CARD, INK, MUT, LINE, W = V.PET, V.PETD, V.GOLD, V.LG, V.CREAM, V.CARD, V.INK, V.MUT, V.LINE, V.W
UP, UPBG, DN, DNBG = V.UP, V.UPBG, V.DN, V.DNBG
DAYS_SI = V.DAYS_SI


def photo_path(name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        f = os.path.join(V.CROPS, name + ext)
        if os.path.exists(f):
            return f
    return None


def build(days, names):
    order = sorted(days)
    last, prev = order[-1], (order[-2] if len(order) > 1 else None)

    def item(pid):
        v = days[last].get(pid); m = names.get(pid)
        if not v or not m:
            return None
        mid = (v[0] + v[1]) / 2
        pm = None
        if prev and days[prev].get(pid):
            p = days[prev][pid]; pm = (p[0] + p[1]) / 2
        return dict(pid=pid, si=m["si"], en=m["en"], unit=m["unit"], lo=v[0], hi=v[1], mid=mid, prev=pm,
                    pct=(mid - pm) / pm * 100 if pm else None)
    fruit_ids = [k for k, m in names.items() if m.get("cat") == "f" and k not in SKIP_PIDS]
    allr = [r for r in (item(p) for p in fruit_ids) if r]
    rows = []
    for pid, photo in FRUITS:
        r = item(pid)
        if r and pid not in SKIP_PIDS and photo_path(photo):
            r["photo"] = photo
            rows.append(r)
    return date.fromisoformat(last), rows, allr


def frame(rep):
    im = Image.new("RGB", (1920, 1080), CREAM); dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, 1920, 150), fill=PET)
    b = V.logo_badge(110); im.paste(b, (40, 20), b)
    dr.text((175, 22), "දඹුල්ල තොග මිල · අද පලතුරු මිල", font=si(56), fill=W)
    dr.text((178, 96), "TopGoviya.lk", font=si(30, "SemiBold"), fill=LG)
    dr.rounded_rectangle((1440, 38, 1880, 112), radius=37, fill=GOLD)
    dr.text((1660, 75), fdate(rep, "si"), font=si(36), fill=W, anchor="mm")
    dr.rectangle((0, 150, 1920, 158), fill=GOLD)
    dr.rectangle((0, 1000, 1920, 1080), fill=PETD)
    dr.text((60, 1040), "මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · මිල ගණන් මඟපෙන්වීමක් පමණි",
            font=si(28, "Medium"), fill=W, anchor="lm")
    dr.text((1860, 1040), "topgoviya.lk", font=mono(36), fill=LG, anchor="rm")
    return im, dr


D.frame = frame   # the mood slide from the vegetable robot now uses the fruit header


def title_slide(rep):
    im = Image.new("RGB", (1920, 1080), PET); dr = ImageDraw.Draw(im)
    b = V.logo_badge(200); im.paste(b, (860, 100), b)
    dr.text((960, 410), "අද දඹුල්ල පලතුරු මිල", font=si(130), fill=W, anchor="mm")
    dr.text((960, 550), "දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · තොග මිල පරාසය", font=si(46, "SemiBold"), fill=LG, anchor="mm")
    dr.rounded_rectangle((560, 630, 1360, 730), radius=50, fill=GOLD)
    dr.text((960, 680), f"{fdate(rep, 'si')} · {DAYS_SI[rep.weekday()]}", font=si(48), fill=W, anchor="mm")
    dr.text((960, 990), "topgoviya.lk", font=mono(40), fill=LG, anchor="mm")
    return im


def movers_slide(rep, allr):
    im, dr = frame(rep)
    dr.text((960, 225), f"අද පලතුරු මිල වැඩිම වෙනස්වීම් · පලතුරු {len(allr)} අතරින්", font=si(60), fill=PET, anchor="mm")
    ups, dns = D.movers(allr)
    for col_i, (lst, head, col, bg) in enumerate(((ups, "ඉහළ ගිය", UP, UPBG), (dns, "පහළ ගිය", DN, DNBG))):
        x0 = 100 + col_i * 880
        dr.text((x0, 320), head, font=si(50), fill=col, anchor="lm")
        for k, r in enumerate(lst):
            y = 380 + k * 190
            dr.rounded_rectangle((x0, y, x0 + 840, y + 165), radius=24, fill=bg)
            nf = si(56)
            while dr.textlength(r["si"], font=nf) > 520 and nf.size > 34:
                nf = si(nf.size - 3)
            dr.text((x0 + 30, y + 55), r["si"], font=nf, fill=INK, anchor="lm")
            dr.text((x0 + 30, y + 120), f"{r['lo']:,.0f} – {r['hi']:,.0f}", font=mono(36, "Medium"), fill=MUT, anchor="lm")
            dr.text((x0 + 810, y + 82), f"{'▲' if r['pct'] > 0 else '▼'} {abs(r['pct']):.0f}%", font=mono(64), fill=col, anchor="rm")
        if not lst:
            dr.text((x0 + 30, 460), "විශාල වෙනසක් නැත", font=si(48), fill=MUT, anchor="lm")
    return im


def end_slide(rep):
    im = Image.new("RGB", (1920, 1080), PET); dr = ImageDraw.Draw(im)
    b = V.logo_badge(180); im.paste(b, (870, 80), b)
    dr.text((960, 360), "දඹුල්ල පලතුරු හා එළවළු අද මිල", font=si(76), fill=W, anchor="mm")
    dr.text((960, 470), "සම්පූර්ණ මිල වාර්තා බලන්න පිවිසෙන්න", font=si(50, "SemiBold"), fill=LG, anchor="mm")
    dr.rounded_rectangle((560, 560, 1360, 680), radius=60, fill=GOLD)
    dr.text((960, 620), "topgoviya.lk", font=mono(70), fill=W, anchor="mm")
    dr.text((960, 790), "Subscribe කරන්න · ඊළඟ පලතුරු මිල වීඩියෝවෙන් හමුවෙමු", font=si(44, "SemiBold"), fill=W, anchor="mm")
    D.add_subscribe(im, 200, (1560, 520))
    dr.text((960, 960), "මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.", font=si(34, "Medium"), fill=LG, anchor="mm")
    return im


# ---------- animated fruit slide ----------
BOX = (60, 200, 900, 960)


def photo_card(r):
    """The fruit photo cut to the rounded box (made once per fruit)."""
    x0, y0, x1, y1 = BOX
    w, h = x1 - x0, y1 - y0
    ph = ImageOps.fit(Image.open(photo_path(r["photo"])).convert("RGB"), (w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=30, fill=255)
    ph.putalpha(mask)
    return ph


def item_base(rep, r, i, n):
    """Everything on the slide except the photo and the two price numbers."""
    im, dr = frame(rep)
    dr.text((960, 190), f"{i} / {n}", font=mono(30), fill=MUT)
    f = si(130)
    while dr.textlength(r["si"], font=f) > 900 and f.size > 64:
        f = si(f.size - 6)
    dr.text((960, 225), r["si"], font=f, fill=PET)
    dr.text((965, 400), f"{r['en']} · {D.unit_si(r)}", font=si(34, "Medium"), fill=MUT)
    for x, label in ((960, "අවම"), (1420, "උපරිම")):
        dr.rounded_rectangle((x, 470, x + 420, 760), radius=26, fill=CARD, outline=LINE, width=3)
        dr.text((x + 210, 520), label, font=si(40, "SemiBold"), fill=MUT, anchor="mm")
    ar, col, bg = V.change_style(r["pct"])
    dr.rounded_rectangle((960, 800, 1840, 890), radius=20, fill=bg)
    if r["pct"] is None:
        V.segs(dr, 1400, 845, [(f"සාමාන්‍ය මිල රු. {r['mid']:,.0f}", si(34, "SemiBold"), col)], True)
    else:
        V.segs(dr, 1400, 845, [
            (ar + " ", mono(36), col),
            ("සාමාන්‍ය මිල පෙර වාර්තාවට ", si(34, "SemiBold"), col),
            (f"{r['pct']:+.0f}%  ", mono(36), col),
            (f"({r['prev']:,.0f} → {r['mid']:,.0f})", mono(32, "Medium"), col)], True)
    return im


def ease_back(x):     # grows a little past full size, then settles (the bounce)
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out(x):
    return 1 - (1 - x) ** 3


def item_frame(base, card, r, t):
    im = base.copy(); dr = ImageDraw.Draw(im)
    x0, y0, x1, y1 = BOX
    s = 0.45 + 0.55 * ease_back(min(t / POP_SEC, 1.0))
    w, h = max(1, int(card.width * s)), max(1, int(card.height * s))
    c = card.resize((w, h), Image.LANCZOS)
    im.paste(c, ((x0 + x1 - w) // 2, (y0 + y1 - h) // 2), c)
    k = ease_out(min(t / COUNT_SEC, 1.0))
    for x, val, col in ((960, r["lo"], INK), (1420, r["hi"], GOLD)):
        txt = f"{round(val * k):,.0f}"
        fs = mono(120)
        while dr.textlength(f"{val:,.0f}", font=fs) > 380:
            fs = mono(fs.size - 6)
        dr.text((x + 210, 650), txt, font=fs, fill=col, anchor="mm")
    return im


def thumbnail(rep, rows, allr):
    im = Image.new("RGB", (1280, 720), PET); dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, 1280, 120), fill=GOLD)
    dr.text((640, 60), f"{fdate(rep, 'si')} · {DAYS_SI[rep.weekday()]}", font=si(64), fill=W, anchor="mm")
    dr.text((460, 250), "අද දඹුල්ල", font=si(100), fill=W, anchor="mm")
    dr.text((460, 385), "පලතුරු මිල", font=si(100), fill=LG, anchor="mm")
    ups, dns = D.movers(allr, 1)
    pmap = {pid: ph for pid, ph in FRUITS if photo_path(ph)}
    pick = next((pmap[r["pid"]] for r in ups + dns if r["pid"] in pmap), rows[0]["photo"] if rows else None)
    if pick:   # photo of the biggest mover that has a photo
        ph = ImageOps.fit(Image.open(photo_path(pick)).convert("RGB"), (380, 344), Image.LANCZOS)
        m = Image.new("L", ph.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 379, 343), radius=28, fill=255)
        im.paste(ph, (870, 150), m)
    picks = [r for r in (ups[:1] + dns[:1]) if r]
    y0 = 520 if len(picks) == 2 else 560
    for k, r in enumerate(picks[:1] if len(picks) == 1 else picks):
        ar, col, bg = V.change_style(r["pct"])
        y = y0 + k * 92
        dr.rounded_rectangle((60, y, 1220, y + 82), radius=22, fill=bg)
        nf = si(54)
        while dr.textlength(r["si"], font=nf) > 760 and nf.size > 32:
            nf = si(nf.size - 3)
        dr.text((95, y + 41), r["si"], font=nf, fill=INK, anchor="lm")
        dr.text((1190, y + 41), f"{ar} {abs(r['pct']):.0f}%", font=mono(60), fill=col, anchor="rm")
    b = V.logo_badge(100); im.paste(b, (20, 135), b)
    return im


# ---------- YouTube / WhatsApp text ----------
TAG_LIST = [
    "dambulla fruit price today", "palathuru mila ada", "dambulla palathuru mila", "දඹුල්ල පලතුරු මිල",
    "පලතුරු මිල අද", "kesel mila", "banana price sri lanka", "අඹ මිල", "amba mila", "papaya price sri lanka",
    "pineapple price sri lanka", "coconut price today", "pol mila ada", "thambili price", "fruit price sri lanka",
    "dambulla market price today", "dambulla elawalu mila", "TopGoviya",
]


def make_tags():
    out = []
    for tag in TAG_LIST:
        if len(", ".join(out + [tag])) + 2 * len(out + [tag]) > 490:
            break
        out.append(tag)
    return ", ".join(out)


def make_title(rep):
    d, day = rep.strftime('%Y.%m.%d'), DAYS_SI[rep.weekday()]
    for t in (f"Palathuru Mila Ada | දඹුල්ල පලතුරු මිල අද {d} {day} | Dambulla Fruit Prices Today",
              f"Palathuru Mila Ada | දඹුල්ල පලතුරු මිල අද {d} {day} | Dambulla Fruit Price",
              f"Palathuru Mila Ada | දඹුල්ල පලතුරු මිල අද {d} {day}"):
        if len(t) <= 100:
            return t
    return t[:100]


def unit_note(r):
    return "" if r["unit"] == "kg" else " (" + {"nut": "ගෙඩිය", "bundle": "මිටිය"}.get(r["unit"], "") + ")"


def text_file(rep, rows, allr, pin):
    ups, dns = D.movers(allr)
    L = [f"TITLE:\n{make_title(rep)}", "", "DESCRIPTION:",
         f"Palathuru Mila Ada — දඹුල්ල පලතුරු මිල අද {rep.strftime('%Y.%m.%d')} ({DAYS_SI[rep.weekday()]})",
         f"Dambulla fruit prices today · kesel, amba, papol, annasi, pol, thambili mila — {fdate(rep, 'si')}.",
         "දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානයේ පලතුරු තොග මිල පරාසය (අවම – උපරිම), රු.", ""]
    for r in rows:
        L.append(f"• {r['si']} — රු. {r['lo']:,.0f} – {r['hi']:,.0f}{unit_note(r)}")
    L.append("")
    for r in ups:
        L.append(f"📈 {r['si']}: රු. {r['lo']:,.0f}–{r['hi']:,.0f} (+{r['pct']:.0f}%)")
    for r in dns:
        L.append(f"📉 {r['si']}: රු. {r['lo']:,.0f}–{r['hi']:,.0f} (−{abs(r['pct']):.0f}%)")
    L += ["", "👉 දඹුල්ල පලතුරු හා එළවළු 90+ ක අද මිල: https://topgoviya.lk",
          "📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය",
          "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ.", "",
          "#PalathuruMila #Dambulla #පලතුරුමිල #දඹුල්ල #FruitPrice #TopGoviyaLK", "",
          "TAGS (paste into the Tags box):", make_tags(),
          "", "PLAYLIST:", "🍌 දඹුල්ල පලතුරු මිල | Dambulla Fruit Price",
          "", "SETTINGS:", "Category: Education · Video language: Sinhala · Location: Sri Lanka · Not made for kids",
          "", "PINNED COMMENT (post it, then ⋮ → Pin):", pin]
    return "\n".join(L) + "\n"


def whatsapp_file(rep, allr):
    ups, dns = D.movers(allr, 2)
    L = ["(1) Upload the video to YouTube. (2) Replace VIDEO_ID below with the video's ID.",
         "(3) In WhatsApp paste the message, WAIT until the picture preview appears, then Send.",
         "-----", "https://youtu.be/VIDEO_ID", "",
         f"🍌 දඹුල්ල පලතුරු මිල අද — {fdate(rep, 'si')} ({DAYS_SI[rep.weekday()]})", ""]
    for r in ups:
        L.append(f"📈 {r['si']}: රු. {r['lo']:,.0f}–{r['hi']:,.0f}{unit_note(r)} (+{r['pct']:.0f}%)")
    for r in dns:
        L.append(f"📉 {r['si']}: රු. {r['lo']:,.0f}–{r['hi']:,.0f}{unit_note(r)} (−{abs(r['pct']):.0f}%)")
    L += ["", "👉 සම්පූර්ණ මිල වාර්තා බලන්න: https://topgoviya.lk",
          "📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය",
          "⚠️ මිල ගණන් මඟපෙන්වීමක් පමණි. ඔබේ තීරණ ඔබේ වගකීම වේ."]
    return "\n".join(L) + "\n"


def main():
    days, names = D.load()
    if not days:
        sys.exit("No data.")
    last = max(days)
    st = f"{last}_" + hashlib.sha1(json.dumps(days[last], sort_keys=True).encode()).hexdigest()[:8]
    done = os.path.exists(STATE) and open(STATE).read().strip() == st
    if done and "--force" not in sys.argv:
        print("Fruit video for", last, "already made."); return
    if not features.check("raqm"):
        sys.exit("Sinhala text support (raqm) is missing. Stopping.")
    rep, rows, allr = build(days, names)
    if len(rows) < 5:
        sys.exit(f"Only {len(rows)} fruits with photo and price today — too few for the video.")
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "frames"); os.makedirs(tmp, exist_ok=True)
    lst, total, k = [], 0.0, 0

    def add(im, sec):
        nonlocal k, total
        p = os.path.join(tmp, f"f{k:05d}.png"); im.save(p, compress_level=1); k += 1
        lst.append(f"file '{os.path.abspath(p)}'\nduration {sec:.5f}"); total += sec
        return p

    add(title_slide(rep), SEC_TITLE)
    add(D.mood_slide(rep, allr), SEC_MOOD)
    add(movers_slide(rep, allr), SEC_MOVE)
    n_anim = int(max(POP_SEC, COUNT_SEC) * FPS)
    for i, r in enumerate(rows, 1):
        base, card = item_base(rep, r, i, len(rows)), photo_card(r)
        for f in range(n_anim):
            add(item_frame(base, card, r, f / FPS), 1 / FPS)
        add(item_frame(base, card, r, 99), SEC_ITEM - n_anim / FPS)
    last_p = add(end_slide(rep), SEC_END)
    lst.append(f"file '{os.path.abspath(last_p)}'")
    open(os.path.join(tmp, "list.txt"), "w").write("\n".join(lst) + "\n")
    iso = rep.isoformat()
    mp4 = os.path.join(OUT, f"fruit-daily-{iso}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", os.path.join(tmp, "list.txt"), "-vf", "fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-movflags", "+faststart", mp4], check=True)
    try:
        track = short_kit.pick_track("music-5.wav", "music-2.wav", "music-4.wav")
        if track:
            V.add_music_loop(mp4, os.path.join(OUT, f"fruit-daily-{iso}-music.mp4"), track, total)
    except Exception as e:
        print("Music step skipped:", e)
    thumbnail(rep, rows, allr).save(os.path.join(OUT, f"fruit-thumbnail-{iso}.png"))
    ups, dns = D.movers(allr, 1)
    q = (f"\n💬 අද {ups[0]['si']} මිල ඉහළ ගියා. ඔබේ ප්‍රදේශයේ {ups[0]['si']} කීයද? රුපියල් ගාණ කමෙන්ට් කරන්න 👇" if ups else
         f"\n💬 අද {dns[0]['si']} මිල පහළ ගියා. ඔබේ ප්‍රදේශයේ කීයද? රුපියල් ගාණ කමෙන්ට් කරන්න 👇" if dns else "")
    pin = ("📌 දඹුල්ල පලතුරු මිල සඳහා Subscribe කරන්න 🔔\n"
           f"👉 සම්පූර්ණ මිල වාර්තා: https://topgoviya.lk/?d={iso}" + q +
           f"\n📊 මූලාශ්‍රය: දඹුල්ල විශේෂිත ආර්ථික මධ්‍යස්ථානය · {rep.strftime('%Y.%m.%d')}")
    open(os.path.join(OUT, f"fruit-youtube-{iso}.txt"), "w", encoding="utf-8").write(text_file(rep, rows, allr, pin))
    open(os.path.join(OUT, f"fruit-whatsapp-{iso}.txt"), "w", encoding="utf-8").write(whatsapp_file(rep, allr))
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    open(STATE, "w").write(st)
    print(f"Made {mp4} ({total:.0f} seconds, {len(rows)} fruits) for {iso}")


if __name__ == "__main__":
    main()
