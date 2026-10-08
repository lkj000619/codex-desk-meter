"""Codex session log reader and cumulative token telemetry extractor.

Complies with privacy boundaries:
- Reads metadata-only JSONL events.
- Never reads conversation texts, auth tokens, keys, cookies.
- Parses `event_msg` / `token_count` cumulative `total_token_usage`.
- Handles restarts, partial lines, replacements, multiple sessions.
- Keeps source total and normalized total separate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass
class SessionTokenState:
    session_id: str
    observed_at: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_output_tokens: int = 0
    source_total_tokens: int = 0
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


def parse_token_count_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Extract token counts from a token_count or event_msg payload if present.

    Expected structure in Codex CLI 0.159.x:
    type: "token_count" or "event_msg" with subtype / payload
    May contain total_token_usage:
      input_tokens, output_tokens, cached_input_tokens, reasoning_output_tokens, total_tokens
    Or top-level token_count dict.
    """
    if not isinstance(payload, dict):
        return None

    # Check for direct token_count object
    tc = payload.get("token_count")
    if isinstance(tc, dict):
        payload = tc

    # Check for total_token_usage
    ttu = payload.get("total_token_usage")
    if isinstance(ttu, dict):
        return ttu

    # Or fields directly in payload
    if "input_tokens" in payload or "total_tokens" in payload:
        return payload

    return None


def parse_session_file(path: Path) -> SessionTokenState | None:
    """Parse a single synthetic or local session JSONL file without storing raw messages."""
    session_id = path.stem
    state = SessionTokenState(session_id=session_id, source_path=path.name)

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            # Handle partial or truncated lines gracefully
            continue

        if not isinstance(entry, dict):
            continue

        # Look for explicit session identity if defined in log entry
        if "session_id" in entry and isinstance(entry["session_id"], str):
            state.session_id = entry["session_id"]

        timestamp = entry.get("timestamp") or entry.get("created_at") or entry.get("time")
        if isinstance(timestamp, str):
            # Normalise RFC3339 if needed
            state.observed_at = timestamp

        event_type = entry.get("type") or entry.get("event")
        # Check if this entry is a token count event
        data = None
        if event_type in ("token_count", "event_msg", "token_usage"):
            data = parse_token_count_event(entry)
        elif "total_token_usage" in entry or "token_count" in entry:
            data = parse_token_count_event(entry)

        if data:
            # These are cumulative values reported by the runtime
            in_tok = int(data.get("input_tokens") or 0)
            out_tok = int(data.get("output_tokens") or 0)
            cached_tok = int(data.get("cached_input_tokens") or 0)
            reasoning_tok = int(data.get("reasoning_output_tokens") or 0)
            source_tot = int(data.get("total_tokens") or 0)

            # Cumulative values replace previous values, not double-sum
            state.input_tokens = in_tok
            state.output_tokens = out_tok
            state.cached_input_tokens = cached_tok
            state.reasoning_output_tokens = reasoning_tok
            state.source_total_tokens = source_tot
            state.normalized_total_tokens = in_tok + out_tok
            state.event_count += 1

    if state.event_count == 0 and state.observed_at is None:
        return None

    if state.observed_at is None:
        state.observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return state


def scan_sessions_directory(dir_path: Path) -> dict[str, SessionTokenState]:
    """Scan directory for JSONL session files and return map by session_id."""
    sessions: dict[str, SessionTokenState] = {}
    if not dir_path.is_dir():
        return sessions

    for item in sorted(dir_path.glob("*.jsonl")):
        res = parse_session_file(item)
        if res:
            sessions[res.session_id] = res
    return sessions


def select_latest_session(sessions: dict[str, SessionTokenState]) -> SessionTokenState | None:
    """Documented policy: Select session with the most recent observed_at timestamp."""
    if not sessions:
        return None

    def sort_key(s: SessionTokenState) -> str:
        return s.observed_at or ""

    return max(sessions.values(), key=sort_key)
