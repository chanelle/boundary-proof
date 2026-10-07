"""BoundaryProof v0.1 — assessment engine (orchestrator).

Pipeline (each stage gets only the context it needs — least privilege):
  1. Load inputs (fixture/assessment JSON)
  2. G1 scope authorization
  3. Build I/C/O matrix
  4. G2 intent confirmation
  5. Plan + execute safe tests (G3 for consequential tests)
  6. Detect mismatches (matrix + delegation + containment + un-delegated authority)
  7. Synthesize evidence-backed findings (no evidence -> Unknown, never a finding)
  8. Score severity / likelihood / blast radius
  9. Chain attack paths
  10. Draft remediations
  11. Apply + verify remediations (retest)
  12. G4 risk acceptance
  13. Render report + compute HITL metrics

Definition of done: give it a stated agent intent + a sample deployment /
configuration + an authorized test target (as one JSON document), and receive
an evidence-backed assessment while requiring human participation only at the
four gates.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from . import attack_paths, findings as finding_mod, hitl, matrix, planner
from . import remediation as remediation_mod
from . import report as report_mod
from . import severity as sev_mod
from . import verification as verification_mod
from .evidence import EvidenceStore, make_evidence
from .models import Assessment, IntentStatement


def load_inputs(doc: Dict[str, Any]) -> Dict[str, Any]:
    required = ("agent", "intent", "configured_sources")
    missing = [k for k in required if k not in doc]
    if missing:
        raise ValueError(f"input document missing required sections: {missing}. "
                         "See fixtures/ for the canonical input format.")
    return doc


def _register_evidence(doc: Dict[str, Any], store: EvidenceStore) -> None:
    for ev in doc.get("evidence", []):
        store.add(make_evidence(
            id=ev["id"], kind=ev.get("kind", "document"),
            source=ev.get("source", ""), summary=ev.get("summary", ""),
            collected_at=ev.get("collected_at", "")))


def run(doc: Dict[str, Any],
        policy: Dict[str, Any] | None = None,
        human: Dict[str, Any] | None = None) -> Assessment:
    """Run one assessment.

    doc:    the assessment input document (fixture format).
    policy: {gate: {"by": "policy:name", "approve": bool, "note": str}} for
            pre-authorized gates (fixture/auto mode). Recorded as policy, not human.
    human:  {gate: {"by": "Name", "approve": bool, "minutes": float, "note": str}}
            for simulated human decisions (tests, demos).
    Returns a fully populated Assessment.
    """
    t0 = time.monotonic()
    policy = policy or {}
    human = human or {}
    doc = load_inputs(doc)
    matrix.reset_ids()

    ledger = hitl.HitlLedger()
    store = EvidenceStore()
    _register_evidence(doc, store)

    agent = doc["agent"]
    agent_name = agent.get("name", "unnamed-agent")

    def gate(g: str, context: Dict[str, Any]) -> bool:
        """Resolve one gate: human > policy > deny. Records the decision."""
        scoped = hitl.gate_context(g, context)
        if g in human:
            h = human[g]
            ledger.decide(hitl.GateDecision(gate=g, approved=bool(h.get("approve", True)),
                                           decided_by=h.get("by", "human"),
                                           minutes=float(h.get("minutes", 1.0)),
                                           note=h.get("note", "")))
            return bool(h.get("approve", True))
        if g in policy:
            p = policy[g]
            ledger.policy_authorize(g, p.get("by", "default"), p.get("note", ""))
            return bool(p.get("approve", True))
        # No human, no policy: deny consequential gates, hold the assessment.
        ledger.decide(hitl.GateDecision(gate=g, approved=False, decided_by="engine",
                                       minutes=0.0,
                                       note="no human or policy authorization present; denied by default"))
        return False

    # ---- G1: scope authorization ----
    g1_ctx = {"agent_name": agent_name,
              "proposed_systems": doc.get("scope", {}).get("systems", []),
              "test_targets": doc.get("scope", {}).get("test_targets", [])}
    if not gate("G1", g1_ctx):
        raise PermissionError("G1 scope authorization denied; assessment halted.")
    ledger.step()

    # ---- Matrix ----
    intent_doc = doc["intent"]
    intent = IntentStatement(
        text=intent_doc.get("text", ""),
        allowed=intent_doc.get("allowed", {}),
        denied=intent_doc.get("denied", []),
        limits=intent_doc.get("limits", {}),
        expires=intent_doc.get("expires"),
        source=intent_doc.get("source", ""))
    rows = matrix.build_matrix(intent, doc.get("configured_sources", []),
                               doc.get("observations", []))
    ledger.step()

    # ---- G2: intent confirmation ----
    g2_ctx = {"agent_name": agent_name, "intent_text": intent.text,
              "allowed_verbs": [v for v, ok in intent.allowed.items() if ok],
              "denied_verbs": intent.denied}
    g2_ok = gate("G2", g2_ctx)
    if g2_ok:
        # find the approving record to stamp confirmed_by
        for r in reversed(ledger.records):
            if r.gate == "G2" and r.decision in ("approved", "policy_authorized"):
                intent.confirmed_by = r.decided_by
                break
    ledger.step()

    # ---- Tests: plan, G3 for consequential, execute safe ones ----
    planned = [planner.classify(t) for t in doc.get("proposed_tests", [])]
    g3_ctx_base = {"agent_name": agent_name}
    g3_approved = True
    consequential = [t for t in planned if t.classification == "CONSEQUENTIAL"]
    if consequential:
        t0c = consequential[0]
        g3_approved = gate("G3", {**g3_ctx_base, "test_name": t0c.name,
                                  "test_verbs": t0c.verbs, "test_target": t0c.target,
                                  "classification": t0c.classification})
    for t in planned:
        planner.authorize(t, gate_g3_approved=(g3_approved or t.classification != "CONSEQUENTIAL"))
    results = planner.execute_fixture_tests(planned, doc.get("observations", []))
    # Fold executed observations into the matrix's observed column.
    for r in results:
        if r.executed and r.observation:
            for row in rows:
                if row.verb == r.observation["verb"]:
                    row.observed = r.observation["result"]
                    row.observed_provenance = r.observation.get("evidence_ref", r.test_name)
    ledger.step(len(planned))

    # ---- Mismatches ----
    mismatches, _ = matrix.detect_mismatches(
        rows, store,
        delegation=doc.get("delegation", []),
        containment=doc.get("containment"),
        identities=doc.get("identities", []))
    ledger.step()

    # ---- Findings (evidence-backed only) ----
    reach_ctx = doc.get("reach_context", {})
    evidence_hints = doc.get("evidence_hints", {})
    found = finding_mod.synthesize(mismatches, store, reach_ctx, evidence_hints)
    ledger.step()

    # ---- Attack paths ----
    matrix_by_verb = {r.verb: {"intended": r.intended, "configured": r.configured,
                               "observed": r.observed} for r in rows}
    paths = attack_paths.chain_attack_paths(mismatches, matrix_by_verb)
    # Link findings to paths that mention their verbs.
    for p in paths:
        for f in found:
            if any(f.mismatch.verb in s.split(":")[0] for s in p.steps):
                if f.id not in p.finding_ids:
                    p.finding_ids.append(f.id)
                if p.id not in f.attack_path_ids:
                    f.attack_path_ids.append(p.id)
    ledger.step()

    # ---- Remediations ----
    for f in found:
        remediation_mod.draft(f)
    # Apply remediations the fixture says were applied.
    for fid, app in doc.get("remediation_applied", {}).items():
        for f in found:
            if f.id == fid:
                f.remediation.status = "applied"
    verification_mod.verify(found, doc.get("retest_observations", {}))
    ledger.step()

    # ---- Most consequential action (executive one-liner) ----
    consequential_verbs = [r for r in rows
                           if r.observed in ("YES", "PARTIAL")
                           and r.verb in ("send_external", "delete", "deploy",
                                          "transact", "execute", "escalate")]
    if consequential_verbs:
        v = consequential_verbs[0]
        mca = (f"{v.verb} (observed {v.observed}; intended {v.intended})")
    else:
        mca = "UNKNOWN — no consequential observed capability could be stated"

    # ---- G4: risk acceptance ----
    sev_counts: Dict[str, int] = {}
    for f in found:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
    g4_ctx = {"agent_name": agent_name, "finding_count": len(found),
              "severities": sev_counts, "unknown_count": len(store.unknowns),
              "unverified_items": [f.id for f in found if f.verification != "passed"]}
    gate("G4", g4_ctx)
    ledger.step()

    total_minutes = (time.monotonic() - t0) / 60.0
    # In fixture mode the wall-clock is ~0; estimate from steps so HIR is
    # meaningful: 0.5 min per autonomous step is the documented estimate.
    estimated = max(total_minutes, ledger.autonomous_steps * 0.5)
    metrics = ledger.metrics(estimated)
    metrics["findings_needing_adjudication"] = sum(
        1 for f in found if f.confidence != "High" or f.verification == "pending")

    assessment = Assessment(
        agent_name=agent_name,
        matrix=rows, mismatches=mismatches, findings=found,
        attack_paths=paths, unknowns=list(store.unknowns.values()),
        evidence=list(store.evidence.values()), gates=ledger.records,
        metrics=metrics,
        most_consequential_action=mca,
        limitations=list(doc.get("limitations", [])),
    )
    sev_names = ", ".join(f"{k}={v}" for k, v in sorted(sev_counts.items()))
    assessment.executive_summary = (
        f"Assessed '{agent_name}': {len(found)} findings ({sev_names or 'none'}), "
        f"{len(paths)} composed attack paths, {len(store.unknowns)} open unknowns. "
        f"Most consequential possible action: {mca}. "
        f"HIR {metrics['human_intervention_ratio']} (target <= 0.10).")
    return assessment


def run_file(path: str, policy_path: str | None = None,
             human_path: str | None = None) -> Assessment:
    with open(path) as fh:
        doc = json.load(fh)
    policy = None
    if policy_path:
        with open(policy_path) as fh:
            policy = json.load(fh)
    human = None
    if human_path:
        with open(human_path) as fh:
            human = json.load(fh)
    return run(doc, policy=policy, human=human)


def render_markdown(assessment: Assessment) -> str:
    return report_mod.render(assessment)
