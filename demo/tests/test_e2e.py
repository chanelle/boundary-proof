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
        self.assertIn("30-MINUTE MIMO DISCOVERY CALL", pg.inner_text("#pilot-cta").upper())
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
        pg.wait_for_selector(".scene[data-scene=hook].active")
        pg.wait_for_selector("#hook-lines li:nth-child(4).show")
        self.assertIn("We don't know", pg.inner_text("#hook-lines"))
        for _ in range(5):
            pg.click("#next")
        self.assertTrue(pg.is_visible(".scene[data-scene=intervene].active"))
        self.assertIn("ENGINE OUTPUT", pg.inner_text("#finding-card"))
        self.assertIn("U-attempt-send_external", pg.inner_text("#finding-card"))
        triad = pg.inner_text("#triad").upper()
        for k in ("RISK SEVERITY", "EVIDENCE CONFIDENCE", "ACTION OUTCOME", "COMPLETION UNKNOWN", "NOT DETECTED LIVE"):
            self.assertIn(k, triad)
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
        href = pg.get_attribute("#book-cta", "href")
        self.assertTrue(href.startswith("https://cal.com/chanelleh/30min?"), href)
        self.assertIn("utm_content=variant_", href)
        self.assertIn("utm_term=excluded_automation", href)  # Playwright is automation: tagged, not counted
        self.assertEqual(pg.get_attribute("#book-cta", "target"), "_blank")
        self.assertIn("Nothing is booked until you confirm", pg.inner_text("#request"))
        pg.evaluate("document.getElementById('book-cta').removeAttribute('href')")  # stay offline in tests
        pg.click("#book-cta")
        events = self.events(pg)
        names = [e["event"] for e in events]
        for n in ["landing_view", "demo_start", "evidence_open", "demo_complete", "pilot_cta_click"]:
            self.assertIn(n, names)
        self.assertNotIn("qualified_request", names)  # only an operator can log that
        self.assertTrue(any(e["props"].get("handoff") == "calcom" for e in events))
        self.assertEqual(pg.external, []); self.assertEqual(pg.errors, [])

    def test_attempt_vs_completion_visible(self):
        pg = self.page()
        pg.goto(self.base + "/demo.html#gap")
        txt = pg.inner_text("#states")
        self.assertIn("TC-7782", txt)
        self.assertIn("Unknown", txt)
        self.assertIn("UNKNOWN", pg.inner_text("#col-o"))
        self.assertIn("U-attempt-send_external", txt)
        pg.goto(self.base + "/demo.html#proof")
        self.assertIn("U-ATTEMPT-SEND_EXTERNAL", pg.inner_text("#unknowns").upper())
        self.assertNotIn("Demo annotation", pg.inner_text("#unknowns"))

    def test_mobile_has_no_horizontal_overflow(self):
        pg = self.page(width=360)
        for url in ["index.html", "pilot.html"] + [f"demo.html#{s}" for s in
                    ["hook", "request", "tools", "attempt", "gap", "intervene", "proof", "end"]]:
            pg.goto(self.base + "/" + url)
            pg.wait_for_timeout(150)
            over = pg.evaluate("""() => [...document.querySelectorAll('main *, header *')]
              .filter(e => !e.closest('.rail,.drawer,.scroll-x'))
              .filter(e => { const r = e.getBoundingClientRect(); return r.width && r.right > innerWidth + 1; }).length""")
            self.assertEqual(over, 0, url)


@unittest.skipIf(sync_playwright is None, "playwright not installed")
class ProductionBuildE2E(unittest.TestCase):
    """Runs the built demo/dist/mimo/ with the Simple Analytics script stubbed."""

    @classmethod
    def setUpClass(cls):
        import subprocess, sys
        root = os.path.dirname(DEMO)
        subprocess.run([sys.executable, os.path.join(DEMO, "tools", "build_site.py")], check=True, cwd=root,
                       stdout=subprocess.DEVNULL)
        handler = functools.partial(_Quiet, directory=os.path.join(DEMO, "dist"))
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}/mimo"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(channel=os.environ.get("MIMO_BROWSER_CHANNEL", "chrome"))
        except Exception:
            cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.httpd.shutdown()

    def page(self, human=True):
        ua = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
              "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1") if human else None
        ctx = self.browser.new_context(viewport={"width": 390, "height": 844}, user_agent=ua)
        if human:  # look like a real visitor so the event is counted
            ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
        pg = ctx.new_page()
        stub = "window.__sa=[];window.sa_event=function(n){window.__sa.push(n)};"
        pg.route("https://scripts.simpleanalyticscdn.com/**", lambda r: r.fulfill(status=200, body=stub, content_type="text/javascript"))
        pg.route("https://queue.simpleanalyticscdn.com/**", lambda r: r.fulfill(status=204, body=""))
        return pg

    def test_counted_visitor_sends_one_event_per_variant(self):
        pg = self.page()
        pg.goto(self.base + "/index.html"); pg.wait_for_timeout(400)
        v = pg.get_attribute("html", "data-variant").lower()
        pg.reload(); pg.wait_for_timeout(400)
        sent = pg.evaluate("(window.__sa||[]).concat((window.sa_event&&window.sa_event.q||[]).map(a=>a[0]))")
        # first view sent it (queued or delivered); the reload must not send it again
        self.assertLessEqual(sent.count(f"mimo_landing_view_{v}"), 1)
        pg.goto(self.base + "/index.html"); pg.wait_for_timeout(500)
        self.assertEqual(pg.evaluate("(window.__sa||[]).length"), 0)  # third view: still nothing new
        stored = pg.evaluate("JSON.parse(localStorage.getItem('mimo.sa.sent.v1')||'{}')")
        self.assertEqual(list(stored), [f"mimo_landing_view_{v}"])
        pg.goto(self.base + "/pilot.html")
        href = pg.get_attribute("#book-cta", "href")
        self.assertIn(f"utm_content=variant_{v.upper()}", href)
        self.assertIn("utm_term=counted", href)

    def test_excluded_visitor_sends_nothing(self):
        pg = self.page(human=False)
        pg.goto(self.base + "/index.html"); pg.wait_for_timeout(400)
        self.assertEqual(pg.evaluate("localStorage.getItem('mimo.sa.sent.v1')"), None)

    def test_forced_variant_sends_nothing(self):
        pg = self.page()
        pg.goto(self.base + "/index.html?variant=B"); pg.wait_for_timeout(400)
        self.assertEqual(pg.evaluate("localStorage.getItem('mimo.sa.sent.v1')"), None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
