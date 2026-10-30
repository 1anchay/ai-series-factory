"""Narrative continuity and editorial quality checks for season 1 pilot."""
from __future__ import annotations
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
e=json.loads((root/'episodes/001.json').read_text(encoding='utf-8'))
scenes=e['scenes']
assert len(scenes)==18, f'Expected 18 shots; found {len(scenes)}'
assert len({s['id'] for s in scenes})==len(scenes)
assert scenes[0]['kind']=='cold_open' and scenes[-1]['kind']=='recording'
assert [s['kind'] for s in scenes].count('introductions')==3
assert 'Соне' in next(s['voice'] for s in scenes if s['id']=='02')
assert 'четыре сорок' in next(s['voice'] for s in scenes if s['id']=='11')
assert 'Ни́ка' in next(s.get('tts_text','') for s in scenes if s['id']=='08b')
assert all(s.get('voice') and s.get('seconds',0)>=2 for s in scenes)
assert scenes[-1].get('sfx')=='glitch'
print('Narrative QA passed:',len(scenes),'shots, human stakes, foreshadowing and twist')
