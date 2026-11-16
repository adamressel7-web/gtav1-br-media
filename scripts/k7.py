"""Reel 'N coisas' estilo respawn: python3 k7.py spec.json [frames]
spec: {music, out, credit, intro:{title,say,src,t,d}, items:[{num,tag,say,src,t,d,fx}], outro:{title,sub,say,src,t,d}}"""
import asyncio, json, os, re, subprocess, sys, wave, hashlib
import numpy as np, edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FPS, W, H = 30, 1080, 1920
S = json.load(open(sys.argv[1]))
PD = "/root/fonts/pricedown.ttf"; AN = "/root/rg/build/Anton.ttf"
IB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"; IX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"; IM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
F = lambda p, s: ImageFont.truetype(p, s)
COLS = [(255, 64, 170), (60, 200, 255), (60, 230, 140), (255, 90, 90), (255, 200, 40), (170, 110, 255), (255, 140, 40)]
VW, VH, VY = 960, 640, 560
sys.path.insert(0, "/root/cards")
PRON = [("Vice City", "Váice Síti"), ("Grassrivers", "Grás Rívers"), ("Keys", "Kíis"), ("Rockstar", "Róckstar"), ("Leonida", "Leônida"),
        ("Jason", "Djêison"), ("Waink", "Uêinc"), ("GTA 6", "GTA seis"), ("PS5", "pê ésse cinco"), ("Xbox", "Écsbox")]
def spoken(t):
    for a, b in PRON: t = re.sub(r"\b" + re.escape(a) + r"\b", b, t)
    return t

async def _tts(text, mp3):
    c = edge_tts.Communicate(spoken(text), "pt-BR-AntonioNeural", rate="+12%", boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    return words

def tts(text):
    h = hashlib.md5(text.encode()).hexdigest()[:10]; mp3 = f"/root/cards/vo/k7_{h}.mp3"; wv = mp3[:-4] + ".wav"; js = mp3[:-4] + ".json"
    if not os.path.exists(js):
        words = asyncio.run(_tts(text, mp3))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "48000", wv], check=True)
        json.dump(words, open(js, "w"))
    words = json.load(open(js)); disp = text.split()
    # alinhar palavras exibidas com os tempos (mesma contagem na maioria dos casos)
    if len(words) != len(disp):
        dur = words[-1][1] if words else 2.0; n = len(disp); words = [(dur * i / n, dur * (i + 1) / n) for i in range(n)]
    with wave.open(wv) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a, list(zip(disp, [w[0] for w in words], [w[1] for w in words]))

def clip(src, t0, vis, n, fx):
    full = src.endswith(".webm")
    vf = f"scale=-2:{VH}:flags=lanczos,crop={VW}:{VH}:(iw-{VW})*{fx}:0,setpts={n / vis:.4f}*PTS,fps={FPS}"
    args = ["ffmpeg", "-v", "error"] + ([] if full else ["-ss", str(max(0, t0 - 2))]) + ["-i", src] + ["-ss", f"{(t0 if full else t0 - max(0, t0 - 2)) * n / vis:.3f}"] if False else None
    pre = 0.0 if full else max(0, t0 - 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(pre), "-i", src, "-vf", f"trim=start={t0 - pre:.3f},setpts=PTS-STARTPTS," + vf,
                          "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, VH, VW, 3)
    if len(a) < n: a = np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)])
    fn = f"/root/cards/k7clip_{hashlib.md5(f'{src}{t0}{n}{fx}'.encode()).hexdigest()[:8]}.raw"
    mm = np.memmap(fn, np.uint8, "w+", shape=(n, VH, VW, 3)); mm[:] = a[:n]; mm.flush()
    return np.memmap(fn, np.uint8, "r", shape=(n, VH, VW, 3))

# ---- montar blocos
BLOCKS = []
for kind, it in [("intro", S["intro"])] + [("item", x) for x in S["items"]] + [("outro", S["outro"])]:
    a, words = tts(it["say"]); n = int(len(a) / 48000 * FPS) + 12
    BLOCKS.append(dict(kind=kind, it=it, audio=a, words=words, n=n, clip=clip(it["src"], it["t"], it["d"], n, it.get("fx", 0.5))))
STARTS = np.cumsum([0] + [b["n"] for b in BLOCKS[:-1]]); TOTAL = int(sum(b["n"] for b in BLOCKS))
NI = len(S["items"])

def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255); return m

MASK = rounded(Image.new("RGB", (VW, VH)), 34)

def ctext(d, y, t, f, fill, sw=6, sf=(10, 5, 20)):
    d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=fill, stroke_width=sw, stroke_fill=sf)

def pill(d, y, t, col, f):
    tw = d.textlength(t, font=f); x0 = (W - tw) / 2 - 26
    d.rounded_rectangle((x0, y, x0 + tw + 52, y + f.size + 26), (f.size + 26) // 2, outline=col, width=4, fill=(15, 10, 25))
    d.text((x0 + 26, y + 11), t, font=f, fill="white")

def frame(n):
    bi = int(np.searchsorted(STARTS, n, side="right") - 1); b = BLOCKS[bi]; k = n - STARTS[bi]; it = b["it"]
    cf = Image.fromarray(np.asarray(b["clip"][min(k, b["n"] - 1)]))
    bg = cf.resize((W, int(W * VH / VW))).resize((W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (12, 6, 22)), 0.55)
    d = ImageDraw.Draw(bg)
    ctext(d, 60, "GTA 6 BRASIL", F(PD, 58), "white", 4)
    col = COLS[(bi - 1) % len(COLS)] if b["kind"] == "item" else (255, 64, 170)
    if b["kind"] == "item":
        idx = bi; t = f"COISA {idx:02d}/{NI:02d}"; f = F(IB, 30); d.text((70, 150), t, font=f, fill=(255, 214, 0))
        for j in range(NI):
            x = 70 + j * 46; d.rounded_rectangle((x, 196, x + 38, 206), 4, fill=(255, 214, 0) if j < idx else (70, 60, 90))
        a = min(1, k / 6); s = int(190 * (1.2 - 0.2 * a))
        ctext(d, 215, f"#{it['num']}", F(PD, s), col, 8)
        pill(d, 452, it["tag"], col, F(IX, 34))
    elif b["kind"] == "intro":
        for j, l in enumerate(it["title"]):
            ctext(d, 190 + j * 120, l, F(PD, 108), (255, 214, 0) if j == len(it["title"]) - 1 else "white", 7)
    else:
        ctext(d, 230, it["title"], F(PD, 170), (255, 214, 0), 8)
    if b["kind"] != "intro" or True:
        bg.paste(cf, ((W - VW) // 2, VY if b["kind"] != "intro" else VY + 40), MASK)
        y0 = VY if b["kind"] != "intro" else VY + 40
        d.rounded_rectangle(((W - VW) // 2 - 3, y0 - 3, (W + VW) // 2 + 3, y0 + VH + 3), 36, outline=col, width=5)
    # legenda karaokê (grupos de até 3 palavras)
    tsec = k / FPS - 0.25; words = b["words"]; groups = [words[i:i + 3] for i in range(0, len(words), 3)]
    gi = 0
    for i, g in enumerate(groups):
        if tsec >= g[0][1] - 0.05: gi = i
    g = groups[gi] if groups else []
    if g and tsec > -0.2:
        f = F(AN, 92); txt = " ".join(w[0].upper() for w in g)
        while d.textlength(txt, font=f) > 1000: f = F(AN, f.size - 6)
        x = (W - d.textlength(txt, font=f)) / 2; y = 1330
        for w, s0, s1 in g:
            wt = w.upper() + " "; on = s0 <= tsec + 0.05
            d.text((x, y), wt, font=f, fill=(255, 214, 0) if on and tsec < s1 + 0.15 else "white", stroke_width=7, stroke_fill=(10, 5, 20))
            x += d.textlength(wt, font=f)
    if b["kind"] == "outro":
        pill(d, 1520, it["sub"], (255, 64, 170), F(IX, 36))
    cr = S["credit"]; d.text(((W - d.textlength(cr, font=F(IM, 24))) / 2, H - 110), cr, font=F(IM, 24), fill=(220, 220, 230))
    return bg

def audio(path):
    sr = 48000; L = int(TOTAL / FPS * sr)
    with wave.open(S["music"]) as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; ch = w.getnchannels(); msr = w.getframerate()
    m = m.reshape(-1, ch).mean(1)
    if msr != sr: m = np.interp(np.arange(0, len(m), msr / sr), np.arange(len(m)), m)
    m = np.tile(m, int(np.ceil(L / len(m))))[:L]; fade = np.ones(L); fl = int(1.2 * sr); fade[-fl:] = np.linspace(1, 0, fl)
    out = m * 0.25 * fade
    for b, s0 in zip(BLOCKS, STARTS):
        s = int(s0 / FPS * sr) + int(0.25 * sr); e = min(L, s + len(b["audio"])); out[s:e] += b["audio"][:e - s] * 1.1
        wl = int(0.25 * sr); wh = 0.12 * np.random.randn(wl) * np.hanning(wl); s2 = int(s0 / FPS * sr); out[s2:s2 + wl] += wh[:max(0, min(wl, L - s2))]
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

if len(sys.argv) > 2:
    ims = [frame(int(x)).resize((270, 480)) for x in sys.argv[2:]]
    o = Image.new("RGB", (270 * len(ims), 480))
    for j, im in enumerate(ims): o.paste(im, (j * 270, 0))
    o.save("/root/cards/k7_prev.jpg"); print(TOTAL, [int(s) for s in STARTS]); sys.exit()
audio("/root/cards/k7.wav")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "/root/cards/k7.wav",
                      "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-maxrate", "16M", "-bufsize", "32M",
                      "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", S["out"]], stdin=subprocess.PIPE)
for n in range(TOTAL): p.stdin.write(frame(n).convert("RGB").tobytes())
p.stdin.close(); p.wait(); print("ok", TOTAL)
for f in os.listdir("/root/cards"):
    if f.startswith("k7clip_"): os.remove("/root/cards/" + f)
