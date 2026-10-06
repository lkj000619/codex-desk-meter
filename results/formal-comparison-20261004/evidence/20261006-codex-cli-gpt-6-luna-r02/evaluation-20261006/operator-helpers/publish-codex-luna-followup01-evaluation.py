"""Publish dated raw evidence and current state; retain all older snapshots."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004'
RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r02');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261006/codex-luna-followup01-evaluation');REST=Path('C:/meter-run-restores-20261006/codex-luna-followup01-evaluation')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest
audit=read(REST/'frozen-validator-audit.json');m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
p=read(FORMAL/'progress.json');ledger=read(Path(p['ledger']));slot=read(OUT/'hardware-slot.json')
assert p['state']=='codex_luna_followup_01_running' and p['product_executions_completed']==12
assert audit['files_verified']==535 and audit['reference_review_applied'] and not audit['product_pass']
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
assert len(ledger['runs'])==2 and ledger['runs'][-1]['reviewed'] and ledger['runs'][-1]['reference_status']=='fail' and ledger['state']=='active'
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
assert len(inputs)==len({read(x)['run_id'] for x in inputs})==13
total=sum(read(x)['measurement']['tokens']['total'] for x in inputs);assert total==57517475
checkpoint=FORMAL/'comparison-checkpoint-13.md';assert not checkpoint.exists()
subprocess.run([sys.executable,'-B','-X','utf8','C:/meter-operator-20261004/scripts/summarize-benchmark.py',*map(str,inputs),'--output',str(checkpoint)],check=True)
body=checkpoint.read_text(encoding='utf-8');assert body.startswith('# Benchmark results\n\n')
header='2026-10-06 checkpoint13: Luna 후속1 구현·제출·동결·독립 복원·COM3 업로드와 사용자 검은 화면 보고를 반영한다. 이번 2,987초·정규화13,414,031 token, Luna series30,827,518 token, 전체13회57,517,475 token에 실패·부적격 비용을 모두 포함한다. RM1 pass/RM2 partial/RM3 fail/RM4·5 not_run, reference fail·product_pass false다. 실제 파이프2호출로 품질/적격 reference-cost에서 제외한다. 후속1회 사용·잔여4,213초/최대2회이며 추가 호출은 없다. Frozen adapter의 reasoning null과 raw94,200을 구분하고 cached12,811,008은 input에 포함한다. Sol/Pro 종료·Flash 보류·최초 판정과 checkpoint12까지는 보존한다. 독립 series 종료3/15로 전체 비교는 미완료다.\n\n'
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
                    (PACK.parent/'codex-luna-followup01-evaluation-create.json','package-create.json')]:copy(source,name)
for slug in ['pre-observation']:
    copy(PACK.parent/('codex-luna-followup01-'+slug)/'package-manifest.json','earlier-packages/'+slug+'/package-manifest.json')
    copy(PACK.parent/('codex-luna-followup01-'+slug+'-create.json'),'earlier-packages/'+slug+'/package-create.json')
copy(Path(__file__),'operator-helpers/'+Path(__file__).name)
save(public/'cost-checkpoint-inputs.json',{'unique_attempts':13,'total_normalized_tokens':total,
    'input_manifests':[{'path':str(x),'run_id':read(x)['run_id'],'sha256':digest(x.read_bytes())} for x in inputs],
    'checkpoint':checkpoint.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(checkpoint.read_bytes()),'original_cost_definitions_unchanged':True})
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'round':1,'captured_at':now,
    'files':{x.relative_to(public).as_posix():{'sha256':digest(extended(x).read_bytes()),'bytes':x.stat().st_size} for x in public.rglob('*') if x.is_file()},
    'scope':'Immutable bounded followup1 evaluation: original source/cost, pipeline-policy invalid, verified COM3 upload and matching boot, current user black-screen report.535-file package independently restored using frozen validators. No confirmed device frame acceptance, BOOT/30s/full-product success or further candidate invocation.'})
runtime=read(OUT/'hardware-post-upload-reset/runtime-source-binding.json')
preserved={k:p[k] for k in ['previous_series','closed_agy_pro_series','deferred_agy_flash_series','closed_codex_sol_series','codex_sol_result_at_transition','current_series_first_result']}
launch_started=p['started_at']
p.update(checked_at=now,state='codex_luna_followup_01_reviewed_black_screen',product_executions_completed=13,
    started_at=m['execution']['started_at'],ended_at=m['execution']['ended_at'],elapsed_seconds=m['measurement']['wall_clock_seconds'],
    tokens=m['measurement']['tokens'],raw_reasoning_output_tokens=94200,tool_calls=m['measurement']['tool_calls'],failed_commands=m['measurement']['failed_commands'],
    launch_snapshot_started_at=launch_started,process_ids_are_historical=True,candidate_processes_remaining=[],
    candidate_terminal_status_observed=m['operator']['status'],ongoing_usage_not_terminal=False,candidate_exit_code=0,
    policy_status='invalid_for_comparison',policy_confirmed_pipeline_calls=2,rm_review='followup01_review_complete_with_unmeasured_items',
    reference_status='fail',rm_items=audit['rm_items'],product_pass=False,source_freeze_complete=True,
    independent_host_evaluation_complete=True,implementation_commit=f['commit'],local_candidate_branch_at_freeze=f['candidate_branch'],
    operator_audited_user_interventions=0,quality_reference_cost_eligible=False,
    candidate_current_phase='Followup1 implementation/submission terminal; original firmware frozen/restored/host checked/uploaded. Matching boot and USB ready observed; user reports continued black screen. Bounded RM review complete; device acceptance and BOOT/30s unconfirmed.',
    candidate_result_submission_present=True,candidate_selection_document_present=True,candidate_submitted_product_pass=False,
    firmware_artifact_present=True,firmware_build_directory='build',source_files_frozen=38,artifacts_frozen=20,
    pre_observation_package_manifest_sha256='857c5888e4afa27fb073bd8d6ad8aed11260f2a43c9e858bff9cd2768218a334',
    pre_observation_package_files_verified=470,pre_observation_package='C:/meter-run-packages-20261006/codex-luna-followup01-pre-observation',
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=audit['files_verified'],
    final_package=str(PACK),final_restore=str(REST),final_snapshot=public.relative_to(ROOT).as_posix(),
    cost_checkpoint=checkpoint.relative_to(ROOT).as_posix(),cost_checkpoint_covers_completed_executions=13,
    cost_checkpoint_covers_completed_invocations=13,total_normalized_tokens_all_attempts=total,current_invocation_terminal_cost_available=True,
    current_series_normalized_tokens=30827518,current_series_measured_seconds=6081.422,
    board_artifact_run_id=RUN.name,board_state_is_prior_sol_observation=False,luna_hardware_upload_performed=True,
    board_state='Original Luna followup1 artifact uploadedCOM3 at2026-10-06 22:51:05KST; supplemental native reset22:54:32KST matches archived ELF and reaches USB ready. User reports continued black LCD. Common host writes0/1 complete; actual frame acceptance unconfirmed. Serial closed.',
    upload_completed_at=slot['upload_completed_at'],hardware_artifact_sha256=slot['artifact_sha256'],
    current_hardware_attempt=1,hardware_attempts_recorded=1,supplemental_native_reset_count=1,supplemental_reset_at=runtime['reset_requested_at'],
    host_writes_completed_sequences=[0,1],receiver_accepted_sequences=[],receiver_rejected_errors=[],receiver_acceptance='unconfirmed',
    first_serial_capture_bytes=0,serial_capture_bytes=5938,application_boot_observed=True,usb_receiver_ready_observed=True,
    psram_memory_test_ok_observed=True,serial_closed=True,current_optical_evidence_received=True,current_optical_evidence_kind='user_text_black_screen',
    user_initiated_reset_confirmed=None,boot_press_count=None,boot_navigation_observed=None,continuous_30s_verified=False,
    collector_matches_common_reference_payload=True,host_provider_fixture_validity_checks_passed=17,host_provider_fixture_validity_cases=17,
    host_python_unit_tests_passed=22,candidate_reported_python_unit_tests=21,host_c_executables_passed=3,common_wire_encoder_exact_match=True,
    production_host_c_receiver_accepted_sequences=[0,1],candidate_wire_schema_cases=29,frozen_operator29_pipeline_completed=False,
    followups_started_for_current_series=1,remaining_current_series_followup_seconds=4213,remaining_current_series_followup_rounds=2,
    remaining_seconds_is_pre_terminal_budget=False,additional_candidate_round_start_authorized_now=False,additional_candidate_round_ready_now=False,
    restart_instruction='Luna followup1 evaluated/frozen/restored and original firmware uploaded22:51KST onCOM3, reset22:54KST. Do not repeat this invocation, operator-repair source or rebuild. Continued black screen; boot confirmed but frame acceptance/BOOT/30s unconfirmed. Remaining own followup budget4213sec/2rounds; another round requires the normal own-source/observational-feedback/fresh-preflight gate and is not prepared or started. Preserve first Luna result/diagnosis and all prior refs/costs; Muse/Pro/Sol closed, Flash deferred.')
assert all(p[k]==v for k,v in preserved.items())
save(FORMAL/'progress.json',p)
print(json.dumps({'state':p['state'],'snapshot_files':len(read(public/'snapshot-inventory.json')['files']),'package_files_verified':535,
    'normalized_tokens_all_attempts':total,'rm_items':p['rm_items'],'current_upload_at':slot['upload_completed_at'],'followups_started':1}))
