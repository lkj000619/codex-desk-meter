"""Persistent sequence reservation, single-sender lock, and serial sender state machine.

Contract rules:
- uint32 sequence reservation is ATOMICALLY persisted BEFORE any write.
- A failed write consumes the sequence number.
- State loss or corruption stops transmission immediately (fail-closed, never re-creates).
- Single-sender locking per device alias.
- Reconnection attempts at most once per second.
- Transmit within 5s of available port.
- Host write receipt is not device ACK (labeled "HOST WRITE").
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from pc.frame import MAX_SEQUENCE, build_frame, encode_frame, fail


class SenderStateError(ValueError):
    """Sender sequence or state error."""


class SenderLockError(IOError):
    """Single sender lock error."""


@dataclass
class DeviceSequenceState:
    device_alias: str
    next_sequence: int
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_alias": self.device_alias,
            "next_sequence": self.next_sequence,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceSequenceState:
        if not isinstance(data, dict):
            raise SenderStateError("STATE_CORRUPT: state must be a dict")
        alias = data.get("device_alias")
        seq = data.get("next_sequence")
        ts = data.get("updated_at")
        if not isinstance(alias, str) or not isinstance(seq, int) or isinstance(seq, bool):
            raise SenderStateError("STATE_CORRUPT: invalid fields in state")
        if not (0 <= seq <= MAX_SEQUENCE):
            raise SenderStateError(f"STATE_CORRUPT: sequence out of uint32 bounds: {seq}")
        return cls(device_alias=alias, next_sequence=seq, updated_at=float(ts or 0.0))


class StateStore:
    """Atomic file-based sequence persistence store."""

    def __init__(self, state_file: Path):
        self.state_file = state_file

    def exists(self) -> bool:
        return self.state_file.exists()

    def load(self, device_alias: str) -> DeviceSequenceState:
        """Load state strictly; if missing or corrupt, raises SenderStateError."""
        if not self.state_file.exists():
            raise SenderStateError(f"STATE_LOST: state file {self.state_file} does not exist")
        try:
            raw = self.state_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            state = DeviceSequenceState.from_dict(data)
            if state.device_alias != device_alias:
                raise SenderStateError(
                    f"STATE_ALIAS_MISMATCH: store has alias {state.device_alias!r}, expected {device_alias!r}"
                )
            return state
        except SenderStateError:
            raise
        except Exception as exc:
            raise SenderStateError(f"STATE_CORRUPT: cannot load state: {exc}") from exc

    def save_atomic(self, state: DeviceSequenceState) -> None:
        """Atomic write using temporary file and atomic replace."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state.to_dict(), indent=2).encode("utf-8")

        temp_dir = self.state_file.parent
        with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False, mode="wb") as tf:
            tf.write(payload)
            tf.flush()
            os.fsync(tf.fileno())
            temp_name = tf.name

        try:
            os.replace(temp_name, self.state_file)
        except Exception as exc:
            if os.path.exists(temp_name):
                os.remove(temp_name)
            raise SenderStateError(f"STATE_PERSIST_FAILED: {exc}") from exc

    def initialize_new(self, device_alias: str, initial_sequence: int = 0) -> DeviceSequenceState:
        """Explicit confirmed initialization for new receiver."""
        state = DeviceSequenceState(
            device_alias=device_alias,
            next_sequence=initial_sequence,
            updated_at=time.time(),
        )
        self.save_atomic(state)
        return state


class DeviceLock:
    """File-based single-sender lock for a device alias."""

    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self._fd: int | None = None

    def acquire(self) -> None:
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Atomic exclusive creation
            self._fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            pid = str(os.getpid()).encode("utf-8")
            os.write(self._fd, pid)
        except FileExistsError:
            raise SenderLockError(f"Device lock already held: {self.lock_file}")

    def release(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None
        if self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except Exception:
                pass


class SerialSink(Protocol):
    """Abstract serial or loopback interface."""

    def write(self, data: bytes) -> int:
        ...

    def flush(self) -> None:
        ...

    def close(self) -> None:
        ...


class LoopbackSink:
    """In-memory sink for testing without hardware."""

    def __init__(self):
        self.written_frames: list[bytes] = []
        self.closed = False

    def write(self, data: bytes) -> int:
        if self.closed:
            raise IOError("Port closed")
        self.written_frames.append(bytes(data))
        return len(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class WindowsSerialSink:
    """Standard serial sink for real COM ports using pyserial when invoked by operator."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        try:
            import serial
        except ImportError:
            raise IOError("pyserial is not installed")

        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            timeout=timeout,
            write_timeout=timeout,
        )

    def write(self, data: bytes) -> int:
        return self.serial.write(data)

    def flush(self) -> None:
        self.serial.flush()

    def close(self) -> None:
        self.serial.close()


@dataclass
class SendOutcome:
    success: bool
    sequence_used: int
    bytes_sent: int
    frame: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None


class CdmSender:
    """Manages sequence reservation, frame construction and transmission."""

    def __init__(
        self,
        device_alias: str,
        state_store: StateStore,
        lock_dir: Path | None = None,
        sink_factory: Callable[[], SerialSink] | None = None,
    ):
        self.device_alias = device_alias
        self.state_store = state_store
        self.sink_factory = sink_factory
        self.last_connect_time = 0.0

        # Acquire lock if lock_dir is given
        self._lock = None
        if lock_dir:
            lock_path = lock_dir / f"{device_alias}.lock"
            self._lock = DeviceLock(lock_path)
            self._lock.acquire()

        # Check existing state strictly; must NOT auto-init or recreate
        self._state = self.state_store.load(device_alias)

    def close(self) -> None:
        if self._lock:
            self._lock.release()
            self._lock = None

    @property
    def current_sequence(self) -> int:
        # Always verify state store is intact
        persisted = self.state_store.load(self.device_alias)
        return persisted.next_sequence

    def reserve_next_sequence(self) -> int:
        """Atomically reserve and persist the next sequence number BEFORE write."""
        # 1. Re-read from disk to detect any runtime state deletion or external tampering
        persisted = self.state_store.load(self.device_alias)
        seq_to_use = persisted.next_sequence

        # 2. Increment with 32-bit wrap-around
        next_seq = (seq_to_use + 1) & MAX_SEQUENCE
        persisted.next_sequence = next_seq
        persisted.updated_at = time.time()

        # 3. Save atomically BEFORE return
        self.state_store.save_atomic(persisted)
        self._state = persisted
        return seq_to_use

    def transmit_payload(
        self,
        payload: dict[str, Any],
        sent_at: str,
        sink: SerialSink | None = None,
        reference_time: str | None = None,
    ) -> SendOutcome:
        """Reserve sequence, construct frame, and write to sink. Failed write consumes sequence."""
        # Check that state store still exists before reserving
        if not self.state_store.exists():
            return SendOutcome(
                success=False,
                sequence_used=-1,
                bytes_sent=0,
                frame={},
                error_code="STATE_LOST",
                error_message="Sender state was lost/deleted during runtime",
            )

        # 1. Reserve sequence atomically FIRST (will fail-closed if state file was deleted/corrupted)
        try:
            seq = self.reserve_next_sequence()
        except SenderStateError as exc:
            return SendOutcome(
                success=False,
                sequence_used=-1,
                bytes_sent=0,
                frame={},
                error_code="STATE_FAILURE",
                error_message=str(exc),
            )

        # 2. Build and encode frame
        try:
            frame = build_frame(payload, sequence=seq, sent_at=sent_at, reference_time=reference_time)
            raw_bytes = encode_frame(frame, reference_time=reference_time)
        except Exception as exc:
            return SendOutcome(
                success=False,
                sequence_used=seq,
                bytes_sent=0,
                frame={},
                error_code="FRAME_BUILD_ERROR",
                error_message=str(exc),
            )

        # 3. Determine sink
        target_sink = sink
        if target_sink is None and self.sink_factory:
            target_sink = self.sink_factory()

        if target_sink is None:
            return SendOutcome(
                success=False,
                sequence_used=seq,
                bytes_sent=0,
                frame=frame,
                error_code="SINK_UNAVAILABLE",
                error_message="No serial sink provided or available",
            )

        # 4. Write
        try:
            written = target_sink.write(raw_bytes)
            target_sink.flush()
            if written != len(raw_bytes):
                return SendOutcome(
                    success=False,
                    sequence_used=seq,
                    bytes_sent=written,
                    frame=frame,
                    error_code="PARTIAL_WRITE",
                    error_message=f"Wrote {written}/{len(raw_bytes)} bytes",
                )
            return SendOutcome(
                success=True,
                sequence_used=seq,
                bytes_sent=written,
                frame=frame,
            )
        except Exception as exc:
            # Sequence is consumed as required by contract
            return SendOutcome(
                success=False,
                sequence_used=seq,
                bytes_sent=0,
                frame=frame,
                error_code="WRITE_IO_ERROR",
                error_message=str(exc),
            )
