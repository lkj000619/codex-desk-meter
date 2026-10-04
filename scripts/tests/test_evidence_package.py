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

    def firmware_artifacts(self, directory="firmware/build", missing=None):
        checkout = self.run / "checkout"
        names = ("meter.bin", "meter.elf", "meter.map",
                 "bootloader/bootloader.bin", "partition_table/partition-table.bin")
        for name in names:
            if name != missing:
                path = checkout / directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((directory + "/" + name).encode("utf-8"))
        return directory + "/meter.bin"

    def claim_firmware_build(self, evidence):
        checkout = self.run / "checkout"
        result = read(self.result_path)
        result["build"].update(status="pass", evidence=[evidence] if isinstance(evidence, str) else evidence, reason=None)
        save(self.result_path, result)
        subprocess.run(["git", "add", "--all"], cwd=checkout, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@localhost",
                        "commit", "-m", "frozen firmware build"], cwd=checkout, check=True, capture_output=True)
        manifest = read(self.run / "run-manifest.json")
        manifest["outputs"]["implementation_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
        save(self.run / "run-manifest.json", manifest)

    def test_restores_artifacts_from_result_build_directory_without_original_checkout(self):
        evidence = self.firmware_artifacts()
        config = self.run / "checkout/firmware/sdkconfig"
        config.write_bytes(b"CONFIG_IDF_TARGET=esp32s3\n")
        self.claim_firmware_build(evidence)
        created = self.package.create_package(self.run, self.path)
        inventory = read(self.path / "package-manifest.json")
        self.assertIn("firmware/build/meter.bin", inventory["artifact_paths"])
        self.assertIn("firmware/build/bootloader/bootloader.bin", inventory["artifact_paths"])
        (self.run / "checkout").rename(self.run / "unavailable-original")
        restored = self.package.restore_package(
            self.path, self.root / "restored", created["package_manifest_sha256"])
        self.assertTrue(restored["result_valid"])
        self.assertEqual((self.root / "restored/checkout/firmware/build/meter.bin").read_bytes(),
                         b"firmware/build/meter.bin")
        self.assertEqual((self.root / "restored/checkout/firmware/build/bootloader/bootloader.bin").read_bytes(),
                         b"firmware/build/bootloader/bootloader.bin")
        self.assertEqual((self.root / "restored/checkout/firmware/sdkconfig").read_bytes(),
                         b"CONFIG_IDF_TARGET=esp32s3\n")

    def test_missing_referenced_build_artifact_cannot_use_an_unrelated_build_directory(self):
        evidence = self.firmware_artifacts(missing="meter.map")
        self.firmware_artifacts("build")
        self.claim_firmware_build(evidence)
        with self.assertRaisesRegex(ValueError, "app/ELF/map/bootloader/partition"):
            self.package.create_package(self.run, self.path)
        self.assertFalse(self.path.exists())

    def test_complete_artifacts_must_come_from_one_referenced_build(self):
        first = self.firmware_artifacts("out/first", missing="meter.map")
        second = self.firmware_artifacts("out/second", missing="bootloader/bootloader.bin")
        self.claim_firmware_build([first, second])
        with self.assertRaisesRegex(ValueError, "app/ELF/map/bootloader/partition"):
            self.package.create_package(self.run, self.path)

    def test_root_build_fallback_preserves_existing_log_evidence(self):
        self.firmware_artifacts("build")
        self.claim_firmware_build("experiments/examples/end-to-end-manifest.example.json")
        created = self.package.create_package(self.run, self.path)
        restored = self.package.restore_package(
            self.path, self.root / "restored", created["package_manifest_sha256"])
        self.assertTrue(restored["result_valid"])
        self.assertEqual((self.root / "restored/checkout/build/meter.bin").read_bytes(), b"build/meter.bin")
