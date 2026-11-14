"""Reel de cartões: python3 cards.py spec.json saida.mp4 [still frames...]
spec: {music, hook:[l1,l2], hookSub, tag, items:[{img, fx, title, sub:[..]}], end:[l1,l2], endSub, credit}
Títulos aceitam **destaque** em amarelo."""
import json, subprocess, sys, wave, glob, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FPS, W, H, TOP, SQ = 30, 1080, 1920, 560, 1080
YEL = (255, 214, 0)
AN = "/root/rg/build/Anton.ttf"
PB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
PM = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
S = json.load(open(sys.argv[1]))
HOOK, ITEM, END = 84, 135, 111
N = len(S["items"]); TOTAL = HOOK + N * ITEM + END
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3

def square(path, fx):
    im = Image.open(glob.glob(path)[0]).convert("RGB"); w, h = im.size; s = min(w, h)
    x = int(max(0, min(w - s, fx * w - s / 2)))
    return im.crop((x, (h - s) // 2, x + s, (h - s) // 2 + s)).resize((1240, 1240), Image.LANCZOS)

IMGS = [square(it["img"], it.get("fx", 0.5)) for it in S["items"]]

def parts(txt):
    return [(p, YEL if i % 2 else (255, 255, 255)) for i, p in enumerate(txt.split("**")) if p]

def ctext(d, y, txt, font, fill=None):
    ps = parts(txt) if fill is None else [(txt, fill)]
    x = (W - sum(d.textlength(t, font=font) for t, _ in ps)) / 2
    for t, c in ps: d.text((x, y), t, font=font, fill=c); x += d.textlength(t, font=font)

def fit(d, txt, size, maxw=1000):
    while d.textlength(txt.replace("**", ""), font=F(AN, size)) > maxw and size > 40: size -= 4
    return F(AN, size)

def header(d):
    f = F(AN, 26); tag = "GTA 6 BRASIL"; tw = d.textlength(tag, font=f)
    hw = F(PB, 30); hh = "@gtav1.br"; x0 = (W - (tw + 38 + d.textlength(hh, font=hw))) / 2
    d.rounded_rectangle((x0, 66, x0 + tw + 24, 108), 8, fill=YEL); d.text((x0 + 12, 70), tag, font=f, fill=(0, 0, 0))
    d.text((x0 + tw + 38, 68), hh, font=hw, fill=(255, 255, 255))

def paste(fr, img, t, dark=0.0):
    z = 1240 - int(160 * t); o = (1240 - z) // 2
    im = img.crop((o, o, o + z, o + z)).resize((SQ, SQ), Image.BILINEAR)
    if dark: im = ImageEnhance.Brightness(im).enhance(1 - dark)
    fr.paste(im, (0, TOP))

def flash(fr, a):
    if a > 0:
        box = (0, TOP, W, TOP + SQ)
        fr.paste(Image.blend(fr.crop(box), Image.new("RGB", (SQ, SQ), (255, 255, 255)), a), box[:2])

def credit(d):
    ctext(d, TOP + SQ + 84, S["credit"], F(PM, 26), (160, 160, 160))

def frame(n):
    fr = Image.new("RGB", (W, H)); d = ImageDraw.Draw(fr)
    if n < HOOK:
        paste(fr, IMGS[0], n / HOOK, dark=0.3); d = ImageDraw.Draw(fr); header(d); a = ease(n / 10)
        if S.get("tag"):
            f = F(PB, 28); tw = d.textlength(S["tag"], font=f)
            d.rounded_rectangle(((W - tw) / 2 - 16, 128, (W + tw) / 2 + 16, 172), 8, fill=(220, 30, 60)); d.text(((W - tw) / 2, 131), S["tag"], font=f, fill=(255, 255, 255))
        for j, l in enumerate(S["hook"]):
            ctext(d, 190 + j * 112, l, fit(d, l, int(100 * (1.3 - 0.3 * a))))
        if n > 12: ctext(d, 445, S["hookSub"], F(PB, 40), (230, 230, 230))
        credit(d); return fr
    k = n - HOOK
    if k < N * ITEM:
        i, t = divmod(k, ITEM); it = S["items"][i]
        paste(fr, IMGS[i], t / ITEM); flash(fr, 0.5 * (1 - t / 6) if t < 6 else 0)
        d = ImageDraw.Draw(fr); header(d); a = ease(t / 8)
        ctext(d, 140, f"{i+1}/{N}", F(AN, 46), YEL)
        ctext(d, 200, it["title"], fit(d, it["title"], int(110 * (1.3 - 0.3 * a))))
        for j, line in enumerate(it["sub"]):
            if t > 10 + 5 * j: ctext(d, 365 + j * 54, line, F(PB, 40), (235, 235, 235))
        for j in range(N):
            x = W / 2 - (N * 46) / 2 + j * 46
            d.rounded_rectangle((x, TOP + SQ + 46, x + 36, TOP + SQ + 56), 5, fill=YEL if j <= i else (70, 70, 70))
        credit(d); return fr
    e = n - HOOK - N * ITEM
    paste(fr, IMGS[-1], 1.0, dark=0.5); d = ImageDraw.Draw(fr); header(d); a = ease(e / 10)
    for j, l in enumerate(S["end"]):
        ctext(d, 150 + j * 120, l, fit(d, l, int(104 * (1.35 - 0.35 * a))))
    if e > 10: ctext(d, 420, S["endSub"], F(PB, 44), (255, 255, 255))
    credit(d); return fr

def audio(path):
    sr = 48000
    with wave.open(S["music"]) as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    L = int(TOTAL / FPS * sr); out = np.zeros(L, np.float32); out[:min(L, len(m))] = m[:L] * 0.6
    wl = int(0.35 * sr); wh = 0.22 * np.random.randn(wl) * np.hanning(wl)
    for i in range(N + 1):
        s = int((HOOK + i * ITEM) / FPS * sr); e = min(L, s + wl); out[s:e] += wh[:e - s]
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    out = sys.argv[2]
    if len(sys.argv) > 3:
        ims = [frame(int(x)).resize((270, 480)) for x in sys.argv[3:]]
        o = Image.new("RGB", (270 * len(ims), 480))
        for j, im in enumerate(ims): o.paste(im, (j * 270, 0))
        o.save(out); sys.exit()
    audio(out + ".wav")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", out + ".wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    for n in range(TOTAL): p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait(); print("ok", TOTAL)
