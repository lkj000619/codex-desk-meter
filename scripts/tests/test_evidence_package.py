import importlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import read, save


class EvidencePackageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("evidence_package"), "independent evidence package missing")
        self.package = importlib.import_module("evidence_package")
        self.temp = tempfile.TemporaryDirectory(prefix="meter-package-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "run"
        checkout = self.run / "checkout"
        checkout.mkdir(parents=True)
        result = read(ROOT / "experiments/examples/end-to-end-result.example.json")
        manifest = read(ROOT / "experiments/examples/run-manifest.example.json")
        evaluation = read(ROOT / "experiments/examples/end-to-end-manifest.example.json")
        manifest.update(run_id=result["run_id"], experiment_id=result["experiment_id"])
        manifest["operator"].update(phase="benchmark", status="completed", repetition=1, evidence={})
        manifest["execution"].update(worktree=str(checkout), base_commit=result["baseline"]["commit"])
        manifest["outputs"].update(structured_result=f"results/{result['run_id']}/end-to-end-result.json",
                                   selection_document=f"docs/agent-runs/{result['run_id']}/hardware-feature-selection.md",
                                   evaluation_manifest=f"results/{result['run_id']}/e2e-evaluation-manifest.json")
        for relative in self.package.result_evidence_paths(result) + [result["manifest"]["path"]]:
            source = ROOT / relative
            target = checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (checkout / ".gitignore").write_text("logs/\n*.bin\n", encoding="utf-8")
        (checkout / "logs").mkdir()
        (checkout / "logs/frame.bin").write_bytes(b"ignored frame evidence\n")
        result["feature_results"]["F1"]["evidence"].append("logs/frame.bin")
        self.result_path = checkout / manifest["outputs"]["structured_result"]
        self.result_path.parent.mkdir(parents=True, exist_ok=True)
        save(self.result_path, result)
        save(self.run / "e2e-evaluation-manifest.json", evaluation)
        subprocess.run(["git", "init", str(checkout)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(checkout), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(checkout), "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "frozen"], check=True, capture_output=True)
        commit = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        manifest["outputs"]["implementation_commit"] = commit
        save(self.run / "run-manifest.json", manifest)
        self.path = self.root / "package"

    def test_restores_ignored_frame_evidence_without_original_checkout(self):
        self.package.create_package(self.run, self.path)
        (self.run / "checkout").rename(self.run / "unavailable-original")
        restored = self.package.restore_package(self.path, self.root / "restored")
        self.assertTrue(restored["result_valid"])
        portable = read(self.root / "restored/operator/run-manifest.json")
        self.assertEqual(Path(portable["execution"]["worktree"]), self.root / "restored/checkout")
        self.assertEqual((self.root / "restored/checkout/logs/frame.bin").read_bytes(), b"ignored frame evidence\n")

    def test_missing_evidence_and_modified_package_are_rejected(self):
        (self.run / "checkout/logs/frame.bin").unlink()
        with self.assertRaisesRegex(ValueError, "evidence|missing"):
            self.package.create_package(self.run, self.path)
        (self.run / "checkout/logs/frame.bin").write_bytes(b"restored ignored evidence")
        self.package.create_package(self.run, self.path)
        manifest = read(self.path / "package-manifest.json")
        target = self.path / next(name for name in manifest["files"] if name.endswith("frame.bin"))
        target.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "hash"):
            self.package.restore_package(self.path, self.root / "restored")

    def test_package_path_escape_is_rejected_before_restore_creates_files(self):
        self.package.create_package(self.run, self.path)
        manifest = read(self.path / "package-manifest.json")
        manifest["files"]["../escape.txt"] = {"sha256": "a" * 64, "bytes": 1}
        save(self.path / "package-manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "path"):
            self.package.restore_package(self.path, self.root / "restored")
        self.assertFalse((self.root / "restored").exists())
