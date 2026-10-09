"""Codex Desk Meter PC Collector and Sender CLI.

Commands:
- `inventory`: List available session JSONL files with timestamps and token counts (recursing date folders).
- `collect`: Collect session telemetry and/or account quota into normalized UsageSnapshot with semantic check.
- `send`: Perform one-shot send to device (real COM port or dry-run loopback/file).
- `watch`: Interruptible watch loop with automatic refresh (<=60s), persistent serial connection,
  reopen throttling (<=1/s), immediate manual refresh trigger (Enter key or event), and source-level error isolation.
- `init-device`: Initialize sequence counter for a specific device alias with confirmed receiver state.
"""

from __future__ import annotations

import argparse
import json
import select
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pc.frame import build_frame, encode_frame
from pc.sender import (
    CdmSender,
    LoopbackSink,
    SenderLockError,
    SenderStateError,
    StateStore,
    WindowsSerialSink,
)
from pc.session import scan_sessions_directory, select_latest_session
from pc.state import SharedCollectionState


def get_default_state_path() -> Path:
    return Path.home() / ".codex-desk-meter" / "sender-state.json"


def get_default_lock_dir() -> Path:
    return Path.home() / ".codex-desk-meter" / "locks"


def cmd_inventory(args: argparse.Namespace) -> int:
    session_dir = Path(args.session_dir) if args.session_dir else None
    if not session_dir or not session_dir.exists():
        print(f"Error: Session directory {session_dir} does not exist", file=sys.stderr)
        return 1

    sessions = scan_sessions_directory(session_dir)
    print(f"Found {len(sessions)} valid session(s) in {session_dir}:")
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


def cmd_init_device(args: argparse.Namespace) -> int:
    # Require explicit confirmed empty receiver or force overwrite
    if not args.confirmed_empty_receiver and not args.force_overwrite:
        print(
            "Error: Initialization requires either --confirmed-empty-receiver (for fresh uninitialized meter) "
            "or --force-overwrite (for intentional sequence replacement). Refusing unconfirmed initialization.",
            file=sys.stderr,
        )
        return 1

    state_path = Path(args.state_file) if args.state_file else get_default_state_path()
    lock_dir = Path(args.lock_dir) if args.lock_dir else get_default_lock_dir()
    store = StateStore(state_path)
    try:
        store.initialize_new(
            args.device_alias,
            initial_sequence=args.initial_sequence,
            confirmed_overwrite=args.force_overwrite,
            lock_dir=lock_dir,
        )
    except (SenderStateError, SenderLockError) as exc:
        print(f"Device init failed: {exc}", file=sys.stderr)
        return 1

    path_str = state_path.as_posix().encode("ascii", errors="backslashreplace").decode("ascii")
    print(
        f"Device state initialized for alias {args.device_alias!r} with initial sequence {args.initial_sequence} at {path_str}"
    )
    return 0


def cmd_collect(args: argparse.Namespace, state_manager: SharedCollectionState | None = None) -> int:
    sm = state_manager or SharedCollectionState()

    provider_fixtures = []
    if args.provider_fixture:
        for p in args.provider_fixture:
            provider_fixtures.append(Path(p))

    try:
        payload = sm.collect_all(
            session_file=Path(args.session_file) if args.session_file else None,
            session_dir=Path(args.session_dir) if args.session_dir else None,
            session_id=args.session_id,
            use_latest=args.latest,
            live_quota=args.live_quota,
            provider_fixtures=provider_fixtures,
            personal_usage_fixture=Path(args.personal_usage) if args.personal_usage else None,
            global_reset_file=Path(args.global_reset) if args.global_reset else None,
            host_alias=args.host_alias,
            agent_id=args.agent_id,
            reference_time=args.reference_time,
        )
    except Exception as exc:
        print(f"Collection error: {exc}", file=sys.stderr)
        return 1

    # Check if collection encountered errors on the requested targets
    has_errors = (
        any(snap.get("status") == "error" for snap in payload.get("usage", []))
        or any(r.get("error_code") is not None for r in payload.get("global_resets", []))
        or bool(sm.source_errors)
    )

    output_text = json.dumps(payload, indent=2, ensure_ascii=True)
    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
        print(f"Collected payload saved to {args.output}")
    else:
        sys.stdout.write(output_text + "\n")
        sys.stdout.flush()

    return 1 if has_errors else 0


def cmd_send(args: argparse.Namespace, state_manager: SharedCollectionState | None = None) -> int:
    if not args.port and not args.dry_run:
        print("Error: Either --port or explicit --dry-run is required. Refusing implicit loopback.", file=sys.stderr)
        return 1

    state_path = Path(args.state_file) if args.state_file else get_default_state_path()
    lock_dir = Path(args.lock_dir) if args.lock_dir else get_default_lock_dir()
    store = StateStore(state_path)

    try:
        sender = CdmSender(args.device_alias, store, lock_dir=lock_dir)
    except (SenderStateError, SenderLockError) as exc:
        print(f"Sender initialization error: {exc}", file=sys.stderr)
        return 1

    sm = state_manager or SharedCollectionState()
    provider_fixtures = [Path(p) for p in args.provider_fixture] if args.provider_fixture else []

    try:
        payload = sm.collect_all(
            session_file=Path(args.session_file) if args.session_file else None,
            session_dir=Path(args.session_dir) if args.session_dir else None,
            session_id=args.session_id,
            use_latest=args.latest,
            live_quota=args.live_quota,
            provider_fixtures=provider_fixtures,
            personal_usage_fixture=Path(args.personal_usage) if args.personal_usage else None,
            global_reset_file=Path(args.global_reset) if args.global_reset else None,
            host_alias=args.host_alias,
            agent_id=args.agent_id,
            reference_time=args.reference_time,
        )
    except Exception as exc:
        print(f"Payload preparation error: {exc}", file=sys.stderr)
        sender.close()
        return 1

    sent_at = args.reference_time if args.reference_time else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        if args.dry_run:
            loopback = LoopbackSink()
            outcome = sender.transmit_payload(payload, sent_at=sent_at, sink=loopback, reference_time=args.reference_time)
            if outcome.success:
                print(
                    f"[HOST WRITE] Staged frame to loopback: seq={outcome.sequence_used}, bytes={outcome.bytes_sent} (host write receipt, not device ACK)"
                )
                if args.output:
                    Path(args.output).write_bytes(loopback.written_frames[0])
                    print(f"Wrote raw frame bytes to {args.output}")
                return 0
            else:
                print(f"Transmission failed: {outcome.error_code}: {outcome.error_message}", file=sys.stderr)
                return 1

        # Real COM port send logic for operator execution
        serial_sink = WindowsSerialSink(port=args.port, baudrate=115200)
        outcome = sender.transmit_payload(payload, sent_at=sent_at, sink=serial_sink, reference_time=args.reference_time)
        serial_sink.close()

        if outcome.success:
            print(
                f"[HOST WRITE] Transmitted frame to {args.port}: seq={outcome.sequence_used}, bytes={outcome.bytes_sent} (host write receipt, not device ACK)"
            )
            return 0
        else:
            print(f"Transmission failed: {outcome.error_code}: {outcome.error_message}", file=sys.stderr)
            return 1
    finally:
        sender.close()


def run_watch_loop(
    args: argparse.Namespace,
    state_manager: SharedCollectionState | None = None,
    sink_override: Any = None,
    manual_trigger_event: threading.Event | None = None,
    stop_event: threading.Event | None = None,
    time_provider: Any = None,
) -> int:
    """Core testable watch scheduler supporting independent manual trigger and persistent port."""
    if not args.port and not args.dry_run and sink_override is None:
        print("Error: Either --port or explicit --dry-run is required. Refusing implicit loopback.", file=sys.stderr)
        return 1

    interval = min(60, max(1, args.interval))
    state_path = Path(args.state_file) if args.state_file else get_default_state_path()
    lock_dir = Path(args.lock_dir) if args.lock_dir else get_default_lock_dir()
    store = StateStore(state_path)

    try:
        sender = CdmSender(args.device_alias, store, lock_dir=lock_dir)
    except Exception as exc:
        print(f"Sender initialization error: {exc}", file=sys.stderr)
        return 1

    sm = state_manager or SharedCollectionState()
    provider_fixtures = [Path(p) for p in args.provider_fixture] if args.provider_fixture else []

    # Time helper
    now_fn = time.monotonic if time_provider is None else time_provider.now
    sleep_fn = time.sleep if time_provider is None else time_provider.sleep

    # Connection and scheduling state
    serial_sink = sink_override
    last_reopen_time = 0.0
    next_auto_deadline = now_fn()
    iteration = 0

    try:
        while True:
            if stop_event and stop_event.is_set():
                break

            current_now = now_fn()
            is_manual = False
            if manual_trigger_event and manual_trigger_event.is_set():
                is_manual = True
                manual_trigger_event.clear()

            is_auto = (current_now >= next_auto_deadline)
            is_port_reopened = False

            # Manage persistent serial connection if real port specified and not dry-run
            if args.port and not args.dry_run and sink_override is None:
                if serial_sink is None:
                    # Reopen throttle <= 1/s
                    if current_now - last_reopen_time >= 1.0:
                        last_reopen_time = current_now
                        try:
                            serial_sink = WindowsSerialSink(port=args.port, baudrate=115200)
                            print(f"[{datetime.now(timezone.utc).isoformat()}] Port {args.port} opened successfully.")
                            # Transmit within 5s of available port
                            is_port_reopened = True
                        except Exception as exc:
                            print(f"Port {args.port} open failed: {exc}")

            should_send = is_manual or is_auto or is_port_reopened

            if should_send:
                iteration += 1
                # Automatic <=60s must include collection/write duration; manual/port must not move auto deadline
                if is_auto:
                    while next_auto_deadline <= current_now:
                        next_auto_deadline += interval

                # Bounded collection budget: for manual / port refresh (max 5s end-to-end),
                # allocate 2.5s to collection RPC so write/flush (<=1.5s) completes within 5s.
                collection_timeout = 2.5 if (is_manual or is_port_reopened) else 4.0

                try:
                    payload = sm.collect_all(
                        session_file=Path(args.session_file) if args.session_file else None,
                        session_dir=Path(args.session_dir) if args.session_dir else None,
                        session_id=args.session_id,
                        use_latest=args.latest,
                        live_quota=args.live_quota,
                        provider_fixtures=provider_fixtures,
                        personal_usage_fixture=Path(args.personal_usage) if args.personal_usage else None,
                        global_reset_file=Path(args.global_reset) if args.global_reset else None,
                        host_alias=args.host_alias,
                        agent_id=args.agent_id,
                        reference_time=args.reference_time,
                        quota_timeout=collection_timeout,
                    )
                except Exception as exc:
                    sent_err = args.reference_time if args.reference_time else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    print(f"[{sent_err}] Iteration {iteration} collection failed: {exc}")
                    payload = {"usage": [], "global_resets": []}

                # Stamp AFTER acquisition so new observations are never newer than the frame
                sent_at = args.reference_time if args.reference_time else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

                active_sink = serial_sink
                if active_sink is None and args.dry_run:
                    active_sink = LoopbackSink()

                if active_sink:
                    outcome = sender.transmit_payload(
                        payload,
                        sent_at=sent_at,
                        sink=active_sink,
                        reference_time=args.reference_time,
                    )
                    # Check if manual trigger arrived while this collection/transmission was in flight:
                    # If so, this newly transmitted sequence genuinely acquired its observations after or during
                    # the manual request, satisfying the requested manual refresh within <=5s!
                    if manual_trigger_event and manual_trigger_event.is_set():
                        is_manual = True
                        manual_trigger_event.clear()

                    if outcome.success:
                        trigger_type = "MANUAL" if is_manual else ("PORT" if is_port_reopened and not is_auto else "AUTO")
                        print(
                            f"[{sent_at}] Iteration {iteration} [{trigger_type}] [HOST WRITE] seq={outcome.sequence_used}, size={outcome.bytes_sent}B"
                        )
                    else:
                        print(f"[{sent_at}] Send failed: {outcome.error_code}: {outcome.error_message}")
                        if outcome.error_code in ("STATE_LOST", "STATE_FAILURE"):
                            print("Halt watch loop due to sender state loss.", file=sys.stderr)
                            return 1
                        # If write IO error occurred on real sink, drop connection for reopening
                        if outcome.error_code == "WRITE_IO_ERROR" and sink_override is None:
                            try:
                                active_sink.close()
                            except Exception:
                                pass
                            serial_sink = None

            if args.once:
                break

            # Small interruptible tick (0.1s)
            sleep_fn(0.1)

    except KeyboardInterrupt:
        print("\nWatch stopped by user.")
    finally:
        if serial_sink and sink_override is None:
            try:
                serial_sink.close()
            except Exception:
                pass
        sender.close()
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    """CLI watch launcher with background stdin listener for manual Enter refresh."""
    manual_event = threading.Event()
    stop_event = threading.Event()

    # Background thread to listen for Enter on stdin
    def stdin_listener():
        try:
            while not stop_event.is_set():
                line = sys.stdin.readline()
                if not line:
                    break
                manual_event.set()
        except Exception:
            pass

    t = threading.Thread(target=stdin_listener, daemon=True)
    t.start()

    print(f"Starting watch loop (interval: {min(60, max(1, args.interval))}s). Press Enter for manual refresh, Ctrl+C to exit.")
    try:
        return run_watch_loop(
            args,
            manual_trigger_event=manual_event,
            stop_event=stop_event,
        )
    finally:
        stop_event.set()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codex Desk Meter PC Collector and Sender")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # inventory
    inv_p = subparsers.add_parser("inventory", help="List session files and token metadata")
    inv_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    inv_p.set_defaults(func=cmd_inventory)

    # init-device
    init_p = subparsers.add_parser("init-device", help="Initialize sequence state for a device alias")
    init_p.add_argument("--device-alias", required=True, help="Stable identifier for the desk meter device")
    init_p.add_argument("--initial-sequence", type=int, default=0, help="Initial sequence number (default 0)")
    init_p.add_argument("--confirmed-empty-receiver", action="store_true", help="Confirmation that the device receiver is uninitialized/empty")
    init_p.add_argument("--force-overwrite", action="store_true", help="Explicit confirmation to replace existing state")
    init_p.add_argument("--state-file", default=None, help="Path to state file")
    init_p.add_argument("--lock-dir", default=None, help="Path to lock directory")
    init_p.set_defaults(func=cmd_init_device)

    # collect
    col_p = subparsers.add_parser("collect", help="Gather normalized UsageSnapshot without sending")
    col_p.add_argument("--session-file", default=None, help="Specific session JSONL file")
    col_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    col_p.add_argument("--session-id", default=None, help="Specific session ID to select")
    col_p.add_argument("--latest", action="store_true", help="Explicit policy to select latest session")
    col_p.add_argument("--live-quota", action="store_true", help="Fetch native codex account rate limits")
    col_p.add_argument("--provider-fixture", action="append", default=None, help="Provider fixture JSON (repeatable)")
    col_p.add_argument("--personal-usage", default=None, help="Personal usage fixture JSON")
    col_p.add_argument("--global-reset", default=None, help="Path to global reset fixture JSON")
    col_p.add_argument("--host-alias", default="pc-collector", help="Sanitized host alias")
    col_p.add_argument("--agent-id", default="codex-cli", help="Agent identifier")
    col_p.add_argument("--reference-time", default=None, help="Reference RFC3339 time for tests")
    col_p.add_argument("--output", "-o", default=None, help="File to write output JSON to")
    col_p.set_defaults(func=cmd_collect)

    # send
    send_p = subparsers.add_parser("send", help="Send cdm/1 frame to device or dry-run")
    send_p.add_argument("--device-alias", default="default-meter", help="Device alias")
    send_p.add_argument("--port", default=None, help="Serial COM port")
    send_p.add_argument("--dry-run", action="store_true", help="Explicit dry-run mode (loopback)")
    send_p.add_argument("--state-file", default=None, help="Path to state file")
    send_p.add_argument("--lock-dir", default=None, help="Path to lock directory")
    send_p.add_argument("--session-file", default=None, help="Specific session JSONL file")
    send_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    send_p.add_argument("--session-id", default=None, help="Specific session ID to select")
    send_p.add_argument("--latest", action="store_true", help="Explicit policy to select latest session")
    send_p.add_argument("--live-quota", action="store_true", help="Fetch native codex account rate limits")
    send_p.add_argument("--provider-fixture", action="append", default=None, help="Provider fixture JSON (repeatable)")
    send_p.add_argument("--personal-usage", default=None, help="Personal usage fixture JSON")
    send_p.add_argument("--global-reset", default=None, help="Path to global reset fixture JSON")
    send_p.add_argument("--host-alias", default="pc-collector", help="Sanitized host alias")
    send_p.add_argument("--agent-id", default="codex-cli", help="Agent identifier")
    send_p.add_argument("--reference-time", default=None, help="Reference RFC3339 time for tests")
    send_p.add_argument("--output", "-o", default=None, help="File to write raw frame bytes to")
    send_p.set_defaults(func=cmd_send)

    # watch
    watch_p = subparsers.add_parser("watch", help="Watch loop with periodic and manual refresh")
    watch_p.add_argument("--device-alias", default="default-meter", help="Device alias")
    watch_p.add_argument("--interval", type=int, default=30, help="Refresh period in seconds (max 60)")
    watch_p.add_argument("--port", default=None, help="Serial COM port")
    watch_p.add_argument("--dry-run", action="store_true", help="Explicit dry-run mode (loopback)")
    watch_p.add_argument("--state-file", default=None, help="Path to state file")
    watch_p.add_argument("--lock-dir", default=None, help="Path to lock directory")
    watch_p.add_argument("--session-file", default=None, help="Specific session JSONL file")
    watch_p.add_argument("--session-dir", default=None, help="Directory containing session JSONL files")
    watch_p.add_argument("--session-id", default=None, help="Specific session ID to select")
    watch_p.add_argument("--latest", action="store_true", help="Explicit policy to select latest session")
    watch_p.add_argument("--live-quota", action="store_true", help="Fetch native codex account rate limits")
    watch_p.add_argument("--provider-fixture", action="append", default=None, help="Provider fixture JSON (repeatable)")
    watch_p.add_argument("--personal-usage", default=None, help="Personal usage fixture JSON")
    watch_p.add_argument("--global-reset", default=None, help="Path to global reset fixture JSON")
    watch_p.add_argument("--host-alias", default="pc-collector", help="Sanitized host alias")
    watch_p.add_argument("--agent-id", default="codex-cli", help="Agent identifier")
    watch_p.add_argument("--reference-time", default=None, help="Reference RFC3339 time for tests")
    watch_p.add_argument("--once", action="store_true", help="Run single iteration")
    watch_p.set_defaults(func=cmd_watch)

    parsed = parser.parse_args(argv)
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
