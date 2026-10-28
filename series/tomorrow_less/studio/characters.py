"""Reusable recognisable 2-D cast, with named faces and readable costume silhouettes.
Original vector art created for 'Завтра нас меньше'. All coordinates are logical
at 360x640; every scene uses the same identity specs to prevent character drift.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from PIL import Image, ImageDraw, ImageFont

INK=(12,19,30)
TEXT=(239,236,224)
PALE=(149,162,176)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

@dataclass(frozen=True)
class Identity:
    key: str
    name: str
    role: str
    age: int
    coat: tuple
    accent: tuple
    skin: tuple
    hair: tuple
    style: str
    shape: str='normal'

CAST={
    'asya': Identity('asya','АСЯ','ДИСПЕТЧЕР',28,(216,144,66),(247,207,116),(213,163,128),(77,53,47),'bob'),
    'mark': Identity('mark','МАРК','ПОЖАРНЫЙ',39,(168,59,65),(250,144,125),(189,139,111),(55,47,43),'buzz','broad'),
    'nika': Identity('nika','НИКА','ВИДЕОБЛОГЕР',23,(138,99,188),(211,166,245),(219,172,140),(81,57,116),'side'),
    'timur':Identity('timur','ТИМУР','ЭЛЕКТРИК',31,(74,135,179),(126,211,238),(181,132,101),(39,49,51),'beanie'),
    'dina': Identity('dina','ДИНА','ВРАЧ',35,(70,153,138),(173,242,224),(183,135,117),(48,46,46),'bun'),
    'lev':  Identity('lev','ЛЕВ','ВОДИТЕЛЬ',64,(150,121,87),(226,202,161),(212,173,144),(196,191,178),'grey','narrow'),
    'gleb': Identity('gleb','ГЛЕБ','ИНЖЕНЕР',42,(79,123,91),(175,214,155),(199,153,126),(62,53,44),'part','narrow'),
}
ORDER=['asya','mark','nika','timur','dina','lev','gleb']


def _p(cx,cy,s,x,y):return (round(cx+x*s),round(cy+y*s))

def _poly(d, cx,cy,s,pts,fill):d.polygon([_p(cx,cy,s,x,y) for x,y in pts],fill=fill)

def _ellipse(d,cx,cy,s,box,fill,outline=None,width=1):
    a=_p(cx,cy,s,box[0],box[1]);b=_p(cx,cy,s,box[2],box[3]);d.ellipse((*a,*b),fill=fill,outline=outline,width=width)

def _line(d,cx,cy,s,pts,fill,width=2):
    d.line([_p(cx,cy,s,x,y) for x,y in pts],fill=fill,width=max(1,round(width*s)),joint='curve')


def person(d:ImageDraw.ImageDraw,cx:float,feet:float,who='asya',scale=1.,phase=0.,pose='idle'):
    """Draw a face-bearing 2-D character. 'feet' is ground baseline.
    Character's logical dimensions approximately 52x121 before scaling.
    """
    spec=CAST[who];s=scale
    # 3/4 facing front; head remains visible and distinguishable at >=0.8x.
    cy=feet-116*s
    sway=math.sin(phase*2)*.7
    cx=cx+sway*s
    step=math.sin(phase*6)*5 if pose=='walk' else 0
    blink=(math.sin(phase*2.1+len(who))>.97)
    _ellipse(d,cx,cy,s,(-25,109,25,118),(8,13,23))
    # legs, separately animated
    for side in (-1,1):
        legx=side*11; swing=step*side
        _line(d,cx,cy,s,[(legx,76),(legx+swing,106),(legx+swing+side*3,112)],(24,32,43),8)
        _line(d,cx,cy,s,[(legx+swing-5,112),(legx+swing+side*10,112)],(11,17,23),6)
    broad=1.22 if spec.shape=='broad' else (.86 if spec.shape=='narrow' else 1)
    _poly(d,cx,cy,s,[(-22*broad,36),(-15*broad,30),(14*broad,30),(22*broad,36),(22*broad,83),(-22*broad,83)],spec.coat)
    # jacket seams and identifying badges (not just a colour swap)
    _line(d,cx,cy,s,[(0,31),(0,81)],(34,41,48),2)
    if who=='asya':
        _line(d,cx,cy,s,[(-19,41),(15,49)],spec.accent,5)
        _poly(d,cx,cy,s,[(12,38),(22,43),(8,74),(1,71)],(237,188,91))
    if who=='mark':
        _poly(d,cx,cy,s,[(-24,52),(24,52),(24,57),(-24,57)],(224,186,94))
        _line(d,cx,cy,s,[(-18,39),(18,39)],(233,168,116),3)
    if who=='nika':
        _line(d,cx,cy,s,[(-20,45),(20,60)],(228,191,241),4)
        _ellipse(d,cx,cy,s,(11,55,27,70),(22,29,39),outline=(198,155,235),width=2)
    if who=='timur':
        _poly(d,cx,cy,s,[(-20,53),(20,53),(20,62),(-20,62)],(202,181,81))
        _ellipse(d,cx,cy,s,(11,67,17,73),(219,211,178))
    if who=='dina':
        _poly(d,cx,cy,s,[(-11,37),(-5,37),(4,59),(-4,65)],(229,230,226))
        _ellipse(d,cx,cy,s,(8,57,17,66),(245,242,235))
    if who=='lev':
        _poly(d,cx,cy,s,[(-22,32),(0,43),(22,32),(18,41),(0,57),(-18,41)],(118,94,69))
        _line(d,cx,cy,s,[(0,30),(0,79)],(210,199,178),3)
    if who=='gleb':
        _ellipse(d,cx,cy,s,(10,44,17,52),(204,201,168))
        _line(d,cx,cy,s,[(-17,38),(-12,67)],(62,87,66),4)
    # arms, independent from torso
    for side in (-1,1):
        wave=(math.sin(phase*3)*4 if pose=='walk' else 0)
        if pose=='write' and side==1: end=(35,-2+math.sin(phase*5)*2)
        elif pose=='reach' and side==1: end=(35,18+math.sin(phase*3)*3)
        else:end=(side*(27*broad)+wave*side,76)
        _line(d,cx,cy,s,[(side*19*broad,39),(side*27*broad,52),end],spec.coat,9)
        _ellipse(d,cx,cy,s,(end[0]-4,end[1]-3,end[0]+4,end[1]+4),spec.skin)
    # neck and distinct face outline
    _poly(d,cx,cy,s,[(-7,27),(7,27),(6,35),(-6,35)],spec.skin)
    face_y=2+math.sin(phase*2)*.55
    _ellipse(d,cx,cy,s,(-18,-17+face_y,18,31+face_y),spec.skin,outline=(83,66,64),width=max(1,round(s)))
    _ellipse(d,cx,cy,s,(-21,8, -16,17),spec.skin)
    _ellipse(d,cx,cy,s,(16,8,21,17),spec.skin)
    # seven hair styles
    if spec.style=='bob':
        _poly(d,cx,cy,s,[(-19,15),(-23,-4),(-16,-23),(10,-24),(20,-17),(21,15),(14,7),(14,-10),(-5,-10),(-12,4),(-12,25),(-20,27)],spec.hair)
        _line(d,cx,cy,s,[(-15,-7),(-9,-19),(7,-21)],(121,83,68),3)
    elif spec.style=='buzz':
        _ellipse(d,cx,cy,s,(-18,-21,18,-8),spec.hair)
        _poly(d,cx,cy,s,[(-11,16),(11,16),(8,27),(-8,27)],(98,67,55))
    elif spec.style=='side':
        _ellipse(d,cx,cy,s,(-20,-25,18,-7),spec.hair)
        _poly(d,cx,cy,s,[(10,-17),(19,-18),(24,20),(16,24),(15,-7)],spec.hair)
        _line(d,cx,cy,s,[(-12,-15),(5,-22),(19,-18)],(157,118,191),3)
    elif spec.style=='beanie':
        _ellipse(d,cx,cy,s,(-19,-23,18,-6),(32,55,67))
        _line(d,cx,cy,s,[(-18,-9),(17,-9)],(126,194,215),6)
    elif spec.style=='bun':
        _ellipse(d,cx,cy,s,(-20,-24,18,-5),spec.hair)
        _ellipse(d,cx,cy,s,(12,-30,24,-15),spec.hair)
        _line(d,cx,cy,s,[(-18,-8),(-10,-21)],(80,73,67),2)
    elif spec.style=='grey':
        _ellipse(d,cx,cy,s,(-17,-20,18,-6),spec.hair)
        _ellipse(d,cx,cy,s,(-12,19,12,30),spec.hair)
        _line(d,cx,cy,s,[(-10,19),(-3,25),(9,19)],(160,155,145),3)
    elif spec.style=='part':
        _ellipse(d,cx,cy,s,(-19,-24,18,-6),spec.hair)
        _line(d,cx,cy,s,[(-4,-21),(-2,-11)],(142,113,86),2)
    # eyebrows, eye whites and pupils
    for side in (-1,1):
        ex=side*8
        _line(d,cx,cy,s,[(ex-4,5),(ex+4,4)],(61,53,52),2)
        if blink:_line(d,cx,cy,s,[(ex-4,10),(ex+3,10)],(55,50,48),2)
        else:
            _ellipse(d,cx,cy,s,(ex-4,8,ex+4,14),(239,231,217))
            _ellipse(d,cx,cy,s,(ex-1,9,ex+2,14),(38,47,57))
    _line(d,cx,cy,s,[(0,12),(-1,18),(2,19)],(133,93,84),1)
    if who in ('mark','lev'):
        _line(d,cx,cy,s,[(-8,23),(0,25),(8,23)],(78,57,56),2)
    else:
        _line(d,cx,cy,s,[(-5,25),(5,25)],(118,65,66),2)
    if who=='nika':
        for fx,fy in [(-12,17),(-9,19),(10,18),(13,17)]:_ellipse(d,cx,cy,s,(fx,fy,fx+2,fy+2),(177,108,98))
    if who=='gleb':
        _ellipse(d,cx,cy,s,(-17,5,-1,18),None,outline=(210,211,206),width=max(1,round(2*s)))
        _ellipse(d,cx,cy,s,(1,5,17,18),None,outline=(210,211,206),width=max(1,round(2*s)))
        _line(d,cx,cy,s,[(-1,9),(1,9)],(206,208,198),2)
    if who=='lev':
        _line(d,cx,cy,s,[(-17,20),(-20,26)],(120,98,89),1)
        _line(d,cx,cy,s,[(17,20),(20,26)],(120,98,89),1)


def portrait_card(im, key, box, phase=0., nameplate=True, active=True):
    s=CAST[key]
    d=ImageDraw.Draw(im)
    x0,y0,x1,y1=box
    width=x1-x0;height=y1-y0
    d.rounded_rectangle(box,radius=12,fill=(23,34,49) if active else (20,26,37),outline=s.accent if active else (69,76,88),width=3)
    d.rounded_rectangle((x0+5,y0+6,x1-5,y1-57),radius=9,fill=(30,46,61))
    d.ellipse((x0+width*.09,y0+height*.17,x1-width*.09,y0+height*.63),fill=(37,52,66))
    # slight animation, no image zoom: character shoulders move in place.
    center=(x0+x1)/2
    yfeet=y1-52
    scale=min(1.4,max(.85,(height-65)/135))
    person(d,center,yfeet,key,scale=scale,phase=phase)
    if nameplate:
        d.rounded_rectangle((x0+7,y1-55,x1-7,y1-7),radius=5,fill=(10,16,26))
        f=ImageFont.truetype(FONT,16 if width>=130 else 13)
        bb=d.textbbox((0,0),s.name,font=f);text_w=bb[2]-bb[0]
        d.text((center-text_w/2,y1-50),s.name,font=f,fill=s.accent)
        ff=ImageFont.truetype(FONT,9)
        bb=d.textbbox((0,0),s.role,font=ff);text_w=bb[2]-bb[0]
        if text_w<width-20:d.text((center-text_w/2,y1-27),s.role,font=ff,fill=PALE)


def label(d,key,x,y,small=False):
    c=CAST[key]
    f=ImageFont.truetype(FONT,10 if small else 14)
    bw=d.textbbox((0,0),c.name,font=f)[2]
    d.rounded_rectangle((x-bw/2-6,y-2,x+bw/2+6,y+16),radius=5,fill=(9,16,25),outline=c.accent,width=1)
    d.text((x-bw/2,y),c.name,font=f,fill=c.accent)
