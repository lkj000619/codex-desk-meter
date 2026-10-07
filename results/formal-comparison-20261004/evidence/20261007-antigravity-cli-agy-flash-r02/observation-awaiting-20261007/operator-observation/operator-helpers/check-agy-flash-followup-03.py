"""Repeat submitted/fresh host checks and actual collector from unmodified frozen source."""
from datetime import datetime,timezone
from pathlib import Path
import importlib.util,json,os,subprocess,sys,time
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02')
CO=RUN/'checkout';OUT=RUN/'operator-observation';HOST=Path('C:/meter-host-evaluations-20261007/agy-flash-followup03')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
original=read(OUT/'terminal-verification.json')
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
assert not f['firmware_source_mutations_after_last_build']
sys.pycache_prefix=str(OUT/'unused-bytecode-cache')
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPYCACHEPREFIX']=str(OUT/'unused-bytecode-cache');checks=[]
def check(name,args,cwd=CO,timeout=120,check_env=env):
    start=time.monotonic();p=subprocess.run([str(a) for a in args],cwd=cwd,env=check_env,capture_output=True,timeout=timeout)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    checks.append({'name':name,'argv':[str(a) for a in args],'cwd':str(cwd),'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start})
    print(json.dumps({'check':name,'exit_code':p.returncode}),flush=True)
    return p
check('submitted-result-validator',[sys.executable,'-B','-X','utf8',BASE/'scripts/validate-end-to-end-result.py',
    '--result',CO/m['outputs']['structured_result'],'--manifest',CO/'.benchmark-inputs/e2e-evaluation-manifest.json','--evidence-root',CO])
check('python-tests',[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-v'])
for name in ('test_meter_parser','test_meter_state','test_feature_imu','test_gui_regression'):
    check('submitted-'+name,[CO/'build-host'/(name+'.exe')])

assert not HOST.exists();HOST.mkdir(parents=True)
host_env=env.copy();host_env.pop('IDF_TARGET',None);host_env.pop('CMAKE_TOOLCHAIN_FILE',None)
cc=Path('C:/Espressif/benchmark-host-tools/llvm-mingw-20260616-ucrt-x86_64/bin/cc.exe')
host_env['PATH']=str(cc.parent)+os.pathsep+host_env['PATH']
configured=check('fresh-host-configure',['cmake','-S',CO,'-B',HOST,'-G','Ninja',
    '-DCMAKE_C_COMPILER='+cc.as_posix(),'-DCMAKE_CXX_COMPILER='+(cc.parent/'c++.exe').as_posix()],check_env=host_env)
if configured.returncode==0:
    built=check('fresh-host-build',['cmake','--build',HOST],check_env=host_env)
    if built.returncode==0:
        check('fresh-host-ctest',['ctest','--test-dir',HOST,'--output-on-failure'],check_env=host_env)
        new_ctest=(HOST/'CTestTestfile.cmake').read_text(encoding='utf-8')
        assert '20261007-antigravity-cli-agy-flash-r01' not in new_ctest and str(HOST).replace('\\','/') in new_ctest
save(OUT/'host-checks.json',{'run_id':RUN.name,'implementation_commit':f['commit'],'checks':checks,
    'fresh_host_build_directory':str(HOST),'host_compiler_same_as_candidate':True,
    'submitted_ctest_points_to_current_checkout':True,
    'fresh_host_test_scope':'Operator host-only build from unmodified frozen current source; preserves submitted binaries/cache/log and does not repair candidate submission or policy verdict.',
    'operator_firmware_rebuild':False})

spec=importlib.util.spec_from_file_location('candidate_pc_collector_sender',CO/'scripts/pc_collector_sender.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
reference=BASE/'experiments/reference/codex-7923f96';raws=(reference/'expected-frames.jsonl').read_bytes().splitlines(keepends=True)
frames=[json.loads(raw) for raw in raws];encoder=[]
for wire,frame in zip(raws,frames):
    generated=module.encode_frame(module.build_frame(frame['payload'],sequence=frame['sequence'],sent_at=frame['sent_at']))
    encoder.append({'sequence':frame['sequence'],'matches_common_wire':generated==wire,'sha256':digest(generated)})
collectors={}
for mode in (False,True):
    label='legacy' if mode else 'default'
    try:
        sender=module.PcCollectorSender(device_alias='operator-common-'+label,state_dir=OUT/('sender-state-'+label),
            reference_time='2026-09-30T18:40:49Z',use_legacy=mode)
        actual,line=sender.collect_and_build(0,sent_at=frames[0]['sent_at'])
        save(OUT/('candidate-collector-'+label+'-frame.json'),actual)
        (OUT/('candidate-collector-'+label+'-frame.jsonl')).write_bytes(line)
        collectors[label]={'status':'built','frame_sha256':digest(line),'matches_common_payload':actual['payload']==frames[0]['payload'],
            'matches_common_wire':line==raws[0],'usage_entries':len(actual['payload']['usage']),'reset_entries':len(actual['payload']['global_resets'])}
    except Exception as e:
        collectors[label]={'status':'failed','error_type':type(e).__name__,'error':str(e),'code':getattr(e,'code',None)}
save(OUT/'common-stimulus-check.json',{'run_id':RUN.name,'implementation_commit':f['commit'],
    'reference_frames_sha256':digest((reference/'expected-frames.jsonl').read_bytes()),'candidate_encoder_checks':encoder,
    'actual_collector_api_modes':collectors,'collector_source_sha256':digest((CO/'scripts/pc_collector_sender.py').read_bytes()),
    'scope':'Unmodified candidate default and declared legacy modes at fixed reference UTC. Do not substitute encoder-only match for actual collector match or physical receipt.'})
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert digest(Path(m['operator']['comparison']['ledger']).read_bytes())==original['original_ledger_sha256']
print(json.dumps({'policy_status':'eligible','checks':checks,'collectors':collectors,'encoder':encoder,
    'source_and_inputs_unchanged':True,'firmware_provenance_review':'current_checkout'},ensure_ascii=False))
