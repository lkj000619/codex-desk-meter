"""Check the new layout package with validators extracted from its frozen ZIP."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

restored = Path('C:/meter-run-restores-20261005/opencode-muse-r01-layout-fixed')
package = Path('C:/meter-run-packages-20261005/opencode-muse-r01-layout-fixed')
source = Path('C:/meter-run-restores-20261005/frozen-operator-source')
source.mkdir(exist_ok=False)
with zipfile.ZipFile(restored / 'operator/operator-baseline.zip') as archive:
    archive.extractall(source)
sys.path.insert(0, str(source / 'scripts'))
from benchmark_support import digest, read, save, validate_operator, validate_schema, verify_evidence
from benchmark import verify_agent_inputs, _check_e2e_manifest_join, _load_e2e_validator
from evidence_package import verify_report_dependencies
from policy_review import review_eligibility
from reference_inputs import validate_reference

inventory = read(package / 'package-manifest.json')
assert digest((package / 'package-manifest.json').read_bytes()) == 'c4f845c4a887a91379e293810824f16dda3e8f590d27b45048baa87ad4a854f0'
for name, metadata in inventory['files'].items():
    original = package / name
    assert original.stat().st_size == metadata['bytes']
    assert digest(original.read_bytes()) == metadata['sha256']
    if name.startswith(('operator/', 'checkout/')):
        target_name = 'operator/raw-run-manifest.json' if name == 'operator/run-manifest.json' else name
        assert digest((restored / target_name).read_bytes()) == metadata['sha256']
manifest = read(restored / 'operator/run-manifest.json')
validate_schema(manifest, 'run-manifest.schema.json')
validate_operator(manifest)
verify_evidence(manifest, restored / 'operator')
verify_report_dependencies(manifest, restored / 'operator')
verify_agent_inputs(restored / 'operator', manifest)
validate_reference(restored / 'operator/reference/reference-inputs.json')
checkout = restored / 'checkout'
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
assert commit == inventory['implementation_commit']
result = read(checkout / inventory['result'])
evaluation = read(checkout / inventory['evaluation_manifest'])
_check_e2e_manifest_join(evaluation, manifest, result)
_load_e2e_validator().validate_result(result, manifest=evaluation, evidence_root=checkout, manifest_root=checkout)
eligible, status, reason = review_eligibility(manifest, restored / 'operator/run-manifest.json')
assert eligible is False and status == 'invalid_for_comparison'
artifacts = {name: digest((checkout / name).read_bytes()) for name in inventory['artifact_paths']}
assert artifacts['firmware/build/cdm_meter.bin'] == 'f91ff86ea8c80ab5ec03f47948259d7de96bd87e0384ceb3d427eb52d0e72dd9'
report = read(restored / 'restore-report.json')
report.update(frozen_operator_validators_used=True,
              frozen_operator_scripts_root=str(source / 'scripts'),
              immutable_input_files_verified=len(read(restored / 'operator/candidate-inputs.json')['files']),
              artifact_sha256=artifacts,
              sdkconfig_sha256=digest((checkout / 'firmware/sdkconfig').read_bytes()),
              inventory_bytes_verified=True,
              original_run_path_used=False,
              product_pass=result['product_pass'])
save(restored / 'frozen-validator-audit.json', report)
print(json.dumps(report, ensure_ascii=False, indent=2))
