"""Publish same-artifact observation evidence and exact terminal budget; await optical facts."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004';RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261007/agy-flash-followup03-awaiting');REST=Path('C:/meter-run-restores-20261007/agy-flash-followup03-awaiting')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
def extended(p):return Path('\\\\?\\'+str(p.resolve()))
p=read(FORMAL/'progress.json');assert p['state']=='agy_flash_followup_3_running' and p['cost_checkpoint_covers_completed_invocations']==17
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');slot=read(OUT/'hardware-slot.json');audit=read(REST/'frozen-validator-audit.json');ledger=read(Path(p['ledger']))
assert m['operator']['status']=='completed' and audit['files_verified']==499 and audit['device_common_frames_accepted']
assert len(ledger['runs'])==4 and not ledger['runs'][-1]['reviewed'] and ledger['runs'][-1]['round']==3
spent=sum(x['elapsed_seconds'] for x in ledger['runs'][1:]);remaining=7200-spent;series_time=sum(x['elapsed_seconds'] for x in ledger['runs']);tokens=sum(x['tokens']['total'] for x in ledger['runs'])
assert abs(remaining-4303.593)<0.00001 and tokens==3892990 and abs(series_time-3659.220)<0.00001
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
PUBLIC=FORMAL/'evidence'/RUN.name/'observation-awaiting-20261007';PUBLIC.mkdir(parents=True,exist_ok=False)
names=['run-manifest.json','profile.json','prompt.txt','candidate-inputs.json','candidate-feedback.json','feedback.json','agent-context.json',
 'stdout.jsonl','stderr.txt','command-audit.json','policy-review.json','operator-policy-decision.json','operator-source-preparation.json','operator-source-freeze.json','execution-preflight.json']
for source in extended(OUT).rglob('*'):
 if source.is_file() and 'artifact-snapshot' not in source.relative_to(extended(OUT)).parts:names.append(source.relative_to(extended(RUN)).as_posix())
for name in sorted(set(names)):
 dest=extended(PUBLIC/name);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(extended(RUN/name),dest)
for source,name in [(Path(p['ledger']),'ledger-before-reference-review.json'),(PACK/'package-manifest.json','package-manifest.json'),
 (REST/'frozen-validator-audit.json','restore-audit.json'),(REST/'restore-report.json','restore-report.json'),
 (PACK.parent/'agy-flash-followup03-awaiting-create.json','package-create.json'),
 (PACK.parent/'verify-agy-flash-followup03-awaiting.py','verify-agy-flash-followup03-awaiting.py'),(Path(__file__),Path(__file__).name)]:shutil.copy2(source,PUBLIC/name)
now=datetime.now(timezone.utc).isoformat()
save(PUBLIC/'observation-state.json',{'run_id':RUN.name,'recorded_at':now,'status':'uploaded_awaiting_user_optical_observation',
 'app_sha256':slot['artifact_sha256'],'upload_completed_at':slot['upload_completed_at'],'common_sequences_accepted':[0,1],
 'lcd_boot_30s_observed':False,'current_run_policy_status':'eligible','series_policy_status':'invalid_for_comparison',
 'remaining_followup_seconds':remaining,'remaining_followup_rounds':0,'additional_candidate_call_allowed':False,
 'candidate_calls_in_user_authorized_resumption':2,'terminal_review_pending_optical_facts':True,
 'board_slot_released':False,'serial_closed':True,'operator_product_repair_or_firmware_rebuild':False})
save(PUBLIC/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,
 'files':{source.relative_to(extended(PUBLIC)).as_posix():{'bytes':source.stat().st_size,'sha256':digest(source.read_bytes())} for source in extended(PUBLIC).rglob('*') if source.is_file()},
 'scope':'Final allowed candidate terminal, unmodified frozen source and same-artifact COM3 capture with0/1 acceptance; optical RM pending.499-file independent restoration verified. Prior485-file package, raw terminal cost and past series judgments preserved.'})
p.update(checked_at=now,state='agy_flash_followup_3_uploaded_awaiting_optical_observation',product_executions_completed=17,
 started_at=m['execution']['started_at'],ended_at=m['execution']['ended_at'],elapsed_seconds=m['measurement']['wall_clock_seconds'],tokens=m['measurement']['tokens'],
 candidate_terminal_status_observed='completed',ongoing_usage_not_terminal=False,current_invocation_terminal_cost_available=True,current_invocation_terminal_time_available=True,
 candidate_current_phase='Final allowed Flash implementation/submissions and499-file independent restoration complete. Same app uploaded; common0/1 accepted. Awaiting LCD/BOOT/30-second observation before RM/series finalization.',
 current_native_scope='Original global settings/instructions/hooks restored and hash verified; native process and owner absent.',
 candidate_processes_remaining=[],process_ids_are_historical=True,tool_calls=m['measurement']['tool_calls'],failed_commands=m['measurement']['failed_commands'],operator_audited_user_interventions=0,
 policy_status='eligible',series_policy_status='invalid_for_comparison',quality_reference_cost_eligible=False,rm_review='awaiting_user_optical_observation',reference_status='pending',product_pass=False,
 implementation_commit=f['commit'],candidate_result_submission='present',candidate_selection_document_submission='present',firmware_artifact_present=True,
 source_freeze_complete=True,independent_host_evaluation_complete=True,host_python_unit_tests_passed=7,host_c_executables_passed=4,
 collector_matches_common_reference_payload=True,common_wire_encoder_exact_match=True,frozen_operator29_pipeline_completed=False,
 remaining_current_series_followup_seconds=remaining,remaining_current_series_followup_rounds=0,remaining_seconds_is_pre_terminal_budget=False,
 current_series_normalized_tokens=tokens,current_series_known_normalized_tokens=tokens,current_series_token_measurement_coverage='4/4',current_series_measured_seconds=series_time,
 current_series_followup_measured_seconds=spent,additional_candidate_round_start_authorized_now=False,additional_candidate_round_ready_now=False,
 hardware_upload_performed=True,board_artifact_run_id=RUN.name,hardware_artifact_sha256=slot['artifact_sha256'],upload_completed_at=slot['upload_completed_at'],
 board_state='COM3 holds frozen final Flash followup3 app; seq0/1 accepted. LCD/BOOT/30s pending; serial closed. Preserve displayed data until observation.',
 receiver_acceptance='observed',receiver_acceptance_observed=True,current_optical_evidence_received=False,boot_navigation_observed=None,continuous_30s_verified=False,continuous_30s_status='not_measured',
 serial_closed=True,terminal_snapshot=PUBLIC.relative_to(ROOT).as_posix(),current_observation_snapshot=PUBLIC.relative_to(ROOT).as_posix(),
 awaiting_package=str(PACK),awaiting_restore=str(REST),awaiting_package_manifest_sha256=audit['package_manifest_sha256'],awaiting_package_files_verified=499,
 pre_observation_package='C:/meter-run-packages-20261007/agy-flash-followup03-pre-observation',pre_observation_package_files_verified=485,
 pre_observation_package_manifest_sha256='565550ac4ab54305e89025eb72babfd68b744cff6427cbe2994f417240ef0a1f',
 restart_instruction='No further candidate round: three followups already used. Obtain current Flash LCD/BOOT/30s facts, distinguish manual RESET, apply one bound RM review and preserve final package/series closure. Do not substitute previous videos, re-run candidate, repair/rebuild firmware or start another independent block.')
save(FORMAL/'progress.json',p)
print(json.dumps({'status':p['state'],'snapshot_files':len(read(PUBLIC/'snapshot-inventory.json')['files']),'remaining_unused_seconds':remaining,'rounds_remaining':0,'current_series_tokens':tokens}))
