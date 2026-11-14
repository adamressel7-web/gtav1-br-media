import subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
FPS, W, H = 30, 1080, 1920
PD = "/root/fonts/pricedown.ttf"
SER = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"; SERB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
IB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"; IM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
F = lambda p, s: ImageFont.truetype(p, s)
CL = [("CLÁUSULA 1", "De 19/11 a 28/11, o jogador tem direito a jogar GTA 6 sem interrupções."),
      ("CLÁUSULA 2", "Fica proibido dizer \"é só um jogo\"."),
      ("CLÁUSULA 3", "Nada de \"a gente precisa conversar\" no meio de uma missão."),
      ("CLÁUSULA 4", "Carinho, só na tela de carregamento."),
      ("CLÁUSULA 5", "A louça fica pra depois do assalto."),
      ("BRECHA", "O contrato pode ser cancelado se o parceiro pagar metade do jogo.")]
HOOK, STEP, END = 60, 84, 120
TOTAL = HOOK + len(CL) * STEP + END
bg = Image.open("/root/rg/hi/1570.png").convert("RGB")
s = max(W / bg.width, H / bg.height); bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1))
x0 = (bg.width - W) // 2; bg = bg.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(8))
BG = ImageEnhance.Brightness(bg).enhance(0.55)
PX0, PY0, PW = 70, 300, 940

def wrap(d, t, f, w):
    out, cur = [], ""
    for word in t.split():
        nxt = (cur + " " + word).strip()
        if d.textlength(nxt, font=f) > w and cur: out.append(cur); cur = word
        else: cur = nxt
    out.append(cur); return out

def paper(nvis, stamp_a):
    p = Image.new("RGBA", (PW, 1340), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
    d.rounded_rectangle((0, 0, PW - 1, 1339), 18, fill=(250, 244, 228, 255))
    t = "CONTRATO DE CONVIVÊNCIA"; f = F(SERB, 46); d.text(((PW - d.textlength(t, font=f)) / 2, 50), t, font=f, fill=(40, 30, 30))
    t = "Lançamento de GTA 6"; f = F(SER, 34); d.text(((PW - d.textlength(t, font=f)) / 2, 112), t, font=f, fill=(110, 60, 90))
    d.line((60, 175, PW - 60, 175), fill=(180, 160, 140), width=2)
    y = 205
    for i, (h, t) in enumerate(CL[:nvis]):
        d.text((60, y), h, font=F(SERB, 30), fill=(200, 40, 120) if h == "BRECHA" else (40, 30, 30)); y += 42
        for l in wrap(d, t, F(SER, 33), PW - 120): d.text((60, y), l, font=F(SER, 33), fill=(50, 45, 45)); y += 44
        y += 22
    yy = 1215
    for k, lab in enumerate(["Jogador(a)", "Parceiro(a)"]):
        x = 60 + k * 430; d.line((x, yy, x + 360, yy), fill=(60, 50, 50), width=2)
        d.text((x, yy + 10), lab, font=F(SER, 26), fill=(90, 80, 80))
    if stamp_a > 0:
        st = Image.new("RGBA", (520, 170), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((6, 6, 513, 163), 18, outline=(220, 30, 60, 255), width=10)
        f = F(PD, 104); t = "ASSINADO"; sd.text(((520 - sd.textlength(t, font=f)) / 2, 22), t, font=f, fill=(220, 30, 60, 255))
        sc = 1.6 - 0.6 * stamp_a; st = st.resize((int(520 * sc), int(170 * sc))).rotate(-12, expand=True)
        st.putalpha(Image.eval(st.getchannel("A"), lambda v: int(v * min(1, stamp_a * 1.5))))
        p.alpha_composite(st, ((PW - st.width) // 2 + 120, 1120 - st.height // 2))
    return p

def frame(n):
    fr = BG.copy().convert("RGBA"); d = ImageDraw.Draw(fr)
    f = F(PD, 64); t = "GTA 6 BRASIL"; d.text(((W - d.textlength(t, font=f)) / 2, 110), t, font=f, fill="white", stroke_width=5, stroke_fill=(40, 0, 50))
    if n < HOOK:
        a = min(1, n / 10)
        for k, (t, c) in enumerate([("ANTES DO DIA 19", (255, 255, 255)), ("ASSINA AQUI", (255, 90, 180))]):
            f = F(PD, int(110 * (1.3 - 0.3 * a))); d.text(((W - d.textlength(t, font=f)) / 2, 720 + k * 130), t, font=f, fill=c, stroke_width=7, stroke_fill=(30, 0, 40))
        return fr.convert("RGB")
    k = n - HOOK; nvis = min(len(CL), k // STEP + 1); stamp = max(0, (k - len(CL) * STEP) / 10) if k >= len(CL) * STEP else 0
    p = paper(nvis, min(1, stamp)); fr.alpha_composite(p, (PX0, PY0))
    if k >= len(CL) * STEP + 25:
        t = "Marca quem precisa assinar"; f = F(IB, 46); tw = d.textlength(t, font=f)
        d.rounded_rectangle(((W - tw) / 2 - 30, 1700, (W + tw) / 2 + 30, 1780), 40, fill=(255, 64, 170)); d.text(((W - tw) / 2, 1713), t, font=f, fill="white")
    return fr.convert("RGB")

def audio(path):
    sr = 48000
    with wave.open("/root/musica/m04_funk.wav") as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    L = int(TOTAL / FPS * sr); m = np.tile(m, int(np.ceil(L / len(m))))[:L]
    fade = np.ones(L); fl = int(1.2 * sr); fade[-fl:] = np.linspace(1, 0, fl); out = m * 0.6 * fade
    t = np.arange(int(0.25 * sr)) / sr; thud = 0.6 * np.sin(2 * np.pi * 90 * t) * np.exp(-t * 18)
    s0 = int((HOOK + len(CL) * STEP) / FPS * sr); out[s0:s0 + len(thud)] += thud[:max(0, min(len(thud), L - s0))]
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

import sys
if len(sys.argv) > 1:
    ims = [frame(int(x)).resize((270, 480)) for x in sys.argv[1:]]
    o = Image.new("RGB", (270 * len(ims), 480))
    for j, im in enumerate(ims): o.paste(im, (j * 270, 0))
    o.save("/root/cards/ctr_st.jpg"); sys.exit()
audio("/root/cards/ctr.wav")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "/root/cards/ctr.wav",
                      "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                      "-movflags", "+faststart", "-shortest", "/root/cards/CTR.mp4"], stdin=subprocess.PIPE)
for n in range(TOTAL): p.stdin.write(frame(n).tobytes())
p.stdin.close(); p.wait(); print("ok", TOTAL)
