#!/usr/bin/env python3
"""Director's tests for the SELECTED Silero voice: Aidar.
No cloning, no substitutions to another voice, no music masking.
"""
from __future__ import annotations
import json, re, wave, subprocess
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
import torch

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"aidar_directed_tests"
MODEL=Path("/tmp/v5_6_ru.pt")
URL="https://models.silero.ai/models/tts/ru/v5_6_ru.pt"
SR=48000
BASE=("В три двенадцать в подъезде погасли все лампы. "
      "Потом на первом этаже раздались шаги. "
      "Но камеры показывали пустую лестницу. "
      "И тогда я услышал голос из своей кухни: "
      "«Не открывай дверь. Он уже внутри».")
# + before the vowel receiving stress; the transcript remains unmodified for captions.
MARKED=("В три двен+адцать в подъезде пог+асли все л+ампы. "
        "Потом на первом этаж+е раздал+ись шаг+и. "
        "Но к+амеры пок+азывали пуст+ую л+естницу. "
        "И тогда я усл+ышал голос из сво+ей к+ухни. "
        "Не открыв+ай дверь. Он уж+е внутр+и.")
PHRASES=[
    ("В три двен+адцать в подъезде пог+асли все л+ампы.", 0.23),
    ("Потом на первом этаж+е раздал+ись шаг+и.", 0.25),
    ("Но к+амеры пок+азывали пуст+ую л+естницу.", 0.38),
    ("И тогда я усл+ышал голос из сво+ей к+ухни.", 0.42),
    ("Не открыв+ай дверь.", 0.33),
    ("Он уж+е внутр+и.", 0.0)
]
SSML=(
 '<speak><s>В три двен+адцать в подъезде пог+асли все л+ампы.</s>'
 '<break time="260ms"/>'
 '<s>Потом на первом этаж+е раздал+ись шаг+и.</s>'
 '<break time="290ms"/>'
 '<s>Но к+амеры пок+азывали пуст+ую л+естницу.</s>'
 '<break time="420ms"/>'
 '<s>И тогда я усл+ышал голос из сво+ей к+ухни.</s>'
 '<break time="450ms"/>'
 '<prosody rate="slow">Не открыв+ай дверь.</prosody>'
 '<break time="340ms"/>'
 '<prosody pitch="low">Он уж+е внутр+и.</prosody></speak>'
)
def synth(model, *, text=None, ssml_text=None):
    with torch.inference_mode():
        kwargs={"speaker":"aidar","sample_rate":SR}
        if ssml_text is not None:kwargs["ssml_text"]=ssml_text
        else:kwargs["text"]=text
        a=model.apply_tts(**kwargs)
        result=np.asarray(a.detach().cpu().numpy() if hasattr(a,"detach") else a,dtype=np.float32).reshape(-1)
        if len(result)<SR//4 or not np.all(np.isfinite(result)):
            raise RuntimeError("Silero produced invalid audio")
        return result

def save(name,a):
    path=OUT/(name+".wav")
    # gentle fades only; never pitch-shift the voice afterward
    a=a.copy()
    fade=min(len(a)//2,int(.035*SR))
    a[:fade]*=np.linspace(0,1,fade,dtype=np.float32)
    a[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes(np.int16(np.clip(a,-1,1)*32767).tobytes())
    mp3=OUT/(name+".mp3")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(path),
                    "-af","loudnorm=I=-17:TP=-1.5:LRA=11","-c:a","libmp3lame",
                    "-b:a","160k",str(mp3)],check=True)
    path.unlink()
    return mp3,round(len(a)/SR,2)

def main():
    OUT.mkdir(exist_ok=True)
    torch.set_num_threads(3)
    if not MODEL.exists():
        torch.hub.download_url_to_file(URL,str(MODEL),progress=False)
    if MODEL.stat().st_size<15_000_000:raise RuntimeError("Missing official model")
    model=torch.package.PackageImporter(str(MODEL)).load_pickle("tts_models","model")
    model.to(torch.device("cpu"))
    examples=[
        ("01_original_aidar",synth(model,text=BASE),"Original text"),
        ("02_stress_punctuation",synth(model,text=MARKED),"Corrected stress + punctuation"),
    ]
    # SSML can have varying syntax in model releases. It must work, no silent substitutions.
    examples.append(("03_directed_ssml",synth(model,ssml_text=SSML),"SSML timing and prosody"))
    # Phrase-based control is a second robust route for exact silences.
    segmented=[]
    for text,pause in PHRASES:
        segmented.append(synth(model,text=text))
        if pause: segmented.append(np.zeros(int(SR*pause),dtype=np.float32))
    examples.append(("04_directed_phrases",np.concatenate(segmented),"Precise pauses and stress"))
    report=[]
    for name,a,description in examples:
        p,duration=save(name,a)
        print("MADE",name,duration,"s",p.stat().st_size,"bytes",flush=True)
        if duration<7:raise RuntimeError("Very short sample")
        report.append(dict(file=p.name,description=description,duration_seconds=duration,voice="aidar"))
    (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    (OUT/"display_text.txt").write_text(BASE,encoding="utf8")
    (OUT/"direction_notes.txt").write_text(
        "1. Original aidar, control.\n2. Human-corrected stress and punctuation.\n"
        "3. SSML with targeted suspense pauses and slower warning.\n"
        "4. Per-phrase narration with exact silences; no alternate TTS.\n"
        "Stress uses '+' BEFORE stressed vowel; display captions use unmarked Russian.\n",encoding="utf8")
if __name__=="__main__":main()
