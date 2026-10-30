"""Lightweight environment regressions (no external services)."""
from __future__ import annotations
from PIL import ImageChops
from art import draw
from environment import base_scene,environment

KINDS=['cold_open','bedroom','street','bus','store','phone','shadow','meeting',
       'introductions','shelter','names','night','clock','morning','reveal','recording']

def run():
    for i,k in enumerate(KINDS):
        base=base_scene(k)
        assert base.size==(360,640),k
        first=environment(k,.25,i)
        later=environment(k,2.2,i)
        assert ImageChops.difference(first,later).getbbox(), f'{k}: atmosphere is static'
        shot=draw(k,1.6,4.6,i,scene={'characters':['asya','mark']})
        assert shot.size==(360,640),k
        assert len(shot.getcolors(maxcolors=1<<20) or [])>70, f'{k}: scene lost detail'
    print(f'OK: {len(KINDS)} distinct 2D sets, animated atmosphere and detailed scenery')

if __name__=='__main__':run()
