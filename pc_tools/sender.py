"""cdm/1 USB-serial sender (candidate product, PC side).

Canonical JSON (sorted keys, no spaces, ensure_ascii=False, no NaN), CRC32
uppercase hex, single LF, <=65536 bytes, uint32 sequence with persistence.
Real serial access only via --send + --port (115200 8N1, no flow control,
reopen at most 1 Hz by the caller). Failed writes still consume the number.
State loss/corruption stops transmission; --init-alias re-provisions an
explicitly empty receiver only.
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL = "cdm/1"
MAX_SEQUENCE = 2**32 - 1
HALF_RANGE = 2**31
MAX_FRAME_BYTES = 64 * 1024


class SendError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def canonical(value) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SendError("CANONICAL_JSON_INVALID", str(exc))


def crc_hex(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"


def check_rfc3339(value: str) -> None:
    if not isinstance(value, str):
        raise SendError("TIMESTAMP_INVALID", "sent_at must be RFC3339")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SendError("TIMESTAMP_INVALID", f"sent_at is not RFC3339: {value!r}")
    if dt.tzinfo is None:
        raise SendError("TIMESTAMP_INVALID", "sent_at must include a timezone")


def build_frame(payload: dict, sequence: int, sent_at: str) -> dict:
    if not isinstance(payload, dict):
        raise SendError("PAYLOAD_INVALID", "payload must be an object")
    if (not isinstance(sequence, int) or isinstance(sequence, bool)
            or not 0 <= sequence <= MAX_SEQUENCE):
        raise SendError("SEQUENCE_INVALID", "sequence must fit uint32")
    check_rfc3339(sent_at)
    usage = payload.get("usage")
    resets = payload.get("global_resets")
    if not isinstance(usage, list) or not isinstance(resets, list):
        raise SendError("PAYLOAD_INVALID", "payload requires usage and global_resets")
    unsigned = {"payload": payload, "protocol": PROTOCOL,
                "sent_at": sent_at, "sequence": sequence}
    value = crc_hex(canonical(unsigned))
    return {"integrity": {"algorithm": "crc32", "value": value},
            "payload": payload, "protocol": PROTOCOL,
            "sent_at": sent_at, "sequence": sequence}


def encode_frame(frame: dict) -> bytes:
    if frame.get("protocol") != PROTOCOL:
        raise SendError("UNSUPPORTED_VERSION", "protocol must be cdm/1")
    unsigned = {k: frame[k] for k in ("payload", "protocol", "sent_at", "sequence")}
    if crc_hex(canonical(unsigned)) != frame["integrity"]["value"]:
        raise SendError("CRC_MISMATCH", "integrity does not match envelope")
    line = canonical(frame) + b"\n"
    if len(line) > MAX_FRAME_BYTES:
        raise SendError("FRAME_OVERSIZED", "encoded frame exceeds 65536 bytes")
    return line


def sequence_is_newer(candidate: int, current: int) -> bool:
    distance = (candidate - current) & MAX_SEQUENCE
    return 0 < distance < HALF_RANGE


class SequenceStore:
    """Atomic per-alias next-sequence persistence."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def load_next(self) -> int:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise SendError("SENDER_STATE_MISSING",
                            f"no sequence state at {self.path}; use --init-alias")
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise SendError("SENDER_STATE_CORRUPT", f"sequence state corrupt: {self.path}")
        if not isinstance(raw, dict) or "next" not in raw:
            raise SendError("SENDER_STATE_CORRUPT", f"sequence state corrupt: {self.path}")
        nxt = raw["next"]
        if not isinstance(nxt, int) or isinstance(nxt, bool) or not 0 <= nxt <= MAX_SEQUENCE:
            raise SendError("SENDER_STATE_CORRUPT", f"sequence state corrupt: {self.path}")
        return nxt

    def save_next(self, nxt: int) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps({"next": nxt}, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def init_alias(self, receiver_empty_ack: bool) -> int:
        if self.path.exists():
            raise SendError("SENDER_STATE_EXISTS",
                            "alias already provisioned; refusing to re-init")
        if not receiver_empty_ack:
            raise SendError("RECEIVER_STATE_UNCONFIRMED",
                            "initial creation requires confirming the receiver is empty")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.save_next(1)
        return 1

    def reserve(self) -> int:
        nxt = self.load_next()
        self.save_next((nxt + 1) & MAX_SEQUENCE)
        return nxt


def send_serial(line: bytes, port: str) -> int:
    try:
        import serial
    except ImportError:
        raise SendError("SERIAL_BACKEND_UNAVAILABLE",
                        "install the owner-approved serial backend")
    ser = serial.Serial(port=port, baudrate=115200, bytesize=8,
                        parity="N", stopbits=1, xonxoff=False,
                        rtscts=False, dsrdtr=False, timeout=1)
    try:
        written = ser.write(line)
    finally:
        ser.close()
    if written != len(line):
        raise SendError("SERIAL_WRITE_INCOMPLETE", f"wrote {written} of {len(line)}")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--sent-at", required=True)
    parser.add_argument("--alias", default="usb-meter")
    parser.add_argument("--state-dir", type=Path, default=Path("out/pc_sender"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--raw-log", type=Path, default=None)
    parser.add_argument("--report-output", type=Path, default=None)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--port", default=None)
    parser.add_argument("--init-alias", action="store_true")
    parser.add_argument("--receiver-empty-ack", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.port and not args.send:
            raise SendError("PORT_REQUIRES_SEND", "--port is accepted only with --send")
        if args.send and not args.port:
            raise SendError("PORT_REQUIRED", "--send requires an explicit --port")
        try:
            payload = json.loads(args.payload.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SendError("PAYLOAD_INVALID", str(exc))
        store = SequenceStore(args.state_dir / f"{args.alias}.seq.json")
        if args.init_alias:
            seq = store.init_alias(args.receiver_empty_ack)
            # The provisioning frame consumes the first number.
            store.save_next((seq + 1) & MAX_SEQUENCE)
        else:
            seq = store.reserve()  # consumed even if the write below fails
        frame = build_frame(payload, seq, args.sent_at)
        line = encode_frame(frame)
        outcome = {"mode": "dry_run", "status": "rendered",
                   "sequence": seq, "bytes": len(line),
                   "frame_sha256": __import__("hashlib").sha256(line).hexdigest(),
                   "device_accessed": False}
        if args.output is not None:
            args.output.write_bytes(line)
            outcome["output_path"] = args.output.as_posix()
        if args.raw_log is not None:
            args.raw_log.parent.mkdir(parents=True, exist_ok=True)
            with open(args.raw_log, "ab") as handle:
                handle.write(line)
            outcome["raw_log"] = args.raw_log.as_posix()
        if args.send:
            written = send_serial(line, args.port)
            outcome.update(mode="serial", status="sent",
                           bytes_written=written, device_accessed=True)
        text = json.dumps(outcome, ensure_ascii=False, sort_keys=True)
        if args.report_output is not None:
            args.report_output.write_text(text + "\n", encoding="utf-8")
        print(text, file=sys.stderr)
        return 0
    except SendError as exc:
        text = json.dumps({"status": "rejected", "error_code": exc.code,
                           "message": str(exc)})
        if args.report_output is not None:
            args.report_output.write_text(text + "\n", encoding="utf-8")
        print(text, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
