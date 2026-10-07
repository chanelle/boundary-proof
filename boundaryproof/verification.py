"""BoundaryProof v0.1 — remediation verification (retest).

After a remediation is applied, the verification test is re-run. The outcome
is binary and evidenced: passed (the boundary now holds, with proof) or
failed (it doesn't). There is no "partially verified".
"""
from __future__ import annotations

from typing import Dict, List

from . import verbs
from .models import Finding


def verify(findings: List[Finding],
           retest_observations: Dict[str, Dict[str, str]]) -> List[Finding]:
    """Re-test each finding with an applied remediation.

    retest_observations maps finding id -> {"verb": v, "result": STATE,
    "evidence_ref": ...}. The retest observation describes what the SAME probe
    now returns after the fix.

    Pass rule (no exceptions):
      - retest result NO ......................... passed (capability removed)
      - retest YES/PARTIAL while intent is NO .... failed  (overreach persists)
      - retest YES/PARTIAL while intent allows it  passed ONLY if evidence_ref
        describes the control now governing it (approval, scoping); otherwise
        pending (unverifiable claim is not a pass).
    """
    for f in findings:
        if not f.remediation or f.remediation.status != "applied":
            f.verification = "pending"
            continue
        retest = retest_observations.get(f.id)
        if not retest:
            f.verification = "pending"
            f.verification_evidence = "no retest observation supplied; remains unverified"
            continue
        result = retest.get("result", verbs.UNKNOWN)
        intended = f.mismatch.intended
        ref = (retest.get("evidence_ref") or "").strip()

        if result == verbs.NO:
            f.verification = "passed"
        elif result in (verbs.YES, verbs.PARTIAL) and intended == verbs.NO:
            f.verification = "failed"
        elif result in (verbs.YES, verbs.PARTIAL) and intended != verbs.NO and ref:
            f.verification = "passed"
        else:
            f.verification = "pending"
            f.verification_evidence = ("retest inconclusive or undescribed; "
                                       "unverifiable claims do not pass")
            continue
        f.verification_evidence = ref
        f.remediation.status = "verified" if f.verification == "passed" else "failed"
    return findings
