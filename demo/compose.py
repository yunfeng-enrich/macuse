"""Compose terminal (w0) and Mac (w1) frames side by side into a PNG sequence for ffmpeg."""
import sys, os, glob
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
TERM_TITLE, VM_TOOLBAR = 28, 52   # rows to trim off the top of each window
GAP, PAD, BG = 16, 12, (28, 28, 32)
idx = sorted(int(l.split()[0]) for l in open(f"{src}/times.txt"))
last0 = last1 = None; n = 0
for i in idx:
    p0, p1 = f"{src}/w0_{i:05d}.png", f"{src}/w1_{i:05d}.png"
    if os.path.exists(p0): last0 = Image.open(p0).convert("RGB")
    if os.path.exists(p1): last1 = Image.open(p1).convert("RGB")
    if last0 is None or last1 is None: continue
    t = last0.crop((0, TERM_TITLE, last0.width, last0.height)); v = last1.crop((0, VM_TOOLBAR, last1.width, last1.height))
    h = max(t.height, v.height)
    canvas = Image.new("RGB", (PAD + t.width + GAP + v.width + PAD, h + 2 * PAD), BG)
    canvas.paste(t, (PAD, PAD)); canvas.paste(v, (PAD + t.width + GAP, PAD))
    canvas.save(f"{out}/f_{n:05d}.png"); n += 1
print("composed", n, "frames", canvas.size)
