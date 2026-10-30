"""Original horror soundtrack and synchronized object sounds.
Does not contain reference audio or borrowed melodies.
"""
import numpy as np,math,subprocess,wave
from pathlib import Path
from scipy.signal import butter,sosfilt
SR=24000
RNG=np.random.default_rng(82311)

def lowpass(x,f):return sosfilt(butter(2,f,btype='lowpass',fs=SR,output='sos'),x).astype('float32')
def tone(freq,dur,amp=.1,decay=1):
 t=np.arange(max(1,int(dur*SR)),dtype=np.float32)/SR
 return (amp*(np.sin(2*np.pi*freq*t)+.14*np.sin(2*np.pi*freq*2.018*t))*np.exp(-decay*t)).astype('float32')
def noise(dur,amp=.1,cutoff=950):
 z=RNG.standard_normal(round(dur*SR)).astype('float32');return lowpass(z,cutoff)*amp
def place(dest,sig,start,gain=1,pan=0):
 at=int(start*SR)
 if at<0 or at>=len(dest):return
 z=min(len(sig),len(dest)-at)
 dest[at:at+z,0]+=sig[:z]*gain*np.sqrt((1-pan)/2)
 dest[at:at+z,1]+=sig[:z]*gain*np.sqrt((1+pan)/2)
def impact(freq=80):
 t=np.arange(int(SR*.62))/SR
 return ((.22*np.sin(2*np.pi*freq*t)*np.exp(-8*t))+noise(.62,.07,1400)*np.exp(-32*t)).astype('float32')
def beep(freq=750):return tone(freq,.24,.15,14)
def footsteps():return impact(92)*.46
def creak():
 t=np.arange(round(1.8*SR))/SR; f=120+75*t+15*np.sin(t*4.8)
 return (.065*np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*np.minimum(1,t/1.8))**1.2).astype('float32')
def electrical():
 t=np.arange(round(.65*SR))/SR
 return (noise(.65,.15,2300)*np.exp(-11*t)+tone(95,.65,.07,8)).astype('float32')
def radar():
 t=np.arange(round(.85*SR))/SR
 return (.038*np.sin(2*np.pi*740*t)*(1+np.sin(t*2*np.pi*19))*.5).astype('float32')
def original_ambience(seconds):
 n=round(seconds*SR);t=np.arange(n,dtype=np.float32)/SR
 z=noise(seconds,.016,370)
 d=(.014*np.sin(2*np.pi*(41.203*t+.11*np.sin(t*.18)))
   +.010*np.sin(2*np.pi*55*t)
   +.007*np.sin(2*np.pi*82.41*t)+.42*z).astype('float32')
 return np.column_stack([d,d]).astype('float32')
def make_audio(cues,voice_mp3,outdir):
 """Cues from validated remote neural narration; music and Foley rendered independently."""
 outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
 total=float(cues[-1]['end'])+.25;n=round(total*SR)
 music=original_ambience(total)[:n]
 if len(music)<n:music=np.pad(music,((0,n-len(music)),(0,0)))
 effects=np.zeros((n,2),dtype='float32')
 # An original sparse 4-tone unease theme that never overlays important events.
 for i,(time,f) in enumerate([(3,146.83),(11,155.56),(21,103.83),(30,123.47),(43,146.83),(54,155.56),(65,103.83),(78,123.47)]):
  if time<total:place(music,tone(f,3.7,.10,.68),time,.80,-.25 if i%2 else .25)
 types={'alarm':lambda:beep(900),'click':lambda:electrical(),'bass':lambda:impact(50),
        'metal':lambda:impact(170),'static':lambda:noise(1,.08,1800),'beep':lambda:beep(620),
        'step':footsteps,'knock':lambda:impact(105),'breaker':electrical,
        'elevator':lambda:tone(49,2.8,.085,.3),'creak':creak,'wind':lambda:noise(1.9,.04,500),
        'glass':lambda:tone(610,1.8,.07,2.7),'intercom':lambda:beep(720),'impact':lambda:impact(55)}
 for i,c in enumerate(cues):
  s=c.get('sfx',[]);a=float(c['at']);d=float(c['end'])-a
  for j,name in enumerate(s):
   sig=types[name]() if name in types else impact()
   rel=(.35+.48*j if name=='knock' else .40+min(1.8,j*.65))
   place(effects,sig,a+min(rel,d-.15),.72 if name=='knock' else .52,(-.5+.4*j)%1-.5)
  if i==len(cues)-1:
   place(effects,impact(49),float(c['end'])-.49,.75)
 # Decode dry narrator: one continuous voice stem exactly in cue timing
 voice=np.zeros((n,2),dtype='float32')
 if voice_mp3:
  p=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(voice_mp3),'-f','f32le','-ac','2','-ar',str(SR),'pipe:1'],capture_output=True,check=True)
  arr=np.frombuffer(p.stdout,dtype='<f4').copy().reshape(-1,2)
  k=min(n,len(arr));voice[:k]=arr[:k]
 # Duck music only under narrator, keep event sounds audible
 if voice_mp3:
  energy=np.maximum(np.abs(voice[:,0]),np.abs(voice[:,1]))
  from scipy.ndimage import uniform_filter1d
  attack=uniform_filter1d((energy>.006).astype(np.float32),size=800)
  duck=(1-.60*np.minimum(1,attack*6)).astype('float32')
  music*=duck[:,None]
 mixed=music*.66+effects*.92+voice*1.08
 peak=np.max(np.abs(mixed))
 if peak>.93:mixed*=.93/peak
 mixed=np.tanh(mixed*1.04)
 def save(dest,data):
  with wave.open(str(dest),'wb') as f:
   f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR)
   f.writeframes(np.int16(np.clip(data,-1,1)*32767).tobytes())
 save(outdir/'master.wav',mixed)
 save(outdir/'music.wav',music)
 save(outdir/'sfx.wav',effects)
 save(outdir/'voice.wav',voice)
 return outdir/'master.wav'