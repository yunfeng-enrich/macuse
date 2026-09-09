"""Capture two windows by owner at a fixed fps into PNG frames. Immune to overlap and cursor."""
import sys, time, os, signal
import Quartz
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGWindowListExcludeDesktopElements, kCGNullWindowID
from Quartz import CGWindowListCreateImage, CGRectNull, kCGWindowListOptionIncludingWindow, kCGWindowImageBoundsIgnoreFraming
from Foundation import NSURL
out, fps, duration = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
owners = sys.argv[4:]
os.makedirs(out, exist_ok=True)
stop = False
signal.signal(signal.SIGINT, lambda *_: globals().__setitem__("stop", True))
def find(owner):
    best = None
    for w in CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements, kCGNullWindowID):
        if w.get("kCGWindowOwnerName") == owner and w.get("kCGWindowLayer") == 0 and w["kCGWindowBounds"]["Height"] > 200:
            best = w["kCGWindowNumber"]; break
    return best
def save(img, path):
    dest = Quartz.CGImageDestinationCreateWithURL(NSURL.fileURLWithPath_(path), "public.png", 1, None)
    Quartz.CGImageDestinationAddImage(dest, img, None); Quartz.CGImageDestinationFinalize(dest)
t0 = time.time(); i = 0; period = 1 / fps
while not stop and time.time() - t0 < duration:
    ts = time.time() - t0
    for k, owner in enumerate(owners):
        wid = find(owner)
        if not wid: continue
        img = CGWindowListCreateImage(CGRectNull, kCGWindowListOptionIncludingWindow, wid, kCGWindowImageBoundsIgnoreFraming)
        if img: save(img, f"{out}/w{k}_{i:05d}.png")
    with open(f"{out}/times.txt", "a") as f: f.write(f"{i} {ts:.3f}\n")
    i += 1
    time.sleep(max(0, (t0 + i * period) - time.time()))
print("frames", i)
