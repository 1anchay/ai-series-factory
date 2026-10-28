"""Original hand-programmed animated 2D art for the Frequency Zero series.
Every shot animates actions and objects; no photo zooms, source screenshots, or copyrighted art.
"""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw, ImageFont
from atmosphere import background as cinematic_background, finish as cinematic_finish

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
    # 2D acting: shifting weight and a ground shadow, no camera zoom.
    step=math.sin(phase*7.0) if pose=='walk' else 0.0
    sway=1.9*math.sin(phase*2.2)
    body_x=x+sway*0.7
    d.ellipse((x-27*s,y+79*s,x+29*s,y+90*s),fill=(10,14,24))
    def p(dx,dy):return (int(body_x+s*dx),int(y+s*dy))
    skin=(21,25,32) if silhouette else FACE
    coat=(15,18,29) if silhouette else (48,76,103)
    hair=(7,8,15)
    # legs with small visible stepping during walking
    walk=step*9 if pose=='walk' else 0
    d.line((p(-9,50),p(-12-walk,85)),fill=coat,width=max(3,int(10*s)))
    d.line((p(9,50),p(12+walk,85)),fill=coat,width=max(3,int(10*s)))
    d.line((p(-12-walk,85),p(-23-walk,85)),fill=(16,18,27),width=max(3,int(5*s)))
    d.line((p(12+walk,85),p(23+walk,85)),fill=(16,18,27),width=max(3,int(5*s)))
    d.rounded_rectangle((*p(-20,-1),*p(20,54)),radius=max(2,int(5*s)),fill=coat)
    raise_arm=pose in ('reach','listen')
    if raise_arm:
        gesture=ease(norm(phase/1.2))
        elbow=p(27,16-16*gesture)
        hand=p(30+5*math.sin(phase*1.5),26-45*gesture)
        d.line((p(15,12),elbow),fill=coat,width=max(3,int(10*s)))
        d.line((elbow,hand),fill=coat,width=max(3,int(9*s)))
        d.ellipse((hand[0]-5*s,hand[1]-5*s,hand[0]+5*s,hand[1]+5*s),fill=skin)
        d.line((p(-17,12),p(-21+math.sin(phase*2)*2,44)),fill=coat,width=max(3,int(9*s)))
    else:
        d.line((p(-17,12),p(-22+step*3,46)),fill=coat,width=max(3,int(10*s)))
        d.line((p(18,12),p(23-step*3,46)),fill=coat,width=max(3,int(10*s)))
    bob=math.sin(phase*2.2)*1.5
    d.ellipse((*p(-17,-36+bob),*p(17,-1+bob)),fill=skin)
    d.pieslice((*p(-19,-39+bob),*p(20,-8+bob)),180,355,fill=hair)
    hair_offset=3*math.sin(phase*1.8)
    d.line((p(-14,-28+bob),p(-19+hair_offset,-8+bob)),fill=hair,width=max(2,int(3*s)))
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

def hud(d,w,h,shot,t,episode_num=1):
    # persistent viewer-orienting HUD inspired by the sample's effectiveness, not copied artwork
    d.rounded_rectangle((12,13,114,42),radius=8,fill=(26,35,52),outline=(65,83,105),width=2)
    d.rectangle((21,22,47,33),outline=CREAM,width=1)
    d.rectangle((47,25,50,30),fill=CREAM)
    d.rectangle((24,25,24+int(12*max(.14,1-episode_num/10)),30),fill=(181,70,83))
    draw_text(d,(58,20),f'ЭФИР {episode_num:02d}',10,CREAM)
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
        beam=4*math.sin(t*1.7+index)
        d.polygon([(174+beam,229),(183+beam,229),(219+beam,464),(137+beam,464)],fill=(31,43,55))
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
    elif kind=='radio':
        studio(d,w,h)
        radio(d,33,212,295,196,pulse=.45+.45*abs(sin(t*6)),knob_angle=t*.28)
        draw_text(d,(180,171),'ВНЕШНИЙ КАНАЛ',18,RED,'mm')
        for j in range(3):
            r=15+j*13+5*sin(t*3+j)
            d.arc((180-r,321-r,180+r,321+r),205,335,fill=BLUE,width=2)
    elif kind in ('phone','receiver'):
        studio(d,w,h)
        d.rectangle((52,250,308,428),fill=(37,44,54),outline=(103,99,92),width=5)
        d.rounded_rectangle((75,326,285,406),radius=14,fill=(59,62,66),outline=AMBER,width=4)
        if kind=='phone':
            shake=3*sin(t*31) if int(t*3)%2==0 else 0
            d.rounded_rectangle((94+shake,254,266+shake,321),radius=29,fill=(31,34,43),outline=(133,142,140),width=6)
            for r in (45,60,80):d.arc((180-r,281-r,180+r,281+r),194,345,fill=RED,width=3)
            draw_text(d,(180,451),'ВЫЗОВ',20,RED,'mm')
        else:
            rx=78+15*ease(p);ry=207-19*ease(p)
            d.rounded_rectangle((rx,ry,rx+188,ry+63),radius=26,fill=(32,35,42),outline=(152,151,131),width=6)
            d.arc((102,312,263,415),20,170,fill=BLUE,width=4)
            draw_text(d,(180,453),'ЛИНИЯ ОТКРЫТА',16,BLUE,'mm')
    elif kind=='ledger':
        studio(d,w,h)
        x0,y0=46,199
        d.polygon([(x0,y0),(180,y0+10),(180,463),(x0,450)],fill=(209,194,156),outline=(145,135,105))
        d.polygon([(180,y0+10),(316,y0),(316,450),(180,463)],fill=(232,214,176),outline=(148,133,111))
        d.line((180,209,180,463),fill=(117,105,86),width=5)
        for k in range(8):
            y=242+k*25
            d.line((61,y,165,y+4),fill=(155,146,125),width=1)
            d.line((196,y+4,302,y),fill=(155,146,125),width=1)
        sentence='СЛУШАТЕЛЬ 02' if int(t*2)%3==0 else 'ПРОТОКОЛ 0'
        chars=min(len(sentence),int(t*7))
        draw_text(d,(202,291),sentence[:chars],13,REDD)
        d.line((245+5*sin(t*2),319,265+4*sin(t*2),357),fill=(58,53,55),width=6)
        if chars<len(sentence) and int(t*5)%2==0:
            cursor_x=202+font(13).getlength(sentence[:chars])
            d.line((cursor_x,292,cursor_x,307),fill=REDD,width=2)
    elif kind=='door':
        studio(d,w,h)
        door(d,w,h,min(.34,ease((t-1.4)/2.0)*.32))
        for j in range(3):
            yy=331+j*30
            if t>1.15+j*.35:
                d.arc((247-18-j*5,yy-18,247+18+j*5,yy+18),-80,88,fill=RED,width=3)
    elif kind=='knocks':
        studio(d,w,h)
        d.rectangle((83,172,281,499),fill=(41,42,49),outline=(106,104,94),width=8)
        beats=sum(t > moment for moment in (.8,1.75,2.68))
        offset=3*sin(t*29) if any(abs(t-moment)<.15 for moment in (.8,1.75,2.68)) else 0
        d.rectangle((102+offset,185,263+offset,477),fill=(72,65,60),outline=(106,96,82),width=4)
        d.ellipse((236+offset,332,246+offset,345),fill=AMBER)
        for j in range(beats):
            x=108+j*65
            d.ellipse((x,544,x+38,582),outline=RED,width=4)
        draw_text(d,(180,160),'КТО СТУЧИТ?',18,CREAM,'mm')
    elif kind=='mirror':
        studio(d,w,h)
        d.rounded_rectangle((46,150,315,481),radius=7,fill=(17,39,50),outline=(138,143,147),width=10)
        for k in range(11):
            x=62+k*22
            d.line((x,166,x+32,468),fill=(43,60,70),width=1)
        shadow_x=173 + 10*sin(t*2+1.1)
        person(d,shadow_x,331,1.04,phase=t+1.1,pose='reach',silhouette=True)
        d.line((77,171,276,445),fill=(99,136,152),width=3)
        d.line((270,171,84,453),fill=(66,102,114),width=2)
    elif kind=='map':
        studio(d,w,h)
        d.rectangle((38,181,322,478),fill=(23,36,47),outline=(105,120,118),width=5)
        for i in range(5):
            x=64+i*48
            d.line((x,200,x,455),fill=(42,65,74),width=2)
        for j in range(5):
            y=219+j*48
            d.line((57,y,301,y),fill=(42,65,74),width=2)
        d.line((105,402,241,263),fill=BLUE,width=3)
        for x,y,num in [(105,402,'9'),(241,263,'10')]:
            radius=8+2*sin(t*5+num.__len__())
            d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=RED if num=='10' else AMBER)
            draw_text(d,(x+15,y-23),num,18,CREAM)
        draw_text(d,(180,502),'ДВЕ СТАНЦИИ',18,RED,'mm')
    elif kind=='archive':
        studio(d,w,h)
        d.rounded_rectangle((30,187,329,448),radius=11,fill=(46,46,52),outline=(118,109,101),width=5)
        for i,cx in enumerate((108,251)):
            cy=307
            d.ellipse((cx-50,cy-50,cx+50,cy+50),fill=(28,31,40),outline=AMBER,width=5)
            for a in range(3):
                angle=t*2.9+a*2*math.pi/3
                dx=27*sin(angle);dy=27*math.cos(angle)
                d.ellipse((cx+dx-9,cy+dy-9,cx+dx+9,cy+dy+9),fill=(113,122,122))
        d.rectangle((98,403,266,422),fill=(23,35,45))
        draw_text(d,(180,473),'АРХИВ / 1994',17,CREAM,'mm')
    elif kind=='switch':
        studio(d,w,h)
        d.rounded_rectangle((62,177,300,461),radius=12,fill=(48,56,65),outline=(117,118,113),width=6)
        d.rounded_rectangle((135,222,226,389),radius=10,fill=(26,32,42),outline=(154,144,119),width=4)
        k=ease(t/max(.1,dur))
        d.line((180,337,172+20*k,257+95*k),fill=(196,189,152),width=15)
        d.ellipse((162+20*k,250+95*k,185+20*k,276+95*k),fill=AMBER)
        for j in range(5):
            if .35<t<.90:
                x=200+int(27*sin(t*17+j))
                y=260+int(j*13)
                d.line((x,y,x+7,y-11),fill=RED,width=3)
        draw_text(d,(180,417),'РУЧНОЙ РЕЖИМ',15,CREAM,'mm')
    return im


def render(kind,t,duration,index,w=360,h=640):
    # Full composition on a consistent 2D stage; never zoom into a still image.
    im=cinematic_background(w,h)
    object_scene(im,kind,t,duration,index)
    return cinematic_finish(im,kind,t,duration,index)
