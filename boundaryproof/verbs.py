"""BoundaryProof v0.1 — canonical capability verbs.

The eleven verbs from the product brief. The taxonomy is deliberately closed
for v0.1: extension is architecturally supported but not exercised, because
every new verb multiplies the matrix cells a human must adjudicate.

Mapping note (recorded decision): Chanelle's Agent Authority Review v0.2 uses
thirteen verbs. The two not in this list are handled without new verbs:
  - EXFILTRATE  -> a *composed* finding (read + send_external chained), see
                   attack_paths.py. Exfiltration is a path, not a permission.
  - RECOVER/REVOKE -> assessed via the containment question ("what stops it
                   right now?"), see matrix.detect_containment_gap().
This keeps the matrix at 33 cells per agent instead of 39, with no loss of
finding classes.
"""

VERBS = [
    "read",
    "write",
    "execute",
    "commit",
    "delete",
    "deploy",
    "send_external",
    "transact",
    "approve",
    "delegate",
    "escalate",
]

# Cell states. UNKNOWN is a first-class value: a blank cell is evidence of an
# evidence gap, never a silent "no".
YES = "YES"
NO = "NO"
PARTIAL = "PARTIAL"
UNKNOWN = "UNKNOWN"

STATES = (YES, NO, PARTIAL, UNKNOWN)

# Numeric rank used only for mismatch comparison, never displayed as a score.
_RANK = {NO: 0, UNKNOWN: -1, PARTIAL: 2, YES: 3}


def rank(state: str) -> int:
    """Return the comparison rank of a cell state.

    UNKNOWN ranks -1 (below NO) so it is never treated as "more permissive"
    by accident; mismatch logic handles UNKNOWN explicitly.
    """
    if state not in _RANK:
        raise ValueError(f"unknown cell state: {state!r}")
    return _RANK[state]


def validate_state(state: str) -> str:
    if state not in STATES:
        raise ValueError(f"cell state must be one of {STATES}, got {state!r}")
    return state


def validate_verb(verb: str) -> str:
    if verb not in VERBS:
        raise ValueError(f"verb must be one of {VERBS}, got {verb!r}")
    return verb


# Verbs whose real-world exercise is consequential enough that any *proposed*
# active test of them requires HITL gate G3 (consequential test approval),
# unless the test runs against an approved sandbox fixture.
CONSEQUENTIAL_VERBS = frozenset({
    "write",
    "execute",
    "commit",
    "delete",
    "deploy",
    "send_external",
    "transact",
    "approve",
    "delegate",
    "escalate",
})

# Verbs that route to a full review in triage (mirrors v0.2 Tier 1 rule).
TRIAGE_VERBS = frozenset({"write", "execute", "send_external", "delegate"})
