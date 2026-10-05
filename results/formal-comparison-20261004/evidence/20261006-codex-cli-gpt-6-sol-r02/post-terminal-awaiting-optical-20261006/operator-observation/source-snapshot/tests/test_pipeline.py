"""Exercise Python serializer against the linked production C receiver."""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc.desk_meter import collect, frame, timestamp


def main(executable):
    payload, errors = collect(timestamp("2026-09-10T00:04:59Z"))
    assert not errors, errors
    sent = "2026-09-10T00:04:59Z"
    good = frame(7, payload, sent)
    corrupt = bytearray(frame(8, payload, sent))
    corrupt[40] = ord("X") if corrupt[40] != ord("X") else ord("Y")
    lines = [good, frame(1, payload, sent), bytes(corrupt), frame(8, payload, sent)]
    result = subprocess.run([executable], input=b"".join(lines), capture_output=True, check=True)
    output = result.stdout.decode().splitlines()
    assert len(output) == 4, output
    assert output[0].startswith("accepted 7 "), output
    assert output[1].startswith("rejected 7 SEQUENCE_OLD"), output
    assert output[2].startswith("rejected 7 "), output
    assert output[3].startswith("accepted 8 "), output
    reference = timestamp("2026-09-30T18:40:49Z")
    legacy_payload, errors = collect(reference, fixture_paths=["personal-usage.json"])
    assert not errors, errors
    assert [w["percent_remaining"] for w in legacy_payload["usage"][0]["windows"]] == [58, 82]
    common_lines = frame(0, legacy_payload, "2026-09-30T18:40:49Z") + frame(1, legacy_payload, "2026-09-30T18:40:54Z")
    common = subprocess.run([executable], input=common_lines, capture_output=True, check=True)
    accepted = common.stdout.decode().splitlines()
    assert len(accepted) == 2 and accepted[0].startswith("accepted 0 ") and accepted[1].startswith("accepted 1 "), accepted
    supplied = Path(__file__).resolve().parents[1] / ".benchmark-inputs/feedback-evidence/003-sent-frames.jsonl"
    supplied_bytes = supplied.read_bytes()
    assert common_lines == supplied_bytes, "legacy collector bytes differ from the supplied fixed frames"
    observed = subprocess.run([executable], input=supplied_bytes, capture_output=True, check=True)
    observed_lines = observed.stdout.decode().splitlines()
    assert len(observed_lines) == 2 and all(line.startswith(f"accepted {number} ") for number, line in enumerate(observed_lines)), observed_lines
    print("PC canonical fixture frame -> production C receiver -> recovery: PASS")


if __name__ == "__main__":
    main(sys.argv[1])
