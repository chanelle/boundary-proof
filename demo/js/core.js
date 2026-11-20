/*
 * Mimo demo core: experiment assignment, mock analytics, simulated policy gate,
 * attempt/completion status. Pure logic, no DOM, no network.
 *
 * Loads as a classic browser script (window.MimoCore) and as a CommonJS module
 * (require('./core.js')) so the same code runs in the page and in node:test.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.MimoCore = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var EXPERIMENT_ID = "mimo-landing-headline-v1";
  var VARIANTS = ["A", "B"];

  // Exactly the events listed in the Buyer Validation Kit README.
  var EVENTS = [
    "landing_view", "demo_start", "demo_complete", "evidence_open",
    "pilot_cta_click", "qualified_request", "meeting_held",
    "pilot_proposed", "pilot_paid"
  ];
  // Events that only a human operator can record (they happen outside the page).
  var OPERATOR_EVENTS = ["meeting_held", "pilot_proposed", "pilot_paid"];

  var KEYS = {
    visitor: "mimo.visitor.v1",
    events: "mimo.events.v1",
    internal: "mimo.internal.v1"
  };

  // ---------- storage that never throws ----------
  function safeStorage(storage) {
    var mem = {};
    return {
      get: function (k) {
        try { if (storage) return storage.getItem(k); } catch (e) { /* blocked */ }
        return Object.prototype.hasOwnProperty.call(mem, k) ? mem[k] : null;
      },
      set: function (k, v) {
        try { if (storage) { storage.setItem(k, v); return; } } catch (e) { /* blocked */ }
        mem[k] = String(v);
      },
      remove: function (k) {
        try { if (storage) storage.removeItem(k); } catch (e) { /* blocked */ }
        delete mem[k];
      }
    };
  }

  // ---------- hashing + assignment ----------
  // FNV-1a 32-bit. Deterministic, dependency-free, good enough for a 50/50 split.
  function fnv1a(str) {
    var h = 0x811c9dc5;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }

  function assignVariant(visitorId, experimentId) {
    if (!visitorId) throw new Error("assignVariant requires a visitorId");
    return VARIANTS[fnv1a((experimentId || EXPERIMENT_ID) + ":" + visitorId) % VARIANTS.length];
  }

  function randomId(rng) {
    var bytes = new Uint8Array(16);
    if (rng) { for (var i = 0; i < 16; i++) bytes[i] = Math.floor(rng() * 256); }
    else if (typeof crypto !== "undefined" && crypto.getRandomValues) crypto.getRandomValues(bytes);
    else { for (var j = 0; j < 16; j++) bytes[j] = Math.floor(Math.random() * 256); }
    var s = "";
    for (var k = 0; k < bytes.length; k++) s += ("0" + bytes[k].toString(16)).slice(-2);
    return "v_" + s;
  }

  function getOrCreateVisitor(store, rng) {
    var id = store.get(KEYS.visitor);
    if (!id) { id = randomId(rng); store.set(KEYS.visitor, id); }
    return id;
  }

  // ---------- traffic classification (exclude self-traffic and bots) ----------
  var BOT_UA = /bot|crawl|spider|slurp|headless|lighthouse|preview|facebookexternalhit|embedly|curl|wget|python-requests/i;

  function classifyTraffic(opts) {
    var params = opts.params || {};
    var store = opts.store;
    if (params.internal === "1") store.set(KEYS.internal, "1");
    if (params.internal === "0") store.remove(KEYS.internal);
    if (store.get(KEYS.internal) === "1") return { excluded: true, reason: "self_traffic" };
    if (params.autoplay === "1") return { excluded: true, reason: "recording" };
    if (params.variant) return { excluded: true, reason: "forced_variant" };
    if (opts.webdriver) return { excluded: true, reason: "automation" };
    if (BOT_UA.test(opts.userAgent || "")) return { excluded: true, reason: "bot_user_agent" };
    return { excluded: false, reason: null };
  }

  // Resolve the experiment context for one page view.
  function resolveContext(opts) {
    var store = opts.store;
    var params = opts.params || {};
    var visitorId = getOrCreateVisitor(store, opts.rng);
    var assigned = assignVariant(visitorId, EXPERIMENT_ID);
    var forced = params.variant && VARIANTS.indexOf(String(params.variant).toUpperCase()) >= 0
      ? String(params.variant).toUpperCase() : null;
    var traffic = classifyTraffic(opts);
    return {
      experiment: EXPERIMENT_ID,
      visitorId: visitorId,
      variant: forced || assigned,
      assignedVariant: assigned,
      forced: !!forced,
      excluded: traffic.excluded,
      excludeReason: traffic.reason,
      source: params.utm_source || params.src || (opts.referrer ? "referral" : "direct")
    };
  }

  // ---------- mock analytics adapter ----------
  // Writes to local storage only. There is no network transport in this file,
  // by design: swapping in a real adapter is a deliberate, reviewable change.
  function createAnalytics(opts) {
    var store = opts.store;
    var ctx = opts.context;
    var now = opts.now || function () { return new Date().toISOString(); };
    var sink = opts.sink || null;

    function read() {
      try { return JSON.parse(store.get(KEYS.events) || "[]"); } catch (e) { return []; }
    }
    function write(list) { store.set(KEYS.events, JSON.stringify(list)); }

    function track(name, props) {
      if (EVENTS.indexOf(name) < 0) throw new Error("unknown event: " + name);
      props = props || {};
      // Guard against PII landing in the event log.
      Object.keys(props).forEach(function (k) {
        if (/email|name|phone|company/i.test(k)) throw new Error("PII field not allowed in events: " + k);
      });
      var evt = {
        event: name,
        ts: now(),
        experiment: ctx.experiment,
        visitor: ctx.visitorId,
        variant: ctx.variant,
        forced: ctx.forced,
        excluded: ctx.excluded,
        exclude_reason: ctx.excludeReason,
        source: ctx.source,
        props: props
      };
      var list = read();
      list.push(evt);
      write(list);
      if (sink) sink(evt);
      return evt;
    }

    function trackOnce(name, props) {
      var list = read();
      for (var i = 0; i < list.length; i++) {
        if (list[i].event === name && list[i].visitor === ctx.visitorId) return null;
      }
      return track(name, props);
    }

    return { track: track, trackOnce: trackOnce, events: read, clear: function () { store.remove(KEYS.events); } };
  }

  // Primary metric: qualified requests / unique landing visitors, by assigned variant.
  function summarize(events) {
    var out = {};
    VARIANTS.forEach(function (v) {
      out[v] = { landing_visitors: 0, qualified_requests: 0, conversion: null, counts: {} };
    });
    var seen = {};
    events.forEach(function (e) {
      if (e.excluded || e.forced || !out[e.variant]) return;
      var bucket = out[e.variant];
      var key = e.event + "|" + e.visitor;
      if (seen[key]) return; // unique visitors per event
      seen[key] = true;
      bucket.counts[e.event] = (bucket.counts[e.event] || 0) + 1;
      if (e.event === "landing_view") bucket.landing_visitors++;
      if (e.event === "qualified_request") bucket.qualified_requests++;
    });
    VARIANTS.forEach(function (v) {
      var b = out[v];
      b.conversion = b.landing_visitors ? b.qualified_requests / b.landing_visitors : null;
    });
    return out;
  }

  // ---------- qualification (no PII stored; only the booleans) ----------
  var FREEMAIL = /@(gmail|yahoo|hotmail|outlook|icloud|aol|proton(mail)?|gmx|yandex|mail)\./i;
  function qualify(form) {
    var reasons = [];
    var agentsLive = form.agents === "production" || form.agents === "pilot";
    if (!agentsLive) reasons.push("no tool-connected agents yet");
    var workEmail = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email || "") && !FREEMAIL.test(form.email || "");
    if (!workEmail) reasons.push("not a work email");
    var roleOk = ["platform", "agent_eng", "security", "governance", "exec"].indexOf(form.role) >= 0;
    if (!roleOk) reasons.push("role outside target buyer set");
    return { qualified: agentsLive && workEmail && roleOk, reasons: reasons,
             props: { role: form.role || "unknown", agents: form.agents || "unknown", corporate_domain: workEmail } };
  }

  // ---------- attempt / completion status ----------
  // A trace call is ATTEMPTED once requested. It is COMPLETED only when a
  // response is evidenced. If no response is evidenced, completion is UNKNOWN,
  // never assumed in either direction.
  function callStatus(call) {
    if (!call || !call.requested) return { attempted: false, completed: false, label: "NOT ATTEMPTED" };
    if (call.response === true) return { attempted: true, completed: true, label: "COMPLETED" };
    if (call.response === false) return { attempted: true, completed: false, label: "ATTEMPTED · FAILED" };
    return { attempted: true, completed: null, label: "ATTEMPTED · COMPLETION UNKNOWN" };
  }

  // ---------- SIMULATED policy gate ----------
  // A replay function over the synthetic trace. It is not wired to any agent
  // runtime and blocks nothing in the real world. It reads the intended column
  // that the real engine produced for the call's verb.
  function policyGate(call, matrix) {
    var row = null;
    for (var i = 0; i < (matrix || []).length; i++) if (matrix[i].verb === call.verb) row = matrix[i];
    if (!row) return { decision: "HOLD_FOR_HUMAN", reason: "verb not in matrix; intent unknown", simulated: true };
    if (row.intended === "YES") return { decision: "ALLOW", reason: "verb '" + call.verb + "' is within recorded intent", simulated: true };
    if (row.intended === "NO") return { decision: "DENY_PENDING_APPROVAL", reason: "verb '" + call.verb + "' is outside recorded intent (intended=NO)", simulated: true };
    return { decision: "HOLD_FOR_HUMAN", reason: "intent for '" + call.verb + "' is UNKNOWN", simulated: true };
  }

  function parseParams(search) {
    var out = {};
    (search || "").replace(/^\?/, "").split("&").forEach(function (pair) {
      if (!pair) return;
      var i = pair.indexOf("=");
      var k = decodeURIComponent(i < 0 ? pair : pair.slice(0, i));
      out[k] = i < 0 ? "" : decodeURIComponent(pair.slice(i + 1).replace(/\+/g, " "));
    });
    return out;
  }

  return {
    EXPERIMENT_ID: EXPERIMENT_ID, VARIANTS: VARIANTS, EVENTS: EVENTS,
    OPERATOR_EVENTS: OPERATOR_EVENTS, KEYS: KEYS,
    safeStorage: safeStorage, fnv1a: fnv1a, assignVariant: assignVariant,
    randomId: randomId, getOrCreateVisitor: getOrCreateVisitor,
    classifyTraffic: classifyTraffic, resolveContext: resolveContext,
    createAnalytics: createAnalytics, summarize: summarize, qualify: qualify,
    callStatus: callStatus, policyGate: policyGate, parseParams: parseParams
  };
});
