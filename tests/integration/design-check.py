#!/usr/bin/env python3
"""Static contract scan for the six LCD previews; browser evidence is in gui-review.md."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import sys


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_LABELS = {
    "mockups/gemini-a/index.html": "A · Telemetry Matrix (Gemini)",
    "mockups/gemini-b/index.html": "B · Swiss Studio Meter (Gemini)",
    "mockups/gemini-c/index.html": "C · Industrial Field Gauge (Gemini)",
    "mockups/sol61-a/index.html": "D · Signal Board (Codex)",
    "mockups/sol61-b/index.html": "E · Session Ledger (Codex)",
    "mockups/sol61-c/index.html": "F · Window Atlas (Codex)",
}
GEMINI_STATES = {"normal", "source_stale", "disconnected", "unknown", "error", "waiting", "recovery"}
SOL_STATES = {"normal", "source-stale", "disconnected", "unknown", "error", "waiting", "recovery", "last-known"}


@dataclass(frozen=True)
class Candidate:
    label: str
    slug: str
    name: str
    lcd_id: str
    selector_id: str
    states: set[str]

    @property
    def path(self) -> str:
        return f"mockups/{self.slug}/index.html"


CANDIDATES = (
    Candidate("A", "gemini-a", "Telemetry Matrix", "lcd-screen", "state-selector", GEMINI_STATES),
    Candidate("B", "gemini-b", "Swiss Studio Meter", "lcd-screen", "state-selector", GEMINI_STATES),
    Candidate("C", "gemini-c", "Industrial Field Gauge", "lcd-screen", "state-selector", GEMINI_STATES),
    Candidate("D", "sol61-a", "Signal Board", "lcd", "scenario", SOL_STATES),
    Candidate("E", "sol61-b", "Session Ledger", "lcd", "scenario", SOL_STATES),
    Candidate("F", "sol61-c", "Window Atlas", "lcd", "scenario", SOL_STATES),
)


class SelectParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.select_id: str | None = None
        self.selects: dict[str, set[str]] = {}
        self.external_resources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "select":
            self.select_id = values.get("id")
            if self.select_id:
                self.selects[self.select_id] = set()
        elif tag == "option" and self.select_id:
            value = values.get("value")
            if value:
                self.selects[self.select_id].add(value)
        elif tag == "script" and values.get("src"):
            self.external_resources.append(values["src"] or "")
        elif tag in {"link", "img", "iframe", "source"}:
            for attr in ("href", "src", "poster"):
                if values.get(attr):
                    self.external_resources.append(values[attr] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "select":
            self.select_id = None


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    assert len(CANDIDATES) == 6 and len({c.path for c in CANDIDATES}) == 6
    sample_values = (
        ("124,800", "124800"),
        ("16,400", "16400"),
        ("89,600", "89600"),
        ("2,300", "2300"),
        ("141,200", "141200"),
    )
    findings: list[str] = []

    for candidate in CANDIDATES:
        path = ROOT / "opendesign" / candidate.path
        if not path.is_file():
            fail(f"missing candidate {path.relative_to(ROOT)}")
        html = path.read_text(encoding="utf-8-sig")
        parser = SelectParser()
        parser.feed(html)
        lcd_rule = re.search(rf"#{re.escape(candidate.lcd_id)}\s*\{{([^{{}}]*)\}}", html, re.S)
        if not lcd_rule or not re.search(r"width\s*:\s*820px", lcd_rule.group(1)) or not re.search(r"height\s*:\s*320px", lcd_rule.group(1)):
            fail(f"{candidate.label}: LCD CSS is not 820x320")
        if candidate.selector_id not in parser.selects or not candidate.states <= parser.selects[candidate.selector_id]:
            fail(f"{candidate.label}: missing state selector/options")
        if not re.search(r"<button\b[^>]*\bid=[\"'](?:boot|btn-boot-cycle)[\"']", html, re.I):
            fail(f"{candidate.label}: missing reachable BOOT preview button")
        if not all(any(value in html for value in variants) for variants in sample_values) or "codex-resets.com" not in html.casefold():
            fail(f"{candidate.label}: missing common sample value or global source")
        remote = [url for url in parser.external_resources if re.match(r"^(?:https?:)?//", url, re.I)]
        if remote:
            fail(f"{candidate.label}: external resource reference {remote[0]}")

        title = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
        if not title or candidate.name.casefold() not in title.group(1).casefold():
            findings.append(f"{candidate.label}: browser title does not name {candidate.name}")
        if not re.search(r"source\s+total", html, re.I):
            findings.append(f"{candidate.label}: source total is not separately labeled")
        if candidate.label in {"A", "B", "C"} and 'id="list-mode"' not in html:
            findings.append(f"{candidate.label}: preview exposes only its two fixed quota windows")

        print(f"PASS: {candidate.label} geometry, sample, state controls, BOOT control, offline resource scan")

    screenshot_dir = ROOT / "opendesign" / "screenshots"
    screenshots = sorted(screenshot_dir.glob("*.png"))
    if len(screenshots) != 6:
        fail(f"expected six PNG screenshots, found {len(screenshots)}")
    for screenshot in screenshots:
        data = screenshot.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", data[16:24]) != (820, 320):
            fail(f"screenshot is not 820x320 PNG: {screenshot.name}")

    manifest = json.loads((ROOT / "opendesign" / "manifest.json").read_text(encoding="utf-8-sig"))
    manifest_files = {
        file["path"]: file["label"]
        for section in manifest["sections"]
        for group in section["groups"]
        for file in group["files"]
    }
    if manifest_files != EXPECTED_LABELS:
        fail("manifest does not map exactly the six scanned candidates to A–F")
    comparison = (ROOT / "opendesign" / "comparison.html").read_text(encoding="utf-8-sig")
    if any(path not in comparison for path in EXPECTED_LABELS) or any(name not in comparison for name in ("141,200", "124,800", "16,400", "89,600", "2,300")):
        fail("comparison page is missing candidate links or common sample data")
    report = ROOT / "docs" / "agent-runs" / "orca-luna" / "gui-review.md"
    if not report.is_file() or "../docs/agent-runs/orca-luna/gui-review.md" not in comparison:
        fail("comparison page is missing its linked GUI review report")

    print("PASS: six 820x320 PNGs, full-scan manifest and comparison links/data")
    for finding in findings:
        print(f"FINDING: {finding}")


if __name__ == "__main__":
    main()
