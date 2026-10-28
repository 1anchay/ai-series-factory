"""Purpose-built, animated 2D environments for 'Завтра нас меньше'.

No stock graphics, no zoom. Scenes have consistent spatial language: outdoor city,
corner grocery, lived-in bedroom, and an abandoned school shelter. 360x640 working
canvas. Static paintings are memoized; small dynamic overlays are redrawn per frame.
"""
from __future__ import annotations
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math

W,H=360,640
SKY=(13,27,42); STEEL=(46,67,80); ROAD=(19,30,41)
INK=(10,18,27); GOLD=(221,175,98); TEAL=(89,156,159)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def f(n):
    try:return ImageFont.truetype(FONT,n)
    except OSError:return ImageFont.load_default()

def grad(im, top, bottom, y0=0,y1=640):
    d=ImageDraw.Draw(im)
    for y in range(max(0,y0),min(H,y1)):
        p=(y-y0)/max(1,y1-y0)
        d.line((0,y,W,y),fill=tuple(int(a*(1-p)+b*p) for a,b in zip(top,bottom)))

def glow_draw(im,cx,cy,r,color=(233,185,106),alpha=105):
    # Soft 2D light bloom; alpha composite, not opaque rectangles.
    layer=Image.new('RGBA',(W,H))
    ld=ImageDraw.Draw(layer,'RGBA')
    ld.ellipse((cx-r/2,cy-r/2,cx+r/2,cy+r/2),fill=(*color,alpha))
    layer=layer.filter(ImageFilter.GaussianBlur(max(2,int(r*.25))))
    return Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')

def brickwork(d,x0,y0,x1,y1,line=(42,58,69),step=23):
    for y in range(int(y0),int(y1),step):
        d.line((x0,y,x1,y),fill=line,width=1)
        k=((y-y0)//step)%2
        for x in range(int(x0)+(step if k else 0),int(x1),step*2):
            d.line((x,y,x,y+step),fill=line,width=1)

def building(d,x,y,ww,hh,front,side,seed,light=0.08):
    rng=random.Random(seed)
    left=x;top=y-hh
    d.polygon([(left,top),(left+ww,top+7),(left+ww,y),(left,y)],fill=front)
    d.polygon([(left+ww,top+7),(left+ww+10,top-2),(left+ww+10,y-6),(left+ww,y)],fill=side)
    d.line((left,top,left+ww,top+7),fill=(76,94,106),width=2)
    for wy in range(int(top+18),int(y-13),25):
        for wx in range(int(left+9),int(left+ww-6),16):
            on=rng.random()<light
            c=(186,156,108) if on else ((39,61,76) if seed%2 else (30,49,64))
            d.rectangle((wx,wy,wx+6,wy+11),fill=c)
            if on:d.point((wx+2,wy+4),fill=(235,200,134))
    for wy in range(int(top+10),int(y-7),43):
        d.line((left,wy,left+ww,wy),fill=(38,53,69))

def exterior(kind):
    im=Image.new('RGB',(W,H))
    grad(im,(11,25,43),(43,66,81))
    d=ImageDraw.Draw(im)
    # dawn sky, layered clouds
    d.ellipse((214,95,311,192),fill=(51,76,92))
    d.ellipse((227,108,296,176),fill=(62,88,102))
    for i in range(14):
        x=(i*57+39)%423-35;y=92+(i*31)%156
        d.ellipse((x,y,x+86,y+20),fill=(26,47,66))
    # far skyline: distinct rooftop shapes and roof antennas
    rng=random.Random(515)
    x=-7
    while x<370:
        ww=rng.randint(23,52);hh=rng.randint(95,230)
        building(d,x,369,ww,hh,(23,42,61),(13,34,50),rng.randint(0,100000),.09)
        if rng.random()<.4:
            d.line((x+ww//2,369-hh,x+ww//2,351-hh),fill=(57,73,83),width=2)
        x+=ww+rng.randint(1,9)
    # closer blocks give parallax-like depth without camera zoom
    building(d,-38,436,119,267,(30,51,65),(20,41,58),311,.055)
    building(d,306,443,118,314,(26,48,63),(18,39,53),700,.035)
    brickwork(d,0,224,58,435,line=(36,60,73),step=31)
    # roadway and sidewalks, true perspective, drain and asphalt patches
    d.polygon([(105,442),(253,442),(W,H),(0,H)],fill=(22,36,46))
    d.polygon([(0,443),(109,443),(0,H)],fill=(43,52,57))
    d.polygon([(255,443),(W,443),(W,H)],fill=(40,51,59))
    d.line((109,443,0,640),fill=(94,95,83),width=4)
    d.line((254,443,360,640),fill=(94,99,91),width=4)
    for yy in (490,535,590):
        k=(yy-442)/198
        d.line((180-int(40*k),yy,180+int(40*k),yy),fill=(32,48,58),width=2)
    for yy in (489,545,606):
        off=int((yy-440)*.13)
        d.polygon([(178-off,yy),(182+off,yy),(185+off,yy+7),(175-off,yy+7)],fill=(95,90,76))
    # water stains/puddles
    for x,y,r in [(123,580,25),(243,549,22),(193,626,34),(62,562,16)]:
        d.ellipse((x-r,y-3,x+r,y+6),fill=(37,61,74),outline=(55,83,92))
        d.line((x-r//2,y,x+r//2,y),fill=(70,100,105),width=1)
    # bus stop/street signage in far field
    d.line((278,330,278,491),fill=(79,90,96),width=5)
    d.rounded_rectangle((256,343,308,367),radius=5,fill=(33,76,91),outline=(107,153,163),width=2)
    d.text((267,346),'17',font=f(15),fill=(217,222,211))
    d.polygon([(295,424),(320,424),(325,473),(284,473)],fill=(19,29,43))
    # utility wires, foreground pipes, broken traffic signal
    d.line((0,286,130,300,240,284,360,306),fill=(31,39,51),width=2,joint='curve')
    d.line((65,306,66,463),fill=(47,60,69),width=5)
    d.rounded_rectangle((52,320,79,385),radius=5,fill=(22,32,43),outline=(72,84,85),width=2)
    for yy,col in ((334,(55,57,52)),(354,(155,68,64)),(373,(61,86,72))):
        d.ellipse((58,yy,72,yy+14),fill=col)
    # outdoor props are placed away from the center of the active scene
    if kind in ('street','shadow','cold_open'):
        d.polygon([(9,540),(41,538),(58,573),(16,575)],fill=(29,42,49))
        d.line((14,543,51,567),fill=(74,82,81),width=2)
        d.rectangle((319,516,344,559),fill=(49,64,68),outline=(97,98,85),width=2)
        d.line((322,520,341,520),fill=(113,119,98),width=2)
    if kind=='bus':
        d.rectangle((21,510,339,517),fill=(64,77,81))
        d.ellipse((15,508,344,528),outline=(38,61,70),width=2)
    return im

def room_perspective(im,kind):
    grad(im,(21,32,49),(43,50,54))
    d=ImageDraw.Draw(im)
    # Walls with corner and roof perspective
    d.polygon([(0,0),(360,0),(360,449),(0,460)],fill=(27,39,54))
    d.polygon([(0,58),(90,124),(90,448),(0,462)],fill=(20,31,43))
    d.polygon([(360,58),(284,128),(284,442),(360,460)],fill=(22,34,48))
    d.line((0,58,90,124),fill=(55,65,73),width=3)
    d.line((360,58,284,128),fill=(55,65,73),width=3)
    d.line((90,124,284,128),fill=(51,62,69),width=2)
    d.polygon([(0,458),(360,453),(360,H),(0,H)],fill=(36,39,42))
    for yy in (482,518,572,623):
        d.line((0,yy,360,yy),fill=(57,57,54),width=2)
    for xx in (70,178,290):
        d.line((xx,460,180+(xx-180)*1.35,H),fill=(54,53,49),width=2)
    d.line((0,457,360,457),fill=(86,78,68),width=5)
    d.line((92,447,285,447),fill=(111,98,79),width=2)
    # plaster chips and nails, kept subtle
    rng=random.Random(240)
    for _ in range(90):
        x=rng.randint(0,358);y=rng.randint(76,435)
        d.line((x,y,x+rng.randint(1,4),y),fill=(42,54,64))
    return im

def sign(d,box,txt,fill=(234,216,178)):
    d.rounded_rectangle(box,radius=3,fill=(33,47,58),outline=(94,100,95),width=2)
    x0,y0,x1,y1=box
    ft=f(10 if len(txt)<11 else 9)
    d.text(((x0+x1)/2,(y0+y1)/2),txt,font=ft,fill=fill,anchor='mm')

def interior(kind):
    im=room_perspective(Image.new('RGB',(W,H)),kind)
    d=ImageDraw.Draw(im)
    # left and right props ensure central action remains unobscured
    if kind in ('bedroom',):
        # wardrobe with rails and shelves at right, rug/floor objects
        d.rectangle((287,155,354,444),fill=(64,54,54),outline=(95,81,74),width=3)
        d.line((318,158,318,442),fill=(41,42,49),width=3)
        d.ellipse((311,283,315,289),fill=GOLD)
        d.ellipse((323,283,328,289),fill=GOLD)
        d.rounded_rectangle((20,321,81,422),radius=5,fill=(67,55,54),outline=(107,86,72),width=2)
        d.rectangle((27,329,74,349),fill=(55,50,52))
        d.polygon([(12,488),(235,488),(280,538),(15,538)],fill=(48,54,54),outline=(74,76,69))
        sign(d,(152,166,243,192),'СЕМЬЯ')
        d.rectangle((150,197,242,266),fill=(59,70,76),outline=(118,101,77),width=4)
        d.line((173,205,224,259),fill=(32,37,45),width=2)
    elif kind in ('store',):
        # shop back wall with luminous refrigerator and hanging signs
        d.rectangle((5,155,353,444),fill=(29,43,55),outline=(65,80,83),width=3)
        for x in (34,140,246):
            d.rectangle((x,168,x+84,429),fill=(38,61,70),outline=(81,96,99),width=2)
            for yy in (220,300,377):
                d.line((x+5,yy,x+80,yy),fill=(102,97,77),width=4)
                for j in range(4):
                    xx=x+7+j*18
                    col=[(166,92,65),(87,151,145),(189,152,94),(98,104,141)][(j+yy//10)%4]
                    d.rounded_rectangle((xx,yy-26,xx+14,yy-3),radius=3,fill=col,outline=(42,54,60))
        d.rectangle((132,86,227,112),fill=(31,60,66),outline=(96,119,116),width=2)
        d.text((180,99),'24 / 7',font=f(17),fill=(208,227,209),anchor='mm')
        d.polygon([(34,490),(336,490),(353,H),(0,H)],fill=(45,51,51))
        for yy in (509,557,601):
            d.line((0,yy,360,yy),fill=(69,70,66))
        d.rectangle((16,518,90,542),fill=(64,68,63))
        sign(d,(12,112,116,135),'ПРОДУКТЫ')
    elif kind in ('meeting','introductions','shelter','names','night','clock','morning','reveal'):
        # Consistent school: corridor/window/exit sign, lockers and radiator
        for x in (15,47):
            d.rectangle((x,161,x+29,392),fill=(59,67,71),outline=(91,100,97),width=2)
            for yy in (177,199,246,291,335):
                d.line((x+5,yy,x+24,yy),fill=(37,55,65),width=2)
            d.ellipse((x+23,290,x+26,295),fill=(190,165,101))
        d.rectangle((287,165,349,353),fill=(14,35,51),outline=(76,91,90),width=6)
        d.line((320,168,320,351),fill=(86,94,99),width=3)
        d.line((291,274,346,274),fill=(86,94,99),width=3)
        # distant city beyond window, distinct from the school interior
        for x,y,bw,bh in ((293,347,14,48),(310,347,17,75),(327,347,15,60)):
            d.rectangle((x,y-bh,x+bw,y),fill=(34,57,70))
        d.rectangle((292,368,344,401),fill=(64,70,73),outline=(96,99,92))
        for yy in (378,388,397):d.line((296,yy,340,yy),fill=(31,45,54))
        # school notice board and emergency exit
        d.rectangle((127,160,229,237),fill=(72,58,49),outline=(108,90,71),width=4)
        for x,y,col in ((144,182,(217,203,163)),(186,182,(129,160,157)),(154,207,(180,115,106))):
            d.rectangle((x,y,x+26,y+22),fill=col)
        sign(d,(127,104,230,126),'ВЫХОД',(160,219,190))
        d.line((179,128,179,159),fill=(90,94,86),width=2)
        if kind in ('shelter','night','names'):
            # makeshift camp: crates, bags, old mattress, water bottles
            d.rectangle((12,453,71,502),fill=(94,73,56),outline=(124,97,69),width=3)
            d.line((12,478,71,478),fill=(143,116,85),width=2)
            d.rectangle((285,468,338,509),fill=(74,70,61),outline=(113,104,82),width=3)
            for x in (307,327):
                d.rounded_rectangle((x,441,x+9,468),radius=3,fill=(71,120,141),outline=(142,174,164),width=1)
                d.rectangle((x+2,438,x+7,443),fill=(222,224,199))
            d.rounded_rectangle((83,504,265,536),radius=11,fill=(65,65,62),outline=(118,101,78),width=2)
            d.line((83,527,264,527),fill=(38,41,44),width=4)
        if kind=='night':
            d.rectangle((17,275,343,286),fill=(55,63,66))
            d.rectangle((29,303,333,316),fill=(66,76,78))
        if kind in ('meeting','introductions','morning'):
            d.line((2,452,358,452),fill=(103,90,75),width=3)
    else:
        # table/wall panel for phone close-up
        d.rounded_rectangle((20,446,341,483),radius=5,fill=(72,57,53),outline=(126,101,78),width=3)
        d.line((31,487,331,487),fill=(43,42,45),width=5)
        d.rectangle((32,232,83,378),fill=(43,58,71),outline=(107,103,82),width=3)
    return im

@lru_cache(maxsize=24)
def base_scene(kind):
    outdoor=kind in ('cold_open','street','bus','shadow')
    im=exterior(kind) if outdoor else interior(kind)
    return im

def environment(kind,t,index=0):
    """A detailed static scene plus subtle weather/light movements, never zoom."""
    im=base_scene(kind).copy()
    ov=Image.new('RGBA',(W,H))
    d=ImageDraw.Draw(ov,'RGBA')
    outdoor=kind in ('cold_open','street','bus','shadow')
    if outdoor:
        # Three depth planes of drizzle; deterministic positions per frame.
        rng=random.Random(2020+index)
        for i in range(42):
            x=rng.randrange(W+35)-17
            y=(rng.randrange(H+30)+int(t*(45+i%5*17)))%(H+30)-15
            d.line((x,y,x+2+(i%3),y+7+(i%9)),fill=(143,189,205,28+(i%4)*8),width=1)
        # faint passing light reflections on empty road; subtle atmospheric life
        pulse=.45+.55*math.sin(t*.71+index)
        d.ellipse((108-int(t*4)%28,556,157+int(t*4)%15,560),fill=(98,133,143,int(18+12*pulse)))
        for i in range(4):
            xx=(i*90+int(t*5+i*21))%390-10
            yy=150+i*67+int(8*math.sin(t*.13+i))
            d.ellipse((xx,yy,xx+73,yy+10),fill=(128,151,169,10))
    else:
        # subtle warm ceiling bounce, shifting warm and cold light; no opaque bands
        pulse=.55+.45*math.sin(t*2.2+index*.9)
        d.ellipse((136,106,231,139),fill=(239,192,116,int(9+15*pulse)))
        d.line((180,111,180,158),fill=(244,193,112,int(24+18*pulse)),width=2)
        rng=random.Random(index+817)
        for i in range(18):
            x=rng.randrange(W);y=(rng.randrange(H)+int(t*(5+i%5)))%H
            d.ellipse((x,y,x+1,y+1),fill=(187,169,123,22+(i%4)*8))
    im=Image.alpha_composite(im.convert('RGBA'),ov)
    return im.convert('RGB')
