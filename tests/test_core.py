"""BoundaryProof v0.1 tests — verbs, matrix, severity, evidence, attack paths."""
import unittest

from boundaryproof import verbs
from boundaryproof import matrix as matrix_mod
from boundaryproof import severity as sev_mod
from boundaryproof import attack_paths as ap_mod
from boundaryproof.evidence import EvidenceStore, make_evidence, make_unknown
from boundaryproof.models import IntentStatement, Mismatch


def _intent(**kw):
    base = dict(text="t", allowed={}, denied=[], limits={}, expires=None, source="s")
    base.update(kw)
    return IntentStatement(**base)


class TestVerbs(unittest.TestCase):
    def test_eleven_verbs(self):
        self.assertEqual(len(verbs.VERBS), 11)
        for v in ("read", "write", "execute", "commit", "delete", "deploy",
                  "send_external", "transact", "approve", "delegate", "escalate"):
            self.assertIn(v, verbs.VERBS)

    def test_invalid_verb_rejected(self):
        with self.assertRaises(ValueError):
            verbs.validate_verb("exfiltrate")

    def test_invalid_state_rejected(self):
        with self.assertRaises(ValueError):
            verbs.validate_state("MAYBE")

    def test_unknown_never_exceeds(self):
        # UNKNOWN must never be treated as more permissive than anything.
        self.assertFalse(matrix_mod._exceeds(verbs.UNKNOWN, verbs.NO))
        self.assertFalse(matrix_mod._exceeds(verbs.YES, verbs.UNKNOWN))
        self.assertTrue(matrix_mod._exceeds(verbs.YES, verbs.NO))
        self.assertTrue(matrix_mod._exceeds(verbs.PARTIAL, verbs.NO))
        self.assertFalse(matrix_mod._exceeds(verbs.NO, verbs.NO))


class TestMatrixBuild(unittest.TestCase):
    def test_intended_mapping(self):
        intent = _intent(allowed={"read": True, "write": False}, denied=["delete"])
        rows = matrix_mod.build_matrix(intent, [], [])
        by = {r.verb: r for r in rows}
        self.assertEqual(by["read"].intended, "YES")
        self.assertEqual(by["write"].intended, "NO")
        self.assertEqual(by["delete"].intended, "NO")
        self.assertEqual(by["execute"].intended, "UNKNOWN")  # absent = unknown, not no

    def test_configured_merge_most_permissive_wins(self):
        srcs = [{"source": "a.json", "verbs": {"read": "NO"}},
                {"source": "b.json", "verbs": {"read": "YES"}}]
        rows = matrix_mod.build_matrix(_intent(), srcs, [])
        by = {r.verb: r for r in rows}
        self.assertEqual(by["read"].configured, "YES")
        self.assertEqual(by["read"].configured_provenance, "b.json")

    def test_unknown_source_contributes_nothing(self):
        srcs = [{"source": "a.json", "verbs": {}}]
        rows = matrix_mod.build_matrix(_intent(), srcs, [])
        by = {r.verb: r for r in rows}
        self.assertEqual(by["read"].configured, "UNKNOWN")


class TestMismatchDetection(unittest.TestCase):
    def _run(self, intent, srcs, obs, **kw):
        matrix_mod.reset_ids()
        store = EvidenceStore()
        rows = matrix_mod.build_matrix(intent, srcs, obs)
        return matrix_mod.detect_mismatches(rows, store, **kw) + (store, rows)

    def test_observed_exceeds_intended(self):
        intent = _intent(allowed={"execute": False})
        srcs = [{"source": "m", "verbs": {"execute": "YES"}}]
        obs = [{"verb": "execute", "result": "YES", "method": "t", "evidence_ref": "EV-1"}]
        mismatches, unknowns, store, rows = self._run(intent, srcs, obs)
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0].mismatch_class, "OBSERVED_EXCEEDS_INTENDED")

    def test_observed_violates_configured(self):
        # intent allows via relay (YES), config says NO, behavior says YES:
        # the config is wrong or bypassed.
        intent = _intent(allowed={"send_external": True})
        srcs = [{"source": "proxy", "verbs": {"send_external": "NO"}}]
        obs = [{"verb": "send_external", "result": "YES", "method": "netflow",
                "evidence_ref": "EV-1"}]
        mismatches, unknowns, store, rows = self._run(intent, srcs, obs)
        self.assertEqual(mismatches[0].mismatch_class, "OBSERVED_VIOLATES_CONFIGURED")

    def test_configured_exceeds_intended_unverified(self):
        intent = _intent(allowed={"deploy": False})
        srcs = [{"source": "iam", "verbs": {"deploy": "YES"}}]
        mismatches, unknowns, store, rows = self._run(intent, srcs, [])
        classes = [m.mismatch_class for m in mismatches]
        self.assertIn("CONFIGURED_EXCEEDS_INTENDED", classes)

    def test_intent_undocumented(self):
        intent = _intent()  # nothing recorded
        srcs = [{"source": "m", "verbs": {"read": "YES"}}]
        mismatches, unknowns, store, rows = self._run(intent, srcs, [])
        self.assertEqual(mismatches[0].mismatch_class, "INTENT_UNDOCUMENTED")

    def test_triage_unknown_becomes_unknown_record(self):
        intent = _intent(allowed={"write": True})
        mismatches, unknowns, store, rows = self._run(intent, [], [])
        ids = [u.id for u in unknowns]
        self.assertIn("U-write", ids)
        # ...but a verb the intent forbids does not generate noise:
        intent2 = _intent(allowed={"write": False})
        m2, u2, s2, r2 = self._run(intent2, [], [])
        self.assertNotIn("U-write", [u.id for u in u2])

    def test_delegation_expansion(self):
        intent = _intent(allowed={"delegate": True})
        mismatches, unknowns, store, rows = self._run(
            intent, [], [],
            delegation=[{"from": "a", "to": "b", "context": "full",
                         "intended_scope": "PARTIAL"}])
        self.assertEqual(mismatches[0].mismatch_class, "DELEGATION_EXPANSION")

    def test_containment_gap_unnamed_and_untested(self):
        intent = _intent()
        m1, u1, s1, r1 = self._run(intent, [], [], containment={"summary": "", "tested": False})
        self.assertEqual(m1[0].mismatch_class, "CONTAINMENT_GAP")
        matrix_mod.reset_ids()
        store2 = EvidenceStore()
        rows2 = matrix_mod.build_matrix(intent, [], [])
        m2, u2 = matrix_mod.detect_mismatches(
            rows2, store2, containment={"summary": "press stop", "tested": False})
        self.assertIn("never exercised", m2[0].detail)
        # tested containment -> no gap
        matrix_mod.reset_ids()
        store3 = EvidenceStore()
        rows3 = matrix_mod.build_matrix(intent, [], [])
        m3, u3 = matrix_mod.detect_mismatches(
            rows3, store3, containment={"summary": "revoke token", "tested": True})
        self.assertEqual([m for m in m3 if m.mismatch_class == "CONTAINMENT_GAP"], [])

    def test_undelegated_authority(self):
        intent = _intent()
        mismatches, unknowns, store, rows = self._run(
            intent, [], [],
            identities=[{"id": "shell-root", "granted_by": "platform",
                         "enables": "execute", "observed": "YES"}])
        self.assertEqual(mismatches[0].mismatch_class, "UNDELEGATED_AUTHORITY")
        # human-granted identities do not trigger it
        matrix_mod.reset_ids()
        store2 = EvidenceStore()
        rows2 = matrix_mod.build_matrix(intent, [], [])
        m2, u2 = matrix_mod.detect_mismatches(
            rows2, store2,
            identities=[{"id": "svc", "granted_by": "human:cto",
                         "enables": "read", "observed": "YES"}])
        self.assertEqual(m2, [])


class TestSeverity(unittest.TestCase):
    def _m(self, verb, cls, i="NO", c="YES", o="YES"):
        return Mismatch(id="M-01", verb=verb, mismatch_class=cls,
                        intended=i, configured=c, observed=o, detail="d")

    def test_critical_exfiltration_no_control(self):
        s, l, b, conf = sev_mod.score(
            self._m("send_external", "OBSERVED_EXCEEDS_INTENDED"),
            {"customer_data_in_reach": True, "approval_effective": False,
             "containment_effective": False, "evidence_direct": True})
        self.assertEqual(s, "Critical")
        self.assertEqual(l, "Proven")
        self.assertEqual(conf, "High")

    def test_likelihood_from_evidence(self):
        s, l, b, conf = sev_mod.score(
            self._m("deploy", "CONFIGURED_EXCEEDS_INTENDED", o="UNKNOWN"),
            {"production_in_reach": True, "evidence_direct": True})
        self.assertEqual(l, "Plausible")  # configured but not observed

    def test_confidence_is_about_evidence(self):
        m = self._m("delete", "OBSERVED_EXCEEDS_INTENDED")
        _, _, _, conf = sev_mod.score(m, {"evidence_direct": False})
        self.assertEqual(conf, "Medium")  # scary but indirect evidence


class TestEvidence(unittest.TestCase):
    def test_source_required(self):
        with self.assertRaises(ValueError):
            make_evidence("EV-1", "test", "", "no source")
        with self.assertRaises(ValueError):
            make_evidence("EV-1", "vibes", "somewhere", "bad kind")

    def test_link_rejects_unregistered(self):
        store = EvidenceStore()
        with self.assertRaises(ValueError):
            store.link("F-01", ["EV-999"])

    def test_mismatch_without_evidence_becomes_unknown(self):
        from boundaryproof import findings as findings_mod
        matrix_mod.reset_ids()
        store = EvidenceStore()
        m = Mismatch(id="M-01", verb="execute",
                     mismatch_class="OBSERVED_EXCEEDS_INTENDED",
                     intended="NO", configured="YES", observed="YES", detail="d")
        found = findings_mod.synthesize([m], store, {}, {})
        self.assertEqual(found, [])  # held back: no finding without evidence
        self.assertEqual(len(store.unknowns), 1)  # recorded as a gap instead


class TestAttackPaths(unittest.TestCase):
    def test_exfiltration_chains(self):
        ms = [Mismatch(id="M-01", verb="read", mismatch_class="UNDELEGATED_AUTHORITY",
                       intended="UNKNOWN", configured="YES", observed="YES", detail="d"),
              Mismatch(id="M-02", verb="send_external",
                       mismatch_class="OBSERVED_EXCEEDS_INTENDED",
                       intended="NO", configured="PARTIAL", observed="YES", detail="d")]
        by = {"read": {"intended": "UNKNOWN", "configured": "YES", "observed": "YES"},
              "send_external": {"intended": "NO", "configured": "PARTIAL", "observed": "YES"}}
        paths = ap_mod.chain_attack_paths(ms, by)
        self.assertTrue(any("exfiltration" in p.id for p in paths))

    def test_unknown_only_does_not_chain(self):
        ms = []
        by = {"read": {"intended": "UNKNOWN", "configured": "UNKNOWN", "observed": "UNKNOWN"},
              "send_external": {"intended": "UNKNOWN", "configured": "UNKNOWN",
                                "observed": "UNKNOWN"}}
        paths = ap_mod.chain_attack_paths(ms, by)
        self.assertEqual(paths, [])


if __name__ == "__main__":
    unittest.main()
