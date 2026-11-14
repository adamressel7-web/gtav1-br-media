import subprocess, numpy as np, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FPS = 30
W, H = 1080, 1920
TOP, SQ = 560, 1080
YEL = (255, 214, 0); PINK = (255, 64, 160); GREEN = (60, 230, 120)
AN = "/root/rg/build/Anton.ttf"
PB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
PM = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
F = lambda p, s: ImageFont.truetype(p, s)

ROUNDS = [  # (arquivo, foco x 0..1, é_real, legenda resposta, crédito)
    ("/root/rg/real/r16.jpg", 0.42, True, "OCEAN DRIVE, MIAMI", "Foto: P. Hughes / Wikimedia Commons (CC BY 4.0)"),
    ("/root/rg/hi/1110.png", 0.55, False, "PRAIA DE VICE CITY", "Gameplay oficial: Rockstar Games"),
    ("/root/rg/real/r4.jpg", 0.40, True, "MIAMI À NOITE", "Foto: Gabriel Kaplan / Wikimedia Commons (CC BY 3.0)"),
    ("/root/rg/hi/1546.png", 0.45, False, "VICE CITY À NOITE", "Gameplay oficial: Rockstar Games"),
    ("/root/rg/hi/1570.png", 0.55, False, "PÔR DO SOL EM VICE CITY", "Gameplay oficial: Rockstar Games"),
]
HOOK, GUESS, REVEAL, END = 75, 105, 66, 111
RD = GUESS + REVEAL
TOTAL = HOOK + len(ROUNDS) * RD + END

def square(path, fx):
    im = Image.open(path).convert("RGB")
    w, h = im.size; s = min(w, h)
    x = int(max(0, min(w - s, fx * w - s / 2)))
    return im.crop((x, (h - s) // 2, x + s, (h - s) // 2 + s)).resize((1240, 1240), Image.LANCZOS)

IMGS = [square(r[0], r[1]) for r in ROUNDS]

def ctext(d, y, txt, font, fill=(255, 255, 255), stroke=0):
    w = d.textlength(txt, font=font)
    d.text(((W - w) / 2, y), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))

def ctext_multi(d, y, parts, font):  # parts: [(txt,color)]
    tot = sum(d.textlength(t, font=font) for t, _ in parts); x = (W - tot) / 2
    for t, c in parts:
        d.text((x, y), t, font=font, fill=c); x += d.textlength(t, font=font)

def header(d):
    f = F(AN, 26); tag = "GTA 6 BRASIL"; tw = d.textlength(tag, font=f)
    hw = F(PB, 30); hh = "@gtav1.br"; hwid = d.textlength(hh, font=hw)
    x0 = (W - (tw + 24 + 14 + hwid)) / 2
    d.rounded_rectangle((x0, 66, x0 + tw + 24, 108), 8, fill=YEL)
    d.text((x0 + 12, 70), tag, font=f, fill=(0, 0, 0))
    d.text((x0 + tw + 38, 68), hh, font=hw, fill=(255, 255, 255))

def paste_img(fr, img, t, dark=0.0, blur=0):
    z = 1240 - int(160 * t)  # zoom lento
    o = (1240 - z) // 2
    im = img.crop((o, o, o + z, o + z)).resize((SQ, SQ), Image.BILINEAR)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    if dark: im = ImageEnhance.Brightness(im).enhance(1 - dark)
    fr.paste(im, (0, TOP))

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def frame(n):
    fr = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(fr)
    if n < HOOK:
        paste_img(fr, IMGS[0], n / HOOK, dark=0.35, blur=6)
        d = ImageDraw.Draw(fr); header(d)
        a = ease(n / 10)
        sz = int(118 * (1.3 - 0.3 * a))
        ctext_multi(d, 170, [("REAL OU ", (255, 255, 255)), ("GTA 6", YEL), ("?", (255, 255, 255))], F(AN, sz))
        if n > 12: ctext(d, 330, "5 imagens. Quantas você acerta?", F(PB, 42), (230, 230, 230))
        if n > 22: ctext(d, 400, "Responde antes do tempo acabar", F(PM, 34), (170, 170, 170))
        return fr
    n2 = n - HOOK
    if n2 < len(ROUNDS) * RD:
        i, k = divmod(n2, RD); real, ans, cred = ROUNDS[i][2], ROUNDS[i][3], ROUNDS[i][4]
        paste_img(fr, IMGS[i], k / RD)
        d = ImageDraw.Draw(fr); header(d)
        if k < GUESS:
            if k < 6:  # flash de entrada
                ov = Image.new("RGB", (SQ, SQ), (255, 255, 255))
                fr.paste(Image.blend(fr.crop((0, TOP, W, TOP + SQ)), ov, 0.5 * (1 - k / 6)), (0, TOP)); d = ImageDraw.Draw(fr)
            ctext_multi(d, 140, [(f"Nº {i+1}", YEL), ("/5", (255, 255, 255))], F(AN, 56))
            ctext_multi(d, 215, [("REAL OU ", (255, 255, 255)), ("GTA 6", YEL), ("?", (255, 255, 255))], F(AN, 96))
            sec = 3 - min(2, (k - 15) // 30) if k >= 15 else 3
            p = ((k - 15) % 30) / 30 if k >= 15 else 0
            ctext(d, 345, str(sec), F(AN, int(130 - 30 * ease(p))), YEL if sec > 1 else PINK)
            # barra de tempo
            bw = int(900 * max(0, 1 - max(0, k - 15) / 90))
            d.rounded_rectangle((90, 515, 90 + bw, 527), 6, fill=YEL)
            ctext(d, TOP + SQ + 40, "Responde de cabeça!", F(PB, 36), (200, 200, 200))
        else:
            r = k - GUESS; a = ease(r / 8)
            if r < 5:
                ov = Image.new("RGB", (SQ, SQ), (255, 255, 255))
                fr.paste(Image.blend(fr.crop((0, TOP, W, TOP + SQ)), ov, 0.6 * (1 - r / 5)), (0, TOP)); d = ImageDraw.Draw(fr)
            col = GREEN if real else PINK
            lab = "É REAL!" if real else "É GTA 6!"
            ctext_multi(d, 140, [(f"Nº {i+1}", YEL), ("/5", (255, 255, 255))], F(AN, 56))
            ctext(d, 215, lab, F(AN, int(150 * (1.4 - 0.4 * a))), col)
            ctext(d, 410, ans, F(PB, 44), (255, 255, 255))
            # selo sobre a imagem
            sw = F(AN, 64); st = "FOTO REAL" if real else "JOGO"
            tw = d.textlength(st, font=sw)
            d.rounded_rectangle((W / 2 - tw / 2 - 28, TOP + 30, W / 2 + tw / 2 + 28, TOP + 125), 14, fill=col)
            d.text((W / 2 - tw / 2, TOP + 38), st, font=sw, fill=(0, 0, 0))
            ctext(d, TOP + SQ + 40, cred, F(PM, 26), (170, 170, 170))
        return fr
    e = n - HOOK - len(ROUNDS) * RD
    paste_img(fr, IMGS[-1], 1.0, dark=0.45, blur=4)
    d = ImageDraw.Draw(fr); header(d); a = ease(e / 10)
    ctext(d, 150, "QUANTAS VOCÊ", F(AN, int(104 * (1.4 - 0.4 * a))))
    ctext(d, 270, "ACERTOU?", F(AN, int(104 * (1.4 - 0.4 * a))), YEL)
    if e > 10: ctext(d, 420, "Comenta de 0 a 5", F(PB, 46))
    if e > 20: ctext(d, TOP + 470, "Respostas: REAL, GTA, REAL, GTA, GTA", F(PB, 34), (230, 230, 230))
    return fr

def audio(path):
    sr = 48000
    with wave.open("/root/rg/build/music.wav") as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    N = int(TOTAL / FPS * sr); out = np.zeros(N, np.float32); out[:min(N, len(m))] = m[:N] * 0.55
    def add(sig, t):
        s = int(t * sr); e = min(N, s + len(sig)); out[s:e] += sig[:e - s]
    tt = np.arange(int(0.06 * sr)) / sr
    tick = 0.35 * np.sin(2 * np.pi * 1400 * tt) * np.exp(-tt * 60)
    t2 = np.arange(int(0.6 * sr)) / sr
    ding = 0.3 * (np.sin(2 * np.pi * 880 * t2) + 0.5 * np.sin(2 * np.pi * 1320 * t2)) * np.exp(-t2 * 6)
    whoosh = 0.25 * np.random.randn(int(0.35 * sr)) * np.hanning(int(0.35 * sr))
    for i in range(len(ROUNDS)):
        b = (HOOK + i * RD) / FPS
        add(whoosh, b)
        for s in range(3): add(tick, b + (15 + 30 * s) / FPS)
        add(ding, b + GUESS / FPS)
    add(whoosh, (HOOK + len(ROUNDS) * RD) / FPS)
    out = np.clip(out, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        for n in map(int, sys.argv[2:]): frame(n).save(f"/root/rg/build/st_{n}.jpg", quality=85)
        sys.exit()
    audio("/root/rg/build/a.wav")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", "/root/rg/build/a.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", "/root/rg/build/RG.mp4"], stdin=subprocess.PIPE)
    for n in range(TOTAL): p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait(); print("ok", TOTAL)
