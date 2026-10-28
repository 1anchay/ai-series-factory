"""Free original stereo atmosphere and sound effects synthesized with NumPy.
No copyrighted sound library or paid sound APIs.
"""
from __future__ import annotations
import math
import wave
from pathlib import Path
import numpy as np
SR = 24000


def create_soundtrack(scenes, voices, lengths, tmp):
    sr = SR
    n = max(1, round(sum(lengths) * sr))
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(91342)
    # Score: sub-bass and two slowly-detuning synth tones.
    score = (.028*np.sin(2*np.pi*(48*t+.35*np.sin(.23*t)))
             +.014*np.sin(2*np.pi*(73*t+.20*np.sin(.13*t)))
             +.006*np.sin(2*np.pi*109*t))
    mix = np.stack([score.copy(), score.copy()], axis=1).astype(np.float32)
    # Separate diffuse environmental rain in L/R; no stereo-correlated noise.
    for ch in range(2):
        white = rng.standard_normal(n).astype(np.float32)
        hp = np.empty_like(white)
        hp[0] = white[0]
        hp[1:] = white[1:] - .77 * white[:-1]
        env = .6 + .35*np.sin(2*np.pi*(.09+ch*.018)*t+ch)
        mix[:,ch] += .017*hp*env
        # Wind gusts with smoother brownish low-frequency texture.
        tiny = rng.normal(0,1,int(np.ceil(n/900))+2).astype(np.float32)
        swell = np.interp(np.arange(n,dtype=np.float32)/900,np.arange(len(tiny)),tiny).astype(np.float32)
        mix[:,ch] += .009*swell

    def add(a, at, gain=.5, pan=0.):
        offset = int(max(0,at)*sr)
        amount = min(len(a), n-offset)
        if amount <= 0: return
        left = math.sqrt((1-pan)/2)
        right = math.sqrt((1+pan)/2)
        mix[offset:offset+amount,0] += a[:amount]*gain*left
        mix[offset:offset+amount,1] += a[:amount]*gain*right

    def hit(freq=85, duration=.8, strength=.25, decay=4., sweep=0.):
        tt = np.arange(max(1,int(duration*sr)),dtype=np.float32)/sr
        phase = 2*np.pi*(freq*tt + sweep*(1-np.exp(-4*tt)))
        return (strength * np.sin(phase) * np.exp(-decay*tt)).astype(np.float32)

    def crack(duration=.7, strength=.25, seed=0, decay=6.):
        tt = np.arange(max(1,int(duration*sr)),dtype=np.float32)/sr
        r = np.random.default_rng(1000+seed).standard_normal(len(tt)).astype(np.float32)
        # Dark crackle rather than broadband static.
        r[1:] = .64*r[1:]+.36*r[:-1]
        return (strength*r*np.exp(-decay*tt)).astype(np.float32)

    def thunder(seed=0, duration=2.6):
        r = np.random.default_rng(850+seed)
        steps = round(duration*sr)
        tt = np.arange(steps,dtype=np.float32)/sr
        low = np.interp(np.arange(steps)/180,np.arange(steps//180+2),
                        r.standard_normal(steps//180+2)).astype(np.float32)
        tail = (.19*low + .15*np.sin(2*np.pi*(31*tt+.6*np.sin(tt))))
        envelope = (1-np.exp(-tt*10))*np.exp(-tt*1.35)
        return (tail*envelope).astype(np.float32)

    # Per-scene foley & pacing. Sound positions are relative to scene start.
    position = 0.
    for index, (scene, length, voice) in enumerate(zip(scenes,lengths,voices)):
        art = scene.get('art','')
        add(hit(58,.55,.17,4),position,1,-.3 if index%2 else .3)
        if art=='city':
            add(crack(1.2,.38,index,4),position+.18,.8,-.65)
            add(thunder(index),position+.7,1.,.45)
            add(hit(39,3,.34,.6,-2.7),position+.55,1,-.1)
        elif art=='street':
            for k in range(4):
                add(crack(.26,.24,index*17+k,13),position+1+k*.78,.70,-.7+.40*k)
            add(thunder(index,2.6),position+1.5,.55,.7)
        elif art=='phone':
            # Distinct short two-note phone warning, avoid over-loud piercing high notes.
            add(hit(740,.27,.30,7),position+.65,.85,.5)
            add(hit(990,.24,.23,9),position+.84,.8,.5)
            add(hit(740,.27,.30,7),position+1.32,.85,.5)
        elif art=='look_up':
            add(hit(36,3.6,.34,.32,-1.4),position+.9,1,-.55)
            add(crack(1.2,.14,index,3),position+2.3,.5,.65)
        elif art=='window':
            add(hit(126,2.5,.20,1.1,2.4),position+1.05,1,.55)
            add(thunder(index,2),position+1.8,.8,-.2)
        elif art=='double':
            add(crack(1.05,.40,index,8),position+1.5,1,0)
            add(hit(38,3.6,.42,.5,-3),position+1.65,1,0)
            add(hit(260,1.4,.16,2,-.4),position+2.1,1,-.3)
        if len(voice):
            start = int((position+.50)*sr)
            amount = min(len(voice),n-start)
            if amount>0:
                v = np.asarray(voice[:amount],dtype=np.float32)
                fadein = np.minimum(1,np.arange(amount)/(sr*.10))
                fadeout = np.minimum(1,(amount-np.arange(amount))/(sr*.18))
                voice_env = fadein*fadeout
                # Slow attack and release to reduce pump artefacts.
                duck = .47 + .12*(1-voice_env)
                mix[start:start+amount,:] *= duck[:,None]
                mix[start:start+amount,0] += .84*v*voice_env
                mix[start:start+amount,1] += .84*v*voice_env
        position += length

    # Safe soft peak limiter, stereo integrity, final quiet fade.
    f = min(int(.80*sr),n//8)
    if f>0:
        mix[:f] *= np.linspace(0,1,f,dtype=np.float32)[:,None]
        mix[-f:] *= np.linspace(1,0,f,dtype=np.float32)[:,None]
    peak = float(np.max(np.abs(mix)))
    if peak > 1.05: mix *= 1.05/peak
    mix = np.tanh(mix*1.16)
    out = Path(tmp)/'soundtrack.wav'
    with wave.open(str(out),'wb') as wf:
        wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(sr)
        wf.writeframes(np.int16(np.clip(mix,-1,1)*32767).tobytes())
    return out
