#!/usr/bin/env python3
"""Render an entire original 2D episode, no scanned storyboards or stock images.
Pass a neural-voice cue JSON and dry narration MP3 after online voice synthesis.
"""
import argparse,json,subprocess,math,sys,os
from pathlib import Path
from graphics import art,W,H
from audio import make_audio

def main():
 root=Path(__file__).resolve().parents[1]
 p=argparse.ArgumentParser()
 p.add_argument('--episode',default=str(root/'episodes/001.json'))
 p.add_argument('--output',default=str(root/'output/episode_001.mp4'))
 p.add_argument('--cue',default=None)
 p.add_argument('--narration',default=None)
 p.add_argument('--fps',type=int,default=24)
 p.add_argument('--quick',action='store_true')
 args=p.parse_args()
 episode=json.loads(Path(args.episode).read_text(encoding='utf8'))
 scenes=episode['scenes']
 if args.cue:
  speech=json.loads(Path(args.cue).read_text(encoding='utf8'))
  if len(speech)!=len(scenes):raise RuntimeError('Audio cue count must equal shot count')
  cues=[dict(id=s['id'],at=c['at'],end=c['end'],sfx=s['sfx'],text=s['text']) for s,c in zip(scenes,speech)]
 else:
  t=0;cues=[]
  for s in scenes:
   cues.append(dict(id=s['id'],at=t,end=t+s['seconds'],sfx=s['sfx'],text=s['text']))
   t+=s['seconds']
 output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
 wav=make_audio(cues,args.narration,output.parent)
 fps=args.fps
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
      '-video_size',f'{W}x{H}','-framerate',str(fps),'-i','pipe:0','-i',str(wav),'-map','0:v','-map','1:a',
      '-c:v','libx264','-preset','veryfast' if args.quick else 'medium','-crf','22','-pix_fmt','yuv420p',
      '-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=10','-movflags','+faststart','-shortest',str(output)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  for i,(s,c) in enumerate(zip(scenes,cues)):
   dur=c['end']-c['at']
   for frame in range(round(dur*fps)):
    t=frame/fps
    img=art(s['kind'],t,dur,i,s)
    proc.stdin.write(img.tobytes())
   print(f'{i+1:02d}/{len(scenes)} {s["kind"]} {dur:.2f}s',flush=True)
  proc.stdin.close()
  err=proc.stderr.read().decode(errors='replace');rc=proc.wait()
 except Exception:
  proc.kill();proc.wait();raise
 if rc:raise RuntimeError('FFmpeg failed '+err[-1500:])
 print('Created',str(output),output.stat().st_size,flush=True)
if __name__=='__main__':main()