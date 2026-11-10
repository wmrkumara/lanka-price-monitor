"""
make_mw_video.py - "මගේ වගාව" app video with a Sinhala voice-over.

Reads mw_video/script.json (one line of speech per scene picture), makes the
voice with Microsoft's free Sinhala voices (Thilini = female, Sameera = male),
fits each scene to its voice line, adds optional soft music (mw_video/music.mp3)
and writes mw_out/mage-wagawa-video-<voice>.mp4 (1080x1920, 30 fps).

Run by .github/workflows/mw-video.yml. Test mode without internet:
    MW_FAKE_VOICE=1 python make_mw_video.py thilini
"""
import asyncio, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mw_video")
OUT = os.path.join(HERE, "mw_out")
VOICES = {"thilini": "si-LK-ThiliniNeural", "sameera": "si-LK-SameeraNeural"}
FPS = 30
LEAD = 0.45   # seconds of picture before the voice starts in each scene
TAIL = 0.65   # seconds of picture after the voice ends
FADE = 0.3
BG = "0x0a3b37"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        raise SystemExit("ffmpeg failed: " + " ".join(cmd[:6]))
    return r.stdout


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", path]).strip())


async def make_voice(text, voice, rate, path):
    if os.environ.get("MW_FAKE_VOICE"):          # offline test: silence sized to the text
        secs = max(1.0, len(text) * 0.07)
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
             f"sine=frequency=220:duration={secs}", "-af", "volume=0.05", path])
        return
    import edge_tts
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, voice, rate=rate).save(path)
            if os.path.getsize(path) > 1000:
                return
        except Exception as e:
            print("  voice retry", attempt + 1, e)
            await asyncio.sleep(3 + attempt * 3)
    raise SystemExit("Could not make the voice for: " + text)


def build(voice_key):
    cfg = json.load(open(os.path.join(SRC, "script.json"), encoding="utf-8"))
    scenes, rate = cfg["scenes"], cfg.get("rate", "-5%")
    min_s = float(cfg.get("min_seconds", 3.5))
    work = os.path.join(OUT, "work_" + voice_key)
    os.makedirs(work, exist_ok=True)
    voice = VOICES[voice_key]

    # 1) voice lines
    lines = []
    for i, s in enumerate(scenes):
        mp3 = os.path.join(work, f"v{i:02d}.mp3")
        print(f"[{voice_key}] voice {i + 1}/{len(scenes)}")
        asyncio.run(make_voice(s["say"], voice, rate, mp3))
        d = duration(mp3)
        lines.append((mp3, d, max(min_s, LEAD + d + TAIL)))

    # 2) one video file per scene (slow zoom + fade through the brand green)
    listfile = os.path.join(work, "list.txt")
    with open(listfile, "w") as lf:
        for i, (s, (_, _, sd)) in enumerate(zip(scenes, lines)):
            n = int(round(sd * FPS))
            tmp, seg = os.path.join(work, f"tmp_s{i:02d}.mp4"), os.path.join(work, f"s{i:02d}.mp4")
            vf = (f"loop=-1:1,trim=duration={sd:.3f},"
                  f"zoompan=z='1+0.035*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},"
                  f"fade=t=in:st=0:d={FADE}:color={BG},fade=t=out:st={sd - FADE:.3f}:d={FADE}:color={BG},format=yuv420p")
            run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(SRC, s["img"]),
                 "-vf", vf, "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
                 "-pix_fmt", "yuv420p", "-r", str(FPS), tmp])
            os.replace(tmp, seg)
            lf.write(f"file '{seg}'\n")
            print(f"[{voice_key}] scene {i + 1}/{len(scenes)}  {sd:.1f}s")
    silent = os.path.join(work, "silent.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", silent])
    total = duration(silent)

    # 3) voice track: each line placed at its scene start + LEAD
    inputs, parts, t = [], [], 0.0
    for i, (mp3, _, sd) in enumerate(lines):
        inputs += ["-i", mp3]
        ms = int((t + LEAD) * 1000)
        parts.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms}[a{i}]")
        t += sd
    mix = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(lines))) + \
        f"amix=inputs={len(lines)}:normalize=0,apad,atrim=0:{total:.3f}[voice]"
    music = os.path.join(SRC, "music.mp3")
    if os.path.exists(music):
        k = len(lines)
        inputs += ["-stream_loop", "-1", "-i", music]
        mix += (f";[{k}:a]aresample=44100,volume=0.12,atrim=0:{total:.3f},"
                f"afade=t=out:st={max(0, total - 2):.3f}:d=2[bgm];[voice][bgm]amix=inputs=2:normalize=0[out]")
        last = "[out]"
    else:
        last = "[voice]"
    voice_audio = os.path.join(work, "voice.m4a")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", mix, "-map", last,
         "-c:a", "aac", "-b:a", "160k", "-ac", "2", voice_audio])

    # 4) final file
    os.makedirs(OUT, exist_ok=True)
    final = os.path.join(OUT, f"mage-wagawa-video-{voice_key}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", voice_audio, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", final])
    print(f"DONE {final}  ({duration(final):.1f}s, {os.path.getsize(final) / 1e6:.1f} MB)")


if __name__ == "__main__":
    which = (sys.argv[1] if len(sys.argv) > 1 else "both").lower()
    for v in (["thilini", "sameera"] if which == "both" else [which]):
        build(v)
