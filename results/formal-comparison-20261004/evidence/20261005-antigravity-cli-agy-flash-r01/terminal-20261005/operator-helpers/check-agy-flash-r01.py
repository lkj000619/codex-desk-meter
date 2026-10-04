"""Post-terminal policy evidence and host checks; no serial, source edit or rebuild."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import time

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
CO=RUN/'checkout';OUT=RUN/'operator-observation'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
tools={};errors=[];mutations=[];builds=[]
for i,event in enumerate(events):
    s=event.get('step_update',{});info=s.get('tool_info',{});n=s.get('tool_name') or info.get('name')
    if s.get('step_type')!='tool':continue
    step=s['step_index'];tool=tools.setdefault(step,{'step_index':step,'first_line':i+1,'name':n})
    if n:tool['name']=n
    tool['last_line']=i+1;tool['last_state']=s['state']
    if info.get('parameters'):tool['parameters']=info['parameters']
    params=tool.get('parameters',{})
    if s.get('state')=='ERROR':errors.append({'line':i+1,'step_index':step,'name':tool['name'],'parameters':params,'error':info.get('error')})
    if s.get('state')=='ACTIVE' and tool['name'] in {'write_to_file','replace_file_content','multi_replace_file_content'}:
        p=params.get('TargetFile',params.get('AbsolutePath',''))
        mutations.append({'line':i+1,'step_index':step,'tool':tool['name'],'path':p})
    if s.get('state')=='DONE' and tool['name']=='run_command' and params.get('CommandLine')=='idf.py build':
        output=json.dumps(info.get('output',''),ensure_ascii=False)
        builds.append({'line':i+1,'step_index':step,'output_contains_build_complete':'Project build complete' in output,
                       'native_exit_code':None,'output_sha256':digest(output.encode()),'tail':output[-800:]})
inventory=[]
for tool in tools.values():
    params=tool.get('parameters',{})
    if tool['name'] in {'write_to_file','replace_file_content','multi_replace_file_content'}:
        tool['parameters_sha256']=digest(json.dumps(params,ensure_ascii=False,sort_keys=True).encode())
        tool['parameters']={k:v for k,v in params.items() if k in {'TargetFile','AbsolutePath','Overwrite','StartLine','EndLine'}}
    inventory.append(tool)
assert len(errors)==1 and errors[0]['line']==382 and errors[0]['step_index']==253
post_denial=[t for t in inventory if t['first_line']>382]
assert not post_denial
external_views=[t for t in inventory if t['name']=='view_file' and not Path(t['parameters']['AbsolutePath']).is_relative_to(CO)]
for t in external_views:
    path=Path(t['parameters']['AbsolutePath'])
    assert path.is_relative_to(Path('C:/Espressif/v5.3.2/esp-idf')) or path.is_relative_to(Path('C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16'))
for item in mutations:assert Path(item['path']).is_relative_to(CO),item
last=next(b for b in reversed(builds) if b['output_contains_build_complete'])
firmware_mutations=[x for x in mutations if Path(x['path']).suffix in {'.c','.h'} or Path(x['path']).name in {'CMakeLists.txt','sdkconfig','sdkconfig.defaults'}]
later=[x for x in firmware_mutations if x['line']>last['line']]
assert not later,later
save(OUT/'native-tool-review.json',{'run_id':RUN.name,'reviewed_at':datetime.now(timezone.utc).isoformat(),
    'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),'raw_events':len(events),'tools':inventory,
    'native_tool_count':len(inventory),'errors':errors,'tools_after_denial':post_denial,
    'external_view_scope':'Declared ESP-IDF v5.3.2 and fixed Waveshare manufacturer source only.',
    'external_views':external_views,'all_mutation_paths_inside_own_checkout':True,
    'commands_reviewed':'26 commands: local Git inventory/search, declared versions, local CMake/CTest/Python, firmware build, local fixture/artifact checks. No serial/flash/network/install/ref-history command observed.',
    'operator_audited_user_interventions':0,'intervention_basis':'Operator supplied no messages, manual permissions or implementation feedback during native conversation; one-shot init/result conversation matches scoped launch. Native denial is policy enforcement, not a manual user intervention.',
    'original_measurement_user_interventions':m['measurement']['user_interventions'],
    'original_measurement_failed_commands':m['measurement']['failed_commands'],
    'stop_rule_observed':True,'failure_record':'Native TOOL_ERROR, terminal denied_actions and frozen adapter environment_failed; no tools after denial and no replacement initial invocation.',
    'policy_observation_limit':'Prompt-and-log, read isolation not enforced. Review covers captured native tool paths/commands and immutable hashes; not an OS access guarantee.'})
save(OUT/'build-source-review.json',{'run_id':RUN.name,'implementation_commit':f['commit'],'firmware_build_events':builds,
    'firmware_mutations':firmware_mutations,'last_successful_build_event':last,'firmware_mutations_after_successful_build':later,
    'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],'source_hashes':{k:v['sha256'] for k,v in f['sources'].items() if k.endswith(('.c','.h'))},
    'operator_firmware_rebuild':False,'scope':'Native build-complete output and no later firmware mutation bind the preserved artifact to candidate source. Native per-command exit codes are unavailable; original unknown counts retained.'})
checks=[];env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
def run_check(name,argv):
    started=time.monotonic();p=subprocess.run(argv,cwd=CO,env=env,capture_output=True,timeout=120)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    checks.append({'name':name,'argv':[str(a) for a in argv],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-started})
    return p
run_check('python-tests',[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-v'])
for name in ('test_meter_parser','test_meter_state','test_feature_imu','test_gui_regression'):
    run_check(name,[str(CO/'build-host'/(name+'.exe'))])
spec=importlib.util.spec_from_file_location('candidate_pc_collector_sender',CO/'scripts/pc_collector_sender.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
reference=BASE/'experiments/reference/codex-7923f96';raws=(reference/'expected-frames.jsonl').read_bytes().splitlines(keepends=True)
frames=[json.loads(raw) for raw in raws];encoder=[]
for wire,frame in zip(raws,frames):
    generated=module.encode_frame(module.build_frame(frame['payload'],sequence=frame['sequence'],sent_at=frame['sent_at']))
    encoder.append({'sequence':frame['sequence'],'matches_common_wire':generated==wire,'sha256':digest(generated)})
collector={};payload=None
try:
    sender=module.PcCollectorSender(device_alias='operator-common-fixture',state_dir=OUT/'sender-state',reference_time='2026-09-30T18:40:49Z')
    actual,line=sender.collect_and_build(0,sent_at=frames[0]['sent_at']);payload=actual['payload']
    save(OUT/'candidate-collector-frame.json',actual)
    (OUT/'candidate-collector-frame.jsonl').write_bytes(line)
    collector={'status':'built','frame_sha256':digest(line),'matches_common_payload':payload==frames[0]['payload'],
               'usage_entries':len(payload['usage']),'reset_entries':len(payload['global_resets'])}
except Exception as e:
    collector={'status':'failed','error_type':type(e).__name__,'error':str(e),'code':getattr(e,'code',None)}
run_check('collector-cli-init',[sys.executable,'-B','-X','utf8','scripts/pc_collector_sender.py','--state-dir',str(OUT/'cli-sender-state'),'--alias','operator-cli','--init-sequence','0'])
run_check('collector-cli-dry-run',[sys.executable,'-B','-X','utf8','scripts/pc_collector_sender.py','--state-dir',str(OUT/'cli-sender-state'),'--alias','operator-cli','--dry-run'])
save(OUT/'common-stimulus-check.json',{'run_id':RUN.name,'implementation_commit':f['commit'],
    'reference_frames_sha256':digest((reference/'expected-frames.jsonl').read_bytes()),'candidate_encoder_checks':encoder,
    'actual_collector_api':collector,'collector_source_sha256':digest((CO/'scripts/pc_collector_sender.py').read_bytes()),
    'candidate_collector_configuration':'Unmodified PcCollectorSender.collect_and_build at common reference UTC; default FixtureRegistry, external state directory. CLI has no reference-time option; separate CLI dry-run uses actual clock.',
    'scope':'Host-only evidence. Production receiver and optical observation are assessed separately.'})
save(OUT/'host-checks.json',{'run_id':RUN.name,'implementation_commit':f['commit'],'checks':checks})
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
print(json.dumps({'checks':checks,'collector':collector,'encoder_checks':encoder,'last_successful_firmware_build_line':last['line'],
    'tools_after_denial':len(post_denial),'source_and_inputs_unchanged':True},ensure_ascii=False))
