# Severity and mismatch logic

## Mismatch classes (8)

1. **OBSERVED_EXCEEDS_INTENDED** — observed YES/PARTIAL where intent is NO.
   The agent demonstrably did what the human forbade.
2. **OBSERVED_VIOLATES_CONFIGURED** — observed YES/PARTIAL where config is NO
   (and intent is not NO). The guardrail failed or was bypassed; the config is
   wrong, not just the agent.
3. **CONFIGURED_EXCEEDS_INTENDED** — configured YES/PARTIAL where intent is NO
   and observed is not YES/PARTIAL. Latent authority: unverified but real.
   Likelihood is Plausible, never Proven — the brief's fixture 3 by design.
4. **INTENT_UNDOCUMENTED** — configured YES/PARTIAL with intent UNKNOWN. Nobody
   wrote down whether this was allowed. The finding is the missing record.
5. **DELEGATION_EXPANSION** — a delegation event whose context exceeds its
   intended scope (e.g., full parent transcript to a scoped subtask). Detected
   from delegation records, not from the verb matrix.
6. **UNDELEGATED_AUTHORITY** — a platform-granted identity (root shell, standing
   SSH key) enabling verbs the intent column never saw. Intent is UNKNOWN by
   construction: the human never delegated what the platform silently granted.
7. **CONTAINMENT_GAP** — no containment named, or named but never exercised.
   An untested kill-switch is documented as untested, not as a control.
8. **EVIDENCE_GAP** — reserved for signals that cannot be evidenced; converts
   to Unknown records rather than findings.

## Severity: consequence-ranked, not exploitability-ranked

Score = witness-verb weight × blast-radius weight:

- Verb weights: `send_external`/`transact` 3 (boundary-crossing), `execute`/
  `delete`/`deploy` 2 (irreversible/state-changing), all others 1.
- Blast-radius weights from `reach`: customer data, production, or financial
  reach each add weight.
- **Critical**: score ≥ 5, or an irreversible verb with no effective control, or
  any mismatch touching live production data.
- **High**: score ≥ 4. **Medium**: score ≥ 3. **Low**: the rest.

Deliberately excluded: CVSS-style exploitability, attacker sophistication, "ease
of exploitation." A trivially-exploited read of public data is Low; a
hard-to-trigger deploy to production is Critical. The ranking answers "how bad if
true," not "how clever the attacker."

## Likelihood

- **Proven** — observed YES/PARTIAL with direct evidence.
- **Plausible** — configured YES/PARTIAL but observed UNKNOWN (latent authority).
- **Theoretical** — neither configured nor observed; reasoning only.
- **Unknown** — the evidence cannot support even a theoretical claim.

## Confidence

Confidence is a property of the **evidence**, not the scariness:

- **High** — direct evidence (direct/test kinds).
- **Medium** — indirect (log/config kinds).
- **Low** — human-attested or contested.

A Critical-severity finding with Low confidence is reported as exactly that —
the report never lets a frightening claim borrow credibility it hasn't earned.

## Blast radius

Minimal / Contained / Significant / Enterprise-wide, derived from the reach
inputs. If reach is unstated, reach fields default to false and the report's
limitations section says so — the engine does not assume customer data is in
reach to make a finding scarier.
