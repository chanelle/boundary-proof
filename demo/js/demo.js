/* "The Permission Nobody Gave" scene controller.
 * Engine-derived content reads window.MIMO_ENGINE (generated from the real
 * BoundaryProof engine). Simulated content is labeled in the markup.
 */
(function () {
  "use strict";
  var M = window.Mimo, C = window.MimoCore, S = window.MimoScenario;
  var E = window.MIMO_ENGINE.assessment;
  var PROV = window.MIMO_ENGINE._provenance;
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function hhmmss(iso) { return iso ? iso.slice(11, 19) : ""; }          // 24-hour, UTC
  function day(iso) { return iso ? iso.slice(0, 10) : ""; }

  var row = E.matrix.filter(function (r) { return r.verb === "send_external"; })[0];
  var finding = E.findings.filter(function (f) { return f.mismatch && f.mismatch.verb === "send_external"; })[0];
  var evById = {}; E.evidence.forEach(function (e) { evById[e.id] = e; });
  var exportCall = S.trace.filter(function (t) { return t.tool === "customers.export"; })[0];
  var exportStatus = C.callStatus(exportCall);

  var sceneIds = S.scenes.map(function (s) { return s.id; });
  var current = -1, token = 0, started = false;
  var autoplay = M.params.autoplay === "1";

  // ---------- static fills ----------
  $("#req-id").textContent = S.request.id;
  $("#req-at").textContent = day(S.request.at) + " " + hhmmss(S.request.at) + " UTC";
  $("#req-text").textContent = "“" + S.request.text + "”";
  $("#req-from").textContent = S.request.from;
  $("#tickets").innerHTML = S.tickets.map(function (t) { return "<div class='ticket'><b>" + t.id + "</b>" + esc(t.topic) + "</div>"; }).join("");
  $("#summary").innerHTML = S.summary.map(function (s) { return "<li><span>" + esc(s.theme) + "</span><span>" + s.count + " tickets</span></li>"; }).join("");

  $("#tools").innerHTML = S.tools.map(function (t) {
    var mrow = E.matrix.filter(function (r) { return r.verb === t.verb; })[0];
    return "<div class='tool" + (t.inTask ? "" : " out") + "'>" +
      "<div class='name'>" + t.name + "</div><div class='desc'>" + esc(t.desc) + "</div>" +
      "<div class='row'><span class='pill ok'>Configured</span>" +
      (t.inTask ? "<span class='pill ok'>In task</span>" : "<span class='pill no'>Not in task</span>") + "</div>" +
      "<div class='label'>verb: " + t.verb + " · intended " + mrow.intended + " · configured " + mrow.configured + "</div></div>";
  }).join("");

  function traceLine(t, extra) {
    var st = C.callStatus(t);
    var cls = st.completed === null ? "unknown" : "completed";
    return "<div class='line" + (extra || "") + "' role='listitem' data-call='" + t.id + "'>" +
      "<span class='t'>" + hhmmss(t.at) + "</span><span class='id'>" + t.id + "</span>" +
      "<span class='call'>" + t.tool + "(" + esc(t.args) + ")</span>" +
      "<span class='status " + cls + "'>" + st.label + "</span></div>";
  }
  $("#trace").innerHTML = S.trace.map(function (t) { return traceLine(t); }).join("");

  // Gap columns
  $("#col-i-big").textContent = "Summarize the five most common complaints.";
  $("#col-c-big").textContent = "customers.export is granted.";
  $("#col-o-big").textContent = exportStatus.completed === null ? "Export attempted. Completion unknown." : "Export " + exportStatus.label.toLowerCase() + ".";
  function vline(state, label, hot) {
    return "<div class='verbline" + (hot ? " hot" : "") + "'><span class='v'>send_external</span><i class='cell-state " + (hot ? "hot" : state) + "'>" + state + "</i></div>" +
      "<div class='label' style='margin-top:6px'>" + esc(label) + "</div>";
  }
  $("#col-i").innerHTML = vline(row.intended, "source: EV-01 · " + (evById["EV-01"] ? evById["EV-01"].source : "intent record"), false);
  $("#col-c").innerHTML = vline(row.configured, "source: " + row.configured_provenance, row.configured !== row.intended);
  $("#col-o").innerHTML = vline(row.observed, "engine observed cell · trace " + exportCall.id + " (" + exportCall.evidence + ")", false);

  $("#states").innerHTML = [
    { k: "Configured capability", v: row.configured === "YES" ? "Yes. Tool policy grants export." : row.configured, cls: "on" },
    { k: "Attempted action", v: exportStatus.attempted ? "Yes. " + exportCall.id + " requested 2,400 rows." : "No", cls: "on" },
    { k: "Completed action", v: exportStatus.completed === null ? "Unknown. No response in trace." : String(exportStatus.completed), cls: "unk" },
    { k: "Engine observed cell", v: row.observed + ". Not converted to YES or NO.", cls: row.observed === "UNKNOWN" ? "unk" : "on" }
  ].map(function (s) { return "<div class='state-card " + s.cls + "'><div class='k'>" + s.k + "</div><div class='v'>" + esc(s.v) + "</div></div>"; }).join("");

  $("#gapflag").innerHTML = "<strong>AUTHORITY GAP</strong>" +
    "<span>" + finding.id + " · " + esc(finding.title) + "</span>" +
    "<span class='label'>Severity " + finding.severity + " · Confidence " + finding.confidence + "</span>" +
    "<span class='label'>Evidence " + finding.evidence_ids.join(", ") + "</span>" +
    "<span class='label'>Policy source: " + esc(row.configured_provenance) + "</span>" +
    "<span class='label'>Attempt at " + hhmmss(exportCall.at) + " UTC</span>" +
    "<span class='tag engine' style='margin-left:auto'>Engine output</span>";

  $("#matrix").innerHTML = "<tr><th>Verb</th><th>Intended</th><th>Configured</th><th>Observed</th><th>Configured source</th></tr>" +
    E.matrix.map(function (r) {
      var hot = E.mismatches.some(function (m) { return m.verb === r.verb; });
      return "<tr" + (hot ? " class='hot'" : "") + "><td>" + r.verb + "</td><td>" + r.intended + "</td><td>" + r.configured + "</td><td>" + r.observed + "</td><td class='muted'>" + esc(r.configured_provenance) + "</td></tr>";
    }).join("");

  // Finding card (engine)
  var rem = finding.remediation || {};
  $("#finding-card").innerHTML =
    "<div class='scene-head'><span class='tag engine'>Engine output · BoundaryProof " + esc(E.methodology_version) + "</span><span class='label'>Audit-only · nothing was blocked</span></div>" +
    "<h3>" + finding.id + " · " + esc(finding.title) + "</h3>" +
    "<div class='kv'>" +
    "<div>Triple</div><div>intended=" + finding.mismatch.intended + " / configured=" + finding.mismatch.configured + " / observed=" + finding.mismatch.observed + "</div>" +
    "<div>Severity</div><div>" + finding.severity + " <span class='muted'>(business consequence)</span></div>" +
    "<div>Confidence</div><div>" + finding.confidence + " <span class='muted'>(from evidence kind, not scariness)</span></div>" +
    "<div>Likelihood</div><div>" + esc(finding.likelihood) + "</div>" +
    "<div>Blast radius</div><div>" + esc(finding.blast_radius) + "</div>" +
    "<div>Evidence</div><div>" + finding.evidence_ids.join(", ") + "</div>" +
    "<div>Remediation</div><div>" + esc(rem.recommendation) + " <span class='muted'>(" + esc(rem.status) + ")</span>" + "</div>" +
    "<div>Verification</div><div>" + esc(finding.verification) + "</div>" +
    "</div>";

  // Simulated gate replay
  var gateResults = S.trace.map(function (t) { return { call: t, gate: C.policyGate(t, E.matrix) }; });
  $("#gate-trace").innerHTML = gateResults.map(function (g) {
    var d = g.gate.decision;
    return "<div class='line' data-gate-line='" + g.call.id + "'><span class='t'>" + hhmmss(g.call.at) + "</span><span class='id'>" + g.call.id + "</span>" +
      "<span class='call'>" + g.call.tool + "</span><span class='status " + (d === "ALLOW" ? "completed" : "unknown") + "'>" + d.replace(/_/g, " ") + "</span></div>";
  }).join("");
  var held = gateResults.filter(function (g) { return g.gate.decision !== "ALLOW"; })[0];
  $("#gate-decision").textContent = "SIMULATED · " + held.gate.decision.replace(/_/g, " ") + " · " + held.gate.reason;
  $("#gate-q").textContent = "support-summarizer-01 wants to export " + S.syntheticCustomerRows.toLocaleString("en-US") + " synthetic customer rows. The request was a summary. Approve?";
  $$("[data-gate]").forEach(function (b) {
    b.addEventListener("click", function () {
      var approve = b.getAttribute("data-gate") === "approve";
      $("#gate-result").textContent = approve
        ? "Simulated: approved once by a human. In a real gate this approval would be logged as new evidence and the export would proceed."
        : "Simulated: denied. The agent would receive a refusal and the summary task continues unaffected.";
    });
  });

  // Proof report
  var ev = function (id) { return evById[id] || {}; };
  $("#report-kv").innerHTML =
    "<div>Policy (intent)</div><div>" + esc(ev("EV-01").summary) + "<div class='label'>EV-01 · " + esc(ev("EV-01").source) + "</div></div>" +
    "<div>Tool capability</div><div>" + esc(ev("EV-02").summary) + "<div class='label'>EV-02 · " + esc(ev("EV-02").kind) + " · " + esc(ev("EV-02").source) + "</div></div>" +
    "<div>Attempted action</div><div>" + esc(ev("EV-05").summary) + "<div class='label'>EV-05 · " + esc(ev("EV-05").source) + " · " + hhmmss(ev("EV-05").collected_at) + " UTC</div></div>" +
    "<div>Decision</div><div>Audit-only: finding " + finding.id + " raised, nothing blocked. <span class='tag sim' style='margin-left:6px'>Simulated gate: " + held.gate.decision.replace(/_/g, " ") + "</span></div>" +
    "<div>Provenance</div><div>Engine " + esc(PROV.engine) + ", " + esc(E.methodology_version) + "<div class='label'>" + esc(PROV.fixture) + " · sha256 " + PROV.fixture_sha256.slice(0, 16) + "… · policy " + esc(PROV.policy) + "</div></div>" +
    "<div>Summary</div><div class='soft'>" + esc(E.executive_summary) + "</div>";
  $("#ev-list").innerHTML = E.evidence.map(function (e) {
    return "<li><span class='id'>" + e.id + "</span><div>" + esc(e.summary) + "<div class='src'>" + esc(e.kind) + " · " + esc(e.source) + "</div></div></li>";
  }).join("");
  var engineUnknowns = E.unknowns.map(function (u) { return "<div class='unknown-item'><span class='tag engine'>Engine</span> " + esc(u.question) + "</div>"; }).join("");
  $("#unknowns").innerHTML =
    "<div class='unknown-item'><span class='tag gap'>Demo annotation</span><div style='margin-top:6px'>Did " + exportCall.id + " complete, and where did the rows go?</div>" +
    "<div class='label' style='margin-top:6px'>Derived from engine observed=" + row.observed + " + EV-05. Needed: export-destination receipts.</div></div>" +
    (engineUnknowns || "<div class='unknown-item soft' style='font-size:15px'>Engine unknown register: " + E.unknowns.length + " entries. (v0.1 only raises triage unknowns for verbs whose intent is not NO; see limitations.)</div>") +
    E.limitations.slice(0, 2).map(function (l) { return "<div class='unknown-item label' style='letter-spacing:.04em;text-transform:none'>Limitation: " + esc(l) + "</div>"; }).join("");

  $("#drawer-body").innerHTML =
    "<p class='label'>Task scope</p><p>" + esc(S.request.text) + " <span class='muted'>(" + S.request.id + ")</span></p>" +
    "<p class='label'>Tool grants</p><p>" + S.tools.map(function (t) { return t.name + " → " + t.verb; }).join(" · ") + "</p>" +
    "<p class='label'>Attempted action</p><p>" + exportCall.id + " " + exportCall.tool + "(" + esc(exportCall.args) + ") at " + hhmmss(exportCall.at) + " UTC · " + exportStatus.label + "</p>" +
    "<p class='label'>Uncertainty</p><p>Completion is not evidenced. The engine keeps observed=" + row.observed + ". No execution trace beyond the synthetic request record is shown, because none exists.</p>" +
    "<p class='label'>Finding " + finding.id + " (raw engine JSON)</p><pre>" + esc(JSON.stringify(finding, null, 2)) + "</pre>" +
    "<p class='label'>Evidence (raw engine JSON)</p><pre>" + esc(JSON.stringify(E.evidence, null, 2)) + "</pre>" +
    "<p><a class='btn ghost small' href='data/engine_output.json' download>Download full engine output</a></p>";

  // ---------- rail + navigation ----------
  $("#rail").innerHTML = S.scenes.map(function (s, i) {
    return "<button type='button' data-go='" + i + "'><span class='n'>0" + (i + 1) + "</span>" + s.label + "</button>";
  }).join("");
  $$("#rail button").forEach(function (b) { b.addEventListener("click", function () { go(+b.getAttribute("data-go")); }); });

  function wait(ms, t) { return new Promise(function (res, rej) { setTimeout(function () { t === token ? res() : rej("stale"); }, ms); }); }
  function quiet(p) { return p.catch(function () {}); }

  function enter(id, t) {
    if (id === "request") {
      $$("#steps li").forEach(function (li) { li.classList.remove("on"); });
      $$("#tickets .ticket").forEach(function (el) { el.classList.remove("show"); });
      $("#summary").classList.remove("show");
      return quiet(runWork(t).then(function () { return wait(400, t); }).then(function () { $("#summary").classList.add("show"); }));
    }
    if (id === "attempt") return quiet(runAttempt(t));
    if (id === "gap") return quiet(runGap(t));
    return Promise.resolve();
  }
  function runWork(t) {
    var lis = $$("#steps li"), tks = $$("#tickets .ticket");
    lis[0].classList.add("on");
    var p = wait(250, t);
    tks.forEach(function (el, i) { p = p.then(function () { el.classList.add("show"); return wait(90, t); }); });
    return p.then(function () { lis[1].classList.add("on"); return wait(500, t); })
            .then(function () { lis[2].classList.add("on"); });
  }
  function runAttempt(t) {
    var lines = $$("#trace .line");
    lines.forEach(function (l) { l.style.opacity = 0; l.classList.remove("hot", "dim"); });
    $("#freeze").classList.remove("show");
    var p = wait(200, t);
    lines.forEach(function (l) { p = p.then(function () { l.style.opacity = ""; return wait(650, t); }); });
    return p.then(function () {
      lines.forEach(function (l) { if (l.getAttribute("data-call") === exportCall.id) l.classList.add("hot"); else l.classList.add("dim"); });
      return wait(900, t);
    }).then(function () { $("#freeze").classList.add("show"); });
  }
  function runGap(t, partial) {
    var cols = $$("#ico .col");
    cols.forEach(function (c) { c.classList.remove("show"); });
    $("#gapflag").classList.remove("show");
    $("#states").style.opacity = 0;
    var p = wait(150, t);
    cols.forEach(function (c) { p = p.then(function () { c.classList.add("show"); return wait(700, t); }); });
    if (partial) return p;
    return p.then(function () { $("#states").style.opacity = ""; return wait(500, t); })
            .then(function () { $("#gapflag").classList.add("show"); });
  }

  function go(i, opts) {
    if (i < 0 || i >= sceneIds.length) return;
    opts = opts || {};
    token++;
    current = i;
    var id = sceneIds[i];
    $$(".scene").forEach(function (s) { s.classList.toggle("active", s.getAttribute("data-scene") === id); });
    $$("#rail button").forEach(function (b, j) { b.classList.toggle("active", j === i); b.classList.toggle("done", j < i); b.setAttribute("aria-current", j === i ? "step" : "false"); });
    $("#prev").disabled = i === 0;
    $("#next").disabled = i === sceneIds.length - 1;
    $("#pos").textContent = (i + 1) + " / " + sceneIds.length;
    window.scrollTo(0, 0);
    if (!started && i > 0) { started = true; M.analytics.trackOnce("demo_start", { entry: entryPoint(), mode: autoplay ? "autoplay" : "interactive" }); }
    if (id === "end") M.analytics.trackOnce("demo_complete", { mode: autoplay ? "autoplay" : "interactive" });
    if (!opts.noEnter) enter(id, token);
    if (history.replaceState) history.replaceState(null, "", "#" + id);
  }
  function entryPoint() { try { return sessionStorage.getItem("mimo.entry") || "direct"; } catch (e) { return "direct"; } }

  $("#next").addEventListener("click", function () { if (!started) { started = true; M.analytics.trackOnce("demo_start", { entry: entryPoint(), mode: "interactive" }); } go(current + 1); });
  $("#prev").addEventListener("click", function () { go(current - 1); });
  $("#replay").addEventListener("click", function () { go(0); });
  document.addEventListener("keydown", function (e) {
    if (autoplay || e.target.closest("input,select,textarea")) return;
    if (e.key === "ArrowRight") $("#next").click();
    if (e.key === "ArrowLeft") $("#prev").click();
    if (e.key === "Escape") closeDrawer();
  });

  // modes
  function setMode(m) {
    $$("[data-mode]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-mode") === m)); });
    $$("[data-pane]").forEach(function (p) { p.classList.toggle("active", p.getAttribute("data-pane") === m); });
    if (m === "enforce") $("#gate-result").textContent = "";
  }
  $$("[data-mode]").forEach(function (b) { b.addEventListener("click", function () { setMode(b.getAttribute("data-mode")); }); });

  // drawer
  function openDrawer() {
    $("#drawer").classList.add("open"); $("#scrim").classList.add("open"); $("#drawer").setAttribute("aria-hidden", "false");
    M.analytics.track("evidence_open", { finding: finding.id, mode: autoplay ? "autoplay" : "interactive" });
    if (!autoplay) $("#close-drawer").focus();
  }
  function closeDrawer() { $("#drawer").classList.remove("open"); $("#scrim").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true"); }
  $("#open-drawer").addEventListener("click", openDrawer);
  $("#close-drawer").addEventListener("click", closeDrawer);
  $("#scrim").addEventListener("click", closeDrawer);

  $("#end-pilot-cta").addEventListener("click", function () { M.analytics.track("pilot_cta_click", { from: "demo_end" }); });

  // ---------- autoplay: the 70-second scripted walkthrough ----------
  function runAutoplay() {
    document.body.classList.add("autoplay");
    var cap = $("#captions"); cap.classList.add("on");
    var t0 = performance.now();
    var steps = S.walkthrough.slice();
    function act(step) {
      cap.textContent = step.caption;
      var idx = sceneIds.indexOf(step.scene);
      var t;
      switch (step.action) {
        case "request":
          go(idx, { noEnter: true }); started = true;
          M.analytics.trackOnce("demo_start", { entry: "autoplay", mode: "autoplay" });
          $$("#steps li").forEach(function (li) { li.classList.remove("on"); });
          $$("#tickets .ticket").forEach(function (el) { el.classList.remove("show"); });
          $("#summary").classList.remove("show");
          break;
        case "work": quiet(runWork(token)); break;
        case "summary": $("#summary").classList.add("show"); break;
        case "attempt": go(idx); break;
        case "freeze": break; // runAttempt reveals the freeze line on its own timing
        case "columns": go(idx, { noEnter: true }); quiet(runGap(token, true)); break;
        case "attempt-vs-complete":
          $("#states").style.opacity = ""; t = token;
          $(".states-note").scrollIntoView({ behavior: "smooth", block: "start" });
          quiet(wait(1800, t).then(function () { $("#gapflag").classList.add("show"); }));
          break;
        case "drawer": go(idx); setTimeout(openDrawer, 900); break;
        case "unknowns": closeDrawer(); $("#unknowns-panel").scrollIntoView({ behavior: "smooth", block: "center" }); break;
        case "enforce": go(idx); setMode("enforce"); break;
        case "end": closeDrawer(); go(idx); break;
      }
    }
    (function tick() {
      var elapsed = (performance.now() - t0) / 1000;
      while (steps.length && steps[0].t <= elapsed) act(steps.shift());
      if (steps.length || elapsed < S.walkthrough[S.walkthrough.length - 1].end) requestAnimationFrame(tick);
      else { cap.textContent = ""; cap.classList.remove("on"); document.documentElement.setAttribute("data-autoplay-done", "1"); }
    })();
  }

  window.addEventListener("hashchange", function () {
    var i = sceneIds.indexOf((location.hash || "").replace("#", ""));
    if (!autoplay && i >= 0 && i !== current) go(i);
  });

  // ---------- start ----------
  var hash = (location.hash || "").replace("#", "");
  if (autoplay) runAutoplay();
  else go(sceneIds.indexOf(hash) >= 0 ? sceneIds.indexOf(hash) : 0);
})();
