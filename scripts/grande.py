"""Montagem rápida 'Está chegando o grande dia' (faixa 16:9 no meio, texto fixo em cima)."""
import subprocess, os
from PIL import Image, ImageDraw, ImageFont
W, H, FPS = 1080, 1920, 30
P = "/root/proxy/"
CUTS = [("lt", 44.6, .7), ("rob", 8.6, .7), ("ft", 8.3, .7), ("lt", 34.9, .7), ("lt", 46.6, .6), ("ft", 41.8, .6),
        ("lt", 18.6, .6), ("rob", 36.6, .6), ("lt", 49.1, .6), ("ft", 17.7, .6), ("lt", 60.9, .6), ("rob", 43.2, .6),
        ("lt", 72.0, .6), ("lt", 66.7, .8), ("lt", 78.0, 1.6)]
TXT = os.environ.get("TXT", "ESTÁ CHEGANDO O GRANDE DIA 🔥").replace(" 🔥", "")
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", 66)
lines = ["ESTÁ CHEGANDO O", "GRANDE DIA"] if "GRANDE DIA" in TXT else [TXT]
y = 470
for l in lines:
    d.text(((W - d.textlength(l, font=f)) / 2, y), l, font=f, fill="white"); y += 84
fire = Image.open("/root/cards/fire.png").convert("RGBA").resize((70, 70)) if os.path.exists("/root/cards/fire.png") else None
if fire: ov.alpha_composite(fire, (int((W + d.textlength(lines[-1], font=f)) / 2 + 14), y - 84 + 4))
# selo do perfil abaixo do vídeo
f2 = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 34); t = "@gtav1.br"; tw = d.textlength(t, font=f2)
av = Image.open("/root/cards/avatar.jpg").convert("RGB").resize((64, 64)); m = Image.new("L", (64, 64), 0); ImageDraw.Draw(m).ellipse((0, 0, 63, 63), fill=255)
x0 = (W - (tw + 84)) / 2; d.rounded_rectangle((x0 - 14, 1300, x0 + tw + 98, 1380), 40, fill=(20, 20, 24, 230))
ov.paste(av, (int(x0), 1308), m); d.text((x0 + 80, 1318), t, font=f2, fill="white")
ov.save("/root/cards/grande_ov.png")
parts = []
for i, (s, t0, dur) in enumerate(CUTS):
    o = f"/root/cards/gr_{i:02d}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-i", P + s + ".mp4", "-t", str(dur), "-vf",
                    f"scale={W}:-2:flags=lanczos,pad={W}:{H}:0:(oh-ih)/2:black,fps={FPS}", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-an", o], check=True)
    parts.append(o)
open("/root/cards/gr_list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "/root/cards/gr_list.txt", "-i", "/root/cards/grande_ov.png",
                "-filter_complex", "[0:v][1:v]overlay=0:0", "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-an", "/root/cards/gr_v.mp4"], check=True)
d_ = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "/root/cards/gr_v.mp4"], capture_output=True, text=True).stdout)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "/root/cards/gr_v.mp4", "-stream_loop", "-1", "-i", os.environ.get("MUS", "/root/musica/m05_phonk.wav"),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", f"afade=in:d=0.2,afade=out:st={d_ - 1:.2f}:d=1,loudnorm=I=-14:TP=-1.5:LRA=11",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{d_:.2f}", "-movflags", "+faststart", os.environ.get("OUT", "/root/cards/GRANDE.mp4")], check=True)
for p in parts: os.remove(p)
print("ok", d_)
