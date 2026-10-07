"""BoundaryProof v0.1 — report renderer.

The report leads with the matrix (the differentiator), then the one-line
executive summary ("most consequential possible action"), ranked findings,
attack paths, unknowns, remediations, verification, HITL ledger, and required
disclosures. Written for a CTO/CISO/founder who is not an AI-security
specialist: plain language first, evidence always one hop away.
"""
from __future__ import annotations

from typing import List

from .models import Assessment, Finding

_SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _matrix_table(matrix) -> str:
    lines = ["| Verb | Intended | Configured | Observed |",
             "|------|----------|------------|----------|"]
    for row in matrix:
        flag = ""
        cells = {row.intended, row.configured, row.observed} - {"UNKNOWN"}
        if len({c for c in (row.intended, row.configured, row.observed)
                if c != "UNKNOWN"}) > 1:
            flag = " <-- MISMATCH"
        lines.append(f"| {row.verb} | {row.intended} | {row.configured} | "
                     f"{row.observed} |{flag}")
    return "\n".join(lines)


def _finding_md(f: Finding) -> str:
    m = f.mismatch
    ev = ", ".join(f.evidence_ids) if f.evidence_ids else "none (held)"
    lines = [
        f"### {f.id} — {f.title}",
        "",
        f"**Severity:** {f.severity} | **Confidence:** {f.confidence} | "
        f"**Likelihood:** {f.likelihood} | **Blast radius:** {f.blast_radius}",
        "",
        f"**Mismatch class:** {m.mismatch_class}",
        f"**Triple:** intended={m.intended} / configured={m.configured} / observed={m.observed}",
        "",
        f"**Detail:** {m.detail}",
        "",
        f"**Evidence:** {ev}",
    ]
    if f.attack_path_ids:
        lines.append(f"**Attack paths:** {', '.join(f.attack_path_ids)}")
    if f.unknown_ids:
        lines.append(f"**Open unknowns:** {', '.join(f.unknown_ids)}")
    if f.remediation:
        lines += ["",
                  f"**Remediation ({f.remediation.status}):** {f.remediation.recommendation}",
                  "",
                  f"**Verification test:** {f.remediation.verification_test}",
                  f"**Verification result:** {f.verification}"
                  + (f" — {f.verification_evidence}" if f.verification_evidence else "")]
    return "\n".join(lines)


def render(a: Assessment) -> str:
    findings = sorted(a.findings, key=lambda f: (_SEV_ORDER.get(f.severity, 4), f.id))
    sev_counts: dict = {}
    for f in a.findings:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
    sev_line = ", ".join(f"{k}: {v}" for k, v in
                         sorted(sev_counts.items(), key=lambda kv: _SEV_ORDER.get(kv[0], 4)))

    L: List[str] = []
    L += [f"# BoundaryProof Assessment — {a.agent_name}", "",
          f"*Methodology: {a.methodology_version}*", "",
          "## Executive summary", "",
          a.executive_summary or "_No summary recorded._", "",
          f"**Most consequential possible action:** {a.most_consequential_action or 'UNKNOWN — could not be stated, which is itself a finding.'}",
          "",
          f"**Findings:** {len(a.findings)} ({sev_line or 'none'}) | "
          f"**Attack paths:** {len(a.attack_paths)} | "
          f"**Open unknowns:** {len(a.unknowns)}",
          "",
          "## Intended / Configured / Observed matrix", "",
          "Every serious finding in this report comes from a column mismatch below.",
          "",
          _matrix_table(a.matrix), "",
          "## Findings (ranked by business consequence)", ""]
    for f in findings:
        L += [_finding_md(f), ""]
    if a.attack_paths:
        L += ["## Attack paths (composed authority)", ""]
        for p in a.attack_paths:
            L += [f"### {p.id} — {p.title}", "",
                  f"**Consequence:** {p.consequence}", "",
                  "**Chain:**"]
            L += [f"- {s}" for s in p.steps]
            L += [""]
    if a.unknowns:
        L += ["## Explicit unknowns and evidence gaps", "",
              "UNKNOWN is a first-class result. Each item below names the smallest "
              "evidence that would resolve it.", ""]
        for u in a.unknowns:
            L += [f"- **{u.id}** [{u.area}] {u.question}",
                  f"  - If true: {u.consequence_if_true}",
                  f"  - Needed: {u.needed_evidence}", ""]
    L += ["## Human-in-the-loop ledger", "",
          f"Gates: {len(a.gates)} | "
          f"Human active minutes: {a.metrics.get('human_active_minutes')} | "
          f"HIR: {a.metrics.get('human_intervention_ratio')} "
          f"(target <= {a.metrics.get('target_hir_max')}) | "
          f"Target met: {a.metrics.get('hir_target_met')}", ""]
    for g in a.gates:
        L.append(f"- **{g.gate}** {g.name}: {g.decision} by {g.decided_by}"
                 + (f" ({g.minutes} min)" if g.minutes else "")
                 + (f" — {g.note}" if g.note else ""))
    L += ["",
          "## Disclosures and limitations", "",
          "- Assessor: BoundaryProof v0.1 (automated assessment engine). Findings marked "
          "below High confidence rest on direct evidence; all else is labeled.",
          "- UNKNOWN cells were not converted into assumptions in either direction."]
    for lim in a.limitations:
        L.append(f"- {lim}")
    L += ["",
          "_What BoundaryProof deliberately did NOT build: see KNOWN_LIMITATIONS.md / "
          "README 'What I deliberately did NOT build'._", ""]
    return "\n".join(L)
