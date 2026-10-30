"""ZNM v6: cohesive story-first 2-D scenes. Each set owns its objects.

No pre-painted bus + overlaid bus; no duplicated checkouts or duplicated doors.
Objects use a shared palette, lighting direction and scale. Original vector art.
"""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw, ImageFont
from characters import person, label, ORDER, CAST
from props import sprite

W,H=360,640
INK=(12,19,30); NAVY=(14,25,39); BLUE=(25,45,65)
PAPER=(234,230,211); MUTED=(150,167,181); AMBER=(239,186,104); RED=(231,93,102)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def f(sz,bold=True):
    try:return ImageFont.truetype(FONT if bold else REG,round(sz))
    except OSError:return ImageFont.load_default()

def text(d,xy,s,sz=17,color=PAPER,anchor=None,bold=True):
    d.text(xy,str(s),font=f(sz,bold),fill=color,anchor=anchor)

def ease(x):
    x=max(0,min(1,x));return x*x*(3-2*x)

def paste(im,name,pos,size):
    obj=sprite(name,*size)
    if im.mode!='RGBA':im=im.convert('RGBA')
    im.alpha_composite(obj,pos)
    return im

def make_canvas(top=(9,22,39),bottom=(33,51,60)):
    im=Image.new('RGBA',(W,H),(0,0,0,255));d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H
        c=tuple(int(a*(1-t)+b*t) for a,b in zip(top,bottom))
        d.line((0,y,W,y),fill=c+(255,))
    return im

def shadow(d,box):
    d.ellipse(box,fill=(11,18,29,255))

def street_bg(d):
    d.polygon([(0,112),(110,143),(110,468),(0,508)], fill=(26,43,56))
    d.polygon([(268,137),(360,113),(360,511),(268,469)],fill=(25,43,57))
    d.polygon([(110,152),(270,152),(270,460),(110,460)],fill=(37,57,70))
    for base,step in ((8,35),(280,27)):
        for y in range(174,443,34):
            for x in range(base,base+(80 if base==8 else 70),step):
                c=(53,77,87) if (x+y)//34%5 else (150,122,81)
                d.rectangle((x,y,x+13,y+18),fill=c)
    d.polygon([(110,456),(265,456),(360,640),(0,640)],fill=(25,34,43))
    d.line((108,457,0,640),fill=(97,105,107),width=4)
    d.line((266,457,360,640),fill=(97,105,107),width=4)
    for y in (489,527,578):
        m=(y-456)*.28
        d.line((180-m,y,180+m,y),fill=(48,63,72),width=2)
    # sidewalk, transit stop, street light: all fixed in perspective
    d.line((310,320,310,476),fill=(87,110,119),width=4)
    d.rounded_rectangle((277,323,341,354),radius=5,fill=(22,53,70),outline=(143,169,169),width=2)
    text(d,(309,339),'17',17,PAPER,'mm')
    d.line((45,357,45,487),fill=(76,97,102),width=4)
    d.rounded_rectangle((30,371,59,442),radius=4,fill=(20,30,40),outline=(90,113,121),width=2)
    for y,c in ((379,(166,62,65)),(400,(91,81,60)),(422,(66,96,72))):d.ellipse((37,y,52,y+15),fill=c)

def school_bg(d,night=False):
    base=(26,36,48) if not night else (14,22,34)
    d.rectangle((0,83,W,482),fill=base)
    d.polygon([(0,478),(W,478),(W,H),(0,H)],fill=(37,40,44) if not night else (19,24,33))
    for y in (500,546,595):d.line((0,y,360,y),fill=(55,60,63) if not night else (33,43,51),width=2)
    # same recognizable window on right in every school shot
    d.rectangle((277,169,348,407),fill=(30,52,70),outline=(104,118,121),width=5)
    d.line((310,172,310,403),fill=(99,116,124),width=3)
    for y in (252,321):d.line((279,y,347,y),fill=(100,112,120),width=2)
    d.rectangle((13,174,73,435),fill=(57,67,75),outline=(115,122,125),width=3)
    for x in (19,44):
        d.line((x,182,x,429),fill=(86,97,102),width=2)
    for y in (231,314,396):
        d.line((18,y,68,y),fill=(107,113,116),width=2)
    d.rectangle((133,90,244,110),fill=(30,73,68),outline=(111,160,146),width=2)
    text(d,(188,100),'УБЕЖИЩЕ · ШКОЛА',10,(202,230,222),'mm')

def board(d,names_visible=7,highlight=False,box=(90,176,267,455)):
    x0,y0,x1,y1=box
    d.rounded_rectangle((x0,y0,x1,y1),radius=8,fill=(46,58,59),outline=(145,122,88),width=5)
    text(d,(x0+16,y0+12),'МЫ ЗДЕСЬ',17,PAPER)
    names=['АСЯ','МАРК','НИКА','ТИМУР','ДИНА','ЛЕВ','ГЛЕБ']
    for j,name in enumerate(names[:names_visible]):
        c=RED if highlight and name=='НИКА' else PAPER
        text(d,(x0+17,y0+48+j*28),f'{j+1}. {name}',14,c)
        d.line((x0+16,y0+72+j*28,x1-15,y0+72+j*28),fill=(85,99,102),width=1)

def drawing(d):
    # Identifiable child drawing, not another photo pasted over a picture frame.
    d.polygon([(85,236),(180,228),(181,350),(89,353)],fill=(230,222,188),outline=(170,145,102))
    d.ellipse((121,247,147,271),fill=(255,203,103))
    for i in range(10):
        a=i*math.pi/5
        d.line((134+math.cos(a)*17,259+math.sin(a)*17,134+math.cos(a)*22,259+math.sin(a)*22),fill=(225,150,77),width=2)
    for cx,h in ((110,294),(153,291)):
        d.ellipse((cx-8,h,cx+8,h+16),fill=(181,131,104))
        d.line((cx,h+16,cx,h+43),fill=(83,113,157),width=4)
        d.line((cx,h+23,cx-12,h+38),fill=(83,113,157),width=3)
        d.line((cx,h+23,cx+12,h+38),fill=(83,113,157),width=3)
    text(d,(129,346),'МАМА + СОНЯ',9,(94,77,68),'mm')

def room(d):
    d.rectangle((0,84,W,480),fill=(46,48,55))
    d.polygon([(0,467),(W,467),(W,H),(0,H)],fill=(46,43,43))
    d.rectangle((23,155,130,335),fill=(34,54,68),outline=(122,117,111),width=6)
    d.line((78,158,78,332),fill=(122,117,111),width=3)
    d.rectangle((185,340,350,437),fill=(73,65,65),outline=(145,119,110),width=3)
    d.polygon([(180,391),(355,391),(355,487),(178,487)],fill=(81,83,91))
    d.polygon([(188,396),(345,396),(344,433),(185,433)],fill=(173,161,147))
    d.rectangle((187,428,346,475),fill=(117,97,104))
    d.rounded_rectangle((19,395,89,462),radius=4,fill=(83,70,66),outline=(129,109,93),width=2)
    d.rectangle((27,408,79,425),fill=(118,93,79))
    d.rectangle((270,195,348,279),fill=(95,82,72),outline=(160,135,103),width=5)
    text(d,(309,229),'СОНЯ',15,PAPER,'mm')

def store_bg(d):
    d.rectangle((0,105,W,478),fill=(39,50,60))
    d.polygon([(0,470),(W,470),(W,H),(0,H)],fill=(42,47,49))
    for y in (493,527,568,610):d.line((0,y,W,y),fill=(62,66,66),width=2)
    d.rectangle((14,152,145,458),fill=(56,65,68),outline=(115,121,120),width=3)
    for yy in (214,293,372,448):
        d.line((21,yy,140,yy),fill=(152,134,106),width=5)
        if yy<448:
            for j in range(5):
                x=25+j*23
                color=[(156,92,76),(95,143,139),(176,144,91),(89,115,150),(158,116,118)][(j+yy//100)%5]
                d.rounded_rectangle((x,yy-30,x+17,yy-5),radius=3,fill=color,outline=(41,57,61))
    d.polygon([(156,158),(347,158),(347,454),(185,454)],fill=(32,48,59),outline=(84,105,109))
    for y in (233,300,377):
        d.line((183,y,344,y),fill=(68,85,91),width=4)
    d.rectangle((157,446,341,512),fill=(48,48,48),outline=(103,100,93),width=3)
    d.rectangle((161,461,262,492),fill=(81,83,83))
    text(d,(180,115),'МИНИМАРКЕТ 24/7',18,PAPER,'mm')

def camera_body(d,x,y,scale=1):
    # No pasted camera over another; distinct real-world camera silhouette.
    w=64*scale;h=35*scale
    d.rounded_rectangle((x,y,x+w,y+h),radius=6,fill=(20,29,36),outline=(125,144,148),width=3)
    d.polygon([(x+w*.67,y+5*scale),(x+w+20*scale,y-3*scale),(x+w+23*scale,y+h*.88),(x+w*.67,y+h*.80)],fill=(26,36,43),outline=(114,131,140))
    d.ellipse((x-8*scale,y+8*scale,x+15*scale,y+30*scale),fill=(42,54,64),outline=(150,175,182),width=3)
    d.ellipse((x-1*scale,y+14*scale,x+9*scale,y+24*scale),fill=(20,95,108))
    d.ellipse((x+w*.15,y-7*scale,x+w*.4,y+4*scale),fill=(30,38,45),outline=(112,129,138))
    d.ellipse((x+w*.79,y+9*scale,x+w*.85,y+15*scale),fill=(226,64,73))

def present_frame(kind,t,duration,index,episode=1,scene=None):
    s=scene or {};im=make_canvas();d=ImageDraw.Draw(im)
    phase=t
    p=ease(t/max(duration,.1))
    if kind in ('street','bus'):
        street_bg(d)
        if kind=='street':
            # one actual bus, embedded into road perspective
            im=paste(im,'bus',(125,364),(178,130));d=ImageDraw.Draw(im)
            shadow(d,(130,483,304,497))
            d.polygon([(17,527),(104,517),(121,549),(27,557)],fill=(55,62,68))
            d.ellipse((153,556,218,567),fill=(56,75,80))
            text(d,(180,210),'ГОРОД ПУСТ',25,PAPER,'mm')
        else:
            # same bus shown from the curb, front door opens into the bus body
            im=paste(im,'bus',(8,290),(346,239));d=ImageDraw.Draw(im)
            gap=round(1+11*ease(t/2.3))
            d.rectangle((274-gap,369,289+gap,462),fill=(17,31,43))
            for x in (275-gap,285+gap):
                d.line((x,369,x,462),fill=(155,174,181),width=4)
            text(d,(180,242),'МАРШРУТ №17',18,PAPER,'mm')
            d.line((14,540,348,540),fill=(103,115,120),width=3)
    elif kind=='bedroom':
        room(d)
        drawing(d)
        # Asya holds the doorframe; child's bed is CLEAR and EMPTY
        person(d,50,487,'asya',1.10,t,'idle')
        text(d,(264,303),'КРОВАТЬ СОНИ',12,(212,202,180),'mm')
        d.rectangle((101,449,171,493),fill=(67,57,57),outline=(122,105,94),width=2)
        d.rectangle((114,419,140,449),fill=(94,77,74))
        text(d,(180,133),'НИКТО НЕ ОТВЕЧАЕТ',17,RED,'mm')
    elif kind=='store':
        store_bg(d)
        # Cash register is the sole prop occupying the counter area
        im=paste(im,'register',(205,373),(126,100));d=ImageDraw.Draw(im)
        if int(t*4)%9 in (0,1):
            d.rectangle((231,398,313,419),fill=(77,104,108))
        text(d,(265,416),'04:40',18,RED,'mm')
        # A visibly moving receipt, physically emerging from the checkout.
        length=7+round(22*ease(min(1,t/3.0)))
        d.polygon([(312,446),(325,446),(325,446+length),(312,446+length)],fill=(227,221,204))
        for dy in range(7,length-1,6):d.line((314,446+dy,322,446+dy),fill=(128,130,120),width=1)
        d.line((310,444,325,465),fill=(225,220,196),width=2)
        # The 04:40 register is the subject; do not print another title over shelves.
    elif kind=='meeting':
        school_bg(d)
        text(d,(180,139),'МЫ НАШЛИ ДРУГ ДРУГА',16,PAPER,'mm')
        # 3 near people distinct in action, four further as silhouettes
        for who,x in [('mark',67),('timur',289),('dina',188),('gleb',343)]:
            person(d,x,451,who,.70,t,'idle')
        person(d,78,533,'asya',1.12,t,'idle')
        person(d,235,538,'nika',1.15,t,'reach')
        person(d,315,548,'lev',.85,t,'idle')
        camera_body(d,245,411,.80)
        text(d,(185,238),'НИКА СНИМАЕТ ВСЁ',21,AMBER,'mm')
        text(d,(185,265),'ОНА — ВИДЕОБЛОГЕР',14,PAPER,'mm')
    elif kind=='shelter':
        school_bg(d)
        d.rectangle((117,268,259,459),fill=(74,61,54),outline=(133,112,88),width=7)
        # Lock on door, bolt visibly slides after 1 sec
        d.ellipse((229,358,242,371),fill=AMBER)
        bolt=round(23*ease((t-1)/1.2))
        d.rectangle((245,373,250+bolt,388),fill=(159,165,155))
        d.rectangle((86,474,275,524),fill=(79,78,70),outline=(135,128,111),width=3)
        for k,c in enumerate(((165,114,68),(87,135,155),(109,142,96))):
            d.rounded_rectangle((103+49*k,449,140+49*k,475),radius=3,fill=c)
        person(d,69,521,'mark',1.25,t,'reach')
        text(d,(180,143),'МАРК ЗАКРЫЛ ДВЕРЬ',16,PAPER,'mm')
        # camera on a desk is not on top of the door
        camera_body(d,280,489,.60)
    elif kind=='names':
        school_bg(d)
        board(d,7,False,(73,154,292,456))
        # Nika writes names, all seven visible throughout
        person(d,315,490,'nika',.80,t,'write')
        d.line((291,330,279,300+round(math.sin(t*7)*5)),fill=(218,191,230),width=3)
        text(d,(181,478),'СЕМЬ ИМЁН',17,AMBER,'mm')
    elif kind=='night':
        school_bg(d,True)
        d.rectangle((85,256,274,457),fill=(42,45,51),outline=(79,77,76),width=3)
        d.rectangle((109,270,252,343),fill=(21,26,37))
        time_text='04:39' if t < duration*.59 else '04:40'
        col=(242,225,197) if time_text=='04:39' else RED
        text(d,(181,300),time_text,43,col,'mm')
        # One lamp actually goes dark at 04:40
        if time_text=='04:39':d.ellipse((160,125,200,141),fill=(242,204,112))
        else:d.ellipse((160,125,200,141),fill=(51,56,59))
        # recorder keeps recording in dark behind door
        camera_body(d,53,466,.75)
        d.ellipse((100,481,108,489),fill=(233,51,64) if int(t*2)%2 else (115,53,59))
        text(d,(185,221),'СБОЙ ПИТАНИЯ',19,RED,'mm')
    elif kind=='morning':
        school_bg(d)
        board(d,7,True,(185,147,345,415))
        # six real cast, an empty seventh CHAIR on left with Nika purple coat
        survivors=[k for k in ORDER if k!='nika']
        for i,who in enumerate(survivors):
            xx=[37,102,161][i%3]
            yy=360 if i<3 else 501
            person(d,xx,yy,who,.63,t,'idle')
        d.rounded_rectangle((11,453,63,501),radius=4,fill=(48,46,56),outline=(146,115,179),width=3)
        d.rectangle((9,494,67,506),fill=(67,55,82))
        text(d,(39,466),'ПУСТО',10,RED,'mm')
        text(d,(168,118),'УТРО: ШЕСТЕРО',19,PAPER,'mm')
    elif kind=='recording':
        school_bg(d,True)
        # dominant camera view of GROUP of seven, with EIGHTH back silhouette
        d.rounded_rectangle((17,159,343,515),radius=16,fill=(16,21,31),outline=(109,132,143),width=7)
        d.rounded_rectangle((32,175,329,464),radius=6,fill=(25,50,63),outline=(82,112,123),width=3)
        d.rectangle((46,190,315,453),outline=(50,83,99),width=2)
        # miniature distant figures with distinct coat colours and faces
        coords=[(48,360),(81,361),(114,362),(147,363),(180,364),(213,365),(246,366)]
        for i,who in enumerate(ORDER):
            x,y=coords[i]
            person(d,x,y,who,.48,t,'idle')
        # sinister EIGHTH: silhouette behind the group, clearly isolated and taller
        xx=295;yy=243
        d.ellipse((xx-12,yy-23,xx+12,yy+1),fill=(8,13,22))
        d.polygon([(xx-19,yy),(xx+19,yy),(xx+29,yy+79),(xx-30,yy+79)],fill=(8,13,22))
        d.line((xx-12,yy+72,xx-14,yy+118),fill=(7,11,21),width=8)
        d.line((xx+12,yy+72,xx+14,yy+118),fill=(7,11,21),width=8)
        d.ellipse((xx-10,yy-14,xx-6,yy-11),fill=RED)
        d.ellipse((xx+5,yy-14,xx+9,yy-11),fill=RED)
        d.line((295,211,295,315),fill=RED,width=2)
        if t>duration*.60:
            d.arc((262,196,331,327),25,325,fill=RED,width=4)
        text(d,(57,184),'● REC',16,RED)
        text(d,(313,186),'04:39',12,PAPER,'ra')
        text(d,(180,487),'СЕМЕРО + КТО-ТО ЕЩЁ',15,AMBER,'mm')
        # Physical camcorder is visible *once*, as a small object in foreground.
        camera_body(d,19,522,.9)
    else:
        school_bg(d)
        text(d,(180,300),'СЦЕНА',22,PAPER,'mm')
    # Fine motion and lighting, never a simulated zoom or duplicate overlay.
    if kind in ('street','bus'):
        rain=random.Random(100+index)
        for k in range(33):
            x=rain.randrange(W);y=(rain.randrange(H)+t*rain.randrange(30,80))%H
            d.line((x,y,x+2,y+12),fill=(70,105,124),width=1)
    if kind in ('night','recording') and int(t*9)%31 == 0:
        d.line((0,509,W,509),fill=(79,98,113),width=1)
    return im.convert('RGB')
