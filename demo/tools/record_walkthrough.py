"""Record the 70-second autoplay walkthrough to video (16:9; 1600x900 viewport, MP4 upscaled to 1920x1080).

Run from repo root (needs Playwright + Chrome/Chromium; ffmpeg for MP4):
    python3 demo/tools/record_walkthrough.py
Output: demo/video/out/walkthrough.webm and walkthrough.mp4 (git-ignored).
The page is opened with ?autoplay=1, which tags the session as a recording
and excludes its events from experiment metrics.
"""
from __future__ import annotations

import functools
import http.server
import os
import shutil
import subprocess
import threading

from playwright.sync_api import sync_playwright

DEMO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DEMO, "video", "out")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=DEMO))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/demo.html?autoplay=1"
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1600, "height": 900},
                                  device_scale_factor=1,
                                  record_video_dir=OUT, record_video_size={"width": 1600, "height": 900})
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_selector("html[data-autoplay-done='1']", timeout=90_000)
        page.wait_for_timeout(1200)
        video = page.video
        ctx.close()
        browser.close()
        webm = os.path.join(OUT, "walkthrough.webm")
        shutil.move(video.path(), webm)
    httpd.shutdown()
    print("wrote", os.path.relpath(webm))
    if shutil.which("ffmpeg"):
        mp4 = os.path.join(OUT, "walkthrough.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", webm, "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-vf", "scale=1920:1080:flags=lanczos", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", mp4], check=True)
        print("wrote", os.path.relpath(mp4))


if __name__ == "__main__":
    main()
