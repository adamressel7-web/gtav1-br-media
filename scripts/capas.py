"""Reel 'Qual a capa mais lendária?' — capas oficiais da Rockstar."""
import subprocess, wave, os, hashlib, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
FPS, W, H = 30, 1080, 1920
PD = "/root/fonts/pricedown.ttf"; IX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"; IM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
F = lambda p, s: ImageFont.truetype(p, s)
C = "/root/capas/"
ITEMS = [("c0.jpg", "GTA III", "2001", "Um: GTA três, de dois mil e um."),
         ("c1.jpg", "VICE CITY", "2002", "Dois: Vice City, de dois mil e dois."),
         ("c2.jpg", "SAN ANDREAS", "2004", "Três: San Andreas, de dois mil e quatro."),
         ("c3.jpg", "GTA IV", "2008", "Quatro: GTA quatro, de dois mil e oito."),
         ("c4.png", "GTA V", "2013", "Cinco: GTA cinco, de dois mil e treze."),
         ("c5.png", "GTA VI", "2026", "E seis: GTA seis, que chega agora em dezenove de novembro.")]
COLS = [(255, 214, 0), (255, 64, 170), (60, 230, 140), (60, 200, 255), (255, 140, 40), (255, 64, 170)]
HOOK_SAY = "Qual é a capa mais lendária da história de GTA? Vai votando."
END_SAY = "Qual é a mais lendária? Comenta o número!"

def tts(text):
    h = hashlib.md5(text.encode()).hexdigest()[:10]; mp3 = f"/root/cards/vo/cp_{h}.mp3"; wv = mp3[:-4] + ".wav"
    if not os.path.exists(wv):
        subprocess.run(["edge-tts", "--voice", "pt-BR-AntonioNeural", "--rate=+12%", "--text", text, "--write-media", mp3], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "48000", wv], check=True)
    with wave.open(wv) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

COV = []; BGS = []
for f, *_ in ITEMS:
    im = Image.open(C + f).convert("RGB")
    big = im.resize((620, int(620 * im.height / im.width)), Image.LANCZOS)
    big = big.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    COV.append(big)
    s_ = max(W / im.width, H / im.height); bg = im.resize((int(im.width * s_) + 1, int(im.height * s_) + 1), Image.BILINEAR); bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(45))
    BGS.append(ImageEnhance.Brightness(bg).enhance(0.45))
VO = [tts(x[3]) for x in ITEMS]; VH_ = tts(HOOK_SAY); VE = tts(END_SAY)
HOOK = int(len(VH_) / 48000 * FPS) + 15
DUR = [int(len(a) / 48000 * FPS) + 18 for a in VO]
END = int(len(VE) / 48000 * FPS) + 40
STARTS = np.cumsum([HOOK] + DUR[:-1]); TOTAL = HOOK + sum(DUR) + END
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3

def ctext(d, y, t, f, fill, sw=7, sf=(15, 5, 25)):
    d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=fill, stroke_width=sw, stroke_fill=sf)

def card(fr, i, a, x=None, y=None, scale=1.0):
    c = COV[i]; s = scale * (0.85 + 0.15 * a)
    c2 = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    m = Image.new("L", c2.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, c2.width - 1, c2.height - 1), 18, fill=int(255 * a))
    sh = Image.new("RGBA", (c2.width + 60, c2.height + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((30, 30, 30 + c2.width, 30 + c2.height), 24, fill=(0, 0, 0, int(160 * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    x = (W - c2.width) // 2 if x is None else x; y = 620 if y is None else y
    fr.paste(sh, (x - 30, y - 20), sh); fr.paste(c2, (x, y), m)

def frame(n):
    if n < HOOK:
        fr = BGS[5].copy(); d = ImageDraw.Draw(fr)
        for j in range(6):  # grade de capas
            a = ease((n - j * 3) / 10)
            if a > 0: card(fr, j, a, 70 + (j % 3) * 320, 520 + (j // 3) * 420, 0.46)
        ctext(d, 170, "QUAL É A CAPA", F(PD, 120), "white"); ctext(d, 300, "MAIS LENDÁRIA?", F(PD, 120), (255, 214, 0))
    elif n < HOOK + sum(DUR):
        i = int(np.searchsorted(STARTS, n, side="right") - 1); k = n - STARTS[i]; a = ease(k / 9)
        fr = BGS[i].copy(); d = ImageDraw.Draw(fr)
        ctext(d, 260, str(i + 1), F(PD, int(200 * (1.2 - 0.2 * a))), COLS[i], 9)
        card(fr, i, a)
        y2 = 620 + COV[i].height + 50
        ctext(d, y2, ITEMS[i][1], F(PD, 110), "white"); ctext(d, y2 + 120, ITEMS[i][2], F(IX, 60), COLS[i], 5)
    else:
        e = n - HOOK - sum(DUR); fr = BGS[1].copy(); d = ImageDraw.Draw(fr)
        for j in range(6): card(fr, j, 1, 70 + (j % 3) * 320, 470 + (j // 3) * 420, 0.46)
        for j in range(6):
            x = 70 + (j % 3) * 320 + 143; y = 470 + (j // 3) * 420 - 20
            d.ellipse((x - 38, y - 38, x + 38, y + 38), fill=COLS[j], outline=(15, 5, 25), width=5)
            t = str(j + 1); f = F(PD, 64); d.text((x - d.textlength(t, font=f) / 2, y - 40), t, font=f, fill=(15, 5, 25))
        ctext(d, 170, "QUAL A MAIS", F(PD, 120), "white"); ctext(d, 300, "LENDÁRIA?", F(PD, 120), (255, 214, 0))
        if e > 8:
            t = "Comenta o número"; f = F(IX, 56); tw = d.textlength(t, font=f)
            d.rounded_rectangle(((W - tw) / 2 - 40, 1400, (W + tw) / 2 + 40, 1500), 50, fill=(255, 64, 170)); d.text(((W - tw) / 2, 1414), t, font=f, fill="white")
    d = ImageDraw.Draw(fr)
    ctext(d, 60, "GTA 6 BRASIL", F(PD, 56), "white", 4)
    cr = "Capas oficiais: Rockstar Games"; d.text(((W - d.textlength(cr, font=F(IM, 24))) / 2, H - 110), cr, font=F(IM, 24), fill=(225, 225, 235))
    return fr

def audio(path):
    sr = 48000; L = int(TOTAL / FPS * sr)
    with wave.open("/root/musica/m09_oldschool.wav") as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    m = np.tile(m, int(np.ceil(L / len(m))))[:L]; fade = np.ones(L); fl = int(1.2 * sr); fade[-fl:] = np.linspace(1, 0, fl)
    out = m * 0.25 * fade
    def put(a, f0):
        s = int(f0 / FPS * sr); e = min(L, s + len(a)); out[s:e] += a[:e - s] * 1.1
    put(VH_, 6)
    for a, s0 in zip(VO, STARTS): put(a, s0 + 6)
    put(VE, HOOK + sum(DUR) + 6)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

import sys
if len(sys.argv) > 1:
    ims = [frame(int(x)).resize((270, 480)) for x in sys.argv[1:]]
    o = Image.new("RGB", (270 * len(ims), 480))
    for j, im in enumerate(ims): o.paste(im, (j * 270, 0))
    o.save("/root/cards/cp_prev.jpg"); print(TOTAL); sys.exit()
audio("/root/cards/cp.wav")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "/root/cards/cp.wav",
                      "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-maxrate", "16M", "-bufsize", "32M", "-profile:v", "high",
                      "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", "/root/cards/CAPAS.mp4"], stdin=subprocess.PIPE)
for n in range(TOTAL): p.stdin.write(frame(n).convert("RGB").tobytes())
p.stdin.close(); p.wait(); print("ok", TOTAL)
