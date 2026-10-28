"""Create the master character reference sheet used to review consistent identities."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from characters import ORDER, CAST, portrait_card


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='output/zavtra_characters.png')
    args=parser.parse_args()
    W=1024;H=900
    img=Image.new('RGB',(W,H),(14,23,36))
    d=ImageDraw.Draw(img)
    bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    d.text((32,26),'ЗАВТРА НАС МЕНЬШЕ',font=ImageFont.truetype(bold,36),fill=(244,239,225))
    d.text((33,75),'СЕМЬ ПОСТОЯННЫХ ПЕРСОНАЖЕЙ',font=ImageFont.truetype(bold,19),fill=(167,184,195))
    xs=[23,279,535,791]
    for i,key in enumerate(ORDER):
        row,col=divmod(i,4)
        portrait_card(img,key,(xs[col],126+row*369,xs[col]+232,480+row*369),phase=1.1)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);img.save(out)
    print(out)

if __name__=='__main__':main()
