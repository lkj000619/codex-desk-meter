"""Freeze existing terminal bytes; no source fixes, builds, models or serial access."""
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys

BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02'); CO=RUN/'checkout'; OUT=RUN/'operator-observation'
LEDGER=Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-flash-r01.json')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest, read, save, verify_evidence
from operator_baseline import verify
from agy_pilot_environment import paths_for,owner_path

m=read(RUN/'run-manifest.json'); ledger=read(LEDGER)
original=read(OUT/'terminal-status.json'); snapshots=read(OUT/'terminal-byte-snapshots.json')
assert m['operator']['status']=='completed' and m['execution']['ended_at']
assert not ledger['runs'][-1]['reviewed']
assert not (RUN/'operator-source-freeze.json').exists()
assert digest((RUN/'run-manifest.json').read_bytes())==original['original_terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
assert digest(LEDGER.read_bytes())==original['original_ledger_sha256']
processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',
    'ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^agy(\\.exe)?$|^opencode(\\.exe)?$" } | Select-Object ProcessId,Name)'],text=True))
assert not processes
gemini=Path.home()/'.gemini'; scope=read(RUN/'operator-launch-preflight/scope-exit.json')
actual={k:digest(p.read_bytes()) if p.is_file() else None for k,p in paths_for(gemini).items()}
assert actual==scope['before_sha256']==scope['after_sha256']
assert not owner_path(gemini).exists()
benchmark.verify_agent_inputs(RUN,m); verify_evidence(m,RUN); verify(m,RUN)
for group in snapshots.values():
    for name,meta in group.items():
        assert digest((CO/name).read_bytes())==meta['sha256'],name
        assert digest((RUN/meta['path']).read_bytes())==meta['sha256'],name
benchmark.git('add','--all',cwd=CO)
if benchmark.git('diff','--cached','--name-only',cwd=CO):
    benchmark.git('-c','user.name=Benchmark','-c','user.email=benchmark@localhost','commit','-m','Freeze '+RUN.name,cwd=CO)
commit=benchmark.git('rev-parse','HEAD',cwd=CO)
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.git('bundle','create',str(RUN/'operator-terminal-source.bundle'),'HEAD',cwd=CO)
def convert(group):
    return {name:{'bytes':meta['bytes'],'sha256':meta['sha256'],'operator_raw_copy':meta['path']} for name,meta in group.items()}
post={name:digest((CO/name).read_bytes())==meta['sha256'] for name,meta in snapshots['artifacts'].items()}
assert all(post.values())
benchmark.verify_agent_inputs(RUN,m)
assert digest((RUN/'run-manifest.json').read_bytes())==original['original_terminal_manifest_sha256']
assert digest(LEDGER.read_bytes())==original['original_ledger_sha256']
save(RUN/'operator-source-freeze.json',{'run_id':RUN.name,'frozen_at':datetime.now(timezone.utc).isoformat(),
    'commit':commit,'candidate_branch':benchmark.git('branch','--show-current',cwd=CO),'separate_repository':True,
    'original_terminal_manifest_sha256':original['original_terminal_manifest_sha256'],
    'original_ledger_sha256':original['original_ledger_sha256'],'terminal_manifest_unchanged':True,'original_ledger_unchanged':True,
    'source_bundle':'operator-terminal-source.bundle','source_bundle_sha256':digest((RUN/'operator-terminal-source.bundle').read_bytes()),
    'artifacts':convert(snapshots['artifacts']),'sources':convert(snapshots['sources']),
    'artifact_bytes_unchanged_after_git_freeze':post,'operator_product_source_modifications':False,'operator_firmware_rebuild':False,
    'candidate_result_submission_missing':False,'candidate_selection_document_present':True,
    'scope':'Post-terminal Git freeze with previously preserved pre-Git raw source and artifact bytes retained; reference review pending.'})
print(json.dumps({'frozen_commit':commit,'source_files':len(snapshots['sources']),'artifact_files':len(snapshots['artifacts']),
    'app_sha256':snapshots['artifacts']['build/meter_esp32s3.bin']['sha256'],'original_manifest_and_ledger_unchanged':True}))
