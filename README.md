# BoundaryProof v0.1

**Authority-boundary auditing for AI agents.** Answers one question: *what is the most
consequential thing this agent can actually do, and can we prove that boundary matches
what the human intended?*

The thesis: every agent has three columns of authority — **intended** (what the human
delegated), **configured** (what the platform/tools allow), **observed** (what the agent
demonstrably does). Where the columns disagree, you have a candidate finding. Where a
column is blank, that blank is evidence — it is never silently converted into an
assumption.

## The 11 verbs

The authority taxonomy is fixed and closed: `read, write, execute, commit, delete,
deploy, send_external, transact, approve, delegate, escalate`. The engine does not
expand it. Exfiltration is a *composed* finding (read + send_external chained), not a
12th verb.

## The 10 required outputs

Every assessment produces: authority map · I/C/O matrix · findings · severity /
likelihood / blast radius per finding · attack paths · evidence per finding ·
remediation · retest result · explicit unknowns · executive summary.

## Quickstart

Requires Python 3.10+, no dependencies (stdlib only — the auditor must not phone home).

```bash
cd boundary-proof

# Assess an agent described in fixtures/f02_observed_exceeds_intended.json
python3 -m boundaryproof assess fixtures/f02_observed_exceeds_intended.json \
  --policy policies/auto.json \
  --out samples/f02_observed_exceeds_intended.md

# Full assessment with human gates pre-decided and JSON export
python3 -m boundaryproof assess fixtures/f02_observed_exceeds_intended.json \
  --policy policies/human.json --human policies/human.json \
  --out report.md --json-out assessment.json

# Run the test suite
python3 -m unittest discover -s tests
```

## Input format

An agent dossier is JSON:

```json
{
  "agent_name": "research-assistant-02",
  "intent": {"text": "...", "allowed": {"read": true}, "denied": ["execute"],
             "limits": {}, "expires": null, "source": "Dana (CTO), 2026-09-28"},
  "configured_sources": [{"source": "tool-manifest.json", "verbs": {"read": "YES"}}],
  "observations": [{"verb": "execute", "result": "YES", "method": "ran probe",
                    "evidence_ref": "EV-02"}],
  "planned_tests": [{"name": "probe-egress", "verbs": ["send_external"],
                     "method": "...", "target": "production",
                     "observation": {"verb": "send_external", "result": "YES", ...}}],
  "delegation": [{"from": "a", "to": "b", "context": "full", "intended_scope": "PARTIAL"}],
  "identities": [{"id": "shell-root", "granted_by": "platform",
                  "enables": "execute", "observed": "YES"}],
  "containment": {"summary": "user can press stop", "tested": false},
  "reach": {"customer_data_in_reach": true},
  "evidence_hints": {"execute:OBSERVED_EXCEEDS_INTENDED": ["EV-02"]},
  "remediation_applied": {"F-01": true},
  "retest": {"F-01": {"verb": "deploy", "result": "NO", "evidence_ref": "EV-9"}}
}
```

Verb states are `YES | PARTIAL | NO | UNKNOWN`. Blank = `UNKNOWN`, never an assumption.

## Human-in-the-loop

Humans intervene at exactly four gates: **G1** scope authorization, **G2** intent
confirmation, **G3** consequential-test approval, **G4** risk acceptance / final
adjudication. The ledger tracks total effort, human active minutes, the Human
Intervention Ratio (human minutes ÷ total assessment minutes, target ≤ 0.10),
intervention count, autonomous completion rate, findings needing adjudication, and
verification rates. Without explicit G3 approval, every consequential test is blocked,
not skipped — the gap is recorded as unverified, never as a pass.

Gate decisions can be pre-supplied via `--policy` (pre-authorization, recorded as
`policy_authorized` and never counted as human intervention) or `--human` (a real
person's recorded decisions, counted toward HIR). See `docs/hitl-gates.md`.

## Fixtures

Eight canonical scenarios in `fixtures/` (see `docs/fixtures.md`): aligned;
observed exceeds intended; configured exceeds intended but unverifiable; configured
restricted but observed violates; insufficient evidence; delegated authority exceeds
parent; remediation verified; remediation failed.

## What I deliberately did NOT build

- No network calls anywhere in the engine. An authority auditor must not phone home.
- No severity model based on exploitability/CVSS-style scoring — severity is ranked
  by business consequence, not attacker cleverness.
- No 12th verb, no custom taxonomy, no auto-discovery of "new" verbs.
- No LLM-judged evidence. `make_evidence` accepts only `direct | test | log |
  config | human_attested` kinds; an LLM opinion is not evidence and has no kind.
- No silent conversion of UNKNOWN to YES or NO anywhere in the pipeline.
- No consequential test execution without an explicit G3 decision. Blocked tests
  stay blocked and visible.
- No SIEM, runtime firewall, IAM replacement, vulnerability scanner, compliance
  platform, red-team platform, or observability platform (per brief anti-scope-creep).
- No credential storage, no secret handling, no invented configs/permissions/vulns —
  insufficient evidence yields UNKNOWN or NEEDS HUMAN REVIEW, never a finding.
- No auto-remediation. The engine proposes; humans apply; the engine re-verifies.

## Known limitations

See `KNOWN_LIMITATIONS.md`. The honest headline: v0.1 reasons over *described*
agents, not live ones — observations and test results are supplied, not gathered by
the engine. The fixture executor simulates execution semantics (including G3
blocking); live probing is deliberately out of scope for v0.1.

## Layout

```
boundaryproof/   the engine (13 stages, stdlib-only)
fixtures/        8 canonical scenarios
policies/        example gate pre-authorizations
tests/           48 automated tests
samples/         completed assessments rendered from fixtures
docs/            architecture, schema, evidence model, gates, severity, fixtures
```
