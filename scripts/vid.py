"""Reel de vídeo narrado: python3 vid.py spec.json [frames]. spec: {src, music, out, credit, segs:[[t,d,texto,fala,(src)]], end:[l1,l2,fala]}"""
import subprocess, wave, numpy as np, os, json, sys, hashlib
S = json.load(open(sys.argv[1]))
from PIL import Image, ImageDraw, ImageFont
FPS, W, H = 30, 1080, 1920
SRC = S["src"]
PD = "/root/fonts/pricedown.ttf"; IB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"; IM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
F = lambda p, s: ImageFont.truetype(p, s)
# (início, duração, texto na tela, narração)
SEG = [tuple(x[:4]) for x in S["segs"]]; SRCS = [x[4] if len(x) > 4 else SRC for x in S["segs"]]
def tts(text, i):
    mp3 = f"/root/cards/vo/v_{hashlib.md5(text.encode()).hexdigest()[:10]}.mp3"; wv = mp3[:-4] + ".wav"
    subprocess.run(["edge-tts", "--voice", "pt-BR-AntonioNeural", "--rate=+12%", "--text", text, "--write-media", mp3], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "48000", wv], check=True)
    with wave.open(wv) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
VO = [tts(s, i) if s else None for i, (_, _, _, s) in enumerate(SEG)]
VO_END = tts(S["end"][2], 99) if S["end"][2] else np.zeros(int(48000 * 1.5), np.float32)
VIS = [int(round(d * FPS)) for _, d, _, _ in SEG]
DUR = [max(v, int(len(a) / 48000 * FPS) + 6) if a is not None else v for v, a in zip(VIS, VO)]
ENDN = int(len(VO_END) / 48000 * FPS) + 30
TOTAL = sum(DUR) + ENDN
STARTS = np.cumsum([0] + DUR[:-1])
CREDIT = S["credit"]

def seg_frames(t0, n, vis, src):
    vert = src.endswith(".mp4") and "1080,1920" in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", src], capture_output=True, text=True).stdout
    pre = max(0, t0 - 3); tr = ""
    vf = (tr + f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,eq=brightness=-0.12[bg];"
          f"[b]scale=-2:900,crop={W}:900[fg];[bg][fg]overlay=0:(H-h)/2,setpts={n / vis:.4f}*PTS,fps={FPS}")
    if vert: vf = tr + f"scale={W}:{H},setpts={n / vis:.4f}*PTS,fps={FPS}"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(pre), "-i", src, "-ss", f"{(t0 - pre) * n / vis:.3f}", "-frames:v", str(n), "-filter_complex", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if len(a) < n: a = np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)])
    return a

CLIPS = [seg_frames(t, n, v, s) for (t, _, _, _), n, v, s in zip(SEG, DUR, VIS, SRCS)]
LAST = Image.fromarray(CLIPS[-1][-1])

def ctext(d, y, t, f, fill, sw=7, sf=(25, 0, 35)):
    d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=fill, stroke_width=sw, stroke_fill=sf)

def frame(n):
    if n >= sum(DUR):
        im = LAST.copy(); d = ImageDraw.Draw(im); e = n - sum(DUR)
        ctext(d, 300, S["end"][0], F(PD, 130), "white"); s2 = 110
        while d.textlength(S["end"][1], font=F(PD, s2)) > 1000: s2 -= 6
        ctext(d, 440, S["end"][1], F(PD, s2), (255, 64, 170))
        t = "Comenta aí"; f = F(IB, 56); tw = d.textlength(t, font=f)
        d.rounded_rectangle(((W - tw) / 2 - 36, 1460, (W + tw) / 2 + 36, 1556), 48, fill=(255, 64, 170)); d.text(((W - tw) / 2, 1472), t, font=f, fill="white")
    else:
        i = int(np.searchsorted(STARTS, n, side="right") - 1); k = n - STARTS[i]
        im = Image.fromarray(CLIPS[i][k]); d = ImageDraw.Draw(im)
        txt = SEG[i][2]
        if txt:
            a = min(1, k / 5); s = int(118 * (1.25 - 0.25 * a))
            while d.textlength(txt, font=F(PD, s)) > 1000: s -= 6
            ctext(d, 1340, txt, F(PD, s), (255, 64, 170) if i == 0 else "white", 8)
    ctext(d, 110, "GTA 6 BRASIL", F(PD, 64), "white", 5)
    d.text(((W - d.textlength(CREDIT, font=F(IM, 26))) / 2, H - 130), CREDIT, font=F(IM, 26), fill=(235, 235, 235), stroke_width=2, stroke_fill=(0, 0, 0))
    return im

def audio(path):
    sr = 48000; L = int(TOTAL / FPS * sr)
    with wave.open(S["music"]) as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    m = np.tile(m, int(np.ceil(L / len(m))))[:L]; fade = np.ones(L); fl = int(1.2 * sr); fade[-fl:] = np.linspace(1, 0, fl)
    out = m * 0.3 * fade; cur = 0
    for i, (_, _, _, say) in enumerate(SEG):
        if not say: continue
        a = VO[i]; s = max(int(STARTS[i] / FPS * sr) + int(0.1 * sr), cur); e = min(L, s + len(a))
        out[s:e] += a[:e - s] * 1.1; cur = e + int(0.1 * sr)
    s = max(int(sum(DUR) / FPS * sr) + int(0.15 * sr), cur); e = min(L, s + len(VO_END)); out[s:e] += VO_END[:e - s] * 1.1
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

if len(sys.argv) > 2:
    ims = [frame(int(x)).resize((270, 480)) for x in sys.argv[2:]]
    o = Image.new("RGB", (270 * len(ims), 480))
    for j, im in enumerate(ims): o.paste(im, (j * 270, 0))
    o.save("/root/cards/vid_prev.jpg"); print(TOTAL); sys.exit()
audio("/root/cards/vid.wav")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "/root/cards/vid.wav",
                      "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                      "-ar", "48000", "-movflags", "+faststart", "-shortest", S["out"]], stdin=subprocess.PIPE)
for n in range(TOTAL): p.stdin.write(frame(n).convert("RGB").tobytes())
p.stdin.close(); p.wait(); print("ok", TOTAL)
