"""
voice_test.py  -  TopGoviya.lk Sinhala voice-over TEST (free)
-------------------------------------------------------------
Reads the same short Dambulla script with Microsoft's two Sinhala neural voices
(Sameera = male, Thilini = female) and saves MP3 files to voice_test/.
Run by the "Sinhala voice test" robot; download the files from Artifacts and listen.
Uses the free edge-tts library (test only). For daily use, the same voices are
available officially through Azure Speech (free monthly allowance).
"""
import asyncio, os
import edge_tts

SCRIPT = ("අද දඹුල්ල එළවළු තොග මිල. ඔක්තෝබර් විසිතුන. අද සාමාන්‍ය දිනයක්. "
          "තක්කාලි කිලෝවක් රුපියල් තුන්සිය තිහේ සිට හාරසියය දක්වා. "
          "බෝංචි තුන්සිය පනහේ සිට හාරසියය දක්වා. "
          "අමු මිරිස් එකසිය අසූවේ සිට දෙසිය පනහ දක්වා. "
          "අද වැඩිම ඉහළ ගියේ චව් චව්, සියයට හැටනවයකින්. "
          "සියලු මිල ටොප්ගොවිය ඩොට් එල්කේ.")
# same script with numbers as digits, to hear how the voice reads them
SCRIPT_DIGITS = ("අද දඹුල්ල එළවළු තොග මිල. ඔක්තෝබර් 23. "
                 "තක්කාලි කිලෝවක් රුපියල් 330 සිට 400 දක්වා. බෝංචි රුපියල් 350 සිට 400 දක්වා.")
VOICES = {"male-sameera": "si-LK-SameeraNeural", "female-thilini": "si-LK-ThiliniNeural"}


async def main():
    os.makedirs("voice_test", exist_ok=True)
    for name, voice in VOICES.items():
        for tag, text in (("words", SCRIPT), ("digits", SCRIPT_DIGITS)):
            out = f"voice_test/{name}-{tag}.mp3"
            await edge_tts.Communicate(text, voice, rate="-5%").save(out)
            print("Saved", out)


asyncio.run(main())
