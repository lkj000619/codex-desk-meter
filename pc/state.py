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
    sanitize_snapshot_id,
)
from pc.quota import fetch_native_rate_limits
from pc.session import (
    SessionError,
    SessionTokenState,
    parse_session_file,
    scan_sessions_directory,
    select_latest_session,
)


def _sanitize_wire_reason(reason: str | None) -> str | None:
    if not reason:
        return reason
    import re
    # Replace Windows drive paths (C:\... or C:/...)
    cleaned = re.sub(r"[a-zA-Z]:[/\\][^\s:;,]+", "<local_path>", reason)
    # Replace UNC paths (\\...)
    cleaned = re.sub(r"\\\\[^\s:;,]+", "<local_path>", cleaned)
    # Replace Unix paths (/...)
    cleaned = re.sub(r"/(?:[a-zA-Z0-9_\-\.]+/)+[a-zA-Z0-9_\-\.]*", "<local_path>", cleaned)
    return cleaned


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
        safe_reason = _sanitize_wire_reason(error_reason)
        self.last_error_code = error_code
        self.last_error_reason = safe_reason

        # If we have a last-good snapshot, retain its values and mark error status
        if self.last_good_snapshot:
            err_snap = copy.deepcopy(self.last_good_snapshot)
            err_snap["status"] = "error"
            err_snap["error_code"] = error_code
            err_snap["error_reason"] = safe_reason
            return err_snap

        # If no prior good snapshot, create minimal error snapshot
        metric_kind = "session_telemetry" if "session" in self.source_id else "quota_window"
        unit = "token" if metric_kind == "session_telemetry" else "unknown"
        raw_key = self.source_id.split(":")[-1] if ":" in self.source_id else self.source_id
        safe_key = sanitize_snapshot_id(raw_key)
        return {
            "schema_version": 1,
            "snapshot_id": f"error-{safe_key}",
            "provider_id": "codex",
            "agent_id": "codex-cli",
            "host_id": "pc-collector",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": metric_kind,
            "unit": unit,
            "status": "error",
            "observed_at": None,
            "windows": [],
            "stale": False,
            "last_good_at": None,
            "error_code": error_code,
            "error_reason": safe_reason,
        }

    def compute_stale(self, snapshot: dict[str, Any], reference_time: str | None) -> dict[str, Any]:
        """Check 0/299/300 stale boundary against observed_at without modifying source timestamp."""
        if not snapshot.get("observed_at"):
            return snapshot

        ref_dt = parse_rfc3339(reference_time) if reference_time else datetime.now(timezone.utc)
        obs_dt = parse_rfc3339(snapshot["observed_at"])
        age_seconds = (ref_dt - obs_dt).total_seconds()

        snap = copy.deepcopy(snapshot)
        if age_seconds >= STALE_THRESHOLD_SECONDS:
            snap["stale"] = True
            if snap.get("status") == "available":
                snap["status"] = "stale"
                snap["error_code"] = snap.get("error_code") or "SOURCE_TIMEOUT"
                snap["error_reason"] = snap.get("error_reason") or f"Source age {age_seconds:.1f}s exceeded threshold"
            elif snap.get("status") == "error":
                snap["stale"] = True
        else:
            snap["stale"] = False

        return snap


class SharedCollectionState:
    """Manages multi-source cache, error isolation, and fixture loading."""

    def __init__(self):
        self.sources: dict[str, CollectionSourceState] = {}
        self.global_reset_caches: dict[str, dict[str, Any]] = {}
        self.provider_file_entries: dict[str, list[str]] = {}
        self.source_errors: dict[str, str] = {}
        self.session_file_sources: dict[str, str] = {}

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
        self.source_errors.clear()
        usage_snapshots = []
        global_resets = []

        # 1. Session Telemetry Collection (Isolated)
        if session_file or session_dir:
            if session_file:
                path_ctx = session_file.resolve().as_posix()
                try:
                    if not session_file.exists():
                        raise SessionError(f"Session file not found: {session_file.name}")
                    selected_session = parse_session_file(session_file)
                    if not selected_session:
                        raise SessionError(f"No valid token metadata in {session_file.name}")
                    if selected_session.observed_at is None:
                        raise SessionError(f"Untimed session token observation in {session_file.name}")

                    sess_key = f"session_file:{path_ctx}:{selected_session.session_id}"
                    self.session_file_sources[path_ctx] = sess_key
                    src = self.get_source(sess_key)

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
                    self.source_errors[f"session_file:{path_ctx}"] = str(exc)
                    prior_key = self.session_file_sources.get(path_ctx)
                    if prior_key and prior_key in self.sources:
                        src = self.sources[prior_key]
                    else:
                        safe_name = sanitize_snapshot_id(session_file.name)
                        src = self.get_source(f"session_file:{path_ctx}:session_{safe_name}")
                    err_snap = src.update_error("SESSION_COLLECTION_ERROR", str(exc), reference_time=reference_time)
                    usage_snapshots.append(err_snap)

            elif session_dir:
                path_ctx = session_dir.resolve().as_posix()
                try:
                    if not session_dir.exists():
                        raise SessionError(f"Session dir not found: {session_dir.name}")
                    sessions = scan_sessions_directory(session_dir)
                    if session_id:
                        if session_id not in sessions:
                            raise SessionError(f"Session ID {session_id!r} not found in session dir")
                        selected_session = sessions[session_id]
                    elif use_latest:
                        selected_session = select_latest_session(sessions)
                        if not selected_session:
                            raise SessionError("No valid session to select in session dir")
                    else:
                        raise SessionError("Either --session-id or --latest required")

                    if selected_session.observed_at is None:
                        raise SessionError(f"Untimed session token observation for {selected_session.session_id}")

                    sess_key = f"session_dir:{path_ctx}:{selected_session.session_id}"
                    src = self.get_source(sess_key)

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
                    self.source_errors[f"session_dir:{path_ctx}"] = str(exc)
                    target_ident = session_id or ("latest" if use_latest else "unknown")
                    safe_ident = sanitize_snapshot_id(f"session_dir_{session_dir.name}_{target_ident}")
                    src = self.get_source(f"session_dir:{path_ctx}:{safe_ident}")
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
                    self.source_errors["quota"] = quota_res.error_code
                    usage_snapshots.append(src.update_error(quota_res.error_code, quota_res.error_reason or "", reference_time))
                else:
                    usage_snapshots.append(src.update_good(snap))
            except Exception as exc:
                self.source_errors["quota"] = str(exc)
                usage_snapshots.append(src.update_error("QUOTA_COLLECTION_ERROR", str(exc), reference_time))

        # 3. Provider Fixtures (Preserves shapes, isolates malformed entry, retains all on file failure)
        if provider_fixtures:
            for fix_path in provider_fixtures:
                fix_path_key = fix_path.resolve().as_posix()
                try:
                    if not fix_path.exists():
                        raise FileNotFoundError(f"Fixture file not found: {fix_path.name}")
                    data = json.loads(fix_path.read_text(encoding="utf-8-sig"))
                    entries = data if isinstance(data, list) else [data]
                    current_entry_ids = []
                    for idx, entry in enumerate(entries):
                        if not isinstance(entry, dict):
                            continue
                        entry_key = entry.get("snapshot_id") or f"{entry.get('provider_id')}_{entry.get('account_profile_id') or idx}"
                        src_id = f"fixture:{fix_path_key}:{entry_key}"
                        current_entry_ids.append(src_id)
                        src = self.get_source(src_id)
                        try:
                            entry["source_kind"] = "fixture"
                            semantic_validate_snapshot(entry, reference_time=reference_time)
                            entry = src.compute_stale(entry, reference_time)
                            usage_snapshots.append(src.update_good(entry))
                        except Exception as entry_exc:
                            self.source_errors[src_id] = str(entry_exc)
                            err_snap = src.update_error("FIXTURE_ENTRY_ERROR", str(entry_exc), reference_time)
                            usage_snapshots.append(err_snap)
                    self.provider_file_entries[fix_path_key] = current_entry_ids
                except Exception as file_exc:
                    self.source_errors[f"fixture_file:{fix_path_key}"] = str(file_exc)
                    saved_ids = self.provider_file_entries.get(fix_path_key, [])
                    if saved_ids:
                        for src_id in saved_ids:
                            src = self.get_source(src_id)
                            err_snap = src.update_error("FIXTURE_LOAD_ERROR", str(file_exc), reference_time)
                            usage_snapshots.append(err_snap)
                    else:
                        safe_name = sanitize_snapshot_id(fix_path.name)
                        src = self.get_source(f"fixture:{fix_path_key}:{safe_name}")
                        err_snap = src.update_error("FIXTURE_LOAD_ERROR", str(file_exc), reference_time)
                        usage_snapshots.append(err_snap)

        # 4. Personal Usage Fixture (experiments/fixtures/personal-usage.json format)
        if personal_usage_fixture:
            path_key = personal_usage_fixture.resolve().as_posix()
            src = self.get_source(f"personal_usage:{path_key}")
            try:
                if not personal_usage_fixture.exists():
                    raise FileNotFoundError(f"Personal usage fixture not found: {personal_usage_fixture.name}")
                data = json.loads(personal_usage_fixture.read_text(encoding="utf-8-sig"))
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
                self.source_errors[f"personal_usage:{path_key}"] = str(exc)
                usage_snapshots.append(src.update_error("PERSONAL_USAGE_FIXTURE_ERROR", str(exc), reference_time))

        # 5. Global Reset Collection (Preserves source & captured_at strictly, omits cold error on wire)
        if global_reset_file:
            path_key = global_reset_file.resolve().as_posix()
            try:
                if not global_reset_file.exists():
                    raise FileNotFoundError(f"Global reset file not found: {global_reset_file.name}")
                raw_reset = json.loads(global_reset_file.read_text(encoding="utf-8-sig"))
                norm_reset = normalize_global_reset(raw_reset)
                if not norm_reset.get("captured_at"):
                    raise ValueError("Missing captured_at in global reset")
                cap_dt = parse_rfc3339(norm_reset["captured_at"])
                ref_dt = parse_rfc3339(reference_time) if reference_time else datetime.now(timezone.utc)
                age_seconds = (ref_dt - cap_dt).total_seconds()
                if age_seconds >= STALE_THRESHOLD_SECONDS:
                    norm_reset["stale"] = True
                self.global_reset_caches[path_key] = copy.deepcopy(norm_reset)
                global_resets.append(norm_reset)
            except Exception as exc:
                self.source_errors[f"global_reset:{path_key}"] = str(exc)
                import sys
                print(f"Global reset source error: {exc}", file=sys.stderr)
                if path_key in self.global_reset_caches:
                    retained = copy.deepcopy(self.global_reset_caches[path_key])
                    retained["stale"] = True
                    retained["error_code"] = "GLOBAL_RESET_ERROR"
                    global_resets.append(retained)
                else:
                    # Cold error: omit unobserved global record on wire to avoid captured_at=null schema violation
                    pass

        return {
            "usage": usage_snapshots,
            "global_resets": global_resets,
        }


def sanitize_identity(value: str) -> str:
    from pc.normalizer import sanitize_identity as s_id
    return s_id(value)
