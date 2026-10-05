"""Preserve an immutable launch snapshot and advance only operator status."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT=Path.cwd();RUN=Path('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import digest,read,save
m=read(RUN/'run-manifest.json');assert m['operator']['status']=='running' and m['execution']['started_at']
ledger_path=Path(m['operator']['comparison']['ledger']);ledger=read(ledger_path)
assert len(ledger['runs'])==1 and ledger['runs'][0]['status']=='running'
previous=read(RUN/'previous-progress-at-transition.json')
assert previous['product_executions_started']==previous['product_executions_completed']==8
raw=(RUN/'stdout.jsonl').read_bytes();raw=raw[:raw.rfind(b'\n')+1]
events=[json.loads(line) for line in raw.splitlines()]
first=next(e for e in events if e.get('type')=='thread.started')
profile=read(RUN/'profile.json');argv=[s.replace('{checkout}',str(RUN/'checkout')).replace('{model}',profile['model']) for s in profile['argv']]
query="Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'codex.exe' -and $_.CommandLine -match 'gpt-6-sol' -and $_.CommandLine -match 'ignore-user-config' } | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Depth 2"
processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True,encoding='utf-8'))
processes=processes if isinstance(processes,list) else [processes]
assert len(processes)==1
assert processes[0]['CommandLine']==subprocess.list2cmdline(argv)
now=datetime.now(timezone.utc).isoformat()
save(RUN/'native-start-observation.json',{'run_id':RUN.name,'observed_at':now,'status':'running',
    'native_thread_id':first['thread_id'],'explicit_profile_model':profile['model'],'explicit_reasoning':profile['reasoning'],
    'actual_native_process_pid':processes[0]['ProcessId'],'actual_process_argv_matches_frozen_profile':True,
    'raw_log_prefix_events':len(events),'raw_log_prefix_bytes':len(raw),'raw_log_prefix_sha256':digest(raw),
    'effective_model_emitted_by_jsonl':False,'effective_model_verified':None,'effective_cwd_emitted_by_jsonl':False,
    'scope':'Native thread and actual process command line only. JSONL does not emit the resolved model or cwd; runner Popen cwd and explicit argv are preserved. No completion or product claim.'})
save(RUN/'process-at-start.json',{'captured_at':now,'processes':processes,'expected_argv':argv,
    'runner_cwd':m['execution']['worktree'],'explicit_permission_arguments':['--ask-for-approval','never','--sandbox','workspace-write','windows.sandbox="elevated"']})
(RUN/'native-start-observation-prefix.jsonl').write_bytes(raw)
launch=read(RUN/'experiment-launch.json');public=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'launch-20261005'
public.mkdir(parents=True,exist_ok=False)
names=['experiment-launch.json','run-manifest.json','profile.json','candidate-inputs.json','agent-context.json','prompt.txt','execution-preflight.json',
       'operator-next-model-decision.json','native-start-observation.json','native-start-observation-prefix.jsonl','process-at-start.json','previous-progress-at-transition.json']
names += [p.relative_to(RUN).as_posix() for p in (RUN/'operator-launch-preflight').rglob('*') if p.is_file()]
for name in names:
    dest=public/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
shutil.copy2(ledger_path,public/'ledger-at-start.json')
for path in [RUN.parent/'launch-codex-sol-r01.py',RUN.parent/'launch-codex-sol-r01.ps1',Path(__file__)]:shutil.copy2(path,public/path.name)
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,
    'files':{p.relative_to(public).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in public.rglob('*') if p.is_file()},
    'scope':'Immutable first-run start snapshot. Thread and process argv are observed; product implementation/evaluation remain pending. Previous Pro closure and Flash deferred budget retained.'})
p={'checked_at':now,'baseline_commit':previous['baseline_commit'],'block':1,'seed':1,'active_models':5,
   'independent_series_planned':15,'independent_series_completed':2,'initial_series_started':4,'followups_started':5,
   'product_executions_started':9,'product_executions_completed':8,'state':'codex_sol_initial_running',
   'current_run':RUN.name,'current_directory':str(RUN),'ledger':str(ledger_path),'round':0,'model':'gpt-6-sol','reasoning':'medium',
   'started_at':m['execution']['started_at'],'ended_at':None,'timeout_seconds':7200,'launcher_pid':launch['launcher_pid'],
   'native_candidate_pid':processes[0]['ProcessId'],'native_thread_id':first['thread_id'],
   'profile_sha256':m['execution']['profile_sha256'],'input_bundle_sha256':m['execution']['input_bundle_sha256'],
   'receipt_sha256':digest((RUN/'execution-preflight.json').read_bytes()),'policy_review_required':True,'policy_status':'pending_terminal_review',
   'rm_review':'awaiting_candidate_terminal','elapsed_seconds':None,'tokens':m['measurement']['tokens'],
   'candidate_terminal_status_observed':'running','ongoing_usage_not_terminal':True,
   'candidate_current_phase':'Independent initial implementation running; source, final submission, product and reference evaluation pending.',
   'user_interventions_reported':None,'hardware_access_by_operator_during_candidate':False,'candidate_hardware_access':False,
   'operator_implementation_feedback_sent_during_run':False,'operator_observational_feedback_supplied_before_run':False,
   'followups_started_for_current_series':0,'remaining_current_series_followup_seconds':7200,'remaining_current_series_followup_rounds':3,
   'actual_process_argv_matches_frozen_profile':True,'native_model_verified':None,
   'native_model_verification_note':'Actual process has explicit -m gpt-6-sol and medium; Codex JSONL emits thread ID but not resolved model/cwd.',
   'current_native_scope':'Ephemeral exec with frozen ignore-user-config/rules and native feature/skill overrides; no global settings mutation.',
   'board_state':'Existing evaluated Flash r02 artifact retained; no Codex upload or serial during candidate implementation.',
   'previous_series':previous['previous_series'],'closed_agy_pro_series':previous['current_series_completion'],
   'deferred_agy_flash_series':previous['deferred_agy_flash_series'],'user_requested_hold':False,
   'user_hold_resumption_scope':'User proceeds to Codex Sol series under the existing comparison contract; Pro remains closed and Flash remains deferred.',
   'next_model':'codex-luna','next_model_execution_started':False,'next_model_start_authorized_now':False,
   'additional_candidate_round_start_authorized_now':False,'launch_operator_errors_before_model':0,'operator_preflight_error_model_calls':0,
   'launch_snapshot':public.relative_to(ROOT).as_posix(),
   'restart_instruction':'Read Codex Sol manifest, ledger and actual launcher/candidate processes before any action; never repeat a running or terminal initial invocation. Freeze source and raw cost after terminal, then evaluate and upload only a genuine ESP32 artifact. Pro round limit and Flash original budgets remain retained.'}
save(ROOT/'results/formal-comparison-20261004/progress.json',p)
print(json.dumps({'run_id':RUN.name,'status':'running','started_at':m['execution']['started_at'],
    'native_thread_id':first['thread_id'],'native_candidate_pid':processes[0]['ProcessId'],'actual_argv_matches':True,
    'launch_snapshot_files':len(read(public/'snapshot-inventory.json')['files'])}))
