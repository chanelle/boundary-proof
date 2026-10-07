"""BoundaryProof v0.1 — canonical data models.

Every model serializes to plain dicts/lists so assessments, fixtures, and
reports are JSON-round-trippable. No ORM, no hidden state.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


def _d(obj: Any) -> Any:
    """Recursively convert dataclasses to plain dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _d(v) for k, v in asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_d(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _d(v) for k, v in obj.items()}
    return obj


@dataclass
class VerbRow:
    """One row of the Intended / Configured / Observed matrix."""

    verb: str
    intended: str   # YES | NO | PARTIAL | UNKNOWN
    configured: str
    observed: str
    configured_provenance: str = ""  # which source the configured cell came from
    observed_provenance: str = ""    # which test/log the observed cell came from

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class IntentStatement:
    text: str
    allowed: Dict[str, bool] = field(default_factory=dict)  # verb -> allowed?
    denied: List[str] = field(default_factory=list)
    limits: Dict[str, Any] = field(default_factory=dict)    # e.g. max_spend_usd
    expires: Optional[str] = None
    source: str = ""            # where the intent was captured from
    confirmed_by: Optional[str] = None  # human who confirmed at gate G2

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class Evidence:
    """One provenance-bearing evidence artifact.

    Rule: an LLM opinion is not evidence. Every evidence record must name a
    source that a third party could re-check. If there is no source, the
    correct record is an Unknown, not an Evidence.
    """

    id: str
    kind: str       # config | observation | test | interview | log | document
    source: str     # file path, command run, person interviewed, log stream...
    summary: str
    collected_at: str = ""
    sha256: str = ""
    supports: List[str] = field(default_factory=list)  # finding ids / matrix refs

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class Unknown:
    """An explicit evidence gap. UNKNOWN with consequence is a finding-class
    result, not an absence of a result."""

    id: str
    area: str
    question: str
    consequence_if_true: str
    needed_evidence: str

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class Mismatch:
    id: str
    verb: str  # or a scope like "delegation" / "containment" / "identity"
    mismatch_class: str
    intended: str
    configured: str
    observed: str
    detail: str
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class Remediation:
    recommendation: str          # concrete, operable next week
    verification_test: str       # what to attempt; what proves it worked/failed
    status: str = "proposed"     # proposed | applied | verified | failed
    banned_phrases_checked: bool = True

    # Phrases that may never appear in a recommendation (from v0.2):
    BANNED = ("improve security", "follow best practices", "consider hardening")

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class AttackPath:
    id: str
    title: str
    steps: List[str]            # human-readable chain links
    finding_ids: List[str]
    consequence: str

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class Finding:
    id: str
    title: str
    severity: str               # Critical | High | Medium | Low
    confidence: str             # High | Medium | Low (evidence quality, not scariness)
    likelihood: str             # Proven | Plausible | Theoretical | Unknown
    blast_radius: str           # None | Limited | Significant | Enterprise
    mismatch: Mismatch = None
    attack_path_ids: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    unknown_ids: List[str] = field(default_factory=list)
    remediation: Optional[Remediation] = None
    verification: str = "pending"  # pending | passed | failed | not_applicable
    verification_evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class GateRecord:
    gate: str                   # G1 | G2 | G3 | G4
    name: str
    decided_by: str             # human name or "policy:<name>"
    decision: str               # approved | denied | policy_authorized
    at: str = ""
    minutes: float = 0.0        # human active minutes spent at this gate
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)


@dataclass
class Assessment:
    agent_name: str
    methodology_version: str = "boundaryproof-v0.1"
    matrix: List[VerbRow] = field(default_factory=list)
    mismatches: List[Mismatch] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    attack_paths: List[AttackPath] = field(default_factory=list)
    unknowns: List[Unknown] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    gates: List[GateRecord] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    executive_summary: str = ""
    most_consequential_action: str = ""
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _d(self)
