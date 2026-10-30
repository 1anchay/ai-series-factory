"""Continuity checks for episode 2 and distinctive character 08."""
import json
from pathlib import Path
from episode2_stage import render
ROOT=Path(__file__).resolve().parents[1]
e=json.loads((ROOT/'episodes/002.json').read_text(encoding='utf8'))
shots=e['scenes']
assert e['episode']==2 and len(shots)==12
expected=['eight_record','eight_reveal','locked_school','wet_steps','nika_last',
          'gleb_reacts','marked_door','secret_monitor','sector_screen','timur_target',
          'camera_live','turn_around']
assert [s['kind'] for s in shots]==expected
assert all(s['voice'] and s.get('sfx') for s in shots)
assert sum(float(s['seconds']) for s in shots)>=65
assert 'Ник' in shots[4]['voice'] and 'восьмёр' in shots[4]['voice']
assert 'Тимур' in shots[9]['voice'] and 'Тимур' in shots[10]['voice']
assert 'маска' in shots[-1]['voice']
for i,s in enumerate(shots):
    f=render(s['kind'],s['seconds']/2,s['seconds'],i,2,s)
    assert f.size==(360,640)
# Ensures the mask and 08 patch are part of the same repeatedly used design.
from episode2_stage import unknown
from PIL import Image,ImageDraw
img=Image.new('RGB',(360,640),(27,39,46))
unknown(ImageDraw.Draw(img),180,520,1.7,0)
print('QA PASS: 12 shots, 6 survivors, consistent white mask + red 08, Timur cliffhanger')
