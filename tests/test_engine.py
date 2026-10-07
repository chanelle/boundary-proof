"""BoundaryProof v0.1 tests — planner safety, HITL ledger, remediation,
verification, and end-to-end fixture runs."""
import json
import os
import unittest

from boundaryproof import planner, hitl, engine
from boundaryproof import remediation as remediation_mod
from boundaryproof import verification as verification_mod
from boundaryproof.models import Finding, Mismatch, Remediation

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures")
POL = os.path.join(os.path.dirname(__file__), "..", "policies")

AUTO = {"G1": {"by": "t", "approve": True},
        "G2": {"by": "t", "approve": True},
        "G3": {"by": "t", "approve": False},
        "G4": {"by": "t", "approve": True}}


def load(name):
    with open(os.path.join(FIX, name)) as fh:
        return json.load(fh)


class TestPlannerSafety(unittest.TestCase):
    def test_consequential_production_classification(self):
        t = planner.classify({"name": "x", "verbs": ["delete"],
                              "method": "m", "target": "production"})
        self.assertEqual(t.classification, "CONSEQUENTIAL")

    def test_consequential_sandbox_is_safe(self):
        t = planner.classify({"name": "x", "verbs": ["delete"],
                              "method": "m", "target": "sandbox"})
        self.assertEqual(t.classification, "SANDBOX_SAFE")

    def test_read_only(self):
        t = planner.classify({"name": "x", "verbs": ["read"],
                              "method": "m", "target": "production"})
        self.assertEqual(t.classification, "READ_ONLY")

    def test_g3_gate_blocks_without_approval(self):
        t = planner.classify({"name": "x", "verbs": ["send_external"],
                              "method": "m", "target": "production"})
        planner.authorize(t, gate_g3_approved=False)
        self.assertFalse(t.authorized)
        self.assertIn("G3", t.blocked_reason)

    def test_g3_gate_allows_with_approval(self):
        t = planner.classify({"name": "x", "verbs": ["send_external"],
                              "method": "m", "target": "production"})
        planner.authorize(t, gate_g3_approved=True)
        self.assertTrue(t.authorized)


class TestHitl(unittest.TestCase):
    def test_hir_math_and_target(self):
        ledger = hitl.HitlLedger()
        ledger.decide(hitl.GateDecision(gate="G1", approved=True,
                                       decided_by="Dana", minutes=2.0))
        ledger.policy_authorize("G2", "auto")
        ledger.step(18)
        m = ledger.metrics(20.0)
        self.assertEqual(m["human_active_minutes"], 2.0)
        self.assertEqual(m["human_interventions"], 1)  # policy auth not counted
        self.assertAlmostEqual(m["human_intervention_ratio"], 0.1)
        self.assertTrue(m["hir_target_met"])

    def test_hir_target_can_fail(self):
        ledger = hitl.HitlLedger()
        ledger.decide(hitl.GateDecision(gate="G1", approved=True,
                                       decided_by="Dana", minutes=15.0))
        m = ledger.metrics(20.0)
        self.assertFalse(m["hir_target_met"])

    def test_gate_context_is_least_privilege(self):
        ctx = {"agent_name": "a", "intent_text": "t", "allowed_verbs": ["read"],
               "denied_verbs": [], "finding_count": 99, "severities": {}}
        scoped = hitl.gate_context("G2", ctx)
        self.assertNotIn("finding_count", scoped)
        self.assertIn("intent_text", scoped)

    def test_unknown_gate_rejected(self):
        ledger = hitl.HitlLedger()
        with self.assertRaises(ValueError):
            ledger.decide(hitl.GateDecision(gate="G9", approved=True, decided_by="x"))


class TestRemediation(unittest.TestCase):
    def _finding(self, cls="OBSERVED_EXCEEDS_INTENDED", verb="execute"):
        m = Mismatch(id="M-01", verb=verb, mismatch_class=cls,
                     intended="NO", configured="YES", observed="YES", detail="d")
        return Finding(id="F-01", title="t", severity="High", confidence="High",
                       likelihood="Proven", blast_radius="Significant", mismatch=m)

    def test_draft_is_concrete(self):
        f = remediation_mod.draft(self._finding())
        self.assertIsNotNone(f.remediation)
        self.assertTrue(len(f.remediation.recommendation) > 40)
        self.assertTrue(len(f.remediation.verification_test) > 20)

    def test_banned_phrases_rejected(self):
        # monkey-patch a bad template to prove the guard fires
        orig = remediation_mod._TEMPLATES["EVIDENCE_GAP"]["recommendation"]
        remediation_mod._TEMPLATES["EVIDENCE_GAP"]["recommendation"] = \
            "improve security generally"
        try:
            with self.assertRaises(ValueError):
                remediation_mod.draft(self._finding("EVIDENCE_GAP", "read"))
        finally:
            remediation_mod._TEMPLATES["EVIDENCE_GAP"]["recommendation"] = orig


class TestVerification(unittest.TestCase):
    def _finding(self):
        m = Mismatch(id="M-01", verb="deploy", mismatch_class="CONFIGURED_EXCEEDS_INTENDED",
                     intended="NO", configured="YES", observed="UNKNOWN", detail="d")
        f = Finding(id="F-01", title="t", severity="High", confidence="High",
                    likelihood="Plausible", blast_radius="Significant", mismatch=m)
        f.remediation = Remediation(recommendation="r", verification_test="v",
                                    status="applied")
        return f

    def test_retest_no_passes(self):
        f = self._finding()
        verification_mod.verify([f], {"F-01": {"verb": "deploy", "result": "NO",
                                              "evidence_ref": "EV-9"}})
        self.assertEqual(f.verification, "passed")

    def test_retest_yes_fails(self):
        f = self._finding()
        verification_mod.verify([f], {"F-01": {"verb": "deploy", "result": "YES",
                                              "evidence_ref": "EV-9"}})
        self.assertEqual(f.verification, "failed")

    def test_no_retest_stays_pending(self):
        f = self._finding()
        verification_mod.verify([f], {})
        self.assertEqual(f.verification, "pending")


class TestFixturesEndToEnd(unittest.TestCase):
    def test_f01_aligned_is_clean(self):
        a = engine.run(load("f01_aligned.json"), policy=AUTO)
        self.assertEqual(a.findings, [])
        self.assertEqual(a.unknowns, [])
        self.assertTrue(a.metrics["hir_target_met"])

    def test_f02_expected_findings(self):
        a = engine.run(load("f02_observed_exceeds_intended.json"), policy=AUTO)
        by_sev = {}
        for f in a.findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        self.assertEqual(by_sev.get("Critical"), 1)
        self.assertEqual(by_sev.get("High"), 3)
        self.assertEqual(by_sev.get("Medium"), 2)
        self.assertEqual(len(a.attack_paths), 2)
        classes = {f.mismatch.mismatch_class for f in a.findings}
        self.assertIn("UNDELEGATED_AUTHORITY", classes)
        self.assertIn("DELEGATION_EXPANSION", classes)
        # every finding cites real evidence
        for f in a.findings:
            self.assertTrue(f.evidence_ids)

    def test_f03_config_exceeds_unverified(self):
        a = engine.run(load("f03_config_exceeds_unverifiable.json"), policy=AUTO)
        classes = [f.mismatch.mismatch_class for f in a.findings]
        self.assertIn("CONFIGURED_EXCEEDS_INTENDED", classes)
        self.assertTrue(any(f.likelihood == "Plausible" for f in a.findings))
        self.assertIn("U-write", [u.id for u in a.unknowns])

    def test_f04_observed_violates_configured(self):
        a = engine.run(load("f04_config_restricted_observed_violates.json"), policy=AUTO)
        classes = [f.mismatch.mismatch_class for f in a.findings]
        self.assertIn("OBSERVED_VIOLATES_CONFIGURED", classes)

    def test_f05_insufficient_evidence_holds_back(self):
        a = engine.run(load("f05_insufficient_evidence.json"), policy=AUTO)
        self.assertEqual(a.findings, [])  # nothing invented
        self.assertGreaterEqual(len(a.unknowns), 5)

    def test_f06_delegation_expansion(self):
        a = engine.run(load("f06_delegated_exceeds_parent.json"), policy=AUTO)
        classes = [f.mismatch.mismatch_class for f in a.findings]
        self.assertIn("DELEGATION_EXPANSION", classes)

    def test_f07_remediation_verified(self):
        a = engine.run(load("f07_remediation_verified.json"), policy=AUTO)
        self.assertEqual(len(a.findings), 1)
        self.assertEqual(a.findings[0].verification, "passed")

    def test_f08_remediation_failed(self):
        a = engine.run(load("f08_remediation_failed.json"), policy=AUTO)
        self.assertEqual(len(a.findings), 1)
        self.assertEqual(a.findings[0].verification, "failed")

    def test_g1_denied_halts(self):
        pol = dict(AUTO)
        pol["G1"] = {"by": "t", "approve": False}
        with self.assertRaises(PermissionError):
            engine.run(load("f01_aligned.json"), policy=pol)

    def test_report_renders(self):
        a = engine.run(load("f02_observed_exceeds_intended.json"), policy=AUTO)
        md = engine.render_markdown(a)
        self.assertIn("research-assistant-02", md)
        self.assertIn("Intended / Configured / Observed matrix", md)
        self.assertIn("Human-in-the-loop ledger", md)


class TestCli(unittest.TestCase):
    def test_cli_assess(self):
        import tempfile
        from boundaryproof.__main__ import main
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "r.md")
            rc = main(["assess", os.path.join(FIX, "f01_aligned.json"),
                       "--policy", os.path.join(POL, "auto.json"),
                       "--out", out])
            self.assertEqual(rc, 0)
            with open(out) as fh:
                self.assertIn("summarizer-01", fh.read())


if __name__ == "__main__":
    unittest.main()
