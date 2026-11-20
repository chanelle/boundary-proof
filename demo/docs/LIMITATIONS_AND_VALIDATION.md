# Technical limitations and validation checklist

## Limitations (say these before a buyer finds them)

1. **No runtime enforcement exists.** The policy gate is `MimoCore.policyGate`, a pure function replaying a synthetic trace inside the page. It is not connected to any agent runtime and has never blocked a real call. It is labeled `CONCEPT SIMULATION · NOT LIVE ENFORCEMENT` everywhere it appears.
2. **No live monitoring.** BoundaryProof v0.1 reasons over a supplied dossier. The trace in the demo is written by hand, not captured from an agent.
3. **The engine has no ATTEMPTED state.** Verb cells are `YES | PARTIAL | NO | UNKNOWN`. The demo records the export attempt as evidence (EV-05) and the engine keeps observed=UNKNOWN. The attempted/completed/unknown split shown in the UI is a demo layer over the synthetic trace, labeled as such.
4. **The engine's unknown register is empty for this scenario.** v0.1 raises triage unknowns only for verbs whose intent is not NO, so "did the export complete?" is not an engine unknown. The demo shows it as a labeled annotation. Candidate engine change (not made here, to preserve behavior): raise an unknown when a verb has evidence of an attempt but observed is UNKNOWN.
5. **Verbs are not resource-scoped.** `read` covers tickets and customer records alike. The intent limits (`read_scope: support tickets only`) are carried as text and not evaluated.
6. **`customers.export` → `send_external` is a modeling choice.** An export to internal storage would map to `read` + `write` and produce a different finding. The fixture states the destination is external.
7. **Severity is Critical, confidence Medium, on configuration alone.** That is the engine's real output given `customer_data_in_reach: true` and no compensating control. Expect a buyer to ask why Critical without observed exfiltration. The honest answer: severity ranks business consequence; confidence carries the evidence strength.
8. **Analytics are local only.** Events live in one browser's `localStorage`. There is no aggregation across visitors. A real test needs a reviewed adapter, a consent/analytics disclosure, and a backend for the request form.
9. **Bot and self-traffic exclusion is heuristic.** User-agent matching, `navigator.webdriver`, a sticky `?internal=1` flag, forced variants, and autoplay recordings are excluded. Sophisticated bots will get through.
10. **Five buyer conversations cannot pick an A/B winner.** Treat them as qualitative discovery. The randomized landing test needs real traffic volume before conversion numbers mean anything.
11. **Name not cleared.** "Mimo" is provisional; no trademark, domain, or handle check has been done.

## Contradictions found in the source material

- The kit's chat summary gives different supporting copy for the variants than the README. The build uses the README copy, since the build prompt points to it.
- The end message differs across sources: the brief says "Know what your AI agents are actually allowed to do.", the README end screen says "Mimo makes agent authority visible.", and the video script closes on the Variant A question. The demo uses the brief's line as the headline, the README line as the eyebrow, and the video caption from the script.
- The repository README lists evidence kinds `direct | test | log | config | human_attested` and a dossier schema with top-level `agent_name`, `planned_tests`, `reach`, `retest`. The code accepts kinds `config | observation | test | interview | log | document` and reads `agent`, `proposed_tests`, `reach_context`, `retest_observations`. The demo fixture follows the code. The README was not changed.
- Engine report boilerplate says "Findings marked below High confidence rest on direct evidence", which reads backwards. Pre-existing, left untouched.

## Validation checklist

### Automated (run before every showing)

- [ ] `python3 -m unittest discover -s tests` → 54 pass (48 engine + 6 demo data)
- [ ] `node --test demo/tests/*.test.js` → 21 pass
- [ ] `python3 demo/tests/test_e2e.py` → 5 pass (variants share DOM; stable assignment; full funnel events; simulation labels; no external requests; no console errors; no horizontal overflow at 360 px)
- [ ] `python3 demo/build_demo_data.py && git diff --exit-code demo/data` → no drift

### Manual (5 minutes)

- [ ] Fresh private window: landing loads, one variant shown, `?debug=1` shows `counted`
- [ ] Reload: same variant
- [ ] `?internal=1` once on your own devices, then confirm the debug panel shows `EXCLUDED: self_traffic`
- [ ] Every scene: any engine-derived panel carries `ENGINE OUTPUT`; every simulated element carries `SIMULATED`, `SYNTHETIC`, `DEMO LAYER`, or `CONCEPT SIMULATION`
- [ ] Gap scene: completed action reads "Unknown", never "Yes"
- [ ] Phone (real device): all seven scenes readable, controls reachable, drawer closes
- [ ] Autoplay runs 70 s and ends on the close card
- [ ] Network tab: zero requests beyond the local server

### Before any real buyer sees it

- [ ] Naming clearance gate passed (or brand removed)
- [ ] Analytics disclosure written and an adapter chosen and reviewed
- [ ] Request form wired to a channel you will actually read, with the same no-email-in-analytics rule
- [ ] Decide whether to keep "Critical" visible or explain severity vs confidence up front
- [ ] Rehearse the limitations above out loud
