"""Link post-review operator records and package the final timeout evidence."""
from pathlib import Path
from datetime import datetime,timezone
import sys
import json
ROOT=Path.cwd()
RUN=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
DEST=Path('C:/meter-run-packages-20261005/opencode-muse-r02-final')
sys.path.insert(0,str(ROOT/'scripts'))
from benchmark_support import read,save,digest,verify_evidence
from evidence_package import create_package
from policy_review import validate_review
raw=(RUN/'run-manifest.json').read_bytes();m=read(RUN/'run-manifest.json')
assert m['operator']['comparison']['reference_status']=='fail'
assert m['outputs']['implementation_commit']=='354c6475345cb521c92f92e3dce448b0dc5ef58b'
(RUN/'run-manifest-after-reference-review.json').write_bytes(raw)
names=['run-manifest-after-reference-review.json','operator-series-completion.json',
       'operator-observation/observation-finalization.json','operator-reference-review-input.json']
finalization={'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
              'reference_review_applied_once':True,'reference_review_manifest_sha256':digest(raw),
              'post_review_changes':['operator.evidence'],'added_files':names,
              'candidate_source_modified':False,'candidate_submission_fabricated':False,
              'costs_modified':False,'original_terminal_copy':'operator-terminal-manifest-original.json'}
save(RUN/'operator-review-finalization.json',finalization)
for name in names+['operator-review-finalization.json']:
    m['operator']['evidence'][name]=digest((RUN/name).read_bytes())
save(RUN/'run-manifest.json',m)
verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
created=create_package(RUN,DEST)
created.update(final_run_manifest_sha256=digest((RUN/'run-manifest.json').read_bytes()),
               scope='Final operator RM review of timed-out residual implementation; candidate result and selection submissions remain missing.')
save(DEST.parent/'opencode-muse-r02-final-create.json',created)
print(json.dumps(created,ensure_ascii=False,indent=2))
