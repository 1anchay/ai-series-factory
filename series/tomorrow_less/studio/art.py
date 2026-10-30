"""Original flat 2D animated scenery for 'Завтра нас меньше'. No image-generation costs."""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
import random, math
from functools import lru_cache
from characters import CAST, ORDER, person, portrait_card, label
from environment import environment as stage_environment
from cinema import finish as cinematic_finish

W,H=360,640
C_BG=(13,20,32); C_WALL=(25,35,48); C_FLOOR=(18,29,38)
WHITE=(238,236,227); DIM=(154,165,176); RED=(222,78,82)
AMBER=(239,176,89); BLUE=(107,157,186); TEAL=(93,165,157)
COLORS=[(224,156,76),(167,75,76),(144,116,176),(88,151,186),(94,165,157),(159,129,91),(91,130,96)]
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_N='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def font(n,bold=True):
    try:return ImageFont.truetype(FONT if bold else FONT_N,int(n))
    except OSError:return ImageFont.load_default()

def typ(d,xy,t,sz=16,col=WHITE,anchor=None):d.text(xy,str(t),font=font(sz),fill=col,anchor=anchor)
def pt(x,y):return (int(x),int(y))
def ease(a):
    a=max(0,min(1,a));return a*a*(3-2*a)

@lru_cache(maxsize=8)
def background(mode):
    im=Image.new('RGB',(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        k=y/H
        if mode=='street':c=(int(11+13*k),int(19+15*k),int(35+16*k))
        else:c=(int(15+11*k),int(20+14*k),int(31+17*k))
        d.line((0,y,W,y),fill=c)
    rng=random.Random(147)
    if mode=='street':
        x=-10
        while x<W+20:
            width=rng.randint(32,68);height=rng.randint(150,360)
            d.rectangle((x,410-height,x+width,465),fill=(18+rng.randint(0,9),29+rng.randint(0,7),43+rng.randint(0,7)))
            for xx in range(x+9,x+width-5,14):
                for yy in range(425-height,455,22):
                    if rng.random()<.08:d.rectangle((xx,yy,xx+6,yy+8),fill=(84,75,70))
            x+=width+4
        d.polygon([(0,468),(W,468),(W,H),(0,H)],fill=(20,30,39))
        d.line((W//2,510,W//2,H),fill=(63,70,68),width=2)
        for y in [500,548,610]:d.line((0,y,W,y),fill=(25,42,52),width=2)
    else:
        d.polygon([(0,0),(W,0),(W,490),(0,490)],fill=(24,32,47))
        for y in range(90,500,90):d.line((0,y,W,y),fill=(28,40,53),width=2)
        d.polygon([(0,480),(W,480),(W,H),(0,H)],fill=(25,28,34))
        d.polygon([(W*.20,480),(W*.80,480),(W,640),(0,640)],fill=(32,33,37))
        d.line((0,480,W,480),fill=(60,64,68),width=4)
    return im

def glow(im,x,y,r,col=(239,176,89),alpha=68):
    overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
    for i in range(5,0,-1):
        rr=r*(i/5)
        d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(*col,max(1,int(alpha*(6-i)/19))))
    im=Image.alpha_composite(im.convert('RGBA'),overlay)
    return im

def woman(d,x,y,clr=(224,156,76),phase=0,scale=1,walking=False,who=None):
    # Backwards-compatible staging coordinates; actual faces and costumes
    # are defined once in characters.py for every episode.
    if who is None:
        colmap={COLORS[0]:'asya', COLORS[1]:'mark',COLORS[2]:'nika',
                COLORS[3]:'timur',COLORS[4]:'dina',COLORS[5]:'lev',COLORS[6]:'gleb'}
        who=colmap.get(clr,'asya')
    person(d,x,y+55*scale,who,scale=scale*.78,phase=phase,
           pose='walk' if walking else ('write' if who=='nika' else 'idle'))


def city_rain(d,t,num=45):
    r=random.Random(419)
    for i in range(num):
        x=r.randint(0,W);y=(r.randint(0,H)+t*r.randint(80,170))%H
        d.line((x,y,x+3,y+15),fill=(58,83,101),width=1)

def cast(d,x,y,n=7,phase=0):
    selected=ORDER if n==7 else [k for k in ORDER if k!='nika']
    # Two staggered rows make each body/face larger and keep labels readable.
    if n==7:
        rows=[(selected[:4],[46,136,224,312],355,.72),
              (selected[4:],[89,180,272],481,.92)]
    else:
        rows=[(selected[:3],[73,180,287],356,.84),
              (selected[3:],[73,180,287],483,.90)]
    for keys,xs,feet,sc in rows:
        for j,key in enumerate(keys):
            yy=feet+2*math.sin(phase*1.2+j*.7)
            person(d,xs[j],yy,key,sc,phase+j*.35,'idle')
            label(d,key,xs[j],yy+6,small=True)


def wall_names(d,x,y,count=7,highlight=False):
    names=['АСЯ','МАРК','НИКА','ТИМУР','ДИНА','ЛЕВ','ГЛЕБ']
    d.rounded_rectangle((x,y,x+254,y+270),radius=9,fill=(49,47,46),outline=(98,83,69),width=4)
    typ(d,(x+16,y+12),'МЫ ЗДЕСЬ',16,WHITE)
    for j,name in enumerate(names[:count]):
        c=RED if (highlight and name=='НИКА') else (222,213,192)
        typ(d,(x+17,y+46+j*29),f'{j+1}. {name}',15,c)
        d.line((x+130,y+59+j*29,x+227,y+59+j*29),fill=(89,85,81))

def draw(kind,t,duration,index,episode=1,scene=None):
    outdoor=kind in ('cold_open','street','bus','shadow','meeting')
    im=stage_environment(kind,t,index)
    d=ImageDraw.Draw(im)
    p=ease(t/max(.1,duration))
    if kind=='cold_open':
        d.rectangle((18,124,342,270),outline=(74,86,101),width=3)
        typ(d,(180,165),'07:12',46,WHITE,anchor='mm')
        typ(d,(180,226),'ГОРОД НЕ ОТВЕЧАЕТ',16,RED,anchor='mm')
        d.ellipse((47,418,70,436),fill=(53,56,63))
        woman(d,170+3*math.sin(t*.8),457,phase=t,scale=1.4,who='asya')
        label(d,'asya',170,574)
    elif kind=='bedroom':
        d.rectangle((25,122,144,285),fill=(14,25,37),outline=(98,99,94),width=7)
        d.line((85,122,85,284),fill=(64,78,91),width=4)
        d.rectangle((45,382,325,437),fill=(76,58,56));d.rectangle((30,414,335,507),fill=(56,65,74))
        d.rounded_rectangle((209,284,305,381),radius=6,fill=(47,55,68),outline=(99,99,93),width=3)
        typ(d,(258,315),'СОНЯ',15,WHITE,anchor='mm')
        d.ellipse((248,327,269,348),fill=(168,128,99));d.polygon([(239,366),(256,344),(277,366)],fill=(176,128,82))
        d.rounded_rectangle((126,371,181,446),radius=8,fill=(18,29,37),outline=(55,130,148),width=3)
        typ(d,(153,407),'07:12',12,WHITE,anchor='mm')
        d.ellipse((180,410,188,418),fill=(231,101,101))
        # Daughter's missing photo is the emotional stake, not random dressing.
        d.rectangle((244,170,314,246),fill=(104,87,65),outline=(178,148,103),width=4)
        d.ellipse((262,183,283,204),fill=(214,165,135))
        d.polygon([(256,227),(272,205),(290,228)],fill=(180,131,95))
        typ(d,(280,237),'СОНЯ',8,WHITE,anchor='mm')
    elif kind=='street':
        for x,y in [(44,470),(194,490)]:
            d.rounded_rectangle((x,y,x+112,y+44),radius=8,fill=(55,65,76),outline=(84,94,105),width=3)
            d.ellipse((x+14,y+32,x+33,y+51),fill=(15,19,27));d.ellipse((x+82,y+32,x+101,y+51),fill=(15,19,27))
        angle=math.sin(t*1.7)*5
        d.polygon([(151,490),(151+angle,465),(183+angle,466),(184,492)],fill=(75,91,99))
        d.rectangle((0,557,360,558),fill=(44,55,63))
        woman(d,265,430,(224,156,76),t,1.2,who='asya')
        label(d,'asya',265,516)
        d.polygon([(20+t*7%160,541),(34+t*7%160,542),(28+t*7%160,552)],fill=(99,99,88))
    elif kind=='bus':
        d.rounded_rectangle((20,274,341,511),radius=18,fill=(53,71,82),outline=(95,105,111),width=5)
        d.rectangle((45,299,268,411),fill=(17,36,51),outline=(81,102,114),width=5)
        d.line((152,298,152,411),fill=(78,105,115),width=4)
        d.rectangle((283,305,329,480),fill=(25,39,53),outline=(106,111,110),width=4)
        opened=22*abs(math.sin(t*1.5))
        d.line((304-opened,309,304-opened,477),fill=(160,177,174),width=5)
        d.ellipse((54,459,78,486),fill=(215,193,102) if int(t*1.2)%2==0 else (104,104,86))
        # Mechanical door panels visibly slide apart instead of a static empty bus.
        gap=round(3+15*ease(abs(math.sin(t*1.15))))
        d.rectangle((283,308,306-gap,476),fill=(36,64,78),outline=(143,158,160),width=2)
        d.rectangle((306+gap,308,329,476),fill=(36,64,78),outline=(143,158,160),width=2)
        for x in [89,285]:d.ellipse((x,489,x+36,525),fill=(16,22,27))
        typ(d,(154,444),'МАРШРУТ 17',17,WHITE,anchor='mm')
    elif kind=='store':
        for x in (24,145,266):
            d.rectangle((x,158,x+91,488),fill=(45,54,58),outline=(80,80,81),width=3)
            for yy in (216,304,393):
                d.line((x+9,yy,x+82,yy),fill=(128,112,90),width=5)
                for k in range(3):d.rectangle((x+14+23*k,yy-31,x+28+23*k,yy-5),fill=(64+30*k,82,87))
        d.rectangle((162,450,313,507),fill=(48,42,41));d.rectangle((208,421,289,453),fill=(69,73,76))
        d.rectangle((213,430,267,439),fill=(195,198,164) if int(t*3)%7 else (35,39,44))
        d.rectangle((12,78,348,86),fill=AMBER if int(t*3)%7 else (100,105,87))
        typ(d,(180,116),'МАГАЗИН 24/7',17,WHITE,anchor='mm')
        # Unattended conveyor still ticks forward.
        for k in range(5):
            xx=177+((k*27+int(t*12))%114)
            d.line((xx,473,xx+12,473),fill=(91,105,106),width=3)
    elif kind=='phone':
        d.ellipse((130,460,240,485),fill=(18,18,22))
        d.rounded_rectangle((85,172,277,449),radius=23,fill=(13,19,24),outline=(73,100,115),width=8)
        d.rounded_rectangle((98,194,262,423),radius=13,fill=(26,54,68))
        typ(d,(180,244),'СВЯЗЬ',25,WHITE,anchor='mm')
        typ(d,(180,299),'НЕТ СЕТИ',22,RED,anchor='mm')
        for k in range(3):
            rr=14+int((t*60+40*k)%100)
            d.arc((180-rr,337-rr,180+rr,337+rr),15,165,fill=(75,153,166),width=2)
    elif kind=='shadow':
        woman(d,85,450,phase=t,scale=1.1,who='asya')
        label(d,'asya',86,527)
        d.ellipse((260,424,310,440),fill=(12,20,30))
        x=300-18*ease(p)
        d.ellipse((x-10,340,x+10,362),fill=(8,13,20))
        d.polygon([(x-18,358),(x+18,358),(x+24,419),(x-24,419)],fill=(8,13,20))
        d.line((x-12,417,x-14,439),fill=(10,14,19),width=8);d.line((x+13,417,x+12,439),fill=(10,14,19),width=8)
    elif kind=='meeting':
        d.rounded_rectangle((16,119,344,216),radius=13,fill=(20,32,45),outline=(76,90,102),width=3)
        cast(d,180,374,7,t)
        typ(d,(180,161),'МЫ НАШЛИ ДРУГ ДРУГА',19,WHITE,anchor='mm')
        # Warm portable lamp adds continuity between evening scenes.
        d.ellipse((166,550,194,562),fill=(44,37,26))
        d.ellipse((173,540,187,552),fill=AMBER)
        typ(d,(180,194),'НАС СЕМЕРО',23,AMBER,anchor='mm')
    elif kind=='introductions':
        keys=(scene or {}).get('characters',['asya','mark'])
        if len(keys)==2:
            boxes=[(22,158,171,494),(189,158,338,494)]
        else:
            boxes=[(12,158,121,494),(126,158,235,494),(240,158,349,494)]
        for j,(who,box) in enumerate(zip(keys,boxes)):
            portrait_card(im,who,box,phase=t+j*.5)
        typ(d,(180,113),'ТЕ, КТО ОСТАЛСЯ',20,WHITE,anchor='mm')
        d.line((28,522,332,522),fill=(99,89,68),width=3)
    elif kind=='shelter':
        d.rectangle((107,167,253,489),fill=(85,68,63),outline=(118,92,73),width=7)
        d.ellipse((231,320,244,333),fill=AMBER)
        d.rectangle((66+int(20*p),443,296+int(20*p),485),fill=(75,74,66))
        d.line((25,490,331,490),fill=(141,116,89),width=7)
        woman(d,68,400,COLORS[1],t,1.2,who='mark')
        label(d,'mark',83,501)
        typ(d,(180,124),'УБЕЖИЩЕ',21,WHITE,anchor='mm')
    elif kind=='names':
        wall_names(d,51,120,max(1,min(7,int(t*3)+1)))
        woman(d,306,436,COLORS[2],t,1.,who='nika')
        label(d,'nika',300,502)
        d.line((286,386,252,318+math.sin(t*6)*2),fill=(151,125,176),width=8)
    elif kind=='night':
        # Seven different blankets/hair outlines, not seven anonymous heads.
        for k,key in enumerate(ORDER):
            x=16+k*47
            s_cast=CAST[key]
            d.rounded_rectangle((x,396,x+40,445),radius=7,fill=s_cast.coat,outline=s_cast.accent,width=2)
            d.ellipse((x+8,388,x+31,411),fill=s_cast.skin)
            d.pieslice((x+8,385,x+31,402),180,355,fill=s_cast.hair)
        d.polygon([(252,130),(315,130),(336,405),(240,405)],fill=(75,61,43) if int(t*3)%5 else (30,36,40))
        typ(d,(180,260),'04:39',44,WHITE,anchor='mm')
    elif kind=='clock':
        d.ellipse((81,152,279,350),fill=(51,58,67),outline=(131,131,124),width=8)
        d.ellipse((96,165,266,336),fill=(17,28,41))
        typ(d,(180,243),'04:40',40,RED if p>.55 else WHITE,anchor='mm')
        d.line((180,251,181+math.sin(t*7)*56,300),fill=AMBER,width=3)
        d.rectangle((0,414,W,430),fill=(73,74,68) if p>.5 else (41,51,56))
    elif kind=='morning':
        survivors=[k for k in ORDER if k!='nika']
        for j,key in enumerate(survivors):
            xx=12+(j%3)*114; yy=140+(j//3)*184
            portrait_card(im,key,(xx,yy,xx+108,yy+177),phase=t+j*.15)
        typ(d,(180,111),'ИХ ОСТАЛОСЬ ШЕСТЕРО',19,RED,anchor='mm')
    elif kind=='recording':
        # Physical proof survives the memory wipe: Nika's video camera.
        d.rounded_rectangle((35,123,327,502),radius=19,fill=(11,17,26),outline=(106,121,129),width=9)
        d.rounded_rectangle((53,145,308,440),radius=9,fill=(25,40,54),outline=(47,78,92),width=3)
        d.rectangle((59,152,302,435),outline=(75,92,99),width=2)
        d.rectangle((76,300,275,336),fill=(31,47,61))
        d.line((152,155,152,435),fill=(55,69,76),width=2)
        # On the recording, Nika is present despite everyone forgetting her.
        person(d,153+2*math.sin(t*2),382,'nika',1.28,t,'idle')
        typ(d,(77,163),'REC',15,RED)
        if int(t*2)%2==0:d.ellipse((123,167,134,178),fill=RED)
        typ(d,(274,163),'04:39',14,WHITE,anchor='ra')
        d.rectangle((68,452,296,480),fill=(26,33,44),outline=(86,92,99),width=2)
        typ(d,(182,465),'ЗАПИСЬ СОХРАНЕНА',13,AMBER,anchor='mm')
        if p>.72:
            # The unexpected figure beyond the camera's visible area.
            d.ellipse((258,241,282,266),fill=(10,16,23))
            d.polygon([(255,260),(285,260),(302,340),(245,340)],fill=(9,14,22))
    elif kind=='reveal':
        wall_names(d,52,132,7,True)
        d.rounded_rectangle((81,468,280,524),radius=7,fill=(49,52,55))
        typ(d,(180,485),'КТО ТАКАЯ',19,WHITE,anchor='mm')
        typ(d,(180,510),'НИКА?',24,RED,anchor='mm')
        if p>.55:
            # Point specifically at third name, not 'last name'.
            d.line((263,260,226,230),fill=(222,184,124),width=5)
            d.ellipse((218,222,231,235),fill=(236,189,125))
    else:
        typ(d,(180,320),'СЦЕНА',24,WHITE,anchor='mm')
    # Always animate atmosphere, independent of photographed frames.
    flicker=max(.2,(.62+.25*math.sin(t*2.9+index)))
    for k in range(8):
        x=(29+ k*41 + int(t*(4+k%3)))%W
        y=(115+k*51+int(t*(3+k%4)))%H
        d.ellipse((x,y,x+1,y+1),fill=(72,87,93))
    if kind in ('store','clock','night') and int(t*12)%30==0:
        d.rectangle((0,82,W,85),fill=(175,142,99))
    return cinematic_finish(im,kind,t,index)

def subtitle_panel(im,fulltext,t,voice_duration):
    # Max two lines. Words are displayed in consecutive chunks of the actual narration.
    if t<.16 or t>voice_duration+.18:return im
    words=fulltext.split(); groups=[];cur=[]
    for word in words:
        cur.append(word)
        if len(cur)>=5 or (len(cur)>=3 and word.endswith(('.', '?','!'))):groups.append(' '.join(cur));cur=[]
    if cur:groups.append(' '.join(cur))
    weights=[max(1,sum(map(len,g.split()))) for g in groups]
    target=max(0,min(1,(t-.16)/max(voice_duration-.2,.2)))*sum(weights)
    acc=0;idx=len(groups)-1
    for k,ww in enumerate(weights):
        acc+=ww
        if target<acc:idx=k;break
    phrase=groups[idx];size=23
    while size>=15:
        f=font(size);lines=['']
        for word in phrase.split():
            maybe=(lines[-1]+' '+word).strip()
            if f.getlength(maybe)>W-38 and lines[-1]:lines.append(word)
            else:lines[-1]=maybe
        if len(lines)<=2:break
        size-=1
    d=ImageDraw.Draw(im)
    y=535 if len(lines)==2 else 550
    d.rounded_rectangle((12,y-19,348,y+len(lines)*32+12),radius=9,fill=(7,13,23),outline=(90,95,98),width=2)
    for j,line in enumerate(lines):
        ww=f.getlength(line);d.text(((W-ww)/2,y+j*30),line,font=f,fill=WHITE)
    return im

def hud(im,kind,index,t,duration,episode=1):
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((12,12,348,65),radius=9,fill=(8,15,25),outline=(44,61,78),width=2)
    typ(d,(23,19),'ЗАВТРА НАС МЕНЬШЕ',15,WHITE)
    count=6 if kind in ('morning','reveal','recording') else 7
    typ(d,(23,45),f'ДЕНЬ {2 if count==6 else 1:02d}',11,DIM)
    typ(d,(337,44),f'ОСТАЛОСЬ {count:02d}',12,RED if count<7 else AMBER,anchor='ra')
    return im
