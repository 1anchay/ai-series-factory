"""Episode 002: a recurring, identifiable masked observer in coherent animated environments.

All scenery and subjects are drawn as a single composition rather than pasted over
already-existing duplicate objects. Exports 360x640 native frames; no photograph zooms.
"""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw
from v6_stage import (W,H,INK,NAVY,BLUE,PAPER,MUTED,AMBER,RED,ease,text,make_canvas,
                      school_bg,board,shadow,camera_body)
from characters import person, CAST, ORDER

GREY=(95,108,117);MASK=(213,216,207);COAT=(54,66,73);RIM=(150,174,177)

def unknown(d,cx,feet,scale=1.0,t=0,turn=0.0):
    """Character 08: gray long raincoat, off-white face mask and RED 08 sleeve patch.
    Same shape and identity across six shots. 'turn' changes mask orientation,
    not body scale. Clearly human sized and separated from survivors.
    """
    s=float(scale); sway=1.1*math.sin(t*1.6)
    def xy(x,y): return (int(cx+(x+sway)*s),int(feet+y*s))
    def poly(points,c): d.polygon([xy(*a) for a in points],fill=c)
    d.ellipse((*xy(-29,-1),*xy(29,6)),fill=(8,13,22))
    # boots and long coat with colored hems; head above shoulders
    for k in (-1,1):
        d.line((xy(k*14,-63),xy(k*16,0)),fill=(22,30,37),width=max(3,int(11*s)))
        d.line((xy(k*16-8,0),xy(k*16+9,0)),fill=(10,15,22),width=max(3,int(8*s)))
    poly([(-27,-135),(27,-135),(36,-48),(24,-33),(-24,-33),(-37,-48)],COAT)
    poly([(-24,-129),(-15,-117),(-11,-40),(-25,-39)],(75,91,96))
    poly([(24,-129),(16,-117),(12,-43),(27,-41)],(38,52,60))
    d.line((xy(0,-124),xy(0,-41)),fill=(26,40,47),width=max(2,int(3*s)))
    # arms: one sleeve has a clearly legible emblem
    for side in [-1,1]:
        x=side*31
        d.line((xy(side*24,-120),xy(side*37,-81),xy(x,-50)),fill=COAT,width=max(7,int(15*s)))
        d.ellipse((*xy(x-5,-53),*xy(x+5,-42)),fill=(33,40,47))
    bx,by=xy(33,-84)
    r=max(10,int(13*s))
    d.rounded_rectangle((bx-r,by-r,bx+r,by+r),radius=3,fill=(166,51,60),outline=(244,145,137),width=2)
    text(d,(bx,by-1),'08',max(10,int(11*s)),PAPER,'mm')
    # distinct metal collar and mask, slight head turn with pale edge
    poly([(-22,-138),(22,-138),(14,-148),(-14,-148)],(24,41,48))
    mx,my=xy(turn*5,-161)
    ax,ay=xy(-19+turn*5,-190);ex,ey=xy(19+turn*5,-141)
    d.ellipse((ax,ay,ex,ey),fill=MASK,outline=RIM,width=max(1,int(2*s)))
    # black eye visor; no red-glowing monster-eyes
    d.rounded_rectangle((*xy(-13+turn*5,-170),*xy(13+turn*5,-158)),radius=3,fill=(25,39,49))
    d.line((xy(6+turn*5,-153),xy(9+turn*5,-141)),fill=(159,62,68),width=max(1,int(2*s)))
    # left temple crack makes the mask recognizable even without 08
    d.line([xy(-12+turn*5,-171),xy(-9+turn*5,-155),xy(-14+turn*5,-149)],fill=(98,108,110),width=max(1,int(2*s)))

def framing(d,episode=2,count=6):
    d.rounded_rectangle((10,10,350,65),radius=9,fill=(7,14,24),outline=(54,77,88),width=2)
    text(d,(20,20),'ЗАВТРА НАС МЕНЬШЕ',14,PAPER)
    text(d,(20,46),'ДЕНЬ 02 · СЕРИЯ 02',10,MUTED)
    text(d,(342,46),f'ОСТАЛОСЬ {count:02d}',11,RED,'ra')

def movie_screen(d,box=(23,151,337,488),rec=True):
    x0,y0,x1,y1=box
    d.rounded_rectangle((x0,y0,x1,y1),radius=13,fill=(15,23,32),outline=(115,143,151),width=6)
    d.rounded_rectangle((x0+13,y0+14,x1-13,y1-42),radius=5,fill=(27,48,59),outline=(82,120,133),width=2)
    if rec:
        text(d,(x0+22,y0+23),'● REC',13,RED)
        text(d,(x1-16,y0+23),'04:39',11,PAPER,'ra')

def classroom(d,night=False):
    school_bg(d,night=night)
    # stool + board + supply crate; the same layout in each school shot
    d.rectangle((25,468,77,510),fill=(83,74,68),outline=(136,120,96),width=3)
    d.polygon([(25,488),(77,488),(87,510),(18,510)],fill=(66,62,60))
    d.rectangle((87,466,127,507),fill=(61,67,66),outline=(110,120,112),width=2)

def wet_footprints(d,t):
    # feet-size perspective, ending abruptly at the board
    for i in range(min(7,3+int(t*1.7))):
        x=86+(i//2)*25 + (8 if i%2 else -8)
        y=545-int(i*24)
        d.ellipse((x-9,y-13,x+11,y+13),fill=(50,88,101),outline=(91,138,146),width=2)
        d.ellipse((x+5,y-16,x+11,y-10),fill=(124,158,169))

def terminal(d,headline,main,sub,highlight=RED):
    d.rounded_rectangle((36,208,326,434),radius=10,fill=(10,27,32),outline=(100,149,145),width=7)
    d.rectangle((50,224,311,412),fill=(17,42,43))
    text(d,(180,254),headline,15,(150,211,195),'mm')
    text(d,(180,320),main,32,highlight,'mm')
    text(d,(180,379),sub,13,PAPER,'mm')
    d.rectangle((154,437,209,446),fill=(103,103,90))
    d.rectangle((122,448,244,464),fill=(76,78,77))

def render(kind,t,duration,index,episode=2,scene=None):
    im=make_canvas(top=(10,24,37),bottom=(25,40,49))
    d=ImageDraw.Draw(im)
    p=ease(t/max(.1,duration))
    if kind=='eight_record':
        classroom(d,True);movie_screen(d)
        # Seven distinct bodies during previous night, all identifiable by their coats.
        for i,who in enumerate(ORDER):
            xx=65+(i%4)*54;yy=405 if i<4 else 450
            person(d,xx,yy,who,.43,t,'idle')
        # Eighth behind and apart from seven; recognizable white mask and patch.
        unknown(d,279,390,1.0,t)
        d.arc((238,174,330,409),38,325,fill=RED,width=3)
        text(d,(180,465),'7 ВЫЖИВШИХ  +  1 НЕИЗВЕСТНЫЙ',12,AMBER,'mm')
    elif kind=='eight_reveal':
        classroom(d,True)
        shadow(d,(85,543,277,564))
        unknown(d,182,543,1.7,t)
        d.rounded_rectangle((26,121,330,162),radius=8,fill=(28,43,54),outline=(87,107,118),width=2)
        text(d,(177,141),'НЕИЗВЕСТНЫЙ · № 08',19,PAPER,'mm')
        d.line((208,415,280,372),fill=RED,width=3)
        text(d,(281,359),'НАШИВКА 08',13,RED,'ma')
    elif kind=='locked_school':
        classroom(d)
        d.rectangle((101,202,265,492),fill=(74,61,54),outline=(140,115,87),width=7)
        d.ellipse((233,355,246,368),fill=AMBER)
        d.rectangle((240,372,285,384),fill=(146,155,149),outline=(201,194,171),width=2)
        person(d,80,525,'mark',1.35,t,'reach')
        text(d,(173,147),'ЗАМОК ЦЕЛ',18,AMBER,'mm')
        if t>duration*.45:d.line((246,385,287,386),fill=(188,204,196),width=2)
    elif kind=='wet_steps':
        classroom(d)
        board(d,7,True,(166,161,342,446))
        wet_footprints(d,t)
        text(d,(131,137),'МОКРЫЕ СЛЕДЫ',18,PAPER,'mm')
        text(d,(132,170),'ОБРЫВАЮТСЯ У ДОСКИ',10,AMBER,'mm')
    elif kind=='nika_last':
        classroom(d,True);movie_screen(d)
        person(d,175,425,'nika',1.55,t,'idle')
        # Camera footage features a visible, medium-size girl, not tiny silhouettes.
        unknown(d,273,382,.57,t)
        text(d,(180,463),'ПОСЛЕДНЕЕ ВИДЕО НИКИ',14,AMBER,'mm')
    elif kind=='gleb_reacts':
        classroom(d)
        person(d,173,534,'gleb',1.66,t,'idle')
        d.polygon([(235,240),(299,223),(300,294),(244,296)],fill=(38,51,64),outline=(113,131,139))
        text(d,(268,249),'08',24,RED,'mm')
        text(d,(180,151),'ГЛЕБ УЗНАЛ СИМВОЛ?',20,PAPER,'mm')
        text(d,(180,183),'ОН ГОВОРИТ, ЧТО НЕТ',12,AMBER,'mm')
    elif kind=='marked_door':
        classroom(d,True)
        d.rectangle((94,167,281,529),fill=(65,70,70),outline=(152,148,132),width=8)
        d.rectangle((108,184,266,516),fill=(39,47,51),outline=(110,111,107),width=3)
        d.rounded_rectangle((151,263,217,341),radius=6,fill=(128,49,55),outline=(227,118,111),width=3)
        text(d,(184,301),'08',48,PAPER,'mm')
        d.ellipse((249,376,261,390),fill=AMBER)
        text(d,(182,136),'ПОД ШКОЛЬНОЙ ЛЕСТНИЦЕЙ',13,AMBER,'mm')
    elif kind=='secret_monitor':
        classroom(d,True)
        # The supply room has ONE screen, open door shown as a lit strip left.
        d.polygon([(17,145),(46,175),(46,536),(17,570)],fill=(126,111,88))
        d.rectangle((69,196,314,476),fill=(19,30,37),outline=(65,78,81),width=5)
        terminal(d,'ЭКРАН ВКЛЮЧАЕТСЯ','▮', 'ПРОВОДОВ НЕТ',highlight=(133,224,189))
        if int(t*4)%3==0:d.line((60,290,303,290),fill=(99,173,154),width=2)
    elif kind=='sector_screen':
        classroom(d,True)
        terminal(d,'ПРОТОКОЛ «ПОРОГ»','СЕКТОР Б','ОСТАЛОСЬ 06  ·  04:40',highlight=(144,228,191))
        text(d,(180,500),'СЛЕДУЮЩИЙ ПЕРЕНОС',17,RED,'mm')
    elif kind=='timur_target':
        classroom(d)
        d.rounded_rectangle((19,171,205,357),radius=9,fill=(16,40,44),outline=(91,136,133),width=5)
        text(d,(112,200),'СЛЕДУЮЩИЙ',16,(158,220,197),'mm')
        text(d,(112,278),'ТИМУР',29,RED,'mm')
        person(d,271,530,'timur',1.52,t,'idle')
        text(d,(264,544),'ОН НЕ ЗНАЕТ',13,AMBER,'mm')
    elif kind=='camera_live':
        classroom(d,True);movie_screen(d)
        person(d,168,440,'timur',1.32,t,'idle')
        unknown(d,279,415,1.04,t)
        text(d,(180,466),'ВИДНО ТОЛЬКО ЧЕРЕЗ КАМЕРУ',12,AMBER,'mm')
    elif kind=='turn_around':
        classroom(d,True)
        # Two views, not a second pasted full picture. Left is reality, right the recording.
        d.rounded_rectangle((10,147,349,513),radius=8,fill=(13,25,32),outline=(103,122,126),width=3)
        d.rectangle((17,157,175,477),fill=(32,49,60))
        d.rectangle((184,157,341,477),fill=(18,37,45))
        d.line((180,151,180,503),fill=(162,179,182),width=5)
        text(d,(95,179),'ВЖИВУЮ',13,PAPER,'mm')
        text(d,(263,179),'В КАМЕРЕ',13,AMBER,'mm')
        person(d,99,420,'timur',1.03,t,'idle')
        person(d,222,422,'timur',.88,t,'idle')
        unknown(d,304,426,.72,t,turn=-.1+p*.95)
        text(d,(180,496),'МАСКА ПОВЕРНУЛАСЬ',12,RED,'mm')
    else:
        classroom(d)
        text(d,(180,220),'НЕИЗВЕСТНАЯ СЦЕНА',18,RED,'mm')
    # Controlled on-set motion: intermittent fluorescent buzz, fine moving dust.
    if kind not in ('eight_reveal','gleb_reacts'):
        for k in range(8):
            x=(21+k*41+int(t*(k%3+2)))%W
            y=(143+k*43+int(t*(k%4+2)))%H
            d.ellipse((x,y,x+1,y+1),fill=(60,84,91))
    if kind in ('secret_monitor','sector_screen','camera_live','turn_around') and int(t*8)%23==0:
        d.line((19,391,341,391),fill=(81,129,125),width=2)
    framing(d)
    return im.convert('RGB')
