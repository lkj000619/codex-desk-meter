"""Native Codex app-server account rate limits collector.

Uses read-only `account/rateLimits/read` via initialized JSON-RPC stdio subprocess.
Protocol flow:
1. initialize request -> wait for result
2. initialized notification -> sent to server
3. account/rateLimits/read request -> wait for result

Key features:
- Bounded reader using threads and queue with real timeout to prevent hangs.
- Drains/limits stderr in background.
- Process cleanup (terminate then kill/wait) and stream closing on all paths.
- observed_at reflects the exact timestamp of successful reply acquisition.
- Parses both rateLimits AND rateLimitsByLimitId without dropping distinct windows.
- Injected reference time for reset status.
"""

from __future__ import annotations

import json
import queue
import subprocess
import threading
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
        val = float(used_pct)
        if 0.0 <= val <= 100.0:
            used_percent = val
            percent_rem = round(100.0 - val, 2)
        else:
            return None

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

    if isinstance(rate_limits, dict):
        for win_name in ("primary", "secondary"):
            win_data = rate_limits.get(win_name)
            if isinstance(win_data, dict):
                parsed = _parse_single_window(win_data, ref_dt)
                if parsed:
                    windows[win_name] = parsed

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


class BoundedProcessReader:
    """Threaded bounded line reader for subprocess stdout and stderr."""

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc
        self.stdout_queue: queue.Queue[bytes | None] = queue.Queue()
        self.stderr_lines: list[str] = []
        self._stop = False

        self.t_out = threading.Thread(target=self._read_stdout, daemon=True)
        self.t_err = threading.Thread(target=self._read_stderr, daemon=True)
        self.t_out.start()
        self.t_err.start()

    def _read_stdout(self) -> None:
        try:
            if not self.proc.stdout:
                return
            while not self._stop:
                line = self.proc.stdout.readline()
                if not line:
                    break
                self.stdout_queue.put(line)
        except Exception:
            pass
        finally:
            self.stdout_queue.put(None)

    def _read_stderr(self) -> None:
        try:
            if not self.proc.stderr:
                return
            while not self._stop:
                line = self.proc.stderr.readline()
                if not line:
                    break
                if len(self.stderr_lines) < 50:
                    self.stderr_lines.append(line.decode("utf-8", errors="replace").strip())
        except Exception:
            pass

    def read_line(self, timeout: float) -> bytes | None:
        try:
            return self.stdout_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        self._stop = True


def cleanup_process(proc: subprocess.Popen | None, reader: BoundedProcessReader | None = None) -> None:
    if reader:
        reader.close()
    if proc:
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=0.5)
        except Exception:
            try:
                proc.kill()
                proc.wait(timeout=0.5)
            except Exception:
                pass
        try:
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()
        except Exception:
            pass


def execute_jsonrpc_call_bounded(
    proc: subprocess.Popen,
    reader: BoundedProcessReader,
    method: str,
    params: dict[str, Any],
    req_id: int | None = None,
    is_notification: bool = False,
    timeout_seconds: float = 3.0,
) -> dict[str, Any] | None:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params}
    if not is_notification:
        msg["id"] = req_id

    line = json.dumps(msg) + "\n"
    if proc.stdin:
        try:
            proc.stdin.write(line.encode("utf-8"))
            proc.stdin.flush()
        except Exception:
            return None

    if is_notification:
        return None

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        raw_line = reader.read_line(timeout=remaining)
        if raw_line is None:
            # Check if process died
            if proc.poll() is not None:
                break
            continue

        try:
            resp = json.loads(raw_line.decode("utf-8"))
            if isinstance(resp, dict) and resp.get("id") == req_id:
                return resp
        except Exception:
            continue

    return None


def fetch_native_rate_limits(
    timeout_seconds: float = 5.0,
    reference_time: str | None = None,
    command: list[str] | None = None,
) -> AccountQuotaResult:
    """Safe runner for codex app-server with bounded async streams and proper handshake."""
    cmd = command or ["codex", "app-server"]
    proc = None
    reader = None

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        reader = BoundedProcessReader(proc)

        # 1. initialize request
        init_resp = execute_jsonrpc_call_bounded(
            proc,
            reader,
            method="initialize",
            params={"clientInfo": {"name": "codex-desk-meter", "version": "1.0.0"}},
            req_id=1,
            timeout_seconds=min(2.0, timeout_seconds / 2),
        )
        if not init_resp or "result" not in init_resp:
            now_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=now_ts,
                error_code="INITIALIZE_FAILED",
                error_reason="Failed to receive valid initialize response from app-server within timeout",
            )

        # 2. initialized notification
        execute_jsonrpc_call_bounded(
            proc,
            reader,
            method="initialized",
            params={},
            is_notification=True,
        )

        # 3. account/rateLimits/read request
        limits_resp = execute_jsonrpc_call_bounded(
            proc,
            reader,
            method="account/rateLimits/read",
            params={},
            req_id=2,
            timeout_seconds=min(3.0, timeout_seconds / 2),
        )

        acquired_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        if not limits_resp:
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=acquired_at,
                error_code="RATE_LIMIT_TIMEOUT",
                error_reason="Timed out waiting for account/rateLimits/read response",
            )

        if "error" in limits_resp:
            err = limits_resp["error"]
            return AccountQuotaResult(
                account_id=None,
                plan_type=None,
                windows={},
                observed_at=acquired_at,
                error_code="RATE_LIMIT_RPC_ERROR",
                error_reason=str(err.get("message") or err),
            )

        return parse_app_server_rate_limits(limits_resp, acquired_at, reference_time=reference_time)

    except FileNotFoundError:
        now_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return AccountQuotaResult(
            account_id=None,
            plan_type=None,
            windows={},
            observed_at=now_ts,
            error_code="CODEX_CLI_NOT_FOUND",
            error_reason=f"Binary {cmd[0]!r} not found on PATH",
        )
    except Exception as exc:
        now_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return AccountQuotaResult(
            account_id=None,
            plan_type=None,
            windows={},
            observed_at=now_ts,
            error_code="APP_SERVER_FAILURE",
            error_reason=str(exc),
        )
    finally:
        cleanup_process(proc, reader)
