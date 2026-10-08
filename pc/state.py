"""Shared collection state and cache with source isolation, last-good retention, and stale checking."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pc.frame import STALE_THRESHOLD_SECONDS, parse_rfc3339, semantic_validate_snapshot
from pc.normalizer import (
    build_account_quota_snapshot,
    build_session_telemetry_snapshot,
    normalize_global_reset,
)
from pc.quota import fetch_native_rate_limits
from pc.session import (
    SessionError,
    SessionTokenState,
    parse_session_file,
    scan_sessions_directory,
    select_latest_session,
)


class CollectionSourceState:
    """Retains last-good snapshot, observed timestamp, and errors for a single source."""

    def __init__(self, source_id: str):
        self.source_id = source_id
        self.last_good_snapshot: dict[str, Any] | None = None
        self.last_good_at: str | None = None
        self.last_error_code: str | None = None
        self.last_error_reason: str | None = None

    def update_good(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        self.last_good_snapshot = copy.deepcopy(snapshot)
        self.last_good_at = snapshot.get("observed_at")
        self.last_error_code = None
        self.last_error_reason = None
        return snapshot

    def update_error(
        self,
        error_code: str,
        error_reason: str,
        reference_time: str | None = None,
    ) -> dict[str, Any]:
        self.last_error_code = error_code
        self.last_error_reason = error_reason

        # If we have a last-good snapshot, retain its values and mark error status
        if self.last_good_snapshot:
            err_snap = copy.deepcopy(self.last_good_snapshot)
            err_snap["status"] = "error"
            err_snap["error_code"] = error_code
            err_snap["error_reason"] = error_reason
            return err_snap

        # If no prior good snapshot, create minimal error snapshot
        ref_dt = parse_rfc3339(reference_time) if reference_time else datetime.now(timezone.utc)
        now_ts = ref_dt.isoformat().replace("+00:00", "Z")
        return {
            "schema_version": 1,
            "snapshot_id": f"error-{self.source_id}",
            "provider_id": "codex",
            "agent_id": "codex-cli",
            "host_id": "pc-collector",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": "quota_window",
            "unit": "unknown",
            "status": "error",
            "observed_at": now_ts,
            "windows": [],
            "stale": False,
            "last_good_at": None,
            "error_code": error_code,
            "error_reason": error_reason,
        }

    def compute_stale(self, snapshot: dict[str, Any], reference_time: str | None) -> dict[str, Any]:
        """Check 0/299/300 stale boundary against observed_at without modifying source timestamp."""
        if not reference_time or not snapshot.get("observed_at"):
            return snapshot

        ref_dt = parse_rfc3339(reference_time)
        obs_dt = parse_rfc3339(snapshot["observed_at"])
        age_seconds = (ref_dt - obs_dt).total_seconds()

        snap = copy.deepcopy(snapshot)
        if age_seconds >= STALE_THRESHOLD_SECONDS:
            snap["stale"] = True
            if snap.get("status") == "available":
                snap["status"] = "stale"
                snap["error_code"] = snap.get("error_code") or "SOURCE_TIMEOUT"
                snap["error_reason"] = snap.get("error_reason") or f"Source age {age_seconds:.1f}s exceeded threshold"
        else:
            snap["stale"] = False

        return snap


class SharedCollectionState:
    """Manages multi-source cache, error isolation, and fixture loading."""

    def __init__(self):
        self.sources: dict[str, CollectionSourceState] = {}
        self.global_reset_last_good: dict[str, Any] | None = None

    def get_source(self, source_id: str) -> CollectionSourceState:
        if source_id not in self.sources:
            self.sources[source_id] = CollectionSourceState(source_id)
        return self.sources[source_id]

    def collect_all(
        self,
        session_file: Path | None = None,
        session_dir: Path | None = None,
        session_id: str | None = None,
        use_latest: bool = False,
        live_quota: bool = False,
        provider_fixtures: list[Path] | None = None,
        personal_usage_fixture: Path | None = None,
        global_reset_file: Path | None = None,
        host_alias: str = "pc-collector",
        agent_id: str = "codex-cli",
        reference_time: str | None = None,
    ) -> dict[str, Any]:
        usage_snapshots = []
        global_resets = []

        # 1. Session Telemetry Collection (Isolated)
        if session_file or session_dir:
            src = self.get_source("session")
            try:
                selected_session = None
                if session_file:
                    if not session_file.exists():
                        raise SessionError(f"Session file not found: {session_file}")
                    selected_session = parse_session_file(session_file)
                    if not selected_session:
                        raise SessionError(f"No valid token metadata in {session_file}")
                elif session_dir:
                    if not session_dir.exists():
                        raise SessionError(f"Session dir not found: {session_dir}")
                    sessions = scan_sessions_directory(session_dir)
                    if session_id:
                        if session_id not in sessions:
                            raise SessionError(f"Session ID {session_id!r} not found in {session_dir}")
                        selected_session = sessions[session_id]
                    elif use_latest:
                        selected_session = select_latest_session(sessions)
                        if not selected_session:
                            raise SessionError(f"No valid session to select in {session_dir}")
                    else:
                        raise SessionError("Either --session-id or --latest required")

                if selected_session:
                    snap = build_session_telemetry_snapshot(
                        selected_session,
                        host_alias=host_alias,
                        agent_id=agent_id,
                        reference_time=reference_time,
                    )
                    semantic_validate_snapshot(snap, reference_time=reference_time)
                    snap = src.compute_stale(snap, reference_time)
                    usage_snapshots.append(src.update_good(snap))
            except Exception as exc:
                err_snap = src.update_error("SESSION_COLLECTION_ERROR", str(exc), reference_time=reference_time)
                usage_snapshots.append(err_snap)

        # 2. Account Quota Collection (Isolated)
        if live_quota:
            src = self.get_source("quota")
            try:
                quota_res = fetch_native_rate_limits(reference_time=reference_time)
                snap = build_account_quota_snapshot(
                    quota_res,
                    host_alias=host_alias,
                    agent_id=agent_id,
                    reference_time=reference_time,
                )
                semantic_validate_snapshot(snap, reference_time=reference_time)
                snap = src.compute_stale(snap, reference_time)
                if quota_res.error_code:
                    usage_snapshots.append(src.update_error(quota_res.error_code, quota_res.error_reason or "", reference_time))
                else:
                    usage_snapshots.append(src.update_good(snap))
            except Exception as exc:
                usage_snapshots.append(src.update_error("QUOTA_COLLECTION_ERROR", str(exc), reference_time))

        # 3. Provider Fixtures (Preserves existing shapes and fixture provenance)
        if provider_fixtures:
            for fix_path in provider_fixtures:
                src = self.get_source(f"fixture_{fix_path.stem}")
                try:
                    data = json.loads(fix_path.read_text(encoding="utf-8-sig"))
                    entries = data if isinstance(data, list) else [data]
                    for entry in entries:
                        # Ensure fixture source_kind is set
                        entry["source_kind"] = "fixture"
                        semantic_validate_snapshot(entry, reference_time=reference_time)
                        entry = src.compute_stale(entry, reference_time)
                        usage_snapshots.append(src.update_good(entry))
                except Exception as exc:
                    usage_snapshots.append(src.update_error("FIXTURE_LOAD_ERROR", str(exc), reference_time))

        # 4. Personal Usage Fixture (experiments/fixtures/personal-usage.json format)
        if personal_usage_fixture and personal_usage_fixture.exists():
            src = self.get_source("personal_usage_fixture")
            try:
                data = json.loads(personal_usage_fixture.read_text(encoding="utf-8-sig"))
                # Map personal usage format to UsageSnapshot
                captured_at = data.get("captured_at")
                windows = []
                for w in data.get("windows", []):
                    windows.append(
                        {
                            "window_id": str(w.get("id", "win")),
                            "label": str(w.get("label", "Window")),
                            "used_units": None,
                            "remaining_units": None,
                            "limit_units": None,
                            "unit": "percent",
                            "percent_used": float(w.get("percent_used", 0)),
                            "percent_remaining": float(w.get("percent_remaining", 100)),
                            "resets_at": w.get("resets_at"),
                            "reset_status": "unknown",
                        }
                    )
                snap = {
                    "schema_version": 1,
                    "snapshot_id": "personal-usage-fixture",
                    "provider_id": "codex",
                    "agent_id": sanitize_identity(agent_id),
                    "host_id": sanitize_identity(host_alias),
                    "model_id": None,
                    "account_profile_id": "personal-synthetic",
                    "source_kind": "fixture",
                    "metric_kind": "quota_window",
                    "unit": "percent",
                    "status": "available",
                    "observed_at": captured_at,
                    "windows": windows,
                    "stale": bool(data.get("stale", False)),
                    "last_good_at": captured_at,
                    "error_code": data.get("error_code"),
                    "error_reason": None,
                }
                semantic_validate_snapshot(snap, reference_time=reference_time)
                snap = src.compute_stale(snap, reference_time)
                usage_snapshots.append(src.update_good(snap))
            except Exception as exc:
                usage_snapshots.append(src.update_error("PERSONAL_USAGE_FIXTURE_ERROR", str(exc), reference_time))

        # 5. Global Reset Collection (Preserves source & captured_at strictly)
        if global_reset_file and global_reset_file.exists():
            try:
                raw_reset = json.loads(global_reset_file.read_text(encoding="utf-8-sig"))
                norm_reset = normalize_global_reset(raw_reset)
                if not norm_reset.get("captured_at"):
                    raise ValueError("Missing captured_at in global reset")
                self.global_reset_last_good = copy.deepcopy(norm_reset)
                global_resets.append(norm_reset)
            except Exception as exc:
                if self.global_reset_last_good:
                    retained = copy.deepcopy(self.global_reset_last_good)
                    retained["stale"] = True
                    retained["error_code"] = "GLOBAL_RESET_ERROR"
                    global_resets.append(retained)
                else:
                    ref_ts = reference_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    global_resets.append(
                        {
                            "schema_version": 1,
                            "source": "codex-resets.com",
                            "captured_at": ref_ts,
                            "latest_reset_at": None,
                            "forecast_24h_percent": None,
                            "forecast_48h_percent": None,
                            "forecast_is_schedule": False,
                            "stale": True,
                            "error_code": "GLOBAL_RESET_ERROR",
                        }
                    )

        return {
            "usage": usage_snapshots,
            "global_resets": global_resets,
        }


def sanitize_identity(value: str) -> str:
    from pc.normalizer import sanitize_identity as s_id
    return s_id(value)
