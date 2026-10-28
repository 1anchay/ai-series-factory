"""Original hand-programmed animated 2D art for the Frequency Zero series.
Every shot animates actions and objects; no photo zooms, source screenshots, or copyrighted art.
"""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw, ImageFont

NAVY=(9,14,28); DEEP=(6,10,20); WALL=(22,30,46); WALL2=(29,40,55)
RED=(235,73,84); REDD=(110,39,53); AMBER=(255,185,93); BLUE=(75,176,207)
CREAM=(239,235,223); MUTED=(143,155,177); FACE=(174,141,114)

FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def font(sz,bold=True):
    import os
    path=(FONT if bold else FONT_REG)
    if not os.path.exists(path): return ImageFont.load_default()
    return ImageFont.truetype(path,max(8,int(sz)))

def norm(v,a=0,b=1): return max(a,min(b,v))
def ease(x): x=norm(x);return x*x*(3-2*x)
def mix(a,b,k): return a+(b-a)*k

def draw_text(d,xy,s,size=16,fill=CREAM,anchor=None,bold=True,stroke=0):
    d.text(tuple(map(int,xy)),s,font=font(size,bold),fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=DEEP)

def glow(d,xy,r,color=RED,pulse=1):
    # Translucency-free safe light rings: avoid painting opaque circles over art.
    x,y=xy
    for rad,strength in [(r*2.1,.12),(r*1.5,.21),(r*.85,.42)]:
        k=strength*max(.15,pulse)
        tint=tuple(int(c*k + z*(1-k)) for c,z in zip(color,(55,72,91)))
        d.ellipse((x-rad,y-rad,x+rad,y+rad),outline=tint,width=3)

def background(w,h):
    im=Image.new('RGB',(w,h));p=im.load()
    for y in range(h):
        k=y/max(1,h)
        c=(int(8+18*k),int(13+19*k),int(27+21*k))
        ImageDraw.Draw(im).line((0,y,w,y),fill=c)
    return im

def studio(d,w,h):
    d.rectangle((16,125,w-16,h-70),fill=(22,30,46),outline=(51,61,78),width=3)
    for i in range(6):
        x=26+i*56
        d.line((x,126,x+20,h-75),fill=(27,38,52),width=2)
    d.polygon([(0,465),(w,465),(w,h),(0,h)],fill=(18,22,35))
    d.line((0,465,w,465),fill=(65,76,91),width=5)
    d.rectangle((26,388,333,476),fill=(23,37,49),outline=(57,74,86),width=4)
    for i in range(6):
        x=51+i*42
        d.rectangle((x,402,x+22,434),fill=(10,23,34),outline=(47,70,85))
        d.line((x+5,444,x+17,444),fill=(63,82,94),width=2)

def door(d,w,h,opened=0.0):
    d.rectangle((100,190,261,493),fill=(53,60,68),outline=(87,92,103),width=7)
    off=int(99*ease(opened))
    d.polygon([(111+off,201),(252,200),(251,480),(111+off,481)],fill=(71,67,64))
    d.line((250,202,250,483),fill=AMBER,width=max(2,int(opened*20)))
    d.ellipse((234,350,243,359),fill=AMBER)
    d.rectangle((125,216,229,247),fill=(34,39,46))
    draw_text(d,(176,231),'СЛУЖЕБНЫЙ',9,MUTED,'mm')

def person(d,x,y,scale=1.,phase=0,pose='stand',silhouette=False):
    s=scale
    def p(dx,dy):return (int(x+s*dx),int(y+s*dy))
    skin=(21,25,32) if silhouette else FACE
    coat=(15,18,29) if silhouette else (48,76,103)
    hair=(7,8,15)
    # legs with small visible stepping during walking
    walk=math.sin(phase*7)*8 if pose=='walk' else 0
    d.line((p(-9,50),p(-12-walk,85)),fill=coat,width=max(3,int(10*s)))
    d.line((p(9,50),p(12+walk,85)),fill=coat,width=max(3,int(10*s)))
    d.rounded_rectangle((*p(-20,-1),*p(20,54)),radius=max(2,int(5*s)),fill=coat)
    raise_arm=pose in ('reach','listen')
    if raise_arm:
        d.line((p(14,11),p(34,-17+math.sin(phase*3)*2)),fill=coat,width=max(3,int(10*s)))
        d.ellipse((*p(29,-23),*p(39,-13)),fill=skin)
    else:
        d.line((p(-17,12),p(-22+math.sin(phase*2)*2,46)),fill=coat,width=max(3,int(10*s)))
        d.line((p(18,12),p(23-math.sin(phase*2)*2,46)),fill=coat,width=max(3,int(10*s)))
    bob=math.sin(phase*2.2)*1.5
    d.ellipse((*p(-17,-36+bob),*p(17,-1+bob)),fill=skin)
    d.pieslice((*p(-19,-39+bob),*p(20,-8+bob)),180,355,fill=hair)
    if not silhouette:
        blink=abs(math.sin(phase*.75))>.986
        for ex in [-7,8]:
            if blink:d.line((p(ex-2,-19),p(ex+2,-19)),fill=DEEP,width=1)
            else:d.ellipse((*p(ex-1,-20),*p(ex+2,-17)),fill=DEEP)
        d.line((p(-3,-10),p(6,-10)),fill=(85,47,47),width=2)
        # original iconic amber band, consistent every episode
        d.polygon([p(-19,3),p(18,4),p(9,18),p(-17,13)],fill=(192,118,52))

def radio(d,x,y,w=242,h=165,pulse=0.5,knob_angle=0.):
    d.rounded_rectangle((x,y,x+w,y+h),radius=15,fill=(45,53,62),outline=(117,100,89),width=4)
    d.rectangle((x+16,y+21,x+w-16,y+91),fill=(6,24,35),outline=(68,114,125),width=3)
    # Oscilloscope wave genuinely changes over time
    points=[]
    for px in range(x+25,x+w-24,3):
        k=(px-x-25)/max(1,w-50)
        amp=(0.1 + .9*pulse)*math.sin(k*math.pi)**2
        yy=y+56 - 20*amp*math.sin((px-x)*.17+knob_angle*2)
        points.append((px,yy))
    if len(points)>1:d.line(points,fill=BLUE,width=2)
    for i in range(3):
        d.line((x+28,y+109+i*13,x+152,y+109+i*13),fill=(100,99,92),width=3)
    cx,cy=x+w-45,y+h-39
    d.ellipse((cx-23,cy-23,cx+23,cy+23),fill=(29,34,44),outline=(161,157,132),width=4)
    a=knob_angle
    d.line((cx,cy,cx+17*math.sin(a),cy-17*math.cos(a)),fill=AMBER,width=4)
    d.ellipse((x+35,y+h-34,x+48,y+h-21),fill=RED if pulse>.5 else REDD)

def osc(d,x0,y0,width,height,t,power=1):
    d.rectangle((x0,y0,x0+width,y0+height),fill=(8,27,34),outline=(65,96,112),width=4)
    for v in range(1,5):
        x=x0+int(width*v/5)
        d.line((x,y0,x,y0+height),fill=(22,53,61))
    mid=y0+height//2
    arr=[]
    for i in range(8,width-8,3):
        envelope=(.2+.8*math.sin(i*.05+t*2.2)**2)*power
        dy=math.sin(i*.25 + t*6)*envelope*height*.32
        arr.append((x0+i,mid+dy))
    if len(arr)>1:d.line(arr,fill=(94,235,214),width=3)

def hud(d,w,h,shot,t):
    # persistent viewer-orienting HUD inspired by the sample's effectiveness, not copied artwork
    d.rounded_rectangle((12,13,114,42),radius=8,fill=(26,35,52),outline=(65,83,105),width=2)
    d.rectangle((21,22,47,33),outline=CREAM,width=1)
    d.rectangle((47,25,50,30),fill=CREAM)
    d.rectangle((24,25,34,30),fill=(181,70,83))
    draw_text(d,(58,20),'СИГНАЛ 01',10,CREAM)
    d.rounded_rectangle((212,13,348,42),radius=8,fill=(26,35,52),outline=(65,83,105),width=2)
    mm=int((t+shot*3)/60)
    sec=int(t+shot*3)%60
    draw_text(d,(280,27),f'02:{14+mm:02d}:{sec:02d}',13,RED,'mm')
    d.line((0,53,w,53),fill=(53,70,90),width=2)

def object_scene(im, kind, t, dur, index, rng_seed=12):
    w,h=im.size
    d=ImageDraw.Draw(im)
    p=t/max(.1,dur)
    sin=math.sin
    # independently animated actual objects; no background scaling or photographic zoom
    if kind=='cold_open':
        studio(d,w,h)
        radio(d,55,232,252,163,pulse=.5+.5*sin(t*12),knob_angle=t*.25)
        glow(d,(180,310),62,RED,.6+.2*sin(t*2))
        draw_text(d,(180,155),'ЧАСТОТА',34,CREAM,'mm')
        draw_text(d,(180,199),'НОЛЬ',52,RED,'mm')
        d.line((51,469,309,469),fill=RED,width=5)
    elif kind=='station':
        # no giant portrait: Lika is a small, moving figure in an environment
        studio(d,w,h)
        door(d,w,h,.0)
        person(d,180+20*ease(p),400,1.05,phase=t,pose='walk')
        draw_text(d,(180,90),'СТАНЦИЯ № 9',19,CREAM,'mm')
        d.ellipse((287,173,302,188),fill=RED if sin(t*5)>0 else REDD)
    elif kind=='power':
        studio(d,w,h)
        d.rectangle((58,177,304,400),fill=(32,42,51),outline=(100,116,123),width=5)
        draw_text(d,(180,207),'ГЛАВНЫЙ ЩИТ',19,CREAM,'mm')
        for j in range(4):
            y=250+31*j
            d.line((91,y,269,y),fill=(75,94,99),width=4)
            d.ellipse((90,y-6,102,y+6),fill=(69,76,84))
        x=169
        knob_x=x + 6*math.sin(ease(p)*math.pi)
        d.rounded_rectangle((knob_x-12,258,knob_x+12,315),radius=5,fill=(180,164,131))
        draw_text(d,(180,350),'ПИТАНИЕ: 0%',22,RED,'mm')
    elif kind=='dial':
        studio(d,w,h)
        radio(d,30,205,300,210,.55+.45*sin(t*9),knob_angle=math.pi*1.2*ease(p))
        draw_text(d,(180,447),'0.0 МГц',32,AMBER,'mm')
    elif kind=='signal':
        studio(d,w,h)
        osc(d,30,196,300,171,t,.55+.45*abs(sin(t*7)))
        draw_text(d,(180,162),'НЕИЗВЕСТНЫЙ ГОЛОС',15,RED,'mm')
        d.rectangle((140,402,220,436),fill=(39,53,65),outline=BLUE,width=3)
        d.ellipse((154,413,165,424),fill=RED if sin(t*7)>-.2 else REDD)
    elif kind=='hero':
        studio(d,w,h)
        radio(d,65,289,227,140,.45+.3*sin(t*8),knob_angle=t*.08)
        person(d,105,275,1.16,phase=t,pose='reach')
        d.arc((182,181,278,267),210,335,fill=BLUE,width=4)
        for j in range(3):
            rad=40+j*11
            d.arc((206-rad,220-rad,206+rad,220+rad),235,305,fill=(55+20*j,140+10*j,170+8*j),width=3)
    elif kind=='clock':
        studio(d,w,h)
        cx,cy=180,270
        d.ellipse((cx-114,cy-114,cx+114,cy+114),fill=(43,49,58),outline=AMBER,width=7)
        for j in range(12):
            ang=j*2*math.pi/12
            d.line((cx+92*sin(ang),cy-92*math.cos(ang),cx+104*sin(ang),cy-104*math.cos(ang)),fill=CREAM,width=3)
        a=-t*2.7
        d.line((cx,cy,cx+67*sin(a),cy-67*math.cos(a)),fill=RED,width=5)
        d.line((cx,cy,cx+48*sin(a/7+1.1),cy-48*math.cos(a/7+1.1)),fill=CREAM,width=7)
        d.ellipse((cx-7,cy-7,cx+7,cy+7),fill=AMBER)
        draw_text(d,(180,438),'ВРЕМЯ ОТСТУПАЕТ',17,RED,'mm')
    elif kind in ('hall','flashes','shadow'):
        # perspective hallway, the silhouette has an independent trajectory
        d.polygon([(0,100),(360,100),(255,474),(105,474)],fill=(21,28,42))
        d.polygon([(0,600),(360,600),(255,474),(105,474)],fill=(15,19,30))
        d.polygon([(0,100),(105,474),(105,620),(0,620)],fill=(22,33,49))
        d.polygon([(360,100),(255,474),(255,620),(360,620)],fill=(26,35,49))
        for k in range(5):
            y=150+48*k
            d.line((10,y,105,y+int((474-y)*.38)),fill=(50,69,83),width=2)
            d.line((350,y,255,y+int((474-y)*.38)),fill=(50,69,83),width=2)
        d.rectangle((119,294,241,464),fill=(16,28,41),outline=(67,76,84),width=4)
        d.line((180,294,180,464),fill=(58,67,78),width=2)
        x,y=180,210
        flashes=(kind=='flashes' and (0.15<t<.40 or 1.05<t<1.28 or 1.95<t<2.18))
        lit=(kind=='hall' and sin(t*5)>-.2) or flashes or (kind=='shadow' and sin(t*2)>.4)
        glow(d,(x,y),28,RED,1.0 if lit else .25)
        d.ellipse((x-16,y-16,x+16,y+16),fill=RED if lit else REDD)
        if kind=='flashes':
            count=sum(t>x for x in (.40,1.28,2.18))
            draw_text(d,(180,532),f'{count}/3',30,RED,'mm')
        elif kind=='shadow':
            x=100+190*ease(p)
            person(d,x,371,.70,phase=t,pose='walk',silhouette=True)
            # obscuring glass overlay
            d.rectangle((111,305,246,462),outline=(83,94,105),width=5)
    elif kind=='warning':
        studio(d,w,h)
        d.rounded_rectangle((32,185,328,420),radius=18,fill=(24,43,55),outline=(119,66,71),width=6)
        draw_text(d,(180,230),'ПРОТОКОЛ 3',24,RED,'mm')
        for j in range(3):
            x=102+76*j
            active=t>.6+j*.65
            d.ellipse((x-18,289,x+18,325),fill=RED if active else REDD)
            draw_text(d,(x,349),str(j+1),19,CREAM,'mm')
        draw_text(d,(180,390),'НЕ ДВИГАЙСЯ',19,CREAM,'mm')
    elif kind=='recorder':
        studio(d,w,h)
        d.rounded_rectangle((34,211,327,422),radius=14,fill=(48,52,58),outline=(134,122,107),width=4)
        for cx in (115,248):
            cy=285
            d.ellipse((cx-49,cy-49,cx+49,cy+49),fill=(33,39,47),outline=AMBER,width=4)
            for j in range(3):
                a=j*2*math.pi/3+t*3.5
                dx=26*sin(a);dy=26*math.cos(a)
                d.ellipse((cx+dx-8,cy+dy-8,cx+dx+8,cy+dy+8),fill=(86,97,108))
        d.rectangle((80,367,282,397),fill=(23,38,48))
        d.ellipse((93,373,113,393),fill=RED if sin(t*6)>.0 else REDD)
        draw_text(d,(191,384),'REC ●',15,CREAM,'mm')
    elif kind=='tomorrow':
        studio(d,w,h)
        d.rectangle((34,194,326,435),fill=(7,32,39),outline=(76,141,134),width=5)
        draw_text(d,(180,235),'ЗАПИСЬ № 001',18,BLUE,'mm')
        d.line((54,260,304,260),fill=(52,103,109),width=2)
        draw_text(d,(180,307),'ЗАВТРА',41,RED,'mm')
        draw_text(d,(180,356),'02:14',34,CREAM,'mm')
        for i in range(10):
            x=63+i*26
            ht=(12+12*sin(i*2.3+t*6))
            d.line((x,402-ht,x,402+ht),fill=BLUE,width=3)
    elif kind=='final':
        studio(d,w,h)
        d.rectangle((20,170,340,458),fill=(9,29,36),outline=(61,91,106),width=6)
        osc(d,40,204,280,145,t,.5+.5*sin(t*12)**2)
        person(d,176+12*sin(t),465,.75,phase=t,pose='listen',silhouette=True)
        d.ellipse((278,389,297,408),fill=RED if sin(t*9)>0 else REDD)
        if t>dur-1.9:
            draw_text(d,(180,161),'ПРОДОЛЖЕНИЕ',18,RED,'mm')
            draw_text(d,(180,184),'СЛЕДУЕТ...',16,CREAM,'mm')
    return im


def render(kind,t,duration,index,w=360,h=640):
    im=background(w,h)
    object_scene(im,kind,t,duration,index)
    # Low-cost animated dust, tiny texture lines, no scale-based camera motion
    d=ImageDraw.Draw(im,'RGBA')
    rand=random.Random(220+index)
    for _ in range(24):
        x=rand.randrange(w)
        y=(rand.randrange(h)+int(t*(11+rand.randrange(16))))%h
        alpha=35+rand.randrange(40)
        d.ellipse((x,y,x+1,y+1),fill=(125,175,190,alpha))
    return im
