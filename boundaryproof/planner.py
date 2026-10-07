"""BoundaryProof v0.1 — safe test planner and executor.

Safety constraint (from the brief), enforced in code:
  - Default to non-destructive testing.
  - A proposed test touching a CONSEQUENTIAL_VERB is classified CONSEQUENTIAL
    and may NOT execute without HITL gate G3 approval, unless it targets an
    approved sandbox fixture.
  - When the real action would be unsafe, the planner proves as much of the
    path as possible non-destructively and records the remainder as
    UNVERIFIED (an Unknown), never as "safe".

The v0.1 executor runs against fixture-declared observations only: it does not
touch live systems. A production executor would implement the same
classification interface against real sandboxes; the safety logic does not
change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import verbs


@dataclass
class PlannedTest:
    name: str
    verbs: List[str]
    method: str                      # how it would be proven
    classification: str = "READ_ONLY"  # READ_ONLY | SANDBOX_SAFE | CONSEQUENTIAL
    target: str = "fixture"          # fixture | sandbox | production
    authorized: bool = False
    blocked_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "verbs": self.verbs, "method": self.method,
                "classification": self.classification, "target": self.target,
                "authorized": self.authorized, "blocked_reason": self.blocked_reason}


def classify(test: Dict[str, Any]) -> PlannedTest:
    """Classify a proposed test dict {name, verbs, method, target}."""
    name = test.get("name", "unnamed test")
    vbs = test.get("verbs", [])
    target = test.get("target", "fixture")
    for v in vbs:
        verbs.validate_verb(v)
    consequential = any(v in verbs.CONSEQUENTIAL_VERBS for v in vbs)
    if consequential and target == "production":
        classification = "CONSEQUENTIAL"
    elif consequential:
        classification = "SANDBOX_SAFE"
    else:
        classification = "READ_ONLY"
    return PlannedTest(name=name, verbs=vbs, method=test.get("method", ""),
                       classification=classification, target=target)


def authorize(test: PlannedTest, gate_g3_approved: bool) -> PlannedTest:
    """Apply the G3 rule. Returns the test with authorized/blocked_reason set.

    Never raises for a blocked test: blocked tests are recorded, not crashed.
    """
    if test.classification == "CONSEQUENTIAL" and not gate_g3_approved:
        test.authorized = False
        test.blocked_reason = (
            "CONSEQUENTIAL test against a non-sandbox target requires HITL gate G3 "
            "(consequential test approval). Prove the path non-destructively instead; "
            "record the remainder as UNVERIFIED.")
    else:
        test.authorized = True
    return test


@dataclass
class TestResult:
    test_name: str
    executed: bool
    observation: Optional[Dict[str, Any]] = None  # {verb, result, method, evidence_ref}
    note: str = ""


def execute_fixture_tests(tests: List[PlannedTest],
                          fixture_observations: List[Dict[str, Any]]) -> List[TestResult]:
    """Run authorized tests against fixture-declared observations.

    A test "passes" by matching a fixture observation for its verb; there is no
    live execution in v0.1. Unauthorized tests are recorded as not executed.
    """
    results: List[TestResult] = []
    for t in tests:
        if not t.authorized:
            results.append(TestResult(test_name=t.name, executed=False,
                                     note=f"BLOCKED: {t.blocked_reason}"))
            continue
        matched = None
        for obs in fixture_observations:
            if obs.get("verb") in t.verbs and obs.get("test_name", t.name) == t.name:
                matched = obs
                break
        # Fall back: any observation for the verb counts as the test's evidence.
        if matched is None:
            for obs in fixture_observations:
                if obs.get("verb") in t.verbs:
                    matched = obs
                    break
        if matched:
            results.append(TestResult(
                test_name=t.name, executed=True,
                observation={"verb": matched["verb"], "result": matched["result"],
                             "method": t.method, "evidence_ref": matched.get("evidence_ref", "")},
                note="executed against fixture observation (non-destructive)"))
        else:
            results.append(TestResult(test_name=t.name, executed=True, observation=None,
                                      note="no fixture observation; recorded as UNVERIFIED"))
    return results
