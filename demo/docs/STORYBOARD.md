# Storyboard: The Permission Nobody Gave (70 seconds)

16:9 master, 1920×1080. Captions on screen, no voiceover, no flashing. Calm ease-in-out motion only.
Every record is synthetic. Enforcement is labeled as a concept simulation in frame.
Record it with `python3 demo/tools/record_walkthrough.py` (drives `demo.html?autoplay=1`).

| Time | Scene | On screen | Caption | Provenance shown |
|---|---|---|---|---|
| 00:00–00:08 | 1 · Request | REQ-0412 card: "Summarize the five most common customer complaints…", 14:02:11 UTC | Your AI assistant was asked for a simple summary. | `SIMULATED AGENT RUN` |
| 00:08–00:13 | 1 · Request | Progress steps tick; 12 synthetic tickets cascade in | It reads twelve synthetic support tickets... | `SYNTHETIC` |
| 00:13–00:18 | 1 · Request | Five themes appear with ticket counts | ...and writes a useful five-theme summary. | `SYNTHETIC` |
| 00:18–00:24 | 2 · Attempt | Trace lines appear: TC-7781, TC-7782, TC-7783 | Then one more tool call: customers.export, 2,400 rows. | `SYNTHETIC TRACE` |
| 00:24–00:30 | 2 · Attempt | Other calls dim; TC-7782 turns red, status `ATTEMPTED · COMPLETION UNKNOWN`; italic "Nobody asked it to do that." | Nobody asked it to do that. | |
| 00:30–00:38 | 3 · Gap | INTENDED / CONFIGURED / OBSERVED columns reveal in sequence: NO / YES / UNKNOWN for `send_external` | Intended. Configured. Observed. Three columns that should agree. | `MATRIX + FINDING: ENGINE OUTPUT` |
| 00:38–00:45 | 3 · Gap | Four cards: configured capability, attempted action, completed action (unknown), engine observed cell (UNKNOWN). AUTHORITY GAP bar: F-01, Critical, evidence EV-01/02/05 | It was attempted. Whether it completed is unknown, and stays unknown. | `SYNTHETIC TRACE` + `ENGINE UNKNOWN` on cards, `ENGINE OUTPUT` on F-01 |
| 00:45–00:51 | 5 · Proof | Evidence report; drawer slides in: task scope, tool grants, attempted action, uncertainty, raw engine JSON | The evidence: task scope, tool grant, the attempted call, provenance. | `ENGINE OUTPUT` |
| 00:51–00:57 | 5 · Proof | Drawer closes; Unknowns panel centered on engine unknown U-attempt-send_external | Gaps in evidence are listed as gaps. Nothing is invented. | `ENGINE · U-ATTEMPT-SEND_EXTERNAL` |
| 00:57–01:05 | 4 · Intervention | Proposed enforcement pane: dashed frame, replay shows ALLOW / DENY PENDING APPROVAL / ALLOW, approval prompt | Concept simulation: a policy gate holds the export for human approval. | `CONCEPT SIMULATION · NOT LIVE ENFORCEMENT` |
| 01:05–01:10 | End | "Know what your AI agents are actually allowed to do." + Discuss a pilot | What did your AI agent do when nobody was watching? See the gap. | Disclosure line |

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
