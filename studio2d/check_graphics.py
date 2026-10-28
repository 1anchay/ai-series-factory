#!/usr/bin/env python3
"""Fast graphics smoke test across all scene types in season 1."""
from __future__ import annotations
import json
from pathlib import Path
from art import render

ROOT=Path(__file__).resolve().parents[1]

def main():
    episodes=sorted((ROOT/'episodes').glob('*.json'))
    if not episodes:
        raise RuntimeError('No episode scenarios found')
    kinds=sorted({scene['kind'] for path in episodes
                  for scene in json.loads(path.read_text(encoding='utf-8'))['scenes']})
    for i,kind in enumerate(kinds):
        for t in (.25,1.5,3.25):
            frame=render(kind,t,4.0,i)
            if frame.size!=(360,640) or frame.mode!='RGB':
                raise AssertionError(f'Wrong 9:16 canvas for scene {kind}')
            bands=[frame.crop((0,k*160,360,(k+1)*160)) for k in range(4)]
            for j,band in enumerate(bands):
                mn,mx=band.convert('L').getextrema()
                if mx-mn<8:
                    raise AssertionError(f'Scene {kind}, band {j}: flat/blackened image')
    print(f'GRAPHICS OK: {len(kinds)} kinds, {len(kinds)*3} frame checks, 360x640')

if __name__=='__main__':
    main()
