"""Bind the user photograph and apply the terminal followup RM review once."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r01')
REST=Path('C:/meter-run-restores-20261006/codex-sol-followup01-pre-observation')
PACKS=Path('C:/meter-run-packages-20261006')
SOURCE=Path('C:/Users/\uC774\uAD11\uC9C4/AppData/Local/Temp/orca-paste-1791226335194-559d5f72-ac72-4cb8-a1ab-4fd33f7cccab.png')
CO=RUN/'checkout';OUT=RUN/'operator-observation';PHOTO=OUT/'user-photo-01'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from comparison_manager import review_run
from policy_review import validate_review

before=read(RUN/'run-manifest.json');ledger_path=Path(before['operator']['comparison']['ledger'])
ledger=read(ledger_path);f=read(RUN/'operator-source-freeze.json')
original_path=OUT/'terminal-originals/run-manifest.json';original=read(original_path)
assert len(ledger['runs'])==2 and not ledger['runs'][-1]['reviewed'] and not (RUN/'reference-review.json').exists()
assert digest(original_path.read_bytes())==f['original_terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
assert original['measurement']==before['measurement'] and original['execution']==before['execution']
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
verify_evidence(before,RUN);benchmark.verify_agent_inputs(RUN,before)
assert validate_review(before,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
now=datetime.now(timezone.utc).isoformat()
PHOTO.mkdir(exist_ok=False);shutil.copy2(SOURCE,PHOTO/'source.png')
raw=(PHOTO/'source.png').read_bytes();assert raw==SOURCE.read_bytes()
user_answer=str(SOURCE).replace('/','\\')+' 어떠한 버튼을 눌려도 현 이미지임. reset 버튼 누르면 재부팅 후 위 이미지가 올라옴'
save(PHOTO/'photo-metadata.json',{'source_path':str(SOURCE),'source_bytes':len(raw),'source_sha256':digest(raw),
    'filesystem_modified_at_utc':datetime.fromtimestamp(SOURCE.stat().st_mtime,timezone.utc).isoformat(),
    'capture_time_utc':None,'preserved_at':now,'image_edited':False})
save(PHOTO/'capture-identity-confirmation.json',{'run_id':RUN.name,'round':1,'recorded_at':now,
    'question_item_id':'["request_user_input_async","call_72iHRvLmqUiqeah7pkMPiH4n",0]',
    'user_answer_original':user_answer,'source':'User reply to the question identifying Codex Sol followup1 firmware uploaded on 2026-10-06 at03:50KST.',
    'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    'photo_sha256':digest(raw),'hardware_slot':'operator-observation/hardware-slot.json',
    'button_response_user_reported':'No response with any button; pressing RESET reboots and displays the same image.',
    'exact_boot_press_count_confirmed':None,'manual_reset_confirmed':True,
    'manual_reset_is_spontaneous_reboot':False,'feedback_delivered_to_terminal_candidate':False})
save(PHOTO/'photo-review.json',{'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':now,
    'photo_sha256':digest(raw),'source_bytes':len(raw),'implementation_commit':f['commit'],
    'artifact_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    'visible':'Dark blue panel with one horizontal red band and one horizontal pale blue band near the bottom. No legible titles, numbers or text.',
    'orientation_and_clipping':'Board held horizontally; readable text absent, so text orientation and clipping cannot be assessed.',
    'navigation':{'user_reported_response':'none','information_views_reached':[],
        'returned_to_initial_information':False,'exact_press_count_verified':False},
    'reset':{'user_initiated_reset_confirmed':True,'same_image_after_reset_reported':True,'spontaneous_reboot_verified':False},
    'continuity':{'continuous_30s_verified':False,'no_flicker_certified':False,'precise_latency_measured':False,
        'scope':'One still photograph and a button/reset report cannot certify30s continuity, flicker absence or response latency.'},
    'reference_reached':False,'product_pass':False,'candidate_execution_repeated':False})
shutil.copytree(REST/'post-restore-host-checks',OUT/'independent-host-checks')
candidate=read(OUT/'independent-host-checks/candidate-legacy-collector-frame.json')['payload']
reference=json.loads((RUN/'reference/expected-frames.jsonl').read_bytes().splitlines()[0])['payload']
diffs=[]
def compare(a,b,path):
    if isinstance(a,dict) and isinstance(b,dict):
        assert set(a)==set(b),path
        for k in a:compare(a[k],b[k],path+'.'+k)
    elif isinstance(a,list) and isinstance(b,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'[{i}]')
    elif a!=b:diffs.append({'path':path,'candidate':a,'reference':b})
compare(candidate,reference,'payload')
assert diffs==[{'path':f'payload.global_resets[{i}].error_code','candidate':'SOURCE_STALE','reference':None} for i in range(2)]
save(OUT/'independent-host-checks/legacy-collector-payload-differences.json',{'run_id':RUN.name,'compared_at':now,
    'candidate_frame_sha256':digest((OUT/'independent-host-checks/candidate-legacy-collector-frame.json').read_bytes()),
    'reference_wire_sha256':digest((RUN/'reference/expected-frames.jsonl').read_bytes()),'differences':diffs,
    'all_other_payload_values_equal':True,'collector_usage_remaining':[58,82],
    'scope':'Existing independent host results, no candidate execution rerun. Physical stimulus was common operator replay, not candidate collector output; no complete collector-to-device path inferred.'})
pres=OUT/'pre-observation-preservation';pres.mkdir()
for source,name in [(REST/'frozen-validator-audit.json','frozen-validator-audit.json'),
    (REST/'restore-report.json','restore-report.json'),(PACKS/'codex-sol-followup01-pre-observation/package-manifest.json','package-manifest.json'),
    (PACKS/'codex-sol-followup01-pre-observation-create.json','package-create.json'),
    (PACKS/'verify-codex-sol-followup01-pre-observation.py','audit-and-host-checks.py')]:shutil.copy2(source,pres/name)
helpers=OUT/'operator-helpers';helpers.mkdir()
for source in [Path(__file__),RUN.parent/'preserve-codex-sol-followup-01.py',RUN.parent/'observe-codex-sol-followup-01.py',RUN.parent/'review-codex-sol-shell-policy.py']:
    shutil.copy2(source,helpers/source.name)
binding=OUT/'reference-review-binding';binding.mkdir()
shutil.copy2(RUN/'run-manifest.json',binding/'pre-review-operator-metadata.json')
save(binding/'binding-note.json',{'run_id':RUN.name,'recorded_at':now,
    'original_terminal_manifest_sha256':digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256':digest((binding/'pre-review-operator-metadata.json').read_bytes()),
    'scope':'Preserved original terminal bytes satisfy unchanged frozen review guard. Reattach operator sidecars afterward; no ledger terminal hash, execution, measurement or source mutation.'})
names=set(before['operator']['evidence'])|{'policy-review.json'}
names.update(p.relative_to(RUN).as_posix() for p in OUT.rglob('*') if p.is_file())
def evidence(values):return [{'path':n,'sha256':digest((RUN/n).read_bytes())} for n in sorted(values)]
photo_names=[n for n in names if '/user-photo-01/' in n]
capture_names=['operator-observation/independent-host-checks/common-stimulus-check.json',
    'operator-observation/independent-host-checks/legacy-collector-payload-differences.json',
    'operator-observation/receiver-source-review.json','operator-observation/reference-capture-r1/capture.json',
    'operator-observation/reference-capture-r1/sent-frames.jsonl','operator-observation/reference-capture-r1/device-serial.bin']
report={'run_id':RUN.name,'reference_inputs_sha256':ledger['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
        'RM1':{'status':'pass','reason':'ESP-IDF build completed and independently archived same genuine artifact was uploaded and ran onCOM3. Firmware source unchanged after build. LCD functionality is evaluated separately.','evidence':evidence(names)},
        'RM2':{'status':'partial','reason':'Encoder exactly reproduces fixed seq0/1; production host receiver and actual device accept both. Own legacy collector produces remaining58/82 and matching other payload values, but global reset error_code is SOURCE_STALE in two places where reference has null. Device stimulus was common operator replay; complete own collector-to-device path is not demonstrated. This is partial coverage, not a new byte-identity acceptance requirement.','evidence':evidence(capture_names)},
        'RM3':{'status':'fail','reason':'User photograph contains no legible text or numbers; required remaining58%/82% meaning is not visible.','evidence':evidence(photo_names)},
        'RM4':{'status':'fail','reason':'User reports no information change with any button. Photograph has no readable usage/global reset/diagnostic information. Colored bands do not demonstrate information screens.','evidence':evidence(photo_names)},
        'RM5':{'status':'fail','reason':'User reports any button leaves the same image, and only manual RESET reboots to the same image. No BOOT navigation or information return path is demonstrated. Exact count and timing not established; no new acceptance threshold added.','evidence':evidence(photo_names)}},
    'product_pass':False,'policy_status':'invalid_for_comparison',
    'note':'One forbidden pipeline finding is sufficient for policy invalidity; four confirmed. Final Git permission denial was followed only by final report and terminal usage, with no later tool/file actions. Implementation completion, valid submission format, receipt improvement and failed product/reference are separate.30s continuity and precision timing unmeasured; user RESET is deliberate.'}
save(RUN/'operator-reference-review-input.json',report)
(RUN/'run-manifest.json').write_bytes(original_path.read_bytes())
try:review_run(RUN,report)
except Exception:
    if not read(ledger_path)['runs'][-1]['reviewed']:(RUN/'run-manifest.json').write_bytes((binding/'pre-review-operator-metadata.json').read_bytes())
    raise
after=read(RUN/'run-manifest.json');after['outputs']['build_status']='pass'
after['operator']['evidence'].update(before['operator']['evidence'])
assert after['measurement']==original['measurement'] and after['execution']==original['execution']
assert after['outputs']['implementation_commit']==f['commit']==benchmark.git('rev-parse','HEAD',cwd=CO)
assert not benchmark.git('status','--porcelain',cwd=CO)
remaining=7200-sum(v['elapsed_seconds'] for v in read(ledger_path)['runs'] if v['round'])
save(OUT/'observation-finalization.json',{'run_id':RUN.name,'round':1,'recorded_at':now,
    'status':'followup_reference_review_complete','source_and_raw_cost_unchanged':True,'serial_closed':True,
    'board_state':'Frozen followup1 artifact retained; user reports manual RESET after upload. No operator rebuild/reupload after observation.',
    'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'invalid_for_comparison','product_pass':False,
    'remaining_followup_seconds':remaining,'remaining_followup_rounds':2,
    'continuous_30s_verified':False,'spontaneous_reboot_verified':False,'user_initiated_reset_confirmed':True,
    'raw_reasoning_output_tokens':2880,'frozen_normalized_reasoning_tokens':None,
    'cost_note':'Raw native reasoning_output_tokens retained separately; frozen adapter reports reasoning null. No cost reinterpretation.'})
for p in [OUT/'observation-finalization.json',RUN/'operator-reference-review-input.json']:
    after['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',after)
verify_evidence(after,RUN);benchmark.verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
assert read(ledger_path)['runs'][-1]['reviewed'] and read(ledger_path)['runs'][-1]['reference_status']=='fail'
print(json.dumps({'run_id':RUN.name,'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail',
    'policy_status':'invalid_for_comparison','product_pass':False,'source_and_cost_unchanged':True,
    'photo_sha256':digest(raw),'remaining_followup_seconds':remaining,'remaining_followup_rounds':2}))
