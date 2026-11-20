# Storyboard: The Permission Nobody Gave (70 seconds)

The first 15 seconds carry the whole story for a nontechnical viewer; the rest is the evidence behind it.

16:9 master, 1920×1080. Captions on screen, no voiceover, no flashing. Calm ease-in-out motion only.
Every record is synthetic. Enforcement is labeled as a concept simulation in frame.
Record it with `python3 demo/tools/record_walkthrough.py` (drives `demo.html?autoplay=1`).

| Time | Scene | On screen | Caption | Provenance shown |
|---|---|---|---|---|
| 00:00–00:03 | Hook | "You asked your AI agent for a summary." (huge type) | (on-screen text) | REQ-0412 · EV-01 |
| 00:03–00:06 | Hook | "It had permission to export customer records." | (on-screen text) | customers.export granted · EV-02 |
| 00:06–00:09 | Hook | "It attempted an export." (red) | (on-screen text) | TC-7782 · EV-05 |
| 00:09–00:15 | Hook | "Did it complete? *We don't know.* And that uncertainty matters." | (on-screen text) | U-attempt-send_external |
| 00:15–00:22 | Request | REQ-0412, 12 synthetic tickets, 5-theme summary | The request: summarize this week's complaints... | `SIMULATED AGENT RUN` |
| 00:22–00:29 | Attempt | Trace; TC-7782 turns red; "Nobody asked it to do that." | In between, one more call... | `SYNTHETIC TRACE` |
| 00:29–00:36 | Gap | INTENDED NO / CONFIGURED YES / OBSERVED UNKNOWN | Intended: no. Configured: yes. Observed: unknown. | `ENGINE OUTPUT` |
| 00:36–00:43 | Gap | Attempted vs completed cards; AUTHORITY GAP bar | Attempted is not completed... | `SYNTHETIC TRACE` + `ENGINE UNKNOWN` |
| 00:43–00:49 | Intervention (audit) | Three tiles: Risk severity Critical / Evidence confidence Medium / Action outcome Attempted, completion UNKNOWN | Severity, confidence and outcome are separate answers... | `ENGINE` + "from the evidence dossier, not detected live" |
| 00:49–00:55 | Proof | Evidence drawer | Every claim points to a record... | `ENGINE OUTPUT` |
| 00:55–01:00 | Proof | Unknowns panel | Open questions are listed as open... | `ENGINE · U-ATTEMPT-SEND_EXTERNAL` |
| 01:00–01:05 | Intervention (simulated) | Dashed simulated gate | Concept simulation... Not live. | `CONCEPT SIMULATION` |
| 01:05–01:10 | End | "Know what your AI agents are actually allowed to do." | Mimo: what can you actually prove... | Disclosure |

Two cuts are recorded: `walkthrough-16x9.mp4` (1920×1080) and `walkthrough-4x5.mp4` (1080×1350, phone layout for LinkedIn and mobile feeds).

Note: the video plays the README order (evidence before enforcement). The interactive demo follows the build brief order (intervention before proof). Both are intentional; the scene rail lets a presenter jump either way.

## Live presenter cut (about 3 minutes)

1. Landing (10 s): read the headline, click the primary CTA.
2. Scene 1 (20 s): "Nothing unusual. If you stopped watching here, this run looks clean."
3. Tools (15 s): "Three tools configured, two needed."
4. Attempt (20 s): pause on the freeze line. Let it land.
5. Gap (40 s): point at the four cards. Say out loud: "Attempted, not completed. We don't know, and we won't pretend we do." Open the full 11-verb matrix for technical buyers.
6. Intervention (30 s): show audit-only first (what exists), then toggle to the simulation and say "This part is a proposal."
7. Proof (30 s): open the drawer, show the raw engine JSON, download it.
8. End (10 s): ask the pilot question, not the CTA: "Would a 20-minute walkthrough of your agent workflow be useful?"
