"""Cast remains stable although introduction screens are removed."""
import json
from pathlib import Path
from characters import CAST,ORDER
root=Path(__file__).resolve().parents[1]
scenes=json.loads((root/'episodes/001.json').read_text(encoding='utf-8'))['scenes']
assert len(CAST)==len(ORDER)==7
assert len({CAST[c].coat for c in CAST})==7
assert len({CAST[c].name for c in CAST})==7
assert ORDER.index('nika')==2
assert 'meeting' in [s['kind'] for s in scenes]
assert [s['kind'] for s in scenes[-2:]]==['morning','recording']
print('Cast check passed: seven distinct recurring characters; Nika missing at dawn')
