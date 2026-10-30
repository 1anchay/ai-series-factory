"""Cinematic finishing for original illustrated frames. CPU-only, no zoom or letterboxing.

Provides color separation, local light spills, subtle grain, and scene-specific highlights.
These cannot substitute for video generation, but strengthen consistent 2D visual storytelling.
"""
from __future__ import annotations
import math
import random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

@lru_cache(maxsize=4)
def _vignette(size):
    w,h=size
    mask=Image.new('L',size); px=mask.load()
    for yy in range(h):
        y=(yy/h-.47)*1.53
        for xx in range(w):
            x=(xx/w-.5)*1.10
            dist=x*x+y*y
            px[xx,yy]=round(max(0,min(120,dist*165)))
    return mask

@lru_cache(maxsize=5)
def _film_texture(size):
    w,h=size
    rng=random.Random(4972)
    img=Image.new('RGB',size,(0,0,0));d=ImageDraw.Draw(img)
    # Paper-grain illustration texture, kept subtle and spatially stable.
    for i in range(int(w*h*.014)):
        x=rng.randrange(w);y=rng.randrange(h)
        g=rng.choice([16,19,23,27,31,36])
        d.point((x,y),fill=(g,g,g))
    return img

@lru_cache(maxsize=12)
def _light_overlay(kind,size):
    w,h=size
    light=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(light,'RGBA')
    if kind in ('night','clock','reveal'):
        d.ellipse((167,92,390,376),fill=(229,128,66,28))
    if kind=='store':
        d.polygon([(70,96),(270,96),(336,490),(2,490)],fill=(206,217,172,13))
    if kind=='bedroom':
        d.polygon([(0,177),(116,194),(211,552),(0,494)],fill=(107,151,185,22))
    if kind in ('meeting','introductions','shelter','names','morning'):
        d.polygon([(282,186),(344,188),(356,520),(205,526)],fill=(103,177,215,18))
    if kind in ('cold_open','street','bus','shadow'):
        d.ellipse((180,364,390,670),fill=(88,153,182,18))
    return light.filter(ImageFilter.GaussianBlur(14))


def _lightspill(im,kind,t):
    return Image.alpha_composite(im.convert('RGBA'),_light_overlay(kind,im.size))

def finish(image,kind,t,shot=0):
    base=image.convert('RGB')
    # Color grading is applied once per frame; expensive blur is precomputed.
    base=ImageEnhance.Contrast(base).enhance(1.05)
    layer=_lightspill(base,kind,t)
    w,h=base.size
    # Shadows have a cool cast. Keep text and faces bright enough to read.
    blue=Image.new('RGBA',(w,h),(8,17,32,10))
    layer=Image.alpha_composite(layer,blue)
    # Vignette is semi-transparent and never creates borders or a small window.
    shade=Image.new('RGBA',(w,h),(3,7,13,0))
    shade.putalpha(_vignette((w,h)))
    layer=Image.alpha_composite(layer,shade)
    # Animated highlights: moving dust in interior and occasional distant reflections.
    ov=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(ov,'RGBA')
    rng=random.Random(2460+shot*29)
    if kind not in ('street','cold_open','bus','shadow'):
        for _ in range(19):
            x=rng.randrange(w);y=(rng.randrange(h)+int(t*(1+(_%3))))%h
            a=rng.randrange(16,36)
            d.ellipse((x,y,x+1,y+1),fill=(246,215,161,a))
    else:
        for _ in range(12):
            x=rng.randrange(w); y=(rng.randrange(h)+int(t*(55+_%5*20)))%h
            d.line((x,y,x+2,y+7),fill=(134,202,231,27),width=1)
    layer=Image.alpha_composite(layer,ov)
    return layer.convert('RGB')
