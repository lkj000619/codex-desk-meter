"""Preserve a terminal candidate before operator evaluation; no product edits."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
CO=RUN/'checkout'
OUT=RUN/'operator-observation'
LEDGER=RUN.parent/'ledgers'/f'{RUN.name}.json'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from operator_baseline import verify
from agy_pilot_environment import paths_for,owner_path

m=read(RUN/'run-manifest.json'); ledger=read(LEDGER)
assert m['operator']['status']=='environment_failed' and m['execution']['ended_at']
terminal_hash=digest((RUN/'run-manifest.json').read_bytes())
assert terminal_hash==ledger['runs'][-1]['terminal_manifest_sha256']=='c41ee83fecbdd890547f777d5d562b320675cdf4b4e5d8b6331e3e29b0f13961'
assert not ledger['runs'][-1]['reviewed']
processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',
    'ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -in 19644,16120,21368,12900 -or $_.Name -match "^agy(\\.exe)?$|^opencode(\\.exe)?$" } | Select-Object ProcessId,Name,CommandLine)'],text=True))
candidate_processes=[p for p in processes if p['Name'].lower() in {'agy','agy.exe','opencode','opencode.exe'}
                     or RUN.name in (p.get('CommandLine') or '')]
assert candidate_processes==[],candidate_processes
gemini=Path.home()/'.gemini'
actual={k:digest(p.read_bytes()) if p.is_file() else None for k,p in paths_for(gemini).items()}
scope=read(RUN/'operator-launch-preflight-r2/scope-exit.json')
assert actual==scope['before_sha256']==scope['after_sha256']
assert not owner_path(gemini).exists()
benchmark.verify_agent_inputs(RUN,m); verify_evidence(m,RUN); verify(m,RUN)
assert benchmark.git('rev-parse','HEAD',cwd=BASE)==m['execution']['base_commit']
OUT.mkdir(exist_ok=False)
preserved=OUT/'terminal-originals';preserved.mkdir()
for p in (RUN/'run-manifest.json',LEDGER,RUN/'stdout.jsonl',RUN/'stderr.txt',RUN/'command-audit.json'):
    shutil.copy2(p,preserved/p.name)
save(OUT/'terminal-verification.json',{'run_id':RUN.name,'checked_at':datetime.now(timezone.utc).isoformat(),
    'candidate_processes_remaining':candidate_processes,'historical_pids_current_observations':processes,
    'pid_reuse_note':'Historical PID 19644 is now svchost.exe; PID alone is not candidate liveness.',
    'global_files_sha256':actual,'original_global_bytes_restored':True,
    'owner_journal_present':False,'original_terminal_manifest_sha256':terminal_hash,
    'original_ledger_sha256':digest(LEDGER.read_bytes()),'immutable_input_files_verified':57,
    'frozen_operator_baseline_verified':True,'terminal_status':m['operator']['status'],
    'execution':m['execution'],'measurement':m['measurement'],
    'candidate_result_submission_present':(CO/m['outputs']['structured_result']).is_file(),
    'candidate_selection_document_present':(CO/m['outputs']['selection_document']).is_file()})
names=['build/meter_esp32s3.bin','build/meter_esp32s3.elf','build/meter_esp32s3.map',
       'build/bootloader/bootloader.bin','build/bootloader/bootloader.elf','build/bootloader/bootloader.map',
       'build/partition_table/partition-table.bin','build/flasher_args.json','sdkconfig','sdkconfig.defaults']
artifacts={}
for name in names:
    p=CO/name;dest=OUT/'artifact-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    artifacts[name]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes()),'operator_raw_copy':dest.relative_to(RUN).as_posix()}
fixed=set(read(RUN/'candidate-inputs.json')['files'])
sources={}
for p in CO.rglob('*'):
    rel=p.relative_to(CO)
    if not p.is_file() or any(x in {'.git','.benchmark-inputs','build','build-host','__pycache__'} for x in rel.parts): continue
    name=rel.as_posix()
    if name in fixed:continue
    dest=OUT/'source-snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    sources[name]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes()),'operator_raw_copy':dest.relative_to(RUN).as_posix()}
benchmark.git('add','--all',cwd=CO)
if benchmark.git('diff','--cached','--name-only',cwd=CO):
    benchmark.git('-c','user.name=Benchmark','-c','user.email=benchmark@localhost','commit','-m','Freeze '+RUN.name,cwd=CO)
commit=benchmark.git('rev-parse','HEAD',cwd=CO)
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.git('bundle','create',str(RUN/'operator-terminal-source.bundle'),'HEAD',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
assert digest((RUN/'run-manifest.json').read_bytes())==terminal_hash
assert digest(LEDGER.read_bytes())==read(OUT/'terminal-verification.json')['original_ledger_sha256']
artifact_post={name:digest((CO/name).read_bytes())==metadata['sha256'] for name,metadata in artifacts.items()}
assert all(artifact_post.values())
save(RUN/'operator-source-freeze.json',{'run_id':RUN.name,'frozen_at':datetime.now(timezone.utc).isoformat(),
    'commit':commit,'candidate_branch':benchmark.git('branch','--show-current',cwd=CO),'separate_repository':True,
    'original_terminal_manifest_sha256':terminal_hash,'terminal_manifest_unchanged':True,'original_ledger_unchanged':True,
    'source_bundle':'operator-terminal-source.bundle','source_bundle_sha256':digest((RUN/'operator-terminal-source.bundle').read_bytes()),
    'artifacts':artifacts,'sources':sources,'artifact_bytes_unchanged_after_git_freeze':artifact_post,
    'operator_product_source_modifications':False,'operator_firmware_rebuild':False,
    'candidate_result_submission_missing':True,'candidate_selection_document_present':True,
    'scope':'Post-terminal freeze of candidate files with pre-Git raw bytes retained; reference review not applied.'})
print(json.dumps({'frozen_commit':commit,'artifacts':len(artifacts),'source_files':len(sources),
    'app_sha256':artifacts['build/meter_esp32s3.bin']['sha256'],'original_terminal_and_ledger_unchanged':True}))
