#!/usr/bin/env python3
"""Voice casting for an original Russian suspense narrator.
STRICT: no Piper/espeak fallback; each file MUST be genuine Edge Neural speech.
The source video is used only as an artistic reference, never copied.
"""
import asyncio, json, subprocess, tempfile
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"auditions"
SAMPLE=("В три двенадцать в подъезде погасли все лампы. "
        "Потом на первом этаже раздались шаги. "
        "Но камеры показывали пустую лестницу. "
        "И тогда я услышал голос из своей кухни: "
        "«Не открывай дверь. Он уже внутри».")
VERSIONS=[
    dict(key="01_dmitry_natural",voice="ru-RU-DmitryNeural",rate="-2%",pitch="-4Hz",volume="+0%"),
    dict(key="02_dmitry_suspense",voice="ru-RU-DmitryNeural",rate="-10%",pitch="-12Hz",volume="+0%"),
    dict(key="03_svetlana_low",voice="ru-RU-SvetlanaNeural",rate="-7%",pitch="-11Hz",volume="+0%"),
]
async def one(item):
    dest=OUT/(item["key"]+".mp3")
    err=None
    for attempt in range(3):
        try:
            if dest.exists():dest.unlink()
            c=edge_tts.Communicate(SAMPLE, voice=item["voice"], rate=item["rate"], pitch=item["pitch"], volume=item["volume"])
            await c.save(str(dest))
            if not dest.exists() or dest.stat().st_size<8000: raise RuntimeError("Empty or tiny audio output")
            p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(dest)],capture_output=True,text=True,check=True)
            duration=float(p.stdout.strip())
            if duration<7: raise RuntimeError("Unexpectedly short speech: "+str(duration))
            print(item["key"],round(duration,2),"sec",dest.stat().st_size,"bytes",flush=True)
            return dict(item,seconds=duration,status="ok")
        except Exception as ex:
            err=str(ex);print("Try",attempt+1,item["key"],err[:300],flush=True)
            await asyncio.sleep(attempt+1)
    raise RuntimeError("Edge TTS failed, no voice substitution: "+str(err))
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    print("Edge TTS version",getattr(edge_tts,"__version__","unknown"))
    results=[]
    for item in VERSIONS:
        results.append(await one(item))
    (OUT/"voices.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/"transcript.txt").write_text(SAMPLE,encoding="utf-8")
if __name__=="__main__":
    asyncio.run(main())
