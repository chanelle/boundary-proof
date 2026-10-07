"""BoundaryProof v0.1 — human-in-the-loop gates and intervention ledger.

Design target: <=10% human active involvement. Humans intervene ONLY at four
gates:

  G1  Scope authorization ......... What systems may BoundaryProof inspect/test?
  G2  Intent confirmation ......... What did the org actually mean to allow?
  G3  Consequential test approval . May we run this destructive/consequential test?
  G4  Risk acceptance ............. Human owns residual risk; final adjudication.

Everything else — inspection, comparison, evidence organization, report writing,
safe test execution, remediation drafting, non-destructive retesting — runs
autonomously. The ledger records every gate so the Human Intervention Ratio is
computed from data, not estimated.

The product embodies its own thesis here: each gate receives ONLY the context
needed to decide (least privilege), never the full assessment transcript.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import GateRecord

GATES = {
    "G1": "Scope authorization",
    "G2": "Intent confirmation",
    "G3": "Consequential test approval",
    "G4": "Risk acceptance / final adjudication",
}

# Minimal context each gate is allowed to see (least-privilege scoping).
GATE_CONTEXT = {
    "G1": ["agent_name", "proposed_systems", "test_targets"],
    "G2": ["agent_name", "intent_text", "allowed_verbs", "denied_verbs"],
    "G3": ["agent_name", "test_name", "test_verbs", "test_target", "classification"],
    "G4": ["agent_name", "finding_count", "severities", "unknown_count",
           "unverified_items"],
}


@dataclass
class GateDecision:
    gate: str
    approved: bool
    decided_by: str
    minutes: float = 1.0
    note: str = ""


class HitlLedger:
    """Records gate decisions and computes HITL metrics."""

    def __init__(self) -> None:
        self.records: List[GateRecord] = []
        self.autonomous_steps: int = 0
        self.findings_needing_adjudication: int = 0
        self.false_positives: int = 0
        self.rejected_findings: int = 0

    def decide(self, decision: GateDecision) -> GateRecord:
        if decision.gate not in GATES:
            raise ValueError(f"unknown gate {decision.gate!r}")
        rec = GateRecord(
            gate=decision.gate, name=GATES[decision.gate],
            decided_by=decision.decided_by,
            decision="approved" if decision.approved else "denied",
            minutes=max(0.0, decision.minutes), note=decision.note)
        self.records.append(rec)
        return rec

    def policy_authorize(self, gate: str, policy_name: str, note: str = "") -> GateRecord:
        """Pre-authorization from a standing policy (fixture/auto mode).

        Recorded distinctly from human approval: policy_authorized != human.
        """
        rec = GateRecord(gate=gate, name=GATES[gate],
                         decided_by=f"policy:{policy_name}",
                         decision="policy_authorized", minutes=0.0, note=note)
        self.records.append(rec)
        return rec

    def step(self, n: int = 1) -> None:
        self.autonomous_steps += n

    def metrics(self, total_assessment_minutes: float) -> Dict[str, Any]:
        human_minutes = sum(r.minutes for r in self.records
                            if not r.decided_by.startswith("policy:"))
        interventions = sum(1 for r in self.records
                            if not r.decided_by.startswith("policy:"))
        hir = (human_minutes / total_assessment_minutes) if total_assessment_minutes > 0 else 0.0
        total_steps = self.autonomous_steps + interventions
        return {
            "total_assessment_minutes": round(total_assessment_minutes, 2),
            "human_active_minutes": round(human_minutes, 2),
            "human_intervention_ratio": round(hir, 4),
            "human_interventions": interventions,
            "policy_authorized_gates": sum(1 for r in self.records
                                           if r.decided_by.startswith("policy:")),
            "autonomous_steps": self.autonomous_steps,
            "autonomous_completion_rate": round(self.autonomous_steps / total_steps, 4) if total_steps else 0.0,
            "findings_needing_adjudication": self.findings_needing_adjudication,
            "false_positive_or_rejected_findings": self.false_positives + self.rejected_findings,
            "target_hir_max": 0.10,
            "hir_target_met": hir <= 0.10,
        }


def gate_context(gate: str, full_context: Dict[str, Any]) -> Dict[str, Any]:
    """Return ONLY the fields the gate is allowed to see."""
    allowed = GATE_CONTEXT.get(gate, [])
    return {k: full_context.get(k) for k in allowed}
