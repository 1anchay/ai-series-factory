#!/usr/bin/env python3
"""Original dark 2D motion-story renderer inspired by video grammar, not copied shots.
No outside images, footage or music. PIL animation + original procedural audio.
"""
from __future__ import annotations
import argparse, json, math, random, struct, subprocess, tempfile, wave, shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np

HERE=Path(__file__).resolve().parents[1]
W,H=432,768
FPS=20
SR=24000
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
@__import__('functools').lru_cache(maxsize=80)
def font(s,bold=True):return ImageFont.truetype(BOLD if bold else REG,int(s))
NAVY=(8,15,27); BACK=(9,18,33); MID=(22,34,51); LITE=(48,68,84)
PALE=(242,241,232); GRAY=(163,176,186); RED=(218,69,80); YELLOW=(244,193,76); CYAN=(85,181,195)

def clamp(v,a=0,b=1):return max(a,min(b,v))
def ease(v):v=clamp(v);return v*v*(3-2*v)
def rect(d,r,c,rad=0,outline=None,width=1):
 if rad:d.rounded_rectangle(tuple(map(int,r)),radius=rad,fill=c,outline=outline,width=width)
 else:d.rectangle(tuple(map(int,r)),fill=c,outline=outline,width=width)
def txt(d,xy,s,size=15,c=PALE,anchor=None,bold=True,stroke=0):
 d.text(xy,s,font=font(size,bold),fill=c,anchor=anchor,stroke_width=stroke,stroke_fill=NAVY)
def line(d,points,c,width=2,joint='curve'):d.line([(int(x),int(y)) for x,y in points],fill=c,width=width,joint=joint)

def base(seed):
 im=Image.new('RGB',(W,H),BACK);d=ImageDraw.Draw(im)
 for y in range(H):
  f=y/H;c=(int(7+11*f),int(15+13*f),int(28+16*f));d.line((0,y,W,y),fill=c)
 r=random.Random(seed)
 for _ in range(42):
  x=r.randrange(W);y=r.randrange(90,550);d.point((x,y),fill=(45,66,77))
 # subtle vignette strips
 d.rectangle((0,0,9,H),fill=(7,13,24));d.rectangle((W-8,0,W,H),fill=(7,13,24))
 return im

def sea(d,t,y=465):
 d.rectangle((0,y,W,645),fill=(8,28,42))
 for k in range(10):
  yy=y+13+k*18
  xx=(24*k + t*(17+k*2))%120
  for xx0 in range(-130,470,120):
   line(d,[(xx0+xx,yy),(xx0+xx+32,yy-1),(xx0+xx+54,yy+2)],(22+min(20,k*2),65,80),2)
 d.polygon([(0,465),(56,461),(121,475),(159,480),(170,642),(0,642)],fill=(17,24,31))

def lighthouse(d,x=281,y=482,scale=1,lights=True,t=0,under=False):
 def xy(dx,dy):return (int(x+dx*scale),int(y+dy*scale))
 col=(16,36,46) if under else (39,47,56)
 d.polygon([xy(-45,0),xy(-26,-220),xy(25,-220),xy(45,0)],fill=col,outline=(82,97,102))
 for k in range(4):
  yy=-28-k*47
  a,b=xy(-25+k*2,yy),xy(25-k*2,yy)
  line(d,[a,b],(74,85,89),3)
  d.rectangle((*xy(-7,yy-25),*xy(7,yy-10)),fill=(220,164,84) if lights and k==2 else (10,29,42),outline=(72,93,103),width=1)
 d.rectangle((*xy(-36,-257),*xy(37,-220)),fill=(50,69,75),outline=(135,143,138),width=3)
 d.rectangle((*xy(-24,-286),*xy(24,-259)),fill=(186,218,205) if lights else (23,39,51),outline=(140,148,144),width=2)
 d.polygon([xy(-47,-259),xy(0,-300),xy(47,-259)],fill=(53,67,75),outline=(102,111,109))
 d.ellipse((*xy(-8,-271),*xy(8,-260)),fill=YELLOW if lights else (46,64,72))

def beam(im,t,x=281,y=209,under=False,bright=True):
 if not bright:return im
 overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay,'RGBA')
 dx=140*math.sin(t*.56);edge=30+15*math.cos(t*.56)
 if under:
  pts=[(x,y),(x-110,y+195),(x+110,y+195)];color=(100,235,218,28)
 else:pts=[(x,y),(x+dx-edge,90),(x+dx+edge,90)];color=(241,217,147,45)
 d.polygon(pts,fill=color)
 d.ellipse((x-15,y-15,x+15,y+15),fill=(244,197,87,83))
 return Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')

def character(d,x,y,t=0,scale=1,turn=False):
 # original simplified technician with readable red raincoat and antenna radio
 bob=1.8*math.sin(t*2.6);s=scale
 def p(dx,dy):return (int(x+dx*s),int(y+(dy+bob)*s))
 d.ellipse((*p(-36,71),*p(38,83)),fill=(9,16,25))
 d.line([p(-12,34),p(-16,70)],fill=(25,37,49),width=max(2,int(8*s)))
 d.line([p(10,34),p(13,70)],fill=(25,37,49),width=max(2,int(8*s)))
 d.polygon([p(-25,-12),p(23,-12),p(30,38),p(-27,38)],fill=(157,51,57),outline=(214,83,86))
 d.line([p(-2,-10),p(-2,38)],fill=(224,140,100),width=max(1,int(2*s)))
 d.line([p(-21,0),p(-30,26)],fill=(157,51,57),width=max(2,int(9*s)))
 d.line([p(21,0),p(31,8+3*math.sin(t*3))],fill=(157,51,57),width=max(2,int(8*s)))
 d.ellipse((*p(-15,-48),*p(15,-13)),fill=(160,146,128))
 d.pieslice((*p(-17,-50),*p(18,-18)),180,360,fill=(36,44,52))
 if not turn:
  d.ellipse((*p(-8,-33),*p(-5,-29)),fill=(17,24,30))
  d.ellipse((*p(5,-33),*p(8,-29)),fill=(17,24,30))
 d.rectangle((*p(31,-2),*p(41,17)),fill=(21,35,46),outline=(84,123,132),width=1)
 d.line([p(36,-2),p(40,-11)],fill=(159,172,178),width=max(1,int(s)))

def callout(d,x,y,s,red=False,size=12):
 ww=font(size).getlength(s)+23;rect(d,(x,y,x+ww,y+29),(174,58,68) if red else (215,207,175),rad=3)
 txt(d,(x+ww/2,y+15),s,size,(254,248,238) if red else (20,25,32),'mm')

def waves(d,x,y,t,n=4,c=CYAN):
 for i in range(n):
  r=14+i*20+(t*14%20)
  d.arc((x-r,y-r,x+r,y+r),55,310,fill=c,width=2)

def main_scene(kind,t,duration,index):
 im=base(index*31+19);d=ImageDraw.Draw(im)
 prog=ease(t/duration)
 if kind in ('coast','beacon','beam','arrival'):
  sea(d,t)
  lighthouse(d,275,480,1.12,lights=kind!='beam' or t<duration*.6,t=t)
  if kind=='arrival':
   character(d,125,501,t,1.55)
   line(d,[(155,475),(205,422)],(110,130,134),2)
   callout(d,25,120,'БЕРЕГОВОЙ ПОСТ № 7')
  elif kind=='coast':
   callout(d,22,121,'СМОТРИТЕЛЬ НЕ НА СВЯЗИ',True)
   for k in range(3):d.ellipse((47+k*25,177,59+k*25,189),fill=RED if k==2 else GRAY)
  elif kind=='beacon':
   callout(d,20,126,'СВЕТ БЕЗ ПИТАНИЯ',True)
   for k in range(6):
    xx=35+k*57;d.ellipse((xx,200,xx+14,214),fill=YELLOW if int((t*1.5+k)%3)==0 else (52,65,74))
  elif kind=='beam':
   callout(d,24,120,'ИСТОЧНИК СВЕТА ?')
   line(d,[(270,210),(225,285),(145,330)],RED,3)
   d.ellipse((136,320,152,336),fill=RED)
  im=beam(im,t,x=275,y=172,bright=kind!='beam' or t<duration*.55)
 elif kind in ('switch','poweroff'):
  d.rectangle((52,156,376,541),fill=(23,39,52),outline=(100,117,121),width=3)
  for k in range(3):
   x=101+k*109
   rect(d,(x-35,226,x+35,305),(14,25,35),rad=6,outline=(93,114,127),width=3)
   d.ellipse((x-19,237,x+19,274),fill=(36,51,62),outline=(112,133,139),width=3)
   line(d,[(x,255),(x+math.sin(t+k)*12,242)],YELLOW,3)
   txt(d,(x,288),['ТОК','ЛУЧ','СВЯЗЬ'][k],12,GRAY,'mm')
  rect(d,(148,345,280,450),(40,48,56),rad=9,outline=(118,121,117),width=4)
  angle=60 if kind=='switch' else 90*ease(t/duration)
  line(d,[(212,413),(212+55*math.sin(angle*math.pi/180),413-58*math.cos(angle*math.pi/180))],RED,9)
  d.ellipse((202,403,222,423),fill=(134,147,148))
  callout(d,63,118,'ГЕНЕРАТОР: ВЫКЛ',True)
  if kind=='poweroff' and t>duration*.45:
   rect(d,(96,480,328,514),RED,rad=4);txt(d,(212,498),'ПИТАНИЕ ОТКЛЮЧЕНО',12,PALE,'mm')
 elif kind=='timeline':
  callout(d,25,115,'ЖУРНАЛ ВСПЫШЕК')
  txt(d,(216,183),'ИНТЕРВАЛЫ СИГНАЛА',19,PALE,'mm')
  line(d,[(37,322),(394,322)],(99,123,137),5)
  pts=[62,177,291,361]
  for i,x in enumerate(pts):
   d.ellipse((x-10,312,x+10,332),fill=YELLOW if i<3 else RED)
   txt(d,(x,355),['0','8','16','20'][i],16,PALE,'mm')
  marker=37+prog*356
  line(d,[(marker,290),(marker,337)],RED,4)
  for i,s in enumerate(['8 СЕК','8 СЕК','4 СЕК']):
   rect(d,(38+i*121,405,147+i*121,453),(27,48,62),rad=9)
   txt(d,(93+i*121,430),s,15,YELLOW if i<2 else RED,'mm')
 elif kind in ('radar','depth'):
  cx,cy=216,346
  d.ellipse((55,185,377,507),fill=(15,40,47),outline=(76,126,130),width=3)
  for r in (38,77,118,153):d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(49,94,95),width=2)
  line(d,[(cx,187),(cx,505)],(48,80,89),2);line(d,[(57,cy),(375,cy)],(48,80,89),2)
  ang=t*.95
  line(d,[(cx,cy),(cx+150*math.cos(ang),cy+150*math.sin(ang))],CYAN,4)
  d.ellipse((cx-9,cy-9,cx+9,cy+9),fill=YELLOW)
  xx,yy=(268,409) if kind=='radar' else (245,449)
  d.ellipse((xx-11,yy-11,xx+11,yy+11),fill=RED)
  waves(d,xx,yy,t,3,RED)
  callout(d,16,115,'ВТОРОЙ ИСТОЧНИК',True) if kind=='radar' else callout(d,15,115,'ГЛУБИНА 42 М')
  if kind=='depth':txt(d,(216,556),'42 МЕТРА ПОД ПОВЕРХНОСТЬЮ',14,YELLOW,'mm')
 elif kind=='camera':
  d.rounded_rectangle((30,152,401,551),radius=18,fill=(29,41,53),outline=(127,144,141),width=5)
  rect(d,(52,182,377,511),(8,30,43),rad=5)
  for k in range(8):
   yy=284+k*25
   for x in range(-50,455,110):
    line(d,[(x+(t*15+k*16)%110,yy),(x+64+(t*15+k*16)%110,yy+2)],(31,81,91),2)
  bright= .6+.4*math.sin(t*3)
  d.ellipse((231,365,267,400),fill=(89,223,212) if bright>.78 else (43,128,125))
  waves(d,250,382,t,2,CYAN)
  txt(d,(67,194),'REC',18,RED);d.ellipse((116,184,128,196),fill=RED if int(t*2)%2 else (44,51,57))
  txt(d,(365,193),'00:47',14,PALE,'ra')
  callout(d,73,108,'КАМЕРА: ВОДА')
 elif kind=='map':
  d.polygon([(41,199),(107,176),(162,203),(239,185),(385,212),(383,512),(307,532),(218,508),(141,541),(49,518)],fill=(214,200,157),outline=(95,111,121))
  for x in range(60,385,60):line(d,[(x,190),(x+10,522)],(171,159,129),1)
  for y in range(232,523,50):line(d,[(47,y),(382,y+8)],(176,160,126),1)
  d.polygon([(53,193),(100,210),(124,330),(101,398),(70,465)],fill=(80,110,107))
  d.ellipse((263,354,285,376),fill=RED)
  txt(d,(273,384),'МАЯК',14,(21,27,33),'mt')
  line(d,[(274,366),(349,306)],RED,4)
  callout(d,18,112,'ПОДВОДНЫХ ОБЪЕКТОВ НЕТ',True)
 elif kind=='cable':
  d.polygon([(0,430),(120,415),(301,422),(432,406),(432,610),(0,610)],fill=(9,34,48))
  line(d,[(65,185),(65,416),(335,420),(335,546)],(127,145,149),6)
  for k in range(3):
   x=94+k*112;y=420
   waves(d,x,y,t+k*.5,2,YELLOW)
   d.ellipse((x-10,y-10,x+10,y+10),fill=RED if int(t*3+k)%3==0 else YELLOW)
  d.rectangle((287,536,382,574),fill=(24,48,61),outline=(96,130,130),width=2)
  callout(d,28,119,'КАБЕЛЬ ПОД ВОДОЙ')
 elif kind=='pulses':
  callout(d,24,115,'НЕИЗВЕСТНЫЙ КОД',True)
  txt(d,(216,210),'ТРИ ИМПУЛЬСА',23,PALE,'mm')
  for i in range(3):
   x=80+i*130
   d.ellipse((x-28,290,x+28,347),fill=RED if t>(i*.7) else (43,54,64))
   txt(d,(x,375),str(i+1),16,PALE,'mm')
  r=int((t*39)%130)
  for k in range(3):d.arc((216-r-k*25,478-r/2-k*15,216+r+k*25,478+r/2+k*15),210,330,fill=CYAN,width=3)
 elif kind in ('below','deep_tower','figure'):
  sea(d,t,y=225)
  d.rectangle((0,225,W,630),fill=(8,24,37))
  for k in range(9):
   y=259+k*36;line(d,[(-10,y),(430,y+4)],(15,48+3*k,59+2*k),2)
  d.polygon([(0,593),(165,573),(252,592),(431,561),(431,639),(0,639)],fill=(18,37,42))
  lighthouse(d,238,581,.88,lights=True,t=t,under=True)
  im=beam(im,t,x=238,y=303,bright=True,under=True)
  d=ImageDraw.Draw(im)
  if kind=='below':callout(d,24,113,'СВЕТ СО ДНА',True)
  elif kind=='deep_tower':
   callout(d,19,113,'ВТОРОЙ МАЯК',True)
   line(d,[(70,370),(158,428)],CYAN,4)
   txt(d,(72,353),'42 М',16,YELLOW)
  else:
   callout(d,19,110,'КТО ТАМ СТОИТ?',True)
   xx=238;yy=310
   d.ellipse((xx-6,yy-15,xx+6,yy-3),fill=(168,184,178))
   line(d,[(xx,yy-3),(xx,yy+18)],(145,160,159),5)
   line(d,[(xx,yy+3),(xx+15,yy-11+3*math.sin(t*3))],(145,160,159),4)
   line(d,[(xx,yy+18),(xx-8,yy+32)],(145,160,159),3)
   line(d,[(xx,yy+18),(xx+8,yy+32)],(145,160,159),3)
   waves(d,xx,yy,t,3,YELLOW)
 elif kind=='mirror':
  rect(d,(30,118,402,600),(18,31,43),rad=12,outline=(97,131,141),width=3)
  rect(d,(48,141,385,575),(10,37,49),rad=8)
  # camera view of distant self in red coat, no copied characters
  character(d,224,411,t,1.9,turn=True)
  txt(d,(72,169),'LIVE / 42М',17,PALE)
  callout(d,45,109,'ТАКОЙ ЖЕ ПЛАЩ',True)
  line(d,[(315,430),(275,407)],YELLOW,3)
 elif kind in ('warning','end'):
  rect(d,(27,145,406,550),(10,18,32),rad=13,outline=(102,111,123),width=3)
  for k in range(9):
   y=195+k*30;line(d,[(39,y),(396,y+2)],(26,41,56),1)
  if kind=='warning':
   txt(d,(216,275),'СООБЩЕНИЕ',18,GRAY,'mm')
   txt(d,(216,343),'НЕ',55,RED,'mm')
   txt(d,(216,419),'ОБОРАЧИВАЙСЯ',33,PALE,'mm')
   if int(t*5)%4==0:rect(d,(30,301,405,311),(105,22,32))
  else:
   character(d,160,405,t,1.7)
   d.ellipse((318,311,339,337),fill=(8,11,19))
   d.polygon([(311,330),(343,329),(362,467),(291,467)],fill=(7,11,18))
   callout(d,41,119,'ШАГИ ЗА СПИНОЙ',True)
 # tiny film noise points in middle area
 d=ImageDraw.Draw(im)
 rng=random.Random(99+index)
 for j in range(16):
  xx=(rng.randint(15,W-15)+int(t*4))%W; yy=(rng.randint(120,620)+int(t*7))%H
  d.point((xx,yy),fill=(43,57,67))
 return im

HIGHLIGHT={'НИКТО','ПРОПАЛ','НЕ','ВЫКЛЮЧЕН','САМА','ВОСЕМЬ','ЧЕТЫРЕ','СНИЗУ','ВТОРОЙ','ПОД','ГЛУБИНЕ','СОРОК','ДВА','ТРИ','ВОДЫ','ЯРЧЕ','КОПИИ','МНЕ','МОЙ','ПЛАЩ','ОБОРАЧИВАЙСЯ','ШАГИ','ОДНА'}

def split_phrases(text):
 import re
 words=text.replace('—','—').split();out=[];line=[]
 for word in words:
  line.append(word)
  if len(line)>=4 or (len(line)>=2 and word[-1:] in '.!?'):
   out.append(' '.join(line));line=[]
 if line:out.append(' '.join(line))
 return out

def caption(im,text,t,duration):
 phrases=split_phrases(text)
 if not phrases:return im
 # pacing approximated by word and character length; cues are scene-relative
 weights=[max(4,sum(len(w) for w in ph.split())) for ph in phrases]
 v=clamp((t-.1)/max(duration-.25,.1))*sum(weights)
 accum=0;idx=len(phrases)-1
 for i,w in enumerate(weights):
  accum+=w
  if v<accum:idx=i;break
 s=phrases[idx].upper()
 d=ImageDraw.Draw(im)
 rect(d,(0,608,W,768),(5,8,17))
 line(d,[(0,608),(W,608)],(31,42,55),2)
 lines=[''];size=33
 while size>=24:
  lines=['']
  for word in s.split():
   trial=(lines[-1]+' '+word).strip()
   if font(size).getlength(trial)>W-38 and lines[-1]:lines.append(word)
   else:lines[-1]=trial
  if len(lines)<=2:break
  size-=1
 if len(lines)>2:lines=lines[:2]
 yy=658 if len(lines)==1 else 634
 for row in lines:
  parts=row.split();totalw=sum(font(size).getlength(w) for w in parts)+(len(parts)-1)*font(size).getlength(' ')
  xx=(W-totalw)/2
  for w in parts:
   norm=''.join(x for x in w if x.isalpha())
   c=RED if norm in ('НЕ','НИКТО','ПРОПАЛ','ВЫКЛЮЧЕН','ОБОРАЧИВАЙСЯ','ШАГИ','ОДНА') else YELLOW if norm in HIGHLIGHT else PALE
   d.text((xx,yy),w,font=font(size),fill=c,stroke_width=1,stroke_fill=(6,10,18))
   xx+=font(size).getlength(w+' ')
  yy+=42
 return im

def overlay(im,i,n,t,scene):
 d=ImageDraw.Draw(im)
 txt(d,(18,21),'НОЧНОЙ ПРОТОКОЛ',13,GRAY)
 txt(d,(W-16,23),f'{i+1:02d}/{n:02d}',11,GRAY,'ra')
 for k in range(n):
  x=18+k*(W-36)/n
  rect(d,(x,50,x+(W-48)/n*.80,54),YELLOW if k==i else RED if k<i else (47,58,69),rad=2)
 txt(d,(18,72),'ПОСТ № 7  ·  00:47',10,GRAY)
 return im

def synth_espeak(text,path):
 run=subprocess.run(['espeak','-v','ru','-s','157','-p','46','-a','145','-w',str(path),text],capture_output=True)
 if run.returncode:raise RuntimeError(run.stderr.decode(errors='replace'))
 with wave.open(str(path)) as f:
  sr=f.getframerate();a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768
  channels=f.getnchannels()
  if channels>1:a=a.reshape(-1,channels).mean(axis=1)
  if sr!=SR:a=np.interp(np.arange(round(len(a)*SR/sr))/SR,np.arange(len(a))/sr,a).astype(np.float32)
 return a

def synth_edge(text,path,voice='ru-RU-SvetlanaNeural'):
 """Microsoft Edge neural voice. Requires edge-tts and a network connection.
 A failed neural synthesis is a hard error (no secret switch to robotic voice).
 """
 media=path.with_suffix('.mp3')
 cmd=['edge-tts','--voice',voice,'--rate=-6%','--pitch=-5Hz','--text',text,'--write-media',str(media)]
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
 if result.returncode or not media.exists():
  raise RuntimeError('Edge TTS unavailable: '+result.stderr[-600:])
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(media),'-ar',str(SR),'-ac','1','-sample_fmt','s16',str(path)]
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 if result.returncode:raise RuntimeError('Cannot decode neural narration: '+result.stderr[-400:])
 with wave.open(str(path)) as wf:
  raw=wf.readframes(wf.getnframes())
 return np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768

def synth_piper(text,path):
 """Offline Russian neural TTS using the Piper Irina model."""
 import urllib.request
 model_dir=HERE/'voice_models';model_dir.mkdir(parents=True,exist_ok=True)
 root='https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/'
 basename='ru_RU-irina-medium.onnx'
 for name in (basename,basename+'.json'):
  target=model_dir/name
  if not target.exists() or target.stat().st_size<(100000 if name.endswith('.onnx') else 100):
   urllib.request.urlretrieve(root+name+'?download=true',target)
 if not shutil.which('piper'):
  raise RuntimeError('Piper CLI not installed')
 result=subprocess.run(['piper','--model',str(model_dir/basename),'--output_file',str(path)],
                       input=text+'\n',text=True,capture_output=True,timeout=150)
 if result.returncode or not path.exists():
  raise RuntimeError('Piper synthesis failed: '+result.stderr[-500:])
 with wave.open(str(path)) as wf:
  rate=wf.getframerate();channels=wf.getnchannels();raw=wf.readframes(wf.getnframes())
 audio=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768
 if channels>1:audio=audio.reshape(-1,channels).mean(axis=1)
 if rate!=SR:
  audio=np.interp(np.arange(round(len(audio)*SR/rate))/SR,np.arange(len(audio))/rate,audio).astype(np.float32)
 return audio


def synth_neural(text,path):
 try:return synth_edge(text,path)
 except Exception as exc:
  print('Edge unavailable; trying Piper:',str(exc)[-200:],flush=True)
  return synth_piper(text,path)


def effects(kind,seed,dur):
 r=np.random.default_rng(seed);n=int(SR*dur);t=np.arange(n,dtype=np.float32)/SR
 s=.013*r.standard_normal(n).astype(np.float32)
 if kind in ('wind','steps','beacon','low','rumble'):
  s+=.024*np.sin(2*np.pi*(39*t+.3*np.sin(.21*t))).astype(np.float32)
 if kind in ('sonar','camera','depth'):
  for pos in np.arange(.5,dur,.92):
   beg=int(pos*SR);N=min(int(.6*SR),n-beg);tt=np.arange(N)/SR
   s[beg:beg+N]+=(.13*np.sin(2*np.pi*(560*tt-220*tt*tt))*np.exp(-tt*7)).astype(np.float32)
 if kind in ('tick','knock','switch','printer','impact','glitch'):
  spacing={'tick':.75,'knock':.4,'switch':10,'printer':.32,'impact':10,'glitch':.42}[kind]
  for pos in np.arange(.25,dur,spacing):
   beg=int(pos*SR);N=min(int(.16*SR),n-beg);tt=np.arange(N)/SR
   amp=.20 if kind in ('knock','impact') else .09
   s[beg:beg+N]+=(amp*(r.standard_normal(N)*.45+np.sin(2*np.pi*95*tt)) *np.exp(-tt*38)).astype(np.float32)
 if kind=='beacon':
  for pos in np.arange(1,dur,1.8):
   beg=int(pos*SR);N=min(int(.25*SR),n-beg);tt=np.arange(N)/SR
   s[beg:beg+N]+=(.10*np.sin(2*np.pi*650*tt)*np.exp(-tt*9)).astype(np.float32)
 if kind=='rumble':s+=.035*np.sin(2*np.pi*(27*t)).astype(np.float32)
 return s

def make_sound(shots,audios,durations,folder):
 n=int(sum(durations)*SR)
 stereo=np.zeros((n,2),dtype=np.float32)
 cursor=0
 for i,(scene,voice,dur) in enumerate(zip(shots,audios,durations)):
  num=int(dur*SR);bed=effects(scene['sfx'],100+i,dur)
  tt=np.arange(num)/SR
  # very quiet original tension bed
  drone=.012*np.sin(2*np.pi*(56*tt+.06*np.sin(.5*tt)))
  aa=bed+drone
  sound=np.stack((aa*(.90+.08*math.sin(i)),aa*(.88+.07*math.cos(i))),axis=1)
  start=int(.28*SR);amount=min(len(voice),num-start)
  if amount:
   sound[start:start+amount]*=.52
   volume=.63
   speech=voice[:amount]*volume
   fade=min(int(.07*SR),amount//4)
   if fade:
    speech[:fade]*=np.linspace(0,1,fade);speech[-fade:]*=np.linspace(1,0,fade)
   sound[start:start+amount,0]+=speech
   sound[start:start+amount,1]+=speech
  stereo[cursor:cursor+num]=sound
  cursor+=num
 peak=float(np.max(np.abs(stereo)))
 if peak>.90:stereo*=.90/peak
 stereo=np.tanh(stereo*1.2)
 out=folder/'audio.wav'
 with wave.open(str(out),'wb') as wf:
  wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(SR)
  wf.writeframes((np.clip(stereo,-1,1)*32767).astype('<i2').tobytes())
 return out

def render(args):
 doc=json.loads(Path(args.episode).read_text(encoding='utf-8'));shots=doc['scenes'];out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as temp:
  tmp=Path(temp)
  voices=[]
  backend=args.tts
  for i,s in enumerate(shots):
   target=tmp/f'{i:02d}.wav'
   if args.tts=='neural':
    if i==0:
     try:
      sample=synth_edge(s['text'],target)
      backend='edge'
     except Exception as exc:
      print('Edge unavailable; using Piper for ALL scenes:',str(exc)[-220:],flush=True)
      sample=synth_piper(s['text'],target)
      backend='piper'
    else:
     sample=synth_piper(s['text'],target) if backend=='piper' else synth_edge(s['text'],target)
   elif args.tts=='edge':sample=synth_edge(s['text'],target)
   else:sample=synth_espeak(s['text'],target)
   voices.append(sample)
  print('Voice backend selected:',backend,flush=True)
  durations=[]
  for s,v in zip(shots,voices):
   durations.append(math.ceil(max(3.6,len(v)/SR+.85)*FPS)/FPS)
  print('Scenes',len(shots),'duration',sum(durations),flush=True)
  audio=make_sound(shots,voices,durations,tmp)
  cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
       '-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0',
       '-i',str(audio),'-vf','scale=576:1024:flags=lanczos,fps=30',
       '-c:v','libx264','-preset','ultrafast','-crf','22','-pix_fmt','yuv420p',
       '-c:a','aac','-b:a','128k','-movflags','+faststart','-shortest',str(out)]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
  try:
   for i,(shot,duration) in enumerate(zip(shots,durations)):
    frames=int(duration*FPS)
    for k in range(frames):
     t=k/FPS
     im=main_scene(shot['kind'],t,duration,i)
     im=overlay(im,i,len(shots),t,shot)
     im=caption(im,shot['text'],t,duration)
     proc.stdin.write(im.tobytes())
    print(f'Scene {i+1:02d}/{len(shots)}: {shot["kind"]} {duration:.1f}s',flush=True)
   proc.stdin.close();err=proc.stderr.read().decode(errors='replace');ret=proc.wait()
  except Exception:
   proc.kill();proc.wait();raise
  if ret:raise RuntimeError(err[-1500:])
 print('DONE',out,round(out.stat().st_size/1024/1024,2),'MB',flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--episode',default=str(HERE/'episode.json'));p.add_argument('--output',default=str(HERE/'output'/'signal_underwater.mp4'));p.add_argument('--tts',choices=['neural','edge','espeak'],default='espeak')
 args=p.parse_args();render(args)
if __name__=='__main__':main()
