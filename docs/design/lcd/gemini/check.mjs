// Run from any directory: node docs/design/lcd/gemini/check.mjs
// Executes actual Candidate B inline JavaScript in a Node vm with a simulated DOM.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const file = new URL("../../../../opendesign/mockups/gemini-b/index.html", import.meta.url);
const html = readFileSync(file, "utf8");

// 1. Static Geometry & Resource Invariants
assert.match(html, /width:\s*820px;\s*height:\s*320px;/);
assert.match(html, /SYNTHETIC TELEMETRY/);
assert.doesNotMatch(html, /<script[^>]+src=|<link[^>]+href=["'](?:https?:)?\/\/|@import|fetch\(|XMLHttpRequest|WebSocket/);

// Trailing whitespace invariant
const lines = html.split("\n");
lines.forEach((line, idx) => {
  assert.equal(/[ \t]+$/.test(line), false, `Line ${idx + 1} has trailing whitespace`);
});

// Extract script
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1, "Expected exactly 1 inline script in Candidate B");
const scriptCode = scripts[0][1];

// Helper to create an element mock
function createElementMock(id, initialValue = "") {
  const classListSet = new Set();
  return {
    id,
    value: initialValue,
    textContent: "",
    innerHTML: "",
    style: {},
    classList: {
      add: (cls) => classListSet.add(cls),
      remove: (cls) => classListSet.delete(cls),
      toggle: (cls, force) => {
        if (force === undefined) {
          if (classListSet.has(cls)) classListSet.delete(cls);
          else classListSet.add(cls);
        } else if (force) {
          classListSet.add(cls);
        } else {
          classListSet.delete(cls);
        }
      },
      contains: (cls) => classListSet.has(cls)
    },
    get className() {
      return Array.from(classListSet).join(" ");
    },
    set className(val) {
      classListSet.clear();
      if (val) val.split(/\s+/).filter(Boolean).forEach((c) => classListSet.add(c));
    }
  };
}

// Elements tracked by ID
const elementIds = [
  "list-mode",
  "screen-direct",
  "state-selector",
  "pill-state",
  "notice-strip",
  "stat-link",
  "stat-src-age",
  "stat-rcv-age",
  "stat-cache",
  "clock-display",
  "quota-page-badge",
  "quota-primary-label",
  "quota-5h-val",
  "quota-5h-rem",
  "quota-5h-rst",
  "bar-5h-fill",
  "bar-5h-track",
  "quota-secondary-label",
  "quota-wk-val",
  "quota-wk-rem",
  "quota-wk-rst",
  "sess-in",
  "sess-out",
  "sess-cached",
  "sess-reason",
  "sess-total",
  "sess-src-total",
  "session-obs-time"
];

const elements = Object.fromEntries(elementIds.map((id) => [id, createElementMock(id)]));
elements["list-mode"].value = "common";
elements["screen-direct"].value = "0";
elements["state-selector"].value = "normal";

// Nav tabs and screen views for BOOT 3-screen cycling
const navTabs = [createElementMock("nav-0"), createElementMock("nav-1"), createElementMock("nav-2")];
const screenViews = [createElementMock("view-usage"), createElementMock("view-global"), createElementMock("view-status")];
navTabs[0].classList.add("active");
screenViews[0].classList.add("active");

const documentMock = {
  getElementById: (id) => {
    if (!elements[id]) {
      elements[id] = createElementMock(id);
    }
    return elements[id];
  },
  querySelectorAll: (selector) => {
    if (selector === ".nav-tab") return navTabs;
    if (selector === ".screen-view") return screenViews;
    return [];
  }
};

const sandbox = {
  document: documentMock,
  console: console
};

const context = vm.createContext(sandbox);
vm.runInContext(scriptCode, context);

const run = (expr) => vm.runInContext(expr, context);

// Test 1: Verify Initial Normal State & F2 Totals
run('applyState("normal")');
assert.equal(elements["pill-state"].textContent, "NORMAL");
assert.equal(elements["sess-total"].textContent, "141,200");
assert.equal(elements["sess-src-total"].textContent, "141,200");
assert.equal(elements["sess-in"].textContent, "124,800");
assert.equal(elements["sess-out"].textContent, "16,400");
assert.equal(elements["sess-cached"].textContent, "89,600");
assert.equal(elements["sess-reason"].textContent, "2,300");
assert.equal(elements["session-obs-time"].textContent, "OBS: 17:10:00Z");
assert.equal(elements["quota-5h-val"].innerHTML, "42<span>%</span>");
assert.equal(elements["quota-5h-rem"].textContent, "58%");
assert.equal(elements["quota-wk-val"].textContent, "18% USED");
assert.equal(elements["quota-wk-rem"].textContent, "82%");
assert.equal(elements["stat-src-age"].textContent, "0s Fresh");
assert.equal(elements["stat-rcv-age"].textContent, "0s Nominal");

// Test 2: F1 Transition Sequence 1: Normal -> Unknown -> Error
// Must retain lastGoodCache internally during unknown, then restore prior values & OBS 17:10:00Z on error!
run('applyState("unknown")');
assert.equal(elements["sess-total"].textContent, "--");
assert.equal(elements["sess-src-total"].textContent, "--");
assert.equal(elements["quota-5h-val"].innerHTML, "--<span>%</span>");
assert.equal(elements["session-obs-time"].textContent, "OBS: UNKNOWN");
assert.equal(run("lastGoodCache.hasCache"), true, "lastGoodCache must NOT be deleted upon unknown");

run('applyState("error")');
assert.equal(elements["pill-state"].textContent, "ERROR");
assert.equal(elements["notice-strip"].textContent.includes("RETAINING LAST-GOOD STATE (OBS 17:10:00Z)"), true);
assert.equal(elements["sess-total"].textContent, "141,200");
assert.equal(elements["sess-src-total"].textContent, "141,200");
assert.equal(elements["sess-in"].textContent, "124,800");
assert.equal(elements["quota-5h-val"].innerHTML, "42<span>%</span>");
assert.equal(elements["session-obs-time"].textContent, "OBS: 17:10:00Z");
assert.equal(elements["stat-cache"].textContent, "LAST-GOOD RETAINED");

// Test 3: F1 Transition Sequence 2: Normal -> Waiting -> Error
run('applyState("normal")');
run('applyState("waiting")');
assert.equal(elements["sess-total"].textContent, "...");
assert.equal(elements["quota-5h-val"].innerHTML, "...<span>%</span>");
assert.equal(elements["session-obs-time"].textContent, "OBS: WAITING");
assert.equal(run("lastGoodCache.hasCache"), true, "lastGoodCache must NOT be deleted upon waiting");

run('applyState("error")');
assert.equal(elements["sess-total"].textContent, "141,200");
assert.equal(elements["quota-5h-val"].innerHTML, "42<span>%</span>");
assert.equal(elements["session-obs-time"].textContent, "OBS: 17:10:00Z");

// Test 4: F1 Transition Sequence 3: Normal -> Unknown -> Disconnected
run('applyState("normal")');
run('applyState("unknown")');
run('applyState("disconnected")');
assert.equal(elements["notice-strip"].textContent.includes("LAST-GOOD VALUES PRESERVED (OBS 17:10:00Z)"), true);
assert.equal(elements["sess-total"].textContent, "141,200");
assert.equal(elements["quota-5h-val"].innerHTML, "42<span>%</span>");
assert.equal(elements["session-obs-time"].textContent, "OBS: 17:10:00Z");
assert.equal(elements["stat-cache"].textContent, "LAST-GOOD RETAINED");

// Test 5: Explicit Cold Start / No Cache Scenarios
run('applyState("cold_error")');
assert.equal(elements["sess-total"].textContent, "--");
assert.equal(elements["quota-5h-val"].innerHTML, "--<span>%</span>");
assert.equal(elements["stat-cache"].textContent, "NO CACHE");
assert.equal(elements["notice-strip"].textContent.includes("NO PRIOR CACHE AVAILABLE (COLD START)"), true);

run('applyState("cold_disconnected")');
assert.equal(elements["sess-total"].textContent, "--");
assert.equal(elements["quota-5h-val"].innerHTML, "--<span>%</span>");
assert.equal(elements["stat-cache"].textContent, "NO CACHE");
assert.equal(elements["notice-strip"].textContent.includes("NO PRIOR CACHE AVAILABLE (COLD START)"), true);

// Test 6: Source Age 299s / 300s / 301s Boundaries & Independent Receive Age
// 299s: Available / Fresh (no warning banner)
run('applyState("source_stale_299")');
assert.equal(elements["notice-strip"].style.display, "none");
assert.equal(elements["stat-src-age"].textContent, "299s (Available)");
assert.equal(elements["stat-rcv-age"].textContent, "0s Fresh");
assert.equal(elements["session-obs-time"].textContent, "OBS: 17:05:01Z"); // Exact math: 17:10:00Z - 299s = 17:05:01Z

// 300s: Stale boundary reached (warning banner)
run('applyState("source_stale_300")');
assert.equal(elements["notice-strip"].style.display, "block");
assert.equal(elements["notice-strip"].textContent.includes("SOURCE STALE"), true);
assert.equal(elements["stat-src-age"].textContent, "300s (Stale)");
assert.equal(elements["stat-rcv-age"].textContent, "0s Fresh");
assert.equal(elements["session-obs-time"].textContent, "OBS: 17:05:00Z");

// 301s: Stale (warning banner)
run('applyState("source_stale_301")');
assert.equal(elements["notice-strip"].style.display, "block");
assert.equal(elements["stat-src-age"].textContent, "301s (Stale)");
assert.equal(elements["stat-rcv-age"].textContent, "0s Fresh");
assert.equal(elements["session-obs-time"].textContent, "OBS: 17:04:59Z");

// Default source_stale also behaves as 301s
run('applyState("source_stale")');
assert.equal(elements["stat-src-age"].textContent, "301s (Stale)");
assert.equal(elements["stat-rcv-age"].textContent, "0s Fresh");

// Test 7: F3 Quota Windows Paging (6 Stress Windows) & Both Directions Wrap
elements["list-mode"].value = "long";
run('onListModeChange("long")');

// Page 0: windows 1-2
assert.equal(run("currentWindowPage"), 0);
assert.equal(elements["quota-page-badge"].textContent, "WIN 1-2 / 6");
assert.equal(elements["quota-primary-label"].textContent, "Primary Rolling Window (5 Hours)");
assert.equal(elements["quota-secondary-label"].textContent, "Weekly Account Limit (7 Days)");

// Next page -> Page 1: windows 3-4
run("nextWindowPage()");
assert.equal(run("currentWindowPage"), 1);
assert.equal(elements["quota-page-badge"].textContent, "WIN 3-4 / 6");
assert.equal(elements["quota-primary-label"].textContent, "Short Burst Window (60m)");
assert.equal(elements["quota-secondary-label"].textContent, "Daily Rate Ceiling (24h)");

// Next page -> Page 2: windows 5-6
run("nextWindowPage()");
assert.equal(run("currentWindowPage"), 2);
assert.equal(elements["quota-page-badge"].textContent, "WIN 5-6 / 6");
assert.equal(elements["quota-primary-label"].textContent, "Team Shared Pool (20h)");
assert.equal(elements["quota-secondary-label"].textContent, "Monthly Account Quota (30 Days)");

// Next page -> Wraps to Page 0
run("nextWindowPage()");
assert.equal(run("currentWindowPage"), 0);
assert.equal(elements["quota-page-badge"].textContent, "WIN 1-2 / 6");

// Prev page -> Wraps backwards to Page 2
run("prevWindowPage()");
assert.equal(run("currentWindowPage"), 2);
assert.equal(elements["quota-page-badge"].textContent, "WIN 5-6 / 6");

// Reset back to common list mode
elements["list-mode"].value = "common";
run('onListModeChange("common")');
assert.equal(elements["quota-page-badge"].textContent, "WIN 1-2 / 2");

// Test 8: BOOT Button 3-screen cycling
assert.equal(run("currentScreen"), 0);
assert.equal(navTabs[0].classList.contains("active"), true);
assert.equal(screenViews[0].classList.contains("active"), true);

run("cycleScreen()"); // Screen 1: Global Reset
assert.equal(run("currentScreen"), 1);
assert.equal(navTabs[1].classList.contains("active"), true);
assert.equal(screenViews[1].classList.contains("active"), true);

run("cycleScreen()"); // Screen 2: Hardware Status
assert.equal(run("currentScreen"), 2);
assert.equal(navTabs[2].classList.contains("active"), true);
assert.equal(screenViews[2].classList.contains("active"), true);

run("cycleScreen()"); // Wraps back to Screen 0: Usage
assert.equal(run("currentScreen"), 0);
assert.equal(navTabs[0].classList.contains("active"), true);
assert.equal(screenViews[0].classList.contains("active"), true);

console.log("PASS: Candidate B actual JavaScript/DOM execution verified successfully.");
console.log("All F1 cache retention, F2 totals, F3 paging/BOOT, and 299/300/301 boundaries confirmed.");
