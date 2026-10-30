"""Self-contained 2.5D prop art library. Each object is an independent transparent PNG.
No stock images, image-generation API, or photorealistic picture-in-picture.
Objects have consistent perspective, readable geometry and painted highlights.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

INK=(13,23,34); EDGE=(92,121,137); BLUE=(52,78,96); SKY=(129,165,177)
GOLD=(242,187,97); RED=(222,80,83); PAPER=(235,226,198)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def f(size):
    try:return ImageFont.truetype(FONT,size)
    except OSError:return ImageFont.load_default()

def new(w,h):return Image.new('RGBA',(w,h),(0,0,0,0))
def rr(d,rect,r,fill,outline=None,width=1):d.rounded_rectangle(tuple(map(int,rect)),r,fill=fill,outline=outline,width=width)
def ell(d,rect,fill,outline=None,width=1):d.ellipse(tuple(map(int,rect)),fill=fill,outline=outline,width=width)

def bus():
    im=new(950,540);d=ImageDraw.Draw(im)
    ell(d,(80,471,914,519),(0,0,0,72))
    # layered metal body and bottom running board
    rr(d,(48,129,906,466),45,(56,82,97), (121,153,166),8)
    d.polygon([(74,134),(830,134),(900,180),(900,292),(54,292)],fill=(84,122,137))
    d.polygon([(54,290),(902,290),(903,405),(48,405)],fill=(48,70,87))
    d.line((66,349,895,349),fill=(193,146,78),width=14)
    d.line((61,365,892,365),fill=(119,80,56),width=5)
    for x in [124,329,535,739]:
        rr(d,(x,163,x+164,278),13,(18,37,52), (142,173,182),5)
        d.polygon([(x+13,173),(x+100,173),(x+59,268),(x+9,267)],fill=(45,87,109,190))
        d.line((x+79,168,x+79,275),fill=(82,110,126),width=3)
        # visible empty passenger seats
        for sx in [x+30,x+111]:
            rr(d,(sx,241,sx+25,270),6,(29,48,60))
    # readable door mechanics
    rr(d,(712,170,828,399),8,(24,45,57), (150,174,180),5)
    d.line((769,173,769,397),fill=(163,177,181),width=5)
    for z in [0,1]:
        off=z*52
        d.rectangle((720+off,190,756+off,298),fill=(40,74,91),outline=(100,136,148),width=3)
    rr(d,(62,418,890,452),10,(35,54,65),(96,116,116),3)
    for cx in [240,750]:
        ell(d,(cx-71,402,cx+71,539),(18,26,34),(111,128,136),10)
        ell(d,(cx-37,437,cx+37,502),(80,92,99),(179,187,188),6)
        ell(d,(cx-10,461,cx+10,481),(38,45,53))
    rr(d,(90,296,264,338),8,(15,43,57), (162,192,194),3)
    d.text((106,300),'МАРШРУТ 17',font=f(25),fill=(232,220,174))
    d.rectangle((860,332,905,365),fill=(241,208,124),outline=(255,233,174),width=3)
    d.rectangle((50,353,65,388),fill=(168,49,53))
    return im

def camcorder():
    im=new(750,500);d=ImageDraw.Draw(im)
    ell(d,(100,400,693,460),(0,0,0,72))
    rr(d,(230,118,660,398),29,(20,34,44),(88,121,138),8)
    rr(d,(237,125,648,196),17,(41,57,70),(106,139,151),3)
    rr(d,(306,101,546,139),8,(25,35,42),(93,112,125),4)
    rr(d,(357,67,483,105),12,(26,36,44),(95,116,127),4)
    # textured round optical lens, glass catches light
    for (r,c) in [(130,(11,18,27)),(110,(90,112,129)),(91,(16,31,43)),(74,(24,68,88)),(58,(9,25,38)),(37,(57,126,150)),(17,(6,13,21))]:
        ell(d,(240-r,273-r,240+r,273+r),c,(121,158,163),3)
    ell(d,(195,217,225,247),(115,208,226,180))
    # LCD opened to side, illuminated screen and REC icon
    rr(d,(480,168,728,375),17,(13,21,32),(111,131,142),9)
    rr(d,(495,185,710,354),5,(26,55,67),(81,117,131),3)
    d.line((514,200,680,340),fill=(40,82,97),width=7)
    d.line((525,345,693,196),fill=(31,69,85),width=4)
    d.rectangle((501,188,547,224),fill=(10,19,25))
    d.text((508,195),'REC',font=f(18),fill=(238,88,91))
    ell(d,(573,129,590,146),(245,83,86));d.text((597,127),'REC',font=f(19),fill=(232,175,171))
    d.polygon([(390,395),(514,395),(536,443),(377,443)],fill=(31,40,49))
    d.line((380,407,531,407),fill=(111,125,126),width=5)
    return im

def register():
    im=new(730,510);d=ImageDraw.Draw(im)
    ell(d,(41,454,700,495),(0,0,0,65))
    # Point of sale, readable receipt and clock
    rr(d,(210,129,563,386),16,(35,47,57),(110,124,132),7)
    rr(d,(229,151,543,317),8,(16,30,40),(72,109,124),3)
    d.text((283,188),'04:40',font=f(66),fill=(244,104,102))
    d.text((278,264),'ПРОВЕРКА',font=f(20),fill=(138,171,178))
    rr(d,(350,389,449,437),8,(36,45,55),(105,120,125),4)
    rr(d,(99,364,633,464),17,(45,55,63),(114,125,133),8)
    rr(d,(129,381,338,443),10,(25,39,51),(77,91,102),4)
    for row in range(3):
        for col in range(5):
            x=144+col*37;y=393+row*14
            rr(d,(x,y,x+27,y+9),2,(82,100,109))
    d.polygon([(572,390),(652,392),(639,441),(561,445)],fill=(214,204,177),outline=(126,122,109))
    d.line((582,404,637,405),fill=(75,70,68),width=3)
    return im

def shelves():
    im=new(700,650);d=ImageDraw.Draw(im)
    d.polygon([(37,41),(635,41),(685,88),(685,625),(35,625)],fill=(54,71,82),outline=(125,145,147))
    d.polygon([(621,56),(672,95),(670,625),(618,605)],fill=(25,38,49))
    for row in range(4):
        yy=95+row*126
        d.polygon([(53,yy+74),(627,yy+74),(667,yy+91),(43,yy+91)],fill=(125,125,116))
        d.line((54,yy+76,625,yy+76),fill=(177,170,146),width=5)
        for col in range(7):
            x=68+col*76
            hue=[(139,80,70),(70,114,119),(143,113,81),(103,135,90),(112,90,124),(151,115,64),(92,117,143)][(col+row)%7]
            rr(d,(x,yy+10,x+46,yy+70),7,hue,(177,166,144),2)
            d.rectangle((x+7,yy+30,x+38,yy+47),fill=(222,202,169))
            d.line((x+11,yy+37,x+32,yy+37),fill=(111,116,108),width=2)
    return im

def drawing():
    im=new(510,550);d=ImageDraw.Draw(im)
    d.polygon([(37,20),(467,41),(455,529),(20,504)],fill=PAPER,outline=(147,124,94),width=5)
    # child handwriting and crayon sunshine
    ell(d,(350,73,428,153),(255,191,65),(202,141,54),7)
    for a in range(0,360,45):
        angle=math.radians(a);x=389;y=113
        d.line((x+45*math.cos(angle),y+45*math.sin(angle),x+69*math.cos(angle),y+69*math.sin(angle)),fill=(233,166,70),width=7)
    # mother and daughter, distinctly different heights
    for x,y,r,col in [(177,218,35,(120,76,74)),(305,268,27,(94,103,157))]:
        ell(d,(x-r,y-r,x+r,y+r),(230,163,118))
        d.arc((x-r,y-r-10,x+r,y+r-15),185,345,fill=col,width=12)
        d.line((x,y+r,x-12,y+142),fill=col,width=20)
        d.line((x-8,y+95,x-72,y+118),fill=col,width=9)
        d.line((x+9,y+96,x+69,y+113),fill=col,width=9)
        d.line((x-12,y+142,x-50,y+192),fill=col,width=10)
        d.line((x-12,y+142,x+38,y+193),fill=col,width=10)
        for xx in [x-12,x+12]:ell(d,(xx-4,y-4,xx+4,y+4),(47,50,64))
    d.text((96,459),'МАМА И СОНЯ',font=f(35),fill=(150,81,84))
    return im

def school_door():
    im=new(570,740);d=ImageDraw.Draw(im)
    ell(d,(34,687,539,727),(0,0,0,70))
    rr(d,(67,45,508,711),22,(66,77,84),(123,143,151),11)
    rr(d,(95,72,465,675),12,(52,67,78),(138,145,148),5)
    rr(d,(118,95,438,332),7,(26,46,57),(97,119,131),6)
    for xx in [214,326]:d.line((xx,105,xx,323),fill=(80,109,125),width=7)
    d.line((118,215,438,215),fill=(80,109,125),width=6)
    rr(d,(127,377,427,624),12,(51,58,66),(104,117,128),6)
    d.line((118,352,434,352),fill=(116,122,124),width=8)
    ell(d,(382,469,414,498),(183,161,120),(232,197,142),5)
    d.polygon([(399,481),(472,470),(470,482),(409,492)],fill=(159,160,147))
    d.rectangle((72,681,506,700),fill=(96,96,88))
    return im

def flashlight():
    im=new(490,360);d=ImageDraw.Draw(im)
    ell(d,(37,255,448,308),(0,0,0,60))
    d.polygon([(97,105),(334,99),(361,122),(360,238),(331,254),(96,248)],fill=(35,45,55),outline=(112,129,136))
    rr(d,(80,111,312,245),20,(49,62,69),(126,137,142),6)
    for xx in range(122,299,25):d.line((xx,116,xx,240),fill=(29,40,50),width=5)
    rr(d,(307,87,402,269),18,(59,69,79),(139,146,144),7)
    ell(d,(374,96,472,265),(198,172,116),(245,217,146),9)
    ell(d,(388,117,460,241),(255,234,175),(239,216,161),5)
    d.line((71,164,45,158),fill=(98,112,123),width=12)
    return im

BUILDERS={'bus':bus,'camera':camcorder,'register':register,'shelves':shelves,'child_drawing':drawing,'school_door':school_door,'flashlight':flashlight}
ASSET_ROOT=Path(__file__).resolve().parents[1] / 'assets' / 'props'

def artwork(name):
    path=ASSET_ROOT/(name+'.png')
    return Image.open(path).convert('RGBA') if path.is_file() else BUILDERS[name]()

@lru_cache(maxsize=32)
def sprite(name, width, height):
    if name not in BUILDERS:raise KeyError(name)
    return artwork(name).resize((int(width),int(height)),Image.Resampling.LANCZOS)

def paste_prop(scene_image, name, xy, size, opacity=255):
    obj=sprite(name,*size)
    if opacity<255:
        obj=obj.copy();obj.putalpha(obj.getchannel('A').point(lambda a:int(a*opacity/255)))
    base=scene_image.convert('RGBA')
    base.alpha_composite(obj,tuple(map(int,xy)))
    return base.convert('RGB')

def export(directory):
    target=Path(directory);target.mkdir(parents=True,exist_ok=True)
    for name,maker in BUILDERS.items():
        img=artwork(name);img.save(target/(name+'.png'))
    return sorted(target.glob('*.png'))

if __name__=='__main__':
    import sys
    for p in export(sys.argv[1] if len(sys.argv)>1 else 'output/props'):
        print(p)
