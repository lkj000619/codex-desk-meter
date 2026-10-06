"""Apply one RM review to confirmed video, keeping source/terminal cost unchanged."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02')
REST=Path('C:/meter-run-restores-20261006/codex-sol-followup02-pre-observation');PACKS=Path('C:/meter-run-packages-20261006')
CO=RUN/'checkout';OUT=RUN/'operator-observation';VIDEO=OUT/'user-video-01'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from comparison_manager import review_run
from policy_review import validate_review
before=read(RUN/'run-manifest.json');ledger_path=Path(before['operator']['comparison']['ledger']);ledger=read(ledger_path)
f=read(RUN/'operator-source-freeze.json');meta=read(VIDEO/'video-metadata.json');original_path=OUT/'terminal-originals/run-manifest.json';original=read(original_path)
assert len(ledger['runs'])==3 and not ledger['runs'][-1]['reviewed'] and not (RUN/'reference-review.json').exists()
assert digest(original_path.read_bytes())==f['original_terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
assert original['measurement']==before['measurement'] and original['execution']==before['execution']
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
verify_evidence(before,RUN);benchmark.verify_agent_inputs(RUN,before)
assert validate_review(before,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
now=datetime.now(timezone.utc).isoformat()
assert digest((VIDEO/'source.mp4').read_bytes())==meta['source_sha256'] and meta['duration_seconds']==63.3
selected=[1,5,7,10,20,21,34,35,53]
for n in selected:shutil.copy2(VIDEO/'frames'/f'frame-{n:03d}.png',VIDEO/f'readable-frame-{n:03d}.png')
save(VIDEO/'capture-identity-confirmation.json',{'run_id':RUN.name,'round':2,'recorded_at':now,
    'video_answer_original':'"'+meta['source_path']+'"','video_question_item_id':'["request_user_input_async","call_fJL4nggN6PHB9ZUlmy3u4by0",0]',
    'reset_answer_original':'RESET(RST)을 직접 누름','reset_question_item_id':'["request_user_input_async","call_9Ic9p4lmCNVC2UvsOcXZ0iLX",0]',
    'source':'User replies identifying current followup2 upload and confirms manual RESET near18s in its video.',
    'video_sha256':meta['source_sha256'],'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    'hardware_slot':'operator-observation/hardware-slot.json','filesystem_save_after_upload':True,'capture_time_utc':None,
    'user_initiated_reset_confirmed':True,'approximate_reset_second':18,'post_reset_no_data_is_spontaneous_reboot_evidence':False,
    'button_type_for_navigation':'BOOT per requested procedure, visual button manipulation and matching submitted page sequence; no separate exact-count reply required for equivalent navigation.',
    'feedback_delivered_to_terminal_candidate':False})
save(VIDEO/'video-review.json',{'run_id':RUN.name,'round':2,'reviewer':'Codex operator','reviewed_at':now,
    'video_sha256':meta['source_sha256'],'duration_seconds':63.3,'source_bytes':meta['source_bytes'],
    'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    'contact_sheets_reviewed':6,'one_second_sample_frames_reviewed':63,'individual_readable_frames_reviewed':selected,
    'findings':[
        {'approximate_seconds':.5,'screen':'GLOBAL RESET; LIVE SEQ1; SOURCE codex-resets.com, fetched timestamp, STALE, last reset2026-09-08T01:56:00Z and elapsed time.'},
        {'approximate_seconds':4.5,'screen':'STATUS; LIVE SEQ1; RECEIVER CONNECTED DATA, FRAME ERROR NONE, last good receive68sec ago; BOOT NEXT PAGE and PC REFRESH.'},
        {'approximate_seconds':6.5,'screen':'USAGE DASHBOARD; five-hour USED42.0% LEFT58.0%, weekly USED18.0% LEFT82.0%, source observed2026-09-11T00:00:00Z, stale/SOURCE STALE and reset unknown.'},
        {'approximate_seconds':7.5,'screen':'Returned to GLOBAL RESET with same input data and sequence1.'},
        {'approximate_seconds':18,'screen':'User explicitly confirms pressing RESET; subsequent WAITING/empty receiver state.'},
        {'interval_seconds':[20.5,30.5],'screen':'Samples show backlit blue panel/header without legible text. Cause not established; do not certify uninterrupted30s readable display.'},
        {'interval_seconds':[31.5,42.5],'screen':'BOOT manipulation again reaches GLOBAL RESET/NO RESET HISTORY, STATUS/RECEIVER NO DATA, USAGE DASHBOARD/WAITING FOR PC FIXTURE and repeats.'},
        {'interval_seconds':[47.5,62.5],'screen':'WAITING FOR PC FIXTURE remains visible in selected frames while board is held/rotated; some views are obscured or out of frame.'}],
    'orientation_and_clipping':'Readable landscape layout before RESET; no material clipping of the required58/82, global reset or diagnostic content in selected frames. Later physical rotation does not establish automatic orientation.',
    'navigation':{'starting_information':'global reset with valid seq1','observed_initial_information_path':[
        {'approximate_second':.5,'view':'global reset'},{'approximate_second':4.5,'view':'diagnostics'},
        {'approximate_second':5.5,'view':'usage'},{'approximate_second':7.5,'view':'global reset'}],
        'three_information_views_reached':True,'returned_to_starting_information':True,'repeatable_navigation_observed_after_reset':True,
        'exact_physical_press_count_separately_confirmed':False,'precise_latency_measured':False},
    'reset':{'user_initiated_reset_confirmed':True,'approximate_reset_second':18,'spontaneous_reboot_verified':False,
        'scope':'Data disappearance after18s attributed to explicitly confirmed manual RESET, not an autonomous reboot. No fresh stimulus was sent after the user reset.'},
    'continuity':{'continuous_30s_readable_valid_data_certified':False,'no_flicker_certified':False,
        'scope':'Valid-data portion is shorter than30s before manual RESET. Post-reset text-free sample interval and obstruction/rotation prevent full C2/no-flicker certification. One-second samples cannot exclude short events.'},
    'reference_reached':True,'product_pass':False,'policy_status':'invalid_for_comparison','quality_reference_cost_eligible':False,
    'candidate_execution_repeated':False})
shutil.copytree(REST/'post-restore-host-checks',OUT/'independent-host-checks')
host=read(OUT/'independent-host-checks/common-stimulus-check.json')
assert host['legacy_collector']['matches_common_reference_payload'] and host['encoder_matches_exact_common_frames']
assert host['receiver_output']==['accepted 0 ok','accepted 1 ok']
pres=OUT/'pre-observation-preservation';pres.mkdir()
for source,name in [(REST/'frozen-validator-audit.json','frozen-validator-audit.json'),(REST/'restore-report.json','restore-report.json'),
    (PACKS/'codex-sol-followup02-pre-observation/package-manifest.json','package-manifest.json'),
    (PACKS/'codex-sol-followup02-pre-observation-create.json','package-create.json'),
    (PACKS/'verify-codex-sol-followup02-pre-observation.py','audit-and-host-checks.py')]:shutil.copy2(source,pres/name)
helpers=OUT/'operator-helpers';helpers.mkdir()
for source in [Path(__file__),RUN.parent/'inspect-codex-sol-followup02-user-video.py',RUN.parent/'preserve-codex-sol-followup-02.py',
    RUN.parent/'observe-codex-sol-followup-02.py',RUN.parent/'review-codex-sol-followup-02-policy.py']:shutil.copy2(source,helpers/source.name)
binding=OUT/'reference-review-binding';binding.mkdir();shutil.copy2(RUN/'run-manifest.json',binding/'pre-review-operator-metadata.json')
save(binding/'binding-note.json',{'run_id':RUN.name,'recorded_at':now,'original_terminal_manifest_sha256':digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256':digest((binding/'pre-review-operator-metadata.json').read_bytes()),
    'scope':'Original terminal bytes satisfy frozen one-review guard; reattach operator sidecars afterward. No ledger terminal hash, execution, measurement, source or past snapshot changes.'})
names=set(before['operator']['evidence'])|{'policy-review.json'}
names.update(p.relative_to(RUN).as_posix() for p in OUT.rglob('*') if p.is_file() and 'frames' not in p.relative_to(OUT).parts)
def evidence(values):return [{'path':n,'sha256':digest((RUN/n).read_bytes())} for n in sorted(values)]
video_names=[n for n in names if '/user-video-01/' in n]
capture_names=['operator-observation/independent-host-checks/common-stimulus-check.json','operator-observation/independent-host-checks/python-frame-to-production-c-stdout.txt',
    'operator-observation/receiver-source-review.json','operator-observation/reference-capture-r1/capture.json',
    'operator-observation/reference-capture-r1/sent-frames.jsonl','operator-observation/reference-capture-r1/device-serial.bin']
report={'run_id':RUN.name,'reference_inputs_sha256':ledger['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
        'RM1':{'status':'pass','reason':'ESP-IDF build completed; same independently preserved genuine artifact uploaded/runs onCOM3, no firmware source change after final build. Manual RESET in video is distinguished from autonomous restart.','evidence':evidence(names)},
        'RM2':{'status':'pass','reason':'Restored own collector payload matches fixed fixture/reference time, own frame encoder and production C pipeline match exact common seq0/1 wire; actual device accepts both identical operator-replayed frames. Byte equality links own collector/encoder to observed device receipt; no broader recovery/oracle claim.','evidence':evidence(capture_names)},
        'RM3':{'status':'pass','reason':'Before user RESET video shows five-hour LEFT58.0%/USED42.0% and weekly LEFT82.0%/USED18.0% with old observed timestamp and SOURCE STALE. Values match accepted fixed payload, not live account usage.','evidence':evidence(video_names)},
        'RM4':{'status':'pass','reason':'Before RESET, usage, global reset/source/fetched/last reset/elapsed and diagnostic receiver/error/seq information are visibly displayed. Later empty-state views are recorded separately.','evidence':evidence(video_names)},
        'RM5':{'status':'pass','reason':'Visual button manipulation cycles valid-data GLOBAL RESET→STATUS→USAGE→GLOBAL RESET and repeats equivalent three-view navigation after manual RESET. Starting global-reset view and exact press count are not new limitations; precise300ms not measured. RST is not used as navigation evidence.','evidence':evidence(video_names)}},
    'product_pass':False,'policy_status':'invalid_for_comparison',
    'note':'Observed reference capability reached under fixed RM items. All preceding/current pipeline violations exclude Sol-series quality and eligible reference-cost aggregation. Full product acceptance/30s readable valid-data continuity, precision timing/full29-case conformance/formal GUI remain incomplete. Confirmed manual RESET clears receiver state without a new stimulus; text-free post-reset samples preserved.'}
save(RUN/'operator-reference-review-input.json',report)
(RUN/'run-manifest.json').write_bytes(original_path.read_bytes())
try:review_run(RUN,report)
except Exception:
    if not read(ledger_path)['runs'][-1]['reviewed']:(RUN/'run-manifest.json').write_bytes((binding/'pre-review-operator-metadata.json').read_bytes())
    raise
after=read(RUN/'run-manifest.json');after['outputs']['build_status']='pass';after['operator']['evidence'].update(before['operator']['evidence'])
assert after['measurement']==original['measurement'] and after['execution']==original['execution']
assert after['outputs']['implementation_commit']==f['commit']==benchmark.git('rev-parse','HEAD',cwd=CO)
assert not benchmark.git('status','--porcelain',cwd=CO)
current_ledger=read(ledger_path);remaining=7200-sum(v['elapsed_seconds'] for v in current_ledger['runs'] if v['round'])
assert current_ledger['state']=='reached' and current_ledger['runs'][-1]['reviewed']
save(OUT/'observation-finalization.json',{'run_id':RUN.name,'round':2,'recorded_at':now,'status':'reference_review_complete',
    'source_and_raw_cost_unchanged':True,'serial_closed':True,'rm_items':{k:'pass' for k in report['items']},
    'reference_status':'pass','policy_status':'invalid_for_comparison','product_pass':False,
    'user_initiated_reset_confirmed':True,'continuous_30s_readable_data_certified':False,'spontaneous_reboot_verified':False,
    'remaining_followup_seconds':remaining,'remaining_followup_rounds':1,'additional_followup_allowed':False,
    'reason_no_more_calls':'Frozen ledger reached observed reference; unused budget/round is not authorization for another call. Series quality remains invalid.',
    'quality_reference_cost_eligible':False,'raw_reasoning_output_tokens':7547,'frozen_normalized_reasoning_tokens':None})
for p in [OUT/'observation-finalization.json',RUN/'operator-reference-review-input.json']:
    after['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',after);verify_evidence(after,RUN);benchmark.verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
print(json.dumps({'run_id':RUN.name,'rm_items':{k:'pass' for k in report['items']},'reference_status':'pass','policy_status':'invalid_for_comparison',
    'product_pass':False,'ledger_state':'reached','quality_reference_cost_eligible':False,'remaining_followup_seconds':remaining,'additional_followup_allowed':False}))
