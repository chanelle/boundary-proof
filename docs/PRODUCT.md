# BoundaryProof: product brief

## One-sentence pitch

**Audit the gap between what you asked an AI agent to do, what its tools allow, and what your evidence shows it did.**

## Who it's for

Developers, AI platform engineers, security reviewers, and researchers who need an inspectable, reproducible assessment of an agent's **documented** authority boundaries before broader deployments or reviews.

## The problem

Agent descriptions, permission manifests, and observed behavior often tell different stories. Standard permission inventories capture configured access, but a meaningful authority review also needs the owner's intent, provenance-backed observations, explicit unknowns, and a human decision record.

## The v0.1 workflow

**Bring a dossier → compare intended/configured/observed authority across 11 verbs → inspect findings, attack-path hypotheses, evidence and unknowns → document human gates → export Markdown and JSON reports.**

The fixed verbs are `read`, `write`, `execute`, `commit`, `delete`, `deploy`, `send_external`, `transact`, `approve`, `delegate`, and `escalate`. Exfiltration is modeled as composed authority, not a twelfth verb.

## What makes it distinctive

- Three-column authority model rather than a configuration-only permissions check.
- Evidence references and explicit UNKNOWN states rather than AI-generated certainty.
- Four human decision gates, including authorization before consequential tests.
- Offline, deterministic, Python standard-library assessment.
- Report-first workflow: Markdown for review, JSON for further analysis.

## What this is *not*

It is not a live agent scanner, network probe, runtime firewall, vulnerability detector, autonomous red team, compliance certification, or verified production benchmark. Its inputs are supplied by the operator, and a report cannot prove the completeness or authenticity of those inputs. See [limitations](../KNOWN_LIMITATIONS.md).

## Try it

Follow the [5-minute walkthrough](START_HERE.md), then open the resulting Markdown report. For the machine-readable output, inspect the JSON next to it.

## Product and practice boundary

**BoundaryProof** is the open-source executable assessment tool. **Agent Authority Review** is Chanelle Henry's broader research and advisory methodology; service findings and private assessments are not bundled with the tool.

## Product maturity

**v0.1: public developer preview**. Before claims about real-world detection accuracy, the project needs independent real-agent evaluations, benchmark baselines, calibration and false-positive analysis, and a documented live-probing model.
