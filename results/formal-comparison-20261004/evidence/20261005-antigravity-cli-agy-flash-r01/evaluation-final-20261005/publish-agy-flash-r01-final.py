"""Publish final evidence separately from the unchanged initial terminal snapshot."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
import json

ROOT=Path.cwd();RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
PACK=Path('C:/meter-run-packages-20261005/agy-flash-r01-final');REST=Path('C:/meter-run-restores-20261005/agy-flash-r01-final')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import digest,read,save

PUBLIC=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'evaluation-final-20261005';PUBLIC.mkdir(exist_ok=False)
names=['run-manifest.json','run-manifest-after-reference-review.json','operator-reference-review-input.json','reference-review.json',
    'operator-review-finalization.json','operator-post-review-evidence.json','operator-observation/observation-finalization.json']
names += ['operator-observation/user-video-01/'+p.name for p in (RUN/'operator-observation/user-video-01').iterdir() if p.is_file() and p.name!='source.mp4']
for name in names:
    dest=PUBLIC/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RUN/name,dest)
shutil.copy2(RUN.parent/'ledgers'/f'{RUN.name}.json',PUBLIC/'ledger-reviewed.json')
for source,name in ((PACK/'package-manifest.json','package-manifest.json'),(PACK.parent/'agy-flash-r01-final-create.json','package-create.json'),
    (REST/'restore-report.json','restore-report.json'),(REST/'frozen-validator-audit.json','restore-audit.json')):shutil.copy2(source,PUBLIC/name)
for source in ('package-agy-flash-r01-final.py','audit-agy-flash-r01-final.py','publish-agy-flash-r01-final.py'):
    shutil.copy2(PACK.parent/source,PUBLIC/source)
review=read(RUN/'reference-review.json');audit=read(REST/'frozen-validator-audit.json');now=datetime.now(timezone.utc).isoformat()
assert audit['frozen_operator_validators_used'] and audit['inventory_bytes_verified'] and audit['rm_review_completed']
save(PUBLIC/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':now,
    'files':{p.relative_to(PUBLIC).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in PUBLIC.rglob('*') if p.is_file()},
    'original_video':{'operator_path':str(RUN/'operator-observation/user-video-01/source.mp4'),
        'sha256':audit['user_video_sha256'],'bytes':23640439,'stored_outside_repository':True},
    'scope':'Final initial RM and independent package restoration; original terminal snapshot/manifest/ledger preserved. Missing candidate JSON, environment_failed, failed USB write, and costs remain.'})
progress_path=ROOT/'results/formal-comparison-20261004/progress.json';p=read(progress_path)
p.update(checked_at=now,state='agy_flash_initial_reviewed_followup_pending',rm_review='complete',
    rm_items={k:v['status'] for k,v in review['items'].items()},reference_status='fail',product_pass=False,
    optical_video_received=True,video_capture_identity_confirmed=True,video_sha256=audit['user_video_sha256'],
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=430,
    independent_restore='verified_with_packaged_frozen_validators',final_rm_review=PUBLIC.relative_to(ROOT).as_posix()+'/reference-review.json',
    candidate_current_phase='Initial evaluation and independent preservation complete; followup not started; initial series not yet complete.',
    board_state='Same frozen AGY Flash r01 app; observed video complete, slot released, failed seq 0 USB write retained.',
    restart_instruction='Initial r01 reviewed once, preserved/restored. Do not repeat initial invocation. Followup may continue own source with remaining 7200 seconds and at most 3 rounds; prepare new ID and check current frozen profile/receipt/native scope.')
save(progress_path,p)
print(json.dumps({'final_public_files':len(read(PUBLIC/'snapshot-inventory.json')['files']),'package_sha256':audit['package_manifest_sha256'],'initial_review_complete':True,'series_complete':False}))
