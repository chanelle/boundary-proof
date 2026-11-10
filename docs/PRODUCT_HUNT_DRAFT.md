# Product Hunt draft (not submitted)

## Name
BoundaryProof

## Tagline
Audit what your AI agents are actually allowed to do

## Short description
BoundaryProof is an open-source, offline Python tool for reviewing documented AI-agent authority. Compare intended, configured, and observed permissions across 11 verbs. Surface evidenced mismatches, unverified assumptions, approval gates, and remediation/retest status in Markdown and JSON reports.

## Maker's first comment (draft)
I built BoundaryProof after asking a question that conventional permission inventories don't answer clearly: What did the human actually delegate to this agent, how does that compare with its tool permissions, and what evidence shows what happened?

This developer preview uses three columns—intended, configured, and observed—and refuses to silently turn missing information into a pass. It includes eight synthetic scenarios, a local CLI, and inspectable reports. There are no third-party Python dependencies or built-in network requests.

A crucial limitation: v0.1 audits the agent *you describe*. It does not independently probe live systems or certify an agent as secure. I'm sharing it early to get feedback on the evidence model, usefulness of the reports, and real integration requirements.

Start with the five-minute example and tell me where the findings or unknowns are hard to interpret.

## Screenshot and demonstration plan
1. Hero: one clean product statement plus a three-column intended/configured/observed visual.
2. A terminal capture of the documented fixture command, with no fake output.
3. A screenshot of the resulting Markdown report highlighting evidence-backed findings.
4. A comparison of f07 and f08 showing verified vs failed remediation.
5. A clearly labeled limitations slide: dossier-based, not live probing.

## Launch criteria (must verify, not claim)
- CLI command executes on clean Python 3.10+ environment.
- CI passes on the supported Python versions.
- Generated Markdown and JSON are legible and useful to an unfamiliar developer.
- No secret/customer data in fixtures or screenshots.
- Public landing/demo link works and offers a clear path to the repository.
- Product Hunt copy and screenshots reviewed by maker.
- Do not submit automatically.
