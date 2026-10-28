"""Three-track original sound design: atmospheric bed, timed foley, intelligible dialogue.
All sounds synthesized on CPU; no external audio assets, licensing, or API costs.
"""
from __future__ import annotations
import math
import wave
from pathlib import Path
import numpy as np
SR=24000


def _tone(freq,duration=.28,amp=.18,decay=6):
    t=np.arange(max(1,int(SR*duration)),dtype=np.float32)/SR
    return (amp*np.sin(2*np.pi*freq*t)*np.exp(-decay*t)).astype('float32')


def _noise(duration=.28,amp=.18,seed=12,decay=6,blur=0.):
    t=np.arange(max(1,int(SR*duration)),dtype=np.float32)/SR
    raw=np.random.default_rng(seed).standard_normal(len(t)).astype('float32')
    if blur>0:
        coeff=np.exp(-1/(SR*blur))
        # vectorized simple moving average to avoid slow loops
        width=max(1,int(SR*blur*.2))
        if width>1:raw=np.convolve(raw,np.ones(width,dtype='float32')/width,'same')
    return (raw*amp*np.exp(-decay*t)).astype('float32')


def _static_sweep(duration=.8,seed=20):
    n=max(1,int(SR*duration));t=np.arange(n,dtype=np.float32)/SR
    r=np.random.default_rng(seed).standard_normal(n).astype('float32')
    modulation=(.3+.7*np.sin(2*np.pi*(3*t+2*t*t))**2)
    tone=.11*np.sin(2*np.pi*(450*t+130*t*t))
    return (.13*r*modulation +tone).astype('float32')


def _click():
    return (_noise(.09,.2,51,decay=30)+_tone(85,.09,.23,decay=28)).astype('float32')


def _wood_knock(seed):
    n=int(.48*SR);t=np.arange(n,dtype=np.float32)/SR
    body=.38*np.sin(2*np.pi*117*t)*np.exp(-t*11)
    body+=.23*np.sin(2*np.pi*173*t)*np.exp(-t*17)
    body+=.08*np.random.default_rng(seed).standard_normal(n)*np.exp(-t*48)
    return body.astype('float32')


def _rising(freq=90,dur=1.3):
    t=np.arange(max(1,int(dur*SR)),dtype=np.float32)/SR
    phase=2*np.pi*(freq*t+130*t*t/dur)
    env=np.sin(np.pi*np.clip(t/dur,0,1))**2
    return (.12*env*np.sin(phase)).astype('float32')


def effect_events(scene):
    """(seconds within shot, mono audio, gain, stereo pan)."""
    fx=scene.get('sfx',scene.get('kind','wind'))
    if fx=='knock':return [(a,_wood_knock(100+i),.98,0.1 if i%2 else -.15) for i,a in enumerate((.55,1.35,2.18))]
    if fx=='radio_scan':return [(.2,_static_sweep(1.3,17),.55,-.35),(1.85,_tone(380,.3,.23,11),.6,.2)]
    if fx=='radio_voice':return [(.05,_static_sweep(.45,19),.35,.0),(.65,_tone(310,.12,.2,17),.50,.2)]
    if fx=='switch':return [(.50,_click(),1.15,.3),(.68,_noise(.33,.17,9,13),.55,-.2)]
    if fx=='tape':return [(i*.57+.25,_click(),.45,(-1)**i*.3) for i in range(6)] +[(.4,_tone(95,2.0,.075,1.3),.3,-.3)]
    if fx=='clock':return [(i*.45+.22,_click(),.60,(-1)**i*.35) for i in range(9)]
    if fx=='alarm':return [(x,_tone(520,.37,.30,3),.78,-.5) for x in (.55,1.25,1.94)]
    if fx=='pencil':return [(i*.30+.8,_noise(.16,.09,91+i,15),.76,0.3) for i in range(6)]
    if fx=='wind':return [(.4,_noise(2.2,.065,35,decay=.7,blur=.003),.55,-.3)]
    if fx=='breath':return [(i*.95+.4,_noise(.55,.06,31+i,3,blur=.001),.65,.4) for i in range(3)]
    if fx=='beep':return [(a,_tone(740,.22,.25,8),.82,.5) for a in (.5,1.14,1.84)]
    if fx=='footsteps':return [(a,_wood_knock(120+i),.34,(-1)**i*.55) for i,a in enumerate((.4,1.12,1.85,2.7))]
    if fx=='ring':return [(a,_tone(470,.24,.25,7)+_tone(610,.24,.13,9),.92,.5) for a in (.3,.78,1.45,1.93)]
    if fx=='glass':return [(.6,_rising(74,1.6),.50,.35),(.9,_noise(.43,.08,30,7),.38,.4)]
    if fx=='latch':return [(1.06,_click(),1.15,.35),(1.19,_noise(.6,.08,40,5),.55,.45)]
    if fx=='dial':return [(i*.28+.35,_click(),.52,.25) for i in range(7)]
    if fx=='power':return [(.2,_noise(.8,.21,60,5),.68,-.4),(1.2,_tone(44,1.5,.25,1.5),.62,0)]
    if fx=='sting':return [(1.35,_wood_knock(720),.82,0),(1.52,_tone(43,2.7,.32,1.2),.85,0),(.14,_static_sweep(.3),.17,0)]
    if fx=='silence':return [(2.55,_wood_knock(950),.45,.25)]
    return[(.6,_click(),.28,0)]


def _add(dst,a,start,gain=.5,pan=0):
    pos=max(0,round(SR*start));n=min(len(a),len(dst)-pos)
    if n<=0:return
    left=math.sqrt((1-pan)/2);right=math.sqrt((1+pan)/2)
    dst[pos:pos+n,0]+=a[:n]*gain*left
    dst[pos:pos+n,1]+=a[:n]*gain*right


def _save(path,mix):
    with wave.open(str(path),'wb') as f:
        f.setframerate(SR);f.setnchannels(2);f.setsampwidth(2)
        f.writeframes(np.int16(np.clip(mix,-1,1)*32767).tobytes())
    return path


def create_mix(scenes,durations,voices,tmp):
    n=round(sum(durations)*SR);t=np.arange(n,dtype=np.float32)/SR
    rng=np.random.default_rng(555)
    # Music is subdued but not absent. Foley has its own louder track.
    drone=(.009*np.sin(2*np.pi*(47*t+.10*np.sin(t*.48)))+.006*np.sin(2*np.pi*70*t))
    bed=np.stack([drone.copy(),drone.copy()],axis=1).astype('float32')
    for ch in range(2):
        raw=rng.standard_normal(n).astype('float32')
        bed[:,ch]+=.0045*(raw - .65*np.roll(raw,1))*(.55+.45*np.sin(.31*t+ch))
    foley=np.zeros_like(bed)
    dialog=np.zeros_like(bed)
    duck=np.ones(n,dtype=np.float32)
    pos=0.
    for scene,dur,voice_entry in zip(scenes,durations,voices):
        speech,backend=voice_entry[:2]
        # Radio and intercom dialogue has its own timbre; narrator remains clean.
        if scene.get('speaker')=='radio':
            speech=np.asarray(speech,dtype=np.float32)
            smooth=np.convolve(speech,np.ones(11,dtype=np.float32)/11,mode='same')
            speech=(.80*smooth + .20*speech).astype('float32')
        for rel,clip,gain,pan in effect_events(scene):_add(foley,clip,pos+rel,gain,pan)
        start=round((pos+.18)*SR);size=min(len(speech),n-start)
        if size>0:
            speech=speech[:size].astype('float32')
            times=np.arange(size,dtype=np.float32)
            ramp=np.minimum(1,times/(SR*.065))*np.minimum(1,(size-times)/(SR*.13))
            # narration should be consistently audible and effects retain some presence
            dialog[start:start+size,:]+=speech[:,None]*ramp[:,None]*.91
            duck[max(0,start-round(.06*SR)):min(n,start+size+round(.12*SR))]=.42
        pos+=dur
    # Smoothed ducking prevents audible pumping while still preserving foley peaks.
    smooth_width=round(SR*.07)
    kernel=np.ones(smooth_width,dtype=np.float32)/smooth_width
    duck=np.convolve(duck,kernel,mode='same')
    mix=dialog + bed*duck[:,None] + foley*(.58+.42*duck[:,None])
    fade=min(round(SR*.36),n//8)
    if fade:
        mix[:fade]*=np.linspace(0,1,fade,dtype=np.float32)[:,None]
        mix[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)[:,None]
    peak=float(np.max(np.abs(mix)))
    if peak> .96:mix *=.96/peak
    mix=np.tanh(mix*1.08).astype('float32')
    result=Path(tmp)/'mix.wav'
    _save(result,mix)
    # Expose diagnostic SFX to let the creator hear actual sound design without narration.
    diagnostics=Path(tmp)/'effects_only.wav'
    _save(diagnostics,np.tanh(foley*1.1))
    return result
