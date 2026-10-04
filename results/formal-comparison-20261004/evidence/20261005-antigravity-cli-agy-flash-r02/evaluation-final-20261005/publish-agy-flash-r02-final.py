"""Publish final current-run evaluation and explicit user hold, preserving earlier snapshots."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys

ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
PACK=Path('C:/meter-run-packages-20261005/agy-flash-r02-final');REST=Path('C:/meter-run-restores-20261005/agy-flash-r02-final')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import digest,read,save

PUBLIC=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'evaluation-final-20261005';PUBLIC.mkdir(exist_ok=False)
names=['run-manifest.json','run-manifest-after-reference-review.json','operator-reference-review-input.json','reference-review.json',
    'operator-review-finalization.json','operator-post-review-evidence.json','operator-user-hold.json','operator-observation/observation-finalization.json']
names += ['operator-observation/user-video-01/'+p.name for p in (RUN/'operator-observation/user-video-01').iterdir() if p.is_file() and p.name!='source.mp4']
for name in names:
    dest=PUBLIC/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
m=read(RUN/'run-manifest.json');shutil.copy2(Path(m['operator']['comparison']['ledger']),PUBLIC/'ledger-reviewed.json')
for source,name in [(PACK/'package-manifest.json','package-manifest.json'),(PACK.parent/'agy-flash-r02-final-create.json','package-create.json'),
    (REST/'restore-report.json','restore-report.json'),(REST/'frozen-validator-audit.json','restore-audit.json')]:shutil.copy2(source,PUBLIC/name)
for name in ['package-agy-flash-r02-final.py','audit-agy-flash-r02-final.py',Path(__file__).name]:shutil.copy2(PACK.parent/name,PUBLIC/name)
review=read(RUN/'reference-review.json');audit=read(REST/'frozen-validator-audit.json');now=datetime.now(timezone.utc).isoformat()
assert audit['frozen_operator_validators_used'] and audit['inventory_bytes_verified'] and audit['rm_review_completed'] and audit['user_hold_preserved']
save(PUBLIC/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,
    'files':{p.relative_to(PUBLIC).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in PUBLIC.rglob('*') if p.is_file()},
    'original_video':{'operator_path':str(RUN/'operator-observation/user-video-01/source.mp4'),
        'sha256':audit['user_video_sha256'],'bytes':22018701,'stored_outside_repository':True},
    'scope':'Final r02 RM, archive and independent frozen-validator restoration. Earlier launch/terminal/evaluation-stage snapshots retained. Explicit user hold prevents candidate progression.'})
p=ROOT/'results/formal-comparison-20261004/progress.json';progress=read(p)
progress.update(checked_at=now,state='agy_flash_followup_1_evaluation_complete_user_hold',rm_review='complete',
    rm_items={k:v['status'] for k,v in review['items'].items()},reference_status='fail',product_pass=False,
    optical_video_received=True,video_capture_identity_confirmed=True,video_sha256=audit['user_video_sha256'],
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=audit['files_verified'],
    independent_restore='verified_with_packaged_frozen_validators',final_rm_review=PUBLIC.relative_to(ROOT).as_posix()+'/reference-review.json',
    candidate_current_phase='Current r02 evaluation and independent preservation complete. Explicit user hold; no further candidate round or next model started. Series remains held with budget retained.',
    board_state='Same original frozen AGY Flash r02 firmware uploaded at 05:38:52 KST; video evaluated, serial closed, no firmware replacement.',
    user_requested_hold=True,next_model_start_authorized_now=False,additional_candidate_round_start_authorized_now=False,
    restart_instruction='Wait for explicit user resumption. AGY Flash r02 evaluated and restored; do not rerun it, start another AGY followup/model, replace board firmware or reset budgets. Retain 5710.781 followup seconds and 2 rounds, original costs/failed product and policy invalidity. Current plan is complete; whole comparison remains on user hold.')
save(p,progress)
print(json.dumps({'final_public_files':len(read(PUBLIC/'snapshot-inventory.json')['files']),'package_sha256':audit['package_manifest_sha256'],
    'current_round_evaluation_complete':True,'series_complete':False,'user_hold':True,'next_model_started':False}))
