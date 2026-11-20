"""End-to-end browser checks for the Mimo demo (Playwright + Chrome/Chromium).

Run from repo root:  python3 demo/tests/test_e2e.py
Skips cleanly if Playwright or a browser is unavailable.
"""
from __future__ import annotations

import functools
import http.server
import json
import os
import threading
import unittest

DEMO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@unittest.skipIf(sync_playwright is None, "playwright not installed")
class DemoE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(_Quiet, directory=DEMO)
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(channel=os.environ.get("MIMO_BROWSER_CHANNEL", "chrome"))
        except Exception:
            try:
                cls.browser = cls.pw.chromium.launch()
            except Exception as e:  # pragma: no cover
                cls.pw.stop(); cls.httpd.shutdown()
                raise unittest.SkipTest(f"no browser available: {e}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.httpd.shutdown()

    def page(self, width=1440):
        ctx = self.browser.new_context(viewport={"width": width, "height": 900})
        pg = ctx.new_page()
        pg.external, pg.errors = [], []
        pg.on("request", lambda r: pg.external.append(r.url)
              if not r.url.startswith(self.base) and not r.url.startswith("data:") else None)
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        return pg

    def events(self, pg):
        return json.loads(pg.evaluate("localStorage.getItem('mimo.events.v1') || '[]'"))

    def test_landing_variants_share_design(self):
        pg = self.page()
        pg.goto(self.base + "/index.html?variant=A")
        a_h = pg.inner_text("h1"); a_cls = pg.evaluate("[...document.querySelectorAll('main *')].map(e=>e.tagName+e.className).join('|')")
        pg.goto(self.base + "/index.html?variant=B")
        b_h = pg.inner_text("h1"); b_cls = pg.evaluate("[...document.querySelectorAll('main *')].map(e=>e.tagName+e.className).join('|')")
        self.assertIn("nobody was watching", a_h)
        self.assertIn("never intended", b_h)
        self.assertEqual(a_cls, b_cls, "variant DOM structure differs")
        self.assertIn("PILOT", pg.inner_text("#pilot-cta").upper())
        self.assertIn("synthetic data", pg.inner_text(".disclosure").lower())
        self.assertEqual(pg.external, []); self.assertEqual(pg.errors, [])

    def test_unforced_assignment_is_stable_and_automation_is_excluded(self):
        pg = self.page()
        pg.goto(self.base + "/index.html")
        v1 = pg.get_attribute("html", "data-variant")
        pg.reload()
        self.assertEqual(v1, pg.get_attribute("html", "data-variant"))
        ev = [e for e in self.events(pg) if e["event"] == "landing_view"]
        self.assertEqual(len(ev), 2)
        self.assertTrue(all(e["excluded"] and e["exclude_reason"] == "automation" for e in ev))

    def test_full_demo_flow_emits_events_and_labels_simulation(self):
        pg = self.page()
        pg.goto(self.base + "/index.html")
        pg.click("#primary-cta")
        pg.wait_for_selector(".scene[data-scene=request].active")
        for _ in range(4):
            pg.click("#next")
        self.assertTrue(pg.is_visible(".scene[data-scene=intervene].active"))
        self.assertIn("ENGINE OUTPUT", pg.inner_text("#finding-card"))
        pg.click("[data-mode=enforce]")
        self.assertIn("CONCEPT SIMULATION", pg.inner_text("[data-pane=enforce]").upper())
        self.assertIn("DENY PENDING APPROVAL", pg.inner_text("#gate-trace"))
        pg.click("[data-gate=deny]")
        self.assertIn("Simulated", pg.inner_text("#gate-result"))
        pg.click("#next")
        pg.click("#open-drawer")
        pg.wait_for_selector("#drawer.open")
        self.assertIn("Completion is not evidenced", pg.inner_text("#drawer"))
        pg.keyboard.press("Escape")
        pg.click("#next")
        self.assertIn("Know what your AI agents are actually allowed to do.", pg.inner_text("#h-end"))
        pg.click("#end-pilot-cta")
        pg.wait_for_url("**/pilot.html*")
        pg.fill("input[name=email]", "lead@corp.example")
        pg.select_option("select[name=role]", "security")
        pg.select_option("select[name=agents]", "production")
        pg.click("form button[type=submit]")
        names = [e["event"] for e in self.events(pg)]
        for n in ["landing_view", "demo_start", "evidence_open", "demo_complete", "pilot_cta_click", "qualified_request"]:
            self.assertIn(n, names)
        self.assertNotIn("lead@corp.example", pg.evaluate("localStorage.getItem('mimo.events.v1')"))
        self.assertEqual(pg.external, []); self.assertEqual(pg.errors, [])

    def test_attempt_vs_completion_visible(self):
        pg = self.page()
        pg.goto(self.base + "/demo.html#gap")
        txt = pg.inner_text("#states")
        self.assertIn("TC-7782", txt)
        self.assertIn("Unknown", txt)
        self.assertIn("UNKNOWN", pg.inner_text("#col-o"))

    def test_mobile_has_no_horizontal_overflow(self):
        pg = self.page(width=360)
        for url in ["index.html", "pilot.html"] + [f"demo.html#{s}" for s in
                    ["request", "tools", "attempt", "gap", "intervene", "proof", "end"]]:
            pg.goto(self.base + "/" + url)
            pg.wait_for_timeout(150)
            over = pg.evaluate("""() => [...document.querySelectorAll('main *, header *')]
              .filter(e => !e.closest('.rail,.drawer,.scroll-x'))
              .filter(e => { const r = e.getBoundingClientRect(); return r.width && r.right > innerWidth + 1; }).length""")
            self.assertEqual(over, 0, url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
