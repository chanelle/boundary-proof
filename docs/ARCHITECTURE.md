# BoundaryProof v0.1 — Architecture Decisions

## Decision 1: A pipeline of scoped stages, not an omnipotent worker

The brief requires that the product embody the authority-control principles it
evaluates: no single omnipotent worker, separation of responsibility, scoped context,
evidence provenance, independent evaluation.

The engine is 13 stages. Each stage receives only the data it needs and emits a typed
result into the assessment context:

1. `matrix` — builds the Intended/Configured/Observed matrix
2. `mismatch` — detects the 8 mismatch classes
3. `evidence` — registers evidence and links it; a mismatch with no evidence is
   held back as an explicit Unknown (never a finding, never dropped)
4. `severity` — scores severity / likelihood / blast radius / confidence
5. `attack_paths` — composes multi-verb chains from evidenced mismatches
6. `findings` — promotes evidenced mismatches to findings
7. `remediation` — drafts concrete remediations per mismatch class
8. `plan` — classifies proposed tests (READ_ONLY / SANDBOX_SAFE / CONSEQUENTIAL)
9. `gates` — G1–G4 human-in-the-loop decisions, least-privilege gate context
10. `authorize` — G3 enforcement; blocked tests stay blocked and recorded
11. `execute` — fixture test executor (simulated semantics, real gate enforcement)
12. `verify` — binary pass/fail on remediation retests; unverifiable ≠ pass
13. `report` — markdown + JSON rendering

No stage can invent authority: the matrix is the single source of truth, and every
downstream stage reads from it. This directly answers the finding that subagents
inherit full parent context — here, context is scoped per stage by construction.

## Decision 2: Stdlib-only Python, zero network

Rationale: an authority auditor is a trust anchor. If the engine phones home, the
assessor needs its own assessment. Stdlib-only also means the entire v0.1 is
auditable in one sitting. Trade-off: no fancy reporting; markdown + JSON suffice.

## Decision 3: UNKNOWN is a value, not a missing value

Every verb cell is one of `YES | PARTIAL | NO | UNKNOWN`. The comparison operator
`_exceeds()` is defined so UNKNOWN never exceeds anything and nothing exceeds
UNKNOWN. Consequences:

- A signal without registered evidence is held back as an Unknown record naming
  the exact evidence needed — it is not promoted to a finding and not dropped.
- Triage verbs (write, execute, send_external, delegate) with no observed data and
  no explicit intent denial auto-generate Unknown records with named needed-evidence.
  An agent nobody ever watched *write* is a gap, not a clean bill.

## Decision 4: The 11 verbs are closed; composition handles the rest

Exfiltration is not a verb — it is a composed finding (`read` + `send_external`
chained, from the brief's own example of composing verbs into attack paths).
Recovery/revocation questions are containment questions, handled by the
CONTAINMENT_GAP class. The taxonomy never grows by accident.

## Decision 5: Consequence-ranked severity, confidence from evidence

Severity ranks by business consequence of the mismatch (witness verb weight ×
blast-radius weight, with Critical reserved for irreversible verbs with no effective
control or any mismatch touching live production data). Confidence is a property of
the *evidence*, not the *scariness*: High = direct evidence (direct/test kinds),
Medium = indirect (log/config), Low = human-attested or contested. This keeps a
terrifying-but-thinly-evidenced signal from outranking a proven-but-boring one.

## Decision 6: Policy pre-authorization is distinct from human approval

`--policy` pre-authorizations are recorded as `policy_authorized` and are never
counted toward the Human Intervention Ratio. `--human` records real human decisions
with minutes spent. HIR = human_active_minutes / total_assessment_minutes, target
≤ 0.10. The distinction matters: an org policy that pre-approves sandbox tests is
not a human intervening.

## Decision 7: Fixtures are the test interface for the real world

v0.1 does not probe live agents (deliberately — see Decision 8). Observations and
planned tests arrive in the dossier; the engine classifies them, enforces G3 on
consequential ones, and records blocked/unverified gaps honestly. The 8 fixtures
pin the semantics so the live-probing layer (a future version) has a contract to
implement against.

## Decision 8: Non-destructive by construction

`planner.classify()` maps every test to READ_ONLY / SANDBOX_SAFE / CONSEQUENTIAL
(verb class × target). CONSEQUENTIAL tests require an explicit G3 decision;
without it they are *blocked*, and the block is recorded in the ledger and the
report. A blocked test never becomes a finding for or against — it becomes an
unverified gap. This is the product's own safety invariant, enforced in code, not
documentation.

## What v0.1 is not (yet)

Live probing, auto-remediation, multi-agent delegation-graph analysis, continuous
monitoring, and any network access. See KNOWN_LIMITATIONS.md.
