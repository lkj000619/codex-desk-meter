"""Reproduce selected-session replacement through the production C receiver/GUI.

Run after the Sol-owned tests/firmware/build-host.ps1 creates cdm-host.exe.
All frames below are synthetic and pass through cdm_accept and gui_render in C.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "tests" / "firmware" / ".build" / "cdm-host.exe"
STAMP = "2026-10-07T17:10:00Z"
CHANNELS = ("input", "output", "cached_input", "reasoning_output", "source_total", "normalized_total")


def session(snapshot_id: str, input_tokens: int, output_tokens: int) -> dict:
    values = {
        "input": input_tokens,
        "output": output_tokens,
        "cached_input": 0,
        "reasoning_output": 0,
        "source_total": input_tokens + output_tokens,
        "normalized_total": input_tokens + output_tokens,
    }
    windows = [
        {
            "window_id": channel,
            "label": channel,
            "used_units": values[channel],
            "remaining_units": None,
            "limit_units": None,
            "unit": "token",
            "percent_used": None,
            "percent_remaining": None,
            "resets_at": None,
            "reset_status": "unknown",
        }
        for channel in CHANNELS
    ]
    return {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "provider_id": "codex",
        "agent_id": "codex-cli",
        "host_id": "synthetic-host",
        "model_id": None,
        "account_profile_id": None,
        "source_kind": "fixture",
        "metric_kind": "session_telemetry",
        "unit": "token",
        "status": "available",
        "observed_at": STAMP,
        "windows": windows,
        "stale": False,
        "last_good_at": STAMP,
        "error_code": None,
        "error_reason": None,
    }


def frame(sequence: int, records: list[dict]) -> bytes:
    unsigned = {
        "protocol": "cdm/1",
        "sequence": sequence,
        "sent_at": STAMP,
        "payload": {"usage": records, "global_resets": []},
    }
    canonical = lambda value: json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    envelope = {
        **unsigned,
        "integrity": {"algorithm": "crc32", "value": f"{zlib.crc32(canonical(unsigned)):08X}"},
    }
    return canonical(envelope) + b"\n"


def render_frames(frames: list[bytes]) -> list[dict]:
    events = [
        {"line_hex": raw.hex(), "mono_ms": 1000 * (i + 1), "now_ms": 1000 * (i + 1), "render": True}
        for i, raw in enumerate(frames)
    ]
    result = subprocess.run(
        [str(HOST), "--wire"], input=json.dumps({"events": events}), text=True,
        capture_output=True, cwd=ROOT,
    )
    if result.returncode:
        raise AssertionError(f"production C host harness failed: {result.stderr or result.stdout}")
    return json.loads(result.stdout)


class SelectedSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not HOST.is_file():
            raise RuntimeError("Run the Sol-owned tests/firmware/build-host.ps1 first")

    def test_switch_replaces_active_session_and_default_pixels(self) -> None:
        first = session("selected-session-A", 10, 1)
        selected = session("selected-session-B", 20, 2)
        only_a = render_frames([frame(1, [first])])[0]
        only_b = render_frames([frame(1, [selected])])[0]
        switched = render_frames([frame(1, [first]), frame(2, [selected])])
        final = switched[-1]
        active_sessions = [
            row["key"] for row in final["usage"]
            if row["current"]["metric_kind"] == "session_telemetry"
        ]
        pixels_after_switch = final["render"]["usage_pages"][0]
        failures = []
        if active_sessions != ["selected-session-B"]:
            failures.append(f"active sessions retained after reselection: {active_sessions}")
        if pixels_after_switch != only_b["render"]["usage_pages"][0]:
            failures.append(
                "default framebuffer after selecting B does not equal B-only framebuffer "
                f"(A-only={only_a['render']['usage_pages'][0]}, "
                f"B-only={only_b['render']['usage_pages'][0]}, "
                f"A→B pages={final['render']['usage_pages']})"
            )
        self.assertEqual(failures, [], "; ".join(failures))


if __name__ == "__main__":
    unittest.main()
