"""BoundaryProof v0.1 — composed authority / attack-path chaining.

Individual verbs are permissions. Composed verbs are authority: the dangerous
outcomes live in CHAINS of individually-defensible steps (read -> write ->
send_external is exfiltration; execute -> delegate is self-replication of
access). This module chains mismatch-bearing verbs into named paths.

Rule: a path is only reported if every link rests on a real mismatch or a
direct observation. Chaining two UNKNOWNs produces an Unknown, not a path.
"""
from __future__ import annotations

from typing import Dict, List

from . import verbs
from .models import AttackPath, Mismatch

# Named compositions. Each is (path_id_suffix, title, verb_sequence, consequence).
_COMPOSITIONS = [
    ("exfiltration",
     "Data exfiltration path",
     ["read", "send_external"],
     "Data readable by the agent can leave the trust boundary."),
    ("destructive_chain",
     "Destructive action path",
     ["execute", "delete"],
     "Code execution chained to deletion reaches data destruction."),
    ("self_replication",
     "Authority self-replication path",
     ["delegate", "escalate"],
     "The agent can hand its authority onward and widen it."),
    ("unauthorized_publish",
     "Unauthorized publish path",
     ["write", "commit", "deploy"],
     "Writes can become persistent and reach production."),
    ("financial_action",
     "Unauthorized financial action path",
     ["approve", "transact"],
     "Approval authority chained to transaction capability moves money."),
    ("approval_bypass",
     "Approval bypass path",
     ["execute", "send_external"],
     "Execution plus egress can achieve externally-visible outcomes that "
     "action-shaped approvals (email/message/purchase gates) do not cover."),
]


def chain_attack_paths(mismatches: List[Mismatch],
                       matrix_by_verb: Dict[str, Dict[str, str]]) -> List[AttackPath]:
    """Build attack paths from verbs that carry real (non-UNKNOWN) authority.

    A link counts if the verb's observed OR configured cell is YES/PARTIAL and
    the mismatch set contains a mismatch for that verb. Pure UNKNOWN chains
    are refused: they become evidence gaps, not findings.
    """
    bad_verbs = set()
    for m in mismatches:
        if m.verb in verbs.VERBS:
            bad_verbs.add(m.verb)

    paths: List[AttackPath] = []
    n = 0
    for suffix, title, seq, consequence in _COMPOSITIONS:
        links = []
        for v in seq:
            cells = matrix_by_verb.get(v, {})
            real = cells.get("observed") in (verbs.YES, verbs.PARTIAL) or \
                cells.get("configured") in (verbs.YES, verbs.PARTIAL)
            if v in bad_verbs and real:
                links.append(v)
        if len(links) >= 2:
            n += 1
            steps = [f"{v}: intended={matrix_by_verb[v]['intended']}, "
                     f"configured={matrix_by_verb[v]['configured']}, "
                     f"observed={matrix_by_verb[v]['observed']}" for v in links]
            paths.append(AttackPath(
                id=f"AP-{n:02d}-{suffix}",
                title=title,
                steps=steps,
                finding_ids=[],  # linked by findings.py after finding ids exist
                consequence=consequence))
    return paths
