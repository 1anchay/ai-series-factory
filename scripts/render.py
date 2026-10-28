#!/usr/bin/env python3
"""Free illustrated vertical short video builder. ChatGPT writes the JSON script."""
import argparse, json, math, random, shutil, subprocess, tempfile, urllib.request, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
BASE='https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SR=24000
def ff(n): return ImageFont.truetype(FONT,int(n))
def bg(w,h,seed):
    rng=np.random.default_rng(seed)
    z=np.linspace(0,1,h)[:,None,None]
    a=np.broadcast_to((1-z)*np.array([5,14,32])[None,None,:]+z*np.array([35,52,67])[None,None,:],(h,w,3)).copy()
    a+=rng.normal(0,2,(h,w,1))
    return Image.fromarray(np.uint8(a.clip(0,255)))
def heroine(d,cx,cy,s=1,evil=False):
    def p(x,y):return(int(cx+x*s),int(cy+y*s))
    def poly(x,c):d.polygon([p(*v) for v in x],fill=c)
    poly([(-65,105),(62,105),(108,280),(-110,280)],(11,25,40))
    poly([(-23,52),(25,52),(25,105),(-23,105)],(138,108,97))
    d.ellipse((p(-48,-84),p(48,75)),fill=(147,132,144) if evil else (180,140,117))
    poly([(-54,-40),(-59,-103),(-3,-130),(50,-104),(53,-34),(30,-80),(-10,-68),(-45,-57)],(8,17,29))
    for x in [-20,20]:
        d.ellipse((p(x-9,0),p(x+9,7)),fill=(226,121,125) if evil else (220,221,210))
        d.ellipse((p(x-3,1),p(x+3,7)),fill=(10,15,24))
    d.arc((p(-17,34),p(18,57 if evil else 45)),0,180,fill=(73,31,42),width=3)
    poly([(-60,75),(33,83),(61,116),(-60,128)],(169,42,53))
    poly([(26,102),(60,117),(26,230),(-5,208)],(179,41,55))
def city(d,w,h,seed):
    r=random.Random(seed);x=0
    while x<w+40:
        bw=r.randint(w//12,w//5);ht=r.randint(h//5,h//2);top=int(h*.87)-ht
        d.rectangle((x,top,x+bw,h),fill=(10+r.randrange(12),24,39))
        for xx in range(x+12,x+bw-9,20):
            for yy in range(top+18,int(h*.82),25):
                if r.random()<.16:d.rectangle((xx,yy,xx+5,yy+8),fill=(50,80,91))
        x+=bw+8
def render_scene(kind,w,h,seed):
    im=bg(w,h,seed);d=ImageDraw.Draw(im)
    city(d,w,h,seed)
    if kind in ('city','street','look_up'):
        cx=int(w*.62);l=int(w*.50);r=int(w*.79);top=int(h*.10)
        d.polygon([(l,top),(r,top),(r+35,h),(l-30,h)],fill=(12,27,42))
        for yy in range(top+20,h,32):d.line((l-20,yy,r+26,yy),fill=(39,58,72),width=2)
        for xx in range(l+14,r,27):d.line((xx,top,xx-15,h),fill=(38,55,69),width=2)
        wx=int(w*.66);wy=int(h*.31)
        d.rectangle((wx-10,wy-14,wx+15,wy+21),fill=(255,195,93))
    if kind=='street':heroine(d,w*.35,h*.70,1.5)
    if kind=='look_up':heroine(d,w*.46,h*.82,1.8)
    if kind=='phone':
        d.rounded_rectangle((w*.22,h*.24,w*.80,h*.81),radius=35,fill=(9,18,24),outline=(57,117,129),width=10)
        d.rounded_rectangle((w*.25,h*.28,w*.77,h*.76),radius=22,fill=(15,48,57))
        d.text((w*.29,h*.39),'03:17',font=ff(w*.054),fill=(187,230,230))
        d.text((w*.29,h*.49),'НЕ СМОТРИ',font=ff(w*.047),fill=(250,100,110))
        d.text((w*.29,h*.55),'ВВЕРХ',font=ff(w*.076),fill=(252,113,120))
    if kind=='window':
        d.rectangle((w*.13,h*.22,w*.86,h*.78),fill=(129,98,77),outline=(230,172,98),width=16)
        heroine(d,w*.50,h*.49,1.55,True)
        d.line((w*.50,h*.22,w*.50,h*.78),fill=(35,44,55),width=12)
    if kind=='double':
        d.rectangle((w*.5,0,w,h),fill=(52,30,50))
        heroine(d,w*.27,h*.44,1.3)
        heroine(d,w*.75,h*.44,1.3,True)
        d.line((w*.5,0,w*.5,h),fill=(122,146,164),width=9)
    return im
def text_lines(txt,f,w):
    a=[];s=''
    for word in txt.split():
        nxt=(s+' '+word).strip()
        if f.getlength(nxt)>w and s:a.append(s);s=word
        else:s=nxt
    if s:a.append(s)
    return a
def make_frame(base,w,h,at,duration,scene,n,series):
    W,H=base.size;progress=min(1,at/duration)
    cw=int(w*(1.09-.05*progress));ch=int(h*(1.09-.05*progress))
    x=max(0,min(W-cw,int((W-cw)*(.35+.30*progress))))
    y=max(0,min(H-ch,int((H-ch)*(.35+.30*progress))))
    im=base.crop((x,y,x+cw,y+ch)).resize((w,h),Image.Resampling.BICUBIC)
    d=ImageDraw.Draw(im,'RGBA');rng=random.Random(1024+n)
    for _ in range(100):
        xx=rng.randint(0,w);yy=int((rng.randint(0,h)+at*rng.randint(130,330))%h)
        d.line((xx,yy,xx+8,yy+29),fill=(173,201,215,70),width=1)
    for yy in range(int(h*.68),h,2):
        d.rectangle((0,yy,w,yy+2),fill=(0,0,8,int(175*(yy/h-.68)/.32)))
    d.text((int(w*.05),int(h*.055)),series,font=ff(w*.037),fill=(231,233,236))
    f=ff(w*.054);lines=text_lines(scene['subtitle'],f,w*.88)
    for j,line in enumerate(lines[:4]):
        d.text((w/2,int(h*.79)+j*int(w*.074)),line,font=f,fill='white',anchor='mt',stroke_width=3,stroke_fill=(2,10,22))
    if n==1 and at<2.4:
        d.text((w/2,h*.24),series,font=ff(w*.078),fill='white',anchor='mm',stroke_width=2,stroke_fill=(2,10,22))
    if n==6 and at>duration-2:
        d.text((w/2,h*.30),'ПРОДОЛЖЕНИЕ СЛЕДУЕТ',font=ff(w*.032),fill=(255,211,213),anchor='mm')
    fade=min(1,at/.28,(duration-at)/.28)
    if fade<1:d.rectangle((0,0,w,h),fill=(0,0,0,int(255*(1-max(0,fade)))))
    return im
def voice_clips(scenes,folder,skip):
    if skip:return [np.array([],dtype=np.float32) for _ in scenes]
    import os
    from urllib.request import urlretrieve
    model_dir=folder/'voice';model_dir.mkdir()
    name='ru_RU-dmitri-medium.onnx'
    for part in (name,name+'.json'):
        print('Download Piper:',part,flush=True)
        urlretrieve(BASE+part+'?download=true',str(model_dir/part))
    result=[]
    for i,scene in enumerate(scenes):
        dest=folder/f'v{i}.wav'
        p=subprocess.run(['piper','--model',str(model_dir/name),'--output_file',str(dest)],input=scene['narration']+'\n',text=True,capture_output=True,timeout=120)
        if p.returncode:raise RuntimeError(p.stderr[-1200:])
        with wave.open(str(dest)) as f:
            rate=f.getframerate();arr=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768
            channels=f.getnchannels()
        if channels>1:arr=arr.reshape(-1,channels).mean(axis=1)
        if rate!=SR:arr=np.interp(np.arange(round(len(arr)*SR/rate))*rate/SR,np.arange(len(arr)),arr)
        result.append(arr.astype(np.float32))
    return result
def soundtrack(clips,durations,folder):
    N=int(round(sum(durations)*SR));t=np.arange(N,dtype=np.float32)/SR
    rng=np.random.default_rng(15)
    a=(.019*np.sin(t*2*np.pi*55)+.008*np.sin(t*2*np.pi*82)+.012*rng.standard_normal(N)).astype(np.float32)
    pos=0
    for clip,dur in zip(clips,durations):
        start=int(round(pos*SR))+int(.55*SR);l=min(len(clip),N-start)
        if l>0:a[start:start+l]+=.87*clip[:l]
        pos+=dur
    a[:SR//2]*=np.linspace(0,1,SR//2)
    a[-SR//2:]*=np.linspace(1,0,SR//2)
    dest=folder/'audio.wav'
    with wave.open(str(dest),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(np.int16(np.tanh(a)*32767).tobytes())
    return dest
def main():
    p=argparse.ArgumentParser();p.add_argument('--episode',required=True);p.add_argument('--output',required=True)
    p.add_argument('--no-tts',action='store_true');p.add_argument('--resolution',type=int,default=720)
    a=p.parse_args();doc=json.loads(Path(a.episode).read_text());scenes=doc['scenes'];w=a.resolution;h=w*16//9;fps=12
    if not shutil.which('ffmpeg'):raise RuntimeError('Install ffmpeg')
    with tempfile.TemporaryDirectory() as dirname:
        tmp=Path(dirname);clips=voice_clips(scenes,tmp,a.no_tts)
        durations=[max(float(s.get('seconds',5)),math.ceil((len(c)/SR+1.3)*fps)/fps) for s,c in zip(scenes,clips)]
        audio=soundtrack(clips,durations,tmp);out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
        cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','-','-i',str(audio),'-c:v','libx264','-preset','veryfast','-crf','25','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(out)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            for i,(s,dur) in enumerate(zip(scenes,durations),1):
                pic=ROOT/'assets'/f"{int(doc['episode']):03d}"/(s['id']+'.png')
                if pic.exists():
                    im=Image.open(pic).convert('RGB');ratio=max(w*1.3/im.width,h*1.3/im.height)
                    im=im.resize((math.ceil(im.width*ratio),math.ceil(im.height*ratio)))
                    W,H=im.size;base=im.crop(((W-int(w*1.3))//2,(H-int(h*1.3))//2,(W+int(w*1.3))//2,(H+int(h*1.3))//2))
                else:base=render_scene(s['art'],int(w*1.30),int(h*1.30),100+i)
                for j in range(round(dur*fps)):
                    proc.stdin.write(make_frame(base,w,h,j/fps,dur,s,i,doc['series']).tobytes())
                print('Rendered scene',i,flush=True)
        finally:
            proc.stdin.close()
        if proc.wait():raise RuntimeError('Video encoding failed')
    print('Created:',a.output)
if __name__=='__main__':main()
