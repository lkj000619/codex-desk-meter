"""Apply the operator RM review after the user's explicit video identity confirmation."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
CO=RUN/'checkout'
VIDEO=RUN/'operator-observation/user-video-01'
FROZEN_PACKAGE=Path('C:/meter-run-packages-20261005/opencode-muse-r02-provisional')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import digest,read,save,verify_evidence
from benchmark import verify_agent_inputs
from policy_review import validate_review
from comparison_manager import review_run

m=read(RUN/'run-manifest.json')
ledger_path=Path(m['operator']['comparison']['ledger'])
ledger=read(ledger_path)
freeze=read(RUN/'operator-source-freeze.json')
assert m['operator']['status']=='timeout' and m['outputs']['implementation_commit'] is None
assert ledger['runs'][-1]['reviewed'] is False
assert digest((RUN/'run-manifest.json').read_bytes())==freeze['terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
verify_agent_inputs(RUN,m);verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']
assert subprocess.check_output(['git','status','--porcelain'],cwd=CO,text=True).strip()==''
assert not (CO/m['outputs']['structured_result']).exists() and not (CO/m['outputs']['selection_document']).exists()
confirmation={'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),'source':'User reply to video capture identity question',
              'question':'Does this video show the first r02 firmware upload at 01:45 KST, before the later 02:50 reupload?',
              'answer':'Confirmed: filmed after the first followup upload.',
              'answer_original':'\uB9DE\uC74C: \uCC98\uC74C \uD6C4\uC18D \uC5C5\uB85C\uB4DC \uC774\uD6C4 \uCD2C\uC601',
              'video_sha256':digest((VIDEO/'source.mp4').read_bytes()),'implementation_commit':freeze['commit'],
              'artifact_sha256':freeze['artifacts']['firmware/build/cdm_meter.bin']['sha256'],
              'hardware_slot':'operator-observation/hardware-slot.json',
              'capture_time_utc':None,'second_upload_video_claimed':False}
save(VIDEO/'capture-identity-confirmation.json',confirmation)
video_review=read(VIDEO/'video-review.json')
save(VIDEO/'confirmed-video-review.json',{**video_review,'status':'capture_identity_confirmed',
     'capture_identity_note':'User explicitly confirmed first r02 upload; precise capture time remains unknown.',
     'confirmation':'capture-identity-confirmation.json','confirmation_sha256':digest((VIDEO/'capture-identity-confirmation.json').read_bytes())})

source_meta=read(FROZEN_PACKAGE/'operator/operator-source-snapshot.json')
source_paths=['operator-source-snapshot.json']+[v['operator_copy'] for v in source_meta['files'].values()]
for name in source_paths:
    source=FROZEN_PACKAGE/'operator'/name
    target=RUN/name
    assert not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)

paths=['operator-source-freeze.json','operator-terminal-manifest-original.json','operator-source.bundle',
       'operator-source-bundle.json','operator-policy-audit.json','policy-review.json']+source_paths
paths += [p.relative_to(RUN).as_posix() for p in (RUN/'operator-observation').rglob('*')
          if p.is_file() and 'user-video-01' not in p.relative_to(RUN).parts]
paths += ['operator-observation/user-video-01/'+name for name in [
    'source.mp4','video-metadata.json','video-review.json','confirmed-video-review.json','capture-identity-confirmation.json','metadata-raw.txt']]
paths += [p.relative_to(RUN).as_posix() for p in VIDEO.glob('readable-frame-*.jpg')]
paths += [p.relative_to(RUN).as_posix() for p in VIDEO.glob('contact-*.jpg')]
paths=sorted(set(paths))
def evidence(names):return [{'path':name,'sha256':digest((RUN/name).read_bytes())} for name in names]
video_paths=[name for name in paths if '/user-video-01/' in name]
capture_paths=['operator-observation/common-stimulus-check.json','operator-observation/receiver-source-review.json',
               'operator-observation/reference-capture-r1/capture.json','operator-observation/reference-capture-r1/sent-frames.jsonl',
               'operator-observation/reference-capture-r1/device-serial.bin']
report={'run_id':RUN.name,'reference_inputs_sha256':m['operator']['comparison']['reference_inputs_sha256'],
        'reviewer':'Codex operator','reviewed_at':datetime.now(timezone.utc).isoformat(),'items':{
    'RM1':{'status':'pass','reason':'Candidate IDF build completed before timeout; unchanged frozen artifact was uploaded and ran on COM3. Same-app receiver accepted fixed seq 0/1. Final candidate result and selection submissions remain missing.','evidence':evidence(paths)},
    'RM2':{'status':'partial','reason':'Encoder matches both fixed frames and real receiver accepts them. Hardware used operator replay. Actual collector rejects the common stale personal-usage fixture with STALE_THRESHOLD_EXCEEDED and exit 2, so collector-to-device conformance is incomplete.','evidence':evidence(capture_paths)},
    'RM3':{'status':'partial','reason':'Confirmed video shows openai/five-hour REM 58% around 28.5s. Weekly remaining 82% is absent from the observed usage view. Both required windows are not reproduced.','evidence':evidence(video_paths)},
    'RM4':{'status':'partial','reason':'Usage, global-reset and diagnostic views are visible. Global reset incorrectly reports default/no history and obs:n/a despite reference payload having reset dates. STATUS says STALE:NO and LAST-GOOD uses transport sent_at; correctness of all required information is incomplete.','evidence':evidence(video_paths+['operator-observation/common-stimulus-check.json'])},
    'RM5':{'status':'pass','reason':'Physical button manipulation in the confirmed video navigates STATUS -> DASHBOARD -> GLOBAL RESET -> STATUS around 24.5/28.5/30.5/32.5s, returning to starting information; earlier transitions also occur. This assesses three-view navigation; RM3/RM4 separately assess data correctness. Exact press count and 300ms latency are unmeasured.','evidence':evidence(video_paths)}},
    'product_pass':False,'policy_status':'invalid_for_comparison',
    'note':'Timed-out residual implementation, not a complete submission. User confirmed video of first r02 upload. One-second optical samples do not certify flicker-free 30s or precise latency. Intentional USB power removal is separate from powered-link recovery.'}
save(RUN/'operator-reference-review-input.json',report)
review_run(RUN,report)
after=read(RUN/'run-manifest.json');ledger_after=read(ledger_path)
assert after['outputs']['implementation_commit']==freeze['commit']
assert ledger_after['runs'][-1]['reviewed'] is True and ledger_after['runs'][-1]['reference_status']=='fail'
assert after['measurement']==m['measurement'] and after['execution']==m['execution']
verify_evidence(after,RUN);verify_agent_inputs(RUN,after);validate_review(after,RUN/'run-manifest.json')
elapsed=sum(item['elapsed_seconds'] or 0 for item in ledger_after['runs'] if item['round'])
assert elapsed>=ledger_after['limits']['remediation_seconds']
completion={'comparison_id':ledger_after['comparison_id'],'recorded_at':datetime.now(timezone.utc).isoformat(),
            'derived_state':'budget_exhausted','reason':'Fixed cumulative remediation budget consumed by timed-out followup; not a user cancellation.',
            'ledger_state':ledger_after['state'],'ledger_state_note':'Frozen tool leaves fail-reviewed series active; prepare-next independently rejects remaining budget below 1 second.',
            'remaining_followup_seconds':0,'additional_followup_allowed':False,
            'followup_elapsed_seconds':elapsed,'followups_run':1,'last_run_id':RUN.name,
            'rm_items':{key:item['status'] for key,item in report['items'].items()},'reference_status':'fail',
            'policy_status':'invalid_for_comparison','product_pass':False,'candidate_result_submission':'missing',
            'candidate_selection_document_submission':'missing','implementation_commit':freeze['commit'],
            'original_terminal_manifest_sha256':freeze['terminal_manifest_sha256'],
            'reviewed_manifest_sha256':digest((RUN/'run-manifest.json').read_bytes()),
            'reviewed_ledger_sha256':digest(ledger_path.read_bytes()),'raw_cost_preserved':True}
save(RUN/'operator-series-completion.json',completion)
save(RUN/'operator-observation/observation-finalization.json',{
    'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'rm_observation_complete',
    'reviewed_video_hardware_slot':'operator-observation/hardware-slot.json',
    'second_upload_hardware_slot':'operator-observation/recapture-r2-20261005/hardware-slot.json',
    'user_video_capture_identity_confirmed':True,'board_currently_has_same_frozen_artifact':True,
    'serial_closed':True,'board_slot_released_for_next_candidate':True,
    'next_candidate_initial':'20261005-antigravity-cli-agy-flash-r01'})
print(json.dumps(completion,ensure_ascii=False,indent=2))
