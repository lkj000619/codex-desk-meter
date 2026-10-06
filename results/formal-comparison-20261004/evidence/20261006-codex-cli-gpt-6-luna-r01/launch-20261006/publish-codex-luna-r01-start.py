"""Preserve actual Luna start and advance operator state without candidate feedback."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys
ROOT=Path.cwd(); FORMAL=ROOT/'results/formal-comparison-20261004'
RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest
m=read(RUN/'run-manifest.json'); profile=read(RUN/'profile.json')
ledger_path=Path(m['operator']['comparison']['ledger']); ledger=read(ledger_path)
assert m['operator']['status']=='running' and m['execution']['started_at']
assert len(ledger['runs'])==1 and ledger['runs'][0]['status']=='running'
previous=read(RUN/'previous-progress-at-transition.json')
assert previous['state']=='codex_sol_series_closed_reference_reached_quality_ineligible'
assert previous['product_executions_started']==previous['product_executions_completed']==11
assert previous==read(FORMAL/'progress.json')
raw=(RUN/'stdout.jsonl').read_bytes(); raw=raw[:raw.rfind(b'\n')+1]
events=[json.loads(line) for line in raw.splitlines()]
first=next(e for e in events if e.get('type')=='thread.started')
argv=[s.replace('{checkout}',str(RUN/'checkout')).replace('{model}',profile['model']) for s in profile['argv']]
query="[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'codex.exe' -and $_.CommandLine -match 'gpt-6-luna' -and $_.CommandLine -match 'ignore-user-config' } | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Depth 2"
processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True,encoding='utf-8'))
processes=processes if isinstance(processes,list) else [processes]
assert len(processes)==1 and processes[0]['CommandLine']==subprocess.list2cmdline(argv)
now=datetime.now(timezone.utc).isoformat(); launch=read(RUN/'experiment-launch.json')
save(RUN/'native-start-observation.json',{'run_id':RUN.name,'observed_at':now,'status':'running',
    'native_thread_id':first['thread_id'],'explicit_profile_model':profile['model'],'explicit_reasoning':profile['reasoning'],
    'actual_native_process_pid':processes[0]['ProcessId'],'actual_process_argv_matches_frozen_profile':True,
    'raw_log_prefix_events':len(events),'raw_log_prefix_bytes':len(raw),'raw_log_prefix_sha256':digest(raw),
    'effective_model_emitted_by_jsonl':False,'effective_model_verified':None,'effective_cwd_emitted_by_jsonl':False,
    'scope':'Native thread and actual process command line only. Resolved model/cwd not emitted; explicit argv and runner cwd preserved. No completion or product claim.'})
save(RUN/'process-at-start.json',{'captured_at':now,'processes':processes,'expected_argv':argv,
    'runner_cwd':m['execution']['worktree'],'explicit_permission_arguments':['--ask-for-approval','never','--sandbox','workspace-write','windows.sandbox="elevated"']})
(RUN/'native-start-observation-prefix.jsonl').write_bytes(raw)
public=FORMAL/'evidence'/RUN.name/'launch-20261006'; public.mkdir(parents=True,exist_ok=False)
names=['experiment-launch.json','run-manifest.json','profile.json','candidate-inputs.json','agent-context.json','prompt.txt','execution-preflight.json',
       'operator-next-model-decision.json','native-start-observation.json','native-start-observation-prefix.jsonl','process-at-start.json','previous-progress-at-transition.json']
names += [path.relative_to(RUN).as_posix() for path in (RUN/'operator-launch-preflight').rglob('*') if path.is_file()]
for name in names:
    dest=public/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(RUN/name,dest)
shutil.copy2(ledger_path,public/'ledger-at-start.json')
for path in [RUN.parent/'luna-preparation.json',RUN.parent/'prepare-codex-luna-r01.py',RUN.parent/'make-luna-launcher.py',
             RUN.parent/'launch-codex-luna-r01.py',RUN.parent/'launch-codex-luna-r01.ps1',Path(__file__)]:
    shutil.copy2(path,public/path.name)
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,
    'files':{path.relative_to(public).as_posix():{'sha256':digest(path.read_bytes()),'bytes':path.stat().st_size} for path in public.rglob('*') if path.is_file()},
    'scope':'Immutable Luna first-run actual start snapshot. New dated isolated input repository; no previous implementation. Sol closure, Pro limit and Flash deferral preserved; implementation/evaluation pending.'})
p={'checked_at':now,'baseline_commit':previous['baseline_commit'],'block':1,'seed':1,'active_models':5,
   'independent_series_planned':15,'independent_series_completed':3,'initial_series_started':5,'followups_started':7,
   'product_executions_started':12,'product_executions_completed':11,'state':'codex_luna_initial_running',
   'current_run':RUN.name,'current_directory':str(RUN),'ledger':str(ledger_path),'round':0,'model':'gpt-6-luna','reasoning':'max',
   'started_at':m['execution']['started_at'],'ended_at':None,'timeout_seconds':7200,'launcher_pid':launch['launcher_pid'],
   'native_candidate_pid':processes[0]['ProcessId'],'native_thread_id':first['thread_id'],
   'profile_sha256':m['execution']['profile_sha256'],'input_bundle_sha256':m['execution']['input_bundle_sha256'],
   'receipt_sha256':digest((RUN/'execution-preflight.json').read_bytes()),'policy_review_required':True,'policy_status':'pending_terminal_review',
   'rm_review':'awaiting_candidate_terminal','elapsed_seconds':None,'tokens':m['measurement']['tokens'],
   'reference_status':'not_run','rm_items':None,'product_pass':None,
   'candidate_terminal_status_observed':'running','ongoing_usage_not_terminal':True,
   'candidate_current_phase':'Independent Luna initial implementation running; source/final submission/product/reference/policy review pending.',
   'user_interventions_reported':None,'hardware_access_by_operator_during_candidate':False,'candidate_hardware_access':False,
   'operator_implementation_feedback_sent_during_run':False,'operator_observational_feedback_supplied_before_run':False,
   'followups_started_for_current_series':0,'remaining_current_series_followup_seconds':7200,'remaining_current_series_followup_rounds':3,
   'actual_process_argv_matches_frozen_profile':True,'native_model_verified':None,
   'native_model_verification_note':'Actual process explicit -m gpt-6-luna and max; JSONL emits thread ID, not resolved model/cwd.',
   'current_native_scope':'Ephemeral exec with frozen ignore-user-config/rules and feature/skill overrides; no global settings mutation.',
   'candidate_repository_is_separate':True,'manifest_experiment_branch':m['execution']['branch'],
   'local_candidate_branch_at_start':read(RUN.parent/'luna-preparation.json')['local_branch'],
   'prepared_local_base_commit':m['operator']['local_base_commit'],'candidate_product_code_present_at_start':False,
   'board_state':previous['board_state'],'board_artifact_run_id':previous['board_artifact_run_id'],
   'board_state_is_prior_sol_observation':True,'luna_hardware_upload_performed':False,
   'previous_series':previous['previous_series'],'closed_agy_pro_series':previous['closed_agy_pro_series'],
   'deferred_agy_flash_series':previous['deferred_agy_flash_series'],'closed_codex_sol_series':previous['closed_codex_sol_series'],
   'codex_sol_result_at_transition':{key:previous[key] for key in ('current_series_first_result','current_series_previous_result','final_snapshot','final_package_manifest_sha256','final_package_files_verified','video_sha256','rm_items','policy_status','reference_status','product_pass','series_policy_correction_snapshot')},
   'user_requested_hold':False,'user_hold_resumption_scope':'User explicitly starts Luna only under frozen comparison contract; Sol/Pro closed and Flash deferred.',
   'next_model':None,'next_model_execution_started':False,'next_model_start_authorized_now':False,
   'additional_candidate_round_start_authorized_now':False,'launch_operator_errors_before_model':0,'operator_preflight_error_model_calls':0,
   'launch_snapshot':public.relative_to(ROOT).as_posix(),'cost_checkpoint':previous['cost_checkpoint'],
   'cost_checkpoint_covers_completed_invocations':11,'current_invocation_terminal_cost_available':False,
   'restart_instruction':'Read Luna manifest, ledger and actual process identity first. Never repeat initial invocation or send implementation feedback. Preserve raw cost and freeze source after terminal, then review policy/host/RM and upload only genuine frozen firmware. Sol closure, Pro limit, Flash budgets and old Luna reservations retained. Board currently records prior Sol observation only.'}
save(FORMAL/'progress.json',p)
print(json.dumps({'run_id':RUN.name,'status':'running','started_at':m['execution']['started_at'],
    'native_thread_id':first['thread_id'],'native_candidate_pid':processes[0]['ProcessId'],
    'actual_argv_matches':True,'launch_snapshot_files':len(read(public/'snapshot-inventory.json')['files'])}))
