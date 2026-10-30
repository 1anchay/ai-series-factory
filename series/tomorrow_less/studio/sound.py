"""Original, copyright-safe synthesized soundscape for a new 2D survival story."""
from __future__ import annotations
import math,wave
from pathlib import Path
import numpy as np
SR=24000

def _sine(freq,secs,amp=.15,decay=4):
    t=np.arange(round(secs*SR),dtype=np.float32)/SR
    return (amp*np.sin(2*np.pi*freq*t)*np.exp(-decay*t)).astype(np.float32)

def _noise(secs,amp=.16,seed=0,decay=8):
    t=np.arange(round(secs*SR),dtype=np.float32)/SR
    raw=np.random.default_rng(seed).standard_normal(len(t)).astype(np.float32)
    # suppress metallic white-noise hiss, retain impact onset
    raw=.75*raw+.25*np.roll(raw,1)
    return (raw*amp*np.exp(-decay*t)).astype(np.float32)

def _knock():
    a=_noise(.16,.34,19,25)+_sine(115,.16,.35,22)
    return a

def _sfx(name):
    if name=='heartbeat':return [(.1,_sine(61,.35,.22,13)),(.42,_sine(58,.25,.15,17))]
    if name=='phone':return [(.30,_sine(780,.25,.15,8)),(.70,_sine(1010,.25,.13,8))]
    if name=='wind':return [(.2,_noise(2.0,.07,11,1))]
    if name=='bus':return [(.5,_sine(93,1.2,.22,1.4)),(1.7,_noise(.5,.09,23,7))]
    if name=='fluorescent':return [(.6,_sine(120,.4,.10,2.2)),(1.6,_sine(125,.4,.08,2.5))]
    if name=='dial':return [(.7,_sine(430,.4,.11,2)),(1.8,_sine(430,.4,.08,2)),(2.8,_sine(430,.4,.06,2))]
    if name=='footsteps':return [(.9,_knock()),(1.5,_knock()),(2.1,_knock())]
    if name=='door':return [(.7,_noise(.6,.22,51,4)),(1.8,_sine(70,.8,.21,2))]
    if name=='writing':return [(.6,_noise(.15,.06,71,15)),(1.7,_noise(.15,.06,72,15)),(2.8,_noise(.15,.06,73,15))]
    if name=='power':return [(.2,_noise(.5,.25,81,7)),(.78,_sine(45,.8,.19,2.8))]
    if name=='clock':return [(i*.62,_noise(.055,.12,100+i,24)) for i in range(5)]
    if name=='count':return [(.9,_sine(55,.9,.21,3)),(1.8,_noise(.3,.11,95,6))]
    if name=='reveal':return [(1.4,_sine(53,1.7,.20,1.1)),(3.5,_knock())]
    if name=='printer':return [(k*.22,_noise(.085,.10,80+k,12)) for k in range(10)]
    if name=='tape':return [(.4,_noise(.27,.26,192,16)),(.78,_sine(155,.95,.12,2.5))]
    if name=='glitch':return [(.55,_noise(.6,.25,240,3.4)),(3.0,_sine(39,1.6,.25,1.1)),(4.6,_noise(.33,.18,241,12))]
    return []

def mix(scenes,durations,voice_arrays,temp):
    n=int(sum(durations)*SR);t=np.arange(n,dtype=np.float32)/SR
    # An original three-tone score with ebbing suspense (never a continuous beep).
    pulse=(.60+.40*np.sin(2*np.pi*.017*t-0.3))
    ambient_chord=(.015*np.sin(2*np.pi*(43*t+.13*np.sin(t*.13)))
                   +.006*np.sin(2*np.pi*65.41*t)
                   +.004*np.sin(2*np.pi*87.31*t))*pulse
    amb=np.column_stack([ambient_chord,ambient_chord*.92]).astype(np.float32)
    rng=np.random.default_rng(350)
    for ch in range(2):
        r=rng.standard_normal(n).astype(np.float32)
        amb[:,ch]+=(r-.84*np.roll(r,1))*.007
    foley=np.zeros((n,2),dtype=np.float32);voice=np.zeros((n,2),dtype=np.float32)
    def add(buf,a,at,gain=.7,pan=0):
        start=int(at*SR);length=min(len(a),n-start)
        if start<0 or length<=0:return
        buf[start:start+length,0]+=a[:length]*gain*math.sqrt((1-pan)/2)
        buf[start:start+length,1]+=a[:length]*gain*math.sqrt((1+pan)/2)
    pos=0
    for i,(scene,dur,v) in enumerate(zip(scenes,durations,voice_arrays)):
        for at,sound in _sfx(scene.get('sfx','')):add(foley,sound,pos+at,.70,(-.25 if i%2 else .25))
        off=pos+.28
        add(voice,np.asarray(v,dtype=np.float32),off,.85,0)
        pos+=dur
    # Voice leads. Effect events remain audible under voice but soft. No overblown sub bass.
    dialogue_mask=np.maximum(np.abs(voice[:,0]),np.abs(voice[:,1]))>.015
    duck=np.ones(n,dtype=np.float32)
    duck[dialogue_mask]=.56
    # smooth volume between voiced/nonvoiced regions without pumping
    for shift in [240,720,1440]:duck=np.minimum(duck,np.roll(duck,shift));duck=np.minimum(duck,np.roll(duck,-shift))
    # Foley is not ducked as much as ambience: the story must sound physical.
    mixdata=voice+foley*.95+amb*duck[:,None]
    mixdata=np.tanh(mixdata*.98).astype(np.float32)
    peak=float(np.max(np.abs(mixdata)))
    if peak>.95:mixdata*=.95/peak
    fade=min(int(.24*SR),len(mixdata)//8)
    if fade:
        mixdata[:fade]*=np.linspace(0,1,fade)[:,None]
        mixdata[-fade:]*=np.linspace(1,0,fade)[:,None]
    out=Path(temp)/'audio.wav'
    with wave.open(str(out),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes(np.int16(np.clip(mixdata,-1,1)*32767).tobytes())
    return out
