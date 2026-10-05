"""Publish first-run terminal evidence before an allowed own-source followup."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys

ROOT = Path.cwd()
RUN = Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-pro-r01')
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest

m = read(RUN / 'run-manifest.json')
audit = read(Path('C:/meter-run-restores-20261005/agy-pro-r01-final-v2/frozen-validator-audit.json'))
assert audit['rm_review_completed'] and audit['frozen_operator_validators_used'] and audit['inventory_bytes_verified']
assert m['operator']['status'] == 'environment_failed'
PUBLIC = ROOT / 'results/formal-comparison-20261004/evidence' / RUN.name / 'evaluation-final-20261005'
PUBLIC.mkdir(parents=True, exist_ok=False)
names = ['experiment-launch.json', 'run-manifest.json', 'stdout.jsonl', 'stderr.txt', 'command-audit.json',
         'profile.json', 'prompt.txt', 'candidate-inputs.json', 'agent-context.json', 'execution-preflight.json',
         'operator-next-model-decision.json', 'previous-progress-at-transition.json', 'operator-source-freeze.json', 'operator-package-coverage-correction.json', 'run-manifest-before-package-coverage-correction.json',
         'policy-review.json', 'operator-policy-decision.json', 'operator-reference-review-input.json',
         'reference-review.json', 'operator-review-finalization.json', 'runner-console.txt', 'runner-console-stderr.txt']
names += [p.relative_to(RUN).as_posix() for p in (RUN / 'operator-observation').rglob('*') if p.is_file()]
names += [p.relative_to(RUN).as_posix() for p in (RUN / 'operator-launch-preflight').rglob('*') if p.is_file()]
for name in names:
    dest = PUBLIC / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUN / name, dest)
shutil.copy2(Path(m['operator']['comparison']['ledger']), PUBLIC / 'ledger-reviewed.json')
for src, dest in [
    (Path('C:/meter-run-packages-20261005/agy-pro-r01-final-v2/package-manifest.json'), 'package-manifest.json'),
    (Path('C:/meter-run-packages-20261005/agy-pro-r01-final-v2-create.json'), 'package-create.json'),
    (Path('C:/meter-run-restores-20261005/agy-pro-r01-final-v2/restore-report.json'), 'restore-report.json'),
    (Path('C:/meter-run-restores-20261005/agy-pro-r01-final-v2/frozen-validator-audit.json'), 'restore-audit.json')
]:
    shutil.copy2(src, PUBLIC / dest)
for helper in [RUN.parent / 'launch-agy-pro-r01.py', RUN.parent / 'launch-agy-pro-r01.ps1',
               RUN.parent / 'finalize-agy-pro-r01.py', Path('C:/meter-run-packages-20261005/correct-agy-pro-r01-package-coverage.py'), Path('C:/meter-run-packages-20261005/audit-agy-pro-r01-final-v2.py'), Path(__file__)]:
    shutil.copy2(helper, PUBLIC / helper.name)
now = datetime.now(timezone.utc).isoformat()
save(PUBLIC / 'snapshot-inventory.json', {
    'run_id': RUN.name, 'captured_at': now,
    'files': {p.relative_to(PUBLIC).as_posix(): {'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size}
              for p in PUBLIC.rglob('*') if p.is_file()},
    'scope': 'Actual first Pro call terminated before implementation. Native identity, failed command, original cost, policy/RM, previous immutable hold and independent restore preserved. No Pro firmware was uploaded.'
})
previous = read(RUN / 'previous-progress-at-transition.json')
verification = read(RUN / 'operator-observation/terminal-verification.json')
progress = {
    'checked_at': now, 'baseline_commit': previous['baseline_commit'], 'block': 1, 'seed': 1,
    'active_models': 5, 'independent_series_planned': 15, 'independent_series_completed': 1,
    'initial_series_started': 3, 'followups_started': 2,
    'product_executions_started': 5, 'product_executions_completed': 5,
    'state': 'agy_pro_initial_review_complete', 'current_run': RUN.name, 'current_directory': str(RUN),
    'ledger': m['operator']['comparison']['ledger'], 'round': 0, 'model': 'gemini-3.1-pro-high',
    'started_at': m['execution']['started_at'], 'ended_at': m['execution']['ended_at'], 'timeout_seconds': 7200,
    'launcher_pid': None, 'profile_sha256': m['execution']['profile_sha256'], 'input_bundle_sha256': m['execution']['input_bundle_sha256'],
    'receipt_sha256': digest((RUN / 'execution-preflight.json').read_bytes()),
    'policy_review_required': True, 'policy_status': 'eligible', 'rm_review': 'complete',
    'elapsed_seconds': m['measurement']['wall_clock_seconds'], 'tokens': m['measurement']['tokens'],
    'candidate_terminal_status_observed': 'environment_failed', 'ongoing_usage_not_terminal': False,
    'candidate_current_phase': 'Initial call reviewed and independently archived; no implementation or firmware. Allowed own-source followup may proceed under unchanged formal limits.',
    'user_interventions_reported': None, 'operator_audited_user_interventions': 0,
    'hardware_access_by_operator_during_candidate': False, 'candidate_hardware_access': False,
    'operator_implementation_feedback_sent_during_run': False,
    'followups_started_for_current_series': 0, 'remaining_current_series_followup_seconds': 7200,
    'remaining_current_series_followup_rounds': 3,
    'native_conversation_id': verification['native_conversation_id'],
    'native_model_verified': 'gemini-3.1-pro-high', 'native_permission_mode_verified': 'request-review',
    'current_native_scope': 'Original global settings/instructions/hooks restored byte-for-byte; owner absent.',
    'board_state': verification['board_state'], 'hardware_upload': 'not_run_no_firmware',
    'candidate_result_submission': 'missing', 'candidate_selection_document_submission': 'missing',
    'implementation_commit': m['outputs']['implementation_commit'],
    'rm_items': audit['rm_items'], 'reference_status': 'fail', 'product_pass': False,
    'independent_restore': 'verified_with_packaged_frozen_validators',
    'final_package_manifest_sha256': audit['package_manifest_sha256'], 'final_package_files_verified': audit['files_verified'],
    'previous_series': previous['previous_series'],
    'deferred_agy_flash_series': {
        'comparison_id': '20261005-antigravity-cli-agy-flash-r01', 'last_run_id': previous['current_run'],
        'state': 'deferred_by_user_next_model_instruction', 'reference_status': 'fail', 'policy_status': 'invalid_for_comparison',
        'product_pass': False, 'rm_items': previous['rm_items'], 'last_implementation_commit': previous['implementation_commit'],
        'remaining_followup_seconds': previous['remaining_current_series_followup_seconds'],
        'remaining_followup_rounds': previous['remaining_current_series_followup_rounds'],
        'final_package_manifest_sha256': previous['final_package_manifest_sha256'],
        'raw_cost_and_terminal_records_preserved': True, 'additional_round_start_authorized_now': False
    },
    'user_requested_hold': False,
    'user_hold_resumption_scope': 'User moves to AGY Pro under the previously authorized comparison workflow; Flash additional rounds remain deferred.',
    'next_model_start_authorized_now': False, 'additional_candidate_round_start_authorized_now': True,
    'terminal_snapshot': PUBLIC.relative_to(ROOT).as_posix(),
    'restart_instruction': 'Do not repeat the initial call. Preserve its environment failure and original costs. Pro own-source formal followup must use its reviewed initial bundle, unchanged profile/permissions/task, new ID and remaining ledger budget.'
}
save(ROOT / 'results/formal-comparison-20261004/progress.json', progress)
print(json.dumps({'run_id': RUN.name, 'status': 'environment_failed', 'policy_status': 'eligible',
                  'public_snapshot_files': len(read(PUBLIC / 'snapshot-inventory.json')['files']),
                  'frozen_validator_audit': 'passed', 'result_valid': False}))
