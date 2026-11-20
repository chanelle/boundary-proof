/* Landing-page copy. The ONLY thing that differs between A and B is the copy
   in VARIANT_COPY. Layout, visuals, demo, and the pilot CTA are shared. */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.MimoCopy = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var SHARED = {
    eyebrow: "Meet Mimo · AI agent authority intelligence",
    secondaryCta: "Explore the evidence",
    proofStrip: ["Intended", "Configured", "Observed"],
    disclosure: "Interactive concept demo using synthetic data. Runtime enforcement is a proposed capability, not currently verified.",
    pilotCta: "Book a 30-minute Mimo discovery call",
    callName: "30-minute Mimo discovery call",
    bookingBase: "https://cal.com/chanelleh/30min",
    pilotHeadline: "Mimo Authority Gap Review",
    pilotLine: "Start with a 30-minute Mimo discovery call. The pilot: one agent workflow, five business days after access and scope approval (proposed), synthetic or sanitized data first, pricing by proposal after scoping."
  };
  var VARIANT_COPY = {
    A: {
      angle: "curiosity",
      headline: "What did your AI agent do when <em>nobody was watching?</em>",
      subhead: "Your agents can have more access than the task requires. Mimo shows the gap between what they were asked to do, what their tools permit, and what the evidence says happened.",
      cta: "Reveal the gap"
    },
    B: {
      angle: "risk",
      headline: "Your AI agent may have permissions <em>you never intended.</em>",
      subhead: "Surface unnecessary tool access and evidence gaps before they become an operational surprise. Compare assigned tasks, configured capabilities, and observed behavior in one review.",
      cta: "Check agent permissions"
    }
  };
  function forVariant(v) {
    var c = VARIANT_COPY[v];
    if (!c) throw new Error("unknown variant " + v);
    var out = {};
    Object.keys(SHARED).forEach(function (k) { out[k] = SHARED[k]; });
    Object.keys(c).forEach(function (k) { out[k] = c[k]; });
    out.variant = v;
    return out;
  }
  return { SHARED: SHARED, VARIANT_COPY: VARIANT_COPY, forVariant: forVariant };
});
