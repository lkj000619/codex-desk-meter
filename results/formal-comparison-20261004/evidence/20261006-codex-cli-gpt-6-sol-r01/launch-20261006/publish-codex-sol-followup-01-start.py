"""Preserve a start snapshot and advance operator status only."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,subprocess,sys
ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r01')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import digest,read,save
m=read(RUN/'run-manifest.json');assert m['operator']['status']=='running' and m['operator']['comparison']['round']==1
ledger_path=Path(m['operator']['comparison']['ledger']);ledger=read(ledger_path)
assert len(ledger['runs'])==2 and ledger['runs'][0]['reviewed'] and ledger['runs'][1]['status']=='running'
raw=(RUN/'stdout.jsonl').read_bytes();raw=raw[:raw.rfind(b'\n')+1]
events=[json.loads(s) for s in raw.splitlines()];first=next(e for e in events if e.get('type')=='thread.started')
profile=read(RUN/'profile.json');argv=[s.replace('{checkout}',str(RUN/'checkout')).replace('{model}',profile['model']) for s in profile['argv']]
query="ConvertTo-Json -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'codex.exe' -and $_.CommandLine -match 'gpt-6-sol' -and $_.CommandLine -match 'ignore-user-config' } | Select-Object ProcessId,ParentProcessId,CommandLine)"
processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True,encoding='utf-8'))
assert len(processes)==1 and processes[0]['CommandLine']==subprocess.list2cmdline(argv)
now=datetime.now(timezone.utc).isoformat()
save(RUN/'native-start-observation.json',{'run_id':RUN.name,'round':1,'observed_at':now,'status':'running','native_thread_id':first['thread_id'],
    'native_candidate_pid':processes[0]['ProcessId'],'actual_process_argv_matches_frozen_profile':True,'explicit_model':'gpt-6-sol','explicit_reasoning':'medium',
    'effective_model_verified':None,'effective_model_cwd_emitted_by_jsonl':False,'raw_log_prefix_events':len(events),
    'raw_log_prefix_sha256':digest(raw),'scope':'Thread/actual argv/runner cwd only; no implementation or product completion claim.'})
save(RUN/'process-at-start.json',{'captured_at':now,'processes':processes,'expected_argv':argv,'runner_cwd':m['execution']['worktree']})
(RUN/'native-start-observation-prefix.jsonl').write_bytes(raw)
public=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'launch-20261006';public.mkdir(parents=True,exist_ok=False)
names=['run-manifest.json','profile.json','candidate-inputs.json','agent-context.json','prompt.txt','execution-preflight.json',
    'feedback.json','candidate-feedback.json','operator-generated-output-cleanup.json','experiment-launch.json',
    'operator-next-model-decision.json','previous-progress-at-transition.json','native-start-observation.json',
    'native-start-observation-prefix.jsonl','process-at-start.json']
names += [p.relative_to(RUN).as_posix() for d in ('feedback-evidence','operator-launch-preflight') for p in (RUN/d).rglob('*') if p.is_file()]
for name in names:
    dest=public/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
shutil.copy2(ledger_path,public/'ledger-at-start.json')
for name in ('prepare-codex-sol-followup-01.py','launch-codex-sol-followup-01.py','launch-codex-sol-followup-01.ps1','publish-codex-sol-followup-01-start.py'):
    shutil.copy2(RUN.parent/name,public/name)
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'round':1,'captured_at':now,
    'files':{p.relative_to(public).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in public.rglob('*') if p.is_file()},
    'scope':'Immutable own-source followup start snapshot; generated-output cleanup and source equivalence proof retained. Previous initial original verdict/cost/453-file package unchanged.'})
p=read(ROOT/'results/formal-comparison-20261004/progress.json');prior=dict(p)
assert p['state']=='codex_sol_initial_evaluated_followup_pending' and p['product_executions_started']==p['product_executions_completed']==9
p['current_series_first_result']={k:prior.get(k) for k in ('current_run','implementation_commit','elapsed_seconds','tokens','policy_status','reference_status','product_pass','rm_items','final_package_manifest_sha256','final_package_files_verified','final_package','final_restore','final_snapshot','hardware_artifact_sha256','video_sha256')}
for key in ('implementation_commit','final_package_manifest_sha256','final_package_files_verified','final_package','final_restore','final_snapshot','video_sha256','video_duration_seconds'):
    p.pop(key,None)
p.update(checked_at=now,state='codex_sol_followup_01_running',current_run=RUN.name,current_directory=str(RUN),round=1,
    product_executions_started=10,product_executions_completed=9,followups_started=6,started_at=m['execution']['started_at'],ended_at=None,
    launcher_pid=read(RUN/'experiment-launch.json')['launcher_pid'],native_candidate_pid=processes[0]['ProcessId'],native_thread_id=first['thread_id'],
    process_ids_are_historical=False,candidate_processes_remaining=[processes[0]['ProcessId']],policy_status='pending_terminal_review',rm_review='awaiting_candidate_terminal',
    reference_status='not_run',product_pass=None,rm_items=None,elapsed_seconds=None,tokens=m['measurement']['tokens'],
    candidate_terminal_status_observed='running',ongoing_usage_not_terminal=True,
    candidate_current_phase='Own-source followup implementation running. Current code/submission/cost/policy/product/RM pending; initial verdict retained separately.',
    followups_started_for_current_series=1,remaining_current_series_followup_seconds=7200,remaining_current_series_followup_rounds=2,
    current_invocation_reserved_seconds=7200,remaining_seconds_is_pre_terminal_budget=True,receipt_sha256=digest((RUN/'execution-preflight.json').read_bytes()),
    source_cleanup_sha256=digest((RUN/'operator-generated-output-cleanup.json').read_bytes()),inherited_generated_outputs_removed=1413,
    prepared_local_base_commit=m['operator']['local_base_commit'],manifest_experiment_branch=m['execution']['branch'],local_candidate_branch_at_start='detached',
    additional_candidate_round_start_authorized_now=False,additional_candidate_round_ready_now=False,
    launch_snapshot=public.relative_to(ROOT).as_posix(),
    restart_instruction='Followup round1 is running; read manifest/ledger/native thread/actual process before any action and never duplicate invocation. After terminal preserve source/raw costs, review policy and same-artifact host/hardware/RM, then subtract actual followup seconds. Initial original 453-file package/ref2257 preserved. Pro closed, Flash deferred, Luna unstarted.')
save(ROOT/'results/formal-comparison-20261004/progress.json',p)
print(json.dumps({'run_id':RUN.name,'round':1,'started_at':m['execution']['started_at'],'native_thread_id':first['thread_id'],
    'native_candidate_pid':processes[0]['ProcessId'],'actual_argv_matches':True,'snapshot_files':len(read(public/'snapshot-inventory.json')['files'])}))
