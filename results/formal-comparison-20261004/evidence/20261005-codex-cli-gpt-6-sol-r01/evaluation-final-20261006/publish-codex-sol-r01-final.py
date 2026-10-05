"""Publish an immutable final metadata snapshot and update operator progress."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
ROOT=Path.cwd();RUN=Path('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01')
REST=Path('C:/meter-run-restores-20261006/codex-sol-r01-final');PACK=Path('C:/meter-run-packages-20261006/codex-sol-r01-final')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');audit=read(REST/'frozen-validator-audit.json')
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['files_verified']==453
assert audit['implementation_commit']==f['commit'] and audit['reference_status']=='fail'
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
public=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'evaluation-final-20261006'
public.mkdir(parents=True,exist_ok=False)
names=['run-manifest.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json','reference-review.json','operator-reference-review-input.json']
names += [p.relative_to(RUN).as_posix() for p in (RUN/'operator-observation').rglob('*') if p.is_file() and 'frames' not in p.relative_to(RUN).parts and 'artifact-snapshot' not in p.relative_to(RUN).parts]
for name in names:
    dest=public/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
for source,name in [(Path(m['operator']['comparison']['ledger']),'ledger-at-review.json'),(REST/'frozen-validator-audit.json','restore-audit.json'),
    (REST/'restore-report.json','restore-report.json'),(PACK/'package-manifest.json','package-manifest.json'),
    (PACK.parent/'codex-sol-r01-final-create.json','package-create.json'),(PACK.parent/'codex-sol-r01-final-audit-correction.json','final-audit-correction.json'),
    (PACK.parent/'verify-codex-sol-r01-final.py','original-final-audit.py'),(PACK.parent/'verify-codex-sol-r01-final-v2.py','corrected-final-audit.py'),
    (Path(__file__),Path(__file__).name)]:shutil.copy2(source,public/name)
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':datetime.now(timezone.utc).isoformat(),
    'files':{p.relative_to(public).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in public.rglob('*') if p.is_file()},
    'scope':'Immutable reviewed first-result snapshot. Full source/artifact/evidence package is independently verified outside repository; inventory and restore proof included. Preserve original candidate result separately from operator assessment.'})
p=read(ROOT/'results/formal-comparison-20261004/progress.json')
assert p['current_run']==RUN.name and p['product_executions_started']==9
p.update(checked_at=datetime.now(timezone.utc).isoformat(),state='codex_sol_initial_evaluated_followup_pending',
    product_executions_completed=9,ended_at=m['execution']['ended_at'],policy_status='eligible',rm_review='complete',
    reference_status='fail',product_pass=False,rm_items=audit['rm_items'],elapsed_seconds=m['measurement']['wall_clock_seconds'],
    tokens=m['measurement']['tokens'],candidate_terminal_status_observed='completed',ongoing_usage_not_terminal=False,
    candidate_current_phase='Initial implementation/submission terminal and reviewed. Common receiver, LCD and BOOT fail; own-source followup pending preparation.',
    process_ids_are_historical=True,candidate_processes_remaining=[],implementation_commit=f['commit'],
    local_candidate_branch_at_freeze=f['candidate_branch'],manifest_experiment_branch=m['execution']['branch'],
    candidate_repository_is_separate=True,user_interventions_reported=None,operator_audited_user_interventions=0,
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=453,
    final_package=str(PACK),final_restore=str(REST),final_snapshot=public.relative_to(ROOT).as_posix(),
    board_state='Frozen Codex Sol r01 installed on COM3 on 2026-10-06 00:57:03 KST; two common frames rejected; confirmed LCD has no legible text and BOOT has no response; serial closed.',
    upload_completed_at=read(RUN/'operator-observation/hardware-slot.json')['upload_completed_at'],
    hardware_artifact_sha256=f['artifacts']['build/codex_desk_meter.bin']['sha256'],receiver_accepted_sequences=[],
    receiver_rejected_errors=['SCHEMA_INVALID','SCHEMA_INVALID'],video_sha256=audit['video_sha256'],video_duration_seconds=12.9,
    additional_candidate_round_start_authorized_now=True,additional_candidate_round_ready_now=False,
    followup_preparation_gate='Remove generated build/build-host output only in fresh followup working copy; prove unchanged own source/fixed inputs/profile; fresh receipt; no prior-cache execution.',
    restart_instruction='Initial invocation is terminal and fully reviewed; do not rerun it or change source/frozen refs. Read final package audit, ledger and progress. Prepare own followup with generated-cache cleanup and dated source-equivalence proof, then unchanged profile and current receipt. Keep Pro closed and Flash deferred; Luna unstarted.')
save(ROOT/'results/formal-comparison-20261004/progress.json',p)
print(json.dumps({'snapshot_files':len(read(public/'snapshot-inventory.json')['files']),'progress_state':p['state'],'package_files':453}))
