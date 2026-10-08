#!/usr/bin/env python3
"""
Regression test suite for Gemini Candidate B (Swiss Studio Meter).
Executes actual Candidate B inline JavaScript in Node vm and asserts rendered prior values,
original timestamps, deterministic F1 state machine transitions, F2 totals, F3 paging, and F5 qualifications.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
MOCKUP_B = ROOT / "opendesign" / "mockups" / "gemini-b" / "index.html"
HANDOFF = ROOT / "docs" / "design" / "lcd" / "gemini" / "handoff.md"
NODE_CHECK = ROOT / "docs" / "design" / "lcd" / "gemini" / "check.mjs"


def test_mockup_b_content() -> None:
    assert MOCKUP_B.is_file(), f"Mockup B not found: {MOCKUP_B}"
    content = MOCKUP_B.read_text(encoding="utf-8")

    # 1. Geometry & Zero-CDN Offline verification
    assert 'width: 820px;' in content and 'height: 320px;' in content, "LCD geometry is not 820x320"
    remote_refs = re.findall(r'(?:href|src)=["\'](https?://[^"\']+)["\']', content)
    assert len(remote_refs) == 0, f"Found external web/CDN dependencies: {remote_refs}"

    # Trailing whitespace check
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        assert not re.search(r"[ \t]+$", line), f"Line {idx} has trailing whitespace"

    # 2. Reviewer F2: Distinct totals & subset semantics
    assert "TOTAL TOKENS (IN+OUT)" in content, "Missing normalized total label"
    assert "Source Total Reported" in content, "Missing source total label"
    assert "sess-src-total" in content, "Missing sess-src-total element"
    assert "* Included subsets: cached in input, reasoning in output" in content, "Missing subset qualification"
    assert "Session limits, remaining tokens, and % are unknown" in content, "Session limit must remain unknown"

    # 3. Reviewer F3: Window Paging & Stress List
    assert 'id="list-mode"' in content, "Missing list-mode selector"
    assert 'btn-prev-page' in content and 'btn-next-page' in content, "Missing held-BOOT window paging controls"
    assert "quota-page-badge" in content, "Missing page badge indicator"
    assert "stress-hourly-3600s" in content, "Missing stress dataset windows"
    assert "stress-monthly-43200m" in content, "Missing monthly window in stress test"

    # 4. Reviewer F1: Deterministic Cache Semantics in JS Logic
    assert "lastGoodCache.hasCache = true;" in content, "Missing cache establishment on normal state"
    assert "lastGoodCache.hasCache" in content, "Missing lastGoodCache conditional check"
    assert "cold_error" in content, "Missing explicit cold_error state option"
    assert "cold_disconnected" in content, "Missing explicit cold_disconnected state option"
    assert "source_stale_299" in content, "Missing boundary state 299s"
    assert "source_stale_300" in content, "Missing boundary state 300s"
    assert "source_stale_301" in content, "Missing boundary state 301s"

    print("PASS: Mockup B HTML contract and syntax scan passed successfully.")


def test_handoff_f5_limits() -> None:
    assert HANDOFF.is_file(), f"Handoff not found: {HANDOFF}"
    handoff_text = HANDOFF.read_text(encoding="utf-8")

    # Ensure unmeasured estimate qualification exists (F5)
    assert "not_run" in handoff_text, "Handoff must qualify physical measurements as not_run"
    assert "60fps 갱신 언급은 설계상의 이론적 목표치(estimate)" in handoff_text, "Missing F5 estimate disclaimer"
    assert "결함 F1 보완" in handoff_text, "Missing F1 correction documentation"
    assert "결함 F2 보완" in handoff_text, "Missing F2 correction documentation"
    assert "결함 F3 보완" in handoff_text, "Missing F3 correction documentation"

    # Ensure handoff ends with a single newline (no duplicate EOF newlines)
    assert handoff_text.endswith("예정입니다.\n") and not handoff_text.endswith("예정입니다.\n\n"), "Handoff has duplicate EOF newline"

    print("PASS: Handoff documentation regression checks passed successfully.")


def test_actual_javascript_dom_execution() -> None:
    """Execute the actual inline JavaScript and DOM state machine using Node.js vm harness."""
    assert NODE_CHECK.is_file(), f"Node check harness not found: {NODE_CHECK}"
    result = subprocess.run(["node", str(NODE_CHECK)], capture_output=True, text=True, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        raise RuntimeError(f"Actual JavaScript execution check failed with exit code {result.returncode}")
    print(result.stdout.strip())
    print("PASS: Actual Candidate B JavaScript & DOM state transitions verified via Node VM harness.")


if __name__ == "__main__":
    test_mockup_b_content()
    test_handoff_f5_limits()
    test_actual_javascript_dom_execution()
    print("ALL GEMINI B REGRESSION CHECKS PASSED.")
