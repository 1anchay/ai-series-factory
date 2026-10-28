#!/usr/bin/env python3
"""Free cinematic shorts renderer with optional Piper narration and layered scene animation."""
from __future__ import annotations

from soundscape import create_soundtrack as enhanced_soundtrack

import argparse
import json
import math
import random
import re
import shutil
import subprocess
import tempfile
import urllib.request
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_BOLD = next((p for p in [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
    'C:/Windows/Fonts/arialbd.ttf'] if Path(p).exists()), None)
FONT_REG = next((p for p in [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
    'C:/Windows/Fonts/arial.ttf'] if Path(p).exists()), None)
FPS = 20
AUDIO_SR = 24000
HF_BASE = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/'


def font(size, bold=True):
    if FONT_BOLD and FONT_REG:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, max(10, int(size)))
    return ImageFont.load_default()


def tr(draw, xy, text, fnt, fill, anchor=None, stroke_width=0, stroke_fill=None):
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor,
              stroke_width=stroke_width, stroke_fill=stroke_fill)


def eased(x):
    x = max(0., min(1., x))
    return x * x * (3 - 2 * x)


def gradient(w, h, top=(7, 17, 37), bot=(28, 47, 62), seed=1):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    base = (np.asarray(top, dtype=np.float32)[None, None, :] * (1 - y)
            + np.asarray(bot, dtype=np.float32)[None, None, :] * y)
    arr = np.broadcast_to(base, (h, w, 3)).copy()
    r = np.random.default_rng(seed)
    arr += r.normal(0, 2.0, (h, w, 1)).astype(np.float32)
    return Image.fromarray(np.uint8(np.clip(arr, 0, 255)), 'RGB')


def glow(img, x, y, r, color, strength=130):
    r = int(max(2, r))
    region = (max(0, x-r*3), max(0, y-r*3), min(img.width, x+r*3), min(img.height, y+r*3))
    if region[2] <= region[0] or region[3] <= region[1]:
        return
    layer = Image.new('RGBA', (region[2]-region[0], region[3]-region[1]))
    d = ImageDraw.Draw(layer)
    cx, cy = x-region[0], y-region[1]
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=tuple(color)+(strength,))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.9))
    img.paste(layer, (region[0], region[1]), layer)


def skyscrapers(img, rng, w, h, horizon=.80):
    d = ImageDraw.Draw(img)
    baseline = int(h * horizon)
    x = -30
    while x < w + 20:
        bw = rng.randint(int(w * .075), int(w * .18))
        bh = rng.randint(int(h * .12), int(h * .35))
        y0 = baseline - bh
        color = rng.choice([(10,22,37),(12,25,40),(16,29,46),(8,18,31)])
        d.rectangle((x, y0, x+bw, baseline+70), fill=color)
        d.line((x+2, y0, x+bw-3, y0), fill=(43,62,81), width=2)
        for wy in range(y0+20, baseline-10, 23):
            for wx in range(x+9, x+bw-8, 16):
                if rng.random() < .21:
                    col = (27,75,88) if rng.random() < .82 else (132,72,46)
                    d.rectangle((wx,wy,wx+5,wy+9), fill=col)
        x += bw + rng.randint(2,10)


def tower(img, w, h, center=None, top=.09, bottom=.86, lit=True):
    d = ImageDraw.Draw(img)
    center = w*.55 if center is None else center
    left = int(center-w*.19); right = int(center+w*.19)
    yt = int(h*top); yb = int(h*bottom)
    d.polygon([(left,yt+45),(right-10,yt),(right,yb),(left-20,yb)], fill=(11,23,38))
    d.polygon([(right-12,yt),(right+18,yt+38),(right+35,yb),(right,yb)], fill=(19,35,51))
    for xx in range(left+14, right-15, 21):
        d.line((xx,yt+36,xx-12,yb), fill=(26,44,57), width=2)
    for yy in range(yt+56, yb-10, 24):
        d.line((left,yy,right+14,yy), fill=(32,46,62), width=2)
    x = int(left+(right-left)*.57); y = int(yt+(yb-yt)*.235)
    if lit:
        glow(img, x+9, y+14, int(w*.05), (245,180,74), 150)
        d = ImageDraw.Draw(img)
        d.rectangle((x,y,x+19,y+28), fill=(255,211,114))
        d.line((x+9,y,x+9,y+28), fill=(105,80,58), width=2)
    return x+9, y+14


def street_road(img, w, h):
    d = ImageDraw.Draw(img)
    y = int(h*.72)
    d.polygon([(0,y),(w,y),(w,int(h*.99)),(0,int(h*.99))], fill=(11,23,32))
    d.polygon([(int(w*.46),y),(int(w*.53),y),(w,h),(0,h)], fill=(17,31,41))
    for k in range(9):
        yy = y + int((h-y) * (k/9)**1.7)
        span = max(1, int((yy-y) * .014))
        d.line((w//2, yy, w//2, yy+span), fill=(98,100,92), width=2+span//7)
    d.line((0,y,w,h*.90), fill=(31,60,69), width=3)
    d.line((w,y,0,h*.94), fill=(31,60,69), width=3)


def draw_vera(img, cx, cy, scale=1., ominous=False):
    s = float(scale)
    d = ImageDraw.Draw(img)
    def pt(x,y): return (int(cx+x*s), int(cy+y*s))
    def poly(coords, col): d.polygon([pt(x,y) for x,y in coords], fill=col)
    poly([(-84,110),(75,105),(133,280),(-155,280)], (10,22,34))
    poly([(-85,100),(-38,68),(7,135),(-70,270)], (23,40,52))
    poly([(60,98),(23,85),(-3,138),(116,270)], (16,28,43))
    poly([(-27,58),(22,58),(28,111),(-34,111)], (142,109,96) if not ominous else (73,98,118))
    d.ellipse((pt(-52,-90),pt(49,76)), fill=(178,137,118) if not ominous else (95,118,133), outline=(48,42,49), width=max(1,int(2*s)))
    poly([(-57,-40),(-70,-108),(-13,-128),(46,-101),(58,-45),(32,-78),(2,-78),(-27,-65)], (13,20,29))
    poly([(-54,-65),(-65,27),(-46,69),(-38,12)], (10,17,25))
    poly([(48,-68),(57,25),(44,73),(35,3)], (9,17,26))
    e = (235,102,103) if ominous else (201,214,211)
    for ex in (-22,20):
        d.ellipse((pt(ex-9,-4),pt(ex+9,4)), fill=e)
        d.ellipse((pt(ex-3,-3),pt(ex+3,4)), fill=(11,14,24))
    d.line((pt(-4,20),pt(-8,33)), fill=(104,76,73), width=max(1,int(2*s)))
    d.arc((pt(-15,35),pt(20,57 if ominous else 43)), 0, 180, fill=(72,27,39) if ominous else (85,56,55), width=max(2,int(3*s)))
    poly([(-67,75),(32,83),(67,122),(-61,127)], (146,39,52))
    poly([(32,103),(64,117),(31,247),(-3,212)], (174,43,58))
    d.line((pt(-35,103),pt(45,111)), fill=(236,87,85), width=max(2,int(3*s)))


def draw_phone(img, w, h):
    d = ImageDraw.Draw(img)
    d.polygon([(w*.12,h*.88),(w*.29,h*.58),(w*.43,h*.62),(w*.48,h),(w*.12,h)], fill=(116,87,80))
    x0,y0,x1,y1 = int(w*.27),int(h*.22),int(w*.77),int(h*.79)
    glow(img,(x0+x1)//2,(y0+y1)//2,int(w*.23),(20,160,173),95)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0,y0,x1,y1), radius=38, fill=(13,17,24), outline=(67,80,86), width=8)
    d.rounded_rectangle((x0+22,y0+25,x1-22,y1-27), radius=15, fill=(18,44,55))
    tr(d,(x0+43,y0+67),'03:17',font(w*.042,False),(153,223,227))
    tr(d,(x0+42,y0+190),'НЕ СМОТРИ',font(w*.048),(252,102,105))
    tr(d,(x0+42,y0+242),'ВВЕРХ',font(w*.076),(255,115,118))
    d.ellipse((x1-75,y1-78,x1-57,y1-60), fill=(118,213,208))


def make_art(kind, w, h, seed):
    rng = random.Random(seed)
    im = gradient(w, h, seed=seed)
    d = ImageDraw.Draw(im)
    if kind == 'city':
        glow(im, int(w*.29), int(h*.16), int(w*.17), (70,122,164), 60)
        skyscrapers(im, rng, w, h, .83)
        tower(im, w, h, center=w*.54, top=.08, bottom=.96)
        d.line((0,h*.76,w,h*.72), fill=(35,49,66), width=8)
        d.line((int(w*.12),0,int(w*.16),h), fill=(26,36,48), width=5)
    elif kind == 'street':
        skyscrapers(im, rng, w, h, .76)
        tower(im, w, h, center=w*.71, top=.06, bottom=.78)
        street_road(im, w, h)
        glow(im, int(w*.82), int(h*.65), int(w*.05), (196,40,55), 140)
        d.rectangle((int(w*.81),int(h*.54),int(w*.84),int(h*.66)), fill=(28,32,38))
        d.ellipse((int(w*.807),int(h*.535),int(w*.849),int(h*.562)), fill=(244,63,68))
        draw_vera(im, w*.39, h*.67, scale=1.45)
    elif kind == 'phone':
        skyscrapers(im, rng, w, h, .83)
        street_road(im, w, h)
        draw_phone(im, w, h)
    elif kind == 'look_up':
        d.polygon([(0,h),(0,0),(w*.29,h*.08),(w*.51,h)], fill=(12,25,40))
        d.polygon([(w*.52,h),(w*.68,0),(w,0),(w,h)], fill=(14,28,42))
        for i in range(20):
            yy = i*h/19
            d.line((0,yy,w*.33,yy+int(h*.08)), fill=(43,60,75), width=4)
            d.line((w*.66,yy-int(h*.06),w,yy), fill=(42,59,72), width=4)
        tower(im, w, h, center=w*.51, top=0, bottom=.90)
        draw_vera(im, w*.50, h*.83, 1.85)
    elif kind == 'window':
        d.rectangle((0,0,w,h), fill=(13,27,43))
        for x in range(20,w,90):
            d.line((x,0,x,h), fill=(43,55,65), width=7)
        for y in range(30,h,115):
            d.line((0,y,w,y), fill=(43,55,65), width=7)
        box=(int(w*.18),int(h*.24),int(w*.83),int(h*.75))
        glow(im, int(w*.50), int(h*.50), int(w*.25), (210,155,78), 165)
        d.rectangle(box, fill=(184,134,76), outline=(58,58,66), width=14)
        d.rectangle((box[0]+18,box[1]+18,box[2]-18,box[3]-18), fill=(101,80,62))
        draw_vera(im, w*.50, h*.52, 1.52, ominous=True)
        d.line((w*.5,box[1],w*.5,box[3]), fill=(35,38,48), width=10)
        d.line((box[0],h*.5,box[2],h*.5), fill=(35,38,48), width=9)
    elif kind == 'double':
        glow(im, int(w*.70), int(h*.44), int(w*.21), (168,32,57), 75)
        d.polygon([(int(w*.50),0),(w,0),(w,h),(int(w*.50),h)], fill=(39,30,48))
        draw_vera(im, w*.31, h*.47, 1.4)
        draw_vera(im, w*.74, h*.47, 1.4, ominous=True)
        d.line((w*.50,0,w*.50,h), fill=(125,159,183), width=7)
    else:
        skyscrapers(im, rng, w, h, .82)
    if kind in ('city','street','look_up'):
        fog = Image.new('RGBA',(w,h),(0,0,0,0))
        fd = ImageDraw.Draw(fog,'RGBA')
        for k in range(22):
            yy = int(h*(.55+k*.017))
            alpha = int(17*math.exp(-((k-9)/10)**2))
            fd.line((0,yy,w,yy+2), fill=(91,128,148,alpha), width=3)
        fog = fog.filter(ImageFilter.GaussianBlur(max(2,w//85)))
        im = Image.alpha_composite(im.convert('RGBA'), fog).convert('RGB')
    overlay = Image.new('RGBA',(w,h))
    ImageDraw.Draw(overlay).rectangle((0,0,w,8), fill=(80,175,196,75))
    im = Image.alpha_composite(im.convert('RGBA'), overlay).convert('RGB')
    return im


def cover_rgba(im, target_w, target_h, scale=1.0):
    im = im.convert('RGBA')
    ratio = max(target_w / im.width, target_h / im.height) * scale
    nw = max(1, math.ceil(im.width * ratio))
    nh = max(1, math.ceil(im.height * ratio))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def crop_shift(im, canvas_w, canvas_h, x_shift=0., y_shift=0.):
    W, H = im.size
    x = int((W - canvas_w) * (.5 + x_shift))
    y = int((H - canvas_h) * (.5 + y_shift))
    x = max(0, min(W-canvas_w, x))
    y = max(0, min(H-canvas_h, y))
    return im.crop((x, y, x + canvas_w, y + canvas_h))


def scene_paths(ep_num, scene_id):
    ep = f'{ep_num:03d}'
    return ROOT/'assets'/ep/(scene_id+'.png'), ROOT/'assets'/ep/scene_id


def load_scene_asset(ep_num, scene, w, h, seed):
    flat_path, layer_dir = scene_paths(ep_num, scene['id'])
    if layer_dir.exists() and layer_dir.is_dir():
        name_map = {
            'bg': ['bg.png', 'background.png'],
            'mg': ['mg.png', 'mid.png', 'midground.png'],
            'char': ['char.png', 'character.png', 'subject.png'],
            'fg': ['fg.png', 'foreground.png'],
        }
        layers = []
        for key, names in name_map.items():
            for name in names:
                p = layer_dir / name
                if p.exists():
                    layers.append((key, Image.open(p).convert('RGBA')))
                    break
        if layers:
            return {'mode': 'layers', 'layers': layers}
    for candidate in (flat_path, flat_path.with_suffix('.jpg'), flat_path.with_suffix('.jpeg'), flat_path.with_suffix('.webp')):
        if candidate.exists():
            return {'mode': 'flat', 'image': cover_rgba(Image.open(candidate).convert('RGB'), w, h)}
    return {'mode': 'flat', 'image': cover_rgba(make_art(scene.get('art','city'), w, h, seed), w, h)}


def scene_frame(asset, t, duration, scene, num, series, resolution):
    w, h = resolution, round(resolution * 16 / 9)
    prog = eased(t / max(.1, duration))
    paths = {1:(-.22,.07,.18,-.14),2:(.19,.04,-.14,-.12),3:(-.06,.06,.05,-.04),
             4:(.07,.20,-.04,-.24),5:(-.08,.04,.06,-.04),6:(-.08,-.01,.09,.01)}
    dx0, dy0, dx1, dy1 = paths.get(num, (0,0,0,0))
    xx = (dx0 + (dx1-dx0) * prog)
    yy = (dy0 + (dy1-dy0) * prog)
    base_zoom = 1.085 - (0.08 * prog if num in (3,5,6) else 0.04 * prog)

    if asset['mode'] == 'flat':
        src = asset['image']
        crop_w = min(src.width, int(w * base_zoom))
        crop_h = min(src.height, int(h * base_zoom))
        frame_img = crop_shift(src, crop_w, crop_h, xx, yy).resize((w, h), Image.Resampling.BICUBIC).convert('RGBA')
    else:
        frame_img = Image.new('RGBA', (w, h), (0,0,0,255))
        parallax = {'bg': .25, 'mg': .55, 'char': .90, 'fg': 1.20}
        extra_scale = {'bg': 1.08, 'mg': 1.12, 'char': 1.17, 'fg': 1.25}
        order = {'bg':0, 'mg':1, 'char':2, 'fg':3}
        for key, layer in sorted(asset['layers'], key=lambda kv: order.get(kv[0], 9)):
            scale = extra_scale.get(key, 1.1)
            oversize = cover_rgba(layer, w, h, scale=scale)
            layer_prog_x = xx * parallax.get(key, .5)
            layer_prog_y = yy * parallax.get(key, .5)
            frame_layer = crop_shift(oversize, w, h, layer_prog_x, layer_prog_y)
            if key == 'char':
                # subtle breathing / alive motion
                breath = 1 + .006 * math.sin(t * 2.7)
                nw = max(1, int(frame_layer.width * breath))
                nh = max(1, int(frame_layer.height * breath))
                resized = frame_layer.resize((nw, nh), Image.Resampling.BICUBIC)
                frame_layer = crop_shift(resized, w, h, 0, -.01)
            frame_img = Image.alpha_composite(frame_img, frame_layer)

    d = ImageDraw.Draw(frame_img, 'RGBA')
    rng = random.Random(1000 + num)
    for _ in range(165):
        rx = rng.randrange(w+160)-80
        ry = rng.randrange(h+130)-65
        speed = rng.randrange(250,450)
        ry = int((ry + speed*t) % (h+140)) - 70
        d.line((rx,ry,rx+rng.randint(5,14),ry+rng.randint(15,38)), fill=(148,194,222,rng.randint(32,89)), width=1)
    rng = random.Random(8888 + num)
    for _ in range(18):
        rx = rng.randrange(w+130)-60
        ry = int((rng.randrange(h+150) + 670*t) % (h+150)) - 75
        d.line((rx,ry,rx+15,ry+68), fill=(188,225,240,48), width=2)
    mist = Image.new('RGBA', (w, h), (0,0,0,0))
    md = ImageDraw.Draw(mist, 'RGBA')
    for band in range(9):
        yy2 = int(h * (.58 + band*.04) + math.sin((t+band)*.6)*3)
        md.rectangle((0, yy2, w, yy2 + 18), fill=(71, 104, 122, max(0, 16-band)))
    frame_img = Image.alpha_composite(frame_img, mist)
    d = ImageDraw.Draw(frame_img, 'RGBA')
    for j in range(18):
        a = max(0, 24-j)
        d.rectangle((j*2,j*3,w-j*2-1,h-j*3-1), outline=(0,4,13,a), width=3)
    for yy3 in range(int(h*.69), h, 3):
        a = int(174 * (yy3-h*.69) / (h*.31))
        d.rectangle((0,yy3,w,yy3+3), fill=(0,4,12,a))
    tr(d,(int(w*.065),int(h*.045)),series,font(w*.039),(226,234,236,220))
    tr(d,(int(w*.94),int(h*.05)),f'{num:02d}/06',font(w*.025,False),(180,199,206,205),anchor='ra')
    lines = wrap_text(scene['subtitle'], font(w*.054), w*.86)
    sy = int(h*.78)
    for line in lines:
        tr(d,(w//2,sy),line,font(w*.054),(251,247,237,255),anchor='mt',stroke_width=2,stroke_fill=(4,12,20,220))
        sy += int(w*.075)
    if num == 1 and t < 2.7:
        alpha = round(255 * min(1, t/.65, (2.7-t)/.6))
        if alpha > 0:
            tr(d,(w//2,int(h*.26)),series,font(w*.085),(245,248,250,alpha),anchor='mm',stroke_width=2,stroke_fill=(10,15,22,alpha))
            tr(d,(w//2,int(h*.315)),'СЕРИЯ 01',font(w*.033,False),(244,118,120,alpha),anchor='mm')
    if num == 6 and t > duration-2.3:
        alpha = int(245 * min(1, (t-(duration-2.3))/.5))
        tr(d,(w//2,int(h*.26)),'ПРОДОЛЖЕНИЕ СЛЕДУЕТ',font(w*.039),(255,231,222,alpha),anchor='mm')
    fade = min(1, t/.27, (duration-t)/.35)
    if fade < 1:
        d.rectangle((0,0,w,h), fill=(0,0,0,int(255*(1-max(0,fade)))))
    return frame_img.convert('RGB')


def wrap_text(txt, fnt, maxw):
    words = txt.split(); lines = []; line = ''
    for word in words:
        trial = (line + ' ' + word).strip()
        if fnt.getlength(trial) > maxw and line:
            lines.append(line); line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines[:4]


def download_model(target):
    """Fetch one of the free Russian Piper voices; cached between runs if available."""
    import os
    selected = os.environ.get('SERIES_NARRATOR', 'irina').strip().lower()
    if selected not in ('irina', 'dmitri', 'denis', 'ruslan'):
        raise ValueError('SERIES_NARRATOR must be irina, dmitri, denis or ruslan')
    target.mkdir(parents=True, exist_ok=True)
    name = f'ru_RU-{selected}-medium.onnx'
    base = f'https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/{selected}/medium/'
    for filename in (name, name + '.json'):
        path = target / filename
        if path.exists() and path.stat().st_size > (10000000 if filename.endswith('.onnx') else 200):
            continue
        print('Downloading voice model:', filename, flush=True)
        tmp = path.with_suffix(path.suffix+'.download')
        request = urllib.request.Request(base + filename + '?download=true',
                                         headers={'User-Agent':'AI-Series-Factory/1.0'})
        try:
            with urllib.request.urlopen(request, timeout=150) as source, tmp.open('wb') as f:
                shutil.copyfileobj(source, f)
            if tmp.stat().st_size < (10000000 if filename.endswith('.onnx') else 200):
                raise RuntimeError(f'Voice model download incomplete: {filename}')
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)
    return target/name


def read_wav(path):
    with wave.open(str(path), 'rb') as f:
        channels = f.getnchannels(); sr = f.getframerate(); width = f.getsampwidth()
        data = f.readframes(f.getnframes())
    if width != 2:
        raise RuntimeError('Unsupported WAV width')
    audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    if sr != AUDIO_SR:
        old = np.arange(len(audio)) / sr
        new = np.arange(round(len(audio)*AUDIO_SR/sr)) / AUDIO_SR
        audio = np.interp(new, old, audio).astype(np.float32)
    return audio


def split_sentences(text):
    parts = [x.strip() for x in re.split(r'(?<=[.!?…])\s+', text.strip()) if x.strip()]
    return parts or [text.strip()]


def compress_voice(x):
    if len(x) == 0:
        return x
    x = x.astype(np.float32)
    peak = max(1e-5, float(np.max(np.abs(x))))
    x = x / peak
    hp = np.empty_like(x)
    hp[0] = x[0]
    hp[1:] = x[1:] - 0.94 * x[:-1]
    x = 0.82 * x + 0.18 * hp
    env = np.abs(x)
    gain = np.where(env > 0.45, 0.45 / np.maximum(env, 1e-4), 1.0)
    x = x * gain
    x = np.tanh(x * 1.04)
    x *= 0.81
    return x.astype(np.float32)


def synth_voices(scenes, tmp, no_tts):
    if no_tts:
        print('Narration skipped (--no-tts).', flush=True)
        return [np.zeros(0, dtype=np.float32) for _ in scenes]
    model = download_model(ROOT/'voices')
    voices = []
    for i, scene in enumerate(scenes):
        parts = split_sentences(scene['narration'])
        chunks = []
        for j, part in enumerate(parts):
            dest = tmp / f'voice_{i:02d}_{j:02d}.wav'
            cmd = ['piper', '--model', str(model), '--output_file', str(dest)]
            run = subprocess.run(cmd, input=part + '\n', text=True, capture_output=True, timeout=120)
            if run.returncode != 0 or not dest.exists():
                raise RuntimeError(f'Piper TTS failed on scene {i+1}: {run.stderr[-1500:]}')
            wav = compress_voice(read_wav(dest))
            chunks.append(wav)
            if j < len(parts) - 1:
                pause = np.zeros(int(AUDIO_SR * min(.24, .10 + len(part.split()) * .012)), dtype=np.float32)
                chunks.append(pause)
        final = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
        voices.append(final)
        print(f'Voice {i+1}: {len(final)/AUDIO_SR:.1f}s', flush=True)
    return voices


def tone(frequency, seconds, volume, sr=AUDIO_SR, decay=2.6):
    tt = np.arange(max(1, int(sr*seconds)), dtype=np.float32) / sr
    phase = 2*np.pi*(frequency*tt + .12*np.sin(2*np.pi*3.1*tt))
    return (volume*np.sin(phase)*np.exp(-decay*tt)).astype(np.float32)


def noise_hit(seconds=1.2, volume=.1, sr=AUDIO_SR, seed=123):
    tt = np.arange(int(seconds*sr), dtype=np.float32) / sr
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal(len(tt)).astype(np.float32)
    return raw * (volume*np.exp(-5*tt)).astype(np.float32)


def create_soundtrack(scenes, voices, lengths, tmp):
    sr = AUDIO_SR
    total = round(sum(lengths)*sr)
    t = np.arange(total, dtype=np.float32) / sr
    rng = np.random.default_rng(2026)
    drone = (.028*np.sin(2*np.pi*(51*t + .45*np.sin(2*np.pi*.075*t)))
             + .014*np.sin(2*np.pi*(78*t + .35*np.sin(2*np.pi*.051*t))))
    soundtrack = np.column_stack((drone, drone)).astype(np.float32)
    for ch in (0,1):
        raw = rng.standard_normal(total).astype(np.float32)
        smooth = np.empty(total, dtype=np.float32)
        smooth[0] = raw[0]
        smooth[1:] = raw[1:] - .84*raw[:-1]
        soundtrack[:,ch] += .015*smooth*(.75+.25*np.sin(2*np.pi*(.13+.025*ch)*t))

    def add_mono(sound, sec, gain=.5, pan=0.):
        start = max(0, int(sec*sr))
        length = min(len(sound), total-start)
        if length <= 0:
            return
        l = math.sqrt((1-pan)/2)
        r = math.sqrt((1+pan)/2)
        soundtrack[start:start+length,0] += sound[:length] * gain * l
        soundtrack[start:start+length,1] += sound[:length] * gain * r

    pos = 0.
    for i, (scene, length, voice) in enumerate(zip(scenes, lengths, voices)):
        art = scene.get('art','')
        add_mono(tone(65,.8,.22), pos, 1, (-.5 if i % 2 else .45))
        if art == 'city':
            add_mono(noise_hit(1.8,.18,seed=10+i), pos+.22, .64, -.65)
            add_mono(tone(43,2.1,.24,decay=1.15), pos+.9, .8, -.2)
        elif art == 'street':
            for k in range(3):
                add_mono(noise_hit(.16,.095,seed=100+i*10+k), pos+1.2+k*.78, .85, -.52+k*.35)
        elif art == 'phone':
            for k in range(2):
                add_mono(tone(850,.18,.20,decay=10.5), pos+.65+k*.31, .85, .7)
                add_mono(tone(1140,.12,.10,decay=13.), pos+.74+k*.31, .7, .7)
        elif art == 'look_up':
            add_mono(tone(38,2.8,.28,decay=.48), pos+.9, .9, -.4)
        elif art == 'window':
            add_mono(tone(115,1.9,.17,decay=1.), pos+1.3, .95, .6)
            add_mono(tone(56,1.3,.21,decay=2.3), pos+2.0, .85, -.25)
        elif art == 'double':
            add_mono(noise_hit(.42,.32,seed=999), pos+1.6, .9, 0)
            add_mono(tone(41,2.0,.31,decay=.55), pos+1.8, .95, 0)
        if len(voice):
            offset = pos + .55
            start = int(offset * sr)
            l = min(len(voice), total - start)
            if l > 0:
                snd = voice[:l]
                env = np.minimum(1, np.arange(l)/max(1,sr*.09)) * np.minimum(1, (l-np.arange(l))/max(1,sr*.18))
                snd = snd * env
                soundtrack[start:start+l,:] *= .55
                soundtrack[start:start+l,0] += snd * .82
                soundtrack[start:start+l,1] += snd * .82
        pos += length
    fade = min(sr, total//8)
    soundtrack[:fade,:] *= np.linspace(0,1,fade,dtype=np.float32)[:,None]
    soundtrack[-fade:,:] *= np.linspace(1,0,fade,dtype=np.float32)[:,None]
    soundtrack = np.tanh(soundtrack * 1.02)
    dest = tmp / 'soundtrack.wav'
    with wave.open(str(dest), 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes(np.int16(np.clip(soundtrack, -1, 1) * 32767).tobytes())
    return dest


def render(episode_file, output, resolution, no_tts, fps):
    if not shutil.which('ffmpeg'):
        raise RuntimeError('ffmpeg is not installed')
    episode = json.loads(Path(episode_file).read_text(encoding='utf-8'))
    scenes = episode['scenes']
    if not (1 <= len(scenes) <= 20):
        raise ValueError('Expected 1-20 scenes')
    w, h = resolution, round(resolution * 16 / 9)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='series_') as tmpd:
        tmp = Path(tmpd)
        voices = synth_voices(scenes, tmp, no_tts)
        lengths = []
        for scene, voice in zip(scenes, voices):
            nominal = float(scene.get('seconds', 5))
            lengths.append(max(nominal, math.ceil((len(voice)/AUDIO_SR + 1.15) * fps) / fps))
        sound = enhanced_soundtrack(scenes, voices, lengths, tmp)
        cmd = ['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo',
               '-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','pipe:0',
               '-i',str(sound),'-map','0:v:0','-map','1:a:0','-c:v','libx264',
               '-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-c:a','aac',
               '-b:a','160k','-movflags','+faststart','-shortest',str(output)]
        print(f'Rendering {len(scenes)} scenes, {sum(lengths):.1f}s, {w}x{h}, {fps} fps', flush=True)
        with (tmp/'ffmpeg.log').open('wb') as logfile:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=logfile)
            try:
                for i, (scene, duration) in enumerate(zip(scenes, lengths), 1):
                    frames = round(duration * fps)
                    seed = 2026 + i * 149
                    asset = load_scene_asset(int(episode['episode']), scene, int(w * 1.32), int(h * 1.32), seed)
                    for j in range(frames):
                        img = scene_frame(asset, j/fps, duration, scene, i, episode['series'], w)
                        proc.stdin.write(img.tobytes())
                    print(f'  shot {i}/{len(scenes)}: {scene["id"]} done', flush=True)
            except Exception:
                proc.stdin.close(); proc.wait()
                raise
            else:
                proc.stdin.close(); rc = proc.wait()
            if rc:
                raise RuntimeError('ffmpeg failed:\n' + (tmp/'ffmpeg.log').read_text()[-2500:])
    print(f'✅ Created: {output} ({output.stat().st_size/1024/1024:.1f} MiB)', flush=True)


def main():
    p = argparse.ArgumentParser(description='Free cinematic shorts creator with layered scene support')
    p.add_argument('--episode', default='episodes/001.json')
    p.add_argument('--output', default='output/episode_001.mp4')
    p.add_argument('--resolution', type=int, default=720)
    p.add_argument('--fps', type=int, default=FPS)
    p.add_argument('--no-tts', action='store_true')
    args = p.parse_args()
    render(args.episode, args.output, args.resolution, args.no_tts, args.fps)


if __name__ == '__main__':
    main()
