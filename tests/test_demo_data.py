"""The demo's engine data must be exactly what the real engine produces.

If this fails, run: python3 demo/build_demo_data.py
"""
from __future__ import annotations

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "demo"))

import build_demo_data  # noqa: E402


class DemoDataTests(unittest.TestCase):
    def setUp(self):
        with open(build_demo_data.OUT_JSON) as fh:
            self.committed = json.load(fh)
        self.fresh = json.loads(json.dumps(build_demo_data.build(), sort_keys=True))

    def test_committed_json_matches_fresh_engine_run(self):
        self.assertEqual(self.committed, self.fresh)

    def test_js_wrapper_matches_json(self):
        with open(build_demo_data.OUT_JS) as fh:
            js = fh.read()
        payload = js.split("window.MIMO_ENGINE = ", 1)[1].rstrip().rstrip(";")
        self.assertEqual(json.loads(payload), self.committed)

    def test_attempt_is_not_converted_to_observed_yes(self):
        a = self.fresh["assessment"]
        row = next(r for r in a["matrix"] if r["verb"] == "send_external")
        self.assertEqual((row["intended"], row["configured"], row["observed"]),
                         ("NO", "YES", "UNKNOWN"))

    def test_gap_finding_is_evidence_backed(self):
        a = self.fresh["assessment"]
        f = next(f for f in a["findings"] if f["mismatch"]["verb"] == "send_external")
        self.assertEqual(f["mismatch"]["mismatch_class"], "CONFIGURED_EXCEEDS_INTENDED")
        self.assertIn("EV-05", f["evidence_ids"])
        ev_ids = {e["id"] for e in a["evidence"]}
        self.assertTrue(set(f["evidence_ids"]) <= ev_ids)

    def test_every_evidence_source_is_marked_synthetic(self):
        for e in self.fresh["assessment"]["evidence"]:
            self.assertIn("synthetic", e["source"].lower(), e["id"])

    def test_no_consequential_test_was_approved(self):
        gates = self.fresh["assessment"]["gates"]
        self.assertFalse(any(g["gate"] == "G3" and g["decision"] in ("approved", "policy_authorized")
                             for g in gates))


if __name__ == "__main__":
    unittest.main()
