"""PC Fixture Collector and Serial Sender for Waveshare ESP32-S3-LCD-3.16.

Conforms to docs/PRODUCT_CONTRACT.md section 3 & 4:
- Collects and normalizes provider and global reset fixtures.
- Maintains atomic persistent sequence number state per device alias.
- Consumes a sequence number before write; even failed writes consume the sequence.
- Resumes with next sequence on restart without resetting receiver.
- Supports auto-refresh (<= 60s) and manual re-collection triggers.
- Transmits newline-delimited canonical cdm/1 JSON frame over 115200 8N1 serial.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from host_device_pipeline import (
    DEFAULT_SENT_AT,
    MAX_SEQUENCE,
    FixtureRegistry,
    LoopbackSerial,
    PipelineError,
    SerialBridge,
    build_frame,
    canonical_json,
    encode_frame,
    open_owner_serial,
    sequence_is_newer,
    sha256,
)


class PersistentSequenceManager:
    """Atomically persists and advances the sender sequence per device alias."""

    def __init__(self, state_dir: Path | str, device_alias: str):
        self.state_dir = Path(state_dir).resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.device_alias = device_alias
        self.state_file = self.state_dir / f".sender_state_{device_alias}.json"

    def initialize_new(self, initial_sequence: int = 1) -> int:
        """Explicit procedure to initialize state for an empty receiver."""
        state = {
            "device_alias": self.device_alias,
            "last_reserved_sequence": initial_sequence - 1,
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        self._atomic_save(state)
        return initial_sequence

    def _atomic_save(self, state: dict[str, Any]) -> None:
        temp_file = self.state_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        temp_file.replace(self.state_file)

    def _load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            raise PipelineError("SENDER_STATE_MISSING", f"No state file found at {self.state_file}. Explicit init required.")
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            if data.get("device_alias") != self.device_alias or "last_reserved_sequence" not in data:
                raise ValueError("Corrupt alias or missing sequence key")
            return data
        except Exception as exc:
            raise PipelineError("SENDER_STATE_CORRUPT", f"State file corrupted: {exc}")

    def reserve_next(self) -> int:
        """Reserve and persist the next sequence number before transmission.
        
        Even if transmission subsequently fails, the number is consumed.
        """
        state = self._load_state()
        last = state["last_reserved_sequence"]
        nxt = (last + 1) & MAX_SEQUENCE
        state["last_reserved_sequence"] = nxt
        state["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._atomic_save(state)
        return nxt

    def get_last_reserved(self) -> int | None:
        if not self.state_file.exists():
            return None
        return self._load_state()["last_reserved_sequence"]


class PcCollectorSender:
    """Manages fixture collection, serialization, and transmission."""

    def __init__(
        self,
        device_alias: str = "com3-default",
        state_dir: Path | str = ROOT / "results",
        reference_time: str | None = None,
        serial_factory: Callable[[str], Any] | None = None,
    ):
        self.device_alias = device_alias
        self.seq_manager = PersistentSequenceManager(state_dir, device_alias)
        self.reference_time = reference_time
        self.serial_factory = serial_factory
        self.bridge = SerialBridge()

    def collect_and_build(self, sequence: int, sent_at: str | None = None) -> tuple[dict[str, Any], bytes]:
        registry = FixtureRegistry.with_defaults(ROOT, reference_time=self.reference_time)
        collected = registry.collect()
        if sent_at is None:
            sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        frame = build_frame(collected.payload, sequence=sequence, sent_at=sent_at)
        line = encode_frame(frame)
        return frame, line

    def execute_send_step(
        self,
        port: str | None = None,
        loopback: LoopbackSerial | None = None,
        sent_at: str | None = None,
    ) -> dict[str, Any]:
        """Atomically reserves sequence number and writes frame."""
        # 1. Reserve sequence (consumed even on failure)
        seq = self.seq_manager.reserve_next()

        # 2. Build frame
        frame, line = self.collect_and_build(seq, sent_at=sent_at)

        # 3. Transmit
        if loopback is not None:
            outcome = self.bridge.send_loopback(frame, loopback)
        elif port is not None:
            outcome = self.bridge.send(frame, port, serial_factory=self.serial_factory or open_owner_serial)
        else:
            outcome = self.bridge.render(frame)

        return {
            "status": "success",
            "sequence": seq,
            "bytes_written": outcome.bytes_written,
            "frame_sha256": outcome.frame_sha256,
            "mode": outcome.mode,
            "sent_at": frame["sent_at"],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alias", default="device-waveshare-316", help="Device alias for sequence state tracking")
    parser.add_argument("--state-dir", default=str(ROOT / "results"), help="Directory storing sequence state")
    parser.add_argument("--init-sequence", type=int, help="Initialize state file with initial sequence")
    parser.add_argument("--port", help="Serial port to send to (e.g. COM3)")
    parser.add_argument("--dry-run", action="store_true", help="Render without serial transmission")
    parser.add_argument("--manual-refresh", action="store_true", help="Trigger one-off manual refresh transmission")
    args = parser.parse_args(argv)

    sender = PcCollectorSender(device_alias=args.alias, state_dir=args.state_dir)

    if args.init_sequence is not None:
        seq = sender.seq_manager.initialize_new(args.init_sequence)
        print(f"Initialized state for {args.alias} at next sequence {seq}")
        return 0

    try:
        if args.dry_run or not args.port:
            result = sender.execute_send_step()
            print(json.dumps(result, indent=2))
        else:
            result = sender.execute_send_step(port=args.port)
            print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
