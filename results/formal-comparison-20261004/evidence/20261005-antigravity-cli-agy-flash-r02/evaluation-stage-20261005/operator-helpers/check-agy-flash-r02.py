"""Independent terminal policy/source/host checks without candidate fixes or firmware rebuild."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import time

BASE=Path('C:/meter-operator-20261004'); RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
CO=RUN/'checkout'; OUT=RUN/'operator-observation'; HOST=Path('C:/meter-host-evaluations-20261005/agy-flash-r02')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save
from policy_review import create_review,validate_review

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');original=read(OUT/'terminal-status.json')
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
tools={};errors=[];mutations=[];builds=[];commands=[]
for line,e in enumerate(events,1):
    s=e.get('step_update',{});info=s.get('tool_info',{})
    if s.get('step_type')!='tool':continue
    step=s['step_index'];t=tools.setdefault(step,{'step_index':step,'first_line':line})
    t['name']=s.get('tool_name') or info.get('name') or t.get('name'); t['last_line']=line; t['last_state']=s['state']
    if info.get('parameters'):t['parameters']=info['parameters']
    params=t.get('parameters',{})
    if s['state']=='ERROR':errors.append({'line':line,'step_index':step,'name':t['name'],'parameters':params,'error':info.get('error')})
    if s['state']=='ACTIVE' and t['name'] in {'write_to_file','replace_file_content','multi_replace_file_content'}:
        path=params.get('TargetFile',params.get('AbsolutePath',''))
        mutations.append({'line':line,'step_index':step,'tool':t['name'],'path':path})
    if s['state']=='DONE' and t['name']=='run_command':
        cmd=params.get('CommandLine',''); output=info.get('output','')
        commands.append({'line':line,'step_index':step,'command':cmd,'output_sha256':digest(str(output).encode()),'output_tail':str(output)[-600:]})
        if cmd=='idf.py build':
            builds.append({'line':line,'step_index':step,'output_contains_build_complete':'Project build complete' in str(output),
                           'native_exit_code':None,'output_sha256':digest(str(output).encode()),'output_tail':str(output)[-900:]})
inventory=[]
for t in tools.values():
    if t['name'] in {'write_to_file','replace_file_content','multi_replace_file_content'}:
        p=t.get('parameters',{})
        t['parameters_sha256']=digest(json.dumps(p,ensure_ascii=False,sort_keys=True).encode())
        t['parameters']={k:v for k,v in p.items() if k in {'TargetFile','AbsolutePath','Overwrite','StartLine','EndLine'}}
    inventory.append(t)
external_views=[]
for t in inventory:
    if t['name']=='view_file':
        p=Path(t['parameters']['AbsolutePath'])
        if not p.is_relative_to(CO):external_views.append(t)
assert all(Path(x['path']).is_relative_to(CO) for x in mutations)
denials=[e for e in errors if any(s in str(e['error']).lower() for s in ['not permitted','denied by','permission denied','denied_actions'])]
assert not denials
assert len(errors)==3 and all('cannot find' in str(e['error']).lower() for e in errors)
ctest_text=(OUT/'build-path-observation/build-host/CTestTestfile.cmake').read_text(encoding='utf-8')
prev_name='20261005-antigravity-cli-agy-flash-r01'
assert ctest_text.count('add_test(')==4 and prev_name in ctest_text
ctest_commands=[c for c in commands if c['command']=='ctest --test-dir build-host --output-on-failure']
assert len(ctest_commands)==3
native_review={'run_id':RUN.name,'reviewed_at':datetime.now(timezone.utc).isoformat(),
    'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),'raw_events':len(events),'tools':inventory,
    'native_tool_count':len(inventory),'command_count':len(commands),'commands':commands,'errors':errors,
    'error_classification':'Three missing-file errors, not permission denials; continuing after these is not a stop-on-permission-denial violation.',
    'permission_denials_observed':denials,'all_explicit_mutation_paths_inside_own_checkout':True,
    'external_views':external_views,
    'external_view_context':'ESP-IDF sources and one system-generated log for task-259 of this same native conversation. No other model implementation was explicitly viewed.',
    'previous_checkout_access':{'ctest_commands':ctest_commands,'testfile':'build-path-observation/build-host/CTestTestfile.cmake',
        'observed_effect':'CTest executed four absolute r01 paths; a build using inherited absolute cache paths also changed r01 build-host/.ninja_log.',
        'inherited_cache_cause':'The followup clone included tracked build output with absolute prior-checkout paths. Scope failure is recorded without attributing intent or erasing harness responsibility.'},
    'operator_audited_user_interventions':0,'original_measurement_user_interventions':m['measurement']['user_interventions'],
    'intervention_basis':'No operator messages, implementation patch, manual approval or permission relaxation during the candidate session.',
    'policy_observation_limit':'Prompt-and-log; OS read isolation not enforced. Verdict covers captured native calls and inherited test/build path evidence.'}
save(OUT/'native-tool-review.json',native_review)
decision={'status':'invalid_for_comparison','reviewer':'Codex operator','user_interventions':0,
    'reason':'The followup explicitly restricts previous run directory access, but native CTest invoked four executables in r01 and a cache-driven host build touched its checkout. The tracked inherited build cache is a harness contribution. Preserve this attempt and its full cost, exclude its quality from identical-condition comparison; evaluate submitted product behavior separately.',
    'intervention_review':'Operator audited zero in-run human/source/permission interventions; original telemetry null remains unchanged. Scope invalidity is separate from candidate exit 0 and product quality.',
    'evidence':[{'path':p.relative_to(RUN).as_posix(),'sha256':digest(p.read_bytes())} for p in [
        OUT/'native-tool-review.json',OUT/'terminal-status.json',OUT/'build-path-observation/build-host/CTestTestfile.cmake']]}
save(RUN/'operator-policy-decision.json',decision)
assert not (RUN/'policy-review.json').exists()
create_review(RUN/'run-manifest.json',decision)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'

last=next(b for b in reversed(builds) if b['output_contains_build_complete'])
firmware_mutations=[x for x in mutations if Path(x['path']).suffix in {'.c','.h'} or Path(x['path']).name in {'CMakeLists.txt','sdkconfig','sdkconfig.defaults'}]
later=[x for x in firmware_mutations if x['line']>last['line']]
assert not later
description=read(CO/'build/project_description.json')
assert Path(description['project_path'])==CO and Path(description['build_dir'])==CO/'build'
compile_db=read(CO/'build/compile_commands.json')
own_firmware_units=[x for x in compile_db if Path(x['file']).is_relative_to(CO) and not Path(x['file']).is_relative_to(CO/'build')]
assert own_firmware_units and all(Path(x['directory'])==CO/'build' for x in own_firmware_units)
save(OUT/'build-source-review.json',{'run_id':RUN.name,'implementation_commit':f['commit'],'firmware_build_events':builds,
    'firmware_mutations':firmware_mutations,'last_successful_build_event':last,'firmware_mutations_after_successful_build':later,
    'project_description_points_to_current_checkout':True,'own_firmware_compile_units':own_firmware_units,
    'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],'operator_firmware_rebuild':False,
    'scope':'ESP-IDF regenerated target in r02; current project/compile database and completed native build with no later firmware mutation support submitted firmware provenance. Host CTest provenance failure remains separate.'})

env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';checks=[]
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
        assert prev_name not in new_ctest and str(HOST).replace('\\','/') in new_ctest
save(OUT/'host-checks.json',{'run_id':RUN.name,'implementation_commit':f['commit'],'checks':checks,
    'fresh_host_build_directory':str(HOST),'host_compiler_same_as_candidate':True,
    'submitted_ctest_log_does_not_validate_current_source':True,
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
print(json.dumps({'policy_status':'invalid_for_comparison','checks':checks,'collectors':collectors,'encoder':encoder,
    'source_and_inputs_unchanged':True,'firmware_provenance_review':'current_checkout'},ensure_ascii=False))
