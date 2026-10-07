"""BoundaryProof v0.1 — evidence model.

Central rule, enforced in code: a claim without provenance cannot become a
finding. The engine will refuse to promote an inference to OBSERVED, and it
will refuse to build a Finding from an empty evidence list.

UNKNOWN handling:
  - A matrix cell may be UNKNOWN (we looked, or we never looked).
  - An UNKNOWN with meaningful business consequence becomes an Unknown record
    AND can raise a finding of class EVIDENCE_GAP (severity Medium by default).
  - UNKNOWN is never silently converted to NO ("we didn't see it, so it's
    safe") or to YES ("assume breach").
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

from .models import Evidence, Unknown


_EVIDENCE_KINDS = ("config", "observation", "test", "interview", "log", "document")


def make_evidence(
    id: str,
    kind: str,
    source: str,
    summary: str,
    collected_at: str = "",
    raw_bytes: Optional[bytes] = None,
) -> Evidence:
    """Create a provenance-bearing evidence record.

    Raises ValueError if kind is unknown or source is empty — an evidence
    without a re-checkable source is not evidence.
    """
    if kind not in _EVIDENCE_KINDS:
        raise ValueError(f"evidence kind must be one of {_EVIDENCE_KINDS}, got {kind!r}")
    if not source or not source.strip():
        raise ValueError("evidence requires a non-empty source (file, command, person, stream)")
    sha = hashlib.sha256(raw_bytes).hexdigest() if raw_bytes is not None else ""
    return Evidence(id=id, kind=kind, source=source.strip(), summary=summary,
                    collected_at=collected_at, sha256=sha)


def make_unknown(
    id: str,
    area: str,
    question: str,
    consequence_if_true: str,
    needed_evidence: str,
) -> Unknown:
    return Unknown(id=id, area=area, question=question,
                   consequence_if_true=consequence_if_true,
                   needed_evidence=needed_evidence)


class EvidenceStore:
    """Collects evidence and unknowns for one assessment.

    Findings may only reference evidence ids present in the store. This is the
    mechanical enforcement of "an LLM opinion is not evidence".
    """

    def __init__(self) -> None:
        self.evidence: Dict[str, Evidence] = {}
        self.unknowns: Dict[str, Unknown] = {}

    def add(self, ev: Evidence) -> None:
        if ev.id in self.evidence:
            raise ValueError(f"duplicate evidence id: {ev.id}")
        self.evidence[ev.id] = ev

    def add_unknown(self, u: Unknown) -> None:
        if u.id in self.unknowns:
            raise ValueError(f"duplicate unknown id: {u.id}")
        self.unknowns[u.id] = u

    def check_references(self, ids: List[str]) -> List[str]:
        """Return the subset of ids that are NOT in the store (must be empty)."""
        return [i for i in ids if i not in self.evidence and i not in self.unknowns]

    def link(self, finding_id: str, ids: List[str]) -> None:
        missing = self.check_references(ids)
        if missing:
            raise ValueError(
                f"finding {finding_id} references unknown evidence/unknowns: {missing}. "
                "Add the evidence first, or record an Unknown — never invent it."
            )
        for i in ids:
            if i in self.evidence and finding_id not in self.evidence[i].supports:
                self.evidence[i].supports.append(finding_id)
