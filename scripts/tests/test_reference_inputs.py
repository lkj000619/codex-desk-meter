from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import digest, read, save
from reference_inputs import recover_reference, validate_reference


class ReferenceInputTests(unittest.TestCase):
    def test_fixture_recovery_is_portable_and_rejects_changed_logged_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            repo, evidence = root / "repo", root / "evidence"
            repo.mkdir()
            evidence.mkdir()
            reference = ROOT / "experiments/reference/codex-7923f96"
            spec = read(reference / "reference-inputs.json")
            fixtures = []
            for name in spec["fixture_files"]:
                target = repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((reference / name).read_bytes())
                fixtures.append({"path": name, "sha256": digest(target.read_bytes()), "raw_utf8": target.read_text(encoding="utf-8")})
            (repo / "scripts").mkdir()
            (repo / "scripts/cdm_collector.py").write_text("# test-only collector source\n", encoding="utf-8")
            for args in (("init",), ("add", "."), ("-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "test fixture")):
                subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
            records, observations = [], []
            for wire in (reference / "expected-frames.jsonl").read_bytes().splitlines(keepends=True):
                frame = json.loads(wire)
                records.append({"frame_json": wire.decode("utf-8").rstrip("\n"), "frame_sha256": digest(wire),
                                "bytes_written": len(wire), "fixture_inputs": fixtures})
                observations.append({"sequence": frame["sequence"], "frame_sha256": digest(wire),
                                     "device_response": f"CDM_RX sequence={frame['sequence']} result=0\n"})
            log = evidence / "sent-frames.jsonl"
            log.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
            save(evidence / "device-check.json", {"frames": observations})
            (evidence / "check-device.py").write_text("# test-only sender harness\n", encoding="utf-8")
            result = recover_reference(repo, evidence, "HEAD", root / "reference")
            validate_reference(root / "reference/reference-inputs.json")
            self.assertEqual(result["required_ids"], ["RM1", "RM2", "RM3", "RM4", "RM5"])
            self.assertEqual(result["display_values"]["five-hour"]["percent_remaining"], 58)
            self.assertEqual(result["display_values"]["weekly"]["percent_remaining"], 82)
            self.assertEqual(result["source_status"], "stale")
            self.assertEqual(result["monotonic_offsets"], [0, 5])
            self.assertEqual(result["receiver_accepted_sequences"], [0, 1])
            records[0]["fixture_inputs"][0]["raw_utf8"] += " "
            log.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fixture disagrees"):
                recover_reference(repo, evidence, "HEAD", root / "rejected")
