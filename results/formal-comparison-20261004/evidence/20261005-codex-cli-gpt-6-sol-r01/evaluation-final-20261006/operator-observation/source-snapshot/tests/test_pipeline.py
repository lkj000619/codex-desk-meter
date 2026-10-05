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
    print("PC canonical fixture frame -> production C receiver -> recovery: PASS")


if __name__ == "__main__":
    main(sys.argv[1])
