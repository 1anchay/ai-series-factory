#!/usr/bin/env python3
"""Zavtra nas menshe: illustrated, animated, fully narrated vertical motion story."""
from __future__ import annotations
import argparse,json,sys,tempfile,subprocess,shutil,math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PROJECT_ROOT=ROOT.parent
sys.path.insert(0,str(Path(__file__).resolve().parent))
from voice import synthesize,SR
from v6_stage import present_frame
from art import subtitle_panel,hud
from sound import mix

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--episode',default=str(ROOT/'episodes/001.json'))
    p.add_argument('--output',default=str(ROOT/'output/001.mp4'))
    p.add_argument('--voice',choices=['auto','edge','piper','espeak'],default='auto')
    p.add_argument('--fps',type=int,choices=[10,12,18,20,24,30],default=20)
    p.add_argument('--width',type=int,choices=[360,720,1080],default=720)
    a=p.parse_args()
    if not shutil.which('ffmpeg'):raise RuntimeError('ffmpeg missing')
    doc=json.loads(Path(a.episode).read_text(encoding='utf8'))
    shots=doc['scenes']
    if not 8<=len(shots)<=24:raise ValueError('Only 8-24 meaningful shots per episode are supported')
    if doc.get('version','').startswith('6.') and len(shots)!=10:raise ValueError('v6 pilot must have exactly 10 purposeful scenes')
    for s in shots:
        if not s.get('voice'):raise ValueError('No line to narrate in shot '+s.get('id','?'))
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='znm_') as tmpstr:
        tmp=Path(tmpstr)
        spoken=synthesize(shots,tmp,a.voice,PROJECT_ROOT/'voice_models')
        durations=[math.ceil(max(s['seconds'],len(v)/SR+.7)*a.fps)/a.fps for s,(v,_backend) in zip(shots,spoken)]
        audio=mix(shots,durations,[v for v,_ in spoken],tmp)
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
             '-video_size','360x640','-framerate',str(a.fps),'-i','pipe:0','-i',str(audio),'-map','0:v','-map','1:a',
             '-vf',f'scale={a.width}:{a.width*16//9}:flags=lanczos', '-c:v','libx264','-preset','veryfast','-crf','21',
             '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','48000','-ac','2','-movflags','+faststart','-shortest',str(dest)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            for i,(scene,duration,(samples,backend)) in enumerate(zip(shots,durations,spoken)):
                for frame in range(int(duration*a.fps)):
                    t=frame/a.fps
                    im=present_frame(scene['kind'],t,duration,i,int(doc['episode']),scene)
                    im=hud(im,scene['kind'],i,t,duration,int(doc['episode']))
                    im=subtitle_panel(im,scene['voice'],t,len(samples)/SR)
                    proc.stdin.write(im.tobytes())
                print(f'Shot {i+1:02d}/{len(shots)}: {scene["kind"]} {duration:.1f}s {backend}',flush=True)
            proc.stdin.close();stderr=proc.stderr.read().decode(errors='replace');rc=proc.wait()
        except Exception:
            proc.kill();proc.wait();raise
        if rc:raise RuntimeError('ffmpeg error: '+stderr[-2500:])
    if not dest.exists() or dest.stat().st_size<10000:raise RuntimeError('Video missing or empty')
    print('Created',dest,'total seconds:',sum(durations),flush=True)

if __name__=='__main__':main()
