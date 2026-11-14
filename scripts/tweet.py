"""Reel estilo 'post/tweet' (padrão @gtav1.br): python3 tweet.py spec.json SAIDA.mp4 [frames de prévia...]
spec: {music, bg, slides:[{text, img?, fx?}], credit}
Texto: **negrito branco**, ==destaque rosa==, \\n = novo parágrafo."""
import json, subprocess, sys, wave, glob, re, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FPS, W, H = 30, 1080, 1920
PINK = (255, 64, 170); WHITE = (255, 255, 255); GRAY = (190, 175, 205); CARD = (30, 14, 46)
IM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
IB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
IX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
PD = "/root/fonts/pricedown.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
S = json.load(open(sys.argv[1]))
EMO = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]")
for _s in S["slides"]: _s["text"] = re.sub(" +", " ", EMO.sub("", _s["text"])).strip()
CX0, CX1 = 60, 1020          # cartão
PADX = 52
TXT_W = CX1 - CX0 - 2 * PADX
FS, LH = 54, 76

def cover(path, w, h, fx=0.5):
    im = Image.open(glob.glob(path)[0]).convert("RGB")
    iw, ih = im.size; s = max(w / iw, h / ih)
    im = im.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    x = int((im.width - w) * fx); y = (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))

def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = Image.new("RGBA", im.size); out.paste(im, (0, 0), m); return out

# ---------- fundo fixo: imagem oficial desfocada + degradê Vice City ----------
def make_bg():
    base = cover(S["bg"], W, H, S.get("bgfx", 0.5)).filter(ImageFilter.GaussianBlur(6))
    base = ImageEnhance.Brightness(base).enhance(0.75)
    grad = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        c = (int(120 + 120 * t), int(40 + 40 * t), int(170 - 60 * t))  # roxo -> rosa/laranja
        grad.putpixel((0, y), c)
    grad = grad.resize((W, H))
    return Image.blend(base, grad, 0.55)
BG = make_bg()

# ---------- texto rico ----------
def tokens(text):
    out = []
    for para in text.split("\n"):
        segs = re.split(r"(\*\*.*?\*\*|==.*?==)", para)
        for sg in segs:
            if not sg: continue
            if sg.startswith("**"): st, sg = "b", sg[2:-2]
            elif sg.startswith("=="): st, sg = "p", sg[2:-2]
            else: st = "n"
            if sg[:1].isspace() and out and out[-1][0] != "\n":
                out[-1] = (out[-1][0] + " ", out[-1][1])
            for w in re.findall(r"\S+\s*", sg): out.append((w, st))
        out.append(("\n", "n"))
    return out[:-1]

FONT = {"n": (IM, WHITE), "b": (IB, WHITE), "p": (IB, PINK)}

def layout(text, d):
    lines, cur, x = [], [], 0
    for w, st in tokens(text):
        if w == "\n":
            lines.append(cur); lines.append("gap"); cur, x = [], 0; continue
        f = F(FONT[st][0], FS); tw = d.textlength(w, font=f)
        if x + d.textlength(w.rstrip(), font=f) > TXT_W and cur:
            lines.append(cur); cur, x = [], 0
        cur.append((w, st, x)); x += tw
    if cur: lines.append(cur)
    return lines

def card(slide):
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = layout(slide["text"], tmp)
    th = sum(LH * 0.45 if l == "gap" else LH for l in lines)
    img_h = 620 if slide.get("img") else 0
    ch = int(40 + 110 + 36 + th + (30 + img_h if img_h else 0) + 46)
    c = Image.new("RGBA", (CX1 - CX0, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, c.width - 1, ch - 1), 36, fill=CARD + (238,), outline=PINK, width=4)
    av = Image.open("/root/cards/avatar.jpg").convert("RGB").resize((110, 110))
    m = Image.new("L", (110, 110), 0); ImageDraw.Draw(m).ellipse((0, 0, 109, 109), fill=255)
    d.ellipse((PADX - 4, 36, PADX + 114, 154), fill=PINK); c.paste(av, (PADX, 40), m)
    d.text((PADX + 136, 52), "GTA 6 Brasil", font=F(IX, 42), fill=WHITE)
    d.text((PADX + 136, 104), "@gtav1.br", font=F(IM, 32), fill=GRAY)
    y = 40 + 110 + 36
    for l in lines:
        if l == "gap": y += LH * 0.45; continue
        for w, st, x in l: d.text((PADX + x, y), w, font=F(FONT[st][0], FS), fill=FONT[st][1])
        y += LH
    if img_h:
        ph = rounded(cover(slide["img"], c.width - 2 * PADX + 24, img_h, slide.get("fx", 0.5)), 26)
        c.alpha_composite(ph, (PADX - 12, int(y + 30)))
    return c

CARDS = [card(s) for s in S["slides"]]
DUR = [int(FPS * max(4.2, 1.6 + 0.36 * len(re.sub(r"[*=]", "", s["text"]).split()))) for s in S["slides"]]

# ---------- narração (edge-tts) ----------
PRON = [("Vice City", "Váice Síti"), ("Grassrivers", "Grás Rívers"), ("Leonida Keys", "Leônida Kíis"), ("Keys", "Kíis"),
        ("Rockstar Games", "Róckstar Guêims"), ("Rockstar", "Róckstar"), ("Leonida", "Leônida"), ("Port Gellhorn", "Pórt Guélhorn"),
        ("Mount Kalaga", "Máunt Kalága"), ("Jason", "Djêison"), ("PS Store", "pê ésse Stór"), ("Xbox Store", "Écsbox Stór"),
        ("Xbox 360", "Écsbox trezentos e sessenta"), ("Xbox", "Écsbox"), ("PS5", "pê ésse cinco"), ("PS4", "pê ésse quatro"), ("PS3", "pê ésse três"), ("Ultimate", "Áltimeit"), ("Scooter Bros", "Scúter Brôs"), ("Macca", "Máka"),
        ("Sensor Tower", "Sênsor Táuer"), ("trailers", "trêilers"), ("trailer", "trêiler"), ("Vintage", "Víntedj"), ("online", "onláine"),
        ("Online", "Onláine"), ("1.002", "um ponto zero zero dois"), ("GB", "gigas"), ("Series", "Séries"), ("GTA V", "GTA cinco"), ("GTA 6", "GTA seis"), ("GTA VI", "GTA seis"), ("Rockstar's", "da Róckstar")]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
def spoken(t):
    t = re.sub(r"[*=]", "", t).replace("\n", ". ").replace("..", ".")
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})\b", lambda m: f"{int(m.group(1))} de {MESES[int(m.group(2)) - 1]}" if 1 <= int(m.group(2)) <= 12 else m.group(0), t)
    for a, b in PRON: t = re.sub(r"\b" + re.escape(a) + r"\b", b, t)
    return t
if S.get("narrate"):
    for s in S["slides"]: s.setdefault("say", spoken(s["text"]))
VO = []
if any(s.get("say") for s in S["slides"]):
    import os, hashlib
    voice = S.get("voice", "pt-BR-AntonioNeural"); rate = S.get("rate", "+8%")
    os.makedirs("/root/cards/vo", exist_ok=True)
    for i, s in enumerate(S["slides"]):
        if not s.get("say"): VO.append(None); continue
        h = hashlib.md5((voice + rate + s["say"]).encode()).hexdigest()[:12]; mp3 = f"/root/cards/vo/{h}.mp3"; wv = mp3[:-4] + ".wav"
        if not os.path.exists(wv):
            subprocess.run(["edge-tts", "--voice", voice, f"--rate={rate}", "--text", s["say"], "--write-media", mp3], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "48000", wv], check=True)
        with wave.open(wv) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        VO.append(a); DUR[i] = max(int(FPS * (len(a) / 48000 + 0.9)), int(FPS * 2.5))
DUR[-1] += 30
STARTS = np.cumsum([0] + DUR[:-1]); TOTAL = int(sum(DUR))
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3

# glow do cartão (pré-calculado)
def glow(c):
    g = Image.new("RGBA", (c.width + 120, c.height + 120), (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((60, 60, 60 + c.width, 60 + c.height), 40, outline=PINK + (255,), width=18)
    return g.filter(ImageFilter.GaussianBlur(22))
GLOWS = [glow(c) for c in CARDS]

TICK = "@GTAV1.BR  •  GTA 6 BRASIL  •  "
def ticker(fr, n):
    d = ImageDraw.Draw(fr)
    band = Image.new("RGB", (W, 64))
    for x in range(W):
        t = x / W; band.paste((int(255), int(70 + 90 * t), int(170 - 120 * t)), (x, 0, x + 1, 64))
    fr.paste(band, (0, H - 150))
    f = F(PD, 40); unit = d.textlength(TICK, font=f); off = -(n * 3) % unit
    x = -off
    while x < W:
        d.text((x, H - 150 + 10), TICK, font=f, fill=(40, 10, 50)); x += unit

def frame(n):
    z = 1 + 0.04 * n / TOTAL
    bg = BG.resize((int(W * z), int(H * z))); ox, oy = (bg.width - W) // 2, (bg.height - H) // 2
    fr = bg.crop((ox, oy, ox + W, oy + H)).convert("RGBA"); d = ImageDraw.Draw(fr)
    # selo topo
    f = F(PD, 70); t = "GTA 6 BRASIL"; tw = d.textlength(t, font=f)
    d.text(((W - tw) / 2, 92), t, font=f, fill=WHITE, stroke_width=4, stroke_fill=(60, 10, 70))
    i = int(np.searchsorted(STARTS, n, side="right") - 1); k = n - STARTS[i]
    a = ease(k / 9)
    c, g = CARDS[i], GLOWS[i]
    y = int((H - c.height) / 2 - 20 + (1 - a) * 80)
    if a < 1:
        c = c.copy(); c.putalpha(Image.eval(c.getchannel("A"), lambda v: int(v * a)))
        g = g.copy(); g.putalpha(Image.eval(g.getchannel("A"), lambda v: int(v * a * 0.8)))
    fr.alpha_composite(g, (CX0 - 60, y - 60)); fr.alpha_composite(c, (CX0, y))
    # progresso
    for j in range(len(CARDS)):
        x = W / 2 - len(CARDS) * 23 + j * 46
        d.rounded_rectangle((x, H - 230, x + 36, H - 220), 5, fill=PINK if j <= i else (90, 60, 110))
    d.text(((W - d.textlength(S["credit"], font=F(IM, 24))) / 2, H - 196), S["credit"], font=F(IM, 24), fill=(235, 220, 240))
    ticker(fr, n)
    return fr.convert("RGB")

def audio(path):
    sr = 48000
    with wave.open(S["music"]) as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    L = int(TOTAL / FPS * sr); reps = int(np.ceil(L / len(m))); m = np.tile(m, reps)[:L]
    fade = np.ones(L); fl = int(1.2 * sr); fade[-fl:] = np.linspace(1, 0, fl)
    out = m * (0.22 if VO else 0.6) * fade
    wl = int(0.3 * sr); wh = 0.18 * np.random.randn(wl) * np.hanning(wl)
    for s0 in STARTS[1:]:
        s = int(s0 / FPS * sr); e = min(L, s + wl); out[s:e] += wh[:e - s]
    for i, a in enumerate(VO):
        if a is None: continue
        s = int(STARTS[i] / FPS * sr) + int(0.3 * sr); e = min(L, s + len(a)); out[s:e] += a[:e - s] * 1.1
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    out = sys.argv[2]
    if len(sys.argv) > 3:
        ims = [frame(int(x)).resize((360, 640)) for x in sys.argv[3:]]
        o = Image.new("RGB", (360 * len(ims), 640))
        for j, im in enumerate(ims): o.paste(im, (j * 360, 0))
        o.save(out); print("frames", TOTAL); sys.exit()
    audio(out + ".wav")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", out + ".wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    for n in range(TOTAL): p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait(); print("ok", TOTAL)
