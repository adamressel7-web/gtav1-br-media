"""REAL ou GTA 6? em vídeo: drone de Miami (CC BY 3.0) x gameplay oficial."""
import subprocess, wave, numpy as np, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FPS, W, H = 30, 1080, 1920
PD = "/root/fonts/pricedown.ttf"; IB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"; IM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
F = lambda p, s: ImageFont.truetype(p, s)
ROUNDS = [("/root/miami/c20.mp4", "REAL"), ("/root/fds/k1574.mp4", "GTA 6"), ("/root/miami/c1520.mp4", "REAL"),
          ("/root/fds/k1546.mp4", "GTA 6"), ("/root/miami/c680.mp4", "REAL"), ("/root/fds/k770.mp4", "GTA 6")]
END_CLIP = "/root/fds/k1550.mp4"
HOOK, RND, REV, END = 60, 120, 78, 96   # reveal starts at frame 78 of each 120-frame round

def frames(path, n):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"setpts=1.65*PTS,fps={FPS},scale={W}:{H}", "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if len(a) < n: a = np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)])
    return a

CL = [frames(p, RND) for p, _ in ROUNDS]; EC = frames(END_CLIP, END)
TOTAL = HOOK + len(ROUNDS) * RND + END
CREDIT = "Gameplay: Rockstar Games  |  Miami: The Nomad With The Drone (CC BY 3.0)"

def ctext(d, y, t, f, fill, sw=7, sf=(25, 0, 35)):
    d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=fill, stroke_width=sw, stroke_fill=sf)

def chrome(d, n):
    ctext(d, 110, "GTA 6 BRASIL", F(PD, 64), "white", 5)
    d.text(((W - d.textlength(CREDIT, font=F(IM, 24))) / 2, H - 120), CREDIT, font=F(IM, 24), fill=(240, 240, 240), stroke_width=2, stroke_fill=(0, 0, 0))

def frame(n):
    if n < HOOK:
        im = Image.fromarray(CL[0][0]).filter(ImageFilter.GaussianBlur(14)); d = ImageDraw.Draw(im); chrome(d, n)
        a = min(1, n / 10); s = int(150 * (1.3 - 0.3 * a))
        ctext(d, 700, "REAL OU", F(PD, s), "white"); ctext(d, 700 + s + 10, "GTA 6?", F(PD, s), (255, 64, 170))
        if n > 15: ctext(d, 1130, "Acerta as 6?", F(IB, 60), "white", 4)
        return im
    k = n - HOOK
    if k < len(ROUNDS) * RND:
        i, t = divmod(k, RND); im = Image.fromarray(CL[i][t]); d = ImageDraw.Draw(im); chrome(d, n)
        d.text((60, 250), f"{i + 1}/6", font=F(PD, 70), fill=(255, 214, 0), stroke_width=5, stroke_fill=(0, 0, 0))
        if t < REV:
            ctext(d, 1380, "REAL OU GTA 6?", F(PD, 110), "white")
            c = 3 - t * 3 // REV
            if t > 8: ctext(d, 1530, str(c), F(PD, 170), (255, 214, 0))
        else:
            lab = ROUNDS[i][1]; col = (40, 220, 120) if lab == "REAL" else (255, 64, 170)
            a = min(1, (t - REV) / 6); s = int(230 * (1.5 - 0.5 * a))
            ctext(d, 1400 - (s - 230) // 2, lab, F(PD, s), col, 10, (10, 0, 15))
            if lab == "REAL": ctext(d, 1650, "Miami, de verdade", F(IB, 48), "white", 4)
            else: ctext(d, 1650, "Gameplay oficial", F(IB, 48), "white", 4)
        return im
    e = n - HOOK - len(ROUNDS) * RND; im = Image.fromarray(EC[e]); d = ImageDraw.Draw(im); chrome(d, n)
    ctext(d, 760, "QUANTAS", F(PD, 140), "white"); ctext(d, 910, "VOCÊ ACERTOU?", F(PD, 120), (255, 64, 170))
    if e > 10:
        t = "Comenta aí"; f = F(IB, 56); tw = d.textlength(t, font=f)
        d.rounded_rectangle(((W - tw) / 2 - 36, 1140, (W + tw) / 2 + 36, 1236), 48, fill=(255, 64, 170)); d.text(((W - tw) / 2, 1152), t, font=f, fill="white")
    return im

def tts(text, name):
    mp3 = f"/root/cards/vo/rg2_{name}.mp3"; wv = mp3[:-4] + ".wav"
    if not os.path.exists(wv):
        subprocess.run(["edge-tts", "--voice", "pt-BR-AntonioNeural", "--rate=+10%", "--text", text, "--write-media", mp3], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "48000", wv], check=True)
    with wave.open(wv) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

def audio(path):
    sr = 48000; L = int(TOTAL / FPS * sr)
    with wave.open("/root/musica/m05_phonk.wav") as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    m = np.tile(m, int(np.ceil(L / len(m))))[:L]; fade = np.ones(L); fl = int(1.2 * sr); fade[-fl:] = np.linspace(1, 0, fl)
    out = m * 0.28 * fade
    def put(a, f0, g=1.1):
        s = int(f0 / FPS * sr); e = min(L, s + len(a)); out[s:e] += a[:e - s] * g
    put(tts("Real ou GTA seis? Vê se você acerta as seis.", "hook"), 4)
    for i, (_, lab) in enumerate(ROUNDS):
        f0 = HOOK + i * RND
        tk = np.arange(int(0.05 * sr)) / sr; tick = 0.35 * np.sin(2 * np.pi * 1200 * tk) * np.exp(-tk * 60)
        for c in range(3): put(tick, f0 + 10 + c * (REV - 10) // 3, 1)
        put(tts("Real!" if lab == "REAL" else "GTA seis!", "r" if lab == "REAL" else "g"), f0 + REV + 2)
    put(tts("Quantas você acertou? Comenta aí!", "end"), HOOK + len(ROUNDS) * RND + 6)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

import sys
if len(sys.argv) > 1:
    ims = [frame(int(x)).resize((270, 480)) for x in sys.argv[1:]]
    o = Image.new("RGB", (270 * len(ims), 480))
    for j, im in enumerate(ims): o.paste(im, (j * 270, 0))
    o.save("/root/cards/rg2_prev.jpg"); sys.exit()
audio("/root/cards/rg2.wav")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "/root/cards/rg2.wav",
                      "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                      "-ar", "48000", "-movflags", "+faststart", "-shortest", "/root/cards/RG2.mp4"], stdin=subprocess.PIPE)
for n in range(TOTAL): p.stdin.write(frame(n).convert("RGB").tobytes())
p.stdin.close(); p.wait(); print("ok", TOTAL)
