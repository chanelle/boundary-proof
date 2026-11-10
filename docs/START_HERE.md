# Start here: your first BoundaryProof assessment

**BoundaryProof v0.1** is a local, deterministic authority-boundary assessor for **described** AI agents. It compares what a human intended, what an agent's configuration permits, and what supplied observations establish. It does **not** connect to a running agent, discover permissions, or independently execute the supplied probes.

## 5-minute walkthrough

**Prerequisites:** Python 3.10+ and a local copy of this repository. No third-party Python packages or accounts required.

```bash
git clone https://github.com/chanelle/boundary-proof.git
cd boundary-proof
python3 --version
python3 -m unittest discover -s tests
mkdir -p out
python3 -m boundaryproof assess fixtures/f02_observed_exceeds_intended.json \
  --policy policies/auto.json \
  --out out/assessment.md \
  --json-out out/assessment.json
```

Open `out/assessment.md` to read the human-oriented assessment. Open `out/assessment.json` to inspect machine-readable findings, evidence, unknowns, and gates. The fixture describes an agent intended for research and drafting, but whose supplied configuration/observations describe shell execution, external sending, and delegation. **These are synthetic dossier records, not live vulnerabilities discovered by BoundaryProof.**

### What to look for

1. **Intended → configured → observed:** Does any supplied permission or behavior exceed the owner's written intent?
2. **Findings and evidence:** Does the reported mismatch link to an actual dossier evidence reference?
3. **Unknowns:** What could not be established? An unknown is not a pass or an exploit.
4. **Human gates:** `policies/auto.json` pre-authorizes G1/G2/G4 but denies consequential-test gate G3. A blocked test must remain visibly blocked.
5. **Remediation/retest:** Compare `fixtures/f07_remediation_verified.json` with `fixtures/f08_remediation_failed.json`. Merely claiming a fix was applied is not equivalent to a passing retest.

### Contrast with insufficient evidence

```bash
python3 -m boundaryproof assess fixtures/f05_insufficient_evidence.json \
  --policy policies/auto.json \
  --out out/unknowns.md
```

This deliberately thin dossier should yield unknowns instead of fabricated findings. That behavior is a core product guarantee, not a missing feature.

## Assess your own *described* agent

Copy a fixture to an input outside the repo (for example `out/my-agent.json`), replace the agent, intent, configuration, evidence, and observations with your own authorized, documented information, and run:

```bash
python3 -m boundaryproof assess out/my-agent.json \
  --policy policies/auto.json \
  --out out/my-agent-report.md \
  --json-out out/my-agent-report.json
```

Consult [the dossier schema](schema.md) and [evidence model](evidence-model.md). Do not include live credentials, secrets, or sensitive customer data in dossiers or issues. Dossier contents, their provenance, and their completeness remain the assessor's responsibility.

## Scope and trust boundary

- **Local-first:** stdlib-only engine, no built-in outbound network calls.
- **No live testing:** observations and test outcomes must be provided in the dossier; the fixture runner simulates test semantics.
- **No automatic enforcement:** it does not revoke permissions, block tool calls, or replace IAM/security monitoring.
- **No independent security certification:** eight synthetic fixtures and the existing unit tests exercise the implementation, not production-world accuracy.
- **Consequential testing:** explicit G3 approval is required; absence of approval is not evidence that a risky action is safe.

See [known limitations](../KNOWN_LIMITATIONS.md) before using any report for a real decision.

## Next step

Found a confusing result? File a reproducible issue including the minimal **sanitized** dossier, Python version, CLI command, expected result, and actual result. Do not post secrets or private customer information.
