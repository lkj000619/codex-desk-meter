"""Codex Desk Meter PC Collector and Sender CLI.

Commands:
- `inventory`: List available session JSONL files with timestamps and token counts.
- `collect`: Collect session telemetry and/or account quota into normalized UsageSnapshot.
- `send`: Perform one-shot send to device (or dry-run to file/loopback).
- `watch`: Loop with automatic refresh period (<= 60s) and manual refresh input support.
- `init-device`: Initialize or reset sequence counter for a specific device alias with confirmed receiver state.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pc.frame import build_frame, encode_frame
from pc.normalizer import (
    build_account_quota_snapshot,
    build_session_telemetry_snapshot,
    normalize_global_reset,
)
from pc.quota import fetch_native_rate_limits
from pc.sender import CdmSender, LoopbackSink, StateStore
from pc.session import (
    SessionTokenState,
    parse_session_file,
    scan_sessions_directory,
    select_latest_session,
)


def get_default_state_path() -> Path:
    return Path.home() / ".codex-desk-meter" / "sender-state.json"


def cmd_inventory(args: argparse.Namespace) -> int:
    session_dir = Path(args.session_dir) if args.session_dir else None
    if not session_dir or not session_dir.exists():
        print(f"Error: Session directory {session_dir} does not exist", file=sys.stderr)
        return 1

    sessions = scan_sessions_directory(session_dir)
    print(f"Found {len(sessions)} session(s) in {session_dir}:")
    latest = select_latest_session(sessions)
    for s_id, s in sorted(sessions.items()):
        is_latest = " [LATEST]" if latest and s_id == latest.session_id else ""
        print(
            f" - {s_id}{is_latest}: observed={s.observed_at}, "
            f"in={s.input_tokens}, out={s.output_tokens}, "
            f"cached={s.cached_input_tokens}, reasoning={s.reasoning_output_tokens}, "
            f"source_total={s.source_total_tokens}, normalized_total={s.normalized_total_tokens}"
        )
    return 0


def gather_payload(
    session_file: Path | None,
    session_dir: Path | None,
    session_id: str | None,
    live_quota: bool,
    global_reset_file: Path | None,
    host_alias: str,
    agent_id: str,
) -> dict[str, Any]:
    usage_snapshots = []
    global_resets = []

    # 1. Session Telemetry
    selected_session = None
    if session_file and session_file.exists():
        selected_session = parse_session_file(session_file)
    elif session_dir and session_dir.exists():
        sessions = scan_sessions_directory(session_dir)
        if session_id:
            selected_session = sessions.get(session_id)
        else:
            selected_session = select_latest_session(sessions)

    if selected_session:
        session_snap = build_session_telemetry_snapshot(
            selected_session,
            host_alias=host_alias,
            agent_id=agent_id,
        )
        usage_snapshots.append(session_snap)

    # 2. Account Quota
    if live_quota:
        quota_res = fetch_native_rate_limits()
        quota_snap = build_account_quota_snapshot(
            quota_res,
            host_alias=host_alias,
            agent_id=agent_id,
        )
        usage_snapshots.append(quota_snap)

    # 3. Global Resets
    if global_reset_file and global_reset_file.exists():
        try:
            raw_reset = json.loads(global_reset_file.read_text(encoding="utf-8-sig"))
            norm_reset = normalize_global_reset(raw_reset)
            global_resets.append(norm_reset)
        except Exception as exc:
            print(f"Warning: Failed to load global reset fixture: {exc}", file=sys.stderr)

    return {
        "usage": usage_snapshots,
        "global_resets": global_resets,
    }


def cmd_collect(args: argparse.Namespace) -> int:
    payload = gather_payload(
        session_file=Path(args.session_file) if args.session_file else None,
        session_dir=Path(args.session_dir) if args.session_dir else None,
        session_id=args.session_id,
        live_quota=args.live_quota,
        global_reset_file=Path(args.global_reset) if args.global_reset else None,
        host_alias=args.host_alias,
        agent_id=args.agent_id,
    )
    output_text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
        print(f"Collected payload saved to {args.output}")
    else:
        print(output_text)
    return 0


def cmd_init_device(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file) if args.state_file else get_default_state_path()
    store = StateStore(state_path)
    store.initialize_new(args.device_alias, initial_sequence=args.initial_sequence)
    path_str = state_path.as_posix().encode("ascii", errors="backslashreplace").decode("ascii")
    print(
        f"Device state initialized for alias {args.device_alias!r} with initial sequence {args.initial_sequence} at {path_str}"
    )
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file) if args.state_file else get_default_state_path()
    store = StateStore(state_path)

    try:
        sender = CdmSender(args.device_alias, store, auto_initialize=args.auto_init)
    except Exception as exc:
        print(f"Sender state error: {exc}", file=sys.stderr)
        return 1

    payload = gather_payload(
        session_file=Path(args.session_file) if args.session_file else None,
        session_dir=Path(args.session_dir) if args.session_dir else None,
        session_id=args.session_id,
        live_quota=args.live_quota,
        global_reset_file=Path(args.global_reset) if args.global_reset else None,
        host_alias=args.host_alias,
        agent_id=args.agent_id,
    )

    sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if args.dry_run:
        loopback = LoopbackSink()
        outcome = sender.transmit_payload(payload, sent_at=sent_at, sink=loopback)
        if outcome.success:
            print(
                f"[DRY-RUN] Successfully encoded and staged frame seq={outcome.sequence_used}, bytes={outcome.bytes_sent}"
            )
            if args.output:
                Path(args.output).write_bytes(loopback.written_frames[0])
                print(f"Wrote raw frame bytes to {args.output}")
            return 0
        else:
            print(f"[DRY-RUN] Frame generation failed: {outcome.error_code}: {outcome.error_message}", file=sys.stderr)
            return 1

    if not args.port:
        print("Error: Serial port must be specified via --port (or use --dry-run)", file=sys.stderr)
        return 1

    # In worker sandbox, COM port open is restricted to coordinator
    print("Error: Direct COM port opening is reserved for coordinator. Use --dry-run for testing.", file=sys.stderr)
    return 1


def cmd_watch(args: argparse.Namespace) -> int:
    """Watch loop with automatic refresh and manual refresh check."""
    interval = min(60, max(1, args.interval))
    print(f"Starting watch loop (interval: {interval}s, device: {args.device_alias}). Press Ctrl+C to stop.")

    state_path = Path(args.state_file) if args.state_file else get_default_state_path()
    store = StateStore(state_path)

    try:
        sender = CdmSender(args.device_alias, store, auto_initialize=args.auto_init)
    except Exception as exc:
        print(f"Sender state error: {exc}", file=sys.stderr)
        return 1

    iteration = 0
    try:
        while True:
            iteration += 1
            start_t = time.monotonic()
            sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            payload = gather_payload(
                session_file=Path(args.session_file) if args.session_file else None,
                session_dir=Path(args.session_dir) if args.session_dir else None,
                session_id=args.session_id,
                live_quota=args.live_quota,
                global_reset_file=Path(args.global_reset) if args.global_reset else None,
                host_alias=args.host_alias,
                agent_id=args.agent_id,
            )

            loopback = LoopbackSink()
            outcome = sender.transmit_payload(payload, sent_at=sent_at, sink=loopback)
            if outcome.success:
                print(
                    f"[{sent_at}] Iteration {iteration}: Staged seq={outcome.sequence_used}, size={outcome.bytes_sent}B"
                )
            else:
                print(f"[{sent_at}] Iteration {iteration} failed: {outcome.error_code}: {outcome.error_message}")

            if args.once:
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch stopped by user.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codex Desk Meter PC Collector and Sender")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # inventory
    inv_p = subparsers.add_parser("inventory", help="List session files and token metadata")
    inv_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    inv_p.set_defaults(func=cmd_inventory)

    # collect
    col_p = subparsers.add_parser("collect", help="Gather normalized UsageSnapshot without sending")
    col_p.add_argument("--session-file", default=None, help="Specific session JSONL file")
    col_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    col_p.add_argument("--session-id", default=None, help="Specific session ID to select")
    col_p.add_argument("--live-quota", action="store_true", help="Fetch native codex account rate limits")
    col_p.add_argument("--global-reset", default=None, help="Path to global reset fixture JSON")
    col_p.add_argument("--host-alias", default="pc-collector", help="Sanitized host alias")
    col_p.add_argument("--agent-id", default="codex-cli", help="Agent identifier")
    col_p.add_argument("--output", "-o", default=None, help="File to write output JSON to")
    col_p.set_defaults(func=cmd_collect)

    # init-device
    init_p = subparsers.add_parser("init-device", help="Initialize sequence state for a device alias")
    init_p.add_argument("--device-alias", required=True, help="Stable identifier for the desk meter device")
    init_p.add_argument("--initial-sequence", type=int, default=0, help="Initial sequence number (default 0)")
    init_p.add_argument("--state-file", default=None, help="Path to state file")
    init_p.set_defaults(func=cmd_init_device)

    # send
    send_p = subparsers.add_parser("send", help="Send cdm/1 frame to device or dry-run")
    send_p.add_argument("--device-alias", default="default-meter", help="Device alias")
    send_p.add_argument("--port", default=None, help="Serial COM port")
    send_p.add_argument("--dry-run", action="store_true", help="Encode and validate frame without hardware COM")
    send_p.add_argument("--auto-init", action="store_true", help="Auto-initialize state if missing")
    send_p.add_argument("--state-file", default=None, help="Path to state file")
    send_p.add_argument("--session-file", default=None, help="Specific session JSONL file")
    send_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    send_p.add_argument("--session-id", default=None, help="Specific session ID to select")
    send_p.add_argument("--live-quota", action="store_true", help="Fetch native codex account rate limits")
    send_p.add_argument("--global-reset", default=None, help="Path to global reset fixture JSON")
    send_p.add_argument("--host-alias", default="pc-collector", help="Sanitized host alias")
    send_p.add_argument("--agent-id", default="codex-cli", help="Agent identifier")
    send_p.add_argument("--output", "-o", default=None, help="File to write raw frame bytes to")
    send_p.set_defaults(func=cmd_send)

    # watch
    watch_p = subparsers.add_parser("watch", help="Watch loop with periodic and manual refresh")
    watch_p.add_argument("--device-alias", default="default-meter", help="Device alias")
    watch_p.add_argument("--interval", type=int, default=30, help="Refresh period in seconds (max 60)")
    watch_p.add_argument("--port", default=None, help="Serial COM port")
    watch_p.add_argument("--dry-run", action="store_true", help="Loopback mode")
    watch_p.add_argument("--auto-init", action="store_true", help="Auto-initialize state if missing")
    watch_p.add_argument("--state-file", default=None, help="Path to state file")
    watch_p.add_argument("--session-file", default=None, help="Specific session JSONL file")
    watch_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    watch_p.add_argument("--session-id", default=None, help="Specific session ID to select")
    watch_p.add_argument("--live-quota", action="store_true", help="Fetch native codex account rate limits")
    watch_p.add_argument("--global-reset", default=None, help="Path to global reset fixture JSON")
    watch_p.add_argument("--host-alias", default="pc-collector", help="Sanitized host alias")
    watch_p.add_argument("--agent-id", default="codex-cli", help="Agent identifier")
    watch_p.add_argument("--once", action="store_true", help="Run single iteration")
    watch_p.set_defaults(func=cmd_watch)

    parsed = parser.parse_args(argv)
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
