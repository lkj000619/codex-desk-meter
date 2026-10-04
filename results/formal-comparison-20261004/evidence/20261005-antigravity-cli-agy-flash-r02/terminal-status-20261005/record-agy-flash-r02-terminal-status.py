"""Preserve terminal bytes and record status; no candidate edits or hardware access."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path.cwd()
BASE = Path('C:/meter-operator-20261004')
RUN = Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
CO = RUN / 'checkout'
PREV = Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
LEDGER = PREV.parent / 'ledgers' / (PREV.name + '.json')
OUT = RUN / 'operator-observation'
PUBLIC = ROOT / 'results/formal-comparison-20261004/evidence' / RUN.name / 'terminal-status-20261005'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def copy(p, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)

sys.path.insert(0, str(BASE / 'scripts'))
import benchmark
from agy_pilot_environment import paths_for, owner_path

m = read(RUN / 'run-manifest.json')
ledger = read(LEDGER)
assert m['operator']['status'] == 'completed' and m['execution']['ended_at']
assert digest(RUN / 'run-manifest.json') == ledger['runs'][-1]['terminal_manifest_sha256']
assert not ledger['runs'][-1]['reviewed']
assert not OUT.exists() and not PUBLIC.exists()
processes = json.loads(subprocess.check_output(['powershell', '-NoProfile', '-Command',
    'ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^agy(\\.exe)?$|^opencode(\\.exe)?$" } | Select-Object ProcessId,Name,CommandLine)'], text=True))
assert not processes
scope = read(RUN / 'operator-launch-preflight/scope-exit.json')
gemini = Path.home() / '.gemini'
actual = {k: digest(p) if p.is_file() else None for k, p in paths_for(gemini).items()}
assert actual == scope['before_sha256'] == scope['after_sha256']
assert not owner_path(gemini).exists()
benchmark.verify_agent_inputs(RUN, m)
OUT.mkdir()
for p in [RUN / 'run-manifest.json', LEDGER, RUN / 'stdout.jsonl', RUN / 'stderr.txt', RUN / 'command-audit.json']:
    copy(p, OUT / 'terminal-originals' / p.name)

old_freeze = read(PREV / 'operator-source-freeze.json')
snapshots = {'sources': {}, 'artifacts': {}}
for name in old_freeze['artifacts']:
    p = CO / name
    assert p.is_file(), name
    dest = OUT / 'artifact-snapshot' / name
    copy(p, dest)
    snapshots['artifacts'][name] = {'sha256': digest(p), 'bytes': p.stat().st_size, 'path': dest.relative_to(RUN).as_posix()}
fixed = set(read(RUN / 'candidate-inputs.json')['files'])
for p in CO.rglob('*'):
    rel = p.relative_to(CO)
    if not p.is_file() or any(x in {'.git', '.benchmark-inputs', 'build', 'build-host', '__pycache__'} for x in rel.parts):
        continue
    if rel.as_posix() in fixed:
        continue
    dest = OUT / 'source-snapshot' / rel
    copy(p, dest)
    snapshots['sources'][rel.as_posix()] = {'sha256': digest(p), 'bytes': p.stat().st_size, 'path': dest.relative_to(RUN).as_posix()}
save(OUT / 'terminal-byte-snapshots.json', snapshots)

cache_paths = ['build-host/CTestTestfile.cmake', 'build-host/CMakeCache.txt', 'build-host/build.ninja',
               'build-host/link_evidence.txt', 'build-host/evaluation-output.json',
               'build-host/Testing/Temporary/LastTest.log', 'build/project_description.json']
for name in cache_paths:
    p = CO / name
    if p.is_file():
        copy(p, OUT / 'build-path-observation' / name)
ctest = (CO / 'build-host/CTestTestfile.cmake').read_text(encoding='utf-8')
previous_changes = subprocess.check_output(['git', 'status', '--porcelain'], cwd=PREV / 'checkout', text=True).splitlines()
previous_artifact_checks = {name: digest(PREV / 'checkout' / name) == meta['sha256'] for name, meta in old_freeze['artifacts'].items()}
assert all(previous_artifact_checks.values())
result = read(CO / m['outputs']['structured_result'])
status = {
    'checked_at': datetime.now(timezone.utc).isoformat(), 'run_id': RUN.name,
    'terminal_status': m['operator']['status'], 'execution': m['execution'], 'measurement': m['measurement'],
    'original_terminal_manifest_sha256': digest(RUN / 'run-manifest.json'), 'original_ledger_sha256': digest(LEDGER),
    'candidate_processes_remaining': processes, 'global_files_restored_independently_verified': True,
    'immutable_common_input_files_verified': 57,
    'candidate_result_submission_present': True,
    'candidate_selection_document_present': (CO / m['outputs']['selection_document']).is_file(),
    'candidate_hardware_status': result['hardware']['status'], 'candidate_product_pass': result['product_pass'],
    'operator_hardware_evaluation_started': False, 'source_git_freeze_status': 'pending',
    'operator_source_edits': False, 'operator_firmware_rebuild': False,
    'native_reported_python_test_count': 6, 'native_result_validator_report': 'VALID',
    'native_reported_c_test_count': 4,
    'c_test_provenance_issue': {
        'ctest_testfile_points_to_previous_run_executables': PREV.name in ctest,
        'current_ctest_success_validates_current_implementation': False,
        'previous_checkout_changes': previous_changes,
        'previous_frozen_firmware_and_config_bytes_unchanged': previous_artifact_checks,
        'previous_raw_snapshots_bundle_and_final_package_preserved': True,
        'scope': 'The final r02 CTest configuration explicitly executes r01 binaries. Candidate edited cache/build.ninja paths but did not regenerate this test file. Full policy and artifact provenance review remains pending.'
    },
    'policy_status': 'pending_terminal_review', 'rm_review': 'pending_operator_evaluation',
    'remaining_followup_seconds': max(0, 7200 - m['measurement']['wall_clock_seconds']),
    'remaining_followup_rounds': 2,
    'restart_instruction': 'Do not repeat r02. Preserve and Git-freeze terminal implementation, audit policy/build/test provenance, independently validate submitted result and fixtures, then perform operator hardware evaluation.'
}
assert status['c_test_provenance_issue']['ctest_testfile_points_to_previous_run_executables']
save(OUT / 'terminal-status.json', status)
for p in (OUT / 'terminal-originals').iterdir():
    copy(p, PUBLIC / 'terminal-originals' / p.name)
for p in (OUT / 'build-path-observation').rglob('*'):
    if p.is_file():
        copy(p, PUBLIC / 'build-path-observation' / p.relative_to(OUT / 'build-path-observation'))
copy(OUT / 'terminal-status.json', PUBLIC / 'terminal-status.json')
copy(OUT / 'terminal-byte-snapshots.json', PUBLIC / 'terminal-byte-snapshots.json')
copy(RUN / 'operator-launch-preflight/scope-exit.json', PUBLIC / 'scope-exit.json')
for name in (m['outputs']['structured_result'], m['outputs']['selection_document']):
    copy(CO / name, PUBLIC / 'candidate-submissions' / name)
copy(Path(__file__), PUBLIC / Path(__file__).name)
inventory = {p.relative_to(PUBLIC).as_posix(): {'sha256': digest(p), 'bytes': p.stat().st_size}
             for p in PUBLIC.rglob('*') if p.is_file()}
save(PUBLIC / 'inventory.json', inventory)

p = ROOT / 'results/formal-comparison-20261004/progress.json'
progress = read(p)
progress.update({
    'checked_at': status['checked_at'], 'state': 'agy_flash_followup_1_terminal_awaiting_evaluation',
    'product_executions_completed': 4, 'ended_at': m['execution']['ended_at'],
    'elapsed_seconds': m['measurement']['wall_clock_seconds'], 'tokens': m['measurement']['tokens'],
    'candidate_terminal_status_observed': 'completed', 'ongoing_usage_not_terminal': False,
    'candidate_current_phase': 'Final result and selection submitted; terminal bytes preserved. Git freeze, policy/build provenance review and operator hardware evaluation pending.',
    'current_native_scope': 'Original global settings/instructions/hooks restored and independently hash-verified; owner absent.',
    'candidate_result_submission': 'present', 'candidate_selection_document_submission': 'present',
    'terminal_snapshot': PUBLIC.relative_to(ROOT).as_posix(), 'last_event_count': len((RUN / 'stdout.jsonl').read_text(encoding='utf-8').splitlines()),
    'native_tool_events_observed': m['measurement']['tool_calls'],
    'remaining_current_series_followup_seconds': status['remaining_followup_seconds'],
    'remaining_current_series_followup_rounds': 2,
    'c_test_provenance_issue': status['c_test_provenance_issue'],
    'rm_review': 'awaiting_operator_evaluation', 'restart_instruction': status['restart_instruction']
})
save(p, progress)
assert digest(RUN / 'run-manifest.json') == status['original_terminal_manifest_sha256']
assert digest(LEDGER) == status['original_ledger_sha256']
print(json.dumps({'terminal_status': status['terminal_status'], 'public_snapshot_files': len(inventory),
    'raw_source_files_preserved': len(snapshots['sources']), 'artifact_and_config_files_preserved': len(snapshots['artifacts']),
    'terminal_and_ledger_unchanged': True, 'current_c_tests_use_previous_run_binaries': True,
    'remaining_followup_seconds': status['remaining_followup_seconds']}))
