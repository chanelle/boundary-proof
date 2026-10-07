"""BoundaryProof v0.1 — Intended / Configured / Observed matrix builder.

The matrix is the engine of the assessment: every serious finding comes from a
column mismatch, not from a checklist item.

Merge policy for multiple configured sources: the MOST PERMISSIVE cell wins,
with provenance recorded. Rationale: an audit must surface the widest
authority any source grants; restrictive sources do not cancel permissive
ones, they create a CONFIGURED_CONFLICT note (kept as detail text, not a
separate finding class, to avoid double-counting).
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from . import verbs
from .models import IntentStatement, Mismatch, Unknown, VerbRow
from .evidence import EvidenceStore, make_unknown

# Ordered most->least permissive for merge. UNKNOWN never wins a merge: an
# unknown source contributes nothing, and the gap is recorded separately.
_MERGE_ORDER = {verbs.YES: 3, verbs.PARTIAL: 2, verbs.NO: 1, verbs.UNKNOWN: 0}

_MISMATCH_SEQ = {"M": 0}


def _next_id(prefix: str) -> str:
    _MISMATCH_SEQ["M"] += 1
    return f"{prefix}-{_MISMATCH_SEQ['M']:02d}"


def reset_ids() -> None:
    _MISMATCH_SEQ["M"] = 0


def build_matrix(
    intent: IntentStatement,
    configured_sources: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
) -> List[VerbRow]:
    """Build the 11-verb x 3-column matrix.

    intent.allowed maps verb -> bool (True/False). A verb absent from both
    allowed and denied is INTENDED UNKNOWN, unless denied lists it (NO).
    configured_sources: [{source, verbs: {verb: STATE}}]
    observations: [{verb, result: STATE, method, evidence_ref}]
    """
    rows: List[VerbRow] = []
    for verb in verbs.VERBS:
        verbs.validate_verb(verb)
        # Intended column
        if verb in intent.denied:
            intended = verbs.NO
        elif verb in intent.allowed:
            intended = verbs.YES if intent.allowed[verb] else verbs.NO
        else:
            intended = verbs.UNKNOWN
        # Configured column: most permissive wins, provenance recorded
        configured = verbs.UNKNOWN
        prov_c = ""
        for src in configured_sources:
            cell = src.get("verbs", {}).get(verb, verbs.UNKNOWN)
            verbs.validate_state(cell)
            if _MERGE_ORDER[cell] > _MERGE_ORDER[configured]:
                configured = cell
                prov_c = src.get("source", "")
        # Observed column: strongest *demonstrated* result wins; a test that
        # proves YES beats a log that suggests PARTIAL. Provenance recorded.
        observed = verbs.UNKNOWN
        prov_o = ""
        for obs in observations:
            if obs.get("verb") != verb:
                continue
            cell = obs.get("result", verbs.UNKNOWN)
            verbs.validate_state(cell)
            if _MERGE_ORDER[cell] > _MERGE_ORDER[observed]:
                observed = cell
                prov_o = obs.get("method", "") or obs.get("evidence_ref", "")
        rows.append(VerbRow(verb=verb, intended=intended, configured=configured,
                            observed=observed, configured_provenance=prov_c,
                            observed_provenance=prov_o))
    return rows


def _exceeds(a: str, b: str) -> bool:
    """True if cell state a is strictly more permissive than b.

    UNKNOWN is never "more permissive" — it is handled by its own classes.
    """
    if a == verbs.UNKNOWN or b == verbs.UNKNOWN:
        return False
    order = {verbs.NO: 0, verbs.PARTIAL: 1, verbs.YES: 2}
    return order[a] > order[b]


def detect_mismatches(
    matrix: List[VerbRow],
    store: EvidenceStore,
    delegation: List[Dict[str, Any]] | None = None,
    containment: Dict[str, Any] | None = None,
    identities: List[Dict[str, Any]] | None = None,
) -> Tuple[List[Mismatch], List[Unknown]]:
    """Compare columns; return (mismatches, new unknowns).

    Every mismatch carries the triple so the finding chain
    (intent -> config -> observation -> mismatch) is reconstructable.
    """
    mismatches: List[Mismatch] = []
    new_unknowns: List[Unknown] = []

    for row in matrix:
        v, i, c, o = row.verb, row.intended, row.configured, row.observed

        # 1. Observed exceeds intended — the sharpest class.
        if _exceeds(o, i):
            mismatches.append(Mismatch(
                id=_next_id("M"), verb=v, mismatch_class="OBSERVED_EXCEEDS_INTENDED",
                intended=i, configured=c, observed=o,
                detail=(f"Observed capability ({o}) exceeds delegated intent ({i}). "
                        f"Via: {row.observed_provenance or 'unstated'}. "
                        f"Configured as: {c} ({row.configured_provenance or 'unstated'}).")))
            continue

        # 2. Observed contradicts configured (config says NO, behavior says YES).
        if o in (verbs.YES, verbs.PARTIAL) and c == verbs.NO:
            mismatches.append(Mismatch(
                id=_next_id("M"), verb=v, mismatch_class="OBSERVED_VIOLATES_CONFIGURED",
                intended=i, configured=c, observed=o,
                detail=(f"Observed behavior ({o}) violates configured restriction ({c}). "
                        "Either the configuration is stale/wrong or a bypass exists. "
                        f"Evidence: {row.observed_provenance or 'unstated'}.")))
            continue

        # 3. Configured exceeds intended, behavior not yet verified.
        if _exceeds(c, i):
            mismatches.append(Mismatch(
                id=_next_id("M"), verb=v, mismatch_class="CONFIGURED_EXCEEDS_INTENDED",
                intended=i, configured=c, observed=o,
                detail=(f"Configured permission ({c}) exceeds delegated intent ({i}); "
                        f"actual behavior is {o}. "
                        "Over-broad configuration with no compensating control.")))
            continue

        # 4. Intent undocumented where authority exists or may exist.
        if i == verbs.UNKNOWN and (c in (verbs.YES, verbs.PARTIAL)
                                  or o in (verbs.YES, verbs.PARTIAL)):
            mismatches.append(Mismatch(
                id=_next_id("M"), verb=v, mismatch_class="INTENT_UNDOCUMENTED",
                intended=i, configured=c, observed=o,
                detail=(f"No delegated intent recorded for '{v}', yet authority exists "
                        f"(configured={c}, observed={o}). Missing delegation record is "
                        "itself a finding: authority without a recorded grant.")))

        # 5. Evidence gaps: consequential verbs with no observed data.
        if o == verbs.UNKNOWN and v in verbs.TRIAGE_VERBS and i != verbs.NO:
            u = make_unknown(
                id=f"U-{v}",
                area="observed capability",
                question=f"What can this agent actually do for verb '{v}'?",
                consequence_if_true=(f"Unverified {v} authority on an agent whose intent "
                                     f"does not forbid it."),
                needed_evidence=(f"A direct test or log review exercising '{v}' "
                                 f"(see verification plan)."))
            new_unknowns.append(u)

    # 6. Delegation expansion: a child with broader context/authority than the
    #    parent's intent for the delegated task.
    for d in delegation or []:
        scope = d.get("context", "")
        child_verbs = d.get("verbs", [])
        if scope == "full" or child_verbs:
            mismatches.append(Mismatch(
                id=_next_id("M"), verb="delegate",
                mismatch_class="DELEGATION_EXPANSION",
                intended=d.get("intended_scope", verbs.UNKNOWN),
                configured="YES", observed="YES",
                detail=(f"Delegation from {d.get('from')} to {d.get('to')} carries "
                        f"{'the full parent context' if scope == 'full' else 'tool verbs: ' + ','.join(child_verbs)}. "
                        "Delegation is an authority-expanding act: the child's reach "
                        "exceeds the parent's stated task scope.")))

    # 7. Containment: the "what stops it right now?" question.
    if containment is not None:
        summary = (containment.get("summary") or "").strip()
        tested = bool(containment.get("tested"))
        if not summary or summary.upper() == verbs.UNKNOWN:
            mismatches.append(Mismatch(
                id=_next_id("M"), verb="containment",
                mismatch_class="CONTAINMENT_GAP",
                intended=verbs.UNKNOWN, configured=verbs.UNKNOWN, observed=verbs.UNKNOWN,
                detail="No containment mechanism could be named. If this agent starts "
                       "doing something unintended right now, nothing documented stops it."))
        elif not tested:
            mismatches.append(Mismatch(
                id=_next_id("M"), verb="containment",
                mismatch_class="CONTAINMENT_GAP",
                intended=verbs.UNKNOWN, configured=verbs.PARTIAL, observed=verbs.UNKNOWN,
                detail=(f"Containment named but never exercised: '{summary}'. "
                        "An untested kill-switch is documented as untested, not as a control.")))

    # 8. Un-delegated authority: identities/credentials no human ever granted.
    #    (v0.3 candidate from the article draft, promoted into v0.1 because the
    #    brief's thesis — intended vs configured vs observed — demands it: some
    #    authority never passes through a delegation event at all.)
    for ident in identities or []:
        if ident.get("granted_by") == "platform":
            mismatches.append(Mismatch(
                id=_next_id("M"), verb=ident.get("enables", "identity"),
                mismatch_class="UNDELEGATED_AUTHORITY",
                intended=verbs.UNKNOWN, configured=verbs.YES, observed=ident.get("observed", verbs.UNKNOWN),
                detail=(f"Identity '{ident.get('id')}' arrived with the platform; no human "
                        f"delegation event granted it. Enables: {ident.get('enables')}. "
                        "Platform-provided authority bypasses the intent column entirely.")))

    for u in new_unknowns:
        store.add_unknown(u)
    return mismatches, new_unknowns
