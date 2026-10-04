"""Preserve review provenance and archive using the frozen package tool."""
from datetime import datetime, timezone
from pathlib import Path
import copy
import json
import sys

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
PACK=Path('C:/meter-run-packages-20261005/agy-flash-r01-final');REST=Path('C:/meter-run-restores-20261005/agy-flash-r01-final')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import digest,read,save,verify_evidence
from policy_review import validate_review
from evidence_package import create_package,restore_package

m=read(RUN/'run-manifest.json');raw=(RUN/'run-manifest.json').read_bytes()
assert m['outputs']['implementation_commit']=='29e1d7af54a8c9c879e36192ec4ed689e5bbf82d'
assert m['operator']['comparison']['reference_status']=='fail'
prior=read(RUN/'operator-review-finalization.json')
(RUN/'run-manifest-after-reference-review.json').write_bytes(raw)
names=['run-manifest-after-reference-review.json','operator-review-finalization.json',
    'operator-reference-review-input.json','operator-observation/observation-finalization.json']
post={'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),'reference_review_applied_once':True,
    'reference_review_manifest_sha256':digest(raw),'post_review_changes':['operator.evidence'],'added_files':names,
    'candidate_source_modified':False,'candidate_submission_fabricated':False,'costs_modified':False,
    'original_terminal_copy':'operator-observation/terminal-originals/run-manifest.json'}
save(RUN/'operator-post-review-evidence.json',post)
for name in names+['operator-post-review-evidence.json']:m['operator']['evidence'][name]=digest((RUN/name).read_bytes())
save(RUN/'run-manifest.json',m)
verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
created=create_package(RUN,PACK)
created.update(final_run_manifest_sha256=digest((RUN/'run-manifest.json').read_bytes()),
    scope='Final operator evaluation of initial environment_failed attempt; missing candidate JSON and failed USB write preserved. Followup budget remains 7200 seconds.')
save(PACK.parent/'agy-flash-r01-final-create.json',created)
print(json.dumps(created),flush=True)
restored=restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps(restored),flush=True)
