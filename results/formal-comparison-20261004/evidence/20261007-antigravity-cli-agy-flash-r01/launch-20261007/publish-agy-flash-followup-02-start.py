"""Preserve native start and replace only current operator status."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,subprocess,sys
ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r01')
PREV=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import digest,read,save
def extended(p):return Path('\\\\?\\'+str(p.resolve()))
m=read(RUN/'run-manifest.json');assert m['operator']['status']=='running' and m['operator']['comparison']['round']==2
raw=(RUN/'stdout.jsonl').read_bytes().splitlines(keepends=True)[0];event=json.loads(raw);init=event['init']
assert init['model']=='gemini-3.8-flash-medium' and init['permission_mode']=='request-review'
assert Path(init['cwd']).resolve()==(RUN/'checkout').resolve()
now=datetime.now(timezone.utc).isoformat();launcher=read(RUN/'experiment-launch.json')
processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',
 "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'agy.exe' } | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Depth 5 -Compress"],text=True,encoding='utf-8'))
if isinstance(processes,dict):processes=[processes]
assert len(processes)==1 and '--model gemini-3.8-flash-medium' in processes[0]['CommandLine']
save(RUN/'native-start-observation.json',{'run_id':RUN.name,'observed_at':now,'status':'running','native_conversation_id':event['conversation_id'],
 'native_model':init['model'],'permission_mode':init['permission_mode'],'native_cwd':init['cwd'],'native_candidate_pid':processes[0]['ProcessId'],
 'processes':processes,'actual_process_argv_matches_frozen_profile':True,'raw_log_prefix_bytes':len(raw),'raw_log_prefix_sha256':digest(raw),
 'scope':'Native init and process identity only; no terminal cost, submission or policy conclusion.'})
(RUN/'native-start-observation-prefix.jsonl').write_bytes(raw)
PUBLIC=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'launch-20261007';PUBLIC.mkdir(parents=True,exist_ok=False)
names=['experiment-launch.json','run-manifest.json','profile.json','candidate-inputs.json','agent-context.json','prompt.txt',
 'feedback.json','candidate-feedback.json','native-start-observation.json','native-start-observation-prefix.jsonl',
 'execution-preflight.json','operator-source-preparation.json','runner-console.txt','runner-console-stderr.txt']
for name in names:
 dest=PUBLIC/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
for folder in ('operator-launch-preflight','feedback-evidence','preflight-evidence'):
 for source in extended(RUN/folder).rglob('*'):
  if source.is_file():
   relative=source.relative_to(extended(RUN));dest=extended(PUBLIC/relative);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
shutil.copy2(Path(m['operator']['comparison']['ledger']),PUBLIC/'ledger-at-start.json')
for name in ('prepare-agy-flash-followup-02.py','launch-agy-flash-followup-02.py','launch-agy-flash-followup-02.ps1','prepared-agy-flash-followup-02.json'):
 shutil.copy2(RUN.parent/name,PUBLIC/name)
shutil.copy2(Path(__file__),PUBLIC/Path(__file__).name)
path=ROOT/'results/formal-comparison-20261004/progress.json';old_raw=path.read_bytes();old=read(path)
assert old['state']=='codex_luna_series_closed_round_limit' and old['product_executions_started']==15
(PUBLIC/'previous-progress-at-resumption.json').write_bytes(old_raw)
keep=('baseline_commit','block','seed','active_models','independent_series_planned','independent_series_completed','initial_series_started',
 'previous_series','closed_agy_pro_series','closed_codex_sol_series','codex_sol_result_at_transition','closed_codex_luna_series',
 'cost_checkpoint','cost_checkpoint_covers_completed_invocations','cost_checkpoint_covers_completed_executions',
 'total_normalized_tokens_all_attempts','known_normalized_tokens_all_attempts','token_measurement_coverage')
p={key:old[key] for key in keep if key in old}
p['agy_flash_deferred_state_at_resumption']=old['deferred_agy_flash_series']
p['codex_luna_result_at_transition']={key:old[key] for key in ('current_run','round','model','started_at','ended_at','elapsed_seconds','tokens','implementation_commit','policy_status','series_policy_status','reference_status','rm_items','product_pass','final_package_manifest_sha256','final_package_files_verified','final_snapshot','current_series_first_result','current_series_previous_result')}
ledger=read(Path(m['operator']['comparison']['ledger']));review=read(PREV/'reference-review.json')
p['current_series_first_result']=ledger['runs'][0]
p['current_series_previous_result']={'run_id':PREV.name,'implementation_commit':review['implementation_commit'] if 'implementation_commit' in review else '94018f1785a590e1514ef1b5145c40f0c03ffca3',
 'rm_items':{key:value['status'] for key,value in review['items'].items()},'reference_status':'fail','policy_status':'invalid_for_comparison',
 'measurement':read(PREV/'run-manifest.json')['measurement'],'final_package_manifest_sha256':'b0e2880fc7c786ae338b9d1870ccd4c3510bf9afb3f5881089ff4d23515f244c'}
p.update(checked_at=now,state='agy_flash_followup_2_running',current_run=RUN.name,current_directory=str(RUN),ledger=m['operator']['comparison']['ledger'],
 product_executions_started=16,product_executions_completed=15,followups_started=11,round=2,model=init['model'],reasoning='medium',
 started_at=m['execution']['started_at'],ended_at=None,timeout_seconds=5710,elapsed_seconds=None,tokens=m['measurement']['tokens'],
 launcher_pid=launcher['launcher_pid'],native_candidate_pid=processes[0]['ProcessId'],native_conversation_id=event['conversation_id'],
 profile_sha256=m['execution']['profile_sha256'],input_bundle_sha256=m['execution']['input_bundle_sha256'],receipt_sha256=digest((RUN/'execution-preflight.json').read_bytes()),
 policy_review_required=True,policy_status='pending_terminal_review',series_policy_status='invalid_for_comparison',rm_review='awaiting_candidate_terminal',
 reference_status='pending',product_pass=None,quality_reference_cost_eligible=False,current_invocation_terminal_cost_available=False,
 candidate_terminal_status_observed='running',ongoing_usage_not_terminal=True,actual_process_argv_matches_frozen_profile=True,native_model_verified=init['model'],
 native_permission_mode_verified=init['permission_mode'],current_native_scope='Existing private scoped AGY settings; originals restored after child exits.',
 candidate_current_phase='Authorized own-source followup2 running; independent terminal evaluation and hardware observation pending.',
 hardware_access_by_operator_during_candidate=False,candidate_hardware_access=False,operator_implementation_feedback_sent_during_run=False,
 operator_observational_feedback_supplied_before_run=True,followups_started_for_current_series=2,current_invocation_reserved_seconds=5710,
 remaining_current_series_followup_seconds=5710.780999999959,remaining_seconds_is_pre_terminal_budget=True,remaining_current_series_followup_rounds=1,
 inherited_generated_outputs_removed=1434,source_cleanup_sha256=digest((RUN/'operator-source-preparation.json').read_bytes()),
 candidate_repository_is_separate=True,manifest_experiment_branch=m['execution']['branch'],local_candidate_branch_at_start='detached',
 prepared_local_base_commit=m['operator']['local_base_commit'],candidate_product_code_present_at_start=True,
 board_state='COM3 retains final Luna followup3 frozen app; no operator serial/flash during current Flash implementation.',board_artifact_run_id='20261007-codex-cli-gpt-6-luna-r01',
 user_requested_hold=False,user_hold_resumption_scope='User explicitly resumed AGY Flash remaining5710.781seconds and at most2 followups.',
 additional_candidate_round_start_authorized_now=True,additional_candidate_round_ready_now=False,next_model_start_authorized_now=False,next_model_execution_started=False,
 serial_closed=True,launch_snapshot=PUBLIC.relative_to(ROOT).as_posix(),
 restart_instruction='Read current manifest/shared Flash ledger/owner/launcher-child processes. Never relaunch a running attempt. Preserve terminal cost, restore globals, freeze and independently evaluate source/artifacts; then same-artifact COM3 observation. Remaining Flash followup3 only after reviewed round2 and actual remaining budget.')
save(path,p)
save(PUBLIC/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,'scope':'Launch snapshot, own feedback and immutable receipt evidence; historical progress preserved.',
 'files':{source.relative_to(extended(PUBLIC)).as_posix():{'sha256':digest(source.read_bytes()),'bytes':source.stat().st_size} for source in extended(PUBLIC).rglob('*') if source.is_file()}})
print(json.dumps({'run_id':RUN.name,'status':'running','round':2,'native_model':init['model'],'launch_files':len(read(PUBLIC/'snapshot-inventory.json')['files']),'native_pid':processes[0]['ProcessId']}))
