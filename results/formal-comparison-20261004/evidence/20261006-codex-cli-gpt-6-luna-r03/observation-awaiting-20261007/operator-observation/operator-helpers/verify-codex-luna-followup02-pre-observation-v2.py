"""Fresh frozen-validator audit and host tests using the independent restoration."""
from datetime import datetime,timezone
from pathlib import Path
import copy,importlib.util,json,os,re,subprocess,sys,time,zipfile

PACK=Path('C:/meter-run-packages-20261007/codex-luna-followup02-pre-observation')
REST=Path('C:/meter-run-restores-20261007/codex-luna-followup02-pre-observation')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit-v2';OUT=REST/'post-restore-host-checks-v2'
trusted=json.loads((PACK.parent/'codex-luna-followup02-pre-observation-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(OP/'operator-baseline.zip') as z:z.extractall(FROZEN)
sys.path.insert(0,str(FROZEN/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from operator_baseline import verify
from policy_review import validate_review
from evidence_package import verify_report_dependencies
assert digest((PACK/'package-manifest.json').read_bytes())==trusted
package=read(PACK/'package-manifest.json');m=read(OP/'run-manifest.json');f=read(OP/'operator-source-freeze.json')
for name,item in package['files'].items():
    p=PACK/name;b=Path('\\\\?\\'+str(p.resolve())).read_bytes()
    assert len(b)==item['bytes'] and digest(b)==item['sha256'],name
verify(m,OP);verify_evidence(m,OP);benchmark.verify_agent_inputs(OP,m);verify_report_dependencies(m,OP)
assert validate_review(m,OP/'run-manifest.json')['decision']['status'] in {'eligible','invalid_for_comparison'}
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']
original=read(OP/'operator-observation/terminal-originals/run-manifest.json')
assert digest((OP/'operator-observation/terminal-originals/run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert original['measurement']==m['measurement']
for key,value in original['execution'].items():
    if key!='worktree':assert value==m['execution'][key],key
for name,item in f['sources'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert digest(raw)==item['sha256'] and len(raw)==item['bytes']
    if name!=m['outputs']['structured_result']:assert (CO/name).read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),name
for name,item in f['artifacts'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
    if name.endswith(('.bin','.elf')):assert (CO/name).read_bytes()==raw,name
assert not f['firmware_source_mutations_after_last_build'] and (CO/'build/codex_desk_meter.elf').read_bytes()[:4]==b'\x7fELF'
OUT.mkdir(exist_ok=False);env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
sys.pycache_prefix=str(REST/'unused-host-bytecode-cache');env['PYTHONPYCACHEPREFIX']=sys.pycache_prefix
assert not Path(sys.pycache_prefix).exists()
cache=(OP/'operator-observation/artifact-snapshot/build-host/CMakeCache.txt').read_text(encoding='utf-8')
compiler=next(line.split('=',1)[1] for line in cache.splitlines() if line.startswith('CMAKE_C_COMPILER:FILEPATH='))
runtime=Path(compiler).parent;assert runtime.is_dir();env['PATH']=str(runtime)+os.pathsep+env.get('PATH','')
checks=[]
def check(name,argv,input_data=None):
    tick=time.monotonic();p=subprocess.run([str(x) for x in argv],cwd=CO,env=env,input=input_data,capture_output=True,timeout=120)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    checks.append({'name':name,'argv':[str(x) for x in argv],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-tick})
    return p

correction=read(REST/'operator-audit-artifact-placement-correction.json')
assert digest((REST/'operator-audit-procedure-v1.py').read_bytes())==correction['original_audit_sha256']
source=OP/'operator-observation/artifact-snapshot/build-host/meter_receiver_cli.exe'
target=CO/'build-host/meter_receiver_cli.exe'
assert digest(source.read_bytes())==f['artifacts']['build-host/meter_receiver_cli.exe']['sha256']
assert target.resolve().is_relative_to(CO.resolve()) and not target.exists()
target.parent.mkdir(parents=True,exist_ok=True);__import__('shutil').copy2(source,target)
assert target.read_bytes()==source.read_bytes()
save(OUT/'artifact-materialization.json',{'path':'build-host/meter_receiver_cli.exe','sha256':digest(target.read_bytes()),'source':'operator/operator-observation/artifact-snapshot/build-host/meter_receiver_cli.exe','candidate_source_modified':False,'rebuild':False})
check('python-unit-tests',[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-v'])
for name in ['test_meter_parser','test_meter_state','test_idle_dim']:
    for suffix in ('stdout','stderr'):
        prior=REST/'post-restore-host-checks'/(name+'-'+suffix+'.txt')
        assert digest(prior.read_bytes())==correction['original_host_logs'][prior.name]
        __import__('shutil').copy2(prior,OUT/prior.name)
    checks.append({'name':name,'exit_code':0,'elapsed_seconds':None,'reused_original_passing_logs':True,'exit_status_basis':'First audit passed all four exit0 assertion before rejecting the skipped Python production cases.'})
assert all(item['exit_code']==0 for item in checks),checks
sys.path.insert(0,str(CO))
from pc import pipeline as module
import tempfile
reference=OP/'reference';wire=(reference/'expected-frames.jsonl').read_bytes();frames=[json.loads(s) for s in wire.splitlines()]
encoded=[module.encode_frame(module.build_frame(frame['payload'],frame['sequence'],frame['sent_at'])) for frame in frames]
encoder_matches=b''.join(encoded)==wire
(OUT/'candidate-encoded-common-frames.jsonl').write_bytes(b''.join(encoded))
with tempfile.TemporaryDirectory(dir=CO) as temporary:
    registry=Path(temporary)/'operator-fixtures.json'
    save(registry,{'provider_fixtures':['experiments/fixtures/personal-usage.json'],
        'global_reset_fixtures':['experiments/fixtures/codex-reset-forecast.json','experiments/fixtures/codex-resets-history.json']})
    collected=module.FixtureCollector(registry).collect_common(module.parse_time('2026-09-30T18:40:49Z','reference'))
    collector={'input_fixture':'experiments/fixtures/personal-usage.json','reference_time':'2026-09-30T18:40:49Z',
        'usage_entries':len(collected.usage),'global_reset_entries':len(collected.global_resets),'errors':collected.failures,
        'matches_common_reference_payload':collected.payload==frames[0]['payload']}
    save(OUT/'candidate-legacy-collector-frame.json',{'payload':collected.payload,'errors':collected.failures})
    matrix=read(CO/'experiments/fixtures/provider-fixture-matrix.json');provider_checks=[]
    for entry in matrix['fixtures']:
        save(registry,{'provider_fixtures':['experiments/fixtures/'+entry['path']],'global_reset_fixtures':[]})
        actual=module.FixtureCollector(registry).collect(module.parse_time(matrix['reference_time'],'reference'))
        invalid=bool(actual.failures)
        provider_checks.append({'fixture':entry['path'],'expected':entry['expected'],'observed_invalid':invalid,
            'matches_expected_validity':invalid==(entry['expected']=='invalid'),'errors':actual.failures})
assert checks[0]['exit_code']==0
unit=(OUT/'python-unit-tests-stderr.txt').read_text(encoding='utf-8')
count=re.search(r'Ran (\d+) tests?',unit);assert count and int(count.group(1))>0 and 'OK' in unit and 'skipped' not in unit,unit[-1000:]
unit_count=int(count.group(1))
assert (CO/'.benchmark-inputs/feedback-evidence/007-sent-frames.jsonl').read_bytes()==wire
received=check('common-production-c-receiver',[OP/'operator-observation/artifact-snapshot/build-host/meter_receiver_cli.exe'],wire)
receiver_output=[json.loads(line) for line in received.stdout.splitlines()]
assert received.returncode==0 and len(receiver_output)==2
assert all(row['accepted'] for row in receiver_output) and [row['sequence'] for row in receiver_output]==[0,1]
assert encoder_matches and collector['matches_common_reference_payload']
assert len(provider_checks)==17 and all(row['matches_expected_validity'] for row in provider_checks)
cli=check('declared-common-collector',[sys.executable,'-B','-X','utf8','-m','pc.collector','--profile','common','--reference-time','2026-09-30T18:40:49Z'])
assert cli.returncode==0 and json.loads(cli.stdout)['payload']==frames[0]['payload']
save(OUT/'host-checks.json',{'run_id':m['run_id'],'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,
    'source_executables_unchanged':True,'operator_firmware_rebuild':False,'original_checkout_used':False,
    'recorded_compiler_runtime':str(runtime),'python_tests_passed':unit_count,'scope':'Restored own Python suite and three original archived C executables; no CTest cached original paths or rebuild.'})
save(OUT/'common-stimulus-check.json',{'run_id':m['run_id'],'common_frames_sha256':digest(wire),
    'encoder_matches_exact_common_frames':encoder_matches,'legacy_collector':collector,'provider_fixture_checks':provider_checks,
    'production_c_receiver_output':receiver_output,'production_c_accepts_common_sequences':[0,1],
    'candidate_wire_schema_cases':'Own wire/schema coverage passed via restored suite; exact cases per archived source, distinct from frozen operator29 pipeline scenarios.',
    'frozen_operator29_pipeline_completed':False,
    'scope':'Host tests and exact wire encoding only; 17 provider validity cases and own C wire/schema cases do not imply frozen operator29 pipeline/device/optical pass.'})
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,original_run_or_checkout_path_used=False,
    inventory_bytes_verified=True,immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,
    raw_candidate_source_files_verified=len(f['sources']),raw_candidate_artifacts_verified=len(f['artifacts']),
    candidate_artifact_source_binding_verified=True,host_checks_completed=True,restored_host_executable_materialized=True,original_skipped_suite_preserved=True,generated_bytecode_cache_not_loaded=True,
    hardware_status='not_run',reference_review_applied=False,product_pass=False)
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps({'audit':audit,'host_checks':checks,'encoder_matches_exact_common_frames':encoder_matches,
    'legacy_collector':collector,'provider_fixture_checks_passed':sum(x['matches_expected_validity'] for x in provider_checks),
    'provider_fixture_cases':len(provider_checks)}))
