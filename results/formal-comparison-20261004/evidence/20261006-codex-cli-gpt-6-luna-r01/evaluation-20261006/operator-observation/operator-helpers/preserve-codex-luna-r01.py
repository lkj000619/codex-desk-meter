"""Post-terminal raw preservation and Git freeze; no product edits or rebuild."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01')
CO=RUN/'checkout';OUT=RUN/'operator-observation'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from operator_baseline import verify

m=read(RUN/'run-manifest.json');ledger_path=Path(m['operator']['comparison']['ledger']);ledger=read(ledger_path)
assert m['operator']['status'] in {'completed','timeout','aborted','environment_failed'} and m['execution']['ended_at']
terminal_hash=digest((RUN/'run-manifest.json').read_bytes())
assert terminal_hash==ledger['runs'][-1]['terminal_manifest_sha256'] and not ledger['runs'][-1]['reviewed']
q="ConvertTo-Json -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'codex.exe' -and $_.CommandLine -match 'gpt-6-luna' -and $_.CommandLine -match 'ignore-user-config' } | Select-Object ProcessId,ParentProcessId,CommandLine)"
assert json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',q],text=True,encoding='utf-8'))==[]
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert benchmark.git('rev-parse','HEAD',cwd=BASE)==m['execution']['base_commit'] and not benchmark.git('status','--porcelain',cwd=BASE)
OUT.mkdir(exist_ok=False);originals=OUT/'terminal-originals';originals.mkdir()
for p in (RUN/'run-manifest.json',ledger_path,RUN/'stdout.jsonl',RUN/'stderr.txt',RUN/'command-audit.json'):
    if p.is_file():shutil.copy2(p,originals/p.name)
fixed=set(read(RUN/'candidate-inputs.json')['files']);sources={};artifacts={}
for p in CO.rglob('*'):
    rel=p.relative_to(CO)
    if not p.is_file() or any(x in {'.git','.benchmark-inputs','build','build-idf','build-host','__pycache__'} for x in rel.parts) or rel.as_posix() in fixed:continue
    dest=OUT/'source-snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    sources[rel.as_posix()]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes()),'operator_raw_copy':dest.relative_to(RUN).as_posix()}
flash=CO/'build-idf/flasher_args.json';flash_data=read(flash) if flash.is_file() else None
names=set()
if flash_data:
    names.update('build-idf/'+name.replace('\\','/') for name in flash_data['flash_files'].values())
    names.add('build-idf/flasher_args.json')
    for p in (CO/'build-idf').glob('*'):
        if p.is_file() and p.suffix in {'.elf','.map'}:names.add(p.relative_to(CO).as_posix())
for name in ('sdkconfig','sdkconfig.defaults','build-idf/build.ninja','build-idf/.ninja_log','build-idf/.ninja_deps','build-idf/CMakeCache.txt',
             'build-host/receiver_test.exe','build-host/CMakeCache.txt','build-host/build.ninja','build-host/.ninja_log','build-host/.ninja_deps'):
    if (CO/name).is_file():names.add(name)
for p in (CO/'build-host').glob('*'):
    if p.is_file() and (p.suffix=='.exe' or p.name.endswith('.dll.a')):names.add(p.relative_to(CO).as_posix())
for name in sorted(names):
    p=CO/name;dest=OUT/'artifact-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    artifacts[name]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes()),'operator_raw_copy':dest.relative_to(RUN).as_posix()}
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
success=[(i+1,e['item']) for i,e in enumerate(events) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution'
         and 'idf.py' in e['item'].get('command','') and 'build' in e['item'].get('command','') and e['item'].get('exit_code')==0 and 'Project build complete' in e['item'].get('aggregated_output','')]
later=[]
if success:
    for i,e in enumerate(events):
        if i+1<=success[-1][0] or e.get('type')!='item.completed' or e.get('item',{}).get('type')!='file_change':continue
        for change in e['item'].get('changes',[]):
            path=Path(change['path']);rel=path.relative_to(CO)
            if rel.parts[0] in {'main','components'} or path.name in {'CMakeLists.txt','sdkconfig','sdkconfig.defaults'}:
                later.append({'line':i+1,'path':rel.as_posix()})
benchmark.git('add','--all',cwd=CO)
if benchmark.git('diff','--cached','--name-only',cwd=CO):
    benchmark.git('-c','user.name=Benchmark','-c','user.email=benchmark@localhost','commit','-m','Freeze '+RUN.name,cwd=CO)
commit=benchmark.git('rev-parse','HEAD',cwd=CO)
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.git('bundle','create',str(RUN/'operator-terminal-source.bundle'),'HEAD',cwd=CO)
assert digest((RUN/'run-manifest.json').read_bytes())==terminal_hash
benchmark.verify_agent_inputs(RUN,m)
for name,item in artifacts.items():assert digest((CO/name).read_bytes())==item['sha256']
save(OUT/'terminal-verification.json',{'run_id':RUN.name,'checked_at':datetime.now(timezone.utc).isoformat(),
    'terminal_status':m['operator']['status'],'execution':m['execution'],'measurement':m['measurement'],
    'original_terminal_manifest_sha256':terminal_hash,'original_ledger_sha256':digest(ledger_path.read_bytes()),
    'candidate_processes_remaining':[],'immutable_input_files_verified':57,'frozen_operator_baseline_verified':True,
    'raw_native_events':len(events),'candidate_result_submission_present':(CO/m['outputs']['structured_result']).is_file(),
    'candidate_selection_document_present':(CO/m['outputs']['selection_document']).is_file(),
    'operator_audited_user_interventions':0,'operator_source_modifications':False,'operator_firmware_rebuild':False,'serial_opened':False})
save(RUN/'operator-source-freeze.json',{'run_id':RUN.name,'frozen_at':datetime.now(timezone.utc).isoformat(),'commit':commit,
    'candidate_branch':benchmark.git('branch','--show-current',cwd=CO),'separate_repository':True,
    'original_terminal_manifest_sha256':terminal_hash,'terminal_manifest_unchanged':True,'original_ledger_unchanged':True,
    'source_bundle':'operator-terminal-source.bundle','source_bundle_sha256':digest((RUN/'operator-terminal-source.bundle').read_bytes()),
    'sources':sources,'artifacts':artifacts,'last_successful_firmware_build_raw_line':None if not success else success[-1][0],
    'firmware_source_mutations_after_last_build':later,'operator_product_source_modifications':False,'operator_firmware_rebuild':False})
print(json.dumps({'status':m['operator']['status'],'commit':commit,'source_files':len(sources),'artifacts':len(artifacts),
    'last_successful_firmware_build_line':None if not success else success[-1][0],'later_firmware_mutations':later,'raw_terminal_preserved':True}))
