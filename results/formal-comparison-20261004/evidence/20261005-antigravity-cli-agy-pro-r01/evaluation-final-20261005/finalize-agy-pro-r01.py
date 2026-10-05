"""Evaluate and preserve the terminated, unimplemented first Pro attempt."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path.cwd()
BASE = Path('C:/meter-operator-20261004')
RUN = Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-pro-r01')
CO = RUN / 'checkout'
OUT = RUN / 'operator-observation'
sys.path.insert(0, str(BASE / 'scripts'))
import benchmark
from benchmark_support import digest, read, save, verify_evidence
from operator_baseline import verify
from agy_pilot_environment import paths_for
from policy_review import create_review, validate_review
from comparison_manager import review_run
from evidence_package import create_package, restore_package

m = read(RUN / 'run-manifest.json')
ledger_path = Path(m['operator']['comparison']['ledger'])
ledger = read(ledger_path)
original_hash = digest((RUN / 'run-manifest.json').read_bytes())
assert original_hash == ledger['runs'][0]['terminal_manifest_sha256']
assert m['operator']['status'] == 'environment_failed' and m['execution']['ended_at']
assert not ledger['runs'][0]['reviewed'] and len(ledger['runs']) == 1
assert benchmark.git('status', '--porcelain', cwd=CO) == ''
assert benchmark.git('rev-parse', 'HEAD', cwd=CO) == m['operator']['local_base_commit']
benchmark.verify_agent_inputs(RUN, m)
verify_evidence(m, RUN)
verify(m, RUN)
assert not (CO / m['outputs']['structured_result']).exists()
assert not (CO / m['outputs']['selection_document']).exists()
assert not (CO / 'firmware').exists() and not (CO / 'pc').exists()
assert not (CO / 'build').exists() and not (CO / 'build-host').exists()
scope = read(RUN / 'operator-launch-preflight/scope-exit.json')
gemini = Path.home() / '.gemini'
actual = {k: digest(p.read_bytes()) if p.is_file() else None for k, p in paths_for(gemini).items()}
assert actual == scope['before_sha256'] == scope['after_sha256'] and scope['global_files_restored']
assert not (gemini / '.agy-pilot-owner.json').exists()
process_count = subprocess.check_output(['powershell', '-NoProfile', '-Command',
    '@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^agy(\\.exe)?$|^opencode(\\.exe)?$" }).Count'], text=True).strip()
assert process_count == '0'
events = [json.loads(line) for line in (RUN / 'stdout.jsonl').read_bytes().splitlines()]
assert len(events) == 30
init = events[0]['init']
assert init['model'] == 'gemini-3.1-pro-high' and init['permission_mode'] == 'request-review'
assert Path(init['cwd']).resolve() == CO.resolve()
steps = [e['step_update'] for e in events if 'step_update' in e]
tool_calls = [s for s in steps if s['step_type'] == 'tool' and s['state'] == 'ACTIVE']
assert len(tool_calls) == 11
reads = [s for s in tool_calls if s['tool_name'] == 'view_file']
assert len(reads) == 10
for s in reads:
    assert Path(s['tool_info']['parameters']['AbsolutePath']).resolve().is_relative_to(CO.resolve())
denied = events[-2]['step_update']
assert denied['step_type'] == 'tool' and denied['state'] == 'ERROR' and denied['tool_name'] == 'run_command'
command = denied['tool_info']['parameters']['CommandLine']
assert command == 'mkdir -p firmware/main pc firmware/components/state_machine scripts tests'
assert 'user denied permission' in denied['tool_info']['error']['message']
assert events[-1]['event'] == 'result' and events[-1]['result']['denied_actions']
OUT.mkdir(exist_ok=False)
originals = OUT / 'terminal-originals'
originals.mkdir()
for p in (RUN / 'run-manifest.json', ledger_path, RUN / 'stdout.jsonl', RUN / 'stderr.txt', RUN / 'command-audit.json'):
    shutil.copy2(p, originals / p.name)
previous_bytes = (ROOT / 'results/formal-comparison-20261004/progress.json').read_bytes()
(RUN / 'previous-progress-at-transition.json').write_bytes(previous_bytes)
terminal = {
    'run_id': RUN.name, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'native_model': init['model'], 'native_permission_mode': init['permission_mode'],
    'native_cwd': init['cwd'], 'native_conversation_id': events[0]['conversation_id'],
    'native_events': 30, 'tool_calls': 11, 'own_checkout_read_calls': 10,
    'denied_command': command, 'denial_raw_line': 29, 'subsequent_tool_calls': 0,
    'terminal_status': m['operator']['status'], 'execution': m['execution'], 'measurement': m['measurement'],
    'original_terminal_manifest_sha256': original_hash, 'original_ledger_sha256': digest(ledger_path.read_bytes()),
    'immutable_input_files_verified': 57, 'candidate_git_changes': [],
    'candidate_result_submission': 'missing', 'candidate_selection_document_submission': 'missing',
    'candidate_implementation_files': 0, 'candidate_firmware_artifacts': 0,
    'build_tests_and_hardware': 'not_run_no_submitted_implementation',
    'global_settings_instructions_hooks_restored_byte_identical': True,
    'owner_journal_present': False, 'native_candidate_processes_remaining': 0,
    'operator_audited_user_interventions': 0, 'operator_product_source_changes': False,
    'board_state': 'Previous frozen Flash r02 retained; no Pro upload or serial access.',
    'scope': 'Actual native invocation ended on its first command denial. Candidate did not implement, submit, or build. Result SUCCESS in the native envelope does not mean product success.'
}
save(OUT / 'terminal-verification.json', terminal)
freeze = {
    'run_id': RUN.name, 'frozen_at': datetime.now(timezone.utc).isoformat(),
    'commit': benchmark.git('rev-parse', 'HEAD', cwd=CO),
    'candidate_branch': benchmark.git('branch', '--show-current', cwd=CO),
    'original_terminal_manifest_sha256': original_hash,
    'candidate_source_changes': False, 'new_product_source_files': 0, 'firmware_artifacts': 0,
    'operator_product_source_modifications': False, 'operator_firmware_rebuild': False
}
save(RUN / 'operator-source-freeze.json', freeze)
notes = {
    'run_id': RUN.name, 'reviewed_at': datetime.now(timezone.utc).isoformat(),
    'raw_stdout_sha256': digest((RUN / 'stdout.jsonl').read_bytes()),
    'raw_stderr_sha256': digest((RUN / 'stderr.txt').read_bytes()),
    'accesses': [s['tool_info']['parameters']['AbsolutePath'] for s in reads],
    'stop_on_denial': {'raw_line': 29, 'step_index': 16, 'command': command, 'later_tool_calls': 0},
    'finding': 'All ten reads were declared candidate inputs within its own checkout. The only shell command was denied and no later assistant or tool action occurred. No serial, flash, online access, earlier candidate source, scope change, retry or operator implementation feedback.',
    'denial_scope': 'Native headless permission matching denied the command. No permission relaxation, alternate tool for the denied action or replacement initial invocation was made.'
}
save(OUT / 'policy-notes.json', notes)
decision = {
    'status': 'eligible', 'reviewer': 'Codex operator',
    'reason': 'All ten native file reads were within its own declared candidate inputs. The first command, mkdir -p firmware/main pc firmware/components/state_machine scripts tests, was denied at raw line 29 and no later tool or assistant action followed. Candidate respected stop-on-denial. Preserve environment_failed, zero implementation, missing submissions and full cost as separate outcomes.',
    'user_interventions': 0,
    'intervention_review': 'Reviewed all 30 events, clean candidate Git status, scoped native inventories and scope-exit restoration. No operator source edits, implementation feedback or hardware access during the candidate.',
    'evidence': [{'path': 'operator-observation/policy-notes.json', 'sha256': digest((OUT / 'policy-notes.json').read_bytes())},
                 {'path': 'operator-observation/terminal-verification.json', 'sha256': digest((OUT / 'terminal-verification.json').read_bytes())}]
}
save(RUN / 'operator-policy-decision.json', decision)
create_review(RUN / 'run-manifest.json', decision)
evidence = [{'path': 'operator-observation/terminal-verification.json', 'sha256': digest((OUT / 'terminal-verification.json').read_bytes())}]
report = {
    'run_id': RUN.name, 'reference_inputs_sha256': m['operator']['comparison']['reference_inputs_sha256'],
    'reviewed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': 'Codex operator',
    'items': {key: {'status': 'fail' if key == 'RM1' else 'not_run', 'evidence': evidence,
                    'reason': 'No submitted implementation or firmware; build prerequisite failed.' if key == 'RM1' else 'Not tested because no implementation or firmware was produced.'}
              for key in ('RM1', 'RM2', 'RM3', 'RM4', 'RM5')},
    'product_pass': False, 'scope': 'No Pro firmware exists to upload or observe. The installed Flash firmware is not evidence for this independent Pro run.'
}
save(RUN / 'operator-reference-review-input.json', report)
review_run(RUN, report)
reviewed = read(RUN / 'run-manifest.json')
assert reviewed['execution'] == m['execution'] and reviewed['measurement'] == m['measurement']
assert validate_review(reviewed, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'
save(RUN / 'operator-review-finalization.json', {
    'run_id': RUN.name, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'rm_review_applied_once': True, 'reference_status': 'fail', 'product_pass': False,
    'remaining_followup_seconds': 7200, 'remaining_followup_rounds': 3,
    'original_terminal_manifest_sha256': original_hash, 'original_cost_preserved': True,
    'candidate_source_unchanged': True, 'board_slot_released': True, 'serial_opened': False
})
PACK = Path('C:/meter-run-packages-20261005/agy-pro-r01-final')
REST = Path('C:/meter-run-restores-20261005/agy-pro-r01-final')
created = create_package(RUN, PACK)
save(PACK.parent / 'agy-pro-r01-final-create.json', created)
restored = restore_package(PACK, REST, created['package_manifest_sha256'])
print(json.dumps({'terminal_status': 'environment_failed', 'seconds': m['measurement']['wall_clock_seconds'],
                  'normalized_tokens': m['measurement']['tokens']['total'], 'policy_status': 'eligible',
                  'rm_items': {key: value['status'] for key, value in report['items'].items()},
                  'frozen_commit': freeze['commit'], 'package': created, 'restore': restored}))
