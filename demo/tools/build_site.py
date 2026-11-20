"""Build the production copy of the Mimo demo for becomingbeta.com/mimo/.

Run from repo root:  python3 demo/tools/build_site.py
Output: demo/dist/mimo/  (git-ignored). Upload with deploy/deploy_mimo.sh.

What differs from the local demo:
- Adds Simple Analytics (already used on becomingbeta.com) and the
  privacy-scoped adapter js/sa-adapter.js. The local demo stays offline.
- Copies only what the page serves: no tests, tools, docs, video or sources.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys

DEMO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DEMO, "dist", "mimo")
PAGES = ["index.html", "demo.html", "pilot.html"]
DIRS = ["css", "js", "fonts", "data"]

SA_HEAD = (
    '<script>window.sa_event=window.sa_event||function(){var a=[].slice.call(arguments);'
    'window.sa_event.q?window.sa_event.q.push(a):window.sa_event.q=[a]};</script>\n'
)
SA_BODY = (
    '<script async src="https://scripts.simpleanalyticscdn.com/latest.js"></script>\n'
    '<noscript><img src="https://queue.simpleanalyticscdn.com/noscript.gif" alt="" '
    'referrerpolicy="no-referrer-when-downgrade"></noscript>\n'
)


def build() -> list[str]:
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for d in DIRS:
        shutil.copytree(os.path.join(DEMO, d), os.path.join(OUT, d),
                        ignore=shutil.ignore_patterns("*.txt") if d != "fonts" else None)
    for page in PAGES:
        with open(os.path.join(DEMO, page), encoding="utf-8") as fh:
            html = fh.read()
        assert '<script src="js/ui-common.js"></script>' in html, page
        html = html.replace("</head>", SA_HEAD + "</head>", 1)
        html = html.replace('<script src="js/ui-common.js"></script>',
                            '<script src="js/sa-adapter.js"></script>\n<script src="js/ui-common.js"></script>', 1)
        html = html.replace("</body>", SA_BODY + "</body>", 1)
        with open(os.path.join(OUT, page), "w", encoding="utf-8") as fh:
            fh.write(html)
    files = []
    for base, _, names in os.walk(OUT):
        for n in names:
            files.append(os.path.relpath(os.path.join(base, n), OUT))
    files.sort()
    with open(os.path.join(OUT, "..", "MANIFEST.txt"), "w") as fh:
        for f in files:
            with open(os.path.join(OUT, f), "rb") as b:
                fh.write(f"{hashlib.md5(b.read()).hexdigest()}  {f}\n")
    return files


if __name__ == "__main__":
    fs = build()
    print(f"built demo/dist/mimo/ with {len(fs)} files")
    sys.exit(0)
