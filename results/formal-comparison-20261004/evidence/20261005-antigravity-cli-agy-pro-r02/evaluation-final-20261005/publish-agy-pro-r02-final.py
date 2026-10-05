from pathlib import Path
from datetime import datetime,timezone
import json,shutil,sys
ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-pro-r02');OUT=RUN/'operator-observation'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
m=read(OUT/'terminal-originals/run-manifest.json');freeze=read(RUN/'operator-source-freeze.json');commit=freeze['commit'];round_number=1
ledger_path=Path(m['operator']['comparison']['ledger'])
PACK=Path('C:/meter-run-packages-20261005/agy-pro-r02-final');REST=Path('C:/meter-run-restores-20261005/agy-pro-r02-final')
created=read(PACK.parent/(PACK.name+'-create.json'));audit_path=PACK.parent/'agy-pro-r02-final-audit-v2.py'
names=[item['path'] for item in read(RUN/'reference-review.json')['items']['RM1']['evidence']]
audit = read(REST / 'frozen-validator-audit.json')
PUBLIC = ROOT / 'results/formal-comparison-20261004/evidence' / RUN.name / 'evaluation-final-20261005'
PUBLIC.mkdir(parents=True, exist_ok=True)
files = set(names) | {'run-manifest.json', 'stdout.jsonl', 'stderr.txt', 'command-audit.json', 'prompt.txt', 'profile.json',
                      'policy-review.json', 'reference-review.json', 'operator-reference-review-input.json',
                      'feedback.json', 'candidate-feedback.json', 'candidate-inputs.json', 'execution-preflight.json'}
for name in files:
    dest = PUBLIC / name; dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert dest.read_bytes() == (RUN / name).read_bytes(), name
    else:
        shutil.copy2(RUN / name, dest)
for src, name in [(ledger_path, 'ledger-reviewed.json'), (PACK / 'package-manifest.json', 'package-manifest.json'),
                  (REST / 'frozen-validator-audit.json', 'restore-audit.json'), (REST / 'restore-report.json', 'restore-report.json'),
                  (PACK.parent / (PACK.name + '-create.json'), 'package-create.json'), (audit_path, audit_path.name), (Path(__file__), Path(__file__).name)]:
    shutil.copy2(src, PUBLIC / name)
now = datetime.now(timezone.utc).isoformat()
save(PUBLIC / 'snapshot-inventory.json', {'run_id': RUN.name, 'captured_at': now,
    'files': {p.relative_to(PUBLIC).as_posix(): {'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size} for p in PUBLIC.rglob('*') if p.is_file()},
    'scope': 'Final review and independent restore of one unbuilt Pro followup. Original terminal/cost and source bytes retained. No Pro firmware upload.'})
p = read(ROOT / 'results/formal-comparison-20261004/progress.json')
assert p['current_run'] == RUN.name
p.update(checked_at=now, state='agy_pro_followup_%d_review_complete' % round_number,
    product_executions_completed=p['product_executions_started'], started_at=m['execution']['started_at'], ended_at=m['execution']['ended_at'],
    launcher_pid=None, candidate_terminal_status_observed='environment_failed', ongoing_usage_not_terminal=False,
    policy_status='eligible', rm_review='complete', rm_items=audit['rm_items'], reference_status='fail', product_pass=False,
    elapsed_seconds=m['measurement']['wall_clock_seconds'], tokens=m['measurement']['tokens'],
    candidate_current_phase='Followup ended on denial without firmware or final submissions; policy/RM and independent archive complete.',
    remaining_current_series_followup_seconds=audit['remaining_followup_seconds'], remaining_current_series_followup_rounds=audit['remaining_followup_rounds'],
    current_native_scope='Global native settings/instructions/hooks restored byte-for-byte; owner absent.',
    implementation_commit=commit, independent_restore='verified_with_packaged_frozen_validators',
    final_package_manifest_sha256=created['package_manifest_sha256'], final_package_files_verified=created['files'],
    candidate_result_submission='missing', candidate_selection_document_submission='missing',
    terminal_snapshot=PUBLIC.relative_to(ROOT).as_posix(), additional_candidate_round_start_authorized_now=audit['remaining_followup_rounds']>0)
save(ROOT / 'results/formal-comparison-20261004/progress.json', p)
print(json.dumps({'run_id': RUN.name, 'seconds': m['measurement']['wall_clock_seconds'], 'tokens': m['measurement']['tokens']['total'],
                  'freeze': commit, 'package_files': created['files'], 'public_files': len(read(PUBLIC / 'snapshot-inventory.json')['files']),
                  'remaining_seconds': audit['remaining_followup_seconds'], 'remaining_rounds': audit['remaining_followup_rounds']}))
