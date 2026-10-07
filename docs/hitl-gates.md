# HITL gate definitions

Humans intervene at exactly four gates. Nothing else in the pipeline waits for a
person.

## G1 — Scope authorization

*When:* before any test is planned.
*Question:* is this assessment authorized to run against this target, in this
environment, at this time?
*Context given:* agent name, proposed test targets.
*Without it:* the engine raises `PermissionError` and stops. There is no
assessment without scope authorization.

## G2 — Intent confirmation

*When:* after the matrix is built, before mismatches become findings.
*Question:* is the recorded intent statement actually what the human delegated?
*Context given (least-privilege):* agent name, intent text, allowed/denied verb
lists only. The human confirming intent does not see findings, severities, or
attack paths — intent confirmation must not be influenced by what the engine found.
*Without it:* findings are not published; the assessment halts at the matrix.

## G3 — Consequential test approval

*When:* per consequential test, before execution.
*Question:* may this specific test run against this specific target?
*Context given:* test name, verbs, method, target, classification.
*Classification:* every planned test is classified READ_ONLY / SANDBOX_SAFE /
CONSEQUENTIAL from verb × target. Only CONSEQUENTIAL tests need G3; the rest run
autonomously.
*Without it:* the test is **blocked** — recorded in the ledger and the report as
unverified. A blocked test is never silently skipped and never treated as a pass.

## G4 — Risk acceptance / final adjudication

*When:* after findings, attack paths, and verification results are assembled.
*Question:* does the human accept the residual risk and the report as final?
*Context given:* finding count, severity breakdown, verification outcomes, unknowns.
*Without it:* the report is marked draft; metrics record findings needing
adjudication.

## The ledger and the ratio

Every decision records: gate, approved/denied, decided-by, minutes spent, note,
and provenance (`human` vs `policy_authorized`). Pre-authorizations supplied via
`--policy` (e.g., "sandbox tests always allowed") are recorded as
`policy_authorized` and **never counted as human intervention** — an org policy is
not a person spending time.

Tracked metrics: total assessment effort, human active minutes, Human Intervention
Ratio (human ÷ total, target ≤ 0.10), intervention count, autonomous completion
rate, findings needing adjudication, false-positive rate, remediation verification
rate.

The ≤10% target is a design constraint, not a vanity metric: if routine
assessments need humans for more than a tenth of the effort, the product has
failed at autonomy. The ledger makes that failure visible instead of hiding it.
