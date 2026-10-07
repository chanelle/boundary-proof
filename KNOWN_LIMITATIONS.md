# Known limitations — BoundaryProof v0.1

Honest accounting of what v0.1 cannot do. Each limitation names what would
resolve it.

1. **v0.1 reasons over described agents, not live ones.** Observations and test
   outcomes are supplied in the dossier; the engine does not probe a running
   agent. The fixture executor simulates execution semantics (including real G3
   blocking) but performs no live action. *Resolves with:* a live-probing layer
   implementing the `EvidenceStore` interface against real sandboxes.

2. **The HIR denominator is estimated, not measured.** `estimated_minutes`
   derives from step counts and wall-clock of the local run, not from real test
   execution time. On fixtures the ratio is synthetic. *Resolves with:* measured
   wall-clock from live test execution (see 1).

3. **No multi-agent delegation graphs.** Delegation is analyzed one hop at a
   time; chains of subagents (A→B→C) and delegation cycles are not modeled.
   *Resolves with:* a graph stage over delegation records.

4. **Configured-source conflict resolution is naive.** Most-permissive wins with
   provenance. Real environments need source-trust ranking (e.g., the IAM export
   outranks the marketing one-pager). *Resolves with:* weighted source trust.

5. **Reach inputs are asserted, not discovered.** Blast radius depends on the
   dossier's `reach` block; the engine cannot verify what data is actually in
   reach. Unstated reach defaults to false and is disclosed. *Resolves with:*
   data-flow analysis (explicitly out of scope per the brief's anti-scope-creep).

6. **Remediation templates are class-level, not environment-specific.** The
   engine drafts the right *shape* of fix; a human adapts it to the stack.
   The banned-phrase guard keeps templates concrete, not custom.

7. **No persistence, no diffing.** Each run is standalone; v0.1 cannot compare
   last quarter's assessment to this quarter's. *Resolves with:* an assessment
   store and a diff stage.

8. **Single-assessor perspective.** The engine does not model an adversarial
   agent actively evading observation. Findings describe authority as described
   and observed, not as a deceptive agent might hide it.

9. **Time and expiry are recorded, not enforced.** Intent `expires` is carried
   in the matrix but no stage evaluates "this delegation lapsed." *Resolves
   with:* a temporal stage (small, planned).

10. **English-only, JSON-in.** Dossiers are hand-built JSON. There is no intake
    UI, no natural-language dossier parser, no integrations.
