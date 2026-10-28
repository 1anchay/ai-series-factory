"""Fast preflight checks. Prevents nonexistent scripts or files without an audio stream."""
import argparse,json,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--episode');p.add_argument('--video');p.add_argument('--width',type=int,default=720);a=p.parse_args()
 if a.episode:
  doc=json.loads(Path(a.episode).read_text(encoding='utf-8'))
  scenes=doc['scenes']
  assert 8<=len(scenes)<=24, 'Expected 8-24 scenes'
  ids=set()
  for i,s in enumerate(scenes):
   assert s['id'] not in ids, 'Duplicate scene id'
   ids.add(s['id'])
   assert len(s.get('voice','').split())>=3, f'Missing narration scene {i+1}'
   assert 2.5<=float(s.get('duration',0))<=8, f'Invalid scene duration {i+1}'
  print('Script OK:',doc['series'],'scenes:',len(scenes))
 if a.video:
  x=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',a.video],text=True,capture_output=True,check=True)
  info=json.loads(x.stdout)
  video=[s for s in info['streams'] if s['codec_type']=='video']
  audio=[s for s in info['streams'] if s['codec_type']=='audio']
  assert video and audio, 'Missing picture or sound'
  assert video[0]['width']==a.width and video[0]['height']==a.width*16//9,'Not full-frame vertical video'
  assert float(info['format']['duration'])>25,'Suspiciously short episode'
  print('MP4 OK: video, audio, full 9:16 frame, duration',info['format']['duration'])
if __name__=='__main__':main()
