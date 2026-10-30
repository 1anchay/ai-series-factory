"""Automated v6 story and art requirements. Run before production."""
import json
from pathlib import Path
import sys
from PIL import ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v6_stage import present_frame

DOC=Path(__file__).resolve().parents[1]/'episodes'/'001.json'
scenes=json.loads(DOC.read_text(encoding='utf-8'))['scenes']
assert len(scenes)==10, 'Pilot must contain 10 scenes'
assert sum(float(s['seconds']) for s in scenes)>=60, 'Narration timeline too short'
assert [s['kind'] for s in scenes]==[
'street','bedroom','bus','store','meeting','shelter','names','night','morning','recording']
assert 'блогер' in scenes[4]['voice'], 'Explain Nika is a blogger before she disappears'
assert 'камер' in scenes[4]['voice'].lower(), 'Show Nika camera before disappearance'
assert 'Нику' in scenes[8]['voice'], 'Mention missing Nika in morning scene'
assert 'восьмой' in scenes[9]['voice'], 'Reveal eighth person in final scene'
assert all(s.get('voice') and s.get('sfx') for s in scenes),'Every scene needs voice and sound'
for idx,s in enumerate(scenes):
    im1=present_frame(s['kind'],1.2,s['seconds'],idx,1,s)
    im2=present_frame(s['kind'],min(5.1,s['seconds']-.2),s['seconds'],idx,1,s)
    assert im1.size==(360,640)
    assert ImageChops.difference(im1,im2).getbbox(),f'Static scene: {s["id"]}'
print('v6 consistency, continuity and live-motion checks passed (10/10 scenes)')
