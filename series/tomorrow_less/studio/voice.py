"""Narration generator. Edge Neural -> free local Piper -> explicitly opt-in eSpeak diagnostic.
An episode is never released silently if a requested voice cannot be generated.
"""
from __future__ import annotations
import asyncio
import os
import time
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


def _piper(text,tmp,idx,model_root,speaker='narrator'):
    model_voice='dmitri' if speaker in ('mark','gleb','timur','lev','kir') else 'irina'
    name=f'ru_RU-{model_voice}-medium.onnx'
    model_root.mkdir(parents=True,exist_ok=True)
    base=f'https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/{model_voice}/medium/'
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
    """Return one coherent voice-engine mix, never random Edge/Piper switches per scene.

    In auto mode, every line is attempted using Edge Neural with a small retry.
    If any line fails, ALL lines are regenerated using local Piper (female Irina,
    male Dmitri). eSpeak remains explicitly diagnostic only.
    """
    model_root=Path(model_root or 'voice_models')
    female=os.environ.get('SERIES_EDGE_VOICE','ru-RU-SvetlanaNeural')

    def generate(backend):
        voices=[]
        for i,scene in enumerate(scenes):
            txt=scene.get('tts_text',scene['voice']).strip()
            if not txt:raise RuntimeError('Empty narration at scene '+str(i+1))
            sp=scene.get('speaker','narrator')
            male=sp in ('kir','mark','gleb','timur','lev')
            remote='ru-RU-DmitryNeural' if male else female
            rate='-11%' if sp in ('radio','kir','gleb') else ('-4%' if sp=='nika' else '+8%')
            tries=3 if backend=='edge' else 1
            last_error=None
            for attempt in range(tries):
                try:
                    print(f'Voice {i+1}/{len(scenes)} {backend} attempt {attempt+1}',flush=True)
                    if backend=='edge':samples=_edge(txt,tmp,i,remote,rate)
                    elif backend=='piper':samples=_piper(txt,tmp,i,model_root,sp)
                    elif backend=='espeak':samples=_espeak(txt,tmp,i)
                    else:raise ValueError('Unknown voice engine: '+backend)
                    rms=float(np.sqrt(np.mean(samples**2)))
                    if rms<.004:raise RuntimeError('Synthesized speech is effectively silent')
                    samples=np.tanh(samples*min(3.,.15/max(rms,.0001))*.87).astype(np.float32)
                    voices.append((samples,backend+':' + (remote if backend=='edge' else ('male' if male else 'female'))))
                    break
                except Exception as err:
                    last_error=err
                    if attempt+1<tries:time.sleep(.8 * 2**attempt)
            else:
                raise RuntimeError(f'{backend} failed for scene {i+1}: {last_error}')
        return voices

    if mode!='auto':return generate(mode)
    try:
        return generate('edge')
    except Exception as exc:
        print('EDGE unavailable for whole episode; resynthesizing ALL lines via Piper: '+str(exc),flush=True)
        return generate('piper')
