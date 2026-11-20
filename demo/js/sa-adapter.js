/*
 * Production-only bridge from the local mock analytics to Simple Analytics,
 * which becomingbeta.com already uses (cookieless, no personal data).
 *
 * Rules:
 * - Sends nothing for excluded traffic (self, bots, automation, recordings)
 *   or forced-variant QA views.
 * - Each event name goes out at most once per browser, so dashboard counts
 *   approximate unique visitors per variant.
 * - Event names carry only the event and variant, e.g. mimo_landing_view_a.
 *   No visitor id, no props, no personal data.
 * Loaded only by the production build (demo/tools/build_site.py).
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else {
    root.MimoSA = api;
    root.MimoSink = api.createSink({
      store: root.MimoCore.safeStorage((function () { try { return root.localStorage; } catch (e) { return null; } })()),
      send: function (name) { if (typeof root.sa_event === "function") root.sa_event(name); }
    });
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var SENT_KEY = "mimo.sa.sent.v1";
  var FORWARD = ["landing_view", "demo_start", "demo_complete", "evidence_open", "pilot_cta_click"];

  function eventName(evt) {
    return ("mimo_" + evt.event + "_" + String(evt.variant || "x")).toLowerCase().replace(/[^a-z0-9_]/g, "_");
  }

  function createSink(opts) {
    function sent() { try { return JSON.parse(opts.store.get(SENT_KEY) || "{}"); } catch (e) { return {}; } }
    return function (evt) {
      if (!evt || evt.excluded || evt.forced) return null;
      if (FORWARD.indexOf(evt.event) < 0) return null;
      var name = eventName(evt), s = sent();
      if (s[name]) return null;
      s[name] = 1;
      opts.store.set(SENT_KEY, JSON.stringify(s));
      opts.send(name);
      return name;
    };
  }
  return { createSink: createSink, eventName: eventName, FORWARD: FORWARD, SENT_KEY: SENT_KEY };
});
