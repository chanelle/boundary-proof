"""BoundaryProof v0.1 — finding synthesis.

A mismatch becomes a Finding only when it can cite evidence. The synthesizer
enforces the chain:

  intent statement -> relevant configuration -> test/observation ->
  evidence artifact -> mismatch -> finding -> remediation -> verification

Mismatches with no supporting evidence are held back and reported as
EVIDENCE_GAP unknowns instead of findings. This is the code-level guarantee
that "an LLM opinion is not evidence".
"""
from __future__ import annotations

from typing import Dict, List

from . import severity as sev
from .evidence import EvidenceStore
from .models import Finding, Mismatch, Remediation, Unknown
from .evidence import make_unknown


def synthesize(mismatches: List[Mismatch],
               store: EvidenceStore,
               context: Dict[str, bool] | None = None,
               evidence_hints: Dict[str, List[str]] | None = None) -> List[Finding]:
    """Turn mismatches into evidence-backed findings.

    evidence_hints maps "verb:MISMATCH_CLASS" -> candidate evidence ids already
    present in the store. Keying by verb+class (not runtime ids) keeps fixtures
    deterministic and human-readable. A mismatch with no evidence becomes an
    Unknown, not a finding.
    """
    ctx = context or {}
    hints = evidence_hints or {}
    findings: List[Finding] = []
    n = 0
    for m in mismatches:
        key = f"{m.verb}:{m.mismatch_class}"
        ev_ids = hints.get(key, [])
        missing = store.check_references(ev_ids)
        if missing:
            raise ValueError(
                f"mismatch {m.id} hints at unregistered evidence {missing}; "
                "register it in the EvidenceStore first.")
        if not ev_ids:
            # No evidence: hold back, record the gap. Never invent a finding.
            u = make_unknown(
                id=f"U-{m.id}",
                area="finding evidence",
                question=f"Can the {m.mismatch_class} signal for '{m.verb}' be evidenced?",
                consequence_if_true=sev.consequence_sentence(m),
                needed_evidence="A configuration artifact, log, or test observation "
                               "that a third party could re-check.")
            store.add_unknown(u)
            continue
        n += 1
        sev_, like_, blast_, conf_ = sev.score(m, ctx)
        store.link(f"F-{n:02d}", ev_ids)
        findings.append(Finding(
            id=f"F-{n:02d}",
            title=f"{m.mismatch_class.replace('_', ' ').title()} — '{m.verb}'",
            severity=sev_, confidence=conf_, likelihood=like_, blast_radius=blast_,
            mismatch=m,
            evidence_ids=list(ev_ids),
            remediation=None,  # attached by remediation.py
        ))
    return findings
