"""Record the user's black-screen report without inventing BOOT/runtime facts."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys
RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01');CO=RUN/'checkout';OUT=RUN/'operator-observation';CURRENT=OUT/'hardware-attempt-02'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
import benchmark
from benchmark_support import read, save, digest, verify_evidence
from comparison_manager import review_run
from policy_review import validate_review
before=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');ledger_path=Path(before['operator']['comparison']['ledger']);ledger=read(ledger_path)
original_path=OUT/'terminal-originals/run-manifest.json';original=read(original_path)
assert len(ledger['runs'])==1 and not ledger['runs'][0]['reviewed'] and not (RUN/'reference-review.json').exists()
assert digest(original_path.read_bytes())==f['original_terminal_manifest_sha256']==ledger['runs'][0]['terminal_manifest_sha256']
assert before['execution']==original['execution'] and before['measurement']==original['measurement']
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
verify_evidence(before,RUN);validate_review(before,RUN/'run-manifest.json')
now=datetime.now(timezone.utc).isoformat();slot=read(CURRENT/'hardware-slot.json')
observation=CURRENT/'user-black-screen-report.json'
save(observation,{'run_id':RUN.name,'recorded_at':now,'source':'User reply to current 2026-10-06 21:03 KST upload observation question',
    'user_answer_original':'com3 포트에 업로드한게 맞을까? lcd에서는 검은 화면만 나옴',
    'current_upload_at':slot['upload_completed_at'],'implementation_commit':f['commit'],'artifact_sha256':slot['artifact_sha256'],
    'lcd_report':'black screen only','legible_values_observed':False,'boot_press_count':None,'boot_response':None,
    'continuous_30_seconds_observed':None,'user_manual_reset':None,'automatic_reboot_observed':None,
    'runtime_receiver_acceptance':'unconfirmed','video_or_photo_received':False,
    'scope':'User-reported current screen; no camera inspection, confirmed BOOT manipulation, runtime initialization, failure cause or continuity facts are inferred.'})
proof=(CURRENT/'frozen-artifact-upload-stdout.txt').read_text(encoding='utf-8')
assert 'Serial port COM3' in proof and 'Chip is ESP32-S3' in proof and proof.count('Hash of data verified.')==3
binding=OUT/'reference-review-binding';binding.mkdir(exist_ok=False)
shutil.copy2(RUN/'run-manifest.json',binding/'pre-review-operator-metadata.json')
save(binding/'binding-note.json',{'run_id':RUN.name,'original_terminal_manifest_sha256':digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256':digest((binding/'pre-review-operator-metadata.json').read_bytes()),
    'scope':'Use preserved original terminal bytes for frozen review guard once; reattach already preserved operator records. No candidate source/execution/cost or ledger terminal-hash change.'})
def evidence(names):return [{'path':name,'sha256':digest((RUN/name).read_bytes())} for name in names]
current=CURRENT.relative_to(RUN).as_posix()
report={'run_id':RUN.name,'reference_inputs_sha256':ledger['reference_inputs_sha256'],'reviewer':'Codex operator','reviewed_at':now,
    'items':{
        'RM1':{'status':'partial','reason':'Original ESP-IDF5.3.2 ESP32-S3 build and unchanged archived artifact verified; COM3 upload writes all three flash images and verifies their hashes. No runtime-ready/receipt marker or legible panel output was captured, so successful application execution is unconfirmed.','evidence':evidence(['operator-source-freeze.json',current+'/hardware-slot.json',current+'/frozen-artifact-upload-stdout.txt',current+'/console-source-review.json'])},
        'RM2':{'status':'partial','reason':'Restored candidate encoder exactly reproduces common frame0/1 and host serial writes complete1543 bytes each. No accepted or rejected device marker appears in zero-byte captures; device receipt is unconfirmed. Candidate legacy collector differs in eight fields and one of17 provider validity cases differs. No receiver success inferred from write completion.','evidence':evidence(['operator-observation/independent-host-checks/common-stimulus-check.json','operator-observation/host-semantic-limitations.json',current+'/reference-capture-r1/capture.json',current+'/receiver-source-review.json'])},
        'RM3':{'status':'fail','reason':'User reports the current21:03 KST Luna artifact shows only a black screen. Required58% five-hour and82% weekly remaining values are not displayed in this report. Exact receiver state and black-screen cause remain unconfirmed.','evidence':evidence([observation.relative_to(RUN).as_posix()])},
        'RM4':{'status':'not_run','reason':'User reports the current screen is black, but no page-selection/three-information-view observations were supplied. Do not infer unseen alternate views.','evidence':evidence([observation.relative_to(RUN).as_posix()])},
        'RM5':{'status':'not_run','reason':'BOOT press count, response and cycle/return were not reported. No button-failure or navigation success inferred.','evidence':evidence([observation.relative_to(RUN).as_posix()])}},
    'product_pass':False,'policy_status':'invalid_for_comparison',
    'note':'Bounded initial assessment from preserved build/upload/host records and user current-screen report. BOOT/30s continuity/physical optional feature/GUI/full29 oracle remain unmeasured. Earlier11:27 target association remains unconfirmed by user; all logs and cost preserved.'}
save(RUN/'operator-reference-review-input.json',report)
(RUN/'run-manifest.json').write_bytes(original_path.read_bytes())
try:review_run(RUN,report)
except Exception:
    if not read(ledger_path)['runs'][0]['reviewed']:(RUN/'run-manifest.json').write_bytes((binding/'pre-review-operator-metadata.json').read_bytes())
    raise
after=read(RUN/'run-manifest.json');after['operator']['evidence'].update(before['operator']['evidence']);after['outputs']['build_status']='pass'
assert after['measurement']==original['measurement'] and after['execution']==original['execution'] and after['outputs']['implementation_commit']==f['commit']
save(OUT/'observation-finalization.json',{'run_id':RUN.name,'recorded_at':now,'status':'initial_reference_review_complete_with_unmeasured_items',
    'source_and_raw_cost_unchanged':True,'serial_closed':True,'current_upload_at':slot['upload_completed_at'],
    'board_state':'Luna initial original artifact onCOM3; user reports black screen. Device acceptance and BOOT/30s remain unconfirmed.',
    'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'invalid_for_comparison','product_pass':False,
    'followups_run':0,'remaining_followup_seconds':7200,'remaining_followup_rounds':3,'additional_candidate_call_started':False})
shutil.copy2(Path(__file__),OUT/'operator-helpers'/Path(__file__).name)
after['operator']['evidence']['operator-reference-review-input.json']=digest((RUN/'operator-reference-review-input.json').read_bytes())
for p in OUT.rglob('*'):
    if p.is_file():after['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',after);verify_evidence(after,RUN);benchmark.verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
assert read(ledger_path)['runs'][0]['reviewed'] and read(ledger_path)['runs'][0]['reference_status']=='fail'
print(json.dumps({'rm_items':{k:v['status'] for k,v in report['items'].items()},'reference_status':'fail','policy_status':'invalid_for_comparison','product_pass':False,'followups_started':0}))
