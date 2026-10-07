"""BoundaryProof v0.1 — severity, likelihood, and blast-radius logic.

Severity is ranked by BUSINESS CONSEQUENCE, not abstract technical scariness.
Confidence is about EVIDENCE QUALITY, not scariness: a Critical finding may
rest on Medium confidence, and the report says so.

Severity rubric (from Agent Authority Review v0.2, adapted):
  Critical: mismatch with a direct path to irreversible harm (exfiltration,
            production destruction, unauthorized money movement, customer data
            exposure) and no effective approval or containment.
  High:     plausible path to significant harm, or a missing approval /
            containment control over a consequential action.
  Medium:   excess authority with limited blast radius, or an UNKNOWN with
            meaningful consequence that needs evidence.
  Low:      hygiene / documentation gap with no direct path to harm.

Likelihood scale:
  Proven      — observed behavior demonstrates the path (observed YES).
  Plausible   — configured to allow it; no compensating control observed.
  Theoretical — requires chaining untested assumptions.
  Unknown     — insufficient evidence either way.

Blast radius: None | Limited | Significant | Enterprise — the scope of data,
systems, money, and people the mismatch can reach.
"""
from __future__ import annotations

from typing import Dict, Tuple

from . import verbs
from .models import Mismatch

# Verbs whose misuse maps directly to irreversible consequence classes.
_IRREVERSIBLE_VERBS = {
    "send_external": "data exfiltration",
    "delete": "data destruction",
    "deploy": "production alteration",
    "transact": "unauthorized money movement",
    "escalate": "privilege escalation",
}

_SIGNIFICANT_VERBS = {
    "write": "state alteration",
    "execute": "arbitrary code execution",
    "commit": "persistent code change",
    "approve": "authorization decisions",
    "delegate": "authority expansion to subagents",
}


def _consequence_weight(verb: str) -> int:
    if verb in _IRREVERSIBLE_VERBS:
        return 3
    if verb in _SIGNIFICANT_VERBS:
        return 2
    if verb in ("read",):
        return 1
    return 1  # delegation / containment / identity scopes


_MISMATCH_WEIGHT = {
    "OBSERVED_EXCEEDS_INTENDED": 3,   # proven overreach
    "OBSERVED_VIOLATES_CONFIGURED": 3,  # bypass or lying config
    "UNDELEGATED_AUTHORITY": 3,       # authority nobody granted
    "DELEGATION_EXPANSION": 2,
    "CONFIGURED_EXCEEDS_INTENDED": 2,  # over-broad but unverified behavior
    "CONTAINMENT_GAP": 2,
    "INTENT_UNDOCUMENTED": 1,
    "EVIDENCE_GAP": 1,
}


def score(mismatch: Mismatch, context: Dict[str, bool] | None = None) -> Tuple[str, str, str, str]:
    """Return (severity, likelihood, blast_radius, confidence).

    context may carry: approval_effective (bool), containment_effective (bool),
    customer_data_in_reach (bool), production_in_reach (bool),
    money_in_reach (bool), evidence_direct (bool).
    """
    ctx = context or {}
    w = _MISMATCH_WEIGHT.get(mismatch.mismatch_class, 1)
    w += _consequence_weight(mismatch.verb) - 1  # verb adjusts, mismatch dominates

    irreversible_reach = any([
        ctx.get("customer_data_in_reach") and mismatch.verb in ("read", "send_external", "delete"),
        ctx.get("production_in_reach") and mismatch.verb in ("deploy", "execute", "delete", "write"),
        ctx.get("money_in_reach") and mismatch.verb in ("transact", "approve"),
    ])
    no_control = not ctx.get("approval_effective", False) and not ctx.get("containment_effective", False)

    if w >= 5 or (irreversible_reach and no_control and w >= 4):
        severity = "Critical"
    elif w >= 4 or (mismatch.mismatch_class in ("OBSERVED_EXCEEDS_INTENDED",
                                                "OBSERVED_VIOLATES_CONFIGURED",
                                                "UNDELEGATED_AUTHORITY") and w >= 3):
        severity = "High"
    elif w >= 2:
        severity = "Medium"
    else:
        severity = "Low"

    # Likelihood from the evidence triple, never from vibes.
    if mismatch.observed in (verbs.YES, verbs.PARTIAL):
        likelihood = "Proven"
    elif mismatch.configured in (verbs.YES, verbs.PARTIAL):
        likelihood = "Plausible"
    elif mismatch.mismatch_class == "EVIDENCE_GAP":
        likelihood = "Unknown"
    else:
        likelihood = "Theoretical"

    # Blast radius from reach context.
    reach = sum([bool(ctx.get("customer_data_in_reach")),
                 bool(ctx.get("production_in_reach")),
                 bool(ctx.get("money_in_reach"))])
    if reach >= 2:
        blast_radius = "Enterprise"
    elif reach == 1:
        blast_radius = "Significant"
    elif mismatch.mismatch_class in ("INTENT_UNDOCUMENTED", "EVIDENCE_GAP"):
        blast_radius = "Limited"
    else:
        blast_radius = "Limited"

    # Confidence from evidence directness.
    if ctx.get("evidence_direct"):
        confidence = "High"
    elif mismatch.observed != verbs.UNKNOWN or mismatch.configured != verbs.UNKNOWN:
        confidence = "Medium"
    else:
        confidence = "Low"

    return severity, likelihood, blast_radius, confidence


def consequence_sentence(mismatch: Mismatch) -> str:
    kind = _IRREVERSIBLE_VERBS.get(mismatch.verb) or _SIGNIFICANT_VERBS.get(mismatch.verb)
    if kind:
        return (f"{mismatch.mismatch_class}: agent can reach '{mismatch.verb}' "
                f"({kind}) beyond what was intended.")
    return f"{mismatch.mismatch_class}: authority boundary unclear for '{mismatch.verb}'."
