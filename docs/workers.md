# Worker (stage) responsibilities

Each stage owns one decision and is deliberately ignorant of the others'
internals. Stages communicate only through the typed assessment context.

| Stage | Module | Owns | Must NOT |
|---|---|---|---|
| matrix | `matrix.py` | The 33-cell I/C/O matrix; most-permissive merge with provenance | invent values for blank cells |
| mismatch | `matrix.py` | Detecting the 8 mismatch classes | promote anything to a finding |
| evidence | `evidence.py` | Registering evidence; linking; holding back unevidenced signals as Unknowns | accept non-registered evidence |
| severity | `severity.py` | Severity / likelihood / blast radius / confidence | consider exploitability |
| attack_paths | `attack_paths.py` | Composing multi-verb chains from evidenced mismatches | chain through UNKNOWN-only verbs |
| findings | `findings.py` | Promoting evidenced mismatches to findings | create a finding without registered evidence |
| remediation | `remediation.py` | Concrete remediation + verification test per class | use banned vague phrases (enforced) |
| plan | `planner.py` | Classifying tests READ_ONLY / SANDBOX_SAFE / CONSEQUENTIAL | execute anything |
| gates | `hitl.py` | The 4 gates; least-privilege gate context; the ledger | leak findings into G2 context |
| authorize | `planner.py` | G3 enforcement; blocked tests recorded as blocked | silently skip a blocked test |
| execute | `planner.py` | Running authorized tests (fixture semantics in v0.1) | run a consequential test without G3 |
| verify | `verification.py` | Binary pass/fail on retests | count "unverifiable" as pass |
| report | `report.py` | Markdown + JSON rendering | add new analysis |

## The independence property

The findings stage cannot see the remediation stage; the severity stage cannot
see the evidence store's internals beyond what it is given. If any stage is
replaced — a better severity model, a live test executor — the contract is the
assessment context schema, not shared mutable state. This is the product's answer
to its own thesis: authority is scoped, provenance is explicit, and no component
is omnipotent.
