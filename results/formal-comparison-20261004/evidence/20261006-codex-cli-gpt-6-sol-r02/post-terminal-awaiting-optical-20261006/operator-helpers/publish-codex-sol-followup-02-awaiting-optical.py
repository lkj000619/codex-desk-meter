"""Preserve terminal cost, independent host tests/upload while RM stays pending."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02')
REST=Path('C:/meter-run-restores-20261006/codex-sol-followup02-pre-observation')
PACK=Path('C:/meter-run-packages-20261006/codex-sol-followup02-pre-observation')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest,verify_evidence
from policy_review import validate_review
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');audit=read(REST/'frozen-validator-audit.json')
slot=read(RUN/'operator-observation/hardware-slot.json');ledger_path=Path(m['operator']['comparison']['ledger']);ledger=read(ledger_path)
assert m['operator']['status']=='completed' and len(ledger['runs'])==3 and not ledger['runs'][-1]['reviewed']
assert audit['files_verified']==418 and audit['inventory_bytes_verified'] and audit['host_checks_completed'] and not audit['reference_review_applied']
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
assert slot['upload_completed'] and slot['receiver_accepted_sequences']==[0,1] and not slot['receiver_rejected_errors']
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
verify_evidence(m,RUN)
remaining=7200-sum(v['elapsed_seconds'] for v in ledger['runs'] if v['round'])
usage=read(RUN/'operator-observation/native-tool-review.json')['raw_turn_usage']
now=datetime.now(timezone.utc).isoformat()
pending_path=RUN/'operator-observation/optical-observation-pending.json'
if not pending_path.exists():save(pending_path,{'run_id':RUN.name,'round':2,'recorded_at':now,
    'candidate_implementation_and_submission_terminal':True,'host_checks_complete':True,'hardware_upload_complete':True,
    'operator_product_pass':None,'rm_review_applied':False,'reference_status':'not_run','optical_observation':'awaiting_user',
    'question_identifies_upload_at_kst':'2026-10-06 04:21','artifact_sha256':slot['artifact_sha256'],
    'receiver_accepted_sequences':[0,1],'serial_closed':True,'remaining_followup_seconds':remaining,'remaining_followup_rounds':1,
    'additional_candidate_call_before_optical_evaluation':False,'old_user_photo_is_current_artifact_evidence':False})
public=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'post-terminal-awaiting-optical-20261006'
public.mkdir(parents=True,exist_ok=True)
assert not (public/'snapshot-inventory.json').exists(),'Published snapshot must never be overwritten.'
def copy_file(source,target):
    extended=Path('\\\\?\\'+str(target.resolve()))
    extended.parent.mkdir(parents=True,exist_ok=True)
    if extended.exists():assert extended.read_bytes()==source.read_bytes(),str(target)
    else:shutil.copy2(source,extended)
names=['run-manifest.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json']
names += [p.relative_to(RUN).as_posix() for p in (RUN/'operator-observation').rglob('*') if p.is_file() and 'artifact-snapshot' not in p.relative_to(RUN).parts]
for name in names:
    copy_file(RUN/name,public/name)
for path in (REST/'post-restore-host-checks').rglob('*'):
    if path.is_file():copy_file(path,public/'independent-host-checks'/path.relative_to(REST/'post-restore-host-checks'))
for source,name in [(ledger_path,'ledger-at-terminal-awaiting-review.json'),(REST/'frozen-validator-audit.json','restore-audit.json'),
    (REST/'restore-report.json','restore-report.json'),(PACK/'package-manifest.json','package-manifest.json'),
    (PACK.parent/'codex-sol-followup02-pre-observation-create.json','package-create.json'),
    (PACK.parent/'verify-codex-sol-followup02-pre-observation.py','verify-pre-observation-and-host.py'),
    (RUN.parent/'sol-followup02-cost-checkpoint-inputs.json','cost-checkpoint-inputs.json')]:copy_file(source,public/name)
helpers=public/'operator-helpers';helpers.mkdir(exist_ok=True)
for name in ('preserve-codex-sol-followup-02.py','prepare-sol-followup02-shell-audit.py','review-codex-sol-followup-02-policy.py',
    'package-codex-sol-followup-02-pre-observation.py','observe-codex-sol-followup-02.py','update-sol-followup02-cost-checkpoint.py',
    'publish-codex-sol-followup-02-awaiting-optical.py','publish-codex-sol-followup-02-awaiting-optical-original.py'):copy_file(RUN.parent/name,helpers/name)
save(helpers/'publication-path-correction.json',{'date':'2026-10-06','run_id':RUN.name,
    'original_failure':'Windows FileNotFoundError at destination longer than MAX_PATH while copying an operator source snapshot. Original helper preserved; extended absolute paths now used.',
    'already_copied_bytes_verified_on_resume':True,'snapshot_not_previously_published':True,
    'candidate_invocations_or_source_cost_changes':0,'hardware_upload_repeated':False})
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'round':2,'captured_at':now,
    'files':{p.relative_to(public).as_posix():{'sha256':digest(Path('\\\\?\\'+str(p.resolve())).read_bytes()),'bytes':p.stat().st_size} for p in public.rglob('*') if p.is_file()},
    'scope':'Immutable terminal/host/upload snapshot awaiting user optical evidence.418-file pre-observation package independently restored; formal RM not applied; not a final product or series completion claim.'})
p=read(ROOT/'results/formal-comparison-20261004/progress.json')
assert p['state']=='codex_sol_followup_02_running' and p['product_executions_started']==11 and p['product_executions_completed']==10
p.update(checked_at=now,state='codex_sol_followup_02_awaiting_user_optical_observation',product_executions_completed=11,
    ended_at=m['execution']['ended_at'],policy_status='invalid_for_comparison',rm_review='awaiting_user_optical_observation',
    reference_status='not_run',product_pass=None,rm_items=None,candidate_submitted_product_pass=False,
    candidate_terminal_status_observed='completed',ongoing_usage_not_terminal=False,elapsed_seconds=m['measurement']['wall_clock_seconds'],tokens=m['measurement']['tokens'],
    raw_reasoning_output_tokens=usage.get('reasoning_output_tokens'),frozen_reasoning_output_tokens=m['measurement']['tokens']['reasoning'],
    candidate_current_phase='Round2 implementation/submission terminal. Independent host tests, collector/common payload equality and original-artifact upload/receipt complete. LCD/BOOT/continuity and formal RM await user. No next call.',
    implementation_commit=f['commit'],local_candidate_branch_at_freeze='detached',process_ids_are_historical=True,candidate_processes_remaining=[],
    operator_audited_user_interventions=0,remaining_current_series_followup_seconds=remaining,remaining_seconds_is_pre_terminal_budget=False,
    pre_observation_package_manifest_sha256=audit['package_manifest_sha256'],pre_observation_package_files_verified=418,
    pre_observation_package=str(PACK),pre_observation_restore=str(REST),terminal_observation_snapshot=public.relative_to(ROOT).as_posix(),
    cost_checkpoint='results/formal-comparison-20261004/comparison-checkpoint-10.md',
    board_state='Frozen Sol followup2 original artifact uploaded onCOM3 at2026-10-06 04:21:15KST; common seq0/1 accepted. Current LCD/BOOT/stability unobserved; prior photo is followup1 only. Serial closed.',
    board_artifact_run_id=RUN.name,upload_completed_at=slot['upload_completed_at'],hardware_artifact_sha256=slot['artifact_sha256'],
    receiver_accepted_sequences=[0,1],receiver_rejected_errors=[],user_initiated_reset_confirmed=None,
    continuous_30s_verified=False,spontaneous_reboot_verified=False,current_optical_evidence_received=False,
    collector_matches_common_reference_payload=True,host_provider_fixture_validity_checks_passed=17,host_python_unit_tests_passed=6,
    additional_candidate_round_start_authorized_now=False,additional_candidate_round_ready_now=False,
    series_measured_seconds=sum(v['elapsed_seconds'] for v in ledger['runs']),
    series_measured_normalized_tokens=sum(v['tokens']['total'] for v in ledger['runs']),
    restart_instruction='Round2 is terminal, archived and uploaded; do not rerun candidate or rebuild. Await user optical evidence for04:21KST artifact486cd84b; preserve exact source/photo/video association and manual RESET versus spontaneous reboot. Formal review guard uses preserved original terminal manifest. Complete RM once, final package/independent audit and remaining6127.751sec/one-round gate before any followup3. Keep series quality invalid, Pro closed, Flash deferred and Luna unstarted.')
save(ROOT/'results/formal-comparison-20261004/progress.json',p)
print(json.dumps({'run_id':RUN.name,'state':p['state'],'snapshot_files':len(read(public/'snapshot-inventory.json')['files']),
    'remaining_followup_seconds':remaining,'remaining_followup_rounds':1,'package_files_verified':418,'formal_rm_applied':False,
    'raw_reasoning_output_tokens':usage.get('reasoning_output_tokens'),'series_tokens':p['series_measured_normalized_tokens']}))
