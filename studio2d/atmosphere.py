"""Layered 2D cinematography (v1.2).

Adds environmental depth without camera zoom, photo assets, or paid APIs.
Lights are created as reusable transparent sprites; no blurred image per frame.
"""
from __future__ import annotations
import math
import random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter


@lru_cache(maxsize=16)
def _background(w: int, h: int) -> Image.Image:
    # Quiet textured background: avoid featureless solid fills, not busy photorealism.
    im = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(im)
    r = random.Random(1298)
    for y in range(h):
        k = y / max(h-1,1)
        c = (int(7 + 13*k), int(12 + 18*k), int(25 + 20*k))
        d.line((0, y, w, y), fill=c)
    # Large architectural silhouettes, kept subtle for foreground readability.
    for x in (0, int(w*.08), int(w*.88), w-4):
        d.rectangle((x, int(h*.085), min(x+4,w-1), int(h*.88)),fill=(15,25,41))
    for _ in range(240):
        x,y = r.randrange(w),r.randrange(h)
        value = r.randrange(13,37)
        d.point((x,y),fill=(value,value+4,min(255,value+14)))
    return im


def background(w: int, h: int) -> Image.Image:
    return _background(w,h).copy()


@lru_cache(maxsize=48)
def _light(radius: int, rgb: tuple[int,int,int]) -> Image.Image:
    # A soft premade glow sprite which can be moved and pulsed cheaply.
    r = int(radius)
    side = 4*r
    layer = Image.new('RGBA',(side,side),(0,0,0,0))
    d=ImageDraw.Draw(layer)
    c=side//2
    d.ellipse((c-r,c-r,c+r,c+r),fill=(*rgb,83))
    return layer.filter(ImageFilter.GaussianBlur(max(2,round(r*.73))))


def _overlay_glow(base: Image.Image, xy, radius, rgb, intensity=1):
    radius = max(10,int(radius))
    sprite=_light(radius,tuple(rgb))
    if intensity<.99:
        sprite=sprite.copy()
        sprite.putalpha(sprite.getchannel('A').point(lambda k:int(k*max(0,min(1,intensity)))))
    x,y=map(int,xy)
    left=x-2*radius;top=y-2*radius
    # Crop for images near frame edges.
    im_w,im_h=base.size
    ix=max(0,left);iy=max(0,top)
    x1=min(im_w,left+sprite.width);y1=min(im_h,top+sprite.height)
    if ix>=x1 or iy>=y1:return
    part=sprite.crop((ix-left,iy-top,x1-left,y1-top))
    base.paste(part,(ix,iy),part)


def _scene_lights(kind, w,h,t):
    f=.83+.17*math.sin(t*2.4)
    amber=(245,155,80);cyan=(44,165,196);red=(235,60,79)
    if kind in {'cold_open','dial','radio','signal','hero','recorder','archive','final'}:
        return [(180,308,105,cyan,f), (275,405,37,red,.65+.25*math.sin(t*6))]
    if kind in {'station','door','knocks'}:
        return [(244,344,94,amber,.45+.20*math.sin(t*1.8)), (274,200,45,red,.45)]
    if kind in {'hall','flashes','shadow','warning'}:
        lit = .25 + .5*max(0,math.sin(t*4.3))
        return [(180,215,95,red,lit),(180,443,55,cyan,.20)]
    if kind in {'phone','receiver'}:
        return [(180,312,95,cyan,.5+.3*max(0,math.sin(t*5)))]
    if kind in {'power','switch'}:
        return [(190,296,100,amber,.48+.22*math.sin(t*2))]
    if kind in {'clock','map','mirror'}:
        return [(180,275,110,amber,.38+.1*math.sin(t*1.7))]
    if kind in {'ledger','tomorrow'}:
        return [(180,321,95,cyan,.47)]
    return [(180,303,90,cyan,.33)]


def finish(im: Image.Image, kind:str,t:float,duration:float,index:int) -> Image.Image:
    """Lighting, dust, foreground, and shallow shadow; never scales the subject."""
    w,h=im.size
    for x,y,r,c,i in _scene_lights(kind,w,h,t):
        _overlay_glow(im,(x,y),r,c,i)

    a=Image.new('RGBA',(w,h),(0,0,0,0))
    d=ImageDraw.Draw(a,'RGBA')
    # Gentle animated floor reflection below central machinery.
    if kind in {'cold_open','radio','signal','dial','hero','station','archive','recorder','power'}:
        p=.65+.35*math.sin(t*2.8+index)
        for k in range(6):
            yy=int(h*.74+k*12)
            half=int((70+k*13)*(.75+.15*math.sin(t*.8+k)))
            d.line((w//2-half,yy,w//2+half,yy),fill=(49,123,154,int((34-k*4)*p)),width=2)
    if kind in {'hall','shadow','flashes','door','knocks'}:
        # Perspectival light stripe and light leaks at the threshold.
        glow=max(0,math.sin(t*3.7))
        d.polygon([(w*.42,h*.71),(w*.55,h*.71),(w*.72,h*.89),(w*.24,h*.89)],
                  fill=(194,105,72,int(12+18*glow)))
    # Local shadow at the bottom edges, not an opaque black strip.
    for j in range(14):
        alpha=int(1.8*(14-j))
        d.line((j*3,int(h*.76),j*3,h),fill=(2,5,13,alpha),width=2)
        d.line((w-j*3,int(h*.76),w-j*3,h),fill=(2,5,13,alpha),width=2)
    # Persistent small dust particles with independent slow motion.
    rng=random.Random(8000+index)
    for _ in range(26):
        x=rng.randrange(w)
        y=(rng.randrange(h)+round(t*(5+rng.randrange(13))))%h
        r=1 if rng.random()<.85 else 2
        d.ellipse((x-r,y-r,x+r,y+r),fill=(115,165,190,rng.randrange(22,57)))
    # Add fine static film grain to avoid blank smooth gradients.
    rng=random.Random(9993+index+int(t*7))
    for _ in range(90):
        x,y=rng.randrange(w),rng.randrange(h)
        d.point((x,y),fill=(175,193,200,16))
    im=Image.alpha_composite(im.convert('RGBA'),a).convert('RGB')
    return im
