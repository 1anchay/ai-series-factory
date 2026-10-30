#!/usr/bin/env python3
"""Original Russian horror audio drama: original score, Foley, Edge TTS voice.
No sounds, melodies or voice recordings copied from the user's reference.
"""
from __future__ import annotations
import argparse, json, math, subprocess, tempfile, time, wave, shutil, urllib.request
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.ndimage import uniform_filter1d

HERE=Path(__file__).parent
SR=24000
RNG=np.random.default_rng(22061)

def call(*cmd):
    p=subprocess.run(cmd,check=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(' '.join(map(str,cmd[:4]))+' failed: '+p.stderr.decode(errors='replace')[-900:])
    return p

def read_wav(path):
    with wave.open(str(path),'rb') as f:
        assert f.getsampwidth()==2, 'expected PCM16'
        data=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768
        nch=f.getnchannels()
    return data.reshape(-1,nch).mean(axis=1) if nch>1 else data

def voice_line(txt, path, voice, rate, pitch):
    # Independent generic synthesized narrator; deliberately not a clone of a real person.
    for trial in range(1,4):
        p=subprocess.run(['edge-tts','--voice',voice,f'--rate={rate}',f'--pitch={pitch}','--text',txt,'--write-media',str(path.with_suffix('.mp3'))],
                         capture_output=True,text=True,timeout=80)
        if p.returncode==0 and path.with_suffix('.mp3').exists() and path.with_suffix('.mp3').stat().st_size>1000:break
        if trial==3:raise RuntimeError('Edge neural narration failed: '+p.stderr[-800:])
        time.sleep(trial*2)
    call('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(path.with_suffix('.mp3')),
         '-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(path))
    x=read_wav(path)
    mask=np.where(np.abs(x)>.006)[0]
    if len(mask):
        lo=max(0,mask[0]-round(.08*SR)); hi=min(len(x),mask[-1]+round(.15*SR))
        x=x[lo:hi]
    if len(x)==0:raise RuntimeError('Empty voice clip after synthesis')
    return x

def piper_voice(txt,path,female=False):
    """Consistent free offline neural fallback. No voice cloning."""
    name='irina' if female else 'dmitri'
    model_dir=HERE/'voice_models';model_dir.mkdir(exist_ok=True)
    base=f'https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/{name}/medium/'
    filename=f'ru_RU-{name}-medium.onnx'
    for part in (filename,filename+'.json'):
        dest=model_dir/part
        minimum=10_000_000 if part==filename else 100
        if not dest.exists() or dest.stat().st_size<minimum:
            print('Download Piper model:',part,flush=True)
            request=urllib.request.Request(base+part+'?download=true',headers={'User-Agent':'HorrorAudioStudio/1.0'})
            with urllib.request.urlopen(request,timeout=120) as r, dest.open('wb') as f:
                shutil.copyfileobj(r,f)
            if dest.stat().st_size<minimum:raise RuntimeError('Downloaded Piper model is incomplete')
    raw=path.with_name(path.stem+'_raw.wav')
    p=subprocess.run(['piper','--model',str(model_dir/filename),'--output_file',str(raw)],input=txt+'\n',text=True,capture_output=True,timeout=180)
    if p.returncode or not raw.exists():raise RuntimeError('Piper failed: '+p.stderr[-1000:])
    call('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(raw),'-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(path))
    x=read_wav(path)
    if len(x)<SR//2:raise RuntimeError('Piper returned empty or very short speech')
    return x

def highpass(x, cutoff=75):return sosfilt(butter(2,cutoff,btype='highpass',fs=SR,output='sos'),x).astype(np.float32)
def lowpass(x, cutoff=2500):return sosfilt(butter(2,cutoff,btype='lowpass',fs=SR,output='sos'),x).astype(np.float32)
def rms(x):return float(np.sqrt(np.mean(np.square(x),dtype=np.float64))) if len(x) else 0.

def master_voice(x, role='narrator'):
    x=highpass(x,85)
    env=np.sqrt(uniform_filter1d(x*x,size=1200)+1e-8)
    # Smooth, gentle dynamics control: avoid harsh robotic artifacts.
    reduction=np.minimum(1.,(0.15/np.maximum(.15,env))**.52)
    x=x*reduction
    if role=='intercom':
        x=lowpass(highpass(x,280),2550)
        x=np.tanh(x*2.0)*.54
        delay=round(.055*SR)
        copy=np.zeros_like(x);copy[delay:]=x[:-delay]
        x=x+.23*copy
        return x.astype(np.float32)
    scale=min(2.0, .155/max(.035,rms(x)))
    return np.tanh(x*scale*.92).astype(np.float32)*.73

def add(track, signal, at, gain=1., pan=0.):
    a=int(max(0,at)*SR)
    if a>=len(track):return
    n=min(len(signal),len(track)-a)
    if n<1:return
    # Constant power panning. Stereo is 2 channels.
    l=np.sqrt((1-pan)/2);r=np.sqrt((1+pan)/2)
    track[a:a+n,0]+=signal[:n]*gain*l
    track[a:a+n,1]+=signal[:n]*gain*r

def fade(x,attack=.01,release=.08):
    n=len(x);a=min(int(attack*SR),n//2);r=min(int(release*SR),n//2)
    x=x.copy()
    if a:x[:a]*=np.linspace(0,1,a)
    if r:x[-r:]*=np.linspace(1,0,r)
    return x

def tonal(freq,duration,amp=.1,vibrato=0.006,decay=0.):
    t=np.arange(int(SR*duration),dtype=np.float32)/SR
    phase=2*np.pi*(freq*t+(vibrato*freq/.48)*np.sin(.48*t))
    y=np.sin(phase)+.17*np.sin(2.002*phase)+.075*np.sin(3.007*phase)
    if decay:y*=np.exp(-decay*t)
    return fade((amp*y).astype(np.float32),.02,min(.19,duration*.25))

def chime(freq,duration=.95,amp=.10):
    t=np.arange(int(SR*duration),dtype=np.float32)/SR
    env=(1-np.exp(-20*t))*np.exp(-t*3.15)
    y=np.sin(2*np.pi*freq*t)+.24*np.sin(2*np.pi*freq*2.07*t)+.13*np.sin(2*np.pi*freq*2.91*t)
    return (amp*y*env).astype(np.float32)

def thump(freq=70,duration=1.05,amp=.30):
    t=np.arange(int(SR*duration),dtype=np.float32)/SR
    phase=2*np.pi*(freq*t + (1-np.exp(-13*t))*3.2)
    grain=RNG.standard_normal(len(t)).astype(np.float32)
    return (amp*(np.sin(phase)*np.exp(-5.5*t)+.14*grain*np.exp(-33*t))).astype(np.float32)

def click(amp=.12,duration=.16):
    t=np.arange(int(SR*duration),dtype=np.float32)/SR
    noise=RNG.standard_normal(len(t)).astype(np.float32)
    return (amp*lowpass(noise,2800)*np.exp(-38*t)).astype(np.float32)

def footstep():
    n=int(.25*SR);t=np.arange(n,dtype=np.float32)/SR
    body=np.sin(2*np.pi*(80-25*t)*t)*np.exp(-20*t)
    texture=lowpass(RNG.standard_normal(n).astype(np.float32),700)*np.exp(-32*t)
    return (.19*body+.055*texture).astype(np.float32)

def door_creak(duration=1.4):
    t=np.arange(int(SR*duration),dtype=np.float32)/SR
    hz=170+85*t+31*np.sin(t*15)
    phase=np.cumsum(hz)/SR*2*np.pi
    return (.055*np.sin(phase)*(np.sin(np.pi*np.clip(t/duration,0,1))**1.5)).astype(np.float32)

def windy(duration):
    n=int(SR*duration);t=np.arange(n,dtype=np.float32)/SR
    z=RNG.standard_normal(n).astype(np.float32)
    low=lowpass(z,200)
    return (.065*low*(.5+.25*np.sin(t*.54)+.12*np.sin(t*1.83))).astype(np.float32)

def radio_noise(duration=.8):
    n=int(SR*duration);t=np.arange(n,dtype=np.float32)/SR
    noise=RNG.standard_normal(n).astype(np.float32)
    band=lowpass(highpass(noise,500),4000)
    gate=(.62+.38*np.sign(np.sin(2*np.pi*13*t)))
    return (.105*band*gate).astype(np.float32)

def raise_tension(duration):
    n=int(duration*SR);t=np.arange(n,dtype=np.float32)/SR
    u=t/max(.01,duration)
    r=RNG.standard_normal(n).astype(np.float32)
    p=lowpass(highpass(r,90),550)
    return (p*(.008+.060*u*u)).astype(np.float32)

def sfx_event(name, bed,at,scene_index=0):
    if name in ('wind','silence'):return
    if name in ('breaker','switch','lamp','cable','power_down'):
        add(bed,click(.16),at,.7,(-.3 if scene_index%2 else .3))
        if name in ('breaker','power_down'):add(bed,thump(62,.70,.22),at+.055,.5,-.15)
    elif name in ('footsteps','steps_three'):
        count=3 if name=='steps_three' else 4
        for k in range(count): add(bed,footstep(),at+k*.68,.75,.45-.28*k)
    elif name=='knock_three':
        for k in range(3):
            add(bed,thump(90,.38,.29),at+k*.52,.70,-.40)
            add(bed,click(.11),at+k*.52+.015,.65,-.40)
    elif name=='phone':add(bed,chime(784,.30,.13),at,.9,.75)
    elif name in ('static','radio_noise'):
        add(bed,radio_noise(1.0),at,.75,.4)
    elif name=='intercom':
        add(bed,click(.22),at,1.,.60)
        add(bed,chime(670,.64,.10),at+.12,.7,.60)
    elif name=='drip':
        for k in range(4):add(bed,chime(730+k*62,.21,.055),at+k*.65,.6,(-.4+.3*k))
    elif name=='glass':
        for k in range(3):add(bed,chime(690+k*57,1.1,.05),at+k*.22,.62,-.18)
    elif name=='cloth':add(bed,lowpass(RNG.standard_normal(round(.5*SR)).astype(np.float32),850)*.06,at,.3,.15)
    elif name=='hum_rise':add(bed,raise_tension(2.3),at,.56,0)
    elif name=='buzz':add(bed,tonal(53,2.1,.045),at,.8,-.3)
    elif name in ('sub_hit','final_hit'):
        add(bed,thump(51,1.4,.35),at,.82,0)
    elif name=='alarm':
        for k in range(2):add(bed,chime(1035,.48,.12),at+k*.62,.76,.35)

def make_music(seconds):
    n=int(SR*seconds)
    t=np.arange(n,dtype=np.float32)/SR
    music=np.zeros((n,2),dtype=np.float32)
    # Original four-note motif, not copied from any reference soundtrack.
    # D - Eb - Ab - Cb: unstable, sparse, with a low unresolved pedal.
    drone=tonal(36.708,seconds,.018,decay=0)[:n]
    wobble=np.sin(2*np.pi*(55*t+.35*np.sin(t*.16)))*.015
    base=(drone+wobble).astype(np.float32)
    add(music,base,0,1,0)
    motifs=[(0,146.832,0.06,-.6),(7,155.563,.05,.4),(14,207.652,.045,-.1),
            (22,123.47,.045,.6),(31,146.832,.043,-.5),(42,155.563,.039,.3),
            (51,207.652,.047,-.3),(62,123.47,.052,.6),(73,146.832,.049,-.4),
            (81,155.563,.057,.4),(91,207.652,.060,-.2)]
    for at,f,gain,pan in motifs:
        if at<seconds:add(music,chime(f,3.8,.13),at,gain*11,pan)
    # Slow original brass/strings swell: no identifiable borrowed melody.
    for at in np.arange(18,seconds,19):
        add(music,tonal(92.5,5.0,.06,decay=.12),at,.23,-.4)
        add(music,tonal(129.5,5.1,.04,decay=.16),at+.25,.22,.35)
    if seconds>25:add(music,raise_tension(min(20,seconds*.26)),max(0,seconds-20),.52,0)
    return music

def mix_episode(doc, mode, outdir,voice='ru-RU-DmitryNeural',rate='-8%',pitch='-8Hz'):
    scenes=doc['scenes'];outdir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d)
        narration=[];durations=[]
        # The entire episode uses ONE voice engine. If online Edge fails, all
        # lines are re-rendered with free local Piper Dmitri / Irina.
        speech=[]
        if mode=='full' and voice=='silero-aidar':
            from silero_voice import AidarVoice
            aidar=AidarVoice()  # loaded once per entire episode
            for scene in scenes:
                speech.append(aidar.speak(scene,output_rate=SR))
            engine='Silero-Aidar-v5.6'
        elif mode=='full':
            try:
                print('Trying Edge neural voice:',voice,flush=True)
                for i,scene in enumerate(scenes):
                    speech.append(voice_line(scene['text'],tmp/f'voice_{i:02d}.wav',voice,rate,pitch))
                engine='Edge'
            except Exception as exc:
                print('Edge unavailable; resynthesizing all lines with offline Piper:',str(exc)[-260:],flush=True)
                speech=[]
                female=('Svetlana' in voice or 'Irina' in voice)
                for i,scene in enumerate(scenes):
                    speech.append(piper_voice(scene['text'],tmp/f'piper_{i:02d}.wav',female=female))
                engine='Piper'
        else:
            engine='none'
        for i,scene in enumerate(scenes):
            y=master_voice(speech[i],scene.get('role','narrator')) if mode=='full' else np.zeros(0,dtype=np.float32)
            duration=max(scene['min_seconds'],len(y)/SR+.7)
            narration.append(y);durations.append(duration)
            print(f"scene {i+1:02d}: {duration:.2f}s voice {len(y)/SR:.2f}s backend={engine}",flush=True)
        duration=sum(durations)+.35
        n=round(duration*SR)
        music=make_music(duration) * 1.9
        foley=np.zeros((n,2),dtype=np.float32)
        voices=np.zeros((n,2),dtype=np.float32)
        duck=np.ones(n,dtype=np.float32)
        # Continuous subtle wind / electrical room tone.
        room=windy(duration)
        add(foley,room,0,.8,-.15)
        add(foley,windy(duration),0,.52,.6)
        cue=[];cursor=0
        for i,(scene,seconds,y) in enumerate(zip(scenes,durations,narration)):
            cue.append(dict(id=scene['id'],at=round(cursor,2),end=round(cursor+seconds,2),
                            narration=scene['text'],tts_text=scene.get('tts_text',scene['text']),visual=scene['visual'],sfx=scene['sfx'],voice_seconds=round(len(y)/SR,2)))
            events=scene.get('sfx',[])
            for j,name in enumerate(events):
                position=cursor+(0.25 if j==0 else min(2.2,seconds*.36))
                sfx_event(name,foley,position,i)
            if len(y):
                start=round((cursor+.22)*SR)
                a=min(len(y),n-start)
                signal=fade(y[:a],attack=.08,release=.2)
                add(voices,signal,cursor+.22,1,0)
                # Fast attack, slow release, fixed ducking: narration remains foreground.
                lo=max(0,start-round(.10*SR));hi=min(n,start+a+round(.50*SR))
                duck[lo:hi]=.35
                # scene-end effects are still audible after speech.
                if i==len(scenes)-1:
                    add(foley,thump(47,1.4,.38),cursor+seconds-.75,.75,0)
            cursor+=seconds
        # smooth ducking edge to avoid clicks
        duck=uniform_filter1d(duck,size=int(.15*SR))
        mixed=music*duck[:,None]+foley*1.05+voices
        # Final dramatic 0.30s quiet window before hard cut.
        end_fade=min(round(.27*SR),len(mixed)//2)
        if end_fade:
            mixed[-end_fade:]*=np.linspace(1,0,end_fade)[:,None]
        peak=float(np.max(np.abs(mixed)))
        if peak>.96:mixed*=.96/peak
        mixed=np.tanh(mixed*1.03).astype(np.float32)
        def save_wav(path,arr):
            with wave.open(str(path),'wb') as wf:
                wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(SR)
                wf.writeframes(np.int16(np.clip(arr,-1,1)*32767).tobytes())
        # Deliver a mixed master and independent stems for future editing.
        for nm,data in [('master',mixed),('music',music),('foley',foley),('narration',voices)]:
            src=tmp/(nm+'.wav');save_wav(src,data)
            target=outdir/(nm+'.mp3')
            call('ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(src),'-c:a','libmp3lame','-b:a','192k',str(target))
        (outdir/'cue_sheet.json').write_text(json.dumps(cue,ensure_ascii=False,indent=2),encoding='utf8')
        def srt_timestamp(t):
            h=int(t//3600);m=int(t%3600//60);s=int(t%60);ms=int((t-int(t))*1000)
            return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
        (outdir/'subtitles.srt').write_text('\n'.join(
            f"{i+1}\n{srt_timestamp(c['at']+.15)} --> {srt_timestamp(min(c['end'], c['at']+max(2.,c['voice_seconds'])))}\n{c['narration']}\n"
            for i,c in enumerate(cue)),encoding='utf8')
        print('CREATED:',outdir,'DURATION:',round(duration,2),'VOICE:',mode,flush=True)
        return cue,duration

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--episode',default=str(HERE/'episode.json'))
    p.add_argument('--mode',choices=['full','music-only'],default='full')
    p.add_argument('--voice',default='silero-aidar')
    p.add_argument('--rate',default='-8%')
    p.add_argument('--pitch',default='-8Hz')
    p.add_argument('--output',default=str(HERE/'output'))
    a=p.parse_args()
    doc=json.loads(Path(a.episode).read_text(encoding='utf8'))
    mix_episode(doc,a.mode,Path(a.output),voice=a.voice,rate=a.rate,pitch=a.pitch)

if __name__=='__main__':main()
