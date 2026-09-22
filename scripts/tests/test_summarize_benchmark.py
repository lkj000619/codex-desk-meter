import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_summary():
    spec = importlib.util.spec_from_file_location("summarize_benchmark", SCRIPTS / "summarize-benchmark.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


summary = load_summary()


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class SummaryTests(unittest.TestCase):
    def test_group_aggregation_reports_ratio_median_range_and_minimum(self):
        base_manifest = read("experiments/examples/run-manifest.example.json")
        base_manifest["experiment_id"] = "version-2-end-to-end-v1"
        base_manifest["agent"].update(provider="example", product="example-cli", interface="cli", model="same-model", reasoning="fixed")
        records = []
        for index, (seconds, tokens, success) in enumerate(((10, 100, True), (30, 300, False)), start=1):
            manifest = copy.deepcopy(base_manifest)
            manifest["run_id"] = f"20260911-example-cli-same-model-r0{index}"
            manifest["operator"]["phase"] = "benchmark"
            result = {
                "build": {"status": "pass"},
                "hardware": {"status": "pass"},
                "product_pass": success,
            }
            records.append({
                "manifest": manifest,
                "result": result,
                "group": "example/example-cli/cli/same-model/fixed",
                "success": success,
                "seconds": seconds,
                "tokens": tokens,
            })
        rendered = summary.render_summary(records, {"pilot": 1, "incomplete": 0, "invalid": 2}, min_repetitions=3)
        self.assertIn("| 2 | no | 0.500 | 20 | 10–30 | 200 | 100–300 |", rendered)
        self.assertIn("Pilot: 1; incomplete: 0; invalid or semantically unjoined: 2; duplicate path/run identity: 0.", rendered)
        self.assertIn("Pilot runs are excluded", rendered)

    def test_collect_records_excludes_pilot_and_invalid_result(self):
        with tempfile.TemporaryDirectory(prefix="meter-summary-") as folder:
            root = Path(folder)
            manifest_path = root / "run-manifest.json"
            result_path = root / "end-to-end-result.json"
            eval_path = root / "e2e-evaluation-manifest.json"
            manifest = read("experiments/examples/run-manifest.example.json")
            manifest.update(run_id="20260911-e2e-contract-example-r01", experiment_id="version-2-end-to-end-v1")
            manifest["agent"].update(provider="example", product="example-cli", interface="cli", model="example-model", reasoning="fixed")
            manifest["execution"].update(
                base_commit="34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f",
                worktree=str(ROOT),
            )
            manifest["operator"].update(phase="benchmark", status="completed", repetition=1, exit_code=0)
            manifest["outputs"].update(
                selection_document="docs/agent-runs/20260911-e2e-contract-example-r01/hardware-feature-selection.md",
                structured_result="results/20260911-e2e-contract-example-r01/end-to-end-result.json",
                evaluation_manifest="results/20260911-e2e-contract-example-r01/e2e-evaluation-manifest.json",
            )
            manifest["measurement"].update(wall_clock_seconds=600)
            manifest["measurement"]["tokens"].update(input=50, output=25, total=75, provider_total=90)
            result = read("experiments/examples/end-to-end-result.example.json")
            evaluation_manifest = read("experiments/examples/end-to-end-manifest.example.json")
            run_id = manifest["run_id"]
            result.update(result_id=run_id, run_id=run_id, manifest_id=run_id,
                          baseline_id=manifest["baseline_id"])
            result["manifest"].update(id=run_id, baseline_id=manifest["baseline_id"])
            result["baseline"].update(id=manifest["baseline_id"], ref=manifest["baseline_ref"],
                                       commit=manifest["execution"]["base_commit"])
            evaluation_manifest.update(manifest_id=run_id, run_id=run_id, result_id=run_id,
                                       baseline_id=manifest["baseline_id"], baseline_ref=manifest["baseline_ref"])
            evaluation_manifest["execution"]["base_commit"] = manifest["execution"]["base_commit"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result_path.write_text(json.dumps(result), encoding="utf-8")
            eval_path.write_text(json.dumps(evaluation_manifest), encoding="utf-8")
            records, excluded = summary.collect_records([manifest_path])
            self.assertEqual(len(records), 1)
            self.assertEqual(excluded["pilot"], 0)

            pilot = copy.deepcopy(manifest)
            pilot["run_id"] = "20260911-e2e-contract-example-r02"
            pilot["operator"]["phase"] = "pilot"
            pilot_path = root / "pilot-run-manifest.json"
            pilot_path.write_text(json.dumps(pilot), encoding="utf-8")
            records, excluded = summary.collect_records([manifest_path, pilot_path])
            self.assertEqual(len(records), 1)
            self.assertEqual(excluded["pilot"], 1)

            result_path.write_text("{\"not\": \"a valid result\"}", encoding="utf-8")
            records, excluded = summary.collect_records([manifest_path])
            self.assertEqual(records, [])
            self.assertEqual(excluded["invalid"], 1)

    def test_collect_records_rejects_e2e_operator_evaluation_result_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="meter-summary-identity-") as folder:
            root = Path(folder)
            manifest_path = root / "run-manifest.json"
            result_path = root / "end-to-end-result.json"
            eval_path = root / "e2e-evaluation-manifest.json"
            manifest = read("experiments/examples/run-manifest.example.json")
            manifest.update(run_id="20260911-e2e-contract-identity-r01", experiment_id="version-2-end-to-end-v1")
            manifest["agent"].update(provider="example", product="example-cli", interface="cli", model="example-model", reasoning="fixed")
            manifest["execution"].update(
                base_commit="34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f",
                worktree=str(ROOT),
            )
            manifest["operator"].update(phase="benchmark", status="completed", repetition=1, exit_code=0)
            manifest["outputs"].update(
                selection_document="docs/agent-runs/20260911-e2e-contract-identity-r01/hardware-feature-selection.md",
                structured_result="results/20260911-e2e-contract-identity-r01/end-to-end-result.json",
                evaluation_manifest="results/20260911-e2e-contract-identity-r01/e2e-evaluation-manifest.json",
            )
            manifest["measurement"].update(wall_clock_seconds=600)
            manifest["measurement"]["tokens"].update(input=50, output=25, total=75, provider_total=90)
            result = read("experiments/examples/end-to-end-result.example.json")
            evaluation_manifest = read("experiments/examples/end-to-end-manifest.example.json")
            run_id = manifest["run_id"]
            result.update(result_id=run_id, run_id=run_id, manifest_id=run_id,
                          baseline_id=manifest["baseline_id"])
            result["manifest"].update(id=run_id, baseline_id=manifest["baseline_id"])
            result["baseline"].update(id=manifest["baseline_id"], ref=manifest["baseline_ref"],
                                       commit=manifest["execution"]["base_commit"])
            evaluation_manifest.update(manifest_id=run_id, run_id=run_id, result_id=run_id,
                                       baseline_id=manifest["baseline_id"], baseline_ref=manifest["baseline_ref"])
            evaluation_manifest["execution"]["base_commit"] = manifest["execution"]["base_commit"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result_path.write_text(json.dumps(result), encoding="utf-8")
            eval_path.write_text(json.dumps(evaluation_manifest), encoding="utf-8")

            for field, value in (("base_commit", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
                                 ("baseline_id", "benchmark-v2-baseline-other")):
                changed = copy.deepcopy(manifest)
                if field == "base_commit":
                    changed["execution"][field] = value
                else:
                    changed[field] = value
                manifest_path.write_text(json.dumps(changed), encoding="utf-8")
                records, excluded = summary.collect_records([manifest_path])
                self.assertEqual(records, [], field)
                self.assertEqual(excluded["invalid"], 1, field)

    def test_collect_records_deduplicates_paths_and_run_identity(self):
        with tempfile.TemporaryDirectory(prefix="meter-summary-duplicates-") as folder:
            root = Path(folder)
            manifest_path = root / "run-manifest.json"
            result_path = root / "end-to-end-result.json"
            eval_path = root / "e2e-evaluation-manifest.json"
            manifest = read("experiments/examples/run-manifest.example.json")
            manifest.update(run_id="20260911-e2e-contract-duplicate-r01", experiment_id="version-2-end-to-end-v1")
            manifest["agent"].update(provider="example", product="example-cli", interface="cli", model="example-model", reasoning="fixed")
            manifest["execution"].update(
                base_commit="34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f",
                worktree=str(ROOT),
            )
            manifest["operator"].update(phase="benchmark", status="completed", repetition=1, exit_code=0)
            manifest["outputs"].update(
                selection_document="docs/agent-runs/20260911-e2e-contract-duplicate-r01/hardware-feature-selection.md",
                structured_result="results/20260911-e2e-contract-duplicate-r01/end-to-end-result.json",
                evaluation_manifest="results/20260911-e2e-contract-duplicate-r01/e2e-evaluation-manifest.json",
            )
            manifest["measurement"].update(wall_clock_seconds=600)
            manifest["measurement"]["tokens"].update(input=50, output=25, total=75, provider_total=90)
            result = read("experiments/examples/end-to-end-result.example.json")
            evaluation_manifest = read("experiments/examples/end-to-end-manifest.example.json")
            run_id = manifest["run_id"]
            result.update(result_id=run_id, run_id=run_id, manifest_id=run_id,
                          baseline_id=manifest["baseline_id"])
            result["manifest"].update(id=run_id, baseline_id=manifest["baseline_id"])
            result["baseline"].update(id=manifest["baseline_id"], ref=manifest["baseline_ref"],
                                       commit=manifest["execution"]["base_commit"])
            evaluation_manifest.update(manifest_id=run_id, run_id=run_id, result_id=run_id,
                                       baseline_id=manifest["baseline_id"], baseline_ref=manifest["baseline_ref"])
            evaluation_manifest["execution"]["base_commit"] = manifest["execution"]["base_commit"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result_path.write_text(json.dumps(result), encoding="utf-8")
            eval_path.write_text(json.dumps(evaluation_manifest), encoding="utf-8")

            copied_path = root / "copied-run-manifest.json"
            copied_path.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
            records, excluded = summary.collect_records([manifest_path, manifest_path, copied_path, copied_path])
            self.assertEqual(len(records), 1)
            self.assertEqual(excluded["duplicate"], 3)
            rendered = summary.render_summary(records, excluded, min_repetitions=3)
            self.assertIn("| 1 | no |", rendered)

    def test_comparison_groups_include_experiment_baseline_and_input_bundle(self):
        with tempfile.TemporaryDirectory(prefix="meter-summary-groups-") as folder:
            root = Path(folder)
            paths = []
            for index, (experiment_id, baseline_id, input_bundle) in enumerate(
                (("version-2-hardware-autonomy-v1", "baseline-a", "a" * 64),
                 ("version-2-hardware-autonomy-v1", "baseline-a", "b" * 64),
                 ("version-2-hardware-autonomy-v1", "baseline-b", "a" * 64),
                 ("version-2-end-to-end-v1", "baseline-a", "a" * 64)),
                start=1,
            ):
                run_id = f"20260911-example-cli-example-model-r{index:02d}"
                manifest = read("experiments/examples/run-manifest.example.json")
                manifest.update(run_id=run_id, experiment_id=experiment_id, baseline_id=baseline_id, baseline_ref=baseline_id)
                manifest["execution"].update(
                    input_bundle_sha256=input_bundle,
                    worktree=str(ROOT),
                )
                manifest["operator"].update(phase="benchmark", status="completed", repetition=index, exit_code=0)
                manifest["outputs"]["selection_document"] = f"docs/agent-runs/{run_id}/hardware-feature-selection.md"
                result_name = "end-to-end-result.json" if experiment_id == "version-2-end-to-end-v1" else "hardware-feature.json"
                manifest["outputs"]["structured_result"] = f"results/{run_id}/{result_name}"
                if experiment_id == "version-2-end-to-end-v1":
                    manifest["outputs"]["evaluation_manifest"] = f"results/{run_id}/e2e-evaluation-manifest.json"
                manifest["measurement"].update(wall_clock_seconds=600)
                manifest["measurement"]["tokens"].update(input=50, output=25, total=75)
                run_dir = root / f"run-{index}"
                run_dir.mkdir()
                manifest_path = run_dir / "run-manifest.json"
                result_path = run_dir / result_name
                if experiment_id == "version-2-end-to-end-v1":
                    result = read("experiments/examples/end-to-end-result.example.json")
                    evaluation_manifest = read("experiments/examples/end-to-end-manifest.example.json")
                    result.update(result_id=run_id, run_id=run_id, manifest_id=run_id, baseline_id=baseline_id)
                    result["manifest"].update(id=run_id, baseline_id=baseline_id)
                    result["baseline"].update(id=baseline_id, ref=baseline_id, commit=manifest["execution"]["base_commit"])
                    evaluation_manifest.update(manifest_id=run_id, run_id=run_id, result_id=run_id,
                                               baseline_id=baseline_id, baseline_ref=baseline_id)
                    evaluation_manifest["execution"]["base_commit"] = manifest["execution"]["base_commit"]
                    (run_dir / "e2e-evaluation-manifest.json").write_text(json.dumps(evaluation_manifest), encoding="utf-8")
                else:
                    result = read("experiments/examples/hardware-feature-result.example.json")
                    result["run_id"] = run_id
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                result_path.write_text(json.dumps(result), encoding="utf-8")
                paths.append(manifest_path)

            records, excluded = summary.collect_records(paths)
            self.assertEqual(len(records), 4)
            self.assertEqual(len({record["group_key"] for record in records}), 4)
            rendered = summary.render_summary(records, excluded, min_repetitions=1)
            self.assertEqual(rendered.count("| 1 | yes |"), 4)

    def test_collect_records_excludes_malformed_manifests_without_crashing(self):
        with tempfile.TemporaryDirectory(prefix="meter-summary-malformed-") as folder:
            root = Path(folder)
            empty = root / "empty.json"
            malformed = root / "malformed.json"
            empty.write_text("{}", encoding="utf-8")
            malformed.write_text("{", encoding="utf-8")
            records, excluded = summary.collect_records([empty, malformed])
            self.assertEqual(records, [])
            self.assertEqual(excluded["invalid"], 2)


if __name__ == "__main__":
    unittest.main()
