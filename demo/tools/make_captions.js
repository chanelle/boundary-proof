// Generate WebVTT captions + transcript from the single walkthrough source.
// Run: node demo/tools/make_captions.js
"use strict";
const fs = require("fs");
const path = require("path");
const S = require("../js/scenario.js");
const out = path.join(__dirname, "..", "video");
const ts = s => { const m = Math.floor(s / 60), r = s % 60; return `00:${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}.000`; };
const mmss = s => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
let vtt = "WEBVTT\n\nNOTE Generated from demo/js/scenario.js (walkthrough). Synthetic data; enforcement is a concept simulation.\n\n";
S.walkthrough.forEach((w, i) => { vtt += `${i + 1}\n${ts(w.t)} --> ${ts(w.end)}\n${w.caption}\n\n`; });
let md = "# Transcript: The Permission Nobody Gave (70 s)\n\n" +
  "On-screen captions only, no voiceover. All records are synthetic. Enforcement is shown as a concept simulation.\n\n" +
  "| Time | Scene | Caption |\n|---|---|---|\n";
S.walkthrough.forEach(w => { md += `| ${mmss(w.t)}–${mmss(w.end)} | ${w.scene} | ${w.caption} |\n`; });
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, "captions.vtt"), vtt);
fs.writeFileSync(path.join(out, "transcript.md"), md);
console.log("wrote demo/video/captions.vtt and demo/video/transcript.md");
