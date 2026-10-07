# Evidence model

## The rule

Every finding must be reconstructable as:

**intent → config → test/observation → artifact → mismatch → finding →
remediation → verification**

Each link in that chain is a registered evidence record or an explicit Unknown.
An LLM opinion is not evidence. v0.1 accepts exactly five evidence kinds:

- `direct` — the assessor directly witnessed the behavior
- `test` — a planned test's recorded outcome
- `log` — a log line, trace, or transcript excerpt
- `config` — a configuration artifact (manifest, policy, IAM export)
- `human_attested` — a named human's signed statement (lowest confidence weight)

`make_evidence()` rejects anything else. There is no `llm_opinion` kind and there
never will be.

## Provenance

Every evidence record carries: id, kind, source (who/where it came from), detail
(what it shows), and timestamp. Every matrix cell carries provenance for the value
it holds. When conflicting configured sources disagree, the most permissive value
wins **and** the conflict is named via `configured_provenance` — the stricter
source is not hidden.

## What happens without evidence

`findings.synthesize()` promotes a mismatch to a finding **only if** the dossier's
`evidence_hints` map it to at least one registered evidence id. Otherwise the
mismatch is converted to an Unknown record naming the smallest evidence that
would resolve it. Three outcomes exist: **finding**, **unknown**, **nothing**.
"Probably fine" is not one of them.

## Unknowns are first-class

An Unknown record answers: what is the question, what is the implication if the
answer is yes, and what is the smallest evidence that would settle it. The report
renders them in their own section, ranked with findings — because in authority
auditing, an unanswered question about `write` authority *is* the headline.

## What v0.1 does not do

v0.1 does not gather evidence itself. Observations and test outcomes are supplied
in the dossier; the engine's job is to reason honestly over what it is given and
to refuse to reason beyond it. A future live-probing layer would implement the
same `EvidenceStore` interface against real agent sandboxes.
