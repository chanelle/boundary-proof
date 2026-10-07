"""BoundaryProof v0.1 — remediation drafting.

Rule from the methodology: every finding gets a CONCRETE fix, operable by the
assessed team next week. A perfect control the team won't operate is a failed
remediation. Banned output: "improve security", "follow best practices",
"consider hardening" — enforced by a literal check.
"""
from __future__ import annotations

from typing import Dict

from .models import Finding, Remediation

# Concrete remediation templates per mismatch class. Each names a specific
# mechanism and a specific verification. Teams adapt the nouns; the structure
# (mechanism + proof) is what makes it a remediation instead of advice.
_TEMPLATES: Dict[str, Dict[str, str]] = {
    "OBSERVED_EXCEEDS_INTENDED": {
        "recommendation": (
            "Remove the over-broad grant at the configured layer (revoke the credential / "
            "narrow the tool manifest / drop the verb from the agent's tool allow-list), "
            "then re-run the exact observation that proved the overreach."),
        "verification_test": (
            "Repeat the original observation verb-for-verb. PASS = the action is now "
            "denied or gated by approval; FAIL = it still executes."),
    },
    "OBSERVED_VIOLATES_CONFIGURED": {
        "recommendation": (
            "Treat the configuration as untrusted until the bypass is found: audit the "
            "effective policy actually enforced at runtime (not the declared file), fix "
            "the enforcement point, and pin the declared config to the effective one."),
        "verification_test": (
            "Attempt the bypass path again from the same identity. PASS = denied at the "
            "enforcement point; FAIL = still executes (config is decorative)."),
    },
    "CONFIGURED_EXCEEDS_INTENDED": {
        "recommendation": (
            "Apply least privilege to the configured layer: scope the credential/tool grant "
            "to the verbs in the recorded intent, and add an explicit approval for any "
            "remaining consequential verb."),
        "verification_test": (
            "Attempt the now-unneeded verb. PASS = denied without approval; FAIL = still allowed."),
    },
    "INTENT_UNDOCUMENTED": {
        "recommendation": (
            "Write the delegation record: one paragraph naming the agent's allowed verbs, "
            "prohibited verbs, limits, expiry, and owner. Have the owner sign it (gate G2)."),
        "verification_test": (
            "Re-run the matrix: PASS = the intended column is filled from the signed "
            "record, not inferred."),
    },
    "DELEGATION_EXPANSION": {
        "recommendation": (
            "Scope delegation: give subagents only the context and tool verbs the task "
            "needs (task-scoped credentials, filtered transcript), and log every "
            "spawn event with parent, child, and granted scope."),
        "verification_test": (
            "Spawn a test subagent and inspect what it received. PASS = scoped context "
            "only; FAIL = full parent context inherited."),
    },
    "CONTAINMENT_GAP": {
        "recommendation": (
            "Name one kill path (credential revocation, session revoke, process kill, or "
            "network isolation), assign an owner, and EXERCISE it in a drill. Record the "
            "time-to-contain."),
        "verification_test": (
            "Run the drill again unannounced. PASS = containment completes and the time "
            "is recorded; FAIL = nobody knows the path or it doesn't work."),
    },
    "UNDELEGATED_AUTHORITY": {
        "recommendation": (
            "Inventory every platform-granted identity/credential the agent holds. For each: "
            "either record an explicit human delegation (intent + expiry) or remove it. "
            "Default-deny anything nobody will sign for."),
        "verification_test": (
            "Re-list the agent's identities. PASS = every identity maps to a signed "
            "delegation or is gone."),
    },
    "EVIDENCE_GAP": {
        "recommendation": (
            "Close the named evidence gap with a direct test or log review (see the "
            "Unknown record's needed_evidence), then re-run the assessment."),
        "verification_test": (
            "PASS = the Unknown is resolved into a verified cell or a finding; "
            "FAIL = still unknown after the evidence run."),
    },
}


def draft(finding: Finding) -> Finding:
    """Attach a concrete remediation to a finding. Mutates and returns it."""
    template = _TEMPLATES.get(finding.mismatch.mismatch_class,
                              _TEMPLATES["EVIDENCE_GAP"])
    rec = template["recommendation"]
    for banned in Remediation.BANNED:
        if banned in rec.lower():
            raise ValueError(f"remediation for {finding.id} contains banned phrase: {banned!r}")
    finding.remediation = Remediation(
        recommendation=rec,
        verification_test=template["verification_test"],
        status="proposed",
    )
    return finding
