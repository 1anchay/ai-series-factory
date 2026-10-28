#!/usr/bin/env python3
"""Frequency Zero: animated narrative Shorts, generated 2D assets, real TTS + original foley."""
from __future__ import annotations
import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image,ImageDraw
from art import render as render_art,hud,draw_text,font,CREAM,RED,AMBER,DEEP
from voice import synthesize,SR
from audio import create_mix

ROOT=Path(__file__).resolve().parents[1]


def chunks_for(text,limit=6):
    words=text.split(); chunks=[]; part=[]
    for word in words:
        part.append(word)
        if len(part)>=limit or (len(part)>=3 and word[-1:] in ('.','!','?',':',';')):
            chunks.append(' '.join(part));part=[]
    if part:chunks.append(' '.join(part))
    return chunks


def subtitle(d,w,h,scene,t,voice_length):
    # Each caption is an exact contiguous portion of the actual spoken transcript.
    caption_chunks=chunks_for(scene['voice'])
    elapsed=max(0,t-.16)
    frac=min(.999,elapsed/max(.1,voice_length))
    idx=min(len(caption_chunks)-1,int(frac*len(caption_chunks)))
    text=caption_chunks[idx]
    size=25
    # Split into at most 2 lines, dynamically shrink for extreme long words.
    while size>=16:
        f=font(size)
        words=text.split();lines=['']
        for word in words:
            trial=(lines[-1]+' '+word).strip()
            if f.getlength(trial)>w-45 and lines[-1]:lines.append(word)
            else:lines[-1]=trial
        if len(lines)<=2:break
        size-=1
    # Animated subtitle panel distinct from the artwork, always readable.
    box=Image.new('RGBA',(w,h),(0,0,0,0));bd=ImageDraw.Draw(box,'RGBA')
    top=515 if len(lines)==2 else 530
    bd.rounded_rectangle((12,top-23,w-12,612),radius=12,fill=(5,9,17,236),outline=(67,77,92,150),width=2)
    bd.rectangle((24,top-16,29,top+len(lines)*34),fill=RED)
    for j,line in enumerate(lines):
        width=f.getlength(line)
        # Accent highlights final words on dramatic beats without changing the spoken words.
        bd.text(((w-width)/2,top+j*33),line,font=f,fill=CREAM)
    return box


def draw_frame(scene,index,t,duration,voicelen,w,h):
    # Source paintings contain actual animated geometry; never scale/zoom a still photo.
    im=render_art(scene['kind'],t,duration,index,w,h)
    d=ImageDraw.Draw(im)
    hud(d,w,h,index,t)
    if t>.12 and t<duration-.10:
        over=subtitle(d,w,h,scene,t,voicelen)
        im=Image.alpha_composite(im.convert('RGBA'),over).convert('RGB')
    return im

len_scene=[15]

def main():
    p=argparse.ArgumentParser(description='Create original animated voiced 2D thriller short')
    p.add_argument('--episode',default=str(ROOT/'episodes/001.json'))
    p.add_argument('--output',default=str(ROOT/'output/frequency_zero_001.mp4'))
    p.add_argument('--voice',choices=['auto','edge','piper','espeak'],default='auto',help='espeak is ONLY for offline diagnostic previews')
    p.add_argument('--width',type=int,choices=[360,540,720],default=720)
    p.add_argument('--fps',type=int,choices=[12,18,20,24,30],default=20)
    p.add_argument('--preview',action='store_true',help='Render at low resolution to test animation quickly')
    args=p.parse_args()
    episode=json.loads(Path(args.episode).read_text(encoding='utf-8'))
    scenes=episode['scenes']
    if not 8<=len(scenes)<=24:raise ValueError('Expected 8-24 short scenes')
    len_scene[0]=len(scenes)
    if args.voice=='espeak' and not args.preview:
        print('WARNING: eSpeak diagnostic voice, not recommended for publishing.',flush=True)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    frame_w=360;frame_h=640
    with tempfile.TemporaryDirectory(prefix='frequencyzero_') as temp:
        tmp=Path(temp)
        narration=synthesize(scenes,tmp,args.voice,ROOT/'voice_models')
        durations=[]
        for scene,(wave,engine) in zip(scenes,narration):
            # narration must be allowed to finish, with a small pause between shots
            durations.append(round(max(float(scene['duration']),len(wave)/SR+.56),2))
        audio=create_mix(scenes,durations,narration,tmp)
        effects=tmp/'effects_only.wav'
        if effects.exists():
            shutil.copyfile(effects,target.with_name(target.stem+'_effects.wav'))

        scale=[]
        if args.width!=frame_w:
            scale=['-vf',f'scale={args.width}:{args.width*16//9}:flags=lanczos']
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
             '-s',f'{frame_w}x{frame_h}','-r',str(args.fps),'-i','pipe:0','-i',str(audio),
             '-map','0:v:0','-map','1:a:0',*scale,'-c:v','libx264','-preset','veryfast',
             '-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',
             '-shortest',str(target)]
        print('Voices:',[engine for _,engine in narration],flush=True)
        print(f'Rendering {len(scenes)} scenes, {sum(durations):.1f} sec, output {args.width}x{args.width*16//9}',flush=True)
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            for i,(scene,duration,(wave,engine)) in enumerate(zip(scenes,durations,narration)):
                frames=round(duration*args.fps)
                for j in range(frames):
                    im=draw_frame(scene,i,j/args.fps,duration,len(wave)/SR,frame_w,frame_h)
                    proc.stdin.write(im.tobytes())
                print(f'  {i+1:02d}/{len(scenes)}: {scene["kind"]} [{duration:.1f}s, {engine}]',flush=True)
            proc.stdin.close();err=proc.stderr.read();rc=proc.wait()
        except Exception:
            proc.kill();proc.wait();raise
        if rc:raise RuntimeError('ffmpeg failed: '+err.decode(errors='replace')[-1800:])
    if not target.is_file() or target.stat().st_size<10000:raise RuntimeError('Output missing or incomplete')
    print('READY',target,'size',target.stat().st_size,flush=True)

if __name__=='__main__':main()
