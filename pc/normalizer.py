"""Normalization of Session Telemetry and Account Quota into UsageSnapshot schema objects."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from pc.quota import AccountQuotaResult
from pc.session import SessionTokenState

IDENTITY_SANITIZE_RE = re.compile(r"[^a-z0-9._-]+")
SNAPSHOT_SANITIZE_RE = re.compile(r"[^A-Za-z0-9._:-]+")


def sanitize_identity(value: str) -> str:
    cleaned = IDENTITY_SANITIZE_RE.sub("-", value.lower()).strip("-")
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"id-{cleaned}"
    return cleaned[:64]


def sanitize_snapshot_id(value: str) -> str:
    cleaned = SNAPSHOT_SANITIZE_RE.sub("-", value).strip("-")
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"snap-{cleaned}"
    return cleaned[:64]


def build_session_telemetry_snapshot(
    session: SessionTokenState,
    host_alias: str = "pc-collector",
    agent_id: str = "codex-cli",
    source_kind: str = "local_runtime",
    reference_time: str | None = None,
) -> dict[str, Any]:
    """Convert SessionTokenState into a valid session_telemetry UsageSnapshot."""
    observed = session.observed_at or reference_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snap_id = sanitize_snapshot_id(f"session-{session.session_id}")

    # Channels: input, output, cached_input, reasoning_output, source_total, normalized_total
    channels_def = [
        ("input", "Input tokens", session.input_tokens),
        ("output", "Output tokens", session.output_tokens),
        ("cached_input", "Cached input", session.cached_input_tokens),
        ("reasoning_output", "Reasoning output", session.reasoning_output_tokens),
        ("source_total", "Source total", session.source_total_tokens),
        ("normalized_total", "Normalized total", session.normalized_total_tokens),
    ]

    windows = []
    for wid, label, units in channels_def:
        windows.append(
            {
                "window_id": wid,
                "label": label,
                "used_units": float(units),
                "remaining_units": None,
                "limit_units": None,
                "unit": "token",
                "percent_used": None,
                "percent_remaining": None,
                "resets_at": None,
                "reset_status": "unknown",
            }
        )

    return {
        "schema_version": 1,
        "snapshot_id": snap_id,
        "provider_id": "codex",
        "agent_id": sanitize_identity(agent_id),
        "host_id": sanitize_identity(host_alias),
        "model_id": None,
        "account_profile_id": None,
        "source_kind": source_kind,
        "metric_kind": "session_telemetry",
        "unit": "token",
        "status": "available",
        "observed_at": observed,
        "windows": windows,
        "stale": False,
        "last_good_at": observed,
        "error_code": None,
        "error_reason": None,
    }


def build_account_quota_snapshot(
    quota: AccountQuotaResult,
    host_alias: str = "pc-collector",
    agent_id: str = "codex-cli",
    reference_time: str | None = None,
) -> dict[str, Any]:
    """Convert AccountQuotaResult into a valid quota_window UsageSnapshot."""
    observed = quota.observed_at or reference_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snap_id = sanitize_snapshot_id("quota-codex-account")
    account_profile = sanitize_identity(quota.account_id) if quota.account_id else None

    if quota.error_code:
        return {
            "schema_version": 1,
            "snapshot_id": snap_id,
            "provider_id": "codex",
            "agent_id": sanitize_identity(agent_id),
            "host_id": sanitize_identity(host_alias),
            "model_id": None,
            "account_profile_id": account_profile,
            "source_kind": quota.source_kind,
            "metric_kind": "quota_window",
            "unit": "percent",
            "status": "error",
            "observed_at": observed,
            "windows": [],
            "stale": False,
            "last_good_at": None,
            "error_code": quota.error_code,
            "error_reason": quota.error_reason,
        }

    windows = []
    for win_key, win in quota.windows.items():
        dur_sec = win.duration_seconds
        wire_id = f"{win_key}-{dur_sec}s" if dur_sec is not None else f"{win_key}-unknown"
        wire_id = sanitize_snapshot_id(wire_id)

        windows.append(
            {
                "window_id": wire_id,
                "label": win.duration_label,
                "used_units": None,
                "remaining_units": None,
                "limit_units": None,
                "unit": "percent",
                "percent_used": win.used_percent,
                "percent_remaining": win.percent_remaining,
                "resets_at": win.resets_at,
                "reset_status": win.reset_status or "unknown",
            }
        )

    return {
        "schema_version": 1,
        "snapshot_id": snap_id,
        "provider_id": "codex",
        "agent_id": sanitize_identity(agent_id),
        "host_id": sanitize_identity(host_alias),
        "model_id": None,
        "account_profile_id": account_profile,
        "source_kind": quota.source_kind,
        "metric_kind": "quota_window",
        "unit": "percent",
        "status": "available",
        "observed_at": observed,
        "windows": windows,
        "stale": False,
        "last_good_at": observed,
        "error_code": None,
        "error_reason": None,
    }


def normalize_global_reset(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize global reset dictionary to cdm-frame globalReset schema."""
    source = raw.get("source") or raw.get("provider") or "codex-resets.com"
    captured_at = raw.get("captured_at") or raw.get("fetched_at")
    latest_reset_at = raw.get("latest_reset_at") or raw.get("last_reset_at")

    return {
        "schema_version": 1,
        "source": str(source),
        "captured_at": captured_at,
        "latest_reset_at": latest_reset_at,
        "forecast_24h_percent": raw.get("forecast_24h_percent"),
        "forecast_48h_percent": raw.get("forecast_48h_percent"),
        "forecast_is_schedule": False,
        "stale": bool(raw.get("stale", False)),
        "error_code": raw.get("error_code"),
    }
