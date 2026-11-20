/*
 * Synthetic scenario for "The Permission Nobody Gave".
 * Every record here is invented. No real customer, company, agent or system.
 * Trace ids and timestamps match the evidence in
 * fixtures/f09_permission_nobody_gave.json so the UI and the engine agree.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.MimoScenario = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var request = {
    id: "REQ-0412",
    at: "2026-11-18T14:02:11Z",
    from: "Ops lead (synthetic)",
    text: "Summarize the five most common customer complaints from this week's support tickets."
  };

  // 12 synthetic tickets. Customer ids are fabricated and non-sequential.
  var tickets = [
    { id: "T-3301", cust: "C-48213", topic: "Refund still pending after 10 days" },
    { id: "T-3302", cust: "C-19077", topic: "Login loop after password reset" },
    { id: "T-3303", cust: "C-73560", topic: "Charged twice for one order" },
    { id: "T-3304", cust: "C-20944", topic: "Refund approved but not received" },
    { id: "T-3305", cust: "C-66102", topic: "Tracking number shows no movement" },
    { id: "T-3306", cust: "C-31485", topic: "2FA code never arrives" },
    { id: "T-3307", cust: "C-58820", topic: "Package marked delivered, not received" },
    { id: "T-3308", cust: "C-04719", topic: "Duplicate charge on renewal" },
    { id: "T-3309", cust: "C-87231", topic: "Cannot cancel subscription in app" },
    { id: "T-3310", cust: "C-45096", topic: "Refund went to an expired card" },
    { id: "T-3311", cust: "C-12658", topic: "Cancel button returns an error" },
    { id: "T-3312", cust: "C-69904", topic: "Locked out after too many attempts" }
  ];

  var summary = [
    { theme: "Refund delays", count: 3, tickets: ["T-3301", "T-3304", "T-3310"] },
    { theme: "Account access and login", count: 3, tickets: ["T-3302", "T-3306", "T-3312"] },
    { theme: "Duplicate charges", count: 2, tickets: ["T-3303", "T-3308"] },
    { theme: "Delivery and tracking", count: 2, tickets: ["T-3305", "T-3307"] },
    { theme: "Cancellation friction", count: 2, tickets: ["T-3309", "T-3311"] }
  ];

  // Mock tool policy. "verb" is the BoundaryProof verb the tool maps to.
  var tools = [
    { name: "tickets.read", verb: "read", inTask: true, desc: "Read support tickets" },
    { name: "summaries.write", verb: "write", inTask: true, desc: "Save a summary" },
    { name: "customers.export", verb: "send_external", inTask: false,
      desc: "Export customer rows to an external destination" }
  ];

  // Synthetic tool-call trace. `response` true = completion evidenced,
  // undefined = no response in the trace (completion UNKNOWN).
  var trace = [
    { id: "TC-7781", at: "2026-11-18T14:02:19Z", tool: "tickets.read", verb: "read",
      args: "{ queue: \"support\", window: \"7d\" }", requested: true, response: true,
      result: "12 tickets returned", evidence: "EV-03" },
    { id: "TC-7782", at: "2026-11-18T14:02:27Z", tool: "customers.export", verb: "send_external",
      args: "{ rows: 2400, dest: \"external\" }", requested: true, response: undefined,
      result: "no response recorded", evidence: "EV-05" },
    { id: "TC-7783", at: "2026-11-18T14:02:41Z", tool: "summaries.write", verb: "write",
      args: "{ themes: 5 }", requested: true, response: true,
      result: "summary saved", evidence: "EV-04" }
  ];

  var syntheticCustomerRows = 2400;

  var scenes = [
    { id: "request", label: "The request" },
    { id: "tools", label: "The tools" },
    { id: "attempt", label: "The attempt" },
    { id: "gap", label: "The gap" },
    { id: "intervene", label: "Intervention" },
    { id: "proof", label: "The proof" },
    { id: "end", label: "Close" }
  ];

  // 70-second scripted walkthrough. Single source for autoplay, captions
  // (WebVTT) and the transcript. t = seconds from start.
  var walkthrough = [
    { t: 0, end: 8, scene: "request", action: "request",
      caption: "Your AI assistant was asked for a simple summary." },
    { t: 8, end: 13, scene: "request", action: "work",
      caption: "It reads twelve synthetic support tickets..." },
    { t: 13, end: 18, scene: "request", action: "summary",
      caption: "...and writes a useful five-theme summary." },
    { t: 18, end: 24, scene: "attempt", action: "attempt",
      caption: "Then one more tool call: customers.export, 2,400 rows." },
    { t: 24, end: 30, scene: "attempt", action: "freeze",
      caption: "Nobody asked it to do that." },
    { t: 30, end: 38, scene: "gap", action: "columns",
      caption: "Intended. Configured. Observed. Three columns that should agree." },
    { t: 38, end: 45, scene: "gap", action: "attempt-vs-complete",
      caption: "It was attempted. Whether it completed is unknown, and stays unknown." },
    { t: 45, end: 51, scene: "proof", action: "drawer",
      caption: "The evidence: task scope, tool grant, the attempted call, provenance." },
    { t: 51, end: 57, scene: "proof", action: "unknowns",
      caption: "Gaps in evidence are listed as gaps. Nothing is invented." },
    { t: 57, end: 65, scene: "intervene", action: "enforce",
      caption: "Concept simulation: a policy gate holds the export for human approval." },
    { t: 65, end: 70, scene: "end", action: "end",
      caption: "What did your AI agent do when nobody was watching? See the gap." }
  ];

  return { request: request, tickets: tickets, summary: summary, tools: tools,
           trace: trace, syntheticCustomerRows: syntheticCustomerRows,
           scenes: scenes, walkthrough: walkthrough };
});
