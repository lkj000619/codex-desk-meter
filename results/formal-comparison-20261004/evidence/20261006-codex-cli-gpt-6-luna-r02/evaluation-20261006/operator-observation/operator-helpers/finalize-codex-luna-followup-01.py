"""Apply one bounded review to the unchanged terminal followup submission."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r02');CO=RUN/'checkout';OUT=RUN/'operator-observation'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
import benchmark
from benchmark_support import read, save, digest, verify_evidence
from comparison_manager import review_run
from policy_review import validate_review

before=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
ledger_path=Path(before['operator']['comparison']['ledger']);ledger=read(ledger_path)
original_path=OUT/'terminal-originals/run-manifest.json';original=read(original_path)
assert len(ledger['runs'])==2 and ledger['runs'][0]['reviewed'] and not ledger['runs'][-1]['reviewed']
assert not (RUN/'reference-review.json').exists()
assert digest(original_path.read_bytes())==f['original_terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
assert before['execution']==original['execution'] and before['measurement']==original['measurement']
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
verify_evidence(before,RUN);validate_review(before,RUN/'run-manifest.json')
now=datetime.now(timezone.utc).isoformat();slot=read(OUT/'hardware-slot.json')
runtime=read(OUT/'hardware-post-upload-reset/runtime-source-binding.json')
raw_path=OUT/'hardware-post-upload-reset/reset-and-frames-capture/device-serial.bin'
raw=raw_path.read_bytes();assert len(raw)==5938 and digest(raw)==runtime['raw_log_sha256']
assert runtime['boot_elf_sha_prefix_matches'] and runtime['usb_receiver_ready_observed'] and b'SPI SRAM memory test OK' in raw
assert not runtime['receiver_accepted_sequences'] and not runtime['receiver_rejected_errors']
save(OUT/'hardware-post-upload-reset/runtime-observation-correction.json',{
    'run_id':RUN.name,'recorded_at':now,'applies_to':'runtime-source-binding.json psram_memory_test_ok only',
    'original_record_sha256':digest((OUT/'hardware-post-upload-reset/runtime-source-binding.json').read_bytes()),
    'original_value':runtime['psram_memory_test_ok'],'corrected_value':True,
    'raw_log_sha256':digest(raw),'exact_observed_marker':'esp_psram: SPI SRAM memory test OK',
    'reason':'Original marker matching returned false despite the preserved raw log. Original record and source/build/cost remain unchanged.'})
observation=OUT/'user-black-screen-report.json'
save(observation,{'run_id':RUN.name,'recorded_at':now,'source':'User reply to followup1 COM3 upload22:51 KST and supplemental reset22:54 KST observation question',
    'question_item_id':'["request_user_input_async","call_3s0ngrTn6y4ZIOtSkQOp4E1c",0]',
    'user_answer_original':'검은 화면이 계속됨','current_upload_at':slot['upload_completed_at'],
    'supplemental_reset_at':runtime['reset_requested_at'],'implementation_commit':f['commit'],'artifact_sha256':slot['artifact_sha256'],
    'lcd_report':'black screen only','legible_values_observed':False,'boot_press_count':None,'boot_response':None,
    'continuous_30_seconds_observed':None,'user_manual_reset':None,'automatic_reboot_observed':None,
    'runtime_receiver_acceptance':'unconfirmed','video_or_photo_received':False,
    'scope':'Current followup1 screen report only. BOOT manipulation, 30-second continuity, manual reset, automatic reboot and black-screen cause are not inferred.'})
proof=(OUT/'frozen-artifact-upload-stdout.txt').read_text(encoding='utf-8')
assert 'Serial port COM3' in proof and 'Chip is ESP32-S3' in proof and proof.count('Hash of data verified.')==3
binding=OUT/'reference-review-binding';binding.mkdir(exist_ok=False)
shutil.copy2(RUN/'run-manifest.json',binding/'pre-review-operator-metadata.json')
save(binding/'binding-note.json',{'run_id':RUN.name,'original_terminal_manifest_sha256':digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256':digest((binding/'pre-review-operator-metadata.json').read_bytes()),
    'scope':'Use preserved original terminal bytes for frozen review guard once, then reattach operator records. No candidate source/execution/cost or ledger terminal-hash change.'})
def evidence(names):return [{'path':name,'sha256':digest((RUN/name).read_bytes())} for name in names]
obs=observation.relative_to(RUN).as_posix();hw='operator-observation/'
report={'run_id':RUN.name,'reference_inputs_sha256':ledger['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
        'RM1':{'status':'pass','reason':'Unchanged original ESP-IDF5.3.2 ESP32-S3 build and COM3 upload verified. All three flash hashes verify, and supplemental boot log ELF SHA prefix matches the frozen ELF; application reaches USB receiver ready. This establishes execution, not readable LCD.','evidence':evidence(['operator-source-freeze.json',hw+'hardware-slot.json',hw+'frozen-artifact-upload-stdout.txt',hw+'hardware-post-upload-reset/runtime-source-binding.json',hw+'hardware-post-upload-reset/runtime-observation-correction.json'])},
        'RM2':{'status':'partial','reason':'Independently restored declared common collector/encoder exactly match common fixture and frames0/1; archived production C CLI accepts both. Both physical host writes complete1543 bytes, but neither capture has accepted/rejected device markers. Actual device acceptance remains unconfirmed.','evidence':evidence([hw+'independent-host-checks/common-stimulus-check.json',hw+'host-semantic-review.json',hw+'reference-capture-r1/capture.json',hw+'hardware-post-upload-reset/runtime-source-binding.json'])},
        'RM3':{'status':'fail','reason':'User reports continued black screen on current followup1 firmware after upload and supplemental reset. Required58% five-hour and82% weekly remaining values are not displayed in this report. Cause and actual frame receipt remain unconfirmed.','evidence':evidence([obs])},
        'RM4':{'status':'not_run','reason':'No selected-page/three-information-view observations were supplied. Do not infer unseen alternate views from the black current screen.','evidence':evidence([obs])},
        'RM5':{'status':'not_run','reason':'BOOT press count, response and cycle/return were not reported. No navigation success or button-failure claim inferred.','evidence':evidence([obs])}},
    'product_pass':False,'policy_status':'invalid_for_comparison',
    'note':'Bounded followup1 assessment. Own Python22/C3 and candidate29 wire cases do not establish frozen operator29 pipeline, GUI, physical optional feature or BOOT/30s pass. Prior first verdict/evidence/cost/freeze remain unchanged.'}
save(RUN/'operator-reference-review-input.json',report)
(RUN/'run-manifest.json').write_bytes(original_path.read_bytes())
try:review_run(RUN,report)
except Exception:
    if not read(ledger_path)['runs'][-1]['reviewed']:(RUN/'run-manifest.json').write_bytes((binding/'pre-review-operator-metadata.json').read_bytes())
    raise
after=read(RUN/'run-manifest.json');after['operator']['evidence'].update(before['operator']['evidence']);after['outputs']['build_status']='pass'
assert after['measurement']==original['measurement'] and after['execution']==original['execution'] and after['outputs']['implementation_commit']==f['commit']
remaining=ledger['limits']['remediation_seconds']-sum(r['elapsed_seconds'] for r in ledger['runs'][1:]);assert remaining==4213
save(OUT/'observation-finalization.json',{'run_id':RUN.name,'recorded_at':now,'status':'followup01_reference_review_complete_with_unmeasured_items',
    'source_and_raw_cost_unchanged':True,'serial_closed':True,'current_upload_at':slot['upload_completed_at'],
    'board_state':'Luna followup1 original artifact onCOM3; matching application boot/USB ready observed, user reports continued black screen. Device acceptance and BOOT/30s unconfirmed.',
    'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'invalid_for_comparison','product_pass':False,
    'followups_run':1,'remaining_followup_seconds':remaining,'remaining_followup_rounds':2,'additional_candidate_call_started':False})
shutil.copy2(Path(__file__),OUT/'operator-helpers'/Path(__file__).name)
after['operator']['evidence']['operator-reference-review-input.json']=digest((RUN/'operator-reference-review-input.json').read_bytes())
for p in OUT.rglob('*'):
    if p.is_file():after['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',after);verify_evidence(after,RUN);benchmark.verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
reviewed=read(ledger_path);assert reviewed['runs'][0]==ledger['runs'][0]
assert reviewed['runs'][-1]['reviewed'] and reviewed['runs'][-1]['reference_status']=='fail'
assert digest((RUN/'comparison-source.bundle').read_bytes())==digest((RUN/'operator-terminal-source.bundle').read_bytes())
print(json.dumps({'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'invalid_for_comparison','product_pass':False,'remaining_followup_seconds':remaining,'remaining_followup_rounds':2}))
