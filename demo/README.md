# Mimo buyer demo: The Permission Nobody Gave

Interactive concept demo built on the BoundaryProof engine in this repository.
Synthetic data only. Mimo is a provisional name pending naming clearance.

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
python3 demo/tools/record_walkthrough.py # records video/out/walkthrough.{webm,mp4} (needs Playwright + Chrome, ffmpeg)
```

## Tests

```bash
python3 -m unittest discover -s tests    # 48 original + 5 attempted-action engine tests + 7 demo-data tests
node --test demo/tests/*.test.js         # 21 unit tests: assignment, analytics, gate, scenario/engine agreement, copy
python3 demo/tests/test_e2e.py           # 5 browser tests (skips if Playwright/Chrome missing)
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
| Pilot request form | No backend. Stores only role category, deployment stage, and a corporate-domain yes/no; never the email | On-page notice |

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
  docs/                    storyboard, pilot one-pager, limitations + validation checklist
  video/                   captions.vtt, transcript.md (recordings go to video/out/, git-ignored)
  tools/  tests/
```
