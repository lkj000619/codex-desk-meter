"""Publish dated raw evidence and current state; retain all older snapshots."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004'
RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261006/codex-luna-r01-evaluation');REST=Path('C:/meter-run-restores-20261006/codex-luna-r01-evaluation')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest
audit=read(REST/'frozen-validator-audit.json');m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
p=read(FORMAL/'progress.json');ledger=read(Path(p['ledger']));slot=read(OUT/'hardware-attempt-02/hardware-slot.json')
assert p['state']=='codex_luna_initial_terminal_awaiting_evaluation' and p['product_executions_completed']==12
assert audit['files_verified']==464 and audit['reference_review_applied'] and not audit['product_pass']
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
assert ledger['runs'][0]['reviewed'] and ledger['runs'][0]['reference_status']=='fail' and ledger['state']=='active'
now=datetime.now(timezone.utc).isoformat()
inputs=[]
for path in [Path('C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json'),
             Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-flash-r01.json'),
             Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-pro-r01.json'),
             Path('C:/meter-runs-20261005/ledgers/20261005-codex-cli-gpt-6-sol-r01.json'),Path(p['ledger'])]:
    for run in read(path)['runs']:
        assert run['status'] in {'completed','timeout','aborted','environment_failed'}
        source=Path(run['directory'])/'run-manifest.json'
        if run['run_id']=='20261005-codex-cli-gpt-6-sol-r01':source=Path('C:/meter-policy-corrections-20261006/codex-sol-initial/run-manifest.json')
        inputs.append(source)
assert len(inputs)==len({read(x)['run_id'] for x in inputs})==12
total=sum(read(x)['measurement']['tokens']['total'] for x in inputs);assert total==44103444
checkpoint=FORMAL/'comparison-checkpoint-12.md';assert not checkpoint.exists()
subprocess.run([sys.executable,'-B','-X','utf8','C:/meter-operator-20261004/scripts/summarize-benchmark.py',*map(str,inputs),'--output',str(checkpoint)],check=True)
body=checkpoint.read_text(encoding='utf-8');assert body.startswith('# Benchmark results\n\n')
header='2026-10-06 checkpoint12: Luna 최초의 원본 동결·독립 검증·COM3 재업로드·검은 화면 사용자 보고를 반영한 후보12회 비용 기록이다. Luna 최초3,094.422초·정규화17,413,487 token과 전체12회44,103,444 token에 모든 실패·부적격 비용을 포함한다. RM1/2 partial·RM3 fail·RM4/5 not_run, reference fail·product_pass false다. 공통 shell 제한 위반으로 Luna 품질/적격 reference-cost는 제외한다. 후속0회·잔여7,200초/3회이며 새 호출은 없다. Sol/Pro 종료·Flash 보류·과거 원본 판정과 checkpoint11까지는 보존한다. 전체 독립 series 종료3/15이며 비교는 미완료다.\n\n'
checkpoint.write_text(body.replace('# Benchmark results\n\n','# Benchmark results\n\n'+header,1),encoding='utf-8')
public=FORMAL/'evidence'/RUN.name/'evaluation-20261006';public.mkdir(parents=True,exist_ok=False)
def extended(path):return Path('\\\\?\\'+str(path.resolve()))
def copy(source,name):
    dest=extended(public/name);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(extended(source),dest)
names=['run-manifest.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json','reference-review.json','operator-reference-review-input.json']
names += [x.relative_to(RUN).as_posix() for x in OUT.rglob('*') if x.is_file() and 'artifact-snapshot' not in x.relative_to(RUN).parts]
for name in sorted(set(names)):copy(RUN/name,name)
for source,name in [(Path(p['ledger']),'ledger-at-review.json'),(REST/'frozen-validator-audit.json','restore-audit.json'),
                    (REST/'restore-report.json','restore-report.json'),(PACK/'package-manifest.json','package-manifest.json'),
                    (PACK.parent/'codex-luna-r01-evaluation-create.json','package-create.json')]:copy(source,name)
for slug in ['pre-observation','upload-record','upload02-awaiting-optical']:
    copy(PACK.parent/('codex-luna-r01-'+slug)/'package-manifest.json','earlier-packages/'+slug+'/package-manifest.json')
    copy(PACK.parent/('codex-luna-r01-'+slug+'-create.json'),'earlier-packages/'+slug+'/package-create.json')
copy(Path(__file__),'operator-helpers/'+Path(__file__).name)
save(public/'cost-checkpoint-inputs.json',{'unique_attempts':12,'total_normalized_tokens':total,
    'input_manifests':[{'path':str(x),'run_id':read(x)['run_id'],'sha256':digest(x.read_bytes())} for x in inputs],
    'checkpoint':checkpoint.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(checkpoint.read_bytes()),'original_cost_definitions_unchanged':True})
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'round':0,'captured_at':now,
    'files':{x.relative_to(public).as_posix():{'sha256':digest(extended(x).read_bytes()),'bytes':x.stat().st_size} for x in public.rglob('*') if x.is_file()},
    'scope':'Immutable bounded initial evaluation: original cost/source, policy invalid, exact COM3 upload2 and user black-screen report.464-file package independently restored with frozen validators. No confirmed receiver/BOOT/30s/full-product success, followup or other model invocation.'})
p.update(checked_at=now,state='codex_luna_initial_reviewed_black_screen',policy_status='invalid_for_comparison',
    rm_review='initial_review_complete_with_unmeasured_items',reference_status='fail',rm_items=audit['rm_items'],product_pass=False,
    source_freeze_complete=True,independent_host_evaluation_complete=True,implementation_commit=f['commit'],
    local_candidate_branch_at_freeze=f['candidate_branch'],operator_audited_user_interventions=0,
    candidate_current_phase='Initial implementation/submission terminal; frozen/restored/host checked and same firmware reuploaded. User reports black screen; bounded RM review complete. Receiver/BOOT/30s unconfirmed; no followup started.',
    source_files_frozen=33,artifacts_frozen=19,quality_reference_cost_eligible=False,
    pre_observation_package_manifest_sha256='7466fc722db5e96f9016a564e4f643640adfbe567397bcf15e88bf144aa85274',
    pre_observation_package_files_verified=404,pre_observation_package='C:/meter-run-packages-20261006/codex-luna-r01-pre-observation',
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=464,
    final_package=str(PACK),final_restore=str(REST),final_snapshot=public.relative_to(ROOT).as_posix(),
    cost_checkpoint=checkpoint.relative_to(ROOT).as_posix(),cost_checkpoint_covers_completed_executions=12,
    total_normalized_tokens_all_attempts=total,current_invocation_terminal_cost_available=True,
    board_artifact_run_id=RUN.name,board_state_is_prior_sol_observation=False,luna_hardware_upload_performed=True,
    board_state='Same frozen Luna initial artifact reuploaded onCOM3 at2026-10-06 21:03:05KST. User reports black LCD. Common seq0/1 host writes complete; no receiver markers. BOOT/30s/reset facts unreported; serial closed.',
    upload_completed_at=slot['upload_completed_at'],hardware_artifact_sha256=slot['artifact_sha256'],
    current_hardware_attempt=2,earlier_hardware_attempt_target_association='unconfirmed_by_user_report',
    hardware_attempts_recorded=2,host_writes_completed_sequences=[0,1],receiver_accepted_sequences=[],receiver_rejected_errors=[],
    receiver_acceptance='unconfirmed',serial_capture_bytes=0,serial_closed=True,current_optical_evidence_received=True,
    current_optical_evidence_kind='user_text_black_screen',user_initiated_reset_confirmed=None,continuous_30s_verified=False,
    collector_matches_common_reference_payload=False,host_provider_fixture_validity_checks_passed=16,host_provider_fixture_validity_cases=17,
    host_python_unit_tests_passed=11,host_c_executables_passed=3,common_wire_encoder_exact_match=True,
    followups_started_for_current_series=0,remaining_current_series_followup_seconds=7200,remaining_current_series_followup_rounds=3,
    additional_candidate_round_start_authorized_now=False,additional_candidate_round_ready_now=False,
    restart_instruction='Luna initial evaluated and current original firmware uploaded21:03KST onCOM3. Do not repeat initial, repair operator-side candidate code or rebuild. Preserve black-screen user report and unconfirmed receipt/BOOT/30s. Own followup would need the normal frozen-source/observational-feedback/fresh-preflight gate; none prepared or started. Keep Luna policy invalid, Sol/Pro closed, Flash deferred and all old evidence/cost/ref unchanged.')
save(FORMAL/'progress.json',p)
print(json.dumps({'state':p['state'],'snapshot_files':len(read(public/'snapshot-inventory.json')['files']),'package_files_verified':464,
    'normalized_tokens_all_attempts':total,'rm_items':p['rm_items'],'current_upload_at':slot['upload_completed_at'],'followups_started':0}))
