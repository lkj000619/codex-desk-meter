// Run from any directory: node docs/design/lcd/sol61/check.mjs
// Executes the real inline scripts with a minimal control DOM; no visual claim.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const states = ["normal", "source-stale", "disconnected", "unknown", "error", "waiting", "recovery", "last-known"];
const luminance = hex => {
  const channels = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16) / 255);
  return channels.map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4).reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
};
for (const candidate of ["a", "b", "c"]) {
  const file = new URL(`../../../../opendesign/mockups/sol61-${candidate}/index.html`, import.meta.url);
  const html = readFileSync(file, "utf8");
  assert.match(html, /width: 820px; height: 320px;/);
  assert.match(html, /SYNTHETIC DATA ONLY/);
  assert.doesNotMatch(html, /<script[^>]+src=|<link|@import|url\(|fetch\(|XMLHttpRequest|WebSocket|React|Babel/);
  const palette = Object.fromEntries([...html.matchAll(/--(bg|fg|muted|accent|rule|warn|error): (#[0-9a-f]{6})/g)].map(match => [match[1], match[2]]));
  for (const [name, hex] of Object.entries(palette)) {
    const channels = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16));
    channels.forEach((value, index) => { const levels = index === 1 ? 63 : 31; assert.equal(Math.round(Math.round(value * levels / 255) * 255 / levels), value); });
    if (["fg", "muted", "accent", "warn", "error"].includes(name)) {
      const light = [luminance(hex), luminance(palette.bg)].sort((a, b) => a - b);
      assert.ok((light[1] + .05) / (light[0] + .05) >= 4.5, `${candidate} ${name} text contrast`);
    }
  }
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 1);
  const elements = Object.fromEntries(["lcd", "scenario", "list-mode", "boot", "previous", "next", "result"].map(id => [id, {
    value: id === "scenario" ? "normal" : "common", dataset: {}, innerHTML: "", textContent: "", listeners: {},
    addEventListener(type, callback) { this.listeners[type] = callback; }
  }]));
  const document = { body: { dataset: { candidate } }, listeners: {}, getElementById: id => elements[id], addEventListener(type, callback) { this.listeners[type] = callback; } };
  const context = vm.createContext({ document });
  const run = expression => vm.runInContext(expression, context);
  run(scripts[0][1]);
  const change = (id, value) => { elements[id].value = value; elements[id].listeners.change(); };
  const click = id => elements[id].listeners.click();
  assert.equal(elements.lcd.dataset.screen, "USAGE");
  assert.match(elements.lcd.innerHTML, /141,200/);
  assert.match(elements.lcd.innerHTML, /124,800/);
  assert.match(elements.lcd.innerHTML, /16,400/);
  assert.match(elements.lcd.innerHTML, /89,600/);
  assert.match(elements.lcd.innerHTML, /2,300/);
  assert.match(elements.lcd.innerHTML, /Limit \/ remaining \/ % unknown/);
  assert.match(elements.lcd.innerHTML, /58<span class="unit">%/);
  if (candidate !== "c") assert.match(elements.lcd.innerHTML, /82<span class="unit">%/);
  for (const title of ["GLOBAL RESET", "STATUS", "USAGE"]) { click("boot"); assert.equal(elements.lcd.dataset.screen, title); }
  click("boot");
  assert.match(elements.lcd.innerHTML, /7h 10m/);
  assert.match(elements.lcd.innerHTML, /codex-resets.com/);
  assert.match(elements.lcd.innerHTML, /07 OCT 19:00/);
  assert.match(elements.lcd.innerHTML, /Captured 08 OCT 02:10 KST/);
  assert.equal(elements.next.disabled, true);
  click("boot"); click("boot");
  change("list-mode", "long");
  const pages = candidate === "c" ? 6 : 3;
  for (let page = 0; page < pages; page++) {
    assert.equal(run("windowPage"), page);
    assert.match(elements.lcd.innerHTML, new RegExp(`Codex account / stress-${page * run("PAGE_SIZE") + 1}`));
    click("next");
  }
  assert.equal(run("windowPage"), 0);
  click("previous"); assert.equal(run("windowPage"), pages - 1);
  change("list-mode", "common");
  for (const state of states) {
    change("scenario", state);
    assert.equal(elements.lcd.dataset.state, state);
    for (let count = 0; count < 3; count++) {
      assert.doesNotMatch(elements.lcd.innerHTML, /NaN|undefined|<button|<select/);
      if (state === "waiting" || state === "unknown") assert.doesNotMatch(elements.lcd.innerHTML, /141,200|124,800|89,600|7h 10m|58<span/);
      click("boot");
    }
  }
  assert.equal(run('getView("source-stale", "common").sourceAge'), 301);
  assert.equal(run('getView("source-stale", "common").receiveAge'), 0);
  assert.equal(run('getView("disconnected", "common").sourceAge'), 301);
  assert.equal(run('getView("disconnected", "common").receiveAge'), 301);
  assert.equal(run('getView("disconnected", "common").session.input'), 124800);
  assert.equal(run('getView("error", "common").lastGood'), "2026-10-07T17:10:00Z");
  assert.equal(run('getView("error", "common").received'), "2026-10-07T17:10:00Z");
  assert.equal(run('getView("error", "common").windows[0].used'), 42);
  assert.equal(run('getView("recovery", "common").observed'), "2026-10-07T17:10:00Z");
  assert.equal(run('getView("waiting", "common").sourceAge'), null);
  assert.equal(run('getView("waiting", "common").receiveAge'), null);
  assert.equal(run('age("2026-10-07T17:14:59Z", SAMPLE.observed)'), 299);
  assert.equal(run('age("2026-10-07T17:15:00Z", SAMPLE.observed)'), 300);
  assert.doesNotMatch(run('statusMarkup({...getView("normal", "common"), sourceAge: 299})'), />STALE</);
  assert.match(run('statusMarkup({...getView("normal", "common"), sourceAge: 300})'), />STALE</);
  assert.match(run('statusMarkup(getView("error", "common"))'), /Quota HTTP 500/);
  assert.match(run('globalMarkup(getView("last-known", "common"))'), /LAST-KNOWN|LAST KNOWN/);
  assert.match(run('globalMarkup(getView("last-known", "common"))'), /7h 10m/);
  assert.match(run('globalMarkup(getView("unknown", "common"))'), /No reset record/);
  assert.doesNotMatch(run('globalMarkup(getView("normal", "common"))'), /03:20|13 OCT/);
  const before = run("screen");
  document.listeners.keydown({ key: "ArrowRight", target: { tagName: "SELECT" } });
  assert.equal(run("screen"), before);
  let prevented = false;
  document.listeners.keydown({ key: "ArrowRight", target: { tagName: "BODY" }, preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(run("screen"), (before + 1) % 3);
  console.log(`sol61-${candidate}: PASS / sample, 8 states, 3 screens, paging, ages, null, last-good, offline controls, RGB565 contrast`);
}
console.log("Browser layout, independent visual QA, fonts on LCD, BOOT hardware and firmware: not_run.");
