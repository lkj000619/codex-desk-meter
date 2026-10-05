"""Record verified native start without modifying the active candidate."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys

ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-pro-r04')
PREV=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-pro-r01');RENEWAL=Path('C:/meter-preflight-20261005/renewal')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import digest,read,save

m=read(RUN/'run-manifest.json');assert m['operator']['status']=='running' and m['execution']['started_at']
raw=(RUN/'stdout.jsonl').read_bytes();raw=raw[:raw.rfind(b'\n')+1];events=[json.loads(s) for s in raw.splitlines()]
init=events[0]['init'];assert init['model']=='gemini-3.1-pro-high' and init['permission_mode']=='request-review'
assert Path(init['cwd']).resolve()==Path(m['execution']['worktree']).resolve()
now=datetime.now(timezone.utc).isoformat()
save(RUN/'native-start-observation.json',{'run_id':RUN.name,'observed_at':now,'status':'running',
    'native_conversation_id':events[0]['conversation_id'],'native_model':init['model'],'permission_mode':init['permission_mode'],
    'native_cwd':init['cwd'],'raw_log_prefix_events':len(events),'raw_log_prefix_bytes':len(raw),'raw_log_prefix_sha256':digest(raw),
    'scope':'Native start only; prefix is not a terminal log, final cost, submission or policy review.'})
(RUN/'native-start-observation-prefix.jsonl').write_bytes(raw)
PUBLIC=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'launch-20261005';PUBLIC.mkdir(parents=True,exist_ok=False)
names=['experiment-launch.json','run-manifest.json','profile.json','candidate-inputs.json','agent-context.json','prompt.txt',
    'feedback.json','candidate-feedback.json','native-start-observation.json','native-start-observation-prefix.jsonl',
    'execution-preflight.json','runner-console.txt','runner-console-stderr.txt']
names += [p.relative_to(RUN).as_posix() for p in (RUN/'operator-launch-preflight').rglob('*') if p.is_file()]
names += [p.relative_to(RUN).as_posix() for p in (RUN/'feedback-evidence').rglob('*') if p.is_file()]
for name in names:
    dest=PUBLIC/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
shutil.copy2(Path(m['operator']['comparison']['ledger']),PUBLIC/'ledger-at-start.json')
for p in (RUN.parent/'launch-agy-pro-r04.py',RUN.parent/'launch-agy-pro-r04.ps1',Path(__file__)):
    shutil.copy2(p,PUBLIC/p.name)
shutil.copy2(RUN.parent/'agy-pro-followup-r04-preparation.json',PUBLIC/'followup-preparation.json')
save(PUBLIC/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,
    'files':{p.relative_to(PUBLIC).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in PUBLIC.rglob('*') if p.is_file()},
    'scope':'Followup launch snapshot and native prefix; not terminal evidence. Own prior final evidence remains unchanged.'})
progress_path=ROOT/'results/formal-comparison-20261004/progress.json';p=read(progress_path)
initial=read(PREV/'run-manifest.json');rm=read(PREV/'reference-review.json')
p['current_series_initial']={'run_id':PREV.name,'status':initial['operator']['status'],
    'measurement':initial['measurement'],'rm_items':{k:v['status'] for k,v in rm['items'].items()},
    'reference_status':'fail','policy_status':'eligible','product_pass':False,'candidate_result_submission':'missing',
    'implementation_commit':initial['outputs']['implementation_commit'],
    'final_package_manifest_sha256':'66d9141c9c1945fb214587680c3d84e9b1dd20eae2163f4aec372bafb98ff746',
    'final_package_files_verified':338,'video_sha256':None}
for key in ('rm_items','reference_status','product_pass','optical_video_received','video_capture_identity_confirmed','video_sha256',
    'final_package_manifest_sha256','final_package_files_verified','independent_restore','final_rm_review','implementation_commit',
    'hardware_artifact_sha256','hardware_upload','hardware_reference_capture','hardware_reference_capture_error',
    'receiver_acceptance_observed','candidate_result_submission','candidate_selection_document_submission','candidate_host_tests',
    'candidate_collector_common_payload_match','candidate_encoder_common_wire_match','operator_audited_user_interventions'):
    p.pop(key,None)
launcher=read(RUN/'experiment-launch.json')
p.update(checked_at=now,state='agy_flash_followup_1_running',current_run=RUN.name,current_directory=str(RUN),
    product_executions_started=8,product_executions_completed=7,followups_started=5,round=3,
    model=init['model'],started_at=m['execution']['started_at'],ended_at=None,timeout_seconds=m['execution']['timeout_seconds'],
    launcher_pid=launcher['launcher_pid'],profile_sha256=m['execution']['profile_sha256'],
    input_bundle_sha256=m['execution']['input_bundle_sha256'],receipt_sha256=digest((RUN/'execution-preflight.json').read_bytes()),
    policy_review_required=True,policy_status='pending_terminal_review',rm_review='awaiting_candidate_terminal',
    elapsed_seconds=None,tokens=m['measurement']['tokens'],user_interventions_reported=None,
    operator_implementation_feedback_sent_during_run=False,operator_observational_feedback_supplied_before_run=True,
    followups_started_for_current_series=3,remaining_current_series_followup_seconds='Running round reserved up to 7066; actual remainder computed from terminal elapsed.',
    current_native_scope='Private scoped AGY settings active until child exits; then launcher restores original global bytes.',
    candidate_terminal_status_observed='running',ongoing_usage_not_terminal=True,last_event_count=len(events),remaining_current_series_followup_rounds=1,additional_candidate_round_start_authorized_now=False,
    native_conversation_id=events[0]['conversation_id'],native_model_verified=init['model'],
    native_permission_mode_verified=init['permission_mode'],native_tool_events_observed=None,
    last_step_type=events[-1].get('step_update',{}).get('step_type'),last_step_state=events[-1].get('step_update',{}).get('state'),
    launch_operator_errors_before_model=0,operator_preflight_error_model_calls=0,
    candidate_current_phase='Fresh final third followup from own frozen implementation, same model/task/permission profile; terminal evaluation pending.',
    board_state='Same evaluated AGY Flash r02 frozen artifact; no Pro firmware has been uploaded and no serial/flash during Pro followup execution.',
    terminal_snapshot=None,launch_snapshot=PUBLIC.relative_to(ROOT).as_posix(),
    restart_instruction='Read r02 manifest, shared ledger, AGY owner and launcher/child processes. Do not repeat or replace running followup. Preserve terminal status/cost, restore global scope and evaluate without operator source edits afterward.')
save(progress_path,p)
print(json.dumps({'run_id':RUN.name,'status':'running','started_at':m['execution']['started_at'],
    'native_model':init['model'],'launcher_pid':launcher['launcher_pid'],'launch_files':len(read(PUBLIC/'snapshot-inventory.json')['files'])}))
