# Host-to-device `cdm/1` contract

This is maintainer-owned, offline pre-experiment infrastructure. It is a host
simulation and conformance oracle; it is not candidate firmware, a benchmark
run, or evidence of ESP32/LCD behavior.

## Frame and integrity

Each frame is a UTF-8 JSON object validated by
[`cdm-frame.schema.json`](../../experiments/schema/cdm-frame.schema.json):

```json
{
  "protocol": "cdm/1",
  "sequence": 1,
  "sent_at": "2026-09-10T00:00:00Z",
  "payload": {
    "usage": [],
    "global_resets": []
  },
  "integrity": {
    "algorithm": "crc32",
    "value": "BE8028D7"
  }
}
```

The canonical bytes are UTF-8 JSON with sorted object keys, no insignificant
whitespace, `ensure_ascii=false`, and no NaN/Infinity values. The CRC32 input is
the canonical envelope with `integrity` removed; the result is an uppercase
eight-hex-digit value. The encoded frame is one JSON object followed by exactly
one `\n` byte, with a maximum total line size of 65,536 bytes.

`sequence` is an unsigned 32-bit counter. A candidate is newer when
`0 < (candidate - current) mod 2^32 < 2^31`; this accepts `0` after
`4,294,967,295` and rejects duplicates, older values, and the ambiguous
half-range. Unsupported protocol versions, malformed JSON, invalid UTF-8,
truncation, extra newlines, non-canonical JSON, schema failures, oversized lines,
and CRC mismatch are rejection classes with stable pipeline error codes. A valid
frame must use the exact canonical JSON bytes before its one trailing newline;
CRLF and pretty-printed variants are rejected.

The baseline has no device ACK or retry protocol. A host write receipt from the
fake/loopback sink is not a device ACK; adding device ACK/retry requires a new
specified and tested contract.

## Fixture registry and receiver model

`FixtureRegistry` reads only repository provider fixtures and normalizes global-reset
inputs separately from provider `UsageSnapshot` values. Codex, Claude Code,
Gemini CLI, and Claude-on-Orca examples use the same adapter interface. A
single adapter failure becomes an error value and failure record while other
adapters continue; unsupported, unavailable, error, and stale statuses do not
abort collection.

`ReferenceReceiver` is the host-only conformance model. It validates frame
schema and CRC, applies sequence ordering, retains the last good payload after
bad input, marks state stale at age 300 seconds relative to the supplied
reference time, preserves provider-local error snapshots, and clears stale state
on the next accepted frame. It is explicitly not firmware evidence.

## Serial safety boundary and evidence

`run-host-device-pipeline.py` defaults to dry-run and performs no device access.
The `--send` path requires an explicit `--port` and an injected owner-approved
serial backend; tests use `LoopbackSerial` only. No test opens COM3, flashes or
resets a board, builds firmware, contacts a provider, or reads credentials.

The E2E examples classify this work as host simulation/reference-model-only:
F1/F2 may use host fixture evidence, F3 is `host_simulated`, F4 is
`reference_model_only`, I3/I4 remain `not_run`, and `product_pass` remains false.
Evidence records are repository-relative and include reproducible SHA-256 values;
they must not be relabeled as serial-device receipt or hardware evidence.
