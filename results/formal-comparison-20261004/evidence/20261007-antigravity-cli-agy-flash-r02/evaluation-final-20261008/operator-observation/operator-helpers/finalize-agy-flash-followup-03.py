"""Apply one bound optical RM review; preserve terminal bytes and prior judgments."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

RUN = Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02')
OUT = RUN / 'operator-observation'; VIDEO = OUT / 'user-video-01'
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
import benchmark
from benchmark_support import read, save, digest, verify_evidence
from comparison_manager import review_run
from policy_review import validate_review

before = read(RUN / 'run-manifest.json'); freeze = read(RUN / 'operator-source-freeze.json')
ledger_path = Path(before['operator']['comparison']['ledger']); prior = read(ledger_path)
original_path = OUT / 'terminal-originals/run-manifest.json'; original = read(original_path)
assert len(prior['runs']) == 4 and all(x['reviewed'] for x in prior['runs'][:3]) and not prior['runs'][-1]['reviewed']
assert not (RUN / 'reference-review.json').exists()
assert digest(original_path.read_bytes()) == freeze['original_terminal_manifest_sha256'] == prior['runs'][-1]['terminal_manifest_sha256']
assert before['execution'] == original['execution'] and before['measurement'] == original['measurement']
assert original['operator']['status'] == 'completed' and original['measurement']['tokens']['total'] == 713570
assert benchmark.git('rev-parse', 'HEAD', cwd=RUN/'checkout') == freeze['commit']
assert not benchmark.git('status', '--porcelain', cwd=RUN/'checkout')
verify_evidence(before, RUN)
assert validate_review(before, RUN/'run-manifest.json')['decision']['status'] == 'eligible'
now = datetime.now(timezone.utc).isoformat(); slot = read(OUT/'hardware-slot.json'); metadata = read(VIDEO/'video-metadata.json')
assert digest((VIDEO/'source.mp4').read_bytes()) == metadata['source_sha256'] == 'b182132aedf1b1002d2448d4d6458f6ec33b8cd7af9b76be55c9e7daee0c5b0d'
assert metadata['duration_seconds'] == 62.87 and len(metadata['sample_frames']) == 63
assert slot['receiver_acceptance_observed'] and slot['artifact_sha256'] == freeze['artifacts']['build/meter_esp32s3.bin']['sha256']
identity = dict(run_id=RUN.name, recorded_at=now, video_sha256=metadata['source_sha256'],
    implementation_commit=freeze['commit'], artifact_sha256=slot['artifact_sha256'], upload_completed_at=slot['upload_completed_at'],
    observation_question_item_id='["request_user_input_async","call_4dbb5a47e395407cbaf433b6d716443c",0]',
    user_answer_original='"C:\\Users\\이광진\\Documents\\카카오톡 받은 파일\\KakaoTalk_20261007_041523508.mp4" boot 연속 3회 눌렸고 reset 버튼도 누르고 전원도 뺐다가 꽂고, lcd 회전도 되는지 확인함',
    identity_basis='Direct reply to the current Flash final followup3 observation question. File saved after the04:12KST upload. Exact camera capture UTC is unknown.',
    boot_short_press_count_reported=3, user_manual_reset=True, user_power_cycle=True, physical_rotation_attempted=True,
    exact_button_and_power_event_times=None, automatic_reboot_observed=None,
    scope='Current final followup3 only; earlier Flash/Luna videos are not substituted.')
save(OUT/'user-observation-confirmation.json', identity)
save(VIDEO/'capture-identity-confirmation.json', identity)
visual = dict(run_id=RUN.name, round=3, reviewed_at=now, reviewer='Codex operator',
    video_sha256=metadata['source_sha256'], duration_seconds=62.87, contact_sheets_reviewed=6,
    one_second_sample_frames_reviewed=63, individual_readable_frames_reviewed=[3,7,8,10,21,29,34,51],
    lcd_output_present=True, normal_readable_screen_observed=True, required_usage_values_observed=True,
    three_information_views_observed=True, boot_navigation_observed=True,
    observed='At0.5-5.5s the dashboard shows5-hour58% REMAINING and weekly82% REMAINING with STALE. At6.5s GLOBAL RESETS shows a populated latest reset and source details;7.5-8.5s SYSTEM STATUS shows sequence1, cached snapshot1/resets2;9.5s returns to the populated dashboard. Later samples show repeated navigation. The data remains present in sampled views through31.5s during physical movement/rotation. At32.5s and40.5s dark samples are followed by WAITING FOR USB DATA; user confirms both manual RESET and power cycling, without exact event timestamps. At47.5-51.5s reset/default/empty diagnostic/dashboard pages remain navigable. After the late power reconnection the waiting screen returns.',
    boot_press_count_user_reported=3, boot_cycle_samples={'usage':0.5,'global_resets':6.5,'diagnostic':7.5,'usage_return':9.5},
    manual_reset_user_confirmed=True, power_cycle_user_confirmed=True, exact_manipulation_times=None,
    automatic_restart_conclusion='Not established. Manual RESET and power cycling are confirmed; dark/waiting samples alone are not counted as automatic crashes.',
    continuous_30_seconds_verified=False, precise_input_display_latency='not_measured',
    orientation_feature_status='unverified',
    orientation_observation='User physically rotates the board. Sampled UI remains in its0-degree layout, including inverted/vertical physical positions; a calibrated stable0/180 automatic flip/debounce/return or shake test is not established.',
    product_pass=False,
    scope='RM display/navigation confirmed. One-second samples with movement/glare and manual resets do not certify flicker-free30-second continuity, precise300ms/2s timing, full error/recovery/provider matrix, autonomous IMU feature or full GUI scoring.')
save(VIDEO/'video-review.json', visual)
save(OUT/'product-observation-scope.json', {'run_id':RUN.name,'recorded_at':now,'product_pass':False,
    'C2_continuous_30s':'not_certified','C8_300ms':'not_measured','I4_2s':'not_measured',
    'F9_IMU_auto_flip_and_shake':'not_verified','powered_USB_disconnect_recovery':'not_run',
    'full_provider_error_recovery_matrix':'not_run','formal_GUI_scores':'not_scored',
    'global_source_freshness':'Video global page says FRESH while captured source timestamp is old relative to the fixed reference time. Complete source-age/status conformance is not certified; preserve this observation separately from RM4 screen presence.',
    'reset_and_power_cycle_data_loss':'After user RESET/power cycle, WAITING/default/cache0 are visible. No operator data retransmission follows; this observation does not test a powered link-only disconnect or establish automatic reboot.',
    'reference_match_does_not_imply_full_product_acceptance':True})
for helper in [Path(__file__), RUN.parent/'inspect-agy-flash-followup03-user-video.py']:
    shutil.copy2(helper, OUT/'operator-helpers'/helper.name)
binding = OUT/'reference-review-binding'; binding.mkdir(exist_ok=False)
shutil.copy2(RUN/'run-manifest.json', binding/'pre-review-operator-metadata.json')
save(binding/'binding-note.json', {'run_id':RUN.name,'original_terminal_manifest_sha256':digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256':digest((binding/'pre-review-operator-metadata.json').read_bytes()),
    'scope':'Apply frozen review once with exact preserved terminal bytes, then reattach post-run operator evidence. Source, execution and713570 normalized tokens remain unchanged.'})
prefix = 'operator-observation/'
def evidence(names): return [{'path':name,'sha256':digest((RUN/name).read_bytes())} for name in names]
visual_evidence = [prefix+'user-observation-confirmation.json',prefix+'user-video-01/video-review.json',prefix+'user-video-01/video-metadata.json',prefix+'user-video-01/source.mp4']
report = {'run_id':RUN.name,'reference_inputs_sha256':prior['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
        'RM1':{'status':'pass','reason':'Candidate ESP-IDF5.3.2 final build succeeds. Archived original app/bootloader/partition hashes match COM3 upload; the same frozen artifact boots and visibly runs. No operator firmware rebuild.',
            'evidence':evidence(['operator-source-freeze.json',prefix+'hardware-slot.json',prefix+'frozen-artifact-upload-stdout.txt',prefix+'build-source-review.json'])},
        'RM2':{'status':'pass','reason':'Declared collector API modes and encoder produce exact common payload/wire. Actual ESP32 receiver explicitly accepts both common sequence0 and1 with usage1/resets2; raw device serial is preserved.',
            'evidence':evidence([prefix+'common-stimulus-check.json',prefix+'reference-capture-r1/capture.json',prefix+'reference-capture-r1/device-serial.bin',prefix+'receiver-source-review.json'])},
        'RM3':{'status':'pass','reason':'Current same-artifact video displays5-hour58% REMAINING and weekly82% REMAINING, matching fixed stale payload percent_remaining. Corresponding used values42%/18% and STALE are visible. These are synthetic common fixture values.',
            'evidence':evidence(visual_evidence+[prefix+'user-video-01/frames/frame-010.png'])},
        'RM4':{'status':'pass','reason':'Populated usage, GLOBAL RESETS with latest reset/source details, and SYSTEM STATUS with sequence1/cache are visible as three distinct information views. This does not certify all reset/source freshness/GUI contract details.',
            'evidence':evidence(visual_evidence+[prefix+'user-video-01/frames/frame-007.png',prefix+'user-video-01/frames/frame-008.png'])},
        'RM5':{'status':'pass','reason':'User confirms three consecutive BOOT presses. Before reset/default state, recording shows usage->global resets->diagnostic->usage return at approximately0.5/6.5/7.5/9.5s; later repeat navigation is visible. Confirmed RST/power events are recorded separately and are not navigation evidence. Exact debounce-to-display300ms is unmeasured.',
            'evidence':evidence(visual_evidence+[prefix+'user-video-01/frames/frame-010.png'])}},
    'product_pass':False,'policy_status':'eligible',
    'note':'Final authorized followup3. RM1-5 reached; current policy eligible, earlier series invalid_for_comparison remains. Quality/reference cost ineligible. Full product,30s stability, timing, IMU and recovery/GUI validation are not certified. No further round/new block.'}
save(RUN/'operator-reference-review-input.json', report)
(RUN/'run-manifest.json').write_bytes(original_path.read_bytes())
try: review_run(RUN, report)
except Exception:
    if not read(ledger_path)['runs'][-1]['reviewed']:
        (RUN/'run-manifest.json').write_bytes((binding/'pre-review-operator-metadata.json').read_bytes())
    raise
after=read(RUN/'run-manifest.json'); after['operator']['evidence'].update(before['operator']['evidence']); after['outputs']['build_status']='pass'
ledger=read(ledger_path); assert ledger['runs'][:3]==prior['runs'][:3] and all(x['reviewed'] for x in ledger['runs']) and ledger['state']=='reached'
spent=sum(x['elapsed_seconds'] for x in ledger['runs'][1:]); remaining=7200-spent
tokens=sum(x['tokens']['total'] for x in ledger['runs']); elapsed=sum(x['elapsed_seconds'] for x in ledger['runs'])
assert abs(remaining-4303.593)<0.00001 and tokens==3892990 and abs(elapsed-3659.220)<0.00001
completion={'comparison_id':ledger['comparison_id'],'recorded_at':now,'derived_state':'observed_reference_reached','ledger_state':'reached',
    'reason':'All five RM items are observed in final followup3; current attempt eligible but prior series invalidity retained. Initial plus three followups ended; unused time does not permit another round.',
    'initial_attempts':1,'followup_rounds':3,'candidate_invocations':4,'reference_reached_at_round':3,
    'final_run_id':RUN.name,'final_implementation_commit':freeze['commit'],'reference_status':'pass',
    'rm_items':{key:value['status'] for key,value in report['items'].items()},'product_pass':False,
    'final_run_policy_status':'eligible','effective_policy_status':'invalid_for_comparison','quality_reference_cost_eligible':False,
    'series_measured_seconds':elapsed,'followup_measured_seconds':spent,'series_normalized_tokens':tokens,'known_series_normalized_tokens':tokens,'token_measurement_coverage':'4/4',
    'remaining_unused_followup_seconds':remaining,'remaining_followup_rounds':0,'additional_followup_allowed':False,
    'ledger_sha256':digest(ledger_path.read_bytes()),'video_sha256':metadata['source_sha256'],
    'user_initiated_reset_confirmed':True,'user_power_cycle_confirmed':True,'boot_press_count_reported':3,
    'normal_readable_screen_observed':True,'continuous_30s_readable_valid_data_certified':False,
    'original_source_execution_cost_and_prior_results_preserved':True}
save(OUT/'operator-series-completion.json',completion)
save(OUT/'observation-finalization.json',dict(completion,run_id=RUN.name,status='followup03_final_reference_review_complete_with_unmeasured_items',serial_closed=True,
    board_state='Same frozen Flash final followup3 app remains; after confirmed user RESET/power cycle latest video shows WAITING/default without operator retransmission. No automatic restart conclusion.'))
after['operator']['evidence']['operator-reference-review-input.json']=digest((RUN/'operator-reference-review-input.json').read_bytes())
for path in OUT.rglob('*'):
    if path.is_file(): after['operator']['evidence'][path.relative_to(RUN).as_posix()]=digest(path.read_bytes())
assert after['measurement']==original['measurement'] and after['execution']==original['execution'] and after['outputs']['implementation_commit']==freeze['commit']
save(RUN/'run-manifest.json',after); verify_evidence(after,RUN); benchmark.verify_agent_inputs(RUN,after)
assert validate_review(after,RUN/'run-manifest.json')['decision']['status']=='eligible'
assert digest((RUN/'comparison-source.bundle').read_bytes())==digest((RUN/'operator-terminal-source.bundle').read_bytes())
print(json.dumps({'rm':completion['rm_items'],'reference':'pass','product_pass':False,'remaining_seconds':remaining,'rounds':0,'series_tokens':tokens}))
