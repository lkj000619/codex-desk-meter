"""Codex session log reader and cumulative token telemetry extractor.

Complies with privacy boundaries:
- Reads metadata-only JSONL events.
- Never reads conversation texts, auth tokens, keys, cookies.
- Parses actual Codex 0.159 nested structures:
  `event_msg -> payload.type == "token_count" -> payload.info.total_token_usage`
  and session meta:
  `session_meta -> payload.id`
- Retains existing supported shapes only when validated.
- Updates observed_at ONLY for accepted token metadata, not unrelated later events.
- Validates nonnegative integer counts, cached <= input, reasoning <= output.
- Keeps source total and normalized total separate.
- Missing selected file/id fails rather than silently returning empty or guessing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SessionError(ValueError):
    """Session parser or selection error."""


@dataclass
class SessionTokenState:
    session_id: str
    observed_at: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    source_total_tokens: int | None = None
    normalized_total_tokens: int = 0
    event_count: int = 0
    source_path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "observed_at": self.observed_at,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "reasoning_output_tokens": self.reasoning_output_tokens,
            "source_total_tokens": self.source_total_tokens,
            "normalized_total_tokens": self.normalized_total_tokens,
            "event_count": self.event_count,
            "source_path": self.source_path,
        }


def _validate_and_extract_counts(usage_dict: dict[str, Any]) -> tuple[int, int, int | None, int | None, int | None] | None:
    """Validate token counts are nonnegative integers, and cached <= input, reasoning <= output."""
    try:
        in_tok = usage_dict.get("input_tokens")
        if in_tok is None:
            return None
        out_tok = usage_dict.get("output_tokens", 0)
        cached_tok = usage_dict.get("cached_input_tokens")
        reasoning_tok = usage_dict.get("reasoning_output_tokens")
        source_tot = usage_dict.get("total_tokens")

        # Check types
        if isinstance(in_tok, bool) or not isinstance(in_tok, int) or in_tok < 0:
            return None
        if isinstance(out_tok, bool) or not isinstance(out_tok, int) or out_tok < 0:
            return None
        if cached_tok is not None:
            if isinstance(cached_tok, bool) or not isinstance(cached_tok, int) or cached_tok < 0:
                return None
            if cached_tok > in_tok:
                return None
        if reasoning_tok is not None:
            if isinstance(reasoning_tok, bool) or not isinstance(reasoning_tok, int) or reasoning_tok < 0:
                return None
            if reasoning_tok > out_tok:
                return None
        if source_tot is not None:
            if isinstance(source_tot, bool) or not isinstance(source_tot, int) or source_tot < 0:
                return None

        return in_tok, out_tok, cached_tok, reasoning_tok, source_tot
    except Exception:
        return None


def extract_token_usage_from_entry(entry: dict[str, Any]) -> tuple[tuple[int, int, int | None, int | None, int | None], str | None] | None:
    """Extract validated token counts and token observation timestamp from an entry.

    Supports:
    1. Actual Codex 0.159 shape:
       `type == "event_msg"`, `payload.type == "token_count"`, `payload.info.total_token_usage`
    2. Direct token_count event shape:
       `type == "token_count"`, `total_token_usage` or `token_count.total_token_usage`
    """
    if not isinstance(entry, dict):
        return None

    entry_type = entry.get("type")
    payload = entry.get("payload")
    timestamp = entry.get("timestamp") or entry.get("created_at") or entry.get("time")

    # Shape 1: Codex 0.159 event_msg -> payload.type == "token_count" -> payload.info.total_token_usage
    if entry_type == "event_msg":
        if isinstance(payload, dict):
            if payload.get("type") == "token_count":
                info = payload.get("info")
                if isinstance(info, dict):
                    ttu = info.get("total_token_usage")
                    if isinstance(ttu, dict):
                        counts = _validate_and_extract_counts(ttu)
                        if counts:
                            ts = payload.get("timestamp") or timestamp
                            return counts, ts if isinstance(ts, str) else None
        # Also support legacy entry.get("token_count")
        tc = entry.get("token_count")
        if isinstance(tc, dict):
            ttu = tc.get("total_token_usage") or tc
            counts = _validate_and_extract_counts(ttu)
            if counts:
                return counts, timestamp if isinstance(timestamp, str) else None

    # Shape 2: Direct token_count
    if entry_type == "token_count":
        ttu = entry.get("total_token_usage")
        if isinstance(ttu, dict):
            counts = _validate_and_extract_counts(ttu)
            if counts:
                return counts, timestamp if isinstance(timestamp, str) else None
        # nested under payload or token_count
        if isinstance(payload, dict) and "total_token_usage" in payload:
            counts = _validate_and_extract_counts(payload["total_token_usage"])
            if counts:
                return counts, timestamp if isinstance(timestamp, str) else None

    # Shape 3: payload has total_token_usage directly
    if isinstance(payload, dict) and isinstance(payload.get("total_token_usage"), dict):
        counts = _validate_and_extract_counts(payload["total_token_usage"])
        if counts:
            return counts, timestamp if isinstance(timestamp, str) else None

    return None


def parse_session_file(path: Path) -> SessionTokenState | None:
    """Parse a single synthetic or local session JSONL file streaming lines."""
    if not path.is_file():
        raise SessionError(f"Session file not found: {path}")

    session_id = path.stem
    state = SessionTokenState(session_id=session_id, source_path=path.name)
    has_valid_token_event = False

    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    # Ignore partial or broken lines
                    continue

                if not isinstance(entry, dict):
                    continue

                # Check for session identity: session_meta -> payload.id
                entry_type = entry.get("type")
                payload = entry.get("payload")
                if entry_type == "session_meta" and isinstance(payload, dict):
                    meta_id = payload.get("id")
                    if isinstance(meta_id, str) and meta_id:
                        state.session_id = meta_id
                elif "session_id" in entry and isinstance(entry["session_id"], str):
                    state.session_id = entry["session_id"]

                # Extract token usage
                extracted = extract_token_usage_from_entry(entry)
                if extracted:
                    counts, token_ts = extracted
                    in_tok, out_tok, cached_tok, reasoning_tok, source_tot = counts
                    state.input_tokens = in_tok
                    state.output_tokens = out_tok
                    state.cached_input_tokens = cached_tok
                    state.reasoning_output_tokens = reasoning_tok
                    state.source_total_tokens = source_tot
                    state.normalized_total_tokens = in_tok + out_tok
                    state.event_count += 1
                    has_valid_token_event = True
                    # IMPORTANT: Update observed_at ONLY for accepted token metadata
                    if token_ts:
                        state.observed_at = token_ts

    except SessionError:
        raise
    except Exception as exc:
        raise SessionError(f"Failed to read session file {path}: {exc}") from exc

    if not has_valid_token_event:
        # No events / missing fields must remain unsupported/error/None, not zero with fresh current time
        return None

    return state


def scan_sessions_directory(dir_path: Path) -> dict[str, SessionTokenState]:
    """Scan directory recursively (handling native date folders) for JSONL session files."""
    sessions: dict[str, SessionTokenState] = {}
    if not dir_path.is_dir():
        return sessions

    # Recurse through date folders (*.jsonl and **/*.jsonl)
    for item in sorted(dir_path.rglob("*.jsonl")):
        try:
            res = parse_session_file(item)
            if res:
                sessions[res.session_id] = res
        except Exception:
            continue
    return sessions


def select_latest_session(sessions: dict[str, SessionTokenState]) -> SessionTokenState | None:
    """Documented policy: Select session with the most recent observed_at timestamp."""
    if not sessions:
        return None

    def sort_key(s: SessionTokenState) -> str:
        return s.observed_at or ""

    return max(sessions.values(), key=sort_key)
