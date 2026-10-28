#!/usr/bin/env python3
"""v0.7: staged full-screen cinematic scenes, readable captions, real layered movement.
No generated storyboard collages. Online Edge TTS optional; local Piper fallback.
"""
from __future__ import annotations
import argparse
import math
import os
import re
import subprocess
import tempfile
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import render as legacy
from soundscape import create_soundtrack

ROOT = Path(__file__).resolve().parents[1]
SR=24000

def font(sz, bold=True):
    return legacy.font(sz, bold)

def ease(t):
    x=max(0.,min(1.,t));return x*x*(3-2*x)

def cover(im,w,h):
    r=max(w/im.width,h/im.height)
    nw,nh=math.ceil(im.width*r),math.ceil(im.height*r)
    im=im.resize((nw,nh),Image.Resampling.LANCZOS)
    l=(nw-w)//2;top=(nh-h)//2
    return im.crop((l,top,l+w,top+h))

def assets(w,h):
    asset_dir=ROOT/'assets'/'001'
    city=Image.open(asset_dir/'01_city.jpg').convert('RGB')
    # Crop out the unwanted face from city background; show the tower and city.
    city=cover(city.crop((0,0,city.width,int(city.height*.75))),w,h)
    full=Image.open(asset_dir/'02_vera.jpg').convert('RGB')
    # Cutout of the entire standing heroine, with feathered edges.
    mask=Image.new('L',full.size,0)
    d=ImageDraw.Draw(mask)
    fw,fh=full.size
    poly=[(.35,.44),(.40,.42),(.49,.40),(.59,.425),(.63,.46),(.63,.53),(.74,.60),(.80,.76),(.84,1),(.20,1),(.215,.77),(.26,.61),(.32,.55),(.30,.49)]
    d.polygon([(int(x*fw),int(y*fh)) for x,y in poly],fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(max(3, fw//95)))
    cutout=full.convert('RGBA');cutout.putalpha(mask)
    cutout=cover(cutout,w,h)
    window=Image.open(asset_dir/'05_window.jpg').convert('RGB')
    # IMPORTANT: the legacy shot contains an embedded storyboard in a blurred
    # frame. Strip the frame entirely instead of enlarging the letterbox.
    ww,wh=window.size
    window=window.crop((int(ww*.44), int(wh*.260), int(ww*.963), int(wh*.779)))
    return {'city':city.convert('RGBA'),'girl':cutout,'window':cover(window,w,h).convert('RGBA')}

def draw_caption(base,txt,w,h):
    if not txt:return
    d=ImageDraw.Draw(base,'RGBA')
    size=max(18,round(w*.047))
    f=font(size)
    words=txt.split(); lines=[]; line=''
    for word in words:
        s=(line+' '+word).strip()
        if f.getlength(s)>w*.87 and line:
            lines.append(line);line=word
        else:line=s
    if line:lines.append(line)
    lines=lines[:2]
    if not lines:return
    lh=int(size*1.34);total=len(lines)*lh
    cy=int(h*.82)
    top=cy-total//2-13
    d.rounded_rectangle((int(w*.055),top,int(w*.945),top+total+24),radius=int(w*.024),fill=(4,8,17,185))
    for j,line in enumerate(lines):
        d.text((w//2,top+12+j*lh),line,font=f,fill=(255,255,255,255),anchor='mt',stroke_width=1,stroke_fill=(3,8,12,245))

def sentence_pages(text):
    p=[x.strip() for x in re.split(r'(?<=[.!?…])\s+',text.strip()) if x.strip()]
    if len(p)>=2:return [p[0], ' '.join(p[1:])]
    words=text.split()
    if len(words)>11:
        k=len(words)//2;return [' '.join(words[:k]),' '.join(words[k:])]
    return [text]

def frame(scene,idx,t,duration,kit,w,h,voice_duration=0):
    progress=ease(t/duration)
    # Stationary framing: <=1% camera drift and absolutely no portrait push-in.
    dx=int(w*.007*math.sin(t*.45+idx));dy=int(h*.006*math.cos(t*.42+idx))
    city=kit['city'];base=Image.new('RGBA',(w,h),(4,10,21,255))
    if idx in (1,2,3,4):
        base.alpha_composite(city,(dx,dy))
        # Active depth: distant clouds drift independently of foreground rain.
        fog=Image.new('RGBA',(w,h),(0,0,0,0));fd=ImageDraw.Draw(fog,'RGBA')
        for k in range(6):
            left=int(w*((k*.24+t*.015)%1.6-.3))
            yy=int(h*(.30+k*.075)+7*math.sin(t*.7+k))
            fd.ellipse((left-w*.24,yy-h*.05,left+w*.22,yy+h*.055),fill=(135,171,198,9))
        fog=fog.filter(ImageFilter.GaussianBlur(max(4,w//60)))
        base=Image.alpha_composite(base,fog)
    else:
        # Different framing for the double: tower with luminous window, not another face close-up.
        base.alpha_composite(kit['window'],(dx,dy))
    if idx in (2,3,4):
        # Real object movement: the heroine is cut out and moves separately from city.
        bob=int(h*.0038*math.sin(t*2.35))
        walk=int(w*.016*math.sin(t*.67))
        if idx==4:walk=int(w*.025*progress)
        base.alpha_composite(kit['girl'],(walk, bob))
    d=ImageDraw.Draw(base,'RGBA')
    if idx==1:
        # A wave of city windows goes dark in sequence.
        for j in range(9):
            x=int(w*(.21 + ((j*113)%67)/100));y=int(h*(.10+((j*73)%52)/100))
            amount=max(0,1-(t*.6-j*.19))
            if amount>0:d.rectangle((x,y,x+max(2,w//140),y+max(4,h//140)),fill=(236,185,98,int(100*amount)))
    if idx==3:
        # Animated PHONE: the handset moves and the screen lights up, independent of heroine.
        pw=int(w*.29);ph=int(h*.37)
        cx=int(w*(.72+.025*math.sin(t*.8)))
        cy=int(h*(.53-.02*math.sin(t*1.05)))
        phone=Image.new('RGBA',(pw+12,ph+12),(0,0,0,0));pd=ImageDraw.Draw(phone,'RGBA')
        pd.rounded_rectangle((5,5,pw+5,ph+5),radius=int(pw*.12),fill=(6,10,20,240),outline=(111,138,154,255),width=4)
        pd.rounded_rectangle((int(pw*.08),int(ph*.07),int(pw*.94),int(ph*.93)),radius=12,fill=(18,46,58,255))
        pd.text((int(pw*.14),int(ph*.18)),'03:17',font=font(w*.028,False),fill=(170,240,244,255))
        if t>1.5:
            pd.text((int(pw*.11),int(ph*.43)),'НЕ СМОТРИ',font=font(w*.025),fill=(255,125,137,255))
            pd.text((int(pw*.21),int(ph*.55)),'ВВЕРХ',font=font(w*.033),fill=(255,125,137,255))
        base.alpha_composite(phone,(cx-pw//2,cy-ph//2))
    if idx==4:
        # Light from the tower pulses and a distant figure moves across the lit window.
        ax=int(w*.71);ay=int(h*.24)
        p=.55+.45*math.sin(t*2.4)
        halo=Image.new('RGBA',(w,h),(0,0,0,0));hd=ImageDraw.Draw(halo,'RGBA')
        hd.ellipse((ax-35,ay-38,ax+35,ay+42),fill=(255,183,75,int(15+20*p)))
        halo=halo.filter(ImageFilter.GaussianBlur(13));base=Image.alpha_composite(base,halo)
    if idx in (5,6):
        # Move the LIGHT inside the photographed window; keep real photographic
        # silhouette rather than drawing a pasted-on stick figure.
        lamp=Image.new('RGBA',(w,h),(0,0,0,0))
        ld=ImageDraw.Draw(lamp,'RGBA')
        shimmer=.5+.5*math.sin(t*1.15+idx)
        x=int(w*(.60+.02*math.sin(t*.38)));y=int(h*.33)
        ld.ellipse((x-int(w*.11),y-int(h*.10),x+int(w*.11),y+int(h*.10)),
                   fill=(254,175,72,int(11+17*shimmer)))
        lamp=lamp.filter(ImageFilter.GaussianBlur(max(5,w//30)))
        base=Image.alpha_composite(base,lamp)
        if idx==6 and t>duration*.60:
            veil=Image.new('RGBA',(w,h),(0,0,0,int(70*(t-duration*.6)/(duration*.4))))
            base=Image.alpha_composite(base,veil)
    # Animated rain in three depth bands. No blur, fake borders, or zoom in face.
    rain=Image.new('RGBA',(w,h),(0,0,0,0));rd=ImageDraw.Draw(rain,'RGBA')
    for layer in range(3):
        count=(65,32,12)[layer];spd=(290,550,900)[layer]
        for i in range(count):
            seed=idx*77+layer*179+i*83
            x=(seed*59)% (w+80)-40
            y=int((seed*97+t*spd)%(h+100))-50
            lw=(9,21,44)[layer]
            rd.line((x,y,x+lw//3,y+lw),fill=(182,214,228,(23,33,47)[layer]),width=1+(layer==2))
    base=Image.alpha_composite(base,rain)
    # Faint shadow only behind text, not over the lower half of the picture.
    pages=sentence_pages(scene['narration'])
    speech_window=min(duration-.35,max(1.0,voice_duration)) if voice_duration>0 else duration-.65
    spoken=max(0,t-.4)
    if len(pages)==1:caption=pages[0]
    else:
        ratio=len(pages[0])/max(1,sum(len(p) for p in pages))
        caption=pages[0] if spoken<speech_window*ratio else pages[1]
    if t<.42:caption=''
    draw_caption(base,caption,w,h)
    if idx==1 and t<2.0:
        d=ImageDraw.Draw(base)
        d.text((w//2,int(h*.19)),'ПОСЛЕ НУЛЯ',font=font(int(w*.071)),fill='white',anchor='mm',stroke_width=2,stroke_fill='#07131e')
    return base.convert('RGB')

def read_wave(path):return legacy.read_wav(path)

def edge_voice(scenes,tmp):
    voices=[]
    gender=os.getenv('SERIES_NARRATOR','irina').lower()
    voice='ru-RU-DmitryNeural' if gender in ('dmitri','denis','ruslan') else 'ru-RU-SvetlanaNeural'
    for i,sc in enumerate(scenes):
        mp3=tmp/f'edge{i}.mp3';wav=tmp/f'edge{i}.wav'
        c=subprocess.run(['edge-tts','--voice',voice,'--rate=-8%','--text',sc['narration'],'--write-media',str(mp3)],capture_output=True,text=True,timeout=65)
        if c.returncode or not mp3.exists() or mp3.stat().st_size<2000:
            raise RuntimeError(f'Edge TTS error on shot {i+1}: {c.stderr[-450:]}')
        ff=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(mp3),'-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(wav)],capture_output=True,timeout=30)
        if ff.returncode:raise RuntimeError('ffmpeg audio decode failed')
        v=read_wave(wav)
        if len(v)<SR:raise RuntimeError('TTS returned near-empty audio')
        voices.append(v)
    return voices

def voice_tracks(scenes,tmp,mode):
    if mode=='none':return [np.zeros(0,np.float32) for _ in scenes], 'none'
    if mode in ('edge','auto'):
        try:
            v=edge_voice(scenes,tmp)
            print('VOICE PROVIDER: Microsoft Edge Neural',flush=True)
            return v,'edge'
        except Exception as e:
            print('WARN: Edge TTS unavailable:',repr(e),' — switching to Piper',flush=True)
    v=legacy.synth_voices(scenes,tmp,False)
    if len(v)!=len(scenes) or any(len(a)<SR for a in v):
        raise RuntimeError('Narration missing, refusing silent export')
    print('VOICE PROVIDER: offline Piper',flush=True)
    return v,'piper'

def render(episode,output,width,fps,mode):
    import json
    doc=json.loads(Path(episode).read_text('utf-8'))
    scenes=doc['scenes'];w=width;h=int(width*16/9)
    if w not in (360,540,720,1080):raise ValueError('Resolution must be 360/540/720/1080')
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tdir:
        tmp=Path(tdir)
        voices,provider=voice_tracks(scenes,tmp,mode)
        durations=[math.ceil(max(float(s.get('seconds',5)),len(v)/SR+1.15,5.0)*fps)/fps for s,v in zip(scenes,voices)]
        soundtrack=create_soundtrack(scenes,voices,durations,tmp)
        kit=assets(w,h)
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}',
             '-r',str(fps),'-i','pipe:0','-i',str(soundtrack),'-c:v','libx264','-preset','veryfast',
             '-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',str(out)]
        p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            for i,(sc,seconds,vox) in enumerate(zip(scenes,durations,voices),start=1):
                for fr in range(round(seconds*fps)):
                    p.stdin.write(frame(sc,i,fr/fps,seconds,kit,w,h,len(vox)/SR).tobytes())
                print('Rendered',i,'/',len(scenes), 'length',seconds,'voice',round(len(vox)/SR,2),flush=True)
        except BaseException:
            p.stdin.close();p.kill();p.wait();raise
        p.stdin.close();err=p.stderr.read();rc=p.wait()
        if rc:raise RuntimeError('FFmpeg encoding failed: '+err.decode(errors='replace')[-1800:])
        if not out.exists() or out.stat().st_size<100000:
            raise RuntimeError('Output missing/suspiciously small')
        print('OUTPUT',str(out),'PROVIDER',provider,'SECONDS',sum(durations),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--episode',default='episodes/001.json')
    ap.add_argument('--output',default='output/episode_001.mp4');ap.add_argument('--resolution',type=int,default=720)
    ap.add_argument('--fps',type=int,default=20);ap.add_argument('--tts',choices=['auto','edge','piper','none'],default='auto')
    a=ap.parse_args();render(a.episode,a.output,a.resolution,a.fps,a.tts)
if __name__=='__main__':main()
