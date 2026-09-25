"""Render the offline fixture-to-frame host pipeline or use an explicit send boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from host_device_pipeline import (
    DEFAULT_SENT_AT,
    FixtureFileAdapter,
    FixtureRegistry,
    PipelineError,
    SerialBridge,
    build_frame,
    open_owner_serial,
)


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_FIXTURE_ROOT = (ROOT / "experiments" / "fixtures" / "providers").resolve()


def resolve_provider_fixture(path: Path) -> Path:
    """Resolve a CLI fixture only within the repository provider-fixture root."""

    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve()
    if not resolved.is_relative_to(PROVIDER_FIXTURE_ROOT):
        raise PipelineError("FIXTURE_PATH_UNSAFE", "--fixture must stay under experiments/fixtures/providers")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        action="append",
        type=Path,
        help="repository-relative provider fixture; repeat to build a selected registry",
    )
    parser.add_argument("--reference-time", default="2026-09-10T00:04:59Z")
    parser.add_argument("--sent-at", default=DEFAULT_SENT_AT)
    parser.add_argument("--sequence", type=int, default=1)
    parser.add_argument("--output", type=Path, help="write the newline-delimited frame to this file")
    parser.add_argument("--report-output", type=Path, help="write the machine-readable outcome JSON to this file")
    parser.add_argument("--dry-run", action="store_true", help="render only; this is the default boundary")
    parser.add_argument("--send", action="store_true", help="request a real serial send; requires --port")
    parser.add_argument("--port", help="explicit serial port required with --send")
    args = parser.parse_args(argv)

    try:
        if args.port and not args.send:
            raise PipelineError("PORT_REQUIRES_SEND", "--port is accepted only with explicit --send")
        if args.send and not args.port:
            raise PipelineError("PORT_REQUIRED", "--send requires an explicit --port")
        if args.fixture:
            adapters = [
                FixtureFileAdapter(path.stem, resolve_provider_fixture(path), PROVIDER_FIXTURE_ROOT)
                for path in args.fixture
            ]
            registry = FixtureRegistry(adapters, reference_time=args.reference_time)
        else:
            registry = FixtureRegistry.with_defaults(ROOT, reference_time=args.reference_time)
        collected = registry.collect()
        frame = build_frame(collected.payload, sequence=args.sequence, sent_at=args.sent_at)
        bridge = SerialBridge()
        if args.send:
            # Real serial access is deliberately only reachable through --send + --port.
            outcome = bridge.send(frame, args.port, serial_factory=open_owner_serial)
        else:
            outcome = bridge.render(frame, args.output)
            if args.output is None:
                sys.stdout.buffer.write(outcome.line)
        report = {
            "mode": outcome.mode,
            "status": outcome.status,
            "bytes_written": outcome.bytes_written,
            "frame_sha256": outcome.frame_sha256,
            "device_accessed": outcome.device_accessed,
            "output_path": outcome.output_path,
            "collection_failures": collected.failures,
        }
        report_line = json.dumps(report, ensure_ascii=False, sort_keys=True)
        if args.report_output is not None:
            args.report_output.write_text(report_line + "\n", encoding="utf-8")
        print(report_line, file=sys.stderr)
        return 0
    except PipelineError as error:
        report_line = json.dumps({"status": "rejected", "error_code": error.code, "message": error.message})
        if args.report_output is not None:
            args.report_output.write_text(report_line + "\n", encoding="utf-8")
        print(report_line, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
