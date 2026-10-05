"""Verify the failed initial Pro attempt from the independent archive only."""
from pathlib import Path
import json
import subprocess
import sys
import zipfile

PACK = Path('C:/meter-run-packages-20261005/agy-pro-r01-final-v2')
REST = Path('C:/meter-run-restores-20261005/agy-pro-r01-final-v2')
FROZEN = Path('C:/meter-run-restores-20261005/agy-pro-r01-final-v2-frozen-operator')
FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(REST / 'operator/operator-baseline.zip') as z:
    for info in z.infolist():
        target = FROZEN / info.filename
        assert target.resolve().is_relative_to(FROZEN.resolve()) and not info.is_dir()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(info))
sys.path.insert(0, str(FROZEN / 'scripts'))
from benchmark_support import digest, read, save, validate_schema, validate_operator, verify_evidence
from benchmark import verify_agent_inputs, validate_preflight_receipt
from policy_review import review_eligibility
from evidence_package import verify_report_dependencies

expected = read(PACK.parent / 'agy-pro-r01-final-v2-create.json')['package_manifest_sha256']
assert digest((PACK / 'package-manifest.json').read_bytes()) == expected
inventory = read(PACK / 'package-manifest.json')
assert len(inventory['files']) == read(PACK.parent / 'agy-pro-r01-final-v2-create.json')['files']
assert {p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()} == set(inventory['files']) | {'package-manifest.json'}
for name, meta in inventory['files'].items():
    data = (PACK / name).read_bytes()
    assert len(data) == meta['bytes'] and digest(data) == meta['sha256']
    if name.startswith(('operator/', 'checkout/')):
        restored_name = 'operator/raw-run-manifest.json' if name == 'operator/run-manifest.json' else name
        assert (REST / restored_name).read_bytes() == data
OP = REST / 'operator'
CO = REST / 'checkout'
m = read(OP / 'run-manifest.json')
original = read(OP / 'operator-observation/terminal-originals/run-manifest.json')
ledger = read(OP / 'comparison-ledger.json')
validate_schema(m, 'run-manifest.schema.json')
validate_operator(m)
verify_evidence(m, OP)
verify_agent_inputs(OP, m)
verify_report_dependencies(m, OP)
validate_preflight_receipt(read(OP / 'execution-preflight.json'), m, read(OP / 'profile.json'), OP / 'preflight-evidence')
eligible, status, reason = review_eligibility(m, OP / 'run-manifest.json')
assert eligible and status == 'eligible'
assert original['measurement'] == m['measurement']
assert {k: v for k, v in original['execution'].items() if k != 'worktree'} == {k: v for k, v in m['execution'].items() if k != 'worktree'}
assert len(ledger['runs']) == 1 and ledger['runs'][0]['reviewed']
assert digest((OP / 'operator-observation/terminal-originals/run-manifest.json').read_bytes()) == ledger['runs'][0]['terminal_manifest_sha256']
assert original['operator']['status'] == m['operator']['status'] == 'environment_failed'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CO, text=True).strip() == m['outputs']['implementation_commit'] == 'ba5609db6fbf6392166586e50341c6e14a26112f'
assert subprocess.check_output(['git', 'remote'], cwd=CO, text=True).strip() == ''
assert not (CO / m['outputs']['structured_result']).exists()
assert not (CO / m['outputs']['selection_document']).exists()
assert not (CO / 'firmware').exists() and not (CO / 'pc').exists()
rm = {k: v['status'] for k, v in read(OP / 'reference-review.json')['items'].items()}
assert rm == {'RM1': 'fail', 'RM2': 'not_run', 'RM3': 'not_run', 'RM4': 'not_run', 'RM5': 'not_run'}
assert read(OP / 'operator-review-finalization.json')['rm_review_applied_once']
audit = dict(read(REST / 'restore-report.json'), frozen_operator_validators_used=True,
    original_run_or_checkout_path_used=False, inventory_bytes_verified=True, immutable_input_files_verified=57,
    original_terminal_and_cost_preserved=True, candidate_implementation_files=0, candidate_firmware_artifacts=0,
    candidate_result_submission='missing', candidate_selection_document_submission='missing',
    rm_review_completed=True, rm_items=rm, reference_status='fail', product_pass=False,
    remaining_followup_seconds=7200, remaining_followup_rounds=3, board_slot_released=True,
    hardware_upload='not_run_no_firmware', global_native_scope_restored=True)
assert audit['result_valid'] is False
save(REST / 'frozen-validator-audit.json', audit)
print(json.dumps(audit))
