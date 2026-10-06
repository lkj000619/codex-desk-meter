"""Persistent sequence reservation and optional USB serial sender."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import timezone
from pathlib import Path
from typing import Any, Callable

from .pipeline import CollectionError, build_frame, encode_frame, timestamp, utc_now


class SequenceStateError(RuntimeError):
    pass


def default_state_path() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "CodexDeskMeter" / "sender-state.json"
    return Path.home() / ".local" / "state" / "codex-desk-meter" / "sender-state.json"


def _safe_alias(alias: str) -> str:
    if not isinstance(alias, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", alias):
        raise SequenceStateError("device alias must be 1-64 ASCII letters, digits, dot, underscore, or dash")
    return alias


@contextmanager
def _exclusive_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


class SequenceStore:
    """Stores last reserved sequence before any serial write is attempted."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or default_state_path())
        self.lock_path = self.path.with_name(self.path.name + ".lock")

    def _read(self) -> dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise
        except (OSError, json.JSONDecodeError) as exc:
            raise SequenceStateError(f"sender state is unreadable; sending is stopped: {exc}") from exc
        if not isinstance(value, dict) or set(value) != {"schema_version", "devices"} or value["schema_version"] != 1 or not isinstance(value["devices"], dict):
            raise SequenceStateError("sender state is damaged; sending is stopped")
        for alias, sequence in value["devices"].items():
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", alias) or isinstance(sequence, bool) or not isinstance(sequence, int) or not 0 <= sequence <= 0xFFFFFFFF:
                raise SequenceStateError("sender state is damaged; sending is stopped")
        return value

    def _write_atomic(self, value: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
            try:
                directory_fd = os.open(self.path.parent, os.O_RDONLY)
            except OSError:
                directory_fd = None
            if directory_fd is not None:
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    def reserve(self, alias: str, initialize_empty_receiver: bool = False) -> int:
        alias = _safe_alias(alias)
        with _exclusive_lock(self.lock_path):
            try:
                value = self._read()
            except FileNotFoundError:
                if not initialize_empty_receiver:
                    raise SequenceStateError("sender state is missing; confirm an empty receiver before explicit initialization")
                value = {"schema_version": 1, "devices": {}}
            devices = value["devices"]
            if alias not in devices:
                if not initialize_empty_receiver:
                    raise SequenceStateError(f"device alias {alias!r} is not initialized; confirm its receiver is empty")
                sequence = 0
            else:
                sequence = (devices[alias] + 1) & 0xFFFFFFFF
            devices[alias] = sequence
            self._write_atomic(value)
            return sequence


def _pyserial_factory(port: str, **kwargs: Any):
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("pyserial is required only when USB serial sending is enabled") from exc
    return serial.Serial(port=port, **kwargs)


def send_payload(payload: dict[str, Any], port: str, device_alias: str,
                 state_path: Path | str | None = None,
                 raw_log_path: Path | str | None = None,
                 initialize_empty_receiver: bool = False,
                 serial_factory: Callable[..., Any] = _pyserial_factory,
                 wait_fn: Callable[[float], None] = time.sleep,
                 clock_fn: Callable[[], float] = time.monotonic,
                 open_timeout_seconds: float = 5.0,
                 sent_at: str | None = None,
                 capture_device_logs_seconds: float = 0.0,
                 device_log_path: Path | str | None = None) -> dict[str, Any]:
    if not isinstance(port, str) or not port.strip():
        raise ValueError("an operator-selected COM port is required")
    if (isinstance(capture_device_logs_seconds, bool) or
            not isinstance(capture_device_logs_seconds, (int, float)) or
            not math.isfinite(capture_device_logs_seconds) or
            capture_device_logs_seconds < 0 or capture_device_logs_seconds > 10):
        raise ValueError("device log capture window must be between 0 and 10 seconds")
    alias = _safe_alias(device_alias)
    store = SequenceStore(state_path)
    with _exclusive_lock(store.path.with_name(store.path.name + ".device-" + alias + ".lock")):
        sequence = store.reserve(alias, initialize_empty_receiver=initialize_empty_receiver)
        frame_sent_at = sent_at or timestamp(utc_now().astimezone(timezone.utc))
        frame = build_frame(payload, sequence, frame_sent_at)
        line = encode_frame(frame)
        raw_path = Path(raw_log_path) if raw_log_path else store.path.with_name("raw-cdm-frames.log")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with raw_path.open("ab") as raw_log:
            raw_log.write(line)
            raw_log.flush()
            os.fsync(raw_log.fileno())
        deadline = clock_fn() + open_timeout_seconds
        serial = None
        last_error: Exception | None = None
        while serial is None:
            try:
                serial = serial_factory(port, baudrate=115200, bytesize=8, parity="N", stopbits=1,
                                        timeout=0.2, write_timeout=2, xonxoff=False, rtscts=False, dsrdtr=False)
            except Exception as exc:
                last_error = exc
                remaining = deadline - clock_fn()
                if remaining <= 0:
                    raise RuntimeError(f"USB serial did not become available within {open_timeout_seconds:g}s; reserved sequence {sequence} remains consumed: {last_error}") from exc
                wait_fn(min(1.0, remaining))
        try:
            written = serial.write(line)
            if written != len(line):
                raise RuntimeError(f"incomplete serial write {written}/{len(line)} bytes; sequence {sequence} remains consumed")
            device_log_lines: list[str] = []
            device_log_error: str | None = None
            deadline = clock_fn() + max(0.0, capture_device_logs_seconds)
            readline = getattr(serial, "readline", None)
            while readline and clock_fn() < deadline:
                try:
                    raw = readline()
                except Exception as exc:
                    device_log_error = f"serial diagnostic read failed: {exc}"
                    break
                if raw:
                    device_log_lines.append(raw.decode("utf-8", errors="replace").rstrip("\r\n"))
            if device_log_path is not None:
                device_path = Path(device_log_path)
                try:
                    device_path.parent.mkdir(parents=True, exist_ok=True)
                    with device_path.open("a", encoding="utf-8", newline="\n") as device_log:
                        for log_line in device_log_lines:
                            device_log.write(log_line + "\n")
                        device_log.flush()
                        os.fsync(device_log.fileno())
                except OSError as exc:
                    device_log_error = f"device diagnostic log write failed: {exc}"
        finally:
            close = getattr(serial, "close", None)
            if close:
                close()
        return {
            "status": "written", "sequence": sequence, "bytes": len(line),
            "raw_log": raw_path.as_posix(), "device_ack": False,
            "device_log_lines": device_log_lines,
            "device_log": Path(device_log_path).as_posix() if device_log_path else None,
            "device_log_error": device_log_error,
            "message": "host write completed; cdm/1 defines no device ACK",
        }
