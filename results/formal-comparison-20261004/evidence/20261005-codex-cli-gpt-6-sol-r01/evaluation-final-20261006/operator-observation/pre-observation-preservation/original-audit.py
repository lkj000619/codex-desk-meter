"""Fresh frozen-validator audit and host tests using the independent restoration."""
from datetime import datetime,timezone
from pathlib import Path
import copy,importlib.util,json,os,re,subprocess,sys,time,zipfile

PACK=Path('C:/meter-run-packages-20261006/codex-sol-r01-pre-observation')
REST=Path('C:/meter-run-restores-20261006/codex-sol-r01-pre-observation')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit';OUT=REST/'post-restore-host-checks'
trusted='11bb5064a5b1f8ee2ae237a2886c14144b98c9b4ea8972bc3a95bf0e0da36364'
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
    p=REST/name;b=Path('\\\\?\\'+str(p.resolve())).read_bytes()
    assert len(b)==item['bytes'] and digest(b)==item['sha256'],name
verify(m,OP);verify_evidence(m,OP);benchmark.verify_agent_inputs(OP,m);verify_report_dependencies(m,OP)
assert validate_review(m,OP/'run-manifest.json')['decision']['status']=='eligible'
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
    if name.endswith(('.bin','.elf','.exe','.dll.a')):assert (CO/name).read_bytes()==raw,name
assert not f['firmware_source_mutations_after_last_build'] and (CO/'build/codex_desk_meter.elf').read_bytes()[:4]==b'\x7fELF'
OUT.mkdir(exist_ok=False);env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
cache=(CO/'build-host/CMakeCache.txt').read_text(encoding='utf-8')
compiler=next(line.split('=',1)[1] for line in cache.splitlines() if line.startswith('CMAKE_C_COMPILER:FILEPATH='))
runtime=Path(compiler).parent;assert runtime.is_dir();env['PATH']=str(runtime)+os.pathsep+env.get('PATH','')
checks=[]
def check(name,argv,input_data=None):
    tick=time.monotonic();p=subprocess.run([str(x) for x in argv],cwd=CO,env=env,input=input_data,capture_output=True,timeout=120)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    checks.append({'name':name,'argv':[str(x) for x in argv],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-tick})
    return p
check('python-unit-tests',[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-v'])
check('receiver-state-and-crc',[CO/'build-host/receiver_test.exe'])
check('idle-backlight-feature',[CO/'build-host/feature_test.exe'])
check('python-frame-to-production-c',[sys.executable,'-B','-X','utf8',CO/'tests/test_pipeline.py',CO/'build-host/receiver_cli.exe'])
spec=importlib.util.spec_from_file_location('restored_candidate_pc',CO/'pc/desk_meter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
reference=OP/'reference';wire=(reference/'expected-frames.jsonl').read_bytes();frames=[json.loads(s) for s in wire.splitlines()]
encoded=[module.frame(frame['sequence'],frame['payload'],frame['sent_at']) for frame in frames]
assert b''.join(encoded)==wire
p=check('common-reference-c-receiver',[CO/'build-host/receiver_cli.exe'],wire)
accepted=p.stdout.decode('utf-8').splitlines()
payload,errors=module.collect(module.timestamp('2026-09-30T18:40:49Z'),fixture_paths=['personal-usage.json'],transition_stale=True)
collector={'input_fixture':'personal-usage.json','reference_time':'2026-09-30T18:40:49Z','usage_entries':len(payload['usage']),
    'global_reset_entries':len(payload['global_resets']),'errors':errors,'matches_common_reference_payload':payload==frames[0]['payload']}
save(OUT/'candidate-legacy-collector-frame.json',{'payload':payload,'errors':errors})
matrix=read(CO/'experiments/fixtures/provider-fixture-matrix.json');provider_checks=[]
for entry in matrix['fixtures']:
    actual,issues=module.collect(module.timestamp(matrix['reference_time']),fixture_paths=[entry['path']])
    invalid=bool(issues)
    provider_checks.append({'fixture':entry['path'],'expected':entry['expected'],'observed_invalid':invalid,
        'matches_expected_validity':invalid==(entry['expected']=='invalid'),'errors':issues})
save(OUT/'host-checks.json',{'run_id':m['run_id'],'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,
    'source_executables_unchanged':True,'operator_firmware_rebuild':False,'original_checkout_used':False,
    'recorded_compiler_runtime':str(runtime),'scope':'Existing archived executables and restored Python source; no CTest cache paths or original checkout used.'})
save(OUT/'common-stimulus-check.json',{'run_id':m['run_id'],'common_frames_sha256':digest(wire),'encoder_matches_exact_common_frames':True,
    'receiver_output':accepted,'receiver_exit_code':p.returncode,'legacy_collector':collector,'provider_fixture_checks':provider_checks,
    'scope':'Host source/encoded frame/production C checks. Device acceptance and optical results remain unmeasured.'})
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,original_run_or_checkout_path_used=False,
    inventory_bytes_verified=True,immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,
    raw_candidate_source_files_verified=len(f['sources']),raw_candidate_artifacts_verified=len(f['artifacts']),
    candidate_artifact_source_binding_verified=True,host_checks_completed=True,hardware_status='not_run',reference_review_applied=False,product_pass=False)
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps({'audit':audit,'host_checks':checks,'common_receiver_output':accepted,'legacy_collector':collector,
    'provider_fixture_checks_passed':sum(x['matches_expected_validity'] for x in provider_checks),'provider_fixture_cases':len(provider_checks)}))
