"""Start the next authorized independent series using the unchanged frozen runner."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

BASE = Path('C:/meter-operator-20261004')
RUN = Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-pro-r01')
CO = RUN / 'checkout'
PREV = Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
RENEWAL = Path('C:/meter-preflight-20261005/renewal')
SOURCE_RECEIPT = RENEWAL / 'agy-pro-receipt.json'
RECEIPT = RENEWAL / 'agy-pro-launch-20261005-receipt.json'
PRIVATE = Path('C:/meter-private-preflight-20261005/agy-pro-initial-scope')
OUT = RUN / 'operator-launch-preflight'
sys.path.insert(0, str(BASE / 'scripts'))
import benchmark
from benchmark_support import KST, digest, read, save, verify_evidence
from operator_baseline import verify
from agy_pilot_environment import scoped_environment, verify_scoped_environment, paths_for, run_child, _OWNER_ENV

assert datetime.now(KST).strftime('%Y%m%d') == '20261005'
audit = read(Path('C:/meter-run-restores-20261005/agy-flash-r02-final/frozen-validator-audit.json'))
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['frozen_operator_validators_used']
assert audit['files_verified'] == 501 and audit['board_slot_released']
previous = read(PREV / 'run-manifest.json')
assert previous['execution']['ended_at'] and previous['operator']['status'] == 'completed'
assert read(PREV / 'operator-observation/observation-finalization.json')['serial_closed']
assert benchmark.git('rev-parse', 'HEAD', cwd=BASE) == '272875140d1998d458e26fdb2f6deab5e5d8f7b5'
assert not benchmark.git('status', '--porcelain', cwd=BASE)
m = read(RUN / 'run-manifest.json')
profile = read(RUN / 'profile.json')
ledger_path = Path(m['operator']['comparison']['ledger'])
ledger = read(ledger_path)
assert m['operator']['status'] == 'prepared' and m['execution']['started_at'] is None
assert m['execution']['timeout_seconds'] == 7200 and profile['model'] == 'gemini-3.1-pro-high'
assert len(ledger['runs']) == 1 and ledger['runs'][0]['status'] == 'prepared' and ledger['runs'][0]['round'] == 0
assert benchmark.git('status', '--porcelain', cwd=CO) == ''
assert benchmark.git('rev-parse', 'HEAD', cwd=CO) == m['operator']['local_base_commit']
assert benchmark.git('rev-list', '--count', 'HEAD', cwd=CO) == '1'
benchmark.verify_agent_inputs(RUN, m)
verify_evidence(m, RUN)
verify(m, RUN)
receipt_source = read(SOURCE_RECEIPT)
benchmark.validate_preflight_receipt(receipt_source, m, profile, RENEWAL)
assert digest(SOURCE_RECEIPT.read_bytes()) == '57cb59f9ef2454fe1467df6b12a076ec20ffc2d3689a068c481b8805c0987d74'

env = os.environ.copy()
env['AGY_CLI_DISABLE_AUTO_UPDATE'] = 'true'
version = subprocess.check_output(profile['version_argv'], env=env, text=True, encoding='utf-8', timeout=30).strip()
assert version == profile['agent_version']
idf = subprocess.check_output([sys.executable, 'C:/Espressif/v5.3.2/esp-idf/tools/idf.py', '--version'], text=True, timeout=30).strip()
assert idf == 'ESP-IDF v5.3.2'
tools = {name: shutil.which(name) for name in ('cmake', 'ninja', 'git', 'xtensa-esp32s3-elf-gcc')}
assert all(tools.values()), tools
other = subprocess.check_output(['powershell', '-NoProfile', '-Command',
    '@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^agy(\\.exe)?$|^opencode(\\.exe)?$" }).Count'], text=True).strip()
assert other == '0', 'Another benchmark-capable native process is active.'
gemini = Path.home() / '.gemini'
paths = paths_for(gemini)
before = {key: digest(path.read_bytes()) if path.is_file() else None for key, path in paths.items()}
assert before == read(PREV / 'operator-launch-preflight/scope-exit.json')['after_sha256']
assert not (gemini / '.agy-pilot-owner.json').exists()
OUT.mkdir(exist_ok=False)
decision = {
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'user_instruction': '다음 모델 ㄱㄱ',
    'authorized_next_model': 'gemini-3.1-pro-high',
    'authorized_run_id': RUN.name,
    'previous_run_id': PREV.name,
    'previous_final_package_manifest_sha256': audit['package_manifest_sha256'],
    'previous_reviewed_manifest_sha256': digest((PREV / 'run-manifest.json').read_bytes()),
    'previous_ledger_sha256': digest(Path(previous['operator']['comparison']['ledger']).read_bytes()),
    'previous_followup_seconds_retained': audit['remaining_followup_seconds'],
    'previous_followup_rounds_retained': audit['remaining_followup_rounds'],
    'scope': 'User resumes progression to AGY Pro only. Flash additional rounds remain deferred; preserve all previous immutable hold, evaluation and cost records. No previous implementation or result is provided to the independent candidate.'
}
assert not (RUN / 'operator-next-model-decision.json').exists()
save(RUN / 'operator-next-model-decision.json', decision)
policy = BASE / 'experiments/config/agy-pilot-permissions.json'
result = None
try:
    with scoped_environment(gemini, policy, PRIVATE, workspace=CO) as identity:
        scoped = verify_scoped_environment(gemini, policy, workspace=CO)
        for name, args in [('mcp', ['mcp', 'list']), ('plugins', ['plugins', 'list']), ('agents', ['agents']), ('models', ['models'])]:
            p = subprocess.run([profile['version_argv'][0], *args], cwd=CO, env=env, capture_output=True, timeout=60)
            (OUT / (name + '-stdout.txt')).write_bytes(p.stdout)
            (OUT / (name + '-stderr.txt')).write_bytes(p.stderr)
            assert p.returncode == 0, (name, p.returncode)
            if name != 'models':
                assert p.stdout == (RENEWAL / ('current/agy-' + name + '.txt')).read_bytes(), name
        assert profile['model'] in (OUT / 'models-stdout.txt').read_text(encoding='utf-8')
        checked = {
            'checked_at': datetime.now(timezone.utc).isoformat(), 'run_id': RUN.name, 'round': 0,
            'cli_version': version, 'idf_version': idf, 'baseline_commit': m['execution']['base_commit'],
            'candidate_commit': m['operator']['local_base_commit'], 'immutable_input_files_verified': 57,
            'original_capability_receipt_sha256': digest(SOURCE_RECEIPT.read_bytes()),
            'profile_sha256': m['execution']['profile_sha256'], 'input_bundle_sha256': m['execution']['input_bundle_sha256'],
            'scoped_settings_sha256': scoped, 'policy_sha256': identity['policy_sha256'],
            'instructions_absent': True, 'hooks_absent': True, 'global_files_before_sha256': before,
            'mcp_plugins_custom_agents_clear': True, 'model_catalog_selected_id_present': True,
            'model_entitlement_retested': False, 'capability_proof_date': '2026-10-04',
            'read_isolation': 'not_enforced', 'network_mode': 'offline-fixture', 'tools': tools,
            'candidate_hardware_access': False, 'previous_evaluation_and_preservation_complete': True,
            'model_invocations_during_preflight': 0, 'backup_private_outside_repository': str(PRIVATE)
        }
        save(OUT / 'current-checks.json', checked)
        relative = 'current/agy-pro-launch-20261005'
        fresh = RENEWAL / relative
        fresh.mkdir(exist_ok=False)
        receipt = dict(receipt_source, checked_at=checked['checked_at'], launch_run_id=RUN.name)
        receipt['evidence'] = dict(receipt_source['evidence'])
        for p in OUT.iterdir():
            if p.is_file():
                shutil.copy2(p, fresh / p.name)
                receipt['evidence'][relative + '/' + p.name] = digest(p.read_bytes())
        shutil.copy2(RUN / 'operator-next-model-decision.json', fresh / 'operator-next-model-decision.json')
        receipt['evidence'][relative + '/operator-next-model-decision.json'] = digest((fresh / 'operator-next-model-decision.json').read_bytes())
        assert not RECEIPT.exists()
        save(RECEIPT, receipt)
        benchmark.validate_preflight_receipt(receipt, m, profile, RENEWAL)
        print(json.dumps({'launch_preflight': 'passed', 'run_id': RUN.name, 'model': profile['model'],
                          'timeout_seconds': 7200, 'receipt_sha256': digest(RECEIPT.read_bytes())}), flush=True)
        child_env = env.copy()
        child_env[_OWNER_ENV] = identity['lock_token']
        result = run_child([sys.executable, '-B', '-X', 'utf8', str(BASE / 'scripts/benchmark.py'),
                            'run', str(RUN), '--receipt', str(RECEIPT)], child_env)
finally:
    after = {key: digest(path.read_bytes()) if path.is_file() else None for key, path in paths.items()}
    save(OUT / 'scope-exit.json', {'recorded_at': datetime.now(timezone.utc).isoformat(), 'runner_exit_code': result,
         'before_sha256': before, 'after_sha256': after, 'global_files_restored': before == after,
         'owner_journal_present': (gemini / '.agy-pilot-owner.json').exists()})
    print(json.dumps({'scope_exit': 'recorded', 'global_files_restored': before == after}), flush=True)
if result is None:
    raise RuntimeError('Runner did not start; inspect evidence before any retry.')
raise SystemExit(result)
