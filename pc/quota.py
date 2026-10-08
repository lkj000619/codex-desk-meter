"""Native Codex app-server account rate limits collector.

Uses read-only `account/rateLimits/read` via initialized JSON-RPC stdio subprocess.
Does not read auth files, cookies, or secrets.
Does not create threads, execute turns, or spend reset credits.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class RateLimitWindow:
    duration_seconds: int | None
    duration_label: str
    used_percent: float | None
    percent_remaining: float | None
    resets_at: str | None
    reset_status: str | None


@dataclass
class AccountQuotaResult:
    account_id: str | None
    plan_type: str | None
    windows: dict[str, RateLimitWindow]
    observed_at: str
    source_kind: str = "local_runtime"
    error_code: str | None = None
    error_reason: str | None = None


def format_duration_label(seconds: int | None) -> str:
    if seconds is None:
        return "Unknown window"
    if seconds % 3600 == 0:
        hours = seconds // 3600
        return f"{hours}h limit"
    if seconds % 60 == 0:
        mins = seconds // 60
        return f"{mins}m limit"
    return f"{seconds}s limit"


def parse_app_server_rate_limits(response_payload: dict[str, Any], observed_at: str) -> AccountQuotaResult:
    """Parse JSON-RPC account/rateLimits/read response into typed structure."""
    result = response_payload.get("result") or {}
    rate_limits = result.get("rateLimits") or {}
    account_id = result.get("accountId")
    plan_type = rate_limits.get("planType")

    windows: dict[str, RateLimitWindow] = {}

    for win_name in ("primary", "secondary"):
        win_data = rate_limits.get(win_name)
        if not isinstance(win_data, dict):
            continue

        mins = win_data.get("windowDurationMins")
        duration_seconds = int(mins * 60) if isinstance(mins, (int, float)) else None

        used_pct = win_data.get("usedPercent")
        used_percent = float(used_pct) if isinstance(used_pct, (int, float)) else None

        percent_rem = (100.0 - used_percent) if used_percent is not None else None
        if percent_rem is not None:
            percent_rem = max(0.0, min(100.0, round(percent_rem, 2)))

        resets_at_raw = win_data.get("resetsAt")
        resets_at = None
        reset_status = None
        if isinstance(resets_at_raw, (int, float)):
            dt = datetime.fromtimestamp(resets_at_raw, tz=timezone.utc)
            resets_at = dt.isoformat().replace("+00:00", "Z")
            # If resets_at is in future, scheduled; else expired
            now = datetime.now(timezone.utc)
            reset_status = "scheduled" if dt >= now else "expired"

        label = format_duration_label(duration_seconds)

        windows[win_name] = RateLimitWindow(
            duration_seconds=duration_seconds,
            duration_label=label,
            used_percent=used_percent,
            percent_remaining=percent_rem,
            resets_at=resets_at,
            reset_status=reset_status,
        )

    return AccountQuotaResult(
        account_id=account_id,
        plan_type=plan_type,
        windows=windows,
        observed_at=observed_at,
    )


def fetch_native_rate_limits(timeout_seconds: float = 10.0) -> AccountQuotaResult:
    """Spawn codex app-server, send initialize and account/rateLimits/read, return parsed result."""
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    proc = None
    try:
        proc = subprocess.Popen(
            ["codex", "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "codex-desk-meter", "version": "1.0.0"}},
        }
        proc.stdin.write(json.dumps(init_req).encode("utf-8") + b"\n")
        proc.stdin.flush()

        limits_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "account/rateLimits/read",
            "params": {},
        }
        proc.stdin.write(json.dumps(limits_req).encode("utf-8") + b"\n")
        proc.stdin.flush()

        start_time = time.monotonic()
        response_msg = None

        while time.monotonic() - start_time < timeout_seconds:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line.decode("utf-8"))
            except Exception:
                continue

            if msg.get("id") == 2:
                response_msg = msg
                break

        if not response_msg:
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=observed_at,
                error_code="APP_SERVER_TIMEOUT",
                error_reason=f"Timed out waiting for response from codex app-server after {timeout_seconds}s",
            )

        if "error" in response_msg:
            err = response_msg["error"]
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=observed_at,
                error_code="RATE_LIMIT_RPC_ERROR",
                error_reason=str(err.get("message") or err),
            )

        return parse_app_server_rate_limits(response_msg, observed_at)

    except FileNotFoundError:
        return AccountQuotaResult(
            account_id=None,
            plan_type=None,
            windows={},
            observed_at=observed_at,
            error_code="CODEX_CLI_NOT_FOUND",
            error_reason="codex binary is not found on PATH",
        )
    except Exception as exc:
        return AccountQuotaResult(
            account_id=None,
            plan_type=None,
            windows={},
            observed_at=observed_at,
            error_code="APP_SERVER_FAILURE",
            error_reason=str(exc),
        )
    finally:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=1.0)
            except Exception:
                pass
