"""Native Codex app-server account rate limits collector.

Uses read-only `account/rateLimits/read` via initialized JSON-RPC stdio subprocess.
Protocol flow:
1. initialize request -> wait for result
2. initialized notification -> sent to server
3. account/rateLimits/read request -> wait for result
- Bounded stdout reading with timeout.
- Process cleanup (terminate/kill/wait) on all failure paths.
- Does not contact real accounts in tests (pure fake streams).
- Parses both rateLimits AND rateLimitsByLimitId without dropping distinct windows.
- Injected reference time for reset status.
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


def _parse_single_window(
    win_data: dict[str, Any],
    reference_dt: datetime,
) -> RateLimitWindow | None:
    """Validate and parse a single window dictionary without clamping bad values."""
    if not isinstance(win_data, dict):
        return None

    mins = win_data.get("windowDurationMins")
    duration_seconds = None
    if isinstance(mins, (int, float)) and not isinstance(mins, bool):
        duration_seconds = int(mins * 60)

    used_pct = win_data.get("usedPercent")
    used_percent = None
    percent_rem = None

    if isinstance(used_pct, (int, float)) and not isinstance(used_pct, bool):
        # Validate range [0, 100] strictly, do not clamp invalid percent
        val = float(used_pct)
        if 0.0 <= val <= 100.0:
            used_percent = val
            percent_rem = round(100.0 - val, 2)
        else:
            return None  # Out of range percent is malformed

    resets_at_raw = win_data.get("resetsAt")
    resets_at = None
    reset_status = "unknown"
    if isinstance(resets_at_raw, (int, float)) and not isinstance(resets_at_raw, bool):
        try:
            dt = datetime.fromtimestamp(resets_at_raw, tz=timezone.utc)
            resets_at = dt.isoformat().replace("+00:00", "Z")
            reset_status = "scheduled" if dt >= reference_dt else "expired"
        except Exception:
            pass

    label = format_duration_label(duration_seconds)
    return RateLimitWindow(
        duration_seconds=duration_seconds,
        duration_label=label,
        used_percent=used_percent,
        percent_remaining=percent_rem,
        resets_at=resets_at,
        reset_status=reset_status,
    )


def parse_app_server_rate_limits(
    response_payload: dict[str, Any],
    observed_at: str,
    reference_time: str | None = None,
) -> AccountQuotaResult:
    """Parse JSON-RPC account/rateLimits/read response into typed structure."""
    if not isinstance(response_payload, dict):
        return AccountQuotaResult(
            account_id=None,
            plan_type=None,
            windows={},
            observed_at=observed_at,
            error_code="INVALID_RPC_RESPONSE",
            error_reason="RPC response is not a dictionary",
        )

    result = response_payload.get("result")
    if not isinstance(result, dict):
        return AccountQuotaResult(
            account_id=None,
            plan_type=None,
            windows={},
            observed_at=observed_at,
            error_code="INVALID_RPC_RESULT",
            error_reason="RPC result field is missing or not a dictionary",
        )

    ref_dt = datetime.now(timezone.utc)
    if reference_time:
        try:
            ref_dt = datetime.fromisoformat(reference_time.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            pass

    account_id = result.get("accountId")
    rate_limits = result.get("rateLimits") or {}
    plan_type = rate_limits.get("planType") if isinstance(rate_limits, dict) else None

    windows: dict[str, RateLimitWindow] = {}

    # 1. Parse top-level rateLimits primary/secondary
    if isinstance(rate_limits, dict):
        for win_name in ("primary", "secondary"):
            win_data = rate_limits.get(win_name)
            if isinstance(win_data, dict):
                parsed = _parse_single_window(win_data, ref_dt)
                if parsed:
                    windows[win_name] = parsed

    # 2. Parse rateLimitsByLimitId without dropping distinct windows
    rate_limits_by_id = result.get("rateLimitsByLimitId")
    if isinstance(rate_limits_by_id, dict):
        for limit_id, limit_obj in rate_limits_by_id.items():
            if isinstance(limit_obj, dict):
                for win_name in ("primary", "secondary"):
                    win_data = limit_obj.get(win_name)
                    if isinstance(win_data, dict):
                        parsed = _parse_single_window(win_data, ref_dt)
                        if parsed:
                            combined_key = f"{limit_id}_{win_name}" if limit_id != "codex" else win_name
                            if combined_key not in windows:
                                windows[combined_key] = parsed

    if not windows and not result.get("rateLimits"):
        return AccountQuotaResult(
            account_id=account_id if isinstance(account_id, str) else None,
            plan_type=plan_type if isinstance(plan_type, str) else None,
            windows={},
            observed_at=observed_at,
            error_code="UNSUPPORTED_RATE_LIMIT_SHAPE",
            error_reason="No valid rate limit windows found in response",
        )

    return AccountQuotaResult(
        account_id=str(account_id) if account_id else None,
        plan_type=str(plan_type) if plan_type else None,
        windows=windows,
        observed_at=observed_at,
    )


def execute_jsonrpc_call(
    proc: subprocess.Popen,
    method: str,
    params: dict[str, Any],
    req_id: int | None = None,
    is_notification: bool = False,
    timeout_seconds: float = 5.0,
) -> dict[str, Any] | None:
    """Send JSON-RPC message and wait for response matching req_id if not notification."""
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params}
    if not is_notification:
        msg["id"] = req_id

    line = json.dumps(msg) + "\n"
    if proc.stdin:
        proc.stdin.write(line.encode("utf-8"))
        proc.stdin.flush()

    if is_notification:
        return None

    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout_seconds:
        if not proc.stdout:
            break
        raw_line = proc.stdout.readline()
        if not raw_line:
            break
        try:
            resp = json.loads(raw_line.decode("utf-8"))
            if isinstance(resp, dict) and resp.get("id") == req_id:
                return resp
        except Exception:
            continue

    return None


def fetch_native_rate_limits(timeout_seconds: float = 10.0, reference_time: str | None = None) -> AccountQuotaResult:
    """Safe runner for codex app-server using proper protocol handshake."""
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    proc = None
    try:
        proc = subprocess.Popen(
            ["codex", "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 1. initialize request
        init_resp = execute_jsonrpc_call(
            proc,
            method="initialize",
            params={"clientInfo": {"name": "codex-desk-meter", "version": "1.0.0"}},
            req_id=1,
            timeout_seconds=min(5.0, timeout_seconds),
        )
        if not init_resp or "result" not in init_resp:
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=observed_at,
                error_code="INITIALIZE_FAILED",
                error_reason="Failed to receive valid initialize response from app-server",
            )

        # 2. initialized notification
        execute_jsonrpc_call(
            proc,
            method="initialized",
            params={},
            is_notification=True,
        )

        # 3. account/rateLimits/read request
        limits_resp = execute_jsonrpc_call(
            proc,
            method="account/rateLimits/read",
            params={},
            req_id=2,
            timeout_seconds=min(5.0, timeout_seconds),
        )

        if not limits_resp:
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=observed_at,
                error_code="RATE_LIMIT_TIMEOUT",
                error_reason=f"Timed out waiting for account/rateLimits/read",
            )

        if "error" in limits_resp:
            err = limits_resp["error"]
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=observed_at,
                error_code="RATE_LIMIT_RPC_ERROR",
                error_reason=str(err.get("message") or err),
            )

        return parse_app_server_rate_limits(limits_resp, observed_at, reference_time=reference_time)

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
                try:
                    proc.kill()
                    proc.wait(timeout=1.0)
                except Exception:
                    pass
