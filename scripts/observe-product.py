"""Replay a production test stimulus offline, or explicitly capture one serial session."""
import argparse
import importlib.util
import json
from pathlib import Path

from product_observation import capture_frames, open_observer_serial, replay_frames
from benchmark_support import digest, read


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True, help="canonical cdm/1 lines")
    parser.add_argument("--reference-time", help="fixture UTC anchor; absent means unknown")
    parser.add_argument("--schedule", type=Path, help="frozen JSON monotonic_offsets for offline replay")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--port")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wait-seconds", type=float, default=5)
    parser.add_argument("--writer-adapter", type=Path, help="operator JSON with module_path/module_sha256/function for the candidate writer")
    parser.add_argument("--receiver-log", type=Path, help="reviewed literal acceptance template and hashed source-review evidence")
    args = parser.parse_args(argv)
    try:
        wires = args.frames.read_bytes().splitlines(keepends=True)
        if not wires:
            raise ValueError("no frames")
        if args.port and not args.send:
            raise ValueError("port requires explicit --send")
        if args.send:
            if not args.port:
                raise ValueError("send requires explicit port")
            writer = None
            if args.writer_adapter:
                adapter = read(args.writer_adapter)
                source = Path(adapter["module_path"]).resolve()
                if digest(source.read_bytes()) != adapter["module_sha256"]:
                    raise ValueError("candidate writer source hash mismatch")
                spec = importlib.util.spec_from_file_location("candidate_observed_writer", source)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                writer = getattr(module, adapter["function"])
            receiver_log = None if args.receiver_log is None else read(args.receiver_log)
            if receiver_log is not None:
                evidence = Path(receiver_log["evidence_path"])
                receiver_log["evidence_path"] = str((args.receiver_log.parent / evidence).resolve())
            report = capture_frames(wires, args.port, open_observer_serial, args.output,
                                    args.wait_seconds, writer, receiver_log)
        else:
            if args.writer_adapter or args.receiver_log:
                raise ValueError("writer adapter and receiver log are only used with explicit send")
            schedule = None if args.schedule is None else read(args.schedule)["monotonic_offsets"]
            report = replay_frames(wires, args.reference_time, monotonic_offsets=schedule)
            with args.output.open("x", encoding="utf-8") as output:
                output.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": report.get("status", "replayed"), "device_accessed": report["device_accessed"], "product_pass": False}))
        return int(report.get("status") == "failed")
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
