"""Preserve post-review provenance, package current evaluation, independently restore; no new candidate."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys

ROOT=Path.cwd();BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
PACK=Path('C:/meter-run-packages-20261005/agy-flash-r02-final');REST=Path('C:/meter-run-restores-20261005/agy-flash-r02-final')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import digest,read,save,verify_evidence
from policy_review import validate_review
from evidence_package import create_package,restore_package

m=read(RUN/'run-manifest.json');raw=(RUN/'run-manifest.json').read_bytes();f=read(RUN/'operator-source-freeze.json')
assert m['outputs']['implementation_commit']==f['commit'] and m['operator']['comparison']['reference_status']=='fail'
assert not read(RUN/'operator-user-hold.json')['next_model_start_authorized_now']
assert not (RUN/'run-manifest-after-reference-review.json').exists()
(RUN/'run-manifest-after-reference-review.json').write_bytes(raw)
names=['run-manifest-after-reference-review.json','operator-review-finalization.json','operator-reference-review-input.json',
    'operator-observation/observation-finalization.json']
host=read(RUN/'operator-observation/fresh-host-artifact-inventory.json')
for name,meta in host['files'].items():
    p=Path(meta['path']);assert digest(p.read_bytes())==meta['sha256']
    dest=RUN/'operator-observation/fresh-host-binary-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    names.append(dest.relative_to(RUN).as_posix())
post={'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),'reference_review_applied_once':True,
    'reference_review_manifest_sha256':digest(raw),'post_review_changes':['operator.evidence'],'added_files':names,
    'candidate_source_modified':False,'candidate_submission_fabricated':False,'costs_modified':False,
    'original_terminal_copy':'operator-observation/terminal-originals/run-manifest.json','user_hold_preserved':True,
    'host_binary_snapshot_scope':'Independent operator host build archived for reproducibility; not submitted firmware and never flashed.'}
save(RUN/'operator-post-review-evidence.json',post)
for name in names+['operator-post-review-evidence.json']:m['operator']['evidence'][name]=digest((RUN/name).read_bytes())
save(RUN/'run-manifest.json',m)
verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
p=ROOT/'results/formal-comparison-20261004/progress.json';progress=read(p)
progress.update(checked_at=post['recorded_at'],state='agy_flash_followup_1_reviewed_user_hold_preservation_pending',
    rm_review='complete',rm_items={k:v['status'] for k,v in read(RUN/'reference-review.json')['items'].items()},
    reference_status='fail',product_pass=False,optical_video_received=True,video_capture_identity_confirmed=True,
    video_sha256=read(RUN/'operator-observation/user-video-01/video-metadata.json')['source_sha256'],
    candidate_current_phase='Current r02 RM review complete; final package/restore underway. User holds all further candidate progression.',
    independent_restore='pending',next_model_start_authorized_now=False,additional_candidate_round_start_authorized_now=False)
save(p,progress)
created=create_package(RUN,PACK)
created.update(final_run_manifest_sha256=digest((RUN/'run-manifest.json').read_bytes()),
    scope='Final r02 evaluation; schema-valid submitted result, policy invalidity, missing real frame acceptance, crash/reboot logs and user video preserved. Explicit user hold; no next model or additional round.')
save(PACK.parent/'agy-flash-r02-final-create.json',created)
print(json.dumps(created),flush=True)
restored=restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps(restored),flush=True)
