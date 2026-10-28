"""Original procedural score/foley and narration mix (no copyrighted audio)."""
from __future__ import annotations
import math
import wave
from pathlib import Path
import numpy as np
SR=24000

def create_mix(scenes,durations,voices,tmp):
    length=int(round(sum(durations)*SR));t=np.arange(length,dtype=np.float32)/SR
    rng=np.random.default_rng(1719)
    # Restrained suspense score: no wall of hiss over dialogue.
    base=.007*np.sin(2*np.pi*(47*t+.06*np.sin(t*.7)))+.004*np.sin(2*np.pi*69*t)
    mix=np.stack([base.copy(),base.copy()],axis=1).astype(np.float32)
    for ch in range(2):
        raw=rng.standard_normal(length).astype(np.float32)
        hp=raw.copy();hp[1:]=raw[1:]-.65*raw[:-1]
        mix[:,ch] += .0035*hp*(.6+.4*np.sin(t*(.37+.07*ch)))

    def add(a,time,gain=.5,pan=0):
        start=max(0,int(time*SR))
        n=min(len(a),length-start)
        if n<=0:return
        l=math.sqrt((1-pan)/2);r=math.sqrt((1+pan)/2)
        mix[start:start+n,0]+=a[:n]*gain*l
        mix[start:start+n,1]+=a[:n]*gain*r

    def beep(freq=660,dur=.19,volume=.12,fall=8):
        ts=np.arange(max(1,int(dur*SR)),dtype=np.float32)/SR
        return (np.sin(2*np.pi*freq*ts)*volume*(1-np.exp(-ts*35))*np.exp(-fall*ts)).astype(np.float32)

    def pulse(freq=53,dur=.75,volume=.22,fall=3):
        ts=np.arange(max(1,int(dur*SR)),dtype=np.float32)/SR
        return (np.sin(2*np.pi*(freq*ts+.07*np.sin(2*ts)))*volume*np.exp(-fall*ts)).astype(np.float32)

    def crack(dur=.16,volume=.13,seed=0):
        ts=np.arange(max(1,int(dur*SR)),dtype=np.float32)/SR
        r=np.random.default_rng(seed+700).standard_normal(len(ts)).astype(np.float32)
        return (r*volume*np.exp(-ts*18)).astype(np.float32)

    position=0
    for i,(scene,dur,(speech,backend)) in enumerate(zip(scenes,durations,voices)):
        kind=scene['kind']
        add(pulse(51,.32,.16,9),position+.03,.6,-.3 if i%2 else .2)
        if kind in ('cold_open','signal'):
            for k in range(4):add(beep(420+200*k,.08,.045,12),position+.3+k*.47,.6,.4)
        elif kind=='power':
            add(crack(.24,.13,i),position+.55,.9,-.5)
            add(pulse(46,1.0,.20,4),position+.68,.7,.1)
        elif kind=='dial':
            for k in range(5):add(crack(.06,.055,i*5+k),position+.35+k*.37,.6,-.25)
        elif kind=='clock':
            for k in range(8):add(crack(.075,.07,k),position+.16+k*.36,.54,(-1)**k*.3)
        elif kind in ('hall','flashes','shadow'):
            add(pulse(44,1.4,.17,2),position+.38,.6,.2)
            if kind=='flashes':
                for sec in [.15,1.05,1.95]:add(beep(360,.21,.21,5),position+sec,.75,-.4)
            if kind=='shadow':
                for k in range(3):add(crack(.22,.075,i+k),position+.7+k*.68,.5,.15)
        elif kind=='warning':
            for k in range(3):add(beep(770,.15,.13),position+.6+k*.65,.6,.55)
        elif kind=='recorder':
            for k in range(5):add(crack(.06,.05,i+k),position+.42+k*.48,.7,-.5)
        elif kind=='tomorrow':
            add(pulse(36,1.8,.16,1),position+.4,.7,.0)
        elif kind=='final':
            add(pulse(41,3.2,.25,.85),position+.9,.9,.0)
            add(crack(.52,.13,i),position+2.35,.65,.45)
        # speech is always center and more prominent; duck bed while spoken
        begin=int((position+.16)*SR)
        n=min(len(speech),length-begin)
        if n>0:
            window=np.minimum(1,np.arange(n)/(SR*.08))*np.minimum(1,(n-np.arange(n))/(SR*.16))
            mix[begin:begin+n,:]*=.22
            centered=speech[:n]*window*.84
            mix[begin:begin+n,0]+=centered
            mix[begin:begin+n,1]+=centered
        position+=dur
    nfade=min(int(.4*SR),length//6)
    mix[:nfade,:]*=np.linspace(0,1,nfade,dtype=np.float32)[:,None]
    mix[-nfade:,:]*=np.linspace(1,0,nfade,dtype=np.float32)[:,None]
    mix=np.tanh(mix*1.13)
    peak=float(np.max(np.abs(mix)))
    if peak>.98:mix*=.98/peak
    out=Path(tmp)/'mix.wav'
    with wave.open(str(out),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
    return out
