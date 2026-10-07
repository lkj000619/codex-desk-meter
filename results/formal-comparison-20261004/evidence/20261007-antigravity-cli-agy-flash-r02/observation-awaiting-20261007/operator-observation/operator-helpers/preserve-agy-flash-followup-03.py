"""Post-terminal raw preservation and Git freeze; no product edits or rebuild."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02')
CO=RUN/'checkout';OUT=RUN/'operator-observation'
def extended(path): return Path('\\\\?\\'+str(path.resolve()))
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from operator_baseline import verify

m=read(RUN/'run-manifest.json');ledger_path=Path(m['operator']['comparison']['ledger']);ledger=read(ledger_path)
assert m['operator']['status'] in {'completed','timeout','aborted','environment_failed'} and m['execution']['ended_at']
terminal_hash=digest((RUN/'run-manifest.json').read_bytes())
assert terminal_hash==ledger['runs'][-1]['terminal_manifest_sha256'] and not ledger['runs'][-1]['reviewed']
q="ConvertTo-Json -InputObject @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'agy.exe' } | Select-Object ProcessId,ParentProcessId,CommandLine)"
assert json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',q],text=True,encoding='utf-8'))==[]
from agy_pilot_environment import paths_for,owner_path
gemini=Path.home()/'.gemini';scope=read(RUN/'operator-launch-preflight/scope-exit.json')
actual={k:digest(p.read_bytes()) if p.is_file() else None for k,p in paths_for(gemini).items()}
assert actual==scope['before_sha256']==scope['after_sha256'] and not owner_path(gemini).exists()
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert benchmark.git('rev-parse','HEAD',cwd=BASE)==m['execution']['base_commit'] and not benchmark.git('status','--porcelain',cwd=BASE)
OUT.mkdir(exist_ok=False);originals=OUT/'terminal-originals';originals.mkdir()
for p in (RUN/'run-manifest.json',ledger_path,RUN/'stdout.jsonl',RUN/'stderr.txt',RUN/'command-audit.json'):
    if p.is_file():shutil.copy2(p,originals/p.name)
fixed=set(read(RUN/'candidate-inputs.json')['files']);sources={};artifacts={}
for p in extended(CO).rglob('*'):
    rel=p.relative_to(extended(CO))
    if not p.is_file() or any(x in {'.git','.benchmark-inputs','build','build-idf','build-host','__pycache__'} for x in rel.parts) or rel.as_posix() in fixed:continue
    dest=extended(OUT/'source-snapshot'/rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    sources[rel.as_posix()]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes()),'operator_raw_copy':dest.relative_to(extended(RUN)).as_posix()}
flash=CO/'build/flasher_args.json';flash_data=read(flash) if flash.is_file() else None
names=set()
if flash_data:
    names.update('build/'+name.replace('\\','/') for name in flash_data['flash_files'].values())
    names.add('build/flasher_args.json')
    for p in (CO/'build').glob('*'):
        if p.is_file() and p.suffix in {'.elf','.map'}:names.add(p.relative_to(CO).as_posix())
for name in ('sdkconfig','sdkconfig.defaults','build/build.ninja','build/.ninja_log','build/.ninja_deps','build/CMakeCache.txt',
             'build-host/receiver_test.exe','build-host/CMakeCache.txt','build-host/build.ninja','build-host/.ninja_log','build-host/.ninja_deps'):
    if (CO/name).is_file():names.add(name)
for p in (CO/'build-host').glob('*'):
    if p.is_file() and (p.suffix=='.exe' or p.name.endswith('.dll.a')):names.add(p.relative_to(CO).as_posix())
for name in sorted(names):
    p=CO/name;dest=OUT/'artifact-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    artifacts[name]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes()),'operator_raw_copy':dest.relative_to(RUN).as_posix()}
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
tools={};success=[];mutations=[]
for i,e in enumerate(events,1):
    s=e.get('step_update',{});info=s.get('tool_info',{})
    if s.get('step_type')!='tool':continue
    t=tools.setdefault(s['step_index'],{})
    t['name']=s.get('tool_name') or info.get('name') or t.get('name')
    if info.get('parameters'):t['parameters']=info['parameters']
    params=t.get('parameters',{})
    if t['name']=='run_command' and s.get('state')=='DONE':
        command=params.get('CommandLine','');output=str(info.get('output',''))
        if 'idf.py' in command and 'build' in command and 'Project build complete' in output:success.append((i,command))
    if t['name'] in {'write_to_file','replace_file_content','multi_replace_file_content'} and s.get('state')=='ACTIVE':
        path=Path(params.get('TargetFile',params.get('AbsolutePath','')))
        assert path.is_relative_to(CO),str(path)
        rel=path.relative_to(CO)
        if rel.parts[0] in {'main','components'} or path.name in {'CMakeLists.txt','sdkconfig','sdkconfig.defaults'}:mutations.append({'line':i,'path':rel.as_posix()})
later=[x for x in mutations if not success or x['line']>success[-1][0]]
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
    'global_files_restored_independently_verified':True,'raw_native_events':len(events),'candidate_result_submission_present':(CO/m['outputs']['structured_result']).is_file(),
    'candidate_selection_document_present':(CO/m['outputs']['selection_document']).is_file(),
    'operator_audited_user_interventions':0,'operator_source_modifications':False,'operator_firmware_rebuild':False,'serial_opened':False})
save(RUN/'operator-source-freeze.json',{'run_id':RUN.name,'frozen_at':datetime.now(timezone.utc).isoformat(),'commit':commit,
    'candidate_branch':benchmark.git('branch','--show-current',cwd=CO),'separate_repository':True,
    'original_terminal_manifest_sha256':terminal_hash,'original_ledger_sha256':digest(ledger_path.read_bytes()),'terminal_manifest_unchanged':True,'original_ledger_unchanged':True,
    'source_bundle':'operator-terminal-source.bundle','source_bundle_sha256':digest((RUN/'operator-terminal-source.bundle').read_bytes()),
    'sources':sources,'artifacts':artifacts,'last_successful_firmware_build_raw_line':None if not success else success[-1][0],
    'firmware_source_mutations_after_last_build':later,'operator_product_source_modifications':False,'operator_firmware_rebuild':False})
print(json.dumps({'status':m['operator']['status'],'commit':commit,'source_files':len(sources),'artifacts':len(artifacts),
    'last_successful_firmware_build_line':None if not success else success[-1][0],'later_firmware_mutations':later,'raw_terminal_preserved':True}))
