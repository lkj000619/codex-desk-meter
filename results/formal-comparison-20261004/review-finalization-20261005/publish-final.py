"""Publish final review and initial AGY start without changing candidate workspaces."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys

ROOT=Path.cwd();BASE=ROOT/'results/formal-comparison-20261004'
RUN=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
PACK=Path('C:/meter-run-packages-20261005/opencode-muse-r02-final')
REST=Path('C:/meter-run-restores-20261005/opencode-muse-r02-final')
AGY=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
PUB=BASE/'review-finalization-20261005'
sys.path.insert(0,str(ROOT/'scripts'))
from benchmark_support import digest,read,save
audit=read(REST/'frozen-validator-audit.json')
assert audit['rm_review_completed'] and audit['frozen_operator_validators_used']
copies={'run-manifest-reviewed.json':RUN/'run-manifest.json',
        'run-manifest-after-reference-review.json':RUN/'run-manifest-after-reference-review.json',
        'reference-review.json':RUN/'reference-review.json','ledger-reviewed.json':Path('C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json'),
        'series-completion.json':RUN/'operator-series-completion.json','post-review-evidence-link.json':RUN/'operator-review-finalization.json',
        'observation-finalization.json':RUN/'operator-observation/observation-finalization.json',
        'capture-identity-confirmation.json':RUN/'operator-observation/user-video-01/capture-identity-confirmation.json',
        'confirmed-video-review.json':RUN/'operator-observation/user-video-01/confirmed-video-review.json',
        'package-manifest.json':PACK/'package-manifest.json','create-report.json':PACK.parent/'opencode-muse-r02-final-create.json',
        'restore-report.json':REST/'restore-report.json','restore-audit.json':REST/'frozen-validator-audit.json',
        'finalize-review.py':Path('C:/meter-followups-20261004/finalize-opencode-r02-review.py'),
        'package-final.py':PACK.parent/'package-opencode-r02-final.py','audit-final.py':PACK.parent/'audit-opencode-r02-final.py',
        'publish-final.py':Path(__file__)}
PUB.mkdir(exist_ok=False)
for name,source in copies.items():shutil.copyfile(source,PUB/name)
save(PUB/'inventory.json',{'run_id':RUN.name,'files':{name:{'sha256':digest((PUB/name).read_bytes()),'bytes':(PUB/name).stat().st_size} for name in copies}})

AGY_PUB=BASE/'evidence'/AGY.name/'launch-20261005'
AGY_PUB.mkdir(parents=True,exist_ok=False)
agy_files=['experiment-launch.json','experiment-launch-attempt2.json','operator-launch-attempt1-review.json',
           'runner-console.txt','runner-console-stderr.txt']
for name in agy_files:shutil.copyfile(AGY/name,AGY_PUB/name)
for folder_name in ['operator-launch-preflight','operator-launch-preflight-r2']:
    for source in (AGY/folder_name).rglob('*'):
        if source.is_file():
            target=AGY_PUB/source.relative_to(AGY);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
for name in ['launch-agy-flash-r01.py','launch-agy-flash-r01.ps1','launch-agy-flash-r01-attempt2.py','launch-agy-flash-r01-attempt2.ps1']:
    shutil.copyfile(AGY.parent/name,AGY_PUB/name)
m=read(AGY/'run-manifest.json')
assert m['operator']['status']=='running' and m['execution']['started_at']
shutil.copyfile(AGY/'run-manifest.json',AGY_PUB/'start-manifest.json')
files={p.relative_to(AGY_PUB).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in AGY_PUB.rglob('*') if p.is_file()}
save(AGY_PUB/'inventory.json',{'run_id':AGY.name,'files':files,'scope':'Fixed launch snapshot; ongoing stdout is not presented as terminal evidence.'})

old=read(BASE/'progress.json')
completion=read(RUN/'operator-series-completion.json')
progress={'checked_at':datetime.now(timezone.utc).isoformat(),'baseline_commit':m['execution']['base_commit'],
          'block':1,'seed':1,'active_models':5,'independent_series_planned':15,
          'independent_series_completed':1,'initial_series_started':2,'followups_started':1,
          'product_executions_started':3,'product_executions_completed':2,
          'state':'agy_flash_initial_running','current_run':AGY.name,'current_directory':str(AGY),
          'ledger':m['operator']['comparison']['ledger'],'round':0,'model':m['agent']['model'],
          'started_at':m['execution']['started_at'],'ended_at':None,'timeout_seconds':7200,
          'launcher_pid':read(AGY/'experiment-launch-attempt2.json')['pid'],
          'profile_sha256':m['execution']['profile_sha256'],'input_bundle_sha256':m['execution']['input_bundle_sha256'],
          'receipt_sha256':digest((AGY/'execution-preflight.json').read_bytes()),
          'policy_review_required':True,'policy_status':'pending_terminal_review',
          'hardware_access_by_operator_during_candidate':False,'user_interventions_reported':None,
          'operator_implementation_feedback_sent_during_run':False,'rm_review':'awaiting_candidate_terminal',
          'elapsed_seconds':None,'tokens':m['measurement']['tokens'],'candidate_hardware_access':False,
          'launch_operator_errors_before_model':1,'operator_preflight_error_model_calls':0,
          'board_state':'Same frozen OpenCode r02 artifact; observation complete; no AGY board upload during execution.',
          'current_native_scope':'Private scoped AGY settings active until runner child exits; global restoration recorded afterward.',
          'previous_series':{**completion,'first_result':old['first_result'],
                             'series_measured_seconds':old['series_measured_seconds'],
                             'series_reported_normalized_tokens':old['series_reported_normalized_tokens'],
                             'final_package_manifest_sha256':audit['package_manifest_sha256'],
                             'final_package_files_verified':430,'final_rm_review':'review-finalization-20261005/reference-review.json'},
          'unstarted_models_remaining_in_block':3,'next_after_current_series':'AGY Pro',
          'restart_instruction':'Read manifest, ledger, active AGY root owner and launcher process; do not invoke another candidate while this run is running.'}
save(BASE/'progress.json',progress)
print(json.dumps({'open_code_series':'budget_exhausted_reviewed_and_restored','final_package_files':430,
                  'agy_state':m['operator']['status'],'agy_run_id':AGY.name,'agy_started_at':m['execution']['started_at'],
                  'launcher_pid':progress['launcher_pid'],'model':progress['model']},indent=2))
