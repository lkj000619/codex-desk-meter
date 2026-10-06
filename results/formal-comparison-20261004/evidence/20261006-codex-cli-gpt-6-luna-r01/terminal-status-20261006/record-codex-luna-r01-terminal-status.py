"""Record terminal status and raw submissions; do not evaluate, freeze, rebuild or upload."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys
ROOT=Path.cwd(); FORMAL=ROOT/'results/formal-comparison-20261004'
RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01'); CO=RUN/'checkout'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
import benchmark
from benchmark_support import read, save, digest, verify_evidence
from operator_baseline import verify
m=read(RUN/'run-manifest.json'); p=read(FORMAL/'progress.json')
ledger_path=Path(p['ledger']); ledger=read(ledger_path)
assert p['current_run']==RUN.name and p['state']=='codex_luna_initial_running'
assert m['operator']['status']=='completed' and m['operator']['exit_code']==0 and m['execution']['ended_at']
assert len(ledger['runs'])==1 and ledger['runs'][0]['status']=='completed' and not ledger['runs'][0]['reviewed']
assert digest((RUN/'run-manifest.json').read_bytes())==ledger['runs'][0]['terminal_manifest_sha256']
q="[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); ConvertTo-Json -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'codex.exe' -and $_.CommandLine -match 'gpt-6-luna' -and $_.CommandLine -match 'ignore-user-config' } | Select-Object ProcessId,ParentProcessId,CommandLine)"
assert json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',q],encoding='utf-8'))==[]
benchmark.verify_agent_inputs(RUN,m); verify_evidence(m,RUN); verify(m,RUN)
events=[json.loads(line) for line in (RUN/'stdout.jsonl').read_bytes().splitlines()]
assert events[-1]['type']=='turn.completed'
usage=events[-1]['usage']; assert usage['input_tokens']+usage['output_tokens']==m['measurement']['tokens']['total']==17413487
messages=[e['item']['text'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
result=read(CO/m['outputs']['structured_result'])
assert (CO/m['outputs']['selection_document']).is_file() and (CO/result['manifest']['path']).is_file()
app=CO/'build-idf/codex_desk_meter.bin'; app_sha=digest(app.read_bytes())
assert app_sha=='3af7fd933b743ea7b16ba02627617e3adb3be0d5273eb9deb184f1be9c9d51d6'
now=datetime.now(timezone.utc).isoformat(); public=FORMAL/'evidence'/RUN.name/'terminal-status-20261006'
public.mkdir(parents=True,exist_ok=False)
for name in ('run-manifest.json','stdout.jsonl','stderr.txt','command-audit.json','operator-launch-preflight/runner-exit.json'):
    source=RUN/name
    if source.exists():
        dest=public/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,dest)
shutil.copy2(ledger_path,public/'ledger-at-terminal.json')
for name in (m['outputs']['structured_result'],m['outputs']['selection_document'],result['manifest']['path'],
             f'docs/agent-runs/{RUN.name}/verification-record.md'):
    dest=public/'candidate-submission'/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(CO/name,dest)
save(public/'candidate-final-response.json',{'run_id':RUN.name,'candidate_message':messages[-1],
    'scope':'Candidate self-report only; no independent host/product/policy/RM review completed.'})
record={'run_id':RUN.name,'checked_at':now,'terminal_status':'completed','exit_code':0,
    'execution':m['execution'],'measurement':m['measurement'],'raw_native_events':len(events),
    'raw_reasoning_output_tokens':usage['reasoning_output_tokens'],'frozen_reasoning_output_tokens':m['measurement']['tokens']['reasoning'],
    'terminal_manifest_sha256':digest((RUN/'run-manifest.json').read_bytes()),'candidate_processes_remaining':[],
    'candidate_result_submission_present':True,'candidate_selection_document_present':True,
    'candidate_manifest_reference':result['manifest']['path'],'candidate_manifest_reference_present':True,
    'firmware_artifact_present':True,'firmware_bytes':app.stat().st_size,'firmware_sha256':app_sha,
    'candidate_reported_python_tests_passed':11,'candidate_reported_ctest_tests_passed':3,'candidate_submitted_product_pass':result['product_pass'],
    'source_freeze_complete':False,'independent_host_evaluation_complete':False,'formal_policy_review_complete':False,
    'rm_review_complete':False,'luna_hardware_upload_performed':False,'immutable_inputs_verified':57,
    'candidate_reported_shell_composition_exception':True,
    'operator_source_changes_rebuild_or_serial':False,
    'start_timestamp_note':'Final runner records01:10:26.660Z versus launch snapshot01:10:26.658Z;2ms difference preserved without rewriting original.',
    'scope':'Terminal cost and submission presence only. Existing raw manifest/ledger unchanged. Exit0 and candidate test reports are not product or comparison eligibility judgments.'}
save(public/'terminal-status.json',record)
shutil.copy2(Path(__file__),public/Path(__file__).name)
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,
    'files':{path.relative_to(public).as_posix():{'sha256':digest(path.read_bytes()),'bytes':path.stat().st_size} for path in public.rglob('*') if path.is_file()},
    'scope':'Immutable post-terminal raw status/submission/cost snapshot. Source freeze, independent evaluation and upload remain pending.'})
p.update(checked_at=now,state='codex_luna_initial_terminal_awaiting_evaluation',product_executions_completed=12,
    started_at=m['execution']['started_at'],ended_at=m['execution']['ended_at'],exit_code=0,
    elapsed_seconds=m['measurement']['wall_clock_seconds'],tokens=m['measurement']['tokens'],
    candidate_terminal_status_observed='completed',ongoing_usage_not_terminal=False,
    candidate_current_phase='Initial implementation/submission terminal. Result/selection and app present. Source freeze and independent policy/host/product/RM review pending; no Luna upload.',
    process_ids_are_historical=True,candidate_processes_remaining=[],policy_status='pending_terminal_review',rm_review='awaiting_post_terminal_evaluation',
    current_invocation_terminal_cost_available=True,raw_reasoning_output_tokens=usage['reasoning_output_tokens'],frozen_reasoning_output_tokens=None,
    candidate_result_submission_present=True,candidate_selection_document_present=True,candidate_manifest_reference_present=True,
    candidate_reported_python_tests_passed=11,candidate_reported_ctest_tests_passed=3,candidate_submitted_product_pass=False,
    firmware_artifact_present=True,firmware_artifact_sha256=app_sha,source_freeze_complete=False,independent_host_evaluation_complete=False,
    candidate_reported_shell_composition_exception=True,terminal_status_snapshot=public.relative_to(ROOT).as_posix(),
    launch_snapshot_started_at='2026-10-06T01:10:26.658Z',
    restart_instruction='Luna initial is terminal: do not replay. Preserve original terminal manifest and raw cost; freeze own source/artifacts and review policy/independent host/product/RM before any followup. Genuine app present but not uploaded. Candidate test claims and shell composition admission need independent review. Old Sol/Pro closure, Flash deferral and all prior snapshots unchanged.')
save(FORMAL/'progress.json',p)
print(json.dumps({'state':p['state'],'status':'completed','terminal_snapshot_files':len(read(public/'snapshot-inventory.json')['files']),
    'elapsed_seconds':p['elapsed_seconds'],'normalized_tokens':p['tokens']['total'],'firmware_sha256':app_sha,
    'formal_evaluation_complete':False,'hardware_uploaded':False}))
