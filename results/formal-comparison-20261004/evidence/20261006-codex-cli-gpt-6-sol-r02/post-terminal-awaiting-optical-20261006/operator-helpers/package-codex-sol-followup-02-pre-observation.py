"""Independently preserve a policy-ineligible product before device observation."""
from pathlib import Path
import json,shutil,sys
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02')
PACK=Path('C:/meter-run-packages-20261006/codex-sol-followup02-pre-observation')
REST=Path('C:/meter-run-restores-20261006/codex-sol-followup02-pre-observation')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read,save,digest,verify_evidence
from policy_review import validate_review
from evidence_package import create_package,restore_package
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert m['operator']['status']=='completed' and digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
assert not f['firmware_source_mutations_after_last_build']
names=['operator-source-freeze.json','operator-terminal-source.bundle','operator-policy-decision.json','policy-review.json',
    'experiment-launch.json','native-start-observation.json','native-start-observation-prefix.jsonl','process-at-start.json',
    'operator-next-model-decision.json','previous-progress-at-transition.json','operator-generated-output-cleanup.json']
names += [p.relative_to(RUN).as_posix() for d in ('operator-observation','operator-launch-preflight') for p in (RUN/d).rglob('*') if p.is_file()]
for name in names:m['operator']['evidence'][name]=digest((RUN/name).read_bytes())
m['outputs']['implementation_commit']=f['commit'];m['outputs']['build_status']='pass'
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN)
created=create_package(RUN,PACK);save(PACK.parent/'codex-sol-followup02-pre-observation-create.json',created)
restored=restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored}))
