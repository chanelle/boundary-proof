"""Render the Mimo product film (demo/motion/index.html) frame by frame.

The page is a pure function of time (window.seek(t)), so every frame is exact:
no dropped frames, no screen-recording judder.

Run from repo root (needs Playwright + Chrome/Chromium and ffmpeg):
    python3 demo/tools/render_motion.py            # both cuts
    python3 demo/tools/render_motion.py 16x9       # one cut
Output (git-ignored): demo/video/out/mimo-film-16x9.mp4 (1920x1080),
                      demo/video/out/mimo-film-4x5.mp4  (1080x1350)
"""
from __future__ import annotations

import functools
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

DEMO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DEMO, "video", "out")
FPS = 30
FORMATS = {"16x9": (1920, 1080), "4x5": (1080, 1350)}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def render(name: str, w: int, h: int, base: str) -> str:
    frames = tempfile.mkdtemp(prefix=f"mimo-{name}-")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.goto(f"{base}/motion/index.html?render=1")
        page.wait_for_function("typeof window.seek === 'function'")
        page.evaluate("document.fonts.ready")
        duration = page.evaluate("window.MOTION_DURATION")
        n = int(duration * FPS)
        for i in range(n + 1):
            page.evaluate(f"seek({i / FPS})")
            page.screenshot(path=os.path.join(frames, f"f{i:05d}.jpg"), type="jpeg", quality=92)
            if i % (FPS * 10) == 0:
                print(f"  {name}: {i / FPS:.0f}s / {duration}s", flush=True)
        browser.close()
    os.makedirs(OUT, exist_ok=True)
    mp4 = os.path.join(OUT, f"mimo-film-{name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i",
                    os.path.join(frames, "f%05d.jpg"), "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(frames, ignore_errors=True)
    return mp4


def main() -> None:
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=DEMO))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    for name in sys.argv[1:] or FORMATS:
        print("wrote", os.path.relpath(render(name, *FORMATS[name], base)))
    httpd.shutdown()


if __name__ == "__main__":
    main()
