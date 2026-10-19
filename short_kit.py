"""
short_kit.py  -  shared helpers for the TopGoviya.lk Shorts robots
------------------------------------------------------------------
  add_music(...)    mix a background track into a finished (silent) video: fade in/out, cut to length
  CTA_CSS, cta(...) like / comment / share / follow box for the last slide (cream slide style)
  package(...)      ready-to-post folder: video-with-music.mp4, video-silent.mp4,
                    youtube.txt, tiktok.txt, facebook.txt
Used by make_short.py (spice roundup) and make_spice_cards.py (14 spice cards).
"""
import os, shutil, subprocess

MUSIC_VOL = 0.8


def pick_track(*names):
    """First music file that exists, e.g. pick_track('music-5.wav', 'music-4.wav')."""
    for n in names:
        p = n if "/" in n else os.path.join("music", n)
        if os.path.exists(p):
            return p
    return None


def add_music(silent, out, track, seconds):
    """Write `out` = `silent` video + background track. Returns True when music was added."""
    if not track:
        print("No music file - video stays silent"); shutil.copy(silent, out); return False
    af = (f"[1:a]atrim=0:{seconds:.2f},asetpts=PTS-STARTPTS,volume={MUSIC_VOL},"
          f"afade=t=in:st=0:d=1,afade=t=out:st={max(seconds - 2.0, 0):.2f}:d=2[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", track,
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    return True


CTA_CSS = """
.cta{margin-top:40px;background:#fffdf7;border:3px solid #0e4f4a;border-radius:26px;padding:6px 30px}
.ct{display:flex;align-items:center;gap:22px;padding:16px 0;font-size:38px;font-weight:700;color:#0e4f4a}
.ct+.ct{border-top:1px solid #e3d9c4}.ci{font-size:48px;width:64px;text-align:center}"""


def cta(comment, share, follow):
    items = [("👍", "ලයික් කරන්න"), ("💬", comment), ("📤", share), ("🔔", follow)]
    return '<div class="cta">' + "".join(f'<div class="ct"><span class="ci">{i}</span><span>{t}</span></div>'
                                         for i, t in items) + "</div>"


def youtube_text(title, desc, tags=None, playlist=None):
    """youtube.txt: everything for the upload screen, ready to copy."""
    t = f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n"
    if tags:
        out, used = [], 0
        for tag in tags:                                   # YouTube allows 500 characters of tags
            if used + len(tag) + 2 > 490:
                break
            out.append(tag); used += len(tag) + 2
        t += f"\nTAGS (paste into the Tags box):\n{', '.join(out)}\n"
    if playlist:
        t += f"\nPLAYLIST:\n{playlist}\n"
    t += "\nSETTINGS:\nCategory: Education · Video language: Sinhala · Location: Sri Lanka · Not made for kids\n"
    return t


def package(folder, silent, track, seconds, title, desc, tiktok, facebook, tags=None, playlist=None):
    """Make the ready-to-post folder from a silent video and the caption texts."""
    os.makedirs(folder, exist_ok=True)
    shutil.copy(silent, f"{folder}/video-silent.mp4")
    add_music(silent, f"{folder}/video-with-music.mp4", track, seconds)
    open(f"{folder}/youtube.txt", "w", encoding="utf-8").write(youtube_text(title, desc, tags, playlist))
    open(f"{folder}/tiktok.txt", "w", encoding="utf-8").write(tiktok.rstrip() + "\n")
    open(f"{folder}/facebook.txt", "w", encoding="utf-8").write(facebook.rstrip() + "\n")
    print("Ready-to-post folder:", folder)
