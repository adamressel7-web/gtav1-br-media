import subprocess, sys, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FPS, W, H, TOP, SQ = 30, 1080, 1920, 560, 1080
YEL = (255, 214, 0); PINK = (255, 64, 160)
AN = "/root/rg/build/Anton.ttf"
PB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
PM = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
I = "/root/rr/img/"
REG = [
    ("Vice_City_08", 0.50, "VICE CITY", ["Hotéis art déco, areia branca", "e a capital mundial dos cruzeiros"]),
    ("Leonida_Keys_01", 0.50, "LEONIDA KEYS", ["Arquipélago tropical: vida tranquila,", "mas as águas mais perigosas do país"]),
    ("Grassrivers_01", 0.62, "GRASSRIVERS", ["O pântano dos jacarés...", "e de predadores bem piores"]),
    ("Port_Gellhorn_01", 0.42, "PORT GELLHORN", ["Motéis baratos, atrações fechadas", "e muita confusão"]),
    ("Ambrosia_03", 0.50, "AMBROSIA", ["Refinaria de açúcar e uma gangue", "de motoqueiros mandando em tudo"]),
    ("Mount_Kalaga_National_Park_02", 0.45, "MOUNT KALAGA", ["Caça, pesca, trilhas off-road", "e uns malucos isolados no mato"]),
]
HOOK, ITEM, END = 84, 129, 111
TOTAL = HOOK + len(REG) * ITEM + END

def square(name, fx):
    import glob
    im = Image.open(glob.glob(I + name + ".*")[0]).convert("RGB")
    w, h = im.size; s = min(w, h)
    x = int(max(0, min(w - s, fx * w - s / 2)))
    return im.crop((x, (h - s) // 2, x + s, (h - s) // 2 + s)).resize((1240, 1240), Image.LANCZOS)

IMGS = [square(r[0], r[1]) for r in REG]
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3

def ctext(d, y, txt, font, fill=(255, 255, 255)):
    d.text(((W - d.textlength(txt, font=font)) / 2, y), txt, font=font, fill=fill)

def ctext_multi(d, y, parts, font):
    x = (W - sum(d.textlength(t, font=font) for t, _ in parts)) / 2
    for t, c in parts: d.text((x, y), t, font=font, fill=c); x += d.textlength(t, font=font)

def header(d):
    f = F(AN, 26); tag = "GTA 6 BRASIL"; tw = d.textlength(tag, font=f)
    hw = F(PB, 30); hh = "@gtav1.br"; x0 = (W - (tw + 38 + d.textlength(hh, font=hw))) / 2
    d.rounded_rectangle((x0, 66, x0 + tw + 24, 108), 8, fill=YEL); d.text((x0 + 12, 70), tag, font=f, fill=(0, 0, 0))
    d.text((x0 + tw + 38, 68), hh, font=hw, fill=(255, 255, 255))

def paste(fr, img, t, dark=0.0, blur=0):
    z = 1240 - int(160 * t); o = (1240 - z) // 2
    im = img.crop((o, o, o + z, o + z)).resize((SQ, SQ), Image.BILINEAR)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    if dark: im = ImageEnhance.Brightness(im).enhance(1 - dark)
    fr.paste(im, (0, TOP))

def flash(fr, a):
    if a <= 0: return
    box = (0, TOP, W, TOP + SQ)
    fr.paste(Image.blend(fr.crop(box), Image.new("RGB", (SQ, SQ), (255, 255, 255)), a), box[:2])

def frame(n):
    fr = Image.new("RGB", (W, H)); d = ImageDraw.Draw(fr)
    if n < HOOK:
        paste(fr, IMGS[n * len(REG) // HOOK], n / HOOK, dark=0.25)
        d = ImageDraw.Draw(fr); header(d); a = ease(n / 10)
        s = int(96 * (1.3 - 0.3 * a))
        ctext(d, 150, "PRA ONDE VOCÊ VAI", F(AN, s))
        ctext_multi(d, 265, [("PRIMEIRO EM ", (255, 255, 255)), ("GTA 6", YEL), ("?", (255, 255, 255))], F(AN, s))
        if n > 12: ctext(d, 410, "As 6 regiões de Leonida", F(PB, 42), (230, 230, 230))
        return fr
    k = n - HOOK
    if k < len(REG) * ITEM:
        i, t = divmod(k, ITEM); name, sub = REG[i][2], REG[i][3]
        paste(fr, IMGS[i], t / ITEM); flash(fr, 0.5 * (1 - t / 6) if t < 6 else 0)
        d = ImageDraw.Draw(fr); header(d); a = ease(t / 8)
        ctext_multi(d, 140, [(f"{i+1}", YEL), (f"/{len(REG)}  REGIÃO", (255, 255, 255))], F(AN, 48))
        ctext(d, 205, name, F(AN, int(122 * (1.35 - 0.35 * a))), YEL)
        for j, line in enumerate(sub):
            if t > 8 + 4 * j: ctext(d, 375 + j * 52, line, F(PB, 40), (235, 235, 235))
        # trilho de progresso das 6 regiões
        for j in range(len(REG)):
            x = W / 2 - (len(REG) * 46) / 2 + j * 46
            d.rounded_rectangle((x, TOP + SQ + 46, x + 36, TOP + SQ + 56), 5, fill=YEL if j <= i else (70, 70, 70))
        ctext(d, TOP + SQ + 84, "Imagem oficial: Rockstar Games", F(PM, 26), (160, 160, 160))
        return fr
    e = n - HOOK - len(REG) * ITEM
    # mosaico 3x2 das 6 regiões
    tile = 360
    for j, im in enumerate(IMGS):
        x, y = (j % 3) * tile, TOP + 180 + (j // 3) * tile
        fr.paste(ImageEnhance.Brightness(im.resize((tile, tile), Image.BILINEAR)).enhance(0.85), (x, y))
    d = ImageDraw.Draw(fr); header(d); a = ease(e / 10)
    for j, r in enumerate(REG):
        x, y = (j % 3) * tile, TOP + 180 + (j // 3) * tile
        f = F(AN, 40); tw = d.textlength(r[2], font=f)
        d.rectangle((x, y + tile - 58, x + tile, y + tile), fill=(0, 0, 0))
        d.text((x + (tile - tw) / 2, y + tile - 56), r[2], font=f, fill=YEL)
    s = int(104 * (1.35 - 0.35 * a))
    ctext(d, 150, "QUAL VOCÊ", F(AN, s)); ctext(d, 270, "ESCOLHE?", F(AN, s), YEL)
    if e > 10: ctext(d, 420, "Comenta a região aí embaixo", F(PB, 44))
    return fr

def audio(path):
    sr = 48000
    with wave.open("/root/rr/music.wav") as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    N = int(TOTAL / FPS * sr); out = np.zeros(N, np.float32); out[:min(N, len(m))] = m[:N] * 0.6
    wl = int(0.35 * sr); whoosh = 0.22 * np.random.randn(wl) * np.hanning(wl)
    for i in range(len(REG) + 1):
        s = int((HOOK + i * ITEM) / FPS * sr); e = min(N, s + wl); out[s:e] += whoosh[:e - s]
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        for n in map(int, sys.argv[2:]): frame(n).save(f"/root/rr/st_{n}.jpg", quality=85)
        sys.exit()
    audio("/root/rr/a.wav")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", "/root/rr/a.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", "/root/rr/RR.mp4"], stdin=subprocess.PIPE)
    for n in range(TOTAL): p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait(); print("ok", TOTAL)
