"""Apply one evidence-bound initial review; preserve all raw candidate bytes."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01')
REST=Path('C:/meter-run-restores-20261006/codex-sol-r01-pre-observation')
PACKS=Path('C:/meter-run-packages-20261006')
CO=RUN/'checkout';OUT=RUN/'operator-observation';VIDEO=OUT/'user-video-01'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from comparison_manager import review_run
from policy_review import validate_review

before=read(RUN/'run-manifest.json');ledger_path=Path(before['operator']['comparison']['ledger'])
ledger=read(ledger_path);f=read(RUN/'operator-source-freeze.json');meta=read(VIDEO/'video-metadata.json')
original_path=OUT/'terminal-originals/run-manifest.json';original=read(original_path)
assert len(ledger['runs'])==1 and not ledger['runs'][0]['reviewed'] and not (RUN/'reference-review.json').exists()
assert digest(original_path.read_bytes())==f['original_terminal_manifest_sha256']==ledger['runs'][0]['terminal_manifest_sha256']
assert original['measurement']==before['measurement'] and original['execution']==before['execution']
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
verify_evidence(before,RUN);benchmark.verify_agent_inputs(RUN,before);validate_review(before,RUN/'run-manifest.json')
now=datetime.now(timezone.utc).isoformat()

shutil.copytree(REST/'post-restore-host-checks',OUT/'independent-host-checks')
pres=OUT/'pre-observation-preservation';pres.mkdir()
for source,name in [
    (REST/'frozen-validator-audit.json','frozen-validator-audit.json'),
    (REST/'restore-report.json','restore-report.json'),
    (PACKS/'codex-sol-r01-pre-observation/package-manifest.json','package-manifest.json'),
    (PACKS/'codex-sol-r01-pre-observation-create.json','package-create.json'),
    (PACKS/'codex-sol-r01-pre-observation-audit-correction.json','audit-correction.json'),
    (PACKS/'verify-codex-sol-r01-pre-observation.py','original-audit.py'),
    (PACKS/'verify-codex-sol-r01-pre-observation-v2.py','corrected-audit.py')]:shutil.copy2(source,pres/name)
save(pres/'operator-audit-notes.json',{'date':'2026-10-06','run_id':RUN.name,
    'pre_package_assertion':'First helper substring esptool also matched harmless CONFIG_ESPTOOLPY_FLASHSIZE. It failed before metadata/package writes and any new model call. Corrected to command-word regex; all 81 captured commands manually reviewed.',
    'restore_audit_correction':'Original package bytes are verified at package; intentionally rewritten restored paths are validated by frozen validators and preserved execution/measurement identity. Original failed audit retained.',
    'execution_branch_field':original['execution']['branch'],'actual_local_branch_at_freeze':f['candidate_branch'],
    'branch_note':'Manifest experiment branch label and actual local Git branch master differ. Isolation is a separate candidate repository and frozen commit, not a claim that local branch has the label. Preserve original metadata and record this distinction.',
    'tracked_generated_output_files':1413,
    'followup_prerequisite':'Exclude generated build/build-host outputs from only the newly prepared followup working copy and prove product source/input equivalence before invocation. Never rewrite original freeze/package.',
    'operator_source_or_cost_change':False,'additional_model_calls':0})

assert digest((VIDEO/'source.mp4').read_bytes())==meta['source_sha256']
selected=[1,5,8,13]
for n in selected:shutil.copy2(VIDEO/'frames'/f'frame-{n:03d}.png',VIDEO/f'readable-frame-{n:03d}.png')
save(VIDEO/'capture-identity-confirmation.json',{'run_id':RUN.name,'recorded_at':now,
    'video_answer_original':'"'+meta['source_path']+'"',
    'button_answer_original':'Boot를 짧게 3번도, 길게도 눌렸지만 아무 반응 없음. 내가 첨부한 영상과 같음',
    'source':'User replies to current Codex Sol firmware observation and BOOT clarification questions.',
    'video_sha256':meta['source_sha256'],'implementation_commit':f['commit'],
    'artifact_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    'hardware_slot':'operator-observation/hardware-slot.json','filesystem_save_after_upload':True,'capture_time_utc':None,
    'short_boot_presses_confirmed':3,'long_boot_press_confirmed':True,'response_reported':'none'})
save(VIDEO/'video-review.json',{'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':now,
    'video_sha256':meta['source_sha256'],'duration_seconds':meta['duration_seconds'],'source_bytes':meta['source_bytes'],
    'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    'contact_sheets_reviewed':2,'sample_frames_reviewed':13,'individual_readable_frames_reviewed':selected,
    'findings':[
      {'interval_seconds':[0.5,3.5],'screen':'Blue/dark illuminated panel; no legible title, numbers or text.'},
      {'interval_seconds':[4.5,11.5],'screen':'Horizontal cyan/blue/red bands; no legible usage, global reset or diagnostic information.'},
      {'at_seconds':12.5,'screen':'Blue/dark panel again; no readable title or numeric information.'}],
    'orientation_and_clipping':'Board is held horizontally. Text layout/orientation/clipping cannot be assessed because no readable text exists.',
    'navigation':{'starting_information':None,'short_boot_presses_user_confirmed':3,'long_press_user_confirmed':True,
                  'user_reported_response':'none','information_views_reached':[],
                  'visual_band_changes_are_page_navigation_proof':False,'returned_to_initial_information':False},
    'continuity':{'continuous_30s_verified':False,'duration_seconds':12.9,
                  'spontaneous_reboot_verified':False,'precise_latency_measured':False,
                  'scope':'Video is shorter than 30 seconds; one-second samples cannot certify no flicker. Band changes alone do not prove a reboot.'},
    'reference_reached':False,'product_pass':False,'candidate_execution_repeated':False})
shutil.copy2(RUN.parent/'inspect-codex-sol-r01-user-video.py',VIDEO/'inspect-video.py')
shutil.copy2(Path(__file__),VIDEO/'finalize-video-review.py')

# Frozen review requires the original terminal digest. Restore only that operator
# metadata view, apply the review once, then reattach preserved operator sidecars.
binding=OUT/'reference-review-binding';binding.mkdir()
shutil.copy2(RUN/'run-manifest.json',binding/'pre-review-operator-metadata.json')
save(binding/'binding-note.json',{'run_id':RUN.name,'recorded_at':now,
    'original_terminal_manifest_sha256':digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256':digest((binding/'pre-review-operator-metadata.json').read_bytes()),
    'scope':'Use preserved original terminal bytes for unchanged frozen review guard, then reattach operator outputs/evidence. No ledger terminal hash, execution, measurement or candidate source mutation.'})
names=set(before['operator']['evidence'])|{'policy-review.json'}
names.update(p.relative_to(RUN).as_posix() for p in OUT.rglob('*') if p.is_file() and 'frames' not in p.relative_to(OUT).parts)
def evidence(values):return [{'path':name,'sha256':digest((RUN/name).read_bytes())} for name in sorted(values)]
video_names=[n for n in names if '/user-video-01/' in n]
capture_names=['operator-observation/independent-host-checks/common-stimulus-check.json',
    'operator-observation/receiver-source-review.json','operator-observation/reference-capture-r1/capture.json',
    'operator-observation/reference-capture-r1/sent-frames.jsonl','operator-observation/reference-capture-r1/device-serial.bin']
report={'run_id':RUN.name,'reference_inputs_sha256':ledger['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
      'RM1':{'status':'pass','reason':'Native ESP-IDF build completed; no later firmware source changes. Same genuine archived ESP32-S3 artifact uploaded with hash verification and receiver runtime output. LCD product failures are assessed separately.','evidence':evidence(names)},
      'RM2':{'status':'fail','reason':'Candidate encoder matches fixed seq 0/1 bytes, but production C host receiver and actual device reject both common frames with SCHEMA_INVALID. Legacy personal-usage collector also fails SCHEMA_INVALID and differs from common payload. No accepted sequence observed; process exit zero/write completion is not receipt.','evidence':evidence(capture_names)},
      'RM3':{'status':'fail','reason':'Confirmed video has no legible numbers or text; required 58% five-hour and 82% weekly remaining values are absent.','evidence':evidence(video_names)},
      'RM4':{'status':'fail','reason':'After requested observation and user-confirmed BOOT manipulation, no readable usage, global-reset or diagnostic information view is visible. Horizontal color bands are not information categories.','evidence':evidence(video_names)},
      'RM5':{'status':'fail','reason':'User explicitly confirms three short BOOT presses and a long press with no response. No readable information navigation or return path is demonstrated. Precise timing and long-press behavior are not new acceptance requirements.','evidence':evidence(video_names)}},
    'product_pass':False,'policy_status':'eligible',
    'note':'Candidate completed and valid submission format are separate from failed common receiver/display/BOOT behavior. 30-second continuity, precise latency, full legacy host oracle and physical idle backlight feature remain unmeasured.'}
save(RUN/'operator-reference-review-input.json',report)
(RUN/'run-manifest.json').write_bytes(original_path.read_bytes())
try:review_run(RUN,report)
except Exception:
    if not read(ledger_path)['runs'][-1]['reviewed']:
        (RUN/'run-manifest.json').write_bytes((binding/'pre-review-operator-metadata.json').read_bytes())
    raise
after=read(RUN/'run-manifest.json');after['outputs']['build_status']='pass'
after['operator']['evidence'].update(before['operator']['evidence'])
assert after['measurement']==original['measurement'] and after['execution']==original['execution']
assert after['outputs']['implementation_commit']==f['commit']==benchmark.git('rev-parse','HEAD',cwd=CO)
assert not benchmark.git('status','--porcelain',cwd=CO)
save(OUT/'observation-finalization.json',{'run_id':RUN.name,'recorded_at':now,
    'status':'initial_reference_review_complete','source_and_raw_cost_unchanged':True,'serial_closed':True,
    'board_state':'Frozen Codex Sol initial artifact retained; no new firmware rebuild or upload after this observation.',
    'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'eligible','product_pass':False,
    'followups_run':0,'remaining_followup_seconds':7200,'remaining_followup_rounds':3})
for p in [OUT/'observation-finalization.json',RUN/'operator-reference-review-input.json']:
    after['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',after)
verify_evidence(after,RUN);benchmark.verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
assert read(ledger_path)['runs'][0]['reviewed'] and read(ledger_path)['runs'][0]['reference_status']=='fail'
print(json.dumps({'run_id':RUN.name,'rm_items':{k:v['status'] for k,v in report['items'].items()},
    'reference_status':'fail','policy_status':'eligible','product_pass':False,'source_and_cost_unchanged':True}))
