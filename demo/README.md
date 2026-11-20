# Mimo buyer demo: The Permission Nobody Gave

Interactive concept demo built on the BoundaryProof engine in this repository.
Synthetic data only. Mimo is a provisional name pending naming clearance.

**Positioning:** Mimo answers *what can you actually prove about your AI agent's authority and behavior?* It separates authority, capability, attempts, completed actions and unresolved questions, and ties each to a record. It works from a supplied evidence dossier; it does not monitor or block agents live.

## Run it locally

No build step, no dependencies, no network calls.

```bash
cd boundary-proof/demo
python3 -m http.server 8765
# open http://localhost:8765/              landing page (A/B assigned)
#      http://localhost:8765/demo.html     interactive demo
#      http://localhost:8765/pilot.html    pilot one-pager + request form
```

Opening `index.html` straight from disk (file://) also works in most browsers.

| URL flag | Effect |
|---|---|
| `?variant=A` / `?variant=B` | Force a landing variant for QA. Forced views are excluded from metrics. |
| `?internal=1` | Mark this browser as self-traffic (sticky). `?internal=0` clears it. |
| `?debug=1` | Show the experiment panel: variant, exclusion status, per-variant funnel, event log, export, and buttons to log operator events (`meeting_held`, `pilot_proposed`, `pilot_paid`). |
| `demo.html?autoplay=1` | Run the 70-second scripted walkthrough with on-screen captions. Tagged as a recording and excluded from metrics. |
| `demo.html#gap` (or any scene id) | Deep-link to a scene. `#proof` is where "Explore the evidence" lands. |

Keyboard: ← → move between scenes, Esc closes the evidence drawer.

## Regenerate engine data

```bash
python3 demo/build_demo_data.py          # runs the real engine on fixtures/f09_permission_nobody_gave.json
node demo/tools/make_captions.js         # regenerates video/captions.vtt and video/transcript.md
python3 demo/tools/record_walkthrough.py # records video/out/walkthrough-16x9.mp4 (1920x1080) and walkthrough-4x5.mp4 (1080x1350, phone layout)
```

## Production build and deploy (becomingbeta.com/mimo/)

```bash
python3 demo/tools/build_site.py     # -> demo/dist/mimo/ (adds Simple Analytics + adapter; local demo stays offline)
bash deploy/deploy_mimo.sh           # you run it: hidden cPanel token prompt, read-only check, plan, type "yes"
```

The deploy touches only `/home/chanpdrb/becomingbeta.com/mimo/`, creates its folders, uploads 19 files, then checks every key file live (HTTP 200 + checksum) and that the existing home page still serves. It refuses to run if `/mimo` exists unless you pass `--update`. Tested end to end against a mock cPanel; not yet run against the real server.

**Reading the A/B result:** visitors per variant = Simple Analytics events `mimo_landing_view_a` / `_b`; bookings per variant = Cal.com bookings whose `utm_content` is `variant_A` / `variant_B` and `utm_term` is `counted`. Primary metric = bookings ÷ visitors, per variant.

## Tests

```bash
python3 -m unittest discover -s tests    # 48 original + 7 attempted-action engine tests + 7 demo-data tests
node --test demo/tests/*.test.js         # 25 unit tests: assignment, analytics, gate, scenario/engine agreement, copy
python3 demo/tests/test_e2e.py           # 8 browser tests (incl. production build with analytics stubbed) (skips if Playwright/Chrome missing)
```

## What is real, what is simulated

| Element | Source | Label in UI |
|---|---|---|
| I/C/O matrix (11 verbs), finding F-01 and F-02, severity, confidence, remediation text, evidence register, executive summary | **Real BoundaryProof engine output** over a synthetic fixture (`demo/data/engine_output.json`, regenerated and diff-checked by tests) | `ENGINE OUTPUT` (solid lime) |
| Support request, 12 tickets, 5-theme summary, tool-call trace (TC-7781/82/83) | Synthetic scenario (`demo/js/scenario.js`); ids and timestamps match the fixture's evidence | `SYNTHETIC`, `SIMULATED AGENT RUN` |
| Attempted vs completed vs unknown cards | Attempt/response read from the synthetic trace; the open question is the engine's own `U-attempt-send_external` | `SYNTHETIC TRACE` + `ENGINE UNKNOWN` |
| "Did the export complete?" | **Engine unknown** `U-attempt-send_external`, raised because the observation carries `attempted: true` with `result: UNKNOWN` | `ENGINE · U-ATTEMPT-SEND_EXTERNAL` |
| Policy gate (deny, request approval) | `MimoCore.policyGate`, a pure function replaying the synthetic trace against the engine's intended column. Connected to nothing | `CONCEPT SIMULATION · NOT LIVE ENFORCEMENT` (dashed frame) |
| Analytics | Mock adapter writing to `localStorage`. No transport exists in code (a test enforces this) | `?debug=1` panel |
| Pilot booking | Real handoff to the 30-minute Mimo discovery call at cal.com/chanelleh/30min, new tab. The link carries `utm_source/medium/campaign/content/term` + `metadata[mimo_variant]`, so each booking shows which landing variant the visitor saw (host-only, on the booking details page). Nothing is booked until the visitor confirms on Cal.com | On-page notice |
| Live analytics (production build only) | Simple Analytics, which becomingbeta.com already uses (cookieless). `js/sa-adapter.js` sends `mimo_<event>_<variant>` once per browser per event; excluded and forced traffic sends nothing | none needed |
| Finding outcome | "Attempted, completion UNKNOWN" comes from the evidence dossier (synthetic trace TC-7782 / EV-05), not from Mimo observing anything | "From the evidence dossier … not detected live" |

## Files

```
demo/
  index.html  demo.html  pilot.html
  css/style.css            Redacted visual system (Fraunces + IBM Plex Mono, self-hosted, OFL)
  js/core.js               assignment, traffic exclusion, mock analytics, qualification, call status, simulated gate
  js/copy.js               A/B copy; the only thing that differs between variants
  js/scenario.js           synthetic scenario + 70 s walkthrough (single source for autoplay, captions, transcript)
  js/engine-data.js        GENERATED from the engine
  js/demo.js  js/ui-common.js
  data/engine_output.json  GENERATED from the engine
  docs/                    storyboard, pilot one-pager, outreach kit, limitations + validation checklist
  video/                   captions.vtt, transcript.md (recordings go to video/out/, git-ignored)
  tools/  tests/
```
