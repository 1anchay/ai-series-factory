#!/usr/bin/env python3
"""Test modern OFFLINE Russian neural voices (Silero v5.6).
No Piper/espeak fallback. Original narrator tones, no identity cloning.
"""
from pathlib import Path
import json, subprocess, wave
import numpy as np
import torch
OUT=Path(__file__).resolve().parent/"silero_auditions"
MODEL=Path("/tmp/v5_6_ru.pt")
URL="https://models.silero.ai/models/tts/ru/v5_6_ru.pt"
TEXT=("В три двенадцать в подъезде погасли все лампы. "
      "Потом на первом этаже раздались шаги. "
      "Но камеры показывали пустую лестницу. "
      "И тогда я услышал голос из своей кухни. "
      "Не открывай дверь. Он уже внутри.")
VOICES=[("01_aidar","aidar"),("02_eugene","eugene"),("03_baya","baya")]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(3)
    if not MODEL.exists():
        print("Downloading official Silero v5_6 Russian model",flush=True)
        torch.hub.download_url_to_file(URL,str(MODEL),progress=True)
    print("Model bytes",MODEL.stat().st_size,flush=True)
    if MODEL.stat().st_size<15000000: raise RuntimeError("Download too small")
    model=torch.package.PackageImporter(str(MODEL)).load_pickle("tts_models","model")
    model.to(torch.device("cpu"))
    result=[]
    for name,speaker in VOICES:
        print("Synthesizing",speaker,flush=True)
        audio=model.apply_tts(text=TEXT,speaker=speaker,sample_rate=48000)
        samples=np.asarray(audio.detach().cpu().numpy() if hasattr(audio,"detach") else audio,dtype=np.float32)
        if len(samples)<48000*6:raise RuntimeError("Empty or implausibly short voice: "+speaker)
        wav=OUT/(name+".wav")
        with wave.open(str(wav),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
            f.writeframes(np.int16(np.clip(samples,-1,1)*32767).tobytes())
        mp3=OUT/(name+".mp3")
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(wav),
                        "-af","loudnorm=I=-16:TP=-1.5:LRA=9",
                        "-c:a","libmp3lame","-b:a","160k",str(mp3)],check=True)
        wav.unlink()
        print("Created",name,len(samples)/48000,mp3.stat().st_size,flush=True)
        result.append({"id":name,"voice":speaker,"seconds":round(len(samples)/48000,2)})
    (OUT/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/"transcript.txt").write_text(TEXT,encoding="utf-8")
if __name__=="__main__":main()
