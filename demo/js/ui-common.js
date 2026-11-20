/* Shared page bootstrap: experiment context, mock analytics, ?debug=1 panel. */
(function () {
  "use strict";
  var C = window.MimoCore;
  var params = C.parseParams(window.location.search);
  var store = C.safeStorage((function () { try { return window.localStorage; } catch (e) { return null; } })());
  var ctx = C.resolveContext({
    store: store, params: params, userAgent: navigator.userAgent,
    webdriver: !!navigator.webdriver, referrer: document.referrer
  });
  var analytics = C.createAnalytics({
    store: store, context: ctx,
    sink: function (e) {
      if (window.console) console.info("[mimo analytics]", e.event, e);
      if (typeof window.MimoSink === "function") { try { window.MimoSink(e); } catch (err) { /* never break the page */ } }
      renderDebug();
    }
  });

  // Carry the visitor's variant through internal links for consistent copy,
  // without forcing it (forced=true would exclude them from metrics).
  function internalHref(path) {
    var keep = [];
    ["internal", "debug"].forEach(function (k) { if (params[k]) keep.push(k + "=" + encodeURIComponent(params[k])); });
    if (params.variant) keep.push("variant=" + encodeURIComponent(params.variant));
    var hashIdx = path.indexOf("#");
    var base = hashIdx >= 0 ? path.slice(0, hashIdx) : path;
    var hash = hashIdx >= 0 ? path.slice(hashIdx) : "";
    return base + (keep.length ? (base.indexOf("?") >= 0 ? "&" : "?") + keep.join("&") : "") + hash;
  }

  function renderDebug() {
    if (params.debug !== "1") return;
    var el = document.getElementById("mimo-debug");
    if (!el) {
      el = document.createElement("aside");
      el.id = "mimo-debug"; el.className = "debug"; el.setAttribute("aria-label", "Experiment debug panel");
      document.body.appendChild(el);
    }
    var events = analytics.events();
    var s = C.summarize(events);
    var rows = C.VARIANTS.map(function (v) {
      var b = s[v];
      return "<tr><td>" + v + "</td><td>" + b.landing_visitors + "</td><td>" + b.qualified_requests +
        "</td><td>" + (b.conversion === null ? "n/a" : (b.conversion * 100).toFixed(1) + "%") + "</td></tr>";
    }).join("");
    var recent = events.slice(-8).reverse().map(function (e) {
      return "<tr><td>" + e.ts.slice(11, 19) + "</td><td>" + e.event + "</td><td>" + e.variant + (e.excluded ? " (excl: " + e.exclude_reason + ")" : "") + "</td></tr>";
    }).join("");
    el.innerHTML =
      "<div class='label accent'>Debug · mock analytics (local only, no network)</div>" +
      "<div style='margin-top:6px'>visitor " + ctx.visitorId.slice(0, 12) + "… · variant <b>" + ctx.variant + "</b>" +
      (ctx.forced ? " (forced)" : "") + " · assigned " + ctx.assignedVariant +
      (ctx.excluded ? " · <span class='alert'>EXCLUDED: " + ctx.excludeReason + "</span>" : " · counted") + "</div>" +
      "<table><tr><th>Var</th><th>Visitors</th><th>Qualified</th><th>Conv</th></tr>" + rows + "</table>" +
      "<div class='muted'>Excluded and forced-variant events are dropped from the summary. " + events.length + " events stored.</div>" +
      "<table>" + recent + "</table>" +
      "<div class='row'>" +
      C.OPERATOR_EVENTS.map(function (n) { return "<button class='btn ghost small' data-op='" + n + "'>log " + n + "</button>"; }).join("") +
      "<button class='btn ghost small' data-act='export'>export json</button>" +
      "<button class='btn ghost small' data-act='clear'>clear</button></div>";
    el.querySelectorAll("[data-op]").forEach(function (b) {
      b.onclick = function () { analytics.track(b.getAttribute("data-op"), { logged_by: "operator" }); };
    });
    el.querySelector("[data-act=export]").onclick = function () {
      var blob = new Blob([JSON.stringify(events, null, 2)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = "mimo-events.json"; a.click();
    };
    el.querySelector("[data-act=clear]").onclick = function () { analytics.clear(); renderDebug(); };
  }

  window.Mimo = { params: params, store: store, ctx: ctx, analytics: analytics, internalHref: internalHref, renderDebug: renderDebug };
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("a[data-internal]").forEach(function (a) { a.setAttribute("href", internalHref(a.getAttribute("href"))); });
    renderDebug();
  });
})();
