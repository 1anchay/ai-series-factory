"""Narration generator. Edge Neural -> free local Piper -> explicitly opt-in eSpeak diagnostic.
An episode is never released silently if a requested voice cannot be generated.
"""
from __future__ import annotations
import asyncio
import os
import shutil
import subprocess
import urllib.request
import wave
from pathlib import Path
import numpy as np
SR=24000


def _wav(path):
    with wave.open(str(path),'rb') as f:
        channels=f.getnchannels();rate=f.getframerate();width=f.getsampwidth()
        data=f.readframes(f.getnframes())
    if width!=2 or rate!=SR:raise RuntimeError('WAV conversion failed')
    samples=np.frombuffer(data,dtype='<i2').astype(np.float32)/32768
    if channels>1:samples=samples.reshape(-1,channels).mean(axis=1)
    if len(samples)<SR//4:raise RuntimeError('Narration too short; speech synthesizer failed')
    return samples


def _convert(src,dst):
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(src),'-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(dst)]
    subprocess.run(cmd,check=True,timeout=100)
    return _wav(dst)


async def _edge_run(text,dst,voice,rate='-7%'):
    import edge_tts
    communicator=edge_tts.Communicate(text,voice,rate=rate,volume='+0%')
    await communicator.save(str(dst))


def _edge(text,tmp,idx,voice,rate='-7%'):
    mp3=tmp/f'edge_{idx:02d}.mp3'
    wav=tmp/f'edge_{idx:02d}.wav'
    asyncio.run(_edge_run(text,mp3,voice,rate))
    return _convert(mp3,wav)


def _piper(text,tmp,idx,model_root):
    name='ru_RU-irina-medium.onnx'
    model_root.mkdir(parents=True,exist_ok=True)
    base='https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/'
    for filename in [name,name+'.json']:
        target=model_root/filename
        if target.exists() and target.stat().st_size> (10_000_000 if filename==name else 100):continue
        url=base+filename+'?download=true'
        req=urllib.request.Request(url,headers={'User-Agent':'FrequencyZero-Studio/1.0'})
        with urllib.request.urlopen(req,timeout=90) as response, target.open('wb') as f:
            shutil.copyfileobj(response,f)
        if target.stat().st_size<(10_000_000 if filename==name else 100):
            raise RuntimeError(f'Invalid Piper voice: {filename}')
    wav=tmp/f'piper_{idx:02d}.wav'
    p=subprocess.run(['piper','--model',str(model_root/name),'--output_file',str(wav)],input=text+'\n',text=True,capture_output=True,timeout=180)
    if p.returncode or not wav.is_file():raise RuntimeError('Piper error '+p.stderr[-1000:])
    return _convert(wav,tmp/f'piper_norm_{idx:02d}.wav')


def _espeak(text,tmp,idx):
    wav=tmp/f'espeak_{idx:02d}.wav'
    subprocess.run(['espeak','-v','ru','-s','130','-p','40','-w',str(wav),text],check=True,timeout=60)
    return _convert(wav,tmp/f'espeak_norm_{idx:02d}.wav')


def synthesize(scenes,tmp,mode='auto',model_root=None):
    """Returns [(wave, backend)] and raises if any requested line is absent."""
    model_root=Path(model_root or 'voice_models')
    result=[]
    voice=os.environ.get('SERIES_EDGE_VOICE','ru-RU-SvetlanaNeural')
    for i,scene in enumerate(scenes):
        # Curated TTS wording can disambiguate stress without changing subtitles.
        # Example: scene['tts_text'] can spell out dates or replace an ambiguous word.
        text=scene.get('tts_text',scene['voice']).strip()
        speaker=scene.get('speaker','narrator')
        desired_voice='ru-RU-DmitryNeural' if speaker=='kir' else voice
        rate='-10%' if speaker in ('radio','kir') else '-7%'
        if not text:raise RuntimeError(f'Empty narration in scene {i+1}')
        candidates={'auto':['edge','piper'],'edge':['edge'],'piper':['piper'],'espeak':['espeak']}[mode]
        errors=[]
        for name in candidates:
            try:
                print(f'Narrating scene {i+1}/{len(scenes)} via {name}...',flush=True)
                if name=='edge':audio=_edge(text,tmp,i,desired_voice,rate)
                elif name=='piper':audio=_piper(text,tmp,i,model_root)
                else:audio=_espeak(text,tmp,i)
                rms=float(np.sqrt(np.mean(audio**2)))
                if rms<.004:raise RuntimeError('Voice file is effectively silent')
                # Consistent perceived loudness without clipping; preserve natural dynamics.
                gain=min(3., .15/max(rms,.0001))
                audio=np.tanh(audio*gain*.87).astype(np.float32)
                result.append((audio, name + ':' + (desired_voice if name=='edge' else 'local')))
                break
            except Exception as exc:
                errors.append(f'{name}: {exc}')
        else:
            raise RuntimeError('Failed to synthesize voice scene '+str(i+1)+'; '+' | '.join(errors))
    return result
