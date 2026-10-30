"""Editorial continuity checks: a fast 10-shot pilot, no introductions montage."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
e=json.loads((root/'episodes/001.json').read_text(encoding='utf-8'))
scenes=e['scenes']
expected=['street','bedroom','bus','store','meeting','shelter','names','night','morning','recording']
assert [s['kind'] for s in scenes]==expected
assert len({s['id'] for s in scenes})==len(scenes)==10
assert all(s.get('voice') and s.get('sfx') and s.get('seconds',0)>2 for s in scenes)
assert any(word in scenes[1]['voice'] for word in ('Соню','Сони','Соня')), 'Asya must mention her missing daughter'
assert 'четыре сорок' in scenes[3]['voice'] and 'четыре сорок' in scenes[7]['voice']
assert any(x in scenes[4]['voice'] for x in ('семеро','шестерых')) and 'шестеро' in scenes[8]['voice']
assert 'восьмой' in scenes[-1]['voice']
assert 'видеоблогер' in scenes[4]['voice'] and 'камеру' in scenes[4]['voice']
assert all(s['kind']!='introductions' for s in scenes)
print('QA PASS: ten meaningful shots; missing child, 04:40, seven-six-eight, no parade of characters')
