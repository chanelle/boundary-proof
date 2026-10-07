# Schema

## Input: agent dossier (JSON)

| Field | Type | Required | Meaning |
|---|---|---|---|
| `agent_name` | string | yes | Identifier of the assessed agent |
| `intent` | object | yes | `text`, `allowed` (verb→bool), `denied` (verb list), `limits`, `expires`, `source` (who stated it, when) |
| `configured_sources` | list | no | `[{source, verbs: {verb: YES\|PARTIAL\|NO\|UNKNOWN}}]` — tool manifests, IAM, proxy configs |
| `observations` | list | no | `[{verb, result, method, evidence_ref?}]` — what the agent demonstrably did |
| `planned_tests` | list | no | `[{name, verbs, method, target, observation?}]` — tests the assessor proposes; G3-gated if consequential |
| `delegation` | list | no | `[{from, to, context: full\|scoped\|summary, intended_scope}]` |
| `identities` | list | no | `[{id, granted_by: platform\|human:…, enables, observed}]` — platform-granted credentials |
| `containment` | object | no | `{summary, tested: bool}` — named kill-switch and whether it was ever exercised |
| `reach` | object | no | `{customer_data_in_reach, production_in_reach, financial_in_reach, approval_effective, containment_effective, evidence_direct}` — blast-radius inputs |
| `evidence_hints` | object | no | `{"verb:MISMATCH_CLASS": ["EV-01", …]}` — which evidence ids support which signal |
| `remediation_applied` | object | no | `{finding_id: bool}` |
| `retest` | object | no | `{finding_id: {verb, result, evidence_ref}}` |

Intent mapping: `allowed[verb] = true` → YES; `false` or `denied` → NO; absent → UNKNOWN.

## Output: assessment (JSON)

- `agent_name`, `methodology_version`
- `matrix`: 33 cells `{verb, intended, configured, observed, *_provenance}`
- `mismatches`: 8 classes — `OBSERVED_EXCEEDS_INTENDED`,
  `OBSERVED_VIOLATES_CONFIGURED`, `CONFIGURED_EXCEEDS_INTENDED`,
  `INTENT_UNDOCUMENTED`, `DELEGATION_EXPANSION`, `UNDELEGATED_AUTHORITY`,
  `CONTAINMENT_GAP`, `EVIDENCE_GAP`
- `findings`: `{id, title, severity, confidence, likelihood, blast_radius,
  mismatch, evidence_ids, attack_paths, remediation, verification}`
- `attack_paths`: composed chains with per-link triples
- `unknowns`: `{id, kind, question, implication_if_true, needed_evidence}`
- `evidence`: the registered evidence store
- `gates`: the four HITL decisions with provenance
- `metrics`: total/human minutes, HIR, intervention count, autonomous completion
  rate, findings needing adjudication, false-positive rate, remediation
  verification rate
- `executive_summary`, `most_consequential_action`, `limitations`

## Verb states

`YES | PARTIAL | NO | UNKNOWN`. Comparison is by permissiveness: YES > PARTIAL >
NO; UNKNOWN is incomparable — it never exceeds and is never exceeded. This is the
load-bearing invariant: no signal is ever derived from a blank cell.
