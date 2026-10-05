"""Publish immutable evaluation and dated policy correction, advance status."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r01')
REST=Path('C:/meter-run-restores-20261006/codex-sol-followup01-final');PACK=Path('C:/meter-run-packages-20261006/codex-sol-followup01-final')
COR=Path('C:/meter-policy-corrections-20261006/codex-sol-initial')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
from policy_review import validate_review
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');audit=read(REST/'frozen-validator-audit.json')
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['files_verified']==459
assert audit['implementation_commit']==f['commit'] and audit['reference_status']=='fail'
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
assert validate_review(read(COR/'run-manifest.json'),COR/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
now=datetime.now(timezone.utc).isoformat()
evidence_root=ROOT/'results/formal-comparison-20261004/evidence'
public=evidence_root/RUN.name/'evaluation-final-20261006';public.mkdir(parents=True,exist_ok=False)
names=['run-manifest.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json','reference-review.json','operator-reference-review-input.json']
names += [p.relative_to(RUN).as_posix() for p in (RUN/'operator-observation').rglob('*') if p.is_file() and 'artifact-snapshot' not in p.relative_to(RUN).parts]
for name in names:
    dest=public/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
for source,name in [(Path(m['operator']['comparison']['ledger']),'ledger-at-review.json'),
    (REST/'frozen-validator-audit.json','restore-audit.json'),(REST/'restore-report.json','restore-report.json'),
    (PACK/'package-manifest.json','package-manifest.json'),(PACK.parent/'codex-sol-followup01-final-create.json','package-create.json'),
    (PACK.parent/'verify-codex-sol-followup01-final.py','verify-final.py'),(Path(__file__),Path(__file__).name)]:shutil.copy2(source,public/name)
def inventory(folder,scope,run_id):
    save(folder/'snapshot-inventory.json',{'run_id':run_id,'captured_at':now,
        'files':{p.relative_to(folder).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in folder.rglob('*') if p.is_file()},'scope':scope})
inventory(public,'Immutable reviewed followup1 snapshot; full459-file package independently verified outside repository. Original first result, raw terminal and cost preserved.',RUN.name)
cor_public=evidence_root/'20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006'
shutil.copytree(COR,cor_public)
for source in [RUN.parent/'review-codex-sol-shell-policy.py',RUN.parent/'shell-command-audit-input.json',RUN.parent/'shell-command-pipeline-findings.json']:
    shutil.copy2(source,cor_public/source.name)
save(cor_public/'publication-scope.json',{'date':'2026-10-06','original_review_and_package_unchanged':True,
    'effective_policy_status':'invalid_for_comparison','initial_confirmed_pipeline_count':7,'followup1_confirmed_pipeline_count':4,
    'policy_audit_method':'PowerShell AST inspection of captured command bodies; commands not executed. Quoted regex pipes excluded; ambiguous parse at first-run line175 excluded from confirmed count.',
    'portable_full_package':False,'scope':'Dated policy reassessment and cost-summary metadata copy. Use the original453-file package for full source/artifact restoration. This copy is not a new candidate invocation or replacement first result.'})
inventory(cor_public,'Dated first-run and Sol-series policy correction; original eligible review and453-file package retained without byte changes. Policy-only metadata copy, not portable full candidate package.','20261005-codex-cli-gpt-6-sol-r01')
p=read(ROOT/'results/formal-comparison-20261004/progress.json')
assert p['current_run']==RUN.name and p['product_executions_started']==10 and p['product_executions_completed']==9
first=p['current_series_first_result'];first['original_policy_status']=first['policy_status'];first['policy_status']='invalid_for_comparison'
first['effective_policy_status']='invalid_for_comparison';first['policy_correction_snapshot']=cor_public.relative_to(ROOT).as_posix()
first['corrected_policy_review_sha256']=read(COR/'correction-note.json')['corrected_policy_review_sha256']
first['original_policy_review_and_package_unchanged']=True
slot=read(RUN/'operator-observation/hardware-slot.json')
p.update(checked_at=now,state='codex_sol_followup_01_evaluated_followup_02_pending',product_executions_completed=10,
    ended_at=m['execution']['ended_at'],policy_status='invalid_for_comparison',rm_review='complete',reference_status='fail',product_pass=False,
    rm_items=audit['rm_items'],elapsed_seconds=m['measurement']['wall_clock_seconds'],tokens=m['measurement']['tokens'],
    raw_reasoning_output_tokens=2880,frozen_reasoning_output_tokens=None,candidate_terminal_status_observed='completed',ongoing_usage_not_terminal=False,
    candidate_current_phase='Followup1 implementation/submission terminal and fully reviewed. Common frames accepted; LCD/BOOT fail. Own-source followup2 pending preparation.',
    process_ids_are_historical=True,candidate_processes_remaining=[],implementation_commit=f['commit'],local_candidate_branch_at_freeze='detached',
    operator_audited_user_interventions=0,operator_observational_feedback_supplied_before_run=True,
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=459,final_package=str(PACK),final_restore=str(REST),
    final_snapshot=public.relative_to(ROOT).as_posix(),series_effective_policy_status='invalid_for_comparison',series_quality_eligible=False,
    series_policy_correction_snapshot=cor_public.relative_to(ROOT).as_posix(),cost_checkpoint='results/formal-comparison-20261004/comparison-checkpoint-09.md',
    board_state='Sol followup1 frozen artifact uploaded onCOM3 at03:50KST; actual common frames0/1 accepted. User photo has no legible text and buttons do not change it. User manual RESET reboots to same image; spontaneous reboot and30s continuity unverified. Serial closed.',
    board_artifact_run_id=RUN.name,upload_completed_at=slot['upload_completed_at'],hardware_artifact_sha256=f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    receiver_accepted_sequences=[0,1],receiver_rejected_errors=[],photo_sha256=audit['photo_sha256'],
    user_initiated_reset_confirmed=True,continuous_30s_verified=False,spontaneous_reboot_verified=False,
    remaining_current_series_followup_seconds=audit['remaining_followup_seconds'],remaining_current_series_followup_rounds=2,
    remaining_seconds_is_pre_terminal_budget=False,additional_candidate_round_start_authorized_now=True,additional_candidate_round_ready_now=False,
    followup_preparation_gate='In new copy only remove inherited generated outputs and tracked Python bytecode; prove source/fixed inputs/profile unchanged, add local generated-output excludes, obtain fresh receipt. Original freezes and global permissions unchanged.',
    restart_instruction='Followup1 is terminal, reviewed, independently preserved. Initial original policy remains archived eligible but dated effective correction makes Sol-series quality invalid. Continue allowed own-source followup2 with6750.313sec/two remaining rounds; never rerun first/followup1 or change their source/cost/conditions. Keep Pro closed, Flash deferred and Luna unstarted.')
save(ROOT/'results/formal-comparison-20261004/progress.json',p)
print(json.dumps({'evaluation_snapshot_files':len(read(public/'snapshot-inventory.json')['files']),
    'correction_snapshot_files':len(read(cor_public/'snapshot-inventory.json')['files']),'state':p['state'],'package_files':459}))
