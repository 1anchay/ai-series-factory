"""Identity and continuity checks for episode 001."""
from __future__ import annotations
import json
from pathlib import Path
from characters import CAST, ORDER

def main():
    root=Path(__file__).resolve().parents[1]
    scenes=json.loads((root/'episodes/001.json').read_text(encoding='utf-8'))['scenes']
    assert len(scenes)==18, f'Expected 17 story shots, got {len(scenes)}'
    assert set(CAST)==set(ORDER) and len(CAST)==7
    assert len(set(c.coat for c in CAST.values()))==7
    assert len(set(c.name for c in CAST.values()))==7
    intro=[s for s in scenes if s['kind']=='introductions']
    assert len(intro)==3
    assert [key for s in intro for key in s['characters']]==ORDER
    assert [s['kind'] for s in scenes].index('introductions')>[s['kind'] for s in scenes].index('meeting')
    assert ORDER.index('nika')==2
    assert [scene['kind'] for scene in scenes[-3:]]==['morning','reveal','recording']
    for s in scenes:
        assert len(s.get('voice',''))>10
    print('OK: seven unique faces/outfits, three introductions, Nika continuity, 18 story scenes')

if __name__=='__main__':main()
