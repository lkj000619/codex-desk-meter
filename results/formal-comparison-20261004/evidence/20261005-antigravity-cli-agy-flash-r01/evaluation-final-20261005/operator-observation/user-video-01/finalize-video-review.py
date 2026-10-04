"""Apply one RM review to the user-confirmed AGY Flash video and raw capture."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
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
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
confirmation={'run_id':RUN.name,'recorded_at':now,'source':'User reply to current AGY Flash firmware observation question',
    'answer_original':'"'+meta['source_path']+'" 해당 펌웨어에 해당하는 동작 영상',
    'video_sha256':meta['source_sha256'],'implementation_commit':f['commit'],
    'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],'hardware_slot':'operator-observation/hardware-slot.json',
    'user_confirmed_current_firmware':True,'filesystem_save_after_upload':True,'capture_time_utc':None}
save(VIDEO/'capture-identity-confirmation.json',confirmation)
selected=[1,8,17,19,22,28,42,47]
for n in selected:shutil.copy2(VIDEO/'frames'/f'frame-{n:03d}.png',VIDEO/f'readable-frame-{n:03d}.png')
video_review={'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':now,'status':'capture_identity_confirmed',
    'video_sha256':meta['source_sha256'],'duration_seconds':48.12,'source_bytes':meta['source_bytes'],
    'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],
    'nominal_timestamps_are_precision_measurements':False,'contact_sheets_reviewed':4,'sample_frames_reviewed':48,
    'individual_readable_frames_reviewed':selected,
    'visual_findings':[
        {'at_seconds':0.5,'frame':'readable-frame-001.png','screen':'CODEX METER dashboard',
         'text':['WAITING FOR USB DATA...','Connect host sender to stream cdm/1 frames','BOOT: SWITCH SCREEN','TRANSPORT: USB CDC 115200 8N1'],
         'remaining_58_or_82_visible':False},
        {'at_seconds':7.5,'frame':'readable-frame-008.png','screen':'GLOBAL RESETS',
         'text':['LATEST GLOBAL RESET','NO RECENT RESET RECORD','SOURCE DETAILS','Provider: codex-resets.com','Status: FRESH']},
        {'at_seconds':16.5,'frame':'readable-frame-017.png','screen':'SYSTEM STATUS',
         'text':['USB TRANSPORT','Protocol: cdm/1','Baud: 115200 8N1','Sequence: NONE','CACHE / RECOVERY','Cached Snapshots: 0','Cached Resets: 0','HARDWARE INFO'],
         'source_note':'No Active Errors/HEALTHY and Auto Recovery READY are default UI state, not successful input or recovery evidence.'},
        {'at_seconds':18.5,'frame':'readable-frame-019.png','screen':'CODEX METER dashboard','text':['WAITING FOR USB DATA...']},
        {'interval_seconds':[21.5,22.5],'frame':'readable-frame-022.png','screen':'blank/dark during hand/button manipulation',
         'note':'Text disappears before dashboard returns at approx 23.5s. Reset cause, specific button identity and spontaneous reboot are not proven.'},
        {'at_seconds':27.5,'frame':'readable-frame-028.png','screen':'SYSTEM STATUS','text':['Sequence: NONE','Cached Snapshots: 0','Cached Resets: 0']},
        {'interval_seconds':[30.5,35.5],'screen':'intentional USB cable removal, dark board, reconnect',
         'note':'Cable removal/power loss is visible; not powered USB-link recovery proof.'},
        {'at_seconds':41.5,'frame':'readable-frame-042.png','screen':'SYSTEM STATUS','text':['Sequence: NONE','Cached Snapshots: 0','Cached Resets: 0']},
        {'at_seconds':46.5,'frame':'readable-frame-047.png','screen':'SYSTEM STATUS','note':'Board physically rotates; selected IMU feature conformance is not established from unmeasured motion alone.'}],
    'navigation':{'starting_screen':'dashboard waiting for USB data','observed_path':['dashboard waiting','GLOBAL RESETS default','SYSTEM STATUS empty cache','dashboard waiting'],
        'nominal_view_times_seconds':[0.5,7.5,16.5,18.5],'physical_hand_and_button_manipulation_visible':True,
        'exact_boot_press_count':None,'individual_transition_trigger_boot_vs_imu':None,'returned_to_starting_information':True,
        'complete_reference_data_navigation_proven':False,
        'scope':'Views cycle, but common input receipt prerequisite and actual usage/reset values are absent. BOOT and selected IMU shake trigger are not individually timed.'},
    'continuity':{'continuous_30s_no_flicker_certified':False,'sample_interval_seconds':1,
        'note':'Blank screen during manipulation before 30s, later intentional USB removal, and one-second sampling prevent a continuous 30s no-flicker claim.'},
    'data_gaps':['No 58% five-hour or 82% weekly remaining values displayed.','No actual global reset timestamps displayed.',
        'Sequence NONE and caches 0 persist; transport label USB CDC does not override UART source or failed USB write.',
        'Default FRESH/HEALTHY labels are not evidence of successful source freshness or recovery.'],
    'reference_reached':False,'product_pass':False,'policy_status':'eligible','candidate_execution_repeated':False}
save(VIDEO/'video-review.json',video_review)
shutil.copy2(Path('C:/meter-runs-20261005/inspect-agy-flash-r01-user-video.py'),VIDEO/'inspect-video.py')
shutil.copy2(Path(__file__),VIDEO/'finalize-video-review.py')
paths=['operator-source-freeze.json','operator-terminal-source.bundle','policy-review.json','operator-policy-decision.json']
paths += [p.relative_to(RUN).as_posix() for p in OUT.rglob('*') if p.is_file() and 'frames' not in p.relative_to(OUT).parts]
paths=sorted(set(paths))
def evidence(names):return [{'path':name,'sha256':digest((RUN/name).read_bytes())} for name in names]
video_paths=[n for n in paths if '/user-video-01/' in n]
capture_paths=['operator-observation/common-stimulus-check.json','operator-observation/receiver-source-review.json',
    'operator-observation/reference-capture-r1/capture.json','operator-observation/reference-capture-r1/events.jsonl',
    'operator-observation/reference-capture-r1/sent-frames.jsonl','operator-observation/reference-capture-r1/device-serial.bin']
report={'run_id':RUN.name,'reference_inputs_sha256':ledger['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
      'RM1':{'status':'pass','reason':'Candidate native IDF build completed before terminal denial; no later firmware mutation. Same frozen artifact uploaded with flash hash verification, and user-confirmed video shows it running. Final candidate JSON remains missing.','evidence':evidence(paths)},
      'RM2':{'status':'partial','reason':'Host candidate encoder matches fixed seq 0/1 wires and collector builds a valid frame, but default collector payload differs from common legacy reference. Real COM3 seq 0 write timed out, bytes_written unknown, raw receiver log empty, seq 1 not attempted. Actual device acceptance and collector-to-device completion are not established.','evidence':evidence(capture_paths)},
      'RM3':{'status':'fail','reason':'Confirmed video shows WAITING FOR USB DATA rather than required 58% five-hour and 82% weekly remaining values. Missing input receipt is documented separately; no fabricated displayed values.','evidence':evidence(video_paths+capture_paths)},
      'RM4':{'status':'partial','reason':'Dashboard, global-reset and diagnostic views visibly render. Dashboard awaits USB data; global view has NO RECENT RESET RECORD; diagnostic has Sequence NONE and caches 0. Required common data is absent despite visible information categories.','evidence':evidence(video_paths)},
      'RM5':{'status':'partial','reason':'User video shows manipulation and repeated dashboard->global->status->dashboard view changes, returning to initial view. Common-frame receipt prerequisite and populated usage information are absent; exact BOOT press count/individual BOOT vs selected IMU shake triggers are not established. Complete reference-data BOOT navigation is not proven.','evidence':evidence(video_paths)}},
    'product_pass':False,'policy_status':'eligible','note':'First execution remains environment_failed after native denial. Optical observation confirms displayed residual firmware; it does not convert failed USB write to receipt or fill missing candidate submission. Exact timing, uninterrupted 30s and selected IMU hardware conformance remain unmeasured.'}
save(RUN/'operator-reference-review-input.json',report)
review_run(RUN,report)
after=read(RUN/'run-manifest.json');after_ledger=read(ledger_path)
assert after['measurement']==m['measurement'] and after['execution']==m['execution']
assert after_ledger['runs'][-1]['reviewed'] and after_ledger['runs'][-1]['reference_status']=='fail'
assert after['outputs']['implementation_commit']==f['commit']
verify_evidence(after,RUN);benchmark.verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
save(OUT/'observation-finalization.json',{'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'status':'initial_reference_review_complete','video_capture_identity_confirmed':True,'receiver_acceptance_observed':False,
    'board_slot_released':True,'serial_closed':True,'source_and_raw_cost_unchanged':True,
    'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'eligible',
    'remaining_followup_seconds':7200,'followups_run':0,'followup_preparation_after_final_package_restore':True})
save(RUN/'operator-review-finalization.json',{'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'original_terminal_manifest_sha256':f['original_terminal_manifest_sha256'],
    'reviewed_manifest_sha256':digest((RUN/'run-manifest.json').read_bytes()),'reviewed_ledger_sha256':digest(ledger_path.read_bytes()),
    'immutable_input_files_verified':57,'execution_and_measurement_unchanged':True,'candidate_result_submission_missing':True,
    'candidate_selection_document_present':True,'implementation_commit':f['commit']})
print(json.dumps({'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'eligible',
    'initial_cost_preserved':True,'remaining_followup_seconds':7200,'implementation_commit':f['commit']}))
