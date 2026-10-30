"""Original vector 2D motion thriller: real character actions, no photo panning.
Resolution 576x1024, independently animated objects, deliberate composition.
"""
import math, random
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont
W,H=576,1024
B=(17,24,39);WALL=(25,34,51);WHITE=(248,246,238);MUTE=(146,158,170);GREY=(189,196,202)
RED=(211,63,81);YELLOW=(239,185,66);CYAN=(87,166,183);GOLD=(204,143,83)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_NORMAL='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
@lru_cache(maxsize=60)
def font(size=34,bold=True):
 try:return ImageFont.truetype(FONT if bold else FONT_NORMAL,size)
 except:return ImageFont.load_default()
def clamp(x,a=0,b=1):return max(a,min(b,x))
def sm(x):x=clamp(x);return x*x*(3-2*x)
def text(d,xy,s,size=30,color=WHITE,anchor=None,stroke=0):d.text(xy,s,font=font(size),fill=color,anchor=anchor,stroke_width=stroke,stroke_fill=B)
def roundrect(d,box,fill,outline=None,r=8,width=2):d.rounded_rectangle(tuple(map(int,box)),radius=r,fill=fill,outline=outline,width=width)
def line(d,*p,fill=WHITE,width=3):d.line(tuple(map(int,p)),fill=fill,width=width,joint='curve')
def disk(d,x,y,r,fill,outline=None,w=2):d.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=outline,width=w)
@lru_cache(maxsize=1)
def backdrop():
 im=Image.new('RGB',(W,H));d=ImageDraw.Draw(im)
 for y in range(H):
  k=y/H;c=(int(15+11*k),int(22+12*k),int(38+8*k));d.line((0,y,W,y),fill=c)
 for y in range(120,770,68):d.line((0,y,W,y),fill=(30,40,57),width=1)
 return im

def header(d,label,t):
 text(d,(31,30),'НОЧНАЯ СМЕНА',17,MUTE)
 text(d,(544,30),'02:17',18,YELLOW,'ra')
 line(d,25,59,550,59,fill=(65,74,91),width=2)
 text(d,(27,88),label,22,WHITE)

def alert(d,label,x=70,y=155,w=None):
 ww=w or min(500,int(font(26).getlength(label)+47))
 d.polygon([(x,y+7),(x+ww-2,y),(x+ww+3,y+52),(x+3,y+55)],fill=(219,215,193))
 text(d,(x+16,y+13),label,26,(25,30,40))

def hero(d,x,y,s=1.,t=0,pose='stand',double=False,face='right'):
 # coherent character identity, with tiny visible features. Grounded feet.
 def P(dx,dy):return (int(x+dx*s),int(y+dy*s))
 bob=2.2*math.sin(t*2);walk=12*math.sin(t*7.2) if pose=='walk' else 0
 d.ellipse((x-39*s,y+3*s,x+42*s,y+15*s),fill=(10,16,26))
 for dx,end in [(-13,-14-walk),(13,16+walk)]:
  line(d,*P(dx,-92),*P(end,-10),fill=(15,20,30),width=max(5,int(13*s)))
  line(d,*P(end,-9),*P(end+12,0),fill=(8,12,19),width=max(5,int(10*s)))
 jacket=(43,51,66) if double else (53,69,83)
 d.polygon([P(-29,-186+bob),P(23,-186+bob),P(35,-92),P(-30,-92)],fill=jacket,outline=(113,123,134))
 if not double:
  # orange safety stripes unmistakable even from afar
  line(d,*P(-26,-136),*P(29,-136),fill=(201,123,59),width=max(3,int(7*s)))
  line(d,*P(-2,-176),*P(0,-100),fill=(201,123,59),width=max(2,int(4*s)))
 hand_target={'switch':(90,-145),'point':(102,-165),'phone':(22,-199),'stand':(34,-104),'walk':(28+walk,-112)}.get(pose,(32,-105))
 sh=P(23,-173+bob);el=P(43,-165);hand=P(*hand_target)
 line(d,*sh,*el,fill=jacket,width=max(5,int(18*s)))
 line(d,*el,*hand,fill=jacket,width=max(5,int(15*s)))
 disk(d,*hand,max(3,int(8*s)),(184,149,127))
 line(d,*P(-28,-174),*P(-32,-110),fill=jacket,width=max(6,int(17*s)))
 d.rectangle((*P(-7,-207+bob),*P(9,-186+bob)),fill=(169,132,114))
 cx,cy=P(0,-234+bob)
 d.ellipse((cx-23*s,cy-29*s,cx+23*s,cy+24*s),fill=(177,145,126),outline=(104,110,117),width=2)
 d.pieslice((cx-26*s,cy-30*s,cx+23*s,cy+7*s),180,343,fill=(26,28,35))
 ex=cx+(10 if face=='right' else -10)*s
 disk(d,ex,cy-5*s,max(1,round(2*s)),(17,18,27))
 line(d,cx+3*s,cy+12*s,cx+11*s,cy+12*s,fill=(113,81,79),width=1)
 return hand

def elevator(d,x=125,y=192,w=332,h=522,open_ratio=0.,panel=True,glow=False):
 # Stationary car and sliding doors in the same 3D perspective.
 d.rectangle((x-14,y-19,x+w+14,y+h+22),fill=(40,47,62),outline=(107,111,117),width=5)
 d.rectangle((x,y,x+w,y+h),fill=(17,24,35))
 for yy in range(y+25,y+h-20,75):line(d,x+27,yy,x+w-27,yy,fill=(34,48,61),width=2)
 r=sm(open_ratio);half=w//2;side=(half-6)*(1-r)
 if side>2:
  d.rectangle((x,y,x+side,y+h),fill=(77,83,94),outline=(139,144,151),width=3)
  d.rectangle((x+w-side,y,x+w,y+h),fill=(70,77,89),outline=(139,144,151),width=3)
  line(d,x+side-11,y+12,x+side-11,y+h-12,fill=(121,131,140),width=2)
  line(d,x+w-side+11,y+12,x+w-side+11,y+h-12,fill=(121,131,140),width=2)
 d.rectangle((x,y-29,x+w,y-3),fill=(32,43,55),outline=(103,113,123),width=2)
 if panel:
  box=(x+w+27,y+143,x+w+84,y+353)
  roundrect(d,box,(46,56,70),(111,119,132),5,3)
  for i,v in enumerate(('9','6','3','0')):
   py=y+173+i*46
   disk(d,x+w+56,py,17,(80,49,55) if (v=='0' and glow) else (36,43,55),RED if (v=='0' and glow) else (91,101,116),2)
   text(d,(x+w+56,py-10),v,18,RED if(v=='0' and glow)else WHITE,'ma')

def monitor(d,man=False,count=1,t=0):
 roundrect(d,(54,147,527,663),(9,15,26),(111,123,137),14,8)
 roundrect(d,(73,174,507,583),(23,32,46),(69,96,109),9,3)
 d.rectangle((102,218,478,550),fill=(36,40,48))
 d.rectangle((220,224,367,530),fill=(21,32,44),outline=(100,105,118),width=4)
 for y in range(238,535,36):line(d,104,y,476,y,fill=(43,48,58),width=1)
 if man:hero(d,299,517,.73,t,'stand',True)
 text(d,(98,185),'CAM 03  ● REC',18,RED)
 text(d,(444,185),'02:17',17,WHITE,'ra')
 text(d,(100,601),'ПАССАЖИРОВ',21,WHITE)
 roundrect(d,(357,595,486,650),(82,35,47) if count>1 else (34,55,65),RED if count>1 else CYAN,7,3)
 text(d,(422,600),f'{count:02d}',34,RED if count>1 else CYAN,'ma')

def staircase(d,t,hero_active=True,other=False):
 # hallway perspective, mechanical objects at different distances.
 d.polygon([(65,176),(516,176),(568,705),(0,705)],fill=(26,35,51),outline=(66,75,91))
 d.polygon([(214,222),(368,222),(425,653),(148,653)],fill=(20,28,42),outline=(82,90,101))
 for xx in (30,549):line(d,xx,170,xx,708,fill=(86,91,106),width=5)
 for yy in range(625,718,30):line(d,0,yy,576,yy,fill=(57,69,84),width=3)
 # electrical cables and emergency lamp
 line(d,144,233,144,704,fill=(111,113,117),width=5)
 roundrect(d,(126,299,167,359),(44,50,63),(114,122,131),4)
 disk(d,147,327,8,RED if int(t*3)%2 else (61,52,60))
 if hero_active:hero(d,154+38*sm(t/4) if other else 190,671,.87,t,'walk' if other else 'switch')

def panel(d,t,zero=False):
 d.rectangle((119,165,467,658),fill=(47,55,69),outline=(124,133,143),width=6)
 text(d,(291,185),'ПАНЕЛЬ УПРАВЛЕНИЯ',21,WHITE,'ma')
 for idx,(l,yy) in enumerate(zip(['9','8','7','6','5','4','3','2','1','−1'],range(231,641,40))):
  xx=214 if idx%2==0 else 344;yt=231+(idx//2)*74
  # use only 10 buttons aligned in five rows
  yv=231+(idx//2)*78
  rr=(xx-28,yv-22,xx+28,yv+22)
  roundrect(d,rr,(36,45,59),(100,110,125),8,3)
  text(d,(xx,yv-14),l,25,WHITE,'ma')
 if zero and t>1.1:
  roundrect(d,(251,630,322,697),(85,39,51),RED,9,4)
  text(d,(287,644),'0',39,RED,'ma')

def group_text(textstr):
 """Split sentence into safe caption cards at syntactic boundaries and 5 words."""
 out=[];block=[]
 for word in textstr.split():
  block.append(word)
  if len(block)>=5 or (len(block)>=3 and word.endswith(('.', '!', '?', '…', ':'))):
   out.append(' '.join(block));block=[]
 if block:out.append(' '.join(block))
 return out

def subtitles(d,scene,t,duration):
 phrases=group_text(scene['text'])
 active=max(.2,duration-.50)
 if t<.25 or t>duration-.14 or not phrases:return
 weights=[max(1,len(p.replace(' ',''))) for p in phrases]
 prog=clamp((t-.25)/active)*sum(weights)
 i=0;s=0
 for j,w in enumerate(weights):
  s+=w
  if prog<=s:i=j;break
 else:i=len(phrases)-1
 phrase=phrases[i];f=font(42)
 lines=['']
 for word in phrase.split():
  trial=(lines[-1]+' '+word).strip()
  if f.getlength(trial)>532 and lines[-1]:lines.append(word)
  else:lines[-1]=trial
 if len(lines)>2:
  size=36;f=font(size);lines=['']
  for word in phrase.split():
   trial=(lines[-1]+' '+word).strip()
   if f.getlength(trial)>534 and lines[-1]:lines.append(word)
   else:lines[-1]=trial
 else:size=42
 # no black box around captions; clean low-third panel with unobtrusive shaded base
 y=762 if len(lines)==2 else 805
 d.rectangle((0,745,576,1024),fill=(15,20,31))
 for j,s in enumerate(lines):
  col=YELLOW if any(x in s.lower() for x in ('ноль','два','второй','нулев','пассажир')) else WHITE
  text(d,(288,y+j*65),s,size,col,'ma',stroke=2)

def art(kind,t,duration,i,scene):
 im=backdrop().copy();d=ImageDraw.Draw(im);p=sm(t/max(duration,.1))
 # scene zone y=140..740; subtitles always below
 header(d,{'hook':'ЛИФТ № 3','building':'СХЕМА ЗДАНИЯ','technician':'ЛИФТЁРНАЯ','monitor':'КАМЕРА № 03',
 'corridor':'МАШИННОЕ ОТДЕЛЕНИЕ','door':'КАБИНА № 3','monitor2':'ЗАПИСЬ С КАМЕРЫ','split':'КТО В КАБИНЕ?',
 'breaker':'ЩИТОВАЯ','button':'ПАНЕЛЬ ЛИФТА','unseen':'НЕИЗВЕСТНЫЙ ЭТАЖ','photo':'КОРИДОР 00',
 'intercom':'ВЫЗОВ','count':'СЧЁТЧИК','ending':'ПОЗАДИ ТЕБЯ'}[kind],t)
 if kind=='hook':
  elevator(d,139,198,275,486,.02,False)
  text(d,(287,187),'00',66,RED,'ma')
  hero(d,80,663,.69,t,'point')
  alert(d,'НЕСУЩЕСТВУЮЩИЙ ЭТАЖ',53,113,469)
  disk(d,426,206,7,RED if int(t*5)%2 else (71,60,65))
 elif kind=='building':
  alert(d,'В ДОМЕ 9 ЭТАЖЕЙ',70,122,440)
  d.rectangle((128,240,451,691),fill=(33,43,58),outline=(105,117,135),width=4)
  for k in range(9):
   y=269+k*43
   line(d,145,y,437,y,fill=(68,80,101),width=2)
   text(d,(165,y+8),f'{9-k:02d}',22,GREY)
   d.rectangle((223,y+9,290,y+34),fill=(37,58,70))
  line(d,352,255,352,650,fill=(150,152,161),width=8)
  d.rectangle((147,661,432,707),fill=(62,32,45),outline=RED,width=3)
  text(d,(281,665),'00  НЕТ НА ПЛАНЕ',23,RED,'ma')
  disk(d,350,657,8,YELLOW)
 elif kind=='technician':
  staircase(d,t)
  panel_x=395
  roundrect(d,(340,250,499,461),(48,58,70),(113,124,133),6,4)
  text(d,(419,270),'ТОЛЬКО',16,GREY,'ma')
  text(d,(419,304),'1—9',34,WHITE,'ma')
  text(d,(419,359),'0',40,RED,'ma')
  line(d,365,391,471,391,fill=RED,width=3)
  text(d,(418,407),'ОТСУТСТВУЕТ',13,RED,'ma')
  hero(d,190,679,1.0,t,'point')
 elif kind=='monitor':
  monitor(d,False,1,t)
  for j in range(18):
   yy=182+(j*29+int(t*12))%395
   line(d,82,yy,498,yy,fill=(45,50,60),width=1)
 elif kind=='corridor':
  staircase(d,t,True,True)
  alert(d,'К ЩИТКУ',333,138,183)
  d.polygon([(467,380),(517,393),(472,410)],fill=YELLOW)
 elif kind=='door':
  elevator(d,140,175,283,518,0,False)
  for n in range(3):
   onset=n*.92+.2
   if 0<t-onset<.60:
    r=30+70*(t-onset)/.6
    d.ellipse((288-r,465-r*.25,288+r,465+r*.25),outline=RED if n==2 else CYAN,width=4)
  alert(d,'ТРИ УДАРА',142,119,288)
 elif kind=='monitor2':
  monitor(d,True,1,t)
  alert(d,'ЭТО Я?',192,134,194)
 elif kind=='split':
  # two deliberately distinct panels; no accidental collisions
  roundrect(d,(18,150,279,646),(35,43,58),(106,117,131),8,3)
  roundrect(d,(298,150,558,646),(22,42,49),(106,117,131),8,3)
  text(d,(146,170),'РЕАЛЬНОСТЬ',20,WHITE,'ma')
  text(d,(426,170),'КАМЕРА',20,WHITE,'ma')
  hero(d,146,573,.76,t,'switch')
  hero(d,424,573,.76,t+.9,'point',True)
  line(d,270,372,306,372,fill=RED,width=4)
  text(d,(288,396),'−2 сек.',16,RED,'ma')
 elif kind=='breaker':
  staircase(d,t,False)
  roundrect(d,(164,182,418,618),(43,53,69),(121,132,141),8,5)
  for j in range(5):
   yy=230+j*68
   d.rectangle((189,yy,390,yy+36),fill=(30,39,55),outline=(82,95,114),width=2)
   rectcolor=CYAN if j<4 and t<1.2 else RED if j==4 else (68,74,81)
   roundrect(d,(317,yy+4,363,yy+32),rectcolor,r=5)
  pos=sm(t/1.8)
  line(d,235,512,235-35*pos,565+20*pos,fill=YELLOW,width=12)
  text(d,(293,605),'ПИТАНИЕ: ВЫКЛ',21,RED,'ma')
  text(d,(287,680),'ЛИФТ ДВИЖЕТСЯ',24,YELLOW,'ma')
 elif kind=='button':
  panel(d,t,True)
  if t>1.1:
   for r in (43,72,102):
    if (t*1.3)%1 <.74:d.arc((287-r,667-r,287+r,667+r),190,350,fill=RED,width=2)
 elif kind=='unseen':
  elevator(d,131,191,315,529,p,False)
  # new corridor emerges through opening; continuous depth with doors
  opening=(315//2-6)*p
  if opening>8:d.rectangle((131+157-opening+6,220,131+157+opening-6,686),fill=(20,34,42))
  for j in range(5):
   y=267+j*75
   if opening>12:line(d,290-opening,y,290+opening,y,fill=(67,87,97),width=2)
  # re-draw mechanical door fronts over corridor near opening
  side=(157-6)*(1-sm(p))
  if side>2:
   d.rectangle((131,191,131+side,720),fill=(76,83,93),outline=(124,131,140),width=3)
   d.rectangle((446-side,191,446,720),fill=(74,82,95),outline=(124,131,140),width=3)
  text(d,(290,229),'00',45,RED,'ma')
 elif kind=='photo':
  d.rectangle((50,153,525,708),fill=(34,43,57))
  roundrect(d,(155,199,418,572),(78,69,63),(155,140,112),8,10)
  d.rectangle((177,223,394,546),fill=(87,105,99))
  # clear distinctive person, not random smear
  d.ellipse((257,268,333,352),fill=(186,150,133),outline=(116,110,104),width=2)
  d.pieslice((251,267,337,351),180,342,fill=(42,35,38))
  d.polygon([(231,490),(256,358),(338,358),(367,490)],fill=(45,80,75))
  disk(d,341,313,9,(234,154,72)) # orange hair clip
  text(d,(286,512),'ЛЕНА',24,WHITE,'ma')
  hero(d,98,713,.7,t,'point')
  text(d,(292,652),'ПРОПАЛА 6 МЕСЯЦЕВ НАЗАД',19,RED,'ma')
 elif kind=='intercom':
  roundrect(d,(150,171,435,621),(46,53,66),(117,128,141),16,8)
  text(d,(292,194),'ДИНАМИК',24,WHITE,'ma')
  for yy in range(280,487,34):
   for xx in range(195,409,35):disk(d,xx,yy,6,(19,27,40))
  disk(d,289,548,16,RED if int(t*3)%2 else (79,52,62))
  for j in range(3):
   rr=65+35*((t*.6+j/3)%1)
   d.arc((289-rr,401-rr,289+rr,401+rr),-50,50,fill=RED,width=3)
  alert(d,'НЕ ЗАХОДИ',138,117,302)
 elif kind=='count':
  monitor(d,False,2 if t>1.35 else 1,t)
  text(d,(287,665),'ОБНАРУЖЕН ВТОРОЙ',23,RED,'ma')
 elif kind=='ending':
  # spatial staging: person in foreground and a second set of doors behind him
  elevator(d,138,186,301,516,sm((t-1.2)/3),False)
  hero(d,275,690,1.06,t,'point')
  if t>3:
   alpha=sm((t-3)/1.7)
   xx=303;d.ellipse((xx-29*alpha,330,xx+29*alpha,410),fill=(9,11,18))
   d.polygon([(xx-37*alpha,414),(xx+35*alpha,414),(xx+46*alpha,577),(xx-42*alpha,577)],fill=(9,11,18))
  alert(d,'КТО-ТО УЖЕ ВНУТРИ',55,119,462)
 # stable atmospheric detail in scene region only
 rng=random.Random(411+i)
 for j in range(19):
  x=rng.randint(15,560);y=(rng.randint(130,740)+int(t*(j%3+1)))%740
  if y>134:d.ellipse((x,y,x+1,y+1),fill=(63,78,96))
 subtitles(d,scene,t,duration)
 fade=min(1,t/.18,(duration-t)/.17)
 if fade<1:
  black=Image.new('RGB',(W,H));im=Image.blend(black,im,max(0,fade))
 return im