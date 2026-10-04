"""Apply one evidence-bound current-run RM review and retain the explicit user hold."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys

BASE=Path('C:/meter-operator-20261004'); RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
CO=RUN/'checkout';OUT=RUN/'operator-observation';VIDEO=OUT/'user-video-01'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from comparison_manager import review_run
from policy_review import validate_review

m=read(RUN/'run-manifest.json');ledger_path=Path(m['operator']['comparison']['ledger']);ledger=read(ledger_path)
f=read(RUN/'operator-source-freeze.json');meta=read(VIDEO/'video-metadata.json');now=datetime.now(timezone.utc).isoformat()
assert not ledger['runs'][-1]['reviewed'] and not (RUN/'reference-review.json').exists()
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
assert digest((VIDEO/'source.mp4').read_bytes())==meta['source_sha256']
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
hold=read(RUN/'operator-user-hold.json');assert not hold['next_model_start_authorized_now']
save(VIDEO/'capture-identity-confirmation.json',{'run_id':RUN.name,'recorded_at':now,
    'source':'User supplied this video in direct reply to r02 upload/observation instructions and requested waiting before next model.',
    'video_source_path':meta['source_path'],'video_sha256':meta['source_sha256'],'implementation_commit':f['commit'],
    'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],'hardware_slot':'operator-observation/hardware-slot.json',
    'user_supplied_current_firmware_video':True,'filesystem_save_after_upload':True,'capture_time_utc':None})
selected=[1,4,6,8,9,11,28,29,41,43,44,45]
for n in selected:shutil.copy2(VIDEO/'frames'/f'frame-{n:03d}.png',VIDEO/f'readable-frame-{n:03d}.png')
video_review={'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':now,'status':'capture_identity_confirmed',
    'video_sha256':meta['source_sha256'],'duration_seconds':46.3,'source_bytes':meta['source_bytes'],
    'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],
    'nominal_timestamps_are_precision_measurements':False,'contact_sheets_reviewed':4,'sample_frames_reviewed':46,
    'individual_readable_frames_reviewed':selected,
    'visual_findings':[
        {'at_seconds':0.5,'frame':'readable-frame-001.png','screen':'CODEX METER dashboard',
         'text':['WAITING FOR USB DATA...','Connect host sender to stream cdm/1 frames','BOOT: SWITCH SCREEN','TRANSPORT: USB Serial / JTAG 115200 8N1'],
         'remaining_58_or_82_visible':False},
        {'at_seconds':3.5,'frame':'readable-frame-004.png','screen':'GLOBAL RESETS',
         'text':['LATEST GLOBAL RESET','NO RECENT RESET RECORD','Provider: codex-resets.com','Status: FRESH']},
        {'at_seconds':5.5,'frame':'readable-frame-006.png','screen':'SYSTEM STATUS',
         'text':['Protocol: cdm/1','Sequence: NONE','Cached Snapshots: 0','Cached Resets: 0','No Active Errors','Auto Recovery: READY','Uptime: 421 sec'],
         'default_labels_are_successful_receipt_evidence':False},
        {'at_seconds':7.5,'frame':'readable-frame-008.png','screen':'mixed transition',
         'note':'Header shows CODEX METER while body retains SYSTEM STATUS information; transient mixed rendering is visible.'},
        {'at_seconds':8.5,'frame':'readable-frame-009.png','screen':'dashboard waiting','returned_to_start':True},
        {'at_seconds':10.5,'frame':'readable-frame-011.png','screen':'mixed transition',
         'note':'SYSTEM STATUS heading coexists with GLOBAL RESETS body in the sample.'},
        {'interval_seconds':[14.5,26.5],'screen':'physical board rotation and camera movement',
         'note':'No extra IMU conformance or calibrated rotation/latency claim from movement alone.'},
        {'interval_seconds':[27.5,29.5],'frames':['readable-frame-028.png','readable-frame-029.png'],
         'screen':'blank/dim then header returns then dashboard',
         'note':'Glare and hand/button manipulation present. Reset cause and spontaneous-vs-manual behavior cannot be assigned from these samples.'},
        {'interval_seconds':[30.5,39.5],'screen':'board occluded or outside camera',
         'note':'Continuous LCD stability and exact input/USB operations cannot be assessed in this interval.'},
        {'at_seconds':40.5,'frame':'readable-frame-041.png','screen':'dashboard waiting'},
        {'at_seconds':42.5,'frame':'readable-frame-043.png','screen':'GLOBAL RESETS default'},
        {'at_seconds':43.5,'frame':'readable-frame-044.png','screen':'SYSTEM STATUS',
         'text':['Sequence: NONE','Cached Snapshots: 0','Cached Resets: 0','Uptime: 3 sec'],
         'note':'Uptime decreased from 421 to 3; a restart occurred during the recording interval, but off-camera manipulation prevents cause attribution.'},
        {'at_seconds':44.5,'frame':'readable-frame-045.png','screen':'dashboard waiting','returned_to_start':True}],
    'navigation':{'starting_screen':'dashboard waiting','observed_paths':[['dashboard waiting','GLOBAL RESETS default','SYSTEM STATUS empty','dashboard waiting'],
        ['dashboard waiting','GLOBAL RESETS default','SYSTEM STATUS empty','dashboard waiting']],
        'first_path_nominal_times_seconds':[0.5,3.5,5.5,8.5],'last_path_nominal_times_seconds':[40.5,42.5,43.5,44.5],
        'physical_button_manipulation_visible':True,'exact_boot_press_count':None,'individual_boot_vs_imu_transition_trigger':None,
        'populated_reference_information_navigation_proven':False},
    'continuity':{'continuous_30s_no_flicker_certified':False,'note':'Blank/mixed samples, off-camera interval, uptime restart and one-second sampling do not certify 30s continuous stable rendering.'},
    'reference_reached':False,'product_pass':False,'policy_status':'invalid_for_comparison','candidate_execution_repeated':False,
    'next_model_started':False,'additional_candidate_round_started':False,'user_hold':hold}
save(VIDEO/'video-review.json',video_review)
shutil.copy2(Path(__file__),VIDEO/'finalize-video-review.py')
paths=['operator-source-freeze.json','operator-terminal-source.bundle','policy-review.json','operator-policy-decision.json','operator-user-hold.json']
paths += [p.relative_to(RUN).as_posix() for p in OUT.rglob('*') if p.is_file() and 'frames' not in p.relative_to(OUT).parts]
paths=sorted(set(paths))
def evidence(names):return [{'path':name,'sha256':digest((RUN/name).read_bytes())} for name in names]
video_paths=[n for n in paths if '/user-video-01/' in n]
capture_paths=['operator-observation/common-stimulus-check.json','operator-observation/receiver-source-review.json',
    'operator-observation/reference-capture-r1/capture.json','operator-observation/reference-capture-r1/events.jsonl',
    'operator-observation/reference-capture-r1/sent-frames.jsonl','operator-observation/reference-capture-r1/device-serial.bin','operator-observation/panic-source-review.json']
report={'run_id':RUN.name,'reference_inputs_sha256':ledger['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
        'RM1':{'status':'pass','reason':'Candidate ESP-IDF build is bound to current r02 source; same preserved original firmware uploaded with flash hash verification and is visibly running in user video. Host-only operator build was not flashed.','evidence':evidence(paths)},
        'RM2':{'status':'partial','reason':'Encoder reproduces fixed seq 0/1 wires and PC writes completed 1543 bytes each; default and legacy collector payloads differ from common identity/stale semantics. Captured device logs show two LoadProhibited panics/reboots and zero successful acceptance lines. Collector-to-device success is not established.','evidence':evidence(capture_paths)},
        'RM3':{'status':'fail','reason':'Confirmed video shows WAITING FOR USB DATA, not required 58% five-hour and 82% weekly remaining. Diagnostic Sequence NONE and caches 0 agree with missing successful receipt.','evidence':evidence(video_paths+capture_paths)},
        'RM4':{'status':'partial','reason':'Three view categories render, but usage waits for input, global reset has NO RECENT RESET RECORD and diagnostics have no accepted sequence/cache. Mixed header/body transition samples and blank/occluded intervals recorded separately.','evidence':evidence(video_paths)},
        'RM5':{'status':'partial','reason':'Physical button manipulation and repeated dashboard->global->diagnostic->dashboard view cycles visible. Successful common-frame receipt and populated usage information prerequisite absent; exact BOOT count/individual BOOT-versus-IMU trigger not established.','evidence':evidence(video_paths)}},
    'product_pass':False,'policy_status':'invalid_for_comparison',
    'note':'One current-run RM review only. Preserve completed exit/cost and policy exclusion. Source fix/rebuild/reupload/extra candidate calls not performed. Precise latency, continuous 30s and selected IMU hardware conformance remain unmeasured. Explicit user hold forbids next model or further round until resumed.'}
save(RUN/'operator-reference-review-input.json',report)
review_run(RUN,report)
after=read(RUN/'run-manifest.json');new_ledger=read(ledger_path)
assert after['measurement']==m['measurement'] and after['execution']==m['execution']
assert new_ledger['runs'][-1]['reviewed'] and new_ledger['runs'][-1]['reference_status']=='fail'
assert after['outputs']['implementation_commit']==f['commit']
verify_evidence(after,RUN);benchmark.verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
remaining=7200-sum(x['elapsed_seconds'] or 0 for x in new_ledger['runs'] if x['round'])
save(OUT/'observation-finalization.json',{'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'status':'followup_reference_review_complete_user_hold','video_capture_identity_confirmed':True,'receiver_acceptance_observed':False,
    'board_slot_released':True,'serial_closed':True,'board_firmware_to_be_retained':True,'source_and_raw_cost_unchanged':True,
    'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'invalid_for_comparison',
    'remaining_followup_seconds':remaining,'followups_run':1,'remaining_followup_rounds':2,
    'next_model_start_authorized_now':False,'additional_candidate_round_start_authorized_now':False})
save(RUN/'operator-review-finalization.json',{'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'original_terminal_manifest_sha256':f['original_terminal_manifest_sha256'],
    'reviewed_manifest_sha256':digest((RUN/'run-manifest.json').read_bytes()),'reviewed_ledger_sha256':digest(ledger_path.read_bytes()),
    'immutable_input_files_verified':57,'execution_and_measurement_unchanged':True,'candidate_result_submission_missing':False,
    'candidate_selection_document_present':True,'implementation_commit':f['commit'],'user_hold_recorded':True})
print(json.dumps({'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail',
    'policy_status':'invalid_for_comparison','remaining_followup_seconds':remaining,'hold':True,'source_commit':f['commit']}))
