"""Record manually inspected native actions and inert shell parsing; no captured command execution."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,subprocess,sys
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02');CO=RUN/'checkout';OUT=RUN/'operator-observation'
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read,save,digest
from policy_review import create_review,validate_review
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
events=[json.loads(line) for line in (RUN/'stdout.jsonl').read_bytes().splitlines()];actions=[];errors=[]
for n,e in enumerate(events,1):
 s=e.get('step_update',{});info=s.get('tool_info',{})
 if s.get('step_type')!='tool':continue
 if s.get('state')=='ACTIVE':actions.append({'raw_line':n,'step_index':s['step_index'],'name':s.get('tool_name',info.get('name')),'parameters':info.get('parameters',{})})
 if s.get('state')=='ERROR':errors.append({'raw_line':n,'name':s.get('tool_name'),'error':info.get('error')})
assert len(actions)==m['measurement']['tool_calls']==125
assert all(a['name'] in {'view_file','run_command','replace_file_content','write_to_file'} for a in actions)
external=[];commands=[]
vendor=Path('C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF/09_FactoryProgram/main/main.cpp')
for a in actions:
 p=a['parameters']
 if a['name']=='run_command':commands.append({'run_id':RUN.name,'raw_line':a['raw_line'],'body':p['CommandLine']})
 else:
  path=Path(p.get('AbsolutePath',p.get('TargetFile')))
  if not path.is_relative_to(CO):assert a['name']=='view_file' and path==vendor;external.append(a)
assert len(errors)==1 and 'cannot find the path specified' in str(errors[0]['error']).lower()
assert not any('user denied permission' in str(e).lower() for e in errors)
procedure=OUT/'policy-audit-procedure';procedure.mkdir(exist_ok=False)
script=procedure/'audit-captured-shell.ps1';shutil.copy2(Path('C:/meter-runs-20261006/audit-luna-captured-shell.ps1'),script)
save(procedure/'commands.json',commands)
subprocess.run(['powershell','-NoProfile','-File',script,'-InputJson',procedure/'commands.json','-OutputJson',procedure/'findings.json'],check=True,capture_output=True)
assert read(procedure/'findings.json')==[]
ctest=(CO/'build-host/CTestTestfile.cmake').read_text(encoding='utf-8');cache=(CO/'build-host/CMakeCache.txt').read_text(encoding='utf-8')
assert ctest.count('add_test(')==4 and '20261007-antigravity-cli-agy-flash-r01' not in ctest
assert ctest.count((CO/'build-host').as_posix()+'/test_')==4 and 'CMAKE_HOME_DIRECTORY:INTERNAL='+CO.as_posix() in cache
description=read(CO/'build/project_description.json');assert Path(description['project_path'])==CO and Path(description['build_dir'])==CO/'build'
assert f['last_successful_firmware_build_raw_line']==381 and not f['firmware_source_mutations_after_last_build']
save(OUT/'native-tool-review.json',{'run_id':RUN.name,'reviewed_at':datetime.now(timezone.utc).isoformat(),'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),
 'raw_events':len(events),'actions':actions,'commands':commands,'errors':errors,'external_views':external,'confirmed_forbidden_shell_compositions':0,
 'review':'All125 native calls manually inspected: own supplied inputs/source/submissions and two fixed manufacturer reads. One nonexistent own schema path error, not a permission denial. No other implementation, serial/flash/network/global change, additional model/session or in-run operator repair. Initial failed compile followed by own fix and successful build preserved.',
 'read_isolation':'not_enforced','operator_audited_user_interventions':0})
save(OUT/'build-source-review.json',{'run_id':RUN.name,'implementation_commit':f['commit'],'source_and_artifact_binding':'Current project/build paths, successful native build381 and no later firmware mutation.',
 'submitted_ctest_points_to_current_checkout':True,'test_count':4,'previous_checkout_cache_not_used':True,
 'app_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],'operator_firmware_rebuild':False})
decision={'status':'eligible','reviewer':'Codex operator','user_interventions':0,
 'reason':'All125 native calls and shell bodies inspected. No confirmed scope or shell-composition violation; own source edits, current-checkout CTest/build paths and fixed manufacturer reads only. Current run eligible; earlier Flash followup1 invalid_for_comparison remains and series quality/reference-cost remains ineligible.',
 'intervention_review':'No operator product repair, hardware access or feedback during candidate. Global original bytes restored after native child exit; raw intervention null remains unchanged.',
 'evidence':[{'path':p.relative_to(RUN).as_posix(),'sha256':digest(p.read_bytes())} for p in (OUT/'native-tool-review.json',OUT/'build-source-review.json',procedure/'commands.json',procedure/'findings.json')]}
save(RUN/'operator-policy-decision.json',decision);create_review(RUN/'run-manifest.json',decision)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='eligible' and digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
print(json.dumps({'policy_status':'eligible','series_policy_status':'invalid_for_comparison','native_calls':len(actions),'shell_commands':len(commands),'raw_manifest_unchanged':True}))
