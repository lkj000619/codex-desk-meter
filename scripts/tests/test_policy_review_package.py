"""Policy review evidence survives independent restoration of every attempt."""
import unittest
import subprocess
from unittest.mock import patch

import test_evidence_package
from benchmark_support import digest, read, save
from policy_review import create_review, review_eligibility


class PolicyReviewPackageTests(unittest.TestCase):
    setUp = test_evidence_package.EvidencePackageTests.setUp

    def test_fixed_input_bytes_survive_git_checkout_line_ending_conversion(self):
        checkout = self.run / "checkout"
        path = self.run / "run-manifest.json"
        manifest = read(path)
        fixed = checkout / "docs/immutable.txt"
        fixed.parent.mkdir(exist_ok=True)
        fixed.write_bytes(b"fixed LF input\n")
        save(self.run / "candidate-inputs.json", {"files": {"docs/immutable.txt": digest(fixed.read_bytes())}})
        save(self.run / "agent-context.json", {})
        inputs = checkout / ".benchmark-inputs"
        inputs.mkdir()
        for source, target in (("candidate-inputs.json", "input-files.json"),
                               ("agent-context.json", "run-context.json"),
                               ("e2e-evaluation-manifest.json", "e2e-evaluation-manifest.json")):
            (inputs / target).write_bytes((self.run / source).read_bytes())
            manifest["operator"]["evidence"][source] = digest((self.run / source).read_bytes())
        subprocess.run(["git", "-C", str(checkout), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(checkout), "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "fixed inputs"], check=True, capture_output=True)
        manifest["outputs"]["implementation_commit"] = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        save(path, manifest)
        packaged = self.package.create_package(self.run, self.path)
        original_git = self.package._git
        def converted_clone(*args, cwd):
            if args[0] == "clone":
                args = ("-c", "core.autocrlf=true", *args)
            return original_git(*args, cwd=cwd)
        with patch.object(self.package, "_git", converted_clone):
            self.package.restore_package(self.path, self.root / "restored", packaged["package_manifest_sha256"])
        self.assertEqual((self.root / "restored/checkout/docs/immutable.txt").read_bytes(), b"fixed LF input\n")

    def prepare_review(self, status="eligible"):
        path = self.run / "run-manifest.json"
        manifest = read(path)
        manifest["operator"]["policy_review_required"] = True
        for name, raw in (("stdout.jsonl", b"events"), ("stderr.txt", b""),
                          ("prompt.txt", b"task"), ("profile.json", b'{"model":"test"}')):
            (self.run / name).write_bytes(raw)
            manifest["operator"]["evidence"][name] = digest(raw)
        manifest["agent"]["configuration_sha256"] = digest(b'{"model":"test"}')
        manifest["execution"]["profile_sha256"] = digest(b'{"model":"test"}')
        save(path, manifest)
        (self.run / "review-notes.txt").write_text("Manual policy findings.", encoding="utf-8")
        decision = {"status": status, "reviewer": "operator", "reason": "Manual policy audit",
                    "user_interventions": 0, "intervention_review": "No external implementation assistance.",
                    "evidence": [{"path": "review-notes.txt", "sha256": digest((self.run / "review-notes.txt").read_bytes())}]}
        create_review(path, decision)

    def test_restoration_preserves_review_and_operator_evidence_without_original_checkout(self):
        self.prepare_review()
        original = (self.run / "policy-review.json").read_bytes()
        packaged = self.package.create_package(self.run, self.path)
        (self.run / "checkout").rename(self.run / "unavailable-original")
        restored = self.root / "restored"
        report = self.package.restore_package(self.path, restored, packaged["package_manifest_sha256"])
        self.assertTrue((restored / "operator/policy-review.json").is_file())
        self.assertEqual((restored / "operator/policy-review.json").read_bytes(), original)
        self.assertEqual((restored / "operator/review-notes.txt").read_bytes(), (self.run / "review-notes.txt").read_bytes())
        path = restored / "operator/run-manifest.json"
        self.assertTrue(review_eligibility(read(path), path)[0])
        self.assertEqual(report["policy_review_status"], "eligible")

    def test_missing_invalid_and_unverified_reviews_do_not_erase_attempt_archives(self):
        for status in ("missing", "invalid_for_comparison", "unverified"):
            with self.subTest(status=status):
                (self.run / "policy-review.json").unlink(missing_ok=True)
                self.prepare_review(status if status != "missing" else "eligible")
                if status == "missing":
                    (self.run / "policy-review.json").unlink()
                package_root = self.root / ("package-" + status)
                self.package.create_package(self.run, package_root)
                report = self.package.restore_package(package_root, self.root / ("restored-" + status))
                self.assertEqual(report.get("policy_review_status"), status)
                self.assertFalse(report["policy_eligible"])
                if (self.run / "policy-review.json").exists():
                    (self.run / "policy-review.json").unlink()

    def test_restore_rechecks_policy_evidence_even_if_outer_inventory_was_rehashed(self):
        self.prepare_review()
        self.package.create_package(self.run, self.path)
        target = self.path / "operator/review-notes.txt"
        self.assertTrue(target.is_file(), "review dependency must enter the package inventory")
        target.write_bytes(b"rewritten after review")
        inventory = read(self.path / "package-manifest.json")
        inventory["files"]["operator/review-notes.txt"] = {"sha256": digest(target.read_bytes()), "bytes": target.stat().st_size}
        save(self.path / "package-manifest.json", inventory)
        with self.assertRaisesRegex(ValueError, "policy review|evidence hash"):
            self.package.restore_package(self.path, self.root / "restored")

    def test_restore_rechecks_immutable_followup_inputs_after_worktree_remap(self):
        manifest_path = self.run / "run-manifest.json"
        manifest = read(manifest_path)
        checkout = self.run / "checkout"
        inputs = checkout / ".benchmark-inputs"
        inputs.mkdir()
        save(self.run / "agent-context.json", {"immutable_files": {".benchmark-inputs/feedback.json": "candidate-feedback.json"}})
        save(self.run / "candidate-feedback.json", {"feedback": "original task feedback"})
        for source, target in (("agent-context.json", "run-context.json"),
                               ("candidate-feedback.json", "feedback.json"),
                               ("e2e-evaluation-manifest.json", "e2e-evaluation-manifest.json")):
            (inputs / target).write_bytes((self.run / source).read_bytes())
            manifest["operator"]["evidence"][source] = digest((self.run / source).read_bytes())
        subprocess.run(["git", "-C", str(checkout), "add", ".benchmark-inputs"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(checkout), "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "input contract"], check=True, capture_output=True)
        manifest["outputs"]["implementation_commit"] = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        save(manifest_path, manifest)
        self.package.create_package(self.run, self.path)
        changed = self.path / "operator/candidate-feedback.json"
        save(changed, {"feedback": "replacement operator feedback"})
        packaged_manifest = self.path / "operator/run-manifest.json"
        manifest = read(packaged_manifest)
        manifest["operator"]["evidence"]["candidate-feedback.json"] = digest(changed.read_bytes())
        save(packaged_manifest, manifest)
        inventory_path = self.path / "package-manifest.json"
        inventory = read(inventory_path)
        for name in ("operator/candidate-feedback.json", "operator/run-manifest.json"):
            item = self.path / name
            inventory["files"][name] = {"sha256": digest(item.read_bytes()), "bytes": item.stat().st_size}
        save(inventory_path, inventory)
        with self.assertRaisesRegex(ValueError, "immutable agent input"):
            self.package.restore_package(self.path, self.root / "restored")


if __name__ == "__main__":
    unittest.main()
