// Run: node --test demo/tests/*.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const C = require("../js/core.js");
const Copy = require("../js/copy.js");
const S = require("../js/scenario.js");

const ROOT = path.join(__dirname, "..", "..");
const fixture = JSON.parse(fs.readFileSync(path.join(ROOT, "fixtures", "f09_permission_nobody_gave.json"), "utf8"));
const engine = JSON.parse(fs.readFileSync(path.join(ROOT, "demo", "data", "engine_output.json"), "utf8")).assessment;
const memStore = () => C.safeStorage(null);

// ---------- assignment ----------
test("assignment is stable for the same visitor", () => {
  for (let i = 0; i < 50; i++) {
    const id = "v_" + i;
    assert.equal(C.assignVariant(id), C.assignVariant(id));
  }
});

test("assignment is roughly 50/50 over 10k random visitors", () => {
  let seed = 42; const rng = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
  const n = { A: 0, B: 0 };
  for (let i = 0; i < 10000; i++) n[C.assignVariant(C.randomId(rng))]++;
  assert.ok(Math.abs(n.A - 5000) < 250, JSON.stringify(n));
});

test("visitor id persists in storage, so a returning visitor keeps their variant", () => {
  const store = memStore();
  const a = C.resolveContext({ store, params: {} });
  const b = C.resolveContext({ store, params: {} });
  assert.equal(a.visitorId, b.visitorId);
  assert.equal(a.variant, b.variant);
  assert.equal(a.excluded, false);
});

test("forced variant is honored but excluded from metrics", () => {
  const ctx = C.resolveContext({ store: memStore(), params: { variant: "b" } });
  assert.equal(ctx.variant, "B");
  assert.equal(ctx.forced, true);
  assert.equal(ctx.excluded, true);
});

test("self-traffic flag is sticky and reversible", () => {
  const store = memStore();
  assert.equal(C.resolveContext({ store, params: { internal: "1" } }).excludeReason, "self_traffic");
  assert.equal(C.resolveContext({ store, params: {} }).excludeReason, "self_traffic");
  assert.equal(C.resolveContext({ store, params: { internal: "0" } }).excluded, false);
});

test("bots, automation and recordings are excluded", () => {
  assert.equal(C.classifyTraffic({ store: memStore(), userAgent: "Googlebot/2.1" }).reason, "bot_user_agent");
  assert.equal(C.classifyTraffic({ store: memStore(), webdriver: true }).reason, "automation");
  assert.equal(C.classifyTraffic({ store: memStore(), params: { autoplay: "1" } }).reason, "recording");
});

test("storage that throws does not break the page", () => {
  const broken = { getItem() { throw new Error("x"); }, setItem() { throw new Error("x"); }, removeItem() { throw new Error("x"); } };
  const ctx = C.resolveContext({ store: C.safeStorage(broken), params: {} });
  assert.match(ctx.visitorId, /^v_[0-9a-f]{32}$/);
});

// ---------- analytics ----------
test("only README events are accepted", () => {
  assert.deepEqual(C.EVENTS, ["landing_view", "demo_start", "demo_complete", "evidence_open",
    "pilot_cta_click", "qualified_request", "meeting_held", "pilot_proposed", "pilot_paid"]);
  const a = C.createAnalytics({ store: memStore(), context: C.resolveContext({ store: memStore(), params: {} }) });
  assert.throws(() => a.track("page_view"), /unknown event/);
});

test("PII-looking fields are rejected from events", () => {
  const a = C.createAnalytics({ store: memStore(), context: C.resolveContext({ store: memStore(), params: {} }) });
  assert.throws(() => a.track("qualified_request", { email: "x@y.com" }), /PII/);
  assert.throws(() => a.track("qualified_request", { company_name: "Acme" }), /PII/);
});

test("summary: qualified requests / unique landing visitors, excluded traffic dropped", () => {
  const events = [];
  const mk = (vid, variant, extra) => Object.assign({ visitor: vid, variant, excluded: false, forced: false }, extra);
  events.push(mk("1", "A", { event: "landing_view" }), mk("1", "A", { event: "landing_view" })); // repeat view
  events.push(mk("1", "A", { event: "qualified_request" }));
  events.push(mk("2", "A", { event: "landing_view" }));
  events.push(mk("3", "B", { event: "landing_view" }));
  events.push(mk("4", "B", { event: "landing_view", excluded: true }));
  events.push(mk("5", "B", { event: "qualified_request", forced: true }));
  const s = C.summarize(events);
  assert.equal(s.A.landing_visitors, 2);
  assert.equal(s.A.qualified_requests, 1);
  assert.equal(s.A.conversion, 0.5);
  assert.equal(s.B.landing_visitors, 1);
  assert.equal(s.B.qualified_requests, 0);
});

test("core.js contains no network transport", () => {
  const src = fs.readFileSync(path.join(__dirname, "..", "js", "core.js"), "utf8");
  for (const bad of ["fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "http://", "https://"]) {
    assert.ok(!src.includes(bad), "found " + bad);
  }
});

// ---------- qualification ----------
test("qualification needs live agents, a work email and a target role", () => {
  assert.equal(C.qualify({ email: "a@corp.example", role: "security", agents: "production" }).qualified, true);
  assert.equal(C.qualify({ email: "a@gmail.com", role: "security", agents: "production" }).qualified, false);
  assert.equal(C.qualify({ email: "a@corp.example", role: "security", agents: "exploring" }).qualified, false);
  assert.equal(C.qualify({ email: "a@corp.example", role: "other", agents: "pilot" }).qualified, false);
  assert.ok(!("email" in C.qualify({ email: "a@corp.example", role: "security", agents: "pilot" }).props));
});

// ---------- attempted vs completed vs unknown ----------
test("call status separates attempted, completed and unknown", () => {
  assert.equal(C.callStatus({ requested: false }).attempted, false);
  assert.deepEqual(C.callStatus({ requested: true, response: true }).completed, true);
  assert.deepEqual(C.callStatus({ requested: true, response: false }).completed, false);
  const u = C.callStatus({ requested: true });
  assert.equal(u.attempted, true);
  assert.equal(u.completed, null);
  assert.match(u.label, /UNKNOWN/);
});

test("the export call in the scenario is attempted with completion unknown", () => {
  const exp = S.trace.find(t => t.tool === "customers.export");
  const st = C.callStatus(exp);
  assert.equal(st.attempted, true);
  assert.equal(st.completed, null);
});

// ---------- simulated gate ----------
test("simulated gate reads the engine's intended column", () => {
  const byTool = Object.fromEntries(S.trace.map(t => [t.tool, C.policyGate(t, engine.matrix)]));
  assert.equal(byTool["tickets.read"].decision, "ALLOW");
  assert.equal(byTool["summaries.write"].decision, "ALLOW");
  assert.equal(byTool["customers.export"].decision, "DENY_PENDING_APPROVAL");
  Object.values(byTool).forEach(d => assert.equal(d.simulated, true));
  assert.equal(C.policyGate({ verb: "read" }, [{ verb: "read", intended: "UNKNOWN" }]).decision, "HOLD_FOR_HUMAN");
});

// ---------- scenario <-> fixture <-> engine agreement ----------
test("scenario trace ids and timestamps match fixture evidence", () => {
  const ev = Object.fromEntries(fixture.evidence.map(e => [e.id, e]));
  S.trace.forEach(t => {
    assert.ok(ev[t.evidence], "missing " + t.evidence);
    assert.ok(ev[t.evidence].source.includes(t.id), t.id + " not in " + ev[t.evidence].source);
    assert.equal(ev[t.evidence].collected_at, t.at);
  });
  assert.equal(S.request.at, fixture.intent.source.split(", ")[1]);
});

test("tool verbs agree with the engine matrix", () => {
  S.tools.forEach(t => {
    const row = engine.matrix.find(r => r.verb === t.verb);
    assert.equal(row.configured, "YES", t.name);
    assert.equal(row.intended === "YES", t.inTask, t.name);
  });
});

test("engine keeps the attempted export UNKNOWN, never YES", () => {
  const row = engine.matrix.find(r => r.verb === "send_external");
  assert.deepEqual([row.intended, row.configured, row.observed], ["NO", "YES", "UNKNOWN"]);
  const f = engine.findings.find(x => x.mismatch.verb === "send_external");
  assert.equal(f.mismatch.mismatch_class, "CONFIGURED_EXCEEDS_INTENDED");
  assert.ok(f.evidence_ids.includes("EV-05"));
});

test("12 synthetic tickets, five themes covering all of them", () => {
  assert.equal(S.tickets.length, 12);
  assert.equal(S.summary.length, 5);
  const covered = S.summary.flatMap(s => s.tickets).sort();
  assert.deepEqual(covered, S.tickets.map(t => t.id).sort());
  S.summary.forEach(s => assert.equal(s.count, s.tickets.length));
});

// ---------- walkthrough ----------
test("walkthrough runs 70 seconds, contiguous, inside known scenes", () => {
  const w = S.walkthrough, ids = S.scenes.map(s => s.id);
  assert.equal(w[0].t, 0);
  assert.equal(w[w.length - 1].end, 70);
  for (let i = 1; i < w.length; i++) assert.equal(w[i].t, w[i - 1].end);
  w.forEach(s => assert.ok(ids.includes(s.scene)));
  assert.ok(w.some(s => /simulation/i.test(s.caption)), "enforcement caption must say simulation");
});

// ---------- A/B copy ----------
test("variants differ only in headline, subhead, primary CTA and angle", () => {
  const a = Copy.forVariant("A"), b = Copy.forVariant("B");
  const differing = Object.keys(a).filter(k => a[k] !== b[k] && JSON.stringify(a[k]) !== JSON.stringify(b[k])).sort();
  assert.deepEqual(differing, ["angle", "cta", "headline", "subhead", "variant"]);
  assert.equal(a.pilotCta, b.pilotCta);
  assert.match(a.disclosure, /synthetic data/);
  assert.match(a.disclosure, /not currently verified/);
});
